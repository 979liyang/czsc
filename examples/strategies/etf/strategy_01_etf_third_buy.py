# -*- coding: utf-8 -*-
"""
策略示例1：ETF 日线三买

策略逻辑：ETF 日线三买信号多头策略，与股票三买逻辑类似。

适用市场：ETF
适用周期：日线、30分钟
"""
from typing import List
from czsc.objects import Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """ETF 日线三买策略（示例骨架）"""

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        return []


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="510300.SH")
    bars = get_raw_bars("510300.SH", freq="日线", sdt="2020-01-01", edt="2024-01-01")
    print("ETF 示例策略")
