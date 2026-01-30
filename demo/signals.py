from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research
from czsc.analyze import CZSC
from pathlib import Path

# 1. 获取K线数据
symbol = "000001.SH"
bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20231231")

# 2. 创建K线合成器
bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value])
for bar in bars:
    bg.update(bar)

# 3. 配置信号
signals_config = [
       {
        'name': 'czsc.signals.tas_ma_base_V221101',
        'freq': '日线',
        'di': 1,
        'ma_type': 'SMA',
        'timeperiod': 5
    },
    {
        'name': 'czsc.signals.tas_ma_base_V221101',
        'freq': '日线',
        'di': 5,
        'ma_type': 'SMA',
        'timeperiod': 20
    }
]

# 4. 创建信号计算对象
cs = CzscSignals(bg=bg, signals_config=signals_config)


# 5. 获取信号
signals = cs.s
print("所有信号：")
for k, v in signals.items():
    if isinstance(k, str) and len(k.split("_")) == 3:
        print(f"{k}: {v}")

# 6. 生成快照
# 保存到根目录下的 .results 目录
project_root = Path(__file__).parent.parent
results_dir = project_root / ".results"
results_dir.mkdir(exist_ok=True)  # 如果目录不存在则创建
output_file = results_dir / "signals_snapshot.html"
cs.take_snapshot(str(output_file))
print(f"快照已保存到: {output_file.absolute()}")