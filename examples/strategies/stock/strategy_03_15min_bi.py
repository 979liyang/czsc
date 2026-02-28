# -*- coding: utf-8 -*-
"""
策略示例3：15分钟笔结构策略

策略逻辑：基于15分钟笔的方向与结构进行交易。

适用市场：股票
适用周期：15分钟
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """15分钟笔结构策略（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="600000.SH")
    bars = get_raw_bars("600000.SH", freq="15分钟", sdt="2022-01-01", edt="2024-01-01")
    print("示例策略")
