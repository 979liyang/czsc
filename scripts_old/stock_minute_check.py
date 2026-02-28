# -*- coding: utf-8 -*-
"""
分钟数据完整性校验脚本

功能说明：
- 按交易日校验分钟数据的完整性（expected vs actual）
- 定位缺失的分钟区间（缺口）并写入 MySQL 的 stock_minute_gaps 表
- 用于数据质量检查，帮助识别哪些时间段的数据需要补数

工作原理：
1. 根据交易时段（默认 09:30-11:30, 13:00-15:00）计算期望分钟数
2. 查询实际存在的分钟数据
3. 计算缺失的分钟时间点
4. 将连续缺失区间合并为缺口记录，写入 gaps 表

时间范围处理：
- 如果指定了 --date：只校验该单日
- 如果指定了 --sdt 和 --edt：校验该日期区间内的所有交易日
- 如果都不指定：自动从 stock_minute_coverage 表或分钟数据中检测最早和最晚时间

用法示例：
    # 校验单只股票单日
    python scripts/stock_minute_check.py --symbol 000001.SZ --date 2024-01-04

    # 批量校验：指定日期区间
    python scripts/stock_minute_check.py --sdt 2024-01-01 --edt 2024-01-31 --market SH,SZ

    # 自动检测时间范围（从 coverage 表或分钟数据中获取最早/最晚时间）
    python scripts/stock_minute_check.py --market SH,SZ

    # 校验指定股票的所有可用日期
    python scripts/stock_minute_check.py --symbol 600078.SH
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="分钟数据完整性校验并写入 gaps 表")
    parser.add_argument("--symbol", default="", help="股票代码（可选）")
    parser.add_argument("--date", default="", help="单日校验 YYYY-MM-DD（可选）")
    parser.add_argument("--sdt", default="", help="开始日期 YYYY-MM-DD（可选）")
    parser.add_argument("--edt", default="", help="结束日期 YYYY-MM-DD（可选）")
    parser.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    parser.add_argument("--limit", type=int, default=0, help="股票数量限制，0 表示不限制")
    return parser.parse_args()


def parse_markets(v: str) -> Optional[List[str]]:
    v = (v or "").strip()
    if not v:
        return None
    return [x.strip().upper() for x in v.split(",") if x.strip()]


def _detect_date_range(session, minute_repo, symbol: Optional[str] = None, markets: Optional[List[str]] = None) -> Tuple[Optional[date], Optional[date]]:
    """自动检测时间范围：优先从 coverage 表，其次从分钟数据表"""
    from backend.src.models.mysql_models import StockBasic, StockMinuteCoverage
    from sqlalchemy import func

    # 优先从 coverage 表获取
    try:
        query = session.query(
            func.MIN(StockMinuteCoverage.start_dt).label("min_dt"),
            func.MAX(StockMinuteCoverage.end_dt).label("max_dt")
        )
        if symbol:
            query = query.filter(StockMinuteCoverage.symbol == symbol)
        elif markets:
            symbols_subq = session.query(StockBasic.symbol).filter(StockBasic.market.in_(markets)).subquery()
            query = query.filter(StockMinuteCoverage.symbol.in_(session.query(symbols_subq.c.symbol)))
        
        row = query.first()
        if row and row.min_dt and row.max_dt:
            start_dt = row.min_dt.date() if isinstance(row.min_dt, datetime) else row.min_dt
            end_dt = row.max_dt.date() if isinstance(row.max_dt, datetime) else row.max_dt
            logger.info(f"从 coverage 表检测到时间范围：{start_dt} ~ {end_dt}")
            return start_dt, end_dt
    except Exception as e:
        logger.warning(f"从 coverage 表检测时间范围失败：{e}，尝试从分钟数据表检测")

    # 降级：从分钟数据表获取（需要先确定股票列表）
    try:
        if symbol:
            symbols = [symbol]
        elif markets:
            symbols = [
                x[0] for x in session.query(StockBasic.symbol)
                .filter(StockBasic.market.in_(markets))
                .order_by(StockBasic.symbol.asc())
                .all()
            ]
        else:
            symbols = [x[0] for x in session.query(StockBasic.symbol).order_by(StockBasic.symbol.asc()).all()]
        
        if not symbols:
            symbols = minute_repo.list_distinct_symbols(limit=100)  # 限制数量避免太慢
        
        if not symbols:
            logger.warning("未找到任何股票，无法检测时间范围")
            return None, None
        
        # 取第一只股票的时间范围作为参考（或可以取所有股票的最小/最大）
        min_dt, max_dt = minute_repo.get_dt_range(symbols[0])
        if min_dt and max_dt:
            start_dt = min_dt.date() if isinstance(min_dt, datetime) else min_dt
            end_dt = max_dt.date() if isinstance(max_dt, datetime) else max_dt
            logger.info(f"从分钟数据表检测到时间范围（参考股票 {symbols[0]}）：{start_dt} ~ {end_dt}")
            return start_dt, end_dt
    except Exception as e:
        logger.warning(f"从分钟数据表检测时间范围失败：{e}")

    return None, None


def main() -> int:
    _bootstrap()
    args = parse_args()
    markets = parse_markets(args.market)

    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.minute_bar_repo import MinuteBarRepo
    from backend.src.models.mysql_models import StockBasic, StockMinuteGap
    from backend.src.services.data_quality_core import calc_missing_minutes, missing_minutes_to_ranges
    from backend.src.utils.trading_calendar import list_trading_dates, expected_minutes_per_day

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        expected = expected_minutes_per_day()
        minute_repo = MinuteBarRepo(session)

        # 1) 交易日范围
        trade_dates: List[date] = []
        if args.date:
            trade_dates = [datetime.strptime(args.date, "%Y-%m-%d").date()]
        elif args.sdt and args.edt:
            trade_dates = list_trading_dates(args.sdt, args.edt)
        else:
            # 自动检测时间范围
            logger.info("未指定时间范围，自动检测最早和最晚时间...")
            start_dt, end_dt = _detect_date_range(session, minute_repo, symbol=args.symbol if args.symbol else None, markets=markets)
            if not start_dt or not end_dt:
                logger.error("无法自动检测时间范围，请手动指定 --date 或 (--sdt 与 --edt)")
                logger.info("提示：可以先运行 stock_minute_scan.py 扫描 coverage 表")
                return 1
            trade_dates = list_trading_dates(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"))
            logger.info(f"自动检测到时间范围：{start_dt} ~ {end_dt}，共 {len(trade_dates)} 个交易日")

        # 2) 股票范围
        symbols: List[str] = []
        if args.symbol:
            symbols = [args.symbol]
        else:
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
            if not symbols:
                symbols = minute_repo.list_distinct_symbols(limit=args.limit)

        if args.limit and args.limit > 0:
            symbols = symbols[: args.limit]

        logger.info(f"开始缺口校验：symbols={len(symbols)} days={len(trade_dates)} expected={expected}")

        now = datetime.now()
        written = 0
        for s in symbols:
            for d in trade_dates:
                # 先清理旧缺口
                session.query(StockMinuteGap).filter(StockMinuteGap.symbol == s, StockMinuteGap.trade_date == d).delete()

                actual_minutes = minute_repo.list_minutes(s, d)
                if len(actual_minutes) >= expected:
                    continue

                missing = calc_missing_minutes(d, actual_minutes)
                ranges = missing_minutes_to_ranges(missing)
                for r in ranges:
                    session.add(
                        StockMinuteGap(
                            symbol=s,
                            trade_date=d,
                            gap_start=r.start,
                            gap_end=r.end,
                            gap_minutes=r.minutes,
                            details=None,
                            created_at=now,
                        )
                    )
                    written += 1

        session.commit()
        logger.info(f"缺口校验完成：gap_rows={written}")
        return 0
    except Exception as e:
        session.rollback()
        logger.error(f"缺口校验失败：{e}", exc_info=True)
        return 2
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())

