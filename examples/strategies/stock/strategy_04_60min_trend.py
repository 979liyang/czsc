# -*- coding: utf-8 -*-
"""
策略示例4：60分钟趋势跟踪

策略逻辑：60分钟级别趋势跟踪示例。

适用市场：股票
适用周期：60分钟
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """60分钟趋势跟踪（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="000300.SH")
    bars = get_raw_bars("000300.SH", freq="60分钟", sdt="2021-01-01", edt="2024-01-01")
    print("示例策略")
