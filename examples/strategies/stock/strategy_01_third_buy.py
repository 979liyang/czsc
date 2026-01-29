# -*- coding: utf-8 -*-
"""
策略示例1：日线三买多头策略

策略逻辑：
1. 开多条件：日线出现三买信号
2. 平多条件：30分钟出现一卖信号，或特定笔数的一卖信号

适用市场：股票
适用周期：日线、30分钟
"""
from typing import List
from czsc.objects import Event, Position
from czsc import CzscStrategyBase


class Strategy(CzscStrategyBase):
    """日线三买多头策略"""

    def create_pos_a(self, symbol, **kwargs):
        """创建多头持仓策略"""
        base_freq = kwargs.get("base_freq", "30分钟")

        opens = [
            {
                "operate": "开多",
                "signals_not": [],
                "signals_all": [],
                "factors": [{"name": "三买多头", "signals_all": ["日线_D1_三买辅助V230228_三买_任意_任意_0"]}],
            }
        ]

        exits = [
            {
                "operate": "平多",
                "signals_all": [],
                "signals_not": [],
                "factors": [
                    {
                        "name": "平多",
                        "signals_all": ["30分钟_D1B_SELL1_一卖_任意_任意_0"],
                        "signals_any": [
                            "30分钟_D1B_SELL1_一卖_9笔_任意_0",
                            "30分钟_D1B_SELL1_一卖_11笔_任意_0",
                            "30分钟_D1B_SELL1_一卖_13笔_任意_0",
                        ],
                    }
                ],
            }
        ]
        opens[0]["signals_all"].append(f"{base_freq}_D1_涨跌停V230331_任意_任意_任意_0")
        pos_name = "日线三买多头A"

        T0 = kwargs.get("T0", False)
        pos_name = f"{pos_name}T0" if T0 else f"{pos_name}"

        pos = Position(
            name=pos_name,
            symbol=symbol,
            opens=[Event.load(x) for x in opens],
            exits=[Event.load(x) for x in exits],
            interval=kwargs.get("interval", 3600 * 2),
            timeout=kwargs.get("timeout", 16 * 30),
            stop_loss=kwargs.get("stop_loss", 300),
            T0=T0,
        )
        return pos

    @property
    def positions(self) -> List[Position]:
        """持仓策略列表"""
        _pos = [
            self.create_pos_a(symbol=self.symbol, base_freq="30分钟", T0=False),
        ]
        return _pos


if __name__ == "__main__":
    from czsc.connectors.research import get_raw_bars

    tactic = Strategy(symbol="000001.SH")
    bars = get_raw_bars("000001.SH", freq="30分钟", sdt="2015-01-01", edt="2022-07-01")
    trader = tactic.backtest(bars, sdt="20200101")
    print("回测完成")
