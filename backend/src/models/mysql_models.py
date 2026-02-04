# -*- coding: utf-8 -*-
"""
MySQL 表结构（SQLAlchemy ORM）

覆盖四类数据：
- 股票主数据：stock_basic
- 分钟覆盖概况：stock_minute_coverage
- 分钟日统计：stock_minute_daily_stats
- 分钟缺口明细：stock_minute_gaps
"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

from ..utils.settings import get_settings

Base = declarative_base()


def _now() -> datetime:
    return datetime.now()


class StockBasic(Base):
    """股票主数据"""

    __tablename__ = get_settings().table_stock_basic

    symbol = Column(String(32), primary_key=True, comment="股票代码，如 000001.SZ / 600000.SH")
    name = Column(String(64), nullable=True, comment="中文名称")
    market = Column(String(8), nullable=True, comment="市场：SH / SZ")
    list_date = Column(String(16), nullable=True, comment="上市日期 YYYYMMDD")
    delist_date = Column(String(16), nullable=True, comment="退市日期 YYYYMMDD")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class StockMinuteCoverage(Base):
    """分钟数据覆盖概况（每只股票一行）"""

    __tablename__ = get_settings().table_minute_coverage

    symbol = Column(String(32), primary_key=True, comment="股票代码")
    start_dt = Column(DateTime, nullable=True, comment="最早分钟时间")
    end_dt = Column(DateTime, nullable=True, comment="最晚分钟时间")
    coverage_ratio = Column(Float, nullable=True, comment="覆盖率（可选，依赖日统计）")
    last_scan_at = Column(DateTime, default=_now, nullable=False, comment="最近扫描时间")
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class StockMinuteDailyStats(Base):
    """分钟日统计（每股票每交易日）"""

    __tablename__ = get_settings().table_minute_daily_stats

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日")
    actual_count = Column(Integer, nullable=False, comment="实际分钟条数")
    expected_count = Column(Integer, nullable=True, comment="期望分钟条数（可选）")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (UniqueConstraint("symbol", "trade_date", name="uq_symbol_trade_date"),)


class StockMinuteGap(Base):
    """分钟缺口明细（按日、按缺口区间）"""

    __tablename__ = get_settings().table_minute_gaps

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日")
    gap_start = Column(DateTime, nullable=False, comment="缺口开始时间（含）")
    gap_end = Column(DateTime, nullable=False, comment="缺口结束时间（不含）")
    gap_minutes = Column(Integer, nullable=False, comment="缺口分钟数")
    details = Column(Text, nullable=True, comment="缺口描述/定位信息（JSON 或文本）")
    created_at = Column(DateTime, default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("symbol", "trade_date", "gap_start", "gap_end", name="uq_gap_range"),)

