# -*- coding: utf-8 -*-
"""
成交量单均线信号 vol_single_ma_V230214 示例

信号逻辑：
- vol > ma → 多头，否则 空头
- ma[-1] > ma[-2] → 向上，否则 向下

输出为 (多头/空头, 向上/向下) 四类组合。
"""
from pathlib import Path

from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research

# 1. 获取K线数据（日线）
symbol = "000001.SZ"
bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20260225")
if not bars:
    print(f"未获取到 {symbol} 日线数据，请确认 cache_path 下 daily/by_stock/stock_code={symbol}/ 存在 parquet 文件。")
    exit(1)

# 2. 创建K线合成器
bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value])
for bar in bars:
    bg.update(bar)

# 3. 配置信号：成交量单均线（可配多组 di / ma_type / timeperiod）
signals_config = [
    {
        "name": "czsc.signals.vol.vol_single_ma_V230214",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 5,
    },
    {
        "name": "czsc.signals.vol.vol_single_ma_V230214",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 20,
    },
]

# 4. 创建信号计算对象
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 5. 打印当前信号（仅输出“信号名”类的 key，格式为 k1_k2_k3）
print("=" * 60)
print("vol_single_ma_V230214 信号分析")
print("=" * 60)
print(f"标的: {cs.symbol}  结束时间: {cs.end_dt}  最新价: {cs.latest_price}")
print()
print("【当前信号】")
for k, v in cs.s.items():
    if isinstance(k, str) and len(k.split("_")) == 3 and "VOL" in k and "分类V230214" in k:
        print(f"  {k}: {v}")
print()

# 6. 生成快照
# project_root = Path(__file__).resolve().parent.parent
# results_dir = project_root / ".results"
# results_dir.mkdir(exist_ok=True)
# output_file = results_dir / "vol_single_ma_V230214.html"
# cs.take_snapshot(str(output_file))
# print(f"快照已保存: {output_file}")
# print("=" * 60)
