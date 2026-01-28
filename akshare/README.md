# AkShare 数据源模块

本模块提供了基于 AkShare 的数据获取和转换功能，与 CZSC 框架集成。

## 模块结构

```
akshare/
├── __init__.py          # 模块入口
├── base.py              # 基础数据获取函数
├── manager.py           # 数据管理器类
└── README.md           # 说明文档
```

## 功能特性

1. **数据获取**：支持实时行情、分钟数据、历史日线数据
2. **格式转换**：自动将 AkShare 数据转换为 CZSC 的 RawBar 格式
3. **代码标准化**：自动处理各种股票代码格式
4. **与 modules 集成**：提供与 `modules/data.py` 类似的接口

## 使用示例

### 1. 基础数据获取

```python
from akshare.base import (
    get_real_time_data,
    get_minute_data,
    get_historical_data,
    format_akshare_to_rawbar,
    normalize_stock_code,
)
from czsc.objects import Freq

# 获取实时行情
real_time_df = get_real_time_data()
print(f"获取到 {len(real_time_df)} 只股票数据")

# 获取分钟数据
minute_df = get_minute_data("sz000001", period="5")
print(minute_df.head())

# 获取历史数据
hist_df = get_historical_data("000001", "20230101", "20231231")
print(hist_df.head())

# 转换为 RawBar
bars = format_akshare_to_rawbar(hist_df, "000001.SZ", Freq.D)
print(f"转换完成，共 {len(bars)} 根K线")

# 标准化股票代码
code1 = normalize_stock_code("000001")  # -> "000001.SZ"
code2 = normalize_stock_code("sz000001")  # -> "000001.SZ"
code3 = normalize_stock_code("600000")  # -> "600000.SH"
```

### 2. 使用数据管理器

```python
from akshare.manager import AkShareDataManager
from czsc.objects import Freq

# 创建数据管理器
manager = AkShareDataManager()

# 获取K线数据（自动转换为 RawBar）
bars = manager.get_raw_bars(
    symbol="000001",  # 支持多种格式
    freq=Freq.D,
    sdt="20200101",
    edt="20231231"
)
print(f"获取到 {len(bars)} 根K线")

# 获取分钟数据
bars_5min = manager.get_raw_bars(
    symbol="000001.SZ",
    freq=Freq.F5,
    sdt="20231201",
    edt="20231231"
)

# 获取标的列表
symbols = manager.get_symbols("A股")
print(f"共 {len(symbols)} 个标的")

# 获取实时行情
real_time_df = manager.get_real_time_quotes()

# 重采样K线数据
bars_weekly = manager.resample_bars(bars, target_freq=Freq.W, base_freq=Freq.D)
```

### 3. 与 CZSC 分析器集成

```python
from akshare.manager import AkShareDataManager
from modules.analyze import CZSCAnalyzer
from czsc.objects import Freq

# 创建数据管理器
data_manager = AkShareDataManager()

# 获取K线数据
bars = data_manager.get_raw_bars("000001", Freq.D, "20200101", "20231231")

# 创建分析器
analyzer = CZSCAnalyzer(symbol="000001.SZ", freq=Freq.D)

# 加载并分析
analyzer.load_bars(bars)

# 获取分析结果
bis = analyzer.get_bis()
print(f"识别出 {len(bis)} 笔")

fxs = analyzer.get_fxs()
print(f"识别出 {len(fxs)} 个分型")
```

### 4. 与策略模块集成

```python
from akshare.manager import AkShareDataManager
from modules.strategy import StrategyManager
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position

# 定义策略
class MyStrategy(CzscStrategyBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def positions(self):
        return []

# 创建数据管理器
data_manager = AkShareDataManager()

# 获取K线数据
bars = data_manager.get_raw_bars("000001", Freq.D, "20200101", "20231231")

# 创建策略管理器
strategy_manager = StrategyManager(strategy_class=MyStrategy)
strategy = strategy_manager.create_strategy(symbol="000001.SZ")

# 回放策略
trader = strategy_manager.replay(bars, res_path="./replay", sdt="20210101")
```

## API 参考

### base.py

#### `get_real_time_data() -> pd.DataFrame`
获取所有A股实时行情数据

#### `get_minute_data(stock_code: str, period: str = "1", adjust: str = "qfq") -> pd.DataFrame`
获取分钟级别数据
- `stock_code`: 股票代码，如 "sz000001"
- `period`: 周期，"1", "5", "15", "30", "60"
- `adjust`: 复权类型，"qfq"（前复权）, "hfq"（后复权）, ""（不复权）

#### `get_historical_data(stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame`
获取历史日线数据
- `stock_code`: 股票代码，如 "000001"
- `start_date`: 开始日期，格式：YYYYMMDD
- `end_date`: 结束日期，格式：YYYYMMDD
- `adjust`: 复权类型

#### `format_akshare_to_rawbar(df: pd.DataFrame, symbol: str, freq: Freq) -> List[RawBar]`
将 AkShare DataFrame 转换为 RawBar 列表

#### `normalize_stock_code(stock_code: str) -> str`
标准化股票代码格式

#### `get_akshare_code(stock_code: str) -> str`
将标准股票代码转换为 AkShare 需要的格式

### manager.py

#### `AkShareDataManager`
数据管理器类，提供与 `modules/data.py` 类似的接口

**主要方法：**
- `get_raw_bars()`: 获取K线数据并转换为 RawBar
- `get_symbols()`: 获取标的列表
- `get_real_time_quotes()`: 获取实时行情
- `format_kline()`: 格式化K线数据
- `resample_bars()`: 重采样K线数据
- `df_to_bars()`: DataFrame 转 RawBar
- `bars_to_df()`: RawBar 转 DataFrame

## 注意事项

1. **股票代码格式**：支持多种格式，会自动标准化
   - "000001" -> "000001.SZ"
   - "sz000001" -> "000001.SZ"
   - "000001.SZ" -> "000001.SZ" (保持不变)

2. **数据周期**：
   - 日线数据：使用 `get_historical_data()`
   - 分钟数据：使用 `get_minute_data()`
   - 其他周期：先获取日线数据，然后重采样

3. **复权处理**：
   - 默认使用前复权（"qfq"）
   - 可根据需要选择后复权（"hfq"）或不复权（""）

4. **错误处理**：
   - 所有函数都包含异常处理和日志记录
   - 失败时返回 None 或抛出异常

5. **性能考虑**：
   - AkShare 有请求频率限制，建议添加适当的延时
   - 大量数据获取时建议分批处理

## 与 modules 的对比

| 功能 | modules/data.py | akshare/manager.py |
|------|----------------|-------------------|
| 数据源 | research 数据源 | AkShare |
| 接口 | 类似 | 类似 |
| 代码格式 | 标准格式 | 自动转换 |
| 实时数据 | 不支持 | 支持 |
| 分钟数据 | 支持 | 支持 |

## 扩展说明

如果需要添加新的数据获取功能：

1. 在 `base.py` 中添加新的获取函数
2. 在 `manager.py` 中添加对应的封装方法
3. 确保数据格式符合 CZSC 的要求
4. 更新本 README 文档

