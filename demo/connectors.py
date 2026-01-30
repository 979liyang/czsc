# 最常用的数据连接器，支持多种数据获取方式。

from czsc.connectors import research
from czsc.objects import Freq

# 获取股票列表
# 可用的分组：'A股主要指数', 'A股场内基金', '中证500成分股', '期货主力'
symbols = research.get_symbols('A股主要指数')
print(f"共 {len(symbols)} 只股票")

# 获取K线数据
bars = research.get_raw_bars(
    symbol="000001.SH",
    freq=Freq.D,
    sdt="20200101",
    edt="20231231"
)

print(len(bars))

# 获取多个标的的K线
# 注意：research 模块没有 get_raw_bars_multi 方法，需要循环调用 get_raw_bars
symbols_list = ["000001.SH", "000002.SH"]
all_bars = {}
for symbol in symbols_list:
    try:
        bars = research.get_raw_bars(
            symbol=symbol,
            freq=Freq.D,
            sdt="20200101",
            edt="20231231"
        )
        all_bars[symbol] = bars
        print(f"{symbol}: {len(bars)} 根K线")
    except Exception as e:
        print(f"获取 {symbol} 数据失败: {e}")

print(f"\n总共获取 {len(all_bars)} 个标的的数据")