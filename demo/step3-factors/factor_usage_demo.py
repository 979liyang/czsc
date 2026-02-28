# -*- coding: utf-8 -*-
"""
因子使用 Demo：将多个信号作为「因子」计算，查看因子值与分数，并做简单筛选。

本 demo 与后端 factor_def / run_factor_screen 概念一致：每个因子对应一个信号函数，
计算得到 值 + 分数（0~100），可用于选股或排序。
"""
from pathlib import Path

from czsc.traders import CzscSignals
from czsc.utils.bar_generator import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research

# 1. 获取K线数据（日线）
symbol = "000001.SZ"
bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20260225")
if not bars:
    print(f"未获取到 {symbol} 日线数据，请确认 cache_path 下 daily/by_stock/stock_code={symbol}/ 存在 parquet。")
    exit(1)

# 2. 创建K线合成器
bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value])
for bar in bars:
    bg.update(bar)

# 3. 定义多个因子（每个因子 = 一条信号配置，name 为信号函数全名）
# 与 factor_def 表的 expression_or_signal_ref 对应，便于与后端筛选任务一致
FACTOR_CONFIGS = [
    {
        "factor_name": "成交量单均线SMA5",
        "name": "czsc.signals.vol.vol_single_ma_V230214",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 5,
    },
    {
        "factor_name": "成交量单均线SMA20",
        "name": "czsc.signals.vol.vol_single_ma_V230214",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 20,
    },
]

signals_config = [{"name": c["name"], "freq": c["freq"], "di": c.get("di", 1),
                   "ma_type": c.get("ma_type", "SMA"), "timeperiod": c.get("timeperiod", 5)}
                  for c in FACTOR_CONFIGS]

# 4. 计算因子（通过 CzscSignals 得到各信号的值与分数）
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 5. 从 cs.s 中按「信号 key」取出因子值；value 格式为 v1_v2_v3_score
def parse_score(value_str):
    """从 value 字符串末尾解析分数。格式: v1_v2_v3_score"""
    if not value_str:
        return None
    s = str(value_str).strip()
    parts = s.rsplit("_", 1)
    if len(parts) == 2 and parts[-1].isdigit():
        return int(parts[-1])
    return None


# 按配置顺序，为每个因子找到对应的信号 key（key 形如 日线_D1VOL#SMA#5_分类V230214）
unique_results = []
for cfg in FACTOR_CONFIGS:
    fac_name = cfg["factor_name"]
    tp = cfg.get("timeperiod", 5)
    # 匹配该因子产出的 key：含 D1VOL#SMA#tp_ 且为三段的信号 key
    want_suffix = f"D1VOL#SMA#{tp}_"
    found = None
    for k, v in cs.s.items():
        if not isinstance(k, str) or len(k.split("_")) != 3:
            continue
        if want_suffix in k and "分类V230214" in k:
            score = parse_score(v)
            found = (fac_name, k, v, score)
            break
    if found:
        unique_results.append(found)

# 6. 打印因子结果
print("=" * 60)
print("因子使用 Demo：多因子计算与分数")
print("=" * 60)
print(f"标的: {cs.symbol}  结束时间: {cs.end_dt}  最新价: {cs.latest_price}")
print()
print("【因子值及分数】")
for fac_name, key, value, score in unique_results:
    sc = score if score is not None else "—"
    print(f"  {fac_name}:  value={value}  分数={sc}")

# 7. 简单筛选：分数 >= 60 的因子视为“偏多”
print()
print("【筛选：分数>=60 的因子（偏多）】")
strong = [(f, k, v, s) for f, k, v, s in unique_results if s is not None and s >= 60]
if strong:
    for fac_name, _, value, score in strong:
        print(f"  {fac_name}: {value}  分数={score}")
else:
    print("  无")
print("=" * 60)

# 8. 可选：保存快照到 demo/.results
# project_root = Path(__file__).resolve().parent.parent
# results_dir = project_root / ".results"
# results_dir.mkdir(exist_ok=True)
# cs.take_snapshot(str(results_dir / "factor_usage_demo.html"))
# print(f"快照已保存: {results_dir / 'factor_usage_demo.html'}")
