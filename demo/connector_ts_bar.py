from czsc.connectors.ts_connector import get_raw_bars
from czsc.objects import Freq

# 注意：ts_connector 的 symbol 参数格式为 "ts_code#asset"
# asset 取值：
#   - "E" 表示股票（Equity）
#   - "I" 表示指数（Index）
#   - "F" 表示基金（Fund）
#   - "O" 表示期权（Option）
#   - "C" 表示期货（Commodity）
bars = get_raw_bars(
    symbol="000001.SH#I",  # 000001.SH 是指数，使用 #I
    freq=Freq.D,
    sdt="20200101",
    edt="20231231",
    fq="前复权"  # 前复权、后复权、不复权
)

print(f"获取到 {len(bars)} 根K线")