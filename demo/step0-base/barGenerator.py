from czsc.utils import BarGenerator
from czsc.objects import RawBar, Freq
from czsc.connectors import research
from czsc.analyze import CZSC

# 1. 获取基础周期K线
symbol = "000001.SZ"
bars = research.get_raw_bars(
    symbol=symbol,
    freq=Freq.F30,  # 30分钟作为基础周期
    sdt="20200101",
    edt="20231231"
)

# 2. 创建K线合成器
# 注意：base_freq 和 freqs 需要使用字符串值，而不是枚举对象
# freqs 列表中不应该包含 base_freq，因为 base_freq 会自动处理
bg = BarGenerator(
    base_freq=Freq.F30.value,  # "30分钟"
    freqs=[Freq.F60.value, Freq.D.value]  # ["60分钟", "日线"]
)

# 3. 更新K线
print(f"开始更新K线，共 {len(bars)} 根")
for bar in bars:
    bg.update(bar)

# 4. 获取各周期K线（使用字符串键）
# 注意：对于 base_freq，BarGenerator 会创建新的 RawBar，但通常我们直接使用原始 bars
# 或者使用 bg.bars[base_freq]，但需要确保它不为空
bars_30m = bg.bars[Freq.F30.value]  # 或 bg.bars["30分钟"]
bars_60m = bg.bars[Freq.F60.value]   # 或 bg.bars["60分钟"]
bars_d = bg.bars[Freq.D.value]       # 或 bg.bars["日线"]

print(f"\n各周期K线数量:")
print(f"  30分钟 (BarGenerator): {len(bars_30m)} 根")
print(f"  原始bars: {len(bars)} 根")
print(f"  60分钟: {len(bars_60m)} 根")
print(f"  日线: {len(bars_d)} 根")

# 5. 对各周期进行分析
# 对于 base_freq，如果 BarGenerator 的 bars 为空，使用原始 bars
if len(bars_30m) == 0:
    print("\n⚠️ 警告: BarGenerator 的 30分钟K线为空，使用原始bars进行分析")
    bars_30m = bars
czsc_30m = CZSC(bars_30m)

if len(bars_60m) > 0:
    czsc_60m = CZSC(bars_60m)
else:
    print("⚠️ 警告: 60分钟K线为空，跳过分析")
    czsc_60m = None

if len(bars_d) > 0:
    czsc_d = CZSC(bars_d)
else:
    print("⚠️ 警告: 日线K线为空，跳过分析")
    czsc_d = None

print("\n=== 分析结果 ===")
print(f"30分钟笔数量: {len(czsc_30m.finished_bis)}")
if czsc_60m:
    print(f"60分钟笔数量: {len(czsc_60m.finished_bis)}")
if czsc_d:
    print(f"日线笔数量: {len(czsc_d.finished_bis)}")