# -*- coding: utf-8 -*-
"""
策略示例3：ETF 笔结构

策略逻辑：基于 ETF 笔结构的缠论策略示例。

适用市场：ETF
适用周期：30分钟
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """ETF 笔结构策略（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="510500.SH")
    bars = get_raw_bars("510500.SH", freq="30分钟", sdt="2021-01-01", edt="2024-01-01")
    print("示例策略")
