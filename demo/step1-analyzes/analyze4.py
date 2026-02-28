"""
`CZSC` 类是缠论分析的核心类，负责分型和笔的识别。
# 属性
czsc.bars_raw          # 原始K线列表
czsc.bars_ubi          # 未完成笔的K线列表
czsc.fx_list           # 分型列表
czsc.finished_bis      # 已完成的笔列表
czsc.bi_list           # 所有笔列表（包括未完成）
czsc.ubi               # 未完成的笔
czsc.last_bi_extend    # 最后一笔是否在延伸

# 方法
czsc.update(bar)       # 更新新的K线
czsc.to_echarts()      # 生成ECharts图表
czsc.open_in_browser() # 在浏览器中打开图表
"""

from czsc import CZSC, Freq
from czsc.connectors import research
from czsc.utils.sig import get_zs_seq
from pathlib import Path
from datetime import datetime

# 获取数据
symbol = "000001.SH"
bars = research.get_raw_bars(symbol=symbol, freq=Freq.D, sdt="20200101", edt="20231231")

# 创建分析对象
czsc = CZSC(bars)

print(len(czsc.bars_raw), '原始K线列表')
print(len(czsc.bars_ubi), '未完成笔的K线列表')
print(len(czsc.fx_list), '分型列表')
print(len(czsc.finished_bis), '已完成的笔列表')
print(len(czsc.bi_list), '所有笔列表（包括未完成）')
print(len(czsc.ubi), '未完成的笔')
print(czsc.last_bi_extend, '最后一笔是否在延伸')

if czsc.finished_bis:
    last_bi = czsc.finished_bis[-1]
    print(f"最后一笔方向：{last_bi.direction.value}")
    print(f"最后一笔幅度：{last_bi.power:.2f}")

# 实时更新
# new_bar = research.get_raw_bars("000001.SH", Freq.D, "20231231", "20240101")[-1]
# czsc.update(new_bar)

# 查看结果
print(f"分型数量：{len(czsc.fx_list)}")
print(f"笔数量：{len(czsc.finished_bis)}")

# 中枢：由至少 3 笔重叠构成，zg 为上沿、zd 为下沿；图中绿色半透明矩形即为中枢区间
chart = czsc.to_echarts(draw_zs=True)
if czsc.finished_bis:
    zs_list = get_zs_seq(czsc.finished_bis)
    valid_zs = [z for z in zs_list if len(z.bis) >= 3 and z.is_valid]
    print(f"中枢数量（已绘制）：{len(valid_zs)}")
# 保存到项目根目录，文件名包含符号和时间戳
project_root = Path(__file__).parent.parent
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = project_root / ".results" /f"czsc_chart_analyze_01_{symbol}_{timestamp}.html"
chart.render(str(output_file))
print(f"✓ 图表已保存到: {output_file.absolute()}")
print(f"  请手动在浏览器中打开该文件查看图表")