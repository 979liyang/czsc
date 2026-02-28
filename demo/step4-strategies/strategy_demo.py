# -*- coding: utf-8 -*-
"""
策略 Demo：单均线多头策略回放

使用 czsc.strategies 的 create_single_ma_long（日线均线看多/看空）进行回放，
输出开平仓记录与持仓评估。数据使用日线，无需分钟数据。
"""
import os
from pathlib import Path

from czsc import CzscStrategyBase
from czsc.objects import Position
from czsc.strategies import create_single_ma_long
from czsc.connectors import research
from czsc.objects import Freq


class Strategy(CzscStrategyBase):
    """日线单均线多头策略：均线看多开多、看空平多。"""

    @property
    def positions(self):
        # 日线、SMA40、A股（涨跌停不交易）
        return [
            create_single_ma_long(
                self.symbol,
                "SMA#40",
                is_stocks=True,
                freq="日线",
                base_freq="日线",
            )
        ]


if __name__ == "__main__":
    symbol = "000001.SZ"
    sdt, edt = "20200101", "20241231"

    bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt=sdt, edt=edt)
    if not bars:
        print(f"未获取到 {symbol} 日线数据，请确认 cache_path 下 daily/by_stock/stock_code={symbol}/ 存在 parquet。")
        exit(1)

    tactic = Strategy(symbol=symbol)
    project_root = Path(__file__).resolve().parent.parent
    res_path = project_root / ".results" / "strategy_demo"
    os.makedirs(res_path, exist_ok=True)

    print("=" * 60)
    print("策略 Demo：单均线多头回放")
    print("=" * 60)
    print(f"标的: {symbol}  区间: {sdt} ~ {edt}  K线数: {len(bars)}")
    print(f"结果目录: {res_path}")
    print()

    # 回放：sdt 前用于初始化 BarGenerator，之后逐根 on_bar
    trader = tactic.replay(
        bars,
        str(res_path),
        sdt="20220101",
        n=500,
        refresh=False,
        exist_ok=True,
    )

    if trader:
        for pos in trader.positions:
            print(f"【{pos.name}】")
            print(f"  操作次数: {len(pos.operates)}")
            if pos.operates:
                for op in pos.operates[-5:]:
                    print(f"    {op['dt'].strftime('%Y-%m-%d')}  {op['op'].value}  bid={op['bid']}  price={op['price']}")
                if len(pos.operates) > 5:
                    print(f"    ... 共 {len(pos.operates)} 次")
            print(f"  评估: {pos.evaluate()}")
            print()
    print("=" * 60)
