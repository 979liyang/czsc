from czsc.analyze import CZSC
from czsc.objects import RawBar, Freq
from czsc.connectors import research
from datetime import datetime
import os
from pathlib import Path

# 1. 获取K线数据
symbol = "000001.SH"
bars = research.get_raw_bars(
    symbol=symbol,
    freq=Freq.D,
    sdt="20200101",
    edt="20231231"
)

# 2. 创建CZSC分析对象
czsc = CZSC(bars)

# 3. 查看分析结果
print(f"识别出 {len(czsc.finished_bis)} 已完成的笔列表")
print(f"识别出 {len(czsc.fx_list)} 个分型列表(包括已完成笔中的分型和未完成笔中的分型)")
print(f"识别出 {len(czsc.ubi_fxs)} 个未完成笔（bars_ubi）中的分型")
print(f"识别出 {len(czsc.ubi)} 个未完成笔")

# 4. 查看最后一笔
if czsc.finished_bis:
    last_bi = czsc.finished_bis[-1]
    print(f"最后一笔方向：{last_bi.direction.value}")
    print(f"最后一笔幅度：{last_bi.power:.2f}")

# 5. 生成图表
print("\n正在生成图表...")

# 方式1: 使用 open_in_browser() 自动打开浏览器
# 注意：在某些环境下，浏览器可能不会自动打开，需要手动打开文件
try:
    czsc.open_in_browser()  # 会在 ~/temp_czsc.html 生成文件并尝试打开浏览器
    home_path = os.path.expanduser("~")
    temp_file = os.path.join(home_path, "temp_czsc.html")
    print(f"✓ 图表已保存到: {temp_file}")
    print("  如果浏览器没有自动打开，请手动打开该文件")
except Exception as e:
    print(f"⚠ 自动打开浏览器失败: {e}")

# 方式2: 手动保存到项目根目录（推荐，更可靠）
chart = czsc.to_echarts()
# 保存到项目根目录，文件名包含符号和时间戳
project_root = Path(__file__).parent.parent
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = project_root / ".results" /f"czsc_chart_{symbol}_{timestamp}.html"
chart.render(str(output_file))
print(f"✓ 图表已保存到: {output_file.absolute()}")
print(f"  请手动在浏览器中打开该文件查看图表")