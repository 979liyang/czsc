# -*- coding: utf-8 -*-
"""
策略示例2：ETF 均线择时

策略逻辑：ETF 均线金叉死叉择时示例。

适用市场：ETF
适用周期：日线
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """ETF 均线择时（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="159915.SZ")
    bars = get_raw_bars("159915.SZ", freq="日线", sdt="2020-01-01", edt="2024-01-01")
    print("示例策略")
