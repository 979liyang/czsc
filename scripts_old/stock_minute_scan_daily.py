# -*- coding: utf-8 -*-
"""
按交易日统计分钟条数（actual_count）并写入 daily_stats 表

用法：
    python scripts/stock_minute_scan_daily.py --sdt 2024-01-01 --edt 2024-01-31 --market SH,SZ
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按交易日统计分钟条数并写入 daily_stats")
    parser.add_argument("--sdt", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--edt", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    parser.add_argument("--limit", type=int, default=0, help="股票数量限制，0 表示不限制")
    return parser.parse_args()


def parse_markets(v: str) -> Optional[List[str]]:
    v = (v or "").strip()
    if not v:
        return None
    return [x.strip().upper() for x in v.split(",") if x.strip()]


def main() -> int:
    _bootstrap()
    args = parse_args()
    markets = parse_markets(args.market)

    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.minute_bar_repo import MinuteBarRepo
    from backend.src.models.mysql_models import StockBasic, StockMinuteDailyStats
    from backend.src.utils.trading_calendar import list_trading_dates, expected_minutes_per_day

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        trade_dates = list_trading_dates(args.sdt, args.edt)
        expected = expected_minutes_per_day()

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

        minute_repo = MinuteBarRepo(session)
        if not symbols:
            symbols = minute_repo.list_distinct_symbols(limit=args.limit)

        if args.limit and args.limit > 0:
            symbols = symbols[: args.limit]

        logger.info(f"开始生成 daily_stats：symbols={len(symbols)} days={len(trade_dates)} expected={expected}")

        now = datetime.now()
        upserted = 0
        for s in symbols:
            for d in trade_dates:
                cnt = minute_repo.count_by_trade_date(s, d)
                row = (
                    session.query(StockMinuteDailyStats)
                    .filter(StockMinuteDailyStats.symbol == s, StockMinuteDailyStats.trade_date == d)
                    .one_or_none()
                )
                if row is None:
                    row = StockMinuteDailyStats(symbol=s, trade_date=d, actual_count=cnt, expected_count=expected)
                    session.add(row)
                else:
                    row.actual_count = cnt
                    row.expected_count = expected
                    row.updated_at = now
                upserted += 1

        session.commit()
        logger.info(f"daily_stats 完成：rows={upserted}")
        return 0
    except Exception as e:
        session.rollback()
        logger.error(f"daily_stats 失败：{e}", exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

