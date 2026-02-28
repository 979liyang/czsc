# -*- coding: utf-8 -*-
"""
四策略信号示例：单均线多空、三买三卖，并给出三买/三卖日期与当前看多/看空结论。

策略对应：
- create_single_ma_long(symbol, ma_name[, ...])  单均线多头
- create_single_ma_short(symbol, ma_name[, ...]) 单均线空头
- create_third_buy_long(symbol[, is_stocks])     缠论三买多头
- create_third_sell_short(symbol[, is_stocks])   缠论三卖空头
"""
from pathlib import Path

from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research

# 1. 获取K线数据
# 凯撒股份
# symbol = "000796.SZ"
# 粤传媒
# symbol = "002236.SZ"
# 石基信息
symbol = "002153.SZ"
bars = research.get_raw_bars_minute(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20260212")

# 2. 创建K线合成器
bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value])
for bar in bars:
    bg.update(bar)

# 3. 配置信号：单均线BS辅助（看多/看空）+ 五笔形态（类三买/类三卖）
# 与 create_single_ma_long/short、create_third_buy_long、create_third_sell_short 所用信号一致
ma_name = "SMA#40"
signals_config = [
    {
        "name": "czsc.signals.tas_ma_base_V230313",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 40,
        "max_overlap": 5,
    },
    {"name": "czsc.signals.cxt_five_bi_V230619", "freq": "日线", "di": 1},
]

# 4. 创建信号计算对象
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 5. 回放历史，收集三买、三卖出现日期
init_n = 300
bg_replay = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value])
for bar in bars[:init_n]:
    bg_replay.update(bar)

third_buy_dates = []
third_sell_dates = []
for bar in bars[init_n:]:
    bg_replay.update(bar)
    cs_replay = CzscSignals(bg=bg_replay, signals_config=signals_config)
    for k, v in cs_replay.s.items():
        if not isinstance(k, str) or v is None:
            continue
        v_str = str(v)
        if "形态V230619" in k and "类三买" in v_str:
            third_buy_dates.append(bar.dt)
            break
    for k, v in cs_replay.s.items():
        if not isinstance(k, str) or v is None:
            continue
        v_str = str(v)
        if "形态V230619" in k and "类三卖" in v_str:
            third_sell_dates.append(bar.dt)
            break

# 6. 当前信号：均线多空 + 是否处于类三买/类三卖
signals = cs.s
ma_bull = None
ma_bear = None
third_buy_now = False
third_sell_now = False
for k, v in signals.items():
    if not isinstance(k, str) or v is None:
        continue
    v_str = str(v)
    if "BS辅助V230313" in k:
        if "看多" in v_str:
            ma_bull = True
        if "看空" in v_str:
            ma_bear = True
    if "形态V230619" in k and "类三买" in v_str:
        third_buy_now = True
    if "形态V230619" in k and "类三卖" in v_str:
        third_sell_now = True

# 7. 结论：看多 / 看空 / 震荡
if (ma_bull or third_buy_now) and not (ma_bear or third_sell_now):
    conclusion = "看多"
elif (ma_bear or third_sell_now) and not (ma_bull or third_buy_now):
    conclusion = "看空"
else:
    conclusion = "震荡"

# 8. 输出详细说明
print("=" * 70)
print("四策略信号详细（单均线多空 + 缠论三买三卖）")
print("=" * 70)
print(f"标的: {cs.symbol}  结束时间: {cs.end_dt}  最新价: {cs.latest_price}")
print()
print("【三买出现日期】")
if third_buy_dates:
    for d in third_buy_dates[-15:]:
        print(f"  {d.strftime('%Y-%m-%d')}")
    if len(third_buy_dates) > 15:
        print(f"  ... 共 {len(third_buy_dates)} 次，仅列最近 15 次")
else:
    print("  无")
print()
print("【三卖出现日期】")
if third_sell_dates:
    for d in third_sell_dates[-15:]:
        print(f"  {d.strftime('%Y-%m-%d')}")
    if len(third_sell_dates) > 15:
        print(f"  ... 共 {len(third_sell_dates)} 次，仅列最近 15 次")
else:
    print("  无")
print()
print("【当前信号状态】")
print(f"  单均线({ma_name}): 看多={ma_bull}  看空={ma_bear}")
print(f"  五笔形态: 类三买={third_buy_now}  类三卖={third_sell_now}")
print()
print("【结论】")
print(f"  >>> 当前 {conclusion} <<<")
print("=" * 70)

# 9. 生成快照
project_root = Path(__file__).parent.parent
results_dir = project_root / ".results"
results_dir.mkdir(exist_ok=True)
output_file = results_dir / "signals_snapshot.html"
cs.take_snapshot(str(output_file))
print(f"快照已保存到: {output_file.absolute()}")
