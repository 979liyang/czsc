# AkShare 数据源使用指南

本模块提供了基于 AkShare 的股票数据获取、存储和 CZSC 对接功能。

## 功能概述

1. **数据获取**：使用 AkShare 获取上证、深证、创业板股票的历史数据
2. **数据存储**：将数据存储到 MySQL 数据库
3. **CZSC 对接**：从 MySQL 读取数据并转换为 CZSC 所需的 RawBar 格式

## 快速开始

### 1. 初始化数据库

```python
from czsc.akshare.database import init_database

# 初始化数据库（创建表）
init_database()
```

### 2. 获取并存储股票数据

```python
from czsc.akshare.store_data import sync_all_stocks

# 同步所有股票数据（上证、深证、创业板）
results = sync_all_stocks(
    markets=['sh', 'sz', 'cyb'],  # 市场列表
    start_date='20230101',        # 开始日期
    end_date='20231231',          # 结束日期
    adjust='qfq',                 # 复权类型：qfq-前复权，hfq-后复权
    freq='D',                     # K线周期：D-日线
    delay=0.1                     # 请求延迟（秒）
)
```

### 3. 从数据库读取数据并用于 CZSC

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.objects import Freq
from czsc.analyze import CZSC

# 从数据库获取K线数据
bars = get_raw_bars(
    symbol='000001.SZ',
    freq=Freq.D,
    sdt='20230101',
    edt='20231231',
    fq='前复权'
)

# 使用 CZSC 分析
c = CZSC(bars)
print(f"识别出 {len(c.bi_list)} 笔")
```

## 命令行使用

### 获取并存储数据

```bash
# 获取所有市场的数据
python -m czsc.akshare.main --action fetch --markets sh sz cyb --start-date 20230101 --end-date 20231231

# 只获取上证股票
python -m czsc.akshare.main --action fetch --markets sh --start-date 20230101

# 测试适配器
python -m czsc.akshare.main --action test
```

## 详细功能

### 1. 数据获取 (fetch_data.py)

- `get_stock_list_by_market()`: 获取按市场分类的股票列表
- `get_stock_info(code)`: 获取股票基本信息
- `fetch_historical_data()`: 获取历史日线数据
- `fetch_minute_data()`: 获取分钟数据
- `batch_fetch_stocks()`: 批量获取股票数据

### 2. 数据存储 (store_data.py)

- `store_stock_info()`: 存储股票基本信息
- `store_kline_data()`: 存储K线数据
- `batch_store_stocks()`: 批量存储股票数据
- `sync_all_stocks()`: 同步所有股票数据

### 3. CZSC 适配器 (czsc_adapter.py)

提供与 `czsc.connectors` 类似的接口：

- `get_symbols()`: 获取标的列表
- `get_raw_bars()`: 获取K线数据并转换为 RawBar
- `get_latest_bar()`: 获取最新K线
- `check_data_availability()`: 检查数据可用性

### 4. 数据库模型 (database.py)

- `StockInfo`: 股票基本信息表
- `StockKline`: K线数据表
- `DatabaseManager`: 数据库管理器

## 对接 CZSC 功能模块

### 1. 基础缠论分析

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.analyze import CZSC
from czsc.objects import Freq

bars = get_raw_bars('000001.SZ', Freq.D, '20220101', '20231231')
c = CZSC(bars)
print(f"笔数量: {len(c.bi_list)}")
print(f"分型数量: {len(c.fx_list)}")
```

### 2. 多周期分析

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.objects import Freq

# 获取不同周期的数据
daily_bars = get_raw_bars('000001.SZ', Freq.D, '20220101', '20231231')
weekly_bars = get_raw_bars('000001.SZ', Freq.W, '20220101', '20231231')
```

### 3. 交易模块集成

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.traders import CzscTrader, BarGenerator
from czsc.objects import Freq

bars = get_raw_bars('000001.SZ', Freq.D, '20220101', '20231231')
bg = BarGenerator(base_freq=Freq.D, freqs=[Freq.D, Freq.W])
for bar in bars:
    bg.update(bar)
```

### 4. 策略模块集成

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.strategies import CzscStrategyBase
from czsc.objects import Freq

bars = get_raw_bars('000001.SZ', Freq.D, '20220101', '20231231')

# 使用自定义策略
class MyStrategy(CzscStrategyBase):
    # 实现策略逻辑
    pass

strategy = MyStrategy(symbol='000001.SZ')
trader = strategy.replay(bars)
```

### 5. 信号分析

```python
from czsc.akshare.czsc_adapter import get_raw_bars
from czsc.analyze import CZSC
from czsc.objects import Freq

bars = get_raw_bars('000001.SZ', Freq.D, '20220101', '20231231')
c = CZSC(bars, get_signals=your_signal_function)

# 获取信号
if c.signals:
    for signal, value in c.signals.items():
        print(f"{signal}: {value}")
```

## 数据库配置

默认数据库连接字符串：
```
mysql+mysqlconnector://root:root123456@localhost:3306/kylin
```

可以通过环境变量或直接传入修改：

```python
from czsc.akshare.database import get_db_manager

db_manager = get_db_manager(
    database_uri="mysql+mysqlconnector://user:password@host:port/database"
)
```

## 注意事项

1. **请求频率限制**：AkShare 有请求频率限制，建议设置适当的延迟（delay 参数）
2. **数据完整性**：首次获取数据可能需要较长时间，建议分批获取
3. **数据更新**：定期更新数据以保持最新
4. **错误处理**：所有函数都包含异常处理，失败时会记录日志

## 示例脚本

运行完整示例：

```bash
python -m czsc.akshare.czsc_integration_examples
```

该脚本展示了：
- 基础缠论分析
- 多周期分析
- 信号分析
- 批量分析
- 交易模块集成
- 策略模块集成
- 数据质量检查

## 文件结构

```
akshare/
├── __init__.py              # 模块入口
├── base.py                  # 基础数据获取函数
├── manager.py              # 数据管理器类
├── database.py             # 数据库模型和管理
├── fetch_data.py           # 数据获取脚本
├── store_data.py           # 数据存储脚本
├── czsc_adapter.py         # CZSC 适配器
├── main.py                 # 主程序入口
├── czsc_integration_examples.py  # 集成示例
├── README.md               # 基础说明
└── README_USAGE.md         # 使用指南（本文件）
```

## 常见问题

### Q: 如何只获取特定市场的股票？

A: 使用 `markets` 参数：
```python
sync_all_stocks(markets=['sh'])  # 只获取上证股票
```

### Q: 如何更新已有数据？

A: 使用 `replace=True` 参数：
```python
store_kline_data(symbol, df, freq, adjust, replace=True)
```

### Q: 如何检查数据是否已存在？

A: 使用 `check_data_availability()`：
```python
availability = check_data_availability('000001.SZ', Freq.D, '前复权')
if availability['available']:
    print(f"数据范围: {availability['min_date']} - {availability['max_date']}")
```

