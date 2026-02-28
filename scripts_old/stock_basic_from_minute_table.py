# -*- coding: utf-8 -*-
"""
从本地 parquet 分钟数据反推股票列表，并补齐 market 字段

适用场景：
- 你已有本地 parquet 分钟数据（.stock_data/raw/minute_by_stock/），但 stock_basic 还没建好
- 想先把 symbol 列表与 market（SH/SZ）补齐，后续再补中文名

用法：
    python scripts/stock_basic_from_minute_table.py --limit 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Set

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从本地 parquet 分钟数据反推 symbol 列表并补齐 stock_basic")
    parser.add_argument("--limit", type=int, default=0, help="distinct symbols 限制条数，0 表示不限制")
    parser.add_argument("--base-path", type=str, default=None, help="分钟数据根目录（默认：项目根目录/.stock_data/raw/minute_by_stock）")
    return parser.parse_args()


def infer_market(symbol: str) -> str | None:
    symbol = (symbol or "").upper()
    if symbol.endswith(".SH"):
        return "SH"
    if symbol.endswith(".SZ"):
        return "SZ"
    return None


def list_symbols_from_parquet(base_path: Path, limit: int = 0) -> list[str]:
    """从 parquet 文件目录结构扫描股票代码列表"""
    symbols: Set[str] = set()
    
    # 扫描 stock_code=xxx 目录
    pattern = "stock_code=*"
    for stock_dir in base_path.glob(pattern):
        if not stock_dir.is_dir():
            continue
        # 提取 stock_code=600078.SH 中的 600078.SH
        stock_code = stock_dir.name.replace("stock_code=", "").strip()
        if stock_code and (stock_code.endswith(".SH") or stock_code.endswith(".SZ")):
            symbols.add(stock_code)
            if limit > 0 and len(symbols) >= limit:
                break
    
    result = sorted(symbols)
    logger.info(f"从 parquet 目录扫描到 distinct symbols={len(result)}（limit={limit}）")
    return result


def main() -> int:
    _bootstrap()
    args = parse_args()

    # 确定分钟数据根目录
    project_root = Path(__file__).resolve().parents[1]
    if args.base_path:
        base_path = Path(args.base_path)
    else:
        base_path = project_root / ".stock_data" / "raw" / "minute_by_stock"
    
    if not base_path.exists():
        logger.error(f"分钟数据目录不存在：{base_path}")
        logger.info("提示：请先运行数据采集脚本（如 fetch_tushare_minute_data_stk_mins.py）生成分钟数据")
        return 1

    # 从 parquet 目录扫描股票代码
    symbols = list_symbols_from_parquet(base_path, limit=args.limit)
    if not symbols:
        logger.warning("未扫描到任何股票代码，请检查数据目录")
        return 1

    # 写入 MySQL stock_basic 表
    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.stock_basic_repo import StockBasicRepo

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        basic_repo = StockBasicRepo(session)
        n = 0
        for s in symbols:
            m = infer_market(s)
            basic_repo.upsert_one(symbol=s, market=m)
            n += 1

        session.commit()
        logger.info(f"反推完成：symbols={n} limit={args.limit}")
        return 0
    except Exception as e:
        session.rollback()
        logger.error(f"反推失败：{e}", exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

