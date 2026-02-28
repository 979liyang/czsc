# -*- coding: utf-8 -*-
"""
筛选任务 CLI：供 scripts/scheduled_tasks.py run_screen 或 cron 调用。

用法：
    python -m backend.src.jobs.screen_task --trade-date 20260222
    python -m backend.src.jobs.screen_task --trade-date 20260222 --market SH,SZ
    python -m backend.src.jobs.screen_task --trade-date 20260222 --max-symbols 10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="执行信号/因子筛选并写入 ScreenResult")
    parser.add_argument(
        "--trade-date",
        type=str,
        default="",
        help="交易日 YYYYMMDD，默认当天",
    )
    parser.add_argument(
        "--market",
        type=str,
        default="",
        help="市场过滤，如 SH,SZ",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=0,
        help="最多处理股票数，0 表示不限制（测试可设 10）",
    )
    args = parser.parse_args()

    from datetime import datetime
    from backend.src.services.screen_service import run_signal_screen
    from backend.src.storage.mysql_db import get_db_session

    trade_date = args.trade_date.strip()
    if not trade_date:
        trade_date = datetime.now().strftime("%Y%m%d")
    market = args.market.strip() or None

    try:
        for session in get_db_session():
            n = run_signal_screen(
                session,
                trade_date=trade_date,
                market=market,
                signal_service=None,
                max_symbols=args.max_symbols,
            )
            session.commit()
            logger.info(f"筛选完成：trade_date={trade_date}，写入 {n} 条")
        return 0
    except Exception as e:
        logger.exception(f"筛选任务失败: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
