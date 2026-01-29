# -*- coding: utf-8 -*-
"""
策略示例1：30分钟笔非多即空策略

策略逻辑：
1. 根据30分钟笔的方向进行交易
2. 笔向上时开多，笔向下时开空
3. 笔方向改变时平仓

适用市场：期货
适用周期：30分钟
"""
from typing import List
from czsc.objects import Event, Position
from czsc import CzscStrategyBase


def create_long_short_V230909(symbol, **kwargs):
    """创建多空持仓策略"""
    base_freq = kwargs.get("base_freq", "30分钟")

    opens = [
        {
            "operate": "开多",
            "signals_all": [f"{base_freq}_D1_表里关系V230102_向上_任意_任意_0"],
            "signals_not": [],
        },
        {
            "operate": "开空",
            "signals_all": [f"{base_freq}_D1_表里关系V230102_向下_任意_任意_0"],
            "signals_not": [],
        },
    ]

    exits = [
        {
            "operate": "平多",
            "signals_all": [f"{base_freq}_D1_表里关系V230102_向下_任意_任意_0"],
            "signals_not": [],
        },
        {
            "operate": "平空",
            "signals_all": [f"{base_freq}_D1_表里关系V230102_向上_任意_任意_0"],
            "signals_not": [],
        },
    ]

    pos = Position(
        name=f"{base_freq}笔非多即空",
        symbol=symbol,
        opens=[Event.load(x) for x in opens],
        exits=[Event.load(x) for x in exits],
        interval=kwargs.get("interval", 3600),
        timeout=kwargs.get("timeout", 16 * 30),
        stop_loss=kwargs.get("stop_loss", 500),
    )
    return pos


class Strategy(CzscStrategyBase):
    """30分钟笔非多即空策略"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_stocks = kwargs.get('is_stocks', False)

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        pos_list = [
            create_long_short_V230909(self.symbol, base_freq='30分钟'),
        ]
        return pos_list


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="RB888")
    bars = get_raw_bars("RB888", freq="30分钟", sdt="2015-01-01", edt="2022-07-01")
    trader = tactic.backtest(bars, sdt="20200101")
    print("回测完成")
