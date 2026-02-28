from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research
from czsc.analyze import CZSC
from pathlib import Path
from typing import Dict

# 1. 获取K线数据
symbol = "000001.SH"
bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20231231")

# 2. 创建K线合成器
bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value])
for bar in bars:
    bg.update(bar)

# 3. 自定义信号函数
def my_signal_V001(czsc: CZSC, **kwargs) -> Dict[str, str]:
    """自定义信号函数示例
    
    根据最后一笔的方向生成信号
    
    :param czsc: CZSC分析对象
    :param kwargs: 其他参数（如 di=1 表示倒数第几笔）
    :return: 信号字典，格式为 {freq_name_signal_value: value}
    """
    s = {}
    di = kwargs.get('di', 1)  # 默认使用最后一笔
    
    # 检查是否有足够的笔
    if len(czsc.finished_bis) < di:
        s[f"{czsc.freq.value}_自定义信号V001_无笔"] = "无笔"
        return s

    # 获取倒数第di笔
    last_bi = czsc.finished_bis[-di]
    freq = czsc.freq.value
    signal_name = f"{freq}_自定义信号V001"
    
    # 根据笔的方向生成信号
    if last_bi.direction.value == "向上":
        s[f"{signal_name}_向上"] = "向上"
    else:
        s[f"{signal_name}_向下"] = "向下"
    
    return s

# 4. 配置信号（使用自定义信号函数）
signals_config = [
    {
        'name': my_signal_V001,  # 直接传入函数对象，也可以使用字符串路径
        'freq': '日线',  # 指定频率，信号函数会接收该频率的 CZSC 对象
        'di': 1  # 自定义参数：使用最后一笔
    },
    # {
    #     'name': my_signal_V001,
    #     'freq': '日线',
    #     'di': 2  # 使用倒数第二笔
    # }
]

# 5. 创建信号计算对象
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 6. 获取信号
signals = cs.s
print("\n=== 所有信号 ===")
for k, v in signals.items():
    if isinstance(k, str) and len(k.split("_")) == 3:
        print(f"{k}: {v}")

# 7. 生成快照
# 保存到根目录下的 .results 目录
project_root = Path(__file__).parent.parent
results_dir = project_root / ".results"
results_dir.mkdir(exist_ok=True)  # 如果目录不存在则创建
output_file = results_dir / "signals1.html"
cs.take_snapshot(str(output_file))
print(f"\n✅ 快照已保存到: {output_file.absolute()}")