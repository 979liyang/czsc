# -*- coding: utf-8 -*-
"""
交易日历与交易时段工具

用于数据质量检查：
- 获取交易日列表
- 计算某交易日“期望分钟数”（expected_count）
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterable, List, Tuple

from loguru import logger

from czsc.utils.calendar import get_trading_dates, is_trading_date

from .settings import get_settings


@dataclass(frozen=True)
class MinuteExpectation:
    """分钟期望条数"""

    trade_date: date
    expected_count: int


def list_trading_dates(sdt: str | date | datetime, edt: str | date | datetime) -> List[date]:
    """获取区间内交易日（闭区间）"""

    dts = get_trading_dates(sdt=sdt, edt=edt)
    return [d.date() if isinstance(d, datetime) else d for d in dts]


def expected_minutes_per_day(sessions: Iterable[Tuple[str, str]] | None = None) -> int:
    """
    计算单个交易日的期望分钟数（按半开区间 [start, end) 统计）

    A股默认：09:30-11:30（120） + 13:00-15:00（120） = 240
    """

    sessions = list(sessions or get_settings().trading_sessions)
    total = 0
    for s, e in sessions:
        start = datetime.strptime(s, "%H:%M")
        end = datetime.strptime(e, "%H:%M")
        minutes = int((end - start).total_seconds() // 60)
        total += max(minutes, 0)
    return total


def build_expected_minutes(trade_dates: List[date]) -> List[MinuteExpectation]:
    """为多个交易日构造期望分钟数"""

    expected = expected_minutes_per_day()
    return [MinuteExpectation(trade_date=d, expected_count=expected) for d in trade_dates]


def is_trade_day(d: date | datetime) -> bool:
    """是否交易日（基于 czsc 内置日历）"""

    return bool(is_trading_date(d))


def safe_recent_trading_dates(days: int = 30) -> List[date]:
    """获取最近 N 天内的交易日列表（容错）"""

    try:
        edt = datetime.now().date()
        sdt = edt - timedelta(days=days * 2)
        dts = list_trading_dates(sdt, edt)
        return dts[-days:] if len(dts) > days else dts
    except Exception as e:
        logger.warning(f"获取最近交易日失败：{e}")
        return []

