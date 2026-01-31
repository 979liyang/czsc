# 与 ts_connector 完全相同的调用方式
from czsc.connectors.ak_connector import get_raw_bars
from czsc.objects import Freq

bars = get_raw_bars(
    symbol="000001.SZ",
    freq=Freq.D,
    sdt="20250101",
    edt="20260131",
    fq="前复权"
)

print(bars)