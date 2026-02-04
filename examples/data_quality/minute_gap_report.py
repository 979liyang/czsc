# -*- coding: utf-8 -*-
"""
分钟缺口报告导出示例

从 MySQL 的 gaps 表导出缺口报告，便于人工审查与补数安排。

用法示例：
    python examples/data_quality/minute_gap_report.py --sdt 2024-01-01 --edt 2024-01-31 --out gaps.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 examples/ 直接运行"""

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出分钟缺口报告（gaps 表）")
    parser.add_argument("--sdt", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--edt", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--out", required=True, help="输出 CSV 路径")
    return parser.parse_args()


def export_gaps(sdt: str, edt: str) -> pd.DataFrame:
    """导出 gaps 区间明细为 DataFrame"""

    from sqlalchemy import text

    from backend.src.storage.mysql_db import get_engine
    from backend.src.utils.settings import get_settings

    settings = get_settings()
    table = settings.table_minute_gaps
    sql = text(
        f"SELECT symbol, trade_date, gap_start, gap_end, gap_minutes, details "
        f"FROM {table} WHERE trade_date >= :sdt AND trade_date <= :edt "
        f"ORDER BY symbol, trade_date, gap_start"
    )
    with get_engine().connect() as conn:
        df = pd.read_sql(sql, conn, params={"sdt": sdt, "edt": edt})
    return df


def main() -> int:
    _bootstrap()
    args = parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    df = export_gaps(args.sdt, args.edt)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    logger.info(f"导出完成：rows={len(df)} out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

