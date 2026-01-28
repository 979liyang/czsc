# CZSC 项目架构说明文档

## 目录

1. [项目概述](#项目概述)
2. [目录结构](#目录结构)
3. [核心模块说明](#核心模块说明)
4. [数据流](#数据流)
5. [模块依赖关系](#模块依赖关系)
6. [扩展指南](#扩展指南)

---

## 项目概述

CZSC（缠中说禅）是一个基于缠论技术分析理论的 Python 量化交易工具库。项目采用模块化设计，核心功能包括：

- **缠论分析**：分型、笔、中枢的自动识别
- **信号系统**：基于缠论结构生成交易信号
- **策略框架**：完整的策略开发和回测框架
- **数据连接**：支持多种数据源接入
- **可视化**：丰富的图表和数据分析工具

---

## 目录结构

```
npc-czsc/
├── czsc/                      # 核心库
│   ├── __init__.py           # 库入口，导出主要接口
│   ├── analyze.py            # 缠论分析核心（分型、笔识别）
│   ├── objects.py            # 数据对象定义（RawBar, BI, FX, Signal等）
│   ├── strategies.py         # 策略基类
│   ├── enum.py               # 枚举定义（Freq, Operate, Direction等）
│   ├── envs.py               # 环境变量配置
│   ├── connectors/           # 数据连接器
│   │   ├── research.py       # 研究数据源（最常用）
│   │   ├── ts_connector.py   # Tushare数据源
│   │   ├── jq_connector.py   # 聚宽数据源
│   │   ├── gm_connector.py   # 掘金量化
│   │   ├── tq_connector.py   # 天勤量化
│   │   ├── qmt_connector.py  # 迅投QMT
│   │   └── cooperation.py   # 合作数据源
│   ├── signals/              # 信号函数库
│   │   ├── bar.py            # K线相关信号
│   │   ├── cxt.py            # 缠论相关信号
│   │   ├── tas.py            # 技术分析信号
│   │   ├── vol.py            # 成交量信号
│   │   ├── pos.py            # 持仓相关信号
│   │   └── ...
│   ├── traders/              # 交易执行模块
│   │   ├── base.py           # CzscTrader基类
│   │   ├── cwc.py            # 客户端权重客户端
│   │   ├── rwc.py            # Redis权重客户端
│   │   ├── dummy.py          # 虚拟回测
│   │   ├── optimize.py      # 参数优化
│   │   └── performance.py    # 性能分析
│   ├── sensors/              # 传感器/研究工具
│   │   ├── cta.py            # CTA研究
│   │   ├── event.py          # 事件匹配
│   │   └── feature.py        # 特征选择
│   ├── features/             # 特征工程
│   │   ├── ret.py            # 收益特征
│   │   ├── tas.py            # 技术分析特征
│   │   └── vpf.py            # 价格特征
│   ├── utils/                # 工具函数
│   │   ├── bar_generator.py  # K线合成器
│   │   ├── cache.py          # 缓存管理
│   │   ├── calendar.py      # 交易日历
│   │   ├── trade.py          # 交易工具
│   │   ├── kline_quality.py  # K线质量检查
│   │   └── ...
│   ├── svc/                  # Streamlit可视化组件
│   │   ├── base.py           # 基础功能
│   │   ├── returns.py        # 收益分析组件
│   │   ├── correlation.py    # 相关性分析
│   │   ├── factor.py         # 因子分析
│   │   ├── backtest.py       # 回测组件
│   │   └── ...
│   └── fsa/                  # 飞书相关功能
│       ├── bi_table.py        # 飞书表格
│       └── ...
│
├── modules/                  # 封装模块（简化调用）
│   ├── analyze.py            # 缠论分析封装
│   ├── trading.py            # 交易管理封装
│   ├── strategy.py           # 策略管理封装
│   ├── data.py               # 数据管理封装
│   └── utils.py              # 工具函数封装
│
├── examples/                 # 示例代码
│   ├── 30分钟笔非多即空.py   # 经典策略示例
│   ├── signals_dev/          # 信号开发示例
│   ├── develop/              # 开发示例
│   └── test_offline/         # 离线测试
│
├── akshare/                  # AkShare数据源集成
│   ├── database.py           # 数据库管理
│   ├── fetch_data.py         # 数据获取
│   ├── store_data.py         # 数据存储
│   └── czsc_adapter.py       # CZSC适配器
│
├── test/                     # 单元测试
│   ├── test_analyze.py       # 分析功能测试
│   ├── test_objects.py       # 对象测试
│   ├── test_strategy.py      # 策略测试
│   └── ...
│
├── docs/                     # 文档
│   ├── source/               # Sphinx文档源
│   └── ...
│
├── requirements.txt          # 依赖列表
├── setup.py                  # 安装脚本
├── README.md                 # 项目说明
├── USAGE_GUIDE.md            # 使用指南（本文档的补充）
└── PROJECT_ARCHITECTURE.md   # 架构说明（本文档）
```

---

## 核心模块说明

### 1. czsc/analyze.py - 缠论分析核心

**职责**：实现缠论的分型和笔识别算法

**核心类**：
- `CZSC`: 缠论分析主类
  - 输入：RawBar列表
  - 输出：分型列表、笔列表、中枢列表

**关键方法**：
- `check_fx()`: 检查分型
- `check_bi()`: 检查笔
- `update()`: 更新新K线
- `to_echarts()`: 生成图表

**依赖**：
- `czsc.objects`: RawBar, NewBar, FX, BI
- `czsc.enum`: Mark, Direction

### 2. czsc/objects.py - 数据对象定义

**职责**：定义所有核心数据对象的结构

**核心对象**：
- `RawBar`: 原始K线数据
- `NewBar`: 去除包含关系后的K线
- `FX`: 分型对象
- `BI`: 笔对象
- `ZS`: 中枢对象
- `Signal`: 信号对象
- `Factor`: 因子对象
- `Event`: 事件对象
- `Position`: 持仓策略对象

**设计模式**：使用 `@dataclass` 定义数据类

### 3. czsc/strategies.py - 策略基类

**职责**：提供策略开发的基类和接口

**核心类**：
- `CzscStrategyBase`: 策略基类（抽象类）
  - 必须实现 `positions` 属性
  - 提供 `replay()` 方法进行回测
  - 提供 `save_positions()` 保存策略配置

**设计模式**：模板方法模式

### 4. czsc/traders/base.py - 交易执行

**职责**：执行策略，管理持仓，生成交易信号

**核心类**：
- `CzscTrader`: 交易者主类
  - 管理多周期K线合成
  - 计算信号
  - 执行交易逻辑
  - 记录交易历史

**关键组件**：
- `BarGenerator`: K线合成器
- `CzscSignals`: 信号计算器

### 5. czsc/connectors/ - 数据连接器

**职责**：从各种数据源获取K线数据并转换为RawBar格式

**统一接口**：
```python
def get_raw_bars(symbol, freq, sdt, edt, **kwargs) -> List[RawBar]
```

**支持的数据源**：
- `research`: 研究数据源（最常用，支持多种数据）
- `ts_connector`: Tushare
- `jq_connector`: 聚宽
- `gm_connector`: 掘金量化
- `tq_connector`: 天勤量化
- `qmt_connector`: 迅投QMT

### 6. czsc/signals/ - 信号函数库

**职责**：提供各种技术分析信号函数

**信号函数规范**：
```python
def signal_name(czsc: CZSC, **kwargs) -> Dict[str, str]:
    """信号函数
    
    :param czsc: CZSC分析对象
    :param kwargs: 其他参数
    :return: 信号字典，格式为 {freq_name_signal_value: value}
    """
    s = {}
    # 计算信号
    return s
```

**信号命名规范**：
- 格式：`{freq}_{name}_{value}`
- 示例：`30分钟_D1_表里关系V230101_向上_任意_任意_0`

### 7. czsc/utils/ - 工具函数

**职责**：提供各种工具函数

**主要模块**：
- `bar_generator.py`: K线合成器
- `cache.py`: 缓存管理
- `calendar.py`: 交易日历
- `trade.py`: 交易工具函数
- `kline_quality.py`: K线质量检查

---

## 数据流

### 1. 数据获取流程

```
数据源 → connectors → RawBar列表 → BarGenerator → 多周期K线
```

### 2. 分析流程

```
RawBar → CZSC → 分型识别 → 笔识别 → 中枢识别
```

### 3. 信号计算流程

```
CZSC对象 → 信号函数 → Signal字典 → Factor → Event → Position
```

### 4. 交易执行流程

```
Position → CzscTrader → 信号计算 → 事件匹配 → 交易执行 → 持仓管理
```

### 5. 完整流程示例

```python
# 1. 获取数据
bars = research.get_raw_bars(symbol, freq, sdt, edt)

# 2. 合成多周期K线
bg = BarGenerator(base_freq, freqs)
for bar in bars:
    bg.update(bar)

# 3. 缠论分析
czsc = CZSC(bg.bars[base_freq])

# 4. 计算信号
cs = CzscSignals(bg=bg, signals_config=signals_config)

# 5. 执行策略
trader = CzscTrader(bg=bg, positions=positions)
trader.update(new_bar)
```

---

## 模块依赖关系

### 核心依赖图

```
czsc.objects (基础对象)
    ↑
    ├── czsc.analyze (分析模块)
    ├── czsc.traders (交易模块)
    ├── czsc.strategies (策略模块)
    └── czsc.signals (信号模块)
        ↑
        └── czsc.connectors (数据连接)
```

### 详细依赖

1. **analyze.py** 依赖：
   - `czsc.objects`: RawBar, NewBar, FX, BI
   - `czsc.enum`: Mark, Direction, Freq
   - `czsc.utils.echarts_plot`: 图表生成

2. **traders/base.py** 依赖：
   - `czsc.analyze`: CZSC
   - `czsc.objects`: Position, Signal, Event
   - `czsc.utils.bar_generator`: BarGenerator
   - `czsc.traders.sig_parse`: 信号解析

3. **strategies.py** 依赖：
   - `czsc.traders.base`: CzscTrader
   - `czsc.objects`: Position, Event
   - `czsc.traders.sig_parse`: 信号配置解析

4. **signals/** 依赖：
   - `czsc.analyze`: CZSC
   - `czsc.objects`: Signal
   - `czsc.enum`: Freq

---

## 扩展指南

### 1. 添加新的数据连接器

在 `czsc/connectors/` 目录下创建新文件：

```python
# czsc/connectors/my_connector.py
from czsc.objects import RawBar, Freq
from typing import List

def get_raw_bars(symbol: str, freq: Freq, sdt: str, edt: str, **kwargs) -> List[RawBar]:
    """从自定义数据源获取K线数据
    
    :param symbol: 标的代码
    :param freq: K线周期
    :param sdt: 开始日期
    :param edt: 结束日期
    :return: RawBar列表
    """
    # 实现数据获取逻辑
    bars = []
    # ... 转换为RawBar格式
    return bars
```

### 2. 添加新的信号函数

在 `czsc/signals/` 目录下创建或修改文件：

```python
# czsc/signals/my_signals.py
from czsc.analyze import CZSC
from typing import Dict

def my_signal_V001(czsc: CZSC, di: int = 1, **kwargs) -> Dict[str, str]:
    """自定义信号函数
    
    :param czsc: CZSC分析对象
    :param di: 倒数第几笔
    :return: 信号字典
    """
    s = {}
    freq = czsc.freq.value
    
    if len(czsc.finished_bis) >= di:
        bi = czsc.finished_bis[-di]
        # 计算信号逻辑
        s[f"{freq}_自定义信号V001_值"] = "信号值"
    
    return s
```

### 3. 创建自定义策略

```python
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, Event

class MyCustomStrategy(CzscStrategyBase):
    """自定义策略"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化参数
    
    @property
    def positions(self):
        """返回持仓策略列表"""
        # 构建策略逻辑
        return [position]
```

### 4. 扩展可视化组件

在 `czsc/svc/` 目录下添加新组件：

```python
# czsc/svc/my_component.py
import streamlit as st
import pandas as pd

def show_my_analysis(data: pd.DataFrame):
    """自定义分析组件
    
    :param data: 数据DataFrame
    """
    st.title("我的分析")
    # 实现可视化逻辑
    st.plotly_chart(fig)
```

---

## 设计原则

### 1. 模块化设计

- 每个模块职责单一
- 模块间通过接口交互
- 便于测试和维护

### 2. 数据驱动

- 所有分析基于RawBar数据
- 信号、因子、事件都是数据对象
- 策略配置可序列化为JSON

### 3. 可扩展性

- 支持自定义信号函数
- 支持自定义数据源
- 支持自定义策略

### 4. 向后兼容

- API变更保持兼容
- 使用deprecated标记废弃功能
- 提供迁移指南

---

## 性能考虑

### 1. 缓存策略

- K线数据缓存
- 信号计算结果缓存
- 使用 `@disk_cache` 装饰器

### 2. 批量处理

- 支持批量获取数据
- 支持批量回测
- 使用多进程并行处理

### 3. 内存管理

- 限制K线数量（max_bi_num）
- 及时清理缓存
- 使用生成器处理大数据

---

## 测试策略

### 1. 单元测试

- 每个核心模块都有对应测试
- 测试文件位于 `test/` 目录
- 使用 pytest 框架

### 2. 集成测试

- 测试完整的数据流
- 测试策略回测流程
- 测试多数据源兼容性

### 3. 性能测试

- 测试大数据量处理
- 测试并发性能
- 测试内存使用

---

## 总结

CZSC项目采用清晰的模块化架构，核心功能分离明确，便于理解、使用和扩展。通过本文档，您可以：

1. 快速了解项目整体结构
2. 理解各模块的职责和关系
3. 知道如何扩展新功能
4. 掌握数据流转过程

更多使用细节请参考 `USAGE_GUIDE.md`。
