# -*- coding: utf-8 -*-
"""
扫描分钟数据覆盖概况（min/max(dt)）并写入 coverage 表

功能说明：
- 从本地 parquet 文件扫描每只股票分钟数据的起止时间（最早/最晚时间）
- 将结果写入 MySQL 的 stock_minute_coverage 表
- 用于数据质量统计，帮助了解每只股票的数据覆盖范围

数据来源：
- 从本地 parquet 文件读取：.stock_data/raw/minute_by_stock/stock_code={symbol}/year={year}/{symbol}_{year}-{month}.parquet
- 不依赖 MySQL 的 stock_minute_bars 表（该表可能不存在）

用法：
    # 扫描所有股票
    python scripts/stock_minute_scan.py

    # 扫描指定市场
    python scripts/stock_minute_scan.py --market SH,SZ

    # 限制扫描数量（测试用）
    python scripts/stock_minute_scan.py --market SH,SZ --limit 10
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描分钟数据起止时间并写入 coverage 表")
    parser.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    parser.add_argument("--limit", type=int, default=0, help="扫描股票数量限制，0 表示不限制")
    parser.add_argument("--output-missing", type=str, default=None, help="输出无数据股票列表到文件（默认：.stock_data/metadata/missing_stocks_{timestamp}.txt）")
    return parser.parse_args()


def parse_markets(v: str) -> Optional[List[str]]:
    v = (v or "").strip()
    if not v:
        return None
    return [x.strip().upper() for x in v.split(",") if x.strip()]


def _get_dt_range_from_parquet(symbol: str, base_path: Path) -> Tuple[Optional[datetime], Optional[datetime]]:
    """从 parquet 文件获取某股票分钟数据的起止时间"""
    import pandas as pd

    stock_dir = base_path / f"stock_code={symbol}"
    if not stock_dir.exists():
        return None, None

    # 扫描所有 parquet 文件
    files = sorted(stock_dir.glob("year=*/**/*.parquet"))
    if not files:
        return None, None

    min_dt = None
    max_dt = None

    for fp in files:
        try:
            df = pd.read_parquet(fp)
            if df is None or len(df) == 0:
                continue

            # 确定时间列名
            dt_col = None
            for col in ["timestamp", "dt", "datetime", "trade_time"]:
                if col in df.columns:
                    dt_col = col
                    break

            if not dt_col:
                continue

            df[dt_col] = pd.to_datetime(df[dt_col])
            file_min = df[dt_col].min()
            file_max = df[dt_col].max()

            if min_dt is None or file_min < min_dt:
                min_dt = file_min
            if max_dt is None or file_max > max_dt:
                max_dt = file_max
        except Exception as e:
            logger.warning(f"读取 parquet 失败：{fp} - {e}")
            continue

    return min_dt, max_dt


def main() -> int:
    _bootstrap()
    args = parse_args()
    markets = parse_markets(args.market)

    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.models.mysql_models import StockBasic, StockMinuteCoverage

    # 确定 parquet 数据根目录
    project_root = Path(__file__).resolve().parents[1]
    base_path = project_root / ".stock_data" / "raw" / "minute_by_stock"

    if not base_path.exists():
        logger.error(f"分钟数据目录不存在：{base_path}")
        logger.info("提示：请先运行数据采集脚本（如 fetch_tushare_minute_data_stk_mins.py）生成分钟数据")
        return 1

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        # 1) 从 stock_basic 取 symbol；如果没有则从 parquet 目录扫描
        symbols: List[str] = []
        if markets is None:
            symbols = [x[0] for x in session.query(StockBasic.symbol).order_by(StockBasic.symbol.asc()).all()]
        else:
            symbols = [
                x[0]
                for x in session.query(StockBasic.symbol)
                .filter(StockBasic.market.in_(markets))
                .order_by(StockBasic.symbol.asc())
                .all()
            ]

        # 如果 stock_basic 为空，从 parquet 目录扫描
        if not symbols:
            logger.info("stock_basic 表为空，从 parquet 目录扫描股票代码...")
            pattern = "stock_code=*"
            for stock_dir in base_path.glob(pattern):
                if not stock_dir.is_dir():
                    continue
                stock_code = stock_dir.name.replace("stock_code=", "").strip()
                if stock_code and (stock_code.endswith(".SH") or stock_code.endswith(".SZ")):
                    symbols.append(stock_code)
            symbols = sorted(symbols)

        if args.limit and args.limit > 0:
            symbols = symbols[: args.limit]

        logger.info(f"开始扫描 coverage：symbols={len(symbols)} markets={markets}")

        now = datetime.now()
        updated = 0
        skipped = 0
        missing_symbols: List[str] = []

        for s in symbols:
            start_dt, end_dt = _get_dt_range_from_parquet(s, base_path)
            if start_dt is None or end_dt is None:
                skipped += 1
                missing_symbols.append(s)
                logger.debug(f"{s} 无数据，跳过")
                continue

            obj = session.get(StockMinuteCoverage, s)
            if obj is None:
                obj = StockMinuteCoverage(symbol=s)
                session.add(obj)

            obj.start_dt = start_dt
            obj.end_dt = end_dt
            obj.last_scan_at = now
            obj.updated_at = now
            updated += 1

        session.commit()
        logger.info(f"coverage 扫描完成：updated={updated} skipped={skipped}")

        # 保存无数据股票列表
        if missing_symbols:
            if args.output_missing:
                output_path = Path(args.output_missing)
            else:
                output_dir = project_root / ".stock_data" / "metadata"
                output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"missing_stocks_{timestamp}.txt"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(sorted(missing_symbols)) + "\n", encoding="utf-8")
            logger.info(f"无数据股票列表已保存：{output_path} (共 {len(missing_symbols)} 只)")

        return 0
    except Exception as e:
        session.rollback()
        logger.error("coverage 扫描失败：%s", str(e), exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

