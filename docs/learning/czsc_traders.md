# CZSC交易模块学习文档

## 概述

本文档记录czsc.traders模块的核心类和使用方法，包括CzscTrader、CzscSignals、BarGenerator等。

## 核心类

### 1. BarGenerator（K线合成器）

**定义位置**: `czsc.utils.bar_generator.BarGenerator`

**用途**: 从基础周期K线合成多周期K线

**关键属性**:
- `base_freq: str` - 基础周期（如"1分钟"）
- `freqs: List[str]` - 需要合成的周期列表（如["5分钟", "30分钟", "日线"]）
- `symbol: str` - 标的代码
- `end_dt: datetime` - 最后一根K线的时间
- `bars: dict` - 各周期的K线数据，格式：{freq: List[RawBar]}

**关键方法**:
- `init_freq_bars(freq, bars)` - 初始化某个周期的K线序列
- `update(bar: RawBar)` - 输入基础周期K线，更新各周期K线
- `_update_freq(bar, freq)` - 更新指定周期的K线

**使用示例**:
```python
from czsc.utils.bar_generator import BarGenerator
from czsc.objects import RawBar

# 创建BarGenerator
bg = BarGenerator(base_freq="1分钟", freqs=["5分钟", "30分钟", "日线"])

# 初始化基础周期K线
bg.init_freq_bars("1分钟", bars_1min)

# 更新K线（逐根输入）
for bar in new_bars:
    bg.update(bar)
```

### 2. CzscSignals（信号计算器）

**定义位置**: `czsc.traders.base.CzscSignals`

**用途**: 多级别信号计算，封装信号计算逻辑

**关键属性**:
- `bg: BarGenerator` - K线合成器
- `symbol: str` - 标的代码
- `base_freq: str` - 基础周期
- `freqs: List[str]` - 所有周期列表
- `kas: dict` - 各周期的CZSC对象，格式：{freq: CZSC}
- `s: OrderedDict` - 信号字典
- `signals_config: List[dict]` - 信号配置列表
- `cache: OrderedDict` - 信号计算缓存

**关键方法**:
- `get_signals_by_conf()` - 通过信号配置获取信号
- `update_signals(bar: RawBar)` - 更新信号
- `take_snapshot(file_html, width, height)` - 生成交易快照

**信号配置格式**:
```python
signals_config = [
    {
        'name': 'czsc.signals.tas_ma_base_V221101',
        'freq': '日线',
        'di': 1,
        'ma_type': 'SMA',
        'timeperiod': 5
    },
    {
        'name': 'czsc.signals.cxt_bi_status_V230101',
        'freq': '30分钟',
        'di': 1
    }
]
```

**使用示例**:
```python
from czsc.traders.base import CzscSignals
from czsc.utils.bar_generator import BarGenerator

# 创建BarGenerator
bg = BarGenerator(base_freq="1分钟", freqs=["5分钟", "30分钟", "日线"])

# 创建CzscSignals
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 更新信号
cs.update_signals(bar)

# 获取信号
signals = dict(cs.s)
```

### 3. CzscTrader（交易执行器）

**定义位置**: `czsc.traders.base.CzscTrader`

**用途**: 执行策略交易逻辑，管理持仓和信号

**关键属性**:
- `bg: BarGenerator` - K线合成器
- `positions: List[Position]` - 持仓策略列表
- `signals_config: List[dict]` - 信号配置
- `cs: CzscSignals` - 信号计算器

**关键方法**:
- `on_bar(bar: RawBar)` - 处理新K线，更新信号和持仓
- `on_sig(sig: dict)` - 处理信号，更新持仓
- `take_snapshot(file_html)` - 生成交易快照

**使用示例**:
```python
from czsc.traders.base import CzscTrader
from czsc.objects import Position

# 创建持仓策略
positions = [pos1, pos2, pos3]

# 创建CzscTrader
trader = CzscTrader(
    bg=bg,
    positions=positions,
    signals_config=signals_config
)

# 处理K线
for bar in bars:
    trader.on_bar(bar)
```

## 数据流转

```
RawBar → BarGenerator → 多周期K线 → CZSC对象 → CzscSignals → 信号字典
                                                              ↓
                                                         CzscTrader → 持仓操作
```

## 关键设计要点

1. **多周期支持**: BarGenerator可以从基础周期合成多个周期的K线
2. **信号缓存**: CzscSignals使用cache缓存计算结果，避免重复计算
3. **事件驱动**: CzscTrader通过on_bar和on_sig方法处理事件
4. **配置驱动**: 信号计算通过signals_config配置，灵活可扩展

## 使用建议

1. **初始化顺序**: BarGenerator → CzscSignals → CzscTrader
2. **数据更新**: 逐根K线更新，确保时间顺序
3. **信号配置**: 合理配置signals_config，避免重复计算
4. **缓存利用**: 充分利用cache字段，提升性能
