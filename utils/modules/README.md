# CZSC 模块封装说明

本模块提供了对 `czsc` 库功能的封装，使调用更加便捷和统一。

## 模块结构

```
modules/
├── __init__.py          # 模块入口
├── analyze.py           # 缠论分析模块
├── trading.py           # 交易管理模块
├── strategy.py          # 策略管理模块
├── data.py              # 数据管理模块
├── utils.py             # 工具函数模块
└── README.md           # 说明文档
```

## 使用示例

### 1. 缠论分析 (analyze.py)

```python
from modules.analyze import CZSCAnalyzer
from czsc.objects import RawBar, Freq
from czsc.connectors import research

# 创建分析器
analyzer = CZSCAnalyzer(symbol="000001.SH", freq=Freq.D)

# 获取K线数据
bars = research.get_raw_bars("000001.SH", freq=Freq.D, sdt="20200101", edt="20230101")

# 加载并分析
analyzer.load_bars(bars)

# 获取笔列表
bis = analyzer.get_bis()
print(f"共识别出 {len(bis)} 笔")

# 获取分型列表
fxs = analyzer.get_fxs()
print(f"共识别出 {len(fxs)} 个分型")

# 获取最后一笔
last_bi = analyzer.get_last_bi()
if last_bi:
    print(f"最后一笔方向：{last_bi.direction.value}")

# 生成图表
chart = analyzer.to_echarts()
analyzer.open_in_browser()
```

### 2. 交易管理 (trading.py)

```python
from modules.trading import TradingManager
from czsc.objects import RawBar, Position, Event, Factor, Signal, Operate, Freq
from czsc.connectors import research

# 创建交易管理器
manager = TradingManager(symbol="000001.SH", base_freq=Freq.D, freqs=["日线", "周线"])

# 获取K线数据
bars = research.get_raw_bars("000001.SH", freq=Freq.D, sdt="20200101", edt="20230101")

# 初始化K线合成器
manager.init_bar_generator(bars, market="A")

# 创建持仓策略
opens = [
    Event(
        operate=Operate.LO,
        factors=[
            Factor(
                signals_all=[Signal(signal="日线_D1_表里关系V230101_向上_任意_任意_0")]
            )
        ]
    )
]
positions = [Position(name="测试策略", symbol="000001.SH", opens=opens)]

# 初始化交易者
manager.init_trader(positions)

# 更新交易状态
for bar in bars[-10:]:
    manager.update(bar)

# 获取当前信号
signals = manager.get_signals()
print(f"当前信号：{signals}")

# 获取操作记录
operates = manager.get_operates()
print(f"共 {len(operates)} 次操作")
```

### 3. 策略管理 (strategy.py)

```python
from modules.strategy import StrategyManager
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, RawBar
from czsc.connectors import research

# 定义策略类
class MyStrategy(CzscStrategyBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def positions(self):
        # 返回持仓策略列表
        return []

# 创建策略管理器
strategy_manager = StrategyManager(strategy_class=MyStrategy)

# 创建策略实例
strategy = strategy_manager.create_strategy(symbol="000001.SH")

# 获取信号配置
signals_config = strategy_manager.get_signals_config()

# 获取K线数据
bars = research.get_raw_bars("000001.SH", freq=strategy.base_freq, sdt="20200101", edt="20230101")

# 回放策略
trader = strategy_manager.replay(bars, res_path="./replay", sdt="20210101")

# 保存持仓策略
strategy_manager.save_positions("./positions")
```

### 4. 数据管理 (data.py)

```python
from modules.data import DataManager
from czsc.objects import Freq
import pandas as pd

# 创建数据管理器
data_manager = DataManager()

# 从研究数据源获取K线数据
bars = data_manager.get_raw_bars("000001.SH", freq=Freq.D, sdt="20200101", edt="20230101")

# 获取标的列表
symbols = data_manager.get_symbols("A股主要指数")
print(f"共 {len(symbols)} 个标的")

# 格式化DataFrame为K线数据
df = pd.DataFrame({
    'dt': ['2023-01-01', '2023-01-02'],
    'open': [100, 101],
    'close': [101, 102],
    'high': [102, 103],
    'low': [99, 100],
    'vol': [1000000, 1100000],
    'amount': [101000000, 112200000]
})
bars = data_manager.format_kline(df, freq=Freq.D)

# 重采样K线数据
bars_weekly = data_manager.resample_bars(bars, target_freq=Freq.W, base_freq=Freq.D)

# 创建K线合成器
bg = data_manager.create_bar_generator(base_freq=Freq.D, freqs=["周线", "月线"])

# DataFrame和RawBar互转
df = data_manager.bars_to_df(bars)
bars = data_manager.df_to_bars(df, symbol="000001.SH", freq=Freq.D)
```

### 5. 工具函数 (utils.py)

```python
from modules.utils import CZSCUtils

# 排序K线周期
freqs = CZSCUtils.sort_freqs(["日线", "周线", "月线", "1分钟"])
print(freqs)

# 四舍五入
result = CZSCUtils.round_number(3.14159, digits=2)
print(result)  # 3.14

# JSON文件操作
data = {"key": "value"}
CZSCUtils.save_json(data, "./data.json")
loaded_data = CZSCUtils.load_json("./data.json")

# 对象序列化
obj = {"test": "object"}
CZSCUtils.save_dill(obj, "./obj.pkl")
loaded_obj = CZSCUtils.load_dill("./obj.pkl")

# 缓存管理
cache_path = CZSCUtils.get_cache_home_path()
cache_size = CZSCUtils.get_cache_size()
CZSCUtils.clear_all_cache()

# 交易日相关
is_trading = CZSCUtils.is_trading_day("20230101")
next_day = CZSCUtils.get_next_trading_day("20230101")
prev_day = CZSCUtils.get_prev_trading_day("20230101")
trading_days = CZSCUtils.get_trading_days_list("20230101", "20230131")

# 权重调整
weights = {"000001.SH": 0.5, "000002.SH": 0.6}
adjusted = CZSCUtils.adjust_weights(weights, max_weight=1.0)

# 环境变量
min_bi_len = CZSCUtils.get_min_bi_len()
max_bi_num = CZSCUtils.get_max_bi_num()
verbose = CZSCUtils.get_verbose()
```

## 模块说明

### analyze.py - 缠论分析模块
- `CZSCAnalyzer`: 缠论分析器封装类
  - 提供分型、笔识别等核心分析功能
  - 支持图表生成和浏览器展示

### trading.py - 交易管理模块
- `TradingManager`: 交易管理器
  - 提供交易信号生成、交易执行等功能
  - 支持多周期K线合成

### strategy.py - 策略管理模块
- `StrategyManager`: 策略管理器
  - 提供策略创建、回测、评估等功能
  - 支持策略回放和结果保存

### data.py - 数据管理模块
- `DataManager`: 数据管理器
  - 提供数据获取、处理、转换等功能
  - 支持多种数据源和格式转换

### utils.py - 工具函数模块
- `CZSCUtils`: 工具函数封装类
  - 提供文件操作、缓存管理、交易日计算等功能
  - 提供环境变量访问接口

## 注意事项

1. 所有模块都使用 `loguru.logger` 进行日志记录
2. 所有方法都包含异常处理和日志记录
3. 遵循项目的编码规范（中文注释、120字符行宽等）
4. 函数复杂度控制在30行以内

## 扩展说明

如果需要添加新的功能模块，可以：

1. 在 `modules` 目录下创建新的 Python 文件
2. 实现相应的封装类或函数
3. 在 `__init__.py` 中导出新模块
4. 更新本 README 文档

