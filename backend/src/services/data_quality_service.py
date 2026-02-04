# -*- coding: utf-8 -*-
"""
数据质量服务（MySQL）

提供 coverage / daily_stats / gaps 的查询能力，供 API 与前端展示使用。
"""

from __future__ import annotations

from datetime import date
from time import perf_counter
from typing import List, Optional, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import StockBasic, StockMinuteCoverage, StockMinuteDailyStats, StockMinuteGap


class DataQualityService:
    """数据质量查询服务"""

    def __init__(self, session: Session):
        """
        初始化服务

        :param session: SQLAlchemy Session
        """

        self.session = session

    def list_coverage(
        self,
        symbol: Optional[str] = None,
        market: Optional[str] = None,
        offset: int = 0,
        limit: int = 200,
    ) -> Tuple[List[dict], int]:
        """查询覆盖概况列表（可选按 symbol/market 过滤）"""

        t0 = perf_counter()
        q = self.session.query(StockMinuteCoverage, StockBasic).outerjoin(
            StockBasic, StockBasic.symbol == StockMinuteCoverage.symbol
        )
        if symbol:
            q = q.filter(StockMinuteCoverage.symbol == symbol)
        if market:
            q = q.filter(StockBasic.market == market)

        total = q.count()
        rows = q.order_by(StockMinuteCoverage.symbol.asc()).offset(max(offset, 0)).limit(max(limit, 1)).all()

        items: List[dict] = []
        for cov, basic in rows:
            items.append(
                {
                    "symbol": cov.symbol,
                    "name": basic.name if basic else None,
                    "market": basic.market if basic else None,
                    "start_dt": cov.start_dt,
                    "end_dt": cov.end_dt,
                    "coverage_ratio": cov.coverage_ratio,
                    "last_scan_at": cov.last_scan_at,
                }
            )

        logger.info(
            f"coverage items={len(items)} total={total} symbol={symbol} market={market} "
            f"offset={offset} limit={limit} cost_ms={(perf_counter() - t0) * 1000:.1f}"
        )
        return items, total

    def list_gaps(self, symbol: str, trade_date: date) -> List[dict]:
        """查询某股票某日缺口区间列表"""

        t0 = perf_counter()
        q = (
            self.session.query(StockMinuteGap)
            .filter(StockMinuteGap.symbol == symbol, StockMinuteGap.trade_date == trade_date)
            .order_by(StockMinuteGap.gap_start.asc())
        )
        rows = q.all()
        items = [
            {
                "start": r.gap_start,
                "end": r.gap_end,
                "minutes": r.gap_minutes,
                "details": r.details,
            }
            for r in rows
        ]
        logger.info(
            f"gaps items={len(items)} symbol={symbol} trade_date={trade_date} cost_ms={(perf_counter() - t0) * 1000:.1f}"
        )
        return items

    def list_daily_stats(
        self,
        symbol: Optional[str] = None,
        trade_date: Optional[date] = None,
        offset: int = 0,
        limit: int = 500,
    ) -> Tuple[List[dict], int]:
        """查询分钟日统计列表"""

        t0 = perf_counter()
        q = self.session.query(StockMinuteDailyStats)
        if symbol:
            q = q.filter(StockMinuteDailyStats.symbol == symbol)
        if trade_date:
            q = q.filter(StockMinuteDailyStats.trade_date == trade_date)

        total = q.count()
        rows = (
            q.order_by(StockMinuteDailyStats.symbol.asc(), StockMinuteDailyStats.trade_date.asc())
            .offset(max(offset, 0))
            .limit(max(limit, 1))
            .all()
        )
        items = [
            {
                "symbol": r.symbol,
                "trade_date": r.trade_date,
                "actual_count": r.actual_count,
                "expected_count": r.expected_count,
            }
            for r in rows
        ]
        logger.info(
            f"daily_stats items={len(items)} total={total} symbol={symbol} trade_date={trade_date} "
            f"offset={offset} limit={limit} cost_ms={(perf_counter() - t0) * 1000:.1f}"
        )
        return items, total

