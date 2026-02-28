# -*- coding: utf-8 -*-
"""
策略示例2：5分钟笔非多即空

策略逻辑：5分钟笔方向交易，与30分钟笔策略类似。

适用市场：期货
适用周期：5分钟
"""
from typing import List
from czsc.objects import Event, Position
from czsc import CzscStrategyBase


def create_5min_long_short(symbol, **kwargs):
    """5分钟笔多空策略"""
    base_freq = kwargs.get("base_freq", "5分钟")
    opens = [
        {"operate": "开多", "signals_all": [f"{base_freq}_D1_表里关系V230102_向上_任意_任意_0"], "signals_not": []},
        {"operate": "开空", "signals_all": [f"{base_freq}_D1_表里关系V230102_向下_任意_任意_0"], "signals_not": []},
    ]
    exits = [
        {"operate": "平多", "signals_all": [f"{base_freq}_D1_表里关系V230102_向下_任意_任意_0"], "signals_not": []},
        {"operate": "平空", "signals_all": [f"{base_freq}_D1_表里关系V230102_向上_任意_任意_0"], "signals_not": []},
    ]
    return Position(
        name=f"{base_freq}笔非多即空",
        symbol=symbol,
        opens=[Event.load(x) for x in opens],
        exits=[Event.load(x) for x in exits],
        interval=kwargs.get("interval", 1800),
        timeout=kwargs.get("timeout", 48 * 5),
        stop_loss=kwargs.get("stop_loss", 200),
    )


class Strategy(CzscStrategyBase):
    """5分钟笔非多即空策略"""

    @property
    def positions(self) -> List[Position]:
        return [create_5min_long_short(self.symbol, base_freq="5分钟")]


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="RB888")
    bars = get_raw_bars("RB888", freq="5分钟", sdt="2020-01-01", edt="2023-01-01")
    print("回测示例")
