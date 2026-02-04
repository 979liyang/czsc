# -*- coding: utf-8 -*-
"""
数据质量计算核心算法

本模块专注“分钟数据完整性”计算，不包含数据库读写。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable, List, Sequence, Tuple

from loguru import logger

from ..utils.settings import get_settings


@dataclass(frozen=True)
class GapRangeResult:
    """缺口区间结果（半开区间 [start, end)）"""

    start: datetime
    end: datetime
    minutes: int


def _parse_hhmm(v: str) -> time:
    return datetime.strptime(v, "%H:%M").time()


def _truncate_to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def expected_minutes_of_day(trade_date: date, sessions: Sequence[Tuple[str, str]] | None = None) -> List[datetime]:
    """
    构造某交易日的“期望分钟时间点”列表

    约定：按半开区间 [start, end) 构造分钟点位。
    """

    sessions = list(sessions or get_settings().trading_sessions)
    res: List[datetime] = []
    for s, e in sessions:
        start_dt = datetime.combine(trade_date, _parse_hhmm(s))
        end_dt = datetime.combine(trade_date, _parse_hhmm(e))
        cur = start_dt
        while cur < end_dt:
            res.append(cur)
            cur += timedelta(minutes=1)
    return res


def calc_expected_count(trade_date: date, sessions: Sequence[Tuple[str, str]] | None = None) -> int:
    """计算期望分钟条数"""

    return len(expected_minutes_of_day(trade_date, sessions=sessions))


def calc_missing_minutes(trade_date: date, actual_dts: Iterable[datetime]) -> List[datetime]:
    """
    计算缺失分钟点位（返回缺失分钟的 datetime 列表）

    :param trade_date: 交易日
    :param actual_dts: 实际分钟时间点（可包含秒/微秒，会截断到分钟）
    """

    expected = set(expected_minutes_of_day(trade_date))
    actual = {_truncate_to_minute(x) for x in actual_dts}
    missing = sorted(expected - actual)
    logger.debug(f"missing_minutes trade_date={trade_date} expected={len(expected)} actual={len(actual)} missing={len(missing)}")
    return missing


def missing_minutes_to_ranges(missing_minutes: List[datetime]) -> List[GapRangeResult]:
    """
    将缺失分钟点位压缩为缺口区间

    连续分钟会被合并成一个区间，区间表示为半开区间 [start, end)。
    """

    if not missing_minutes:
        return []

    missing_minutes = sorted(missing_minutes)
    ranges: List[GapRangeResult] = []

    start = missing_minutes[0]
    prev = start
    for cur in missing_minutes[1:]:
        if cur - prev == timedelta(minutes=1):
            prev = cur
            continue

        end = prev + timedelta(minutes=1)
        ranges.append(GapRangeResult(start=start, end=end, minutes=int((end - start).total_seconds() // 60)))
        start = cur
        prev = cur

    end = prev + timedelta(minutes=1)
    ranges.append(GapRangeResult(start=start, end=end, minutes=int((end - start).total_seconds() // 60)))
    return ranges

