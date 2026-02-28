# -*- coding: utf-8 -*-
"""
策略示例2：日线均线多头策略

策略逻辑：基于日线均线金叉/死叉进行多空切换。

适用市场：股票
适用周期：日线
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """日线均线多头策略（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表（示例无实际开平仓）"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="000001.SZ")
    bars = get_raw_bars("000001.SZ", freq="日线", sdt="2020-01-01", edt="2024-01-01")
    print("示例策略，可在此接入回测")
