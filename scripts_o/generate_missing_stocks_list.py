#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 MySQL 表生成缺失股票列表并批量获取数据

功能说明：
- 从 stock_basic 表获取所有股票列表
- 从 stock_minute_coverage 表获取已有数据的股票列表
- 计算差集，生成没有数据的股票列表
- 保存到文件（.stock_data/metadata/missing_stocks_{timestamp}.txt）
- 可选：直接调用 fetch_tushare_minute_data_stk_mins.py 批量获取数据

使用场景：
- 首次批量补数：识别哪些股票还没有分钟数据
- 定期维护：扫描新增股票或遗漏的股票

用法示例：
    # 仅生成缺失列表（不自动获取）
    python scripts/generate_missing_stocks_list.py

    # 生成列表并自动调用采集脚本获取数据
    python scripts/generate_missing_stocks_list.py --auto-fetch --freq 1min

    # 指定市场过滤
    python scripts/generate_missing_stocks_list.py --market SH,SZ

    # 自定义输出文件路径
    python scripts/generate_missing_stocks_list.py --output missing.txt

    # 自动获取并启用 checkpoint
    python scripts/generate_missing_stocks_list.py --auto-fetch --freq 1min --checkpoint

    python scripts/generate_missing_stocks_list.py --auto-fetch --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-02-02 19:00:00" --checkpoint
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 MySQL 表生成缺失股票列表并可选批量获取")
    parser.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    parser.add_argument("--output", type=str, default=None, help="输出文件路径（默认：.stock_data/metadata/missing_stocks_{timestamp}.txt）")
    parser.add_argument(
        "--auto-fetch",
        action="store_true",
        help="生成列表后自动调用 fetch_tushare_minute_data_stk_mins.py 获取数据",
    )
    parser.add_argument("--freq", type=str, default="1min", choices=["1min", "5min", "15min", "30min", "60min"], help="分钟周期（仅 --auto-fetch 时有效）")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期（仅 --auto-fetch 时有效）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期（仅 --auto-fetch 时有效）")
    parser.add_argument("--checkpoint", action="store_true", help="启用 checkpoint（仅 --auto-fetch 时有效）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票处理间隔（秒，仅 --auto-fetch 时有效）")
    return parser.parse_args()


def parse_markets(v: str) -> Optional[List[str]]:
    v = (v or "").strip()
    if not v:
        return None
    return [x.strip().upper() for x in v.split(",") if x.strip()]


def get_all_stocks_from_basic(session, markets: Optional[List[str]] = None) -> Set[str]:
    """从 stock_basic 表获取所有股票代码"""
    from backend.src.models.mysql_models import StockBasic

    query = session.query(StockBasic.symbol)
    if markets:
        query = query.filter(StockBasic.market.in_(markets))
    symbols = {x[0] for x in query.all() if x[0]}
    logger.info(f"从 stock_basic 获取到 {len(symbols)} 只股票（markets={markets}）")
    return symbols


def get_stocks_with_data_from_coverage(session, markets: Optional[List[str]] = None) -> Set[str]:
    """从 stock_minute_coverage 表获取已有数据的股票代码（start_dt 和 end_dt 不为空）"""
    from backend.src.models.mysql_models import StockBasic, StockMinuteCoverage
    from sqlalchemy import and_

    # 通过 join 获取有 coverage 且有数据的股票
    query = (
        session.query(StockMinuteCoverage.symbol)
        .join(StockBasic, StockBasic.symbol == StockMinuteCoverage.symbol)
        .filter(and_(StockMinuteCoverage.start_dt.isnot(None), StockMinuteCoverage.end_dt.isnot(None)))
    )
    if markets:
        query = query.filter(StockBasic.market.in_(markets))

    symbols = {x[0] for x in query.all() if x[0]}
    logger.info(f"从 stock_minute_coverage 获取到 {len(symbols)} 只有数据的股票（markets={markets}）")
    return symbols


def main() -> int:
    _bootstrap()
    args = parse_args()
    markets = parse_markets(args.market)

    from backend.src.storage.mysql_db import get_session_maker

    project_root = Path(__file__).resolve().parents[1]

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        # 1) 获取所有股票
        all_stocks = get_all_stocks_from_basic(session, markets=markets)
        if not all_stocks:
            logger.warning("stock_basic 表为空，无法生成缺失列表")
            logger.info("提示：请先运行 fetch_tushare_stock_basic.py 导入股票主数据")
            return 1

        # 2) 获取已有数据的股票
        stocks_with_data = get_stocks_with_data_from_coverage(session, markets=markets)

        # 3) 计算差集（缺失的股票）
        missing_stocks = sorted(all_stocks - stocks_with_data)

        if not missing_stocks:
            logger.info("✅ 所有股票都有数据，无需补数")
            return 0

        logger.info(f"发现 {len(missing_stocks)} 只股票缺失数据（共 {len(all_stocks)} 只，已有 {len(stocks_with_data)} 只）")

        # 4) 保存到文件
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = project_root / ".stock_data" / "metadata"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"missing_stocks_{timestamp}.txt"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(missing_stocks) + "\n", encoding="utf-8")
        logger.info(f"缺失股票列表已保存：{output_path} (共 {len(missing_stocks)} 只)")

        # 5) 可选：自动调用采集脚本
        if args.auto_fetch:
            logger.info("开始自动获取缺失股票的数据...")
            fetch_script = project_root / "scripts" / "fetch_tushare_minute_data_stk_mins.py"
            if not fetch_script.exists():
                logger.error(f"采集脚本不存在：{fetch_script}")
                return 1

            cmd = [
                str(project_root / ".venv" / "bin" / "python"),
                str(fetch_script),
                "--freq",
                args.freq,
                "--from-missing-list",
                str(output_path),
            ]

            if args.start_date:
                cmd.extend(["--start-date", args.start_date])
            if args.end_date:
                cmd.extend(["--end-date", args.end_date])
            if args.checkpoint:
                cmd.append("--checkpoint")
            if args.sleep > 0:
                cmd.extend(["--sleep", str(args.sleep)])

            logger.info(f"执行命令：{' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, cwd=str(project_root), check=False)
                if result.returncode == 0:
                    logger.info("✅ 数据获取完成")
                    return 0
                else:
                    logger.error(f"数据获取失败，退出码：{result.returncode}")
                    return result.returncode
            except Exception as e:
                logger.error(f"执行采集脚本失败：{e}", exc_info=True)
                return 2

        return 0
    except Exception as e:
        logger.error("生成缺失列表失败：%s", str(e), exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
