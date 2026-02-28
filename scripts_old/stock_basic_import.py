# -*- coding: utf-8 -*-
"""
导入 / 更新股票主数据（含中文名）

用法：
    python scripts/stock_basic_import.py --csv stock_basic.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导入股票主数据 CSV 到 MySQL（upsert）")
    parser.add_argument("--csv", required=True, help="CSV 路径，包含 symbol,name,market,list_date,delist_date")
    return parser.parse_args()


def main() -> int:
    _bootstrap()
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        logger.error(f"CSV 不存在：{csv_path}")
        return 1

    df = pd.read_csv(csv_path, dtype=str).fillna("")
    required_cols = {"symbol", "name", "market", "list_date", "delist_date"}
    if not required_cols.issubset(set(df.columns)):
        logger.error(f"CSV 缺少列：需要 {sorted(required_cols)}，实际 {list(df.columns)}")
        return 1

    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.stock_basic_repo import StockBasicRepo

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        rows = df.to_dict(orient="records")
        repo = StockBasicRepo(session)
        n = repo.bulk_upsert(rows)
        session.commit()
        logger.info(f"导入完成：rows={n} file={csv_path}")
        return 0
    except Exception as e:
        session.rollback()
        logger.error(f"导入失败：{e}", exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

