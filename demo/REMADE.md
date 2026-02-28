# 数据库设计

## 核心概念

### 1. 数据对象

#### RawBar（原始K线）
```python
from czsc.objects import RawBar, Freq
from datetime import datetime

bar = RawBar(
    symbol="000001.SH",
    id=1,
    dt=datetime(2024, 1, 1),
    freq=Freq.D,  # 日线
    open=3000.0,
    close=3050.0,
    high=3060.0,
    low=2990.0,
    vol=1000000,
    amount=3000000000
)
```

#### NewBar（去除包含关系后的K线）
经过包含关系处理后的K线，是分型识别的基础。

#### FX（分型）
- **顶分型**：中间K线的高点和低点都高于左右两根K线
- **底分型**：中间K线的高点和低点都低于左右两根K线

#### BI（笔）
由相邻的顶分型和底分型连接而成，是缠论分析的基本单位。

#### ZS（中枢）
价格在一定区间内的震荡，是判断趋势和买卖点的重要依据。

### 2. 信号系统

CZSC 采用 **信号-因子-事件-交易** 的逻辑体系：

```
信号(Signal) → 因子(Factor) → 事件(Event) → 持仓(Position) → 交易(Operate)
```

- **Signal（信号）**：最基础的技术指标，如"30分钟_D1_表里关系V230101_向上"
- **Factor（因子）**：信号的组合，可以包含多个信号
- **Event（事件）**：由因子组成的交易事件，如开多、开空
- **Position（持仓）**：包含多个开仓和平仓事件的持仓策略
- **Operate（操作）**：具体的交易操作，如开多、开空、平多、平空

### 3. 时间周期

CZSC 支持多种时间周期：

```python
from czsc.enum import Freq

# 支持的周期
Freq.F1    # 1分钟
Freq.F5    # 5分钟
Freq.F15   # 15分钟
Freq.F30   # 30分钟
Freq.F60   # 60分钟
Freq.D     # 日线
Freq.W     # 周线
Freq.M     # 月线
```

### 4. 交易操作

```python
from czsc.enum import Operate, Direction

# 操作类型
Operate.LO   # 开多 买入（先买开仓，看涨）
Operate.LC   # 平多 卖出（卖出平仓，了结多头）
Operate.SO   # 开空 卖出（先卖开仓，看跌）
Operate.SE   # 平空 买入（买入平仓，了结空头）
Operate.HO   # 持多 持有（已持有买入的多头仓位）
Operate.HS   # 持空 持有（已持有卖出的空头仓位）

开多 = 买，开空 = 卖（开仓方向决定多空）
平多 = 卖，平空 = 买（平仓是与开仓相反的操作）
持多/持空 = 持有仓位，不新开不平仓

# 方向
Direction.Up     # 向上
Direction.Down   # 向下
```

## 快速开始

### 示例 1：基础缠论分析 examples/analyze.py
### 示例 2：多周期分析 examples/barGenerator.py
### 示例 3：信号计算 examples/signals.py

## 核心模块详解

### 1. analyze.py - 缠论分析核心

`CZSC` 类是缠论分析的核心类，负责分型和笔的识别。

#### 主要方法

```python
from czsc.analyze import CZSC

czsc = CZSC(bars)

# 属性
czsc.bars_raw          # 原始K线列表
czsc.bars_ubi          # 未完成笔的K线列表
czsc.fxs               # 分型列表
czsc.finished_bis      # 已完成的笔列表
czsc.bi_list           # 所有笔列表（包括未完成）
czsc.ubi               # 未完成的笔
czsc.last_bi_extend    # 最后一笔是否在延伸

# 方法
czsc.update(bar)       # 更新新的K线
czsc.to_echarts()      # 生成ECharts图表
czsc.open_in_browser() # 在浏览器中打开图表
```

### 2. objects.py - 数据对象定义

定义了所有核心数据对象的结构。

#### 主要对象

- **RawBar**：原始K线数据
- **NewBar**：去除包含关系后的K线
- **FX**：分型对象
- **BI**：笔对象
- **ZS**：中枢对象
- **Signal**：信号对象
- **Factor**：因子对象
- **Event**：事件对象
- **Position**：持仓策略对象

#### Signal 对象示例

```python
from czsc.objects import Signal

# Signal 的格式：{freq}_{name}_{value}
signal = Signal(
    key="30分钟_D1_表里关系V230101_向上_任意_任意_0",
    value="向上"
)

# Signal 会自动解析
print(signal.freq)      # "30分钟"
print(signal.name)      # "D1_表里关系V230101"
print(signal.value)     # "向上"
```

#### Position 对象示例

```python
from czsc.objects import Position, Event, Operate

# 创建开多事件
open_long = Event(
    operate=Operate.LO,
    signals_all=[],  # 必须全部满足的信号
    signals_any=[],  # 至少满足一个的信号
    signals_not=[],  # 不能出现的信号
    factors=[        # 因子列表
        {
            "signals_all": ["30分钟_D1_表里关系V230101_向上_任意_任意_0"],
            "signals_any": [],
            "signals_not": []
        }
    ]
)

# 创建持仓策略
position = Position(
    name="30分钟笔非多即空",
    symbol="000001.SH",
    opens=[open_long],  # 开仓事件列表
    exits=[],           # 平仓事件列表
    interval=3600 * 4,  # 信号更新间隔（秒）
    timeout=16 * 30,    # 持仓超时时间（分钟）
    stop_loss=500       # 止损点数
)
```

### 3. strategies.py - 策略基类

`CzscStrategyBase` 是策略开发的基类。

#### 创建自定义策略

```python
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, Event, Operate

class MyStrategy(CzscStrategyBase):
    """自定义策略"""
    
    @property
    def positions(self):
        """返回持仓策略列表"""
        opens = [
            {
                "operate": "开多",
                "signals_all": [],
                "signals_any": [],
                "signals_not": [],
                "factors": [
                    {
                        "signals_all": ["30分钟_D1_表里关系V230101_向上_任意_任意_0"],
                        "signals_any": [],
                        "signals_not": []
                    }
                ]
            }
        ]
        
        pos = Position(
            name="我的策略",
            symbol=self.symbol,
            opens=[Event.load(x) for x in opens],
            exits=[],
            interval=3600 * 4,
            timeout=16 * 30,
            stop_loss=500
        )
        return [pos]

# 使用策略
strategy = MyStrategy(symbol="000001.SH")
print(f"K线周期：{strategy.freqs}")
print(f"信号配置：{strategy.signals_config}")
```

### 4. traders/base.py - 交易执行

`CzscTrader` 是策略执行的核心类。

#### 主要功能

- 多周期K线合成
- 信号计算
- 持仓管理
- 交易执行
- 回测支持

#### 使用示例

```python
from czsc.traders import CzscTrader
from czsc.strategies import CzscStrategyBase
from czsc.objects import RawBar, Freq
from czsc.connectors import research

# 1. 创建策略
class MyStrategy(CzscStrategyBase):
    @property
    def positions(self):
        # ... 策略定义 ...
        return [position]

# 2. 初始化策略
strategy = MyStrategy(symbol="000001.SH")

# 3. 获取K线数据
bars = research.get_raw_bars(
    symbol="000001.SH",
    freq=strategy.base_freq,
    sdt="20200101",
    edt="20231231"
)

# 4. 创建交易者
trader = strategy.replay(
    bars=bars,
    sdt="20210101",  # 回测开始日期
    res_path="./results"  # 结果保存路径
)

# 5. 查看结果
print(f"交易次数：{len(trader.operates)}")
print(f"最终收益：{trader.pairs['累计收益']}")
```

---

## 数据连接器

CZSC 支持多种数据源，通过 `czsc.connectors` 模块访问。

### 1. research - 研究数据源

最常用的数据连接器，支持多种数据获取方式。

### 2. ts_connector - Tushare 数据源

```python
from czsc.connectors.ts_connector import get_raw_bars
from czsc.objects import Freq

bars = get_raw_bars(
    symbol="000001.SH",
    freq=Freq.D,
    sdt="20200101",
    edt="20231231",
    fq="前复权"  # 前复权、后复权、不复权
)
```

### 3. jq_connector - 聚宽数据源

```python
from czsc.connectors.jq_connector import get_raw_bars
from czsc.objects import Freq

bars = get_raw_bars(
    symbol="000001.XSHG",
    freq=Freq.D,
    sdt="20200101",
    edt="20231231"
)
```

### 4. 其他连接器

- **gm_connector**：掘金量化
- **tq_connector**：天勤量化
- **qmt_connector**：迅投QMT
- **cooperation**：合作数据源

---

## 策略开发

### 1. 策略开发流程

1. **定义信号**：确定需要使用的信号函数
2. **构建因子**：组合信号形成因子
3. **定义事件**：用因子定义开仓和平仓事件
4. **创建持仓**：组合事件形成持仓策略
5. **编写策略类**：继承 `CzscStrategyBase`
6. **回测验证**：使用 `replay` 方法回测
7. **优化参数**：调整参数提升效果

### 2. 信号函数

CZSC 提供了丰富的信号函数，位于 `czsc.signals` 模块。

#### 常用信号函数

- **cxt_bi_status_V230101**：笔状态信号
- **tas_ma_base_V221101**：均线信号
- **bar_zfzd_V241013**：涨跌幅信号
- **vol_obv_V230101**：成交量信号

#### 查看可用信号

```python
from czsc.signals import *

# 查看信号函数列表
import czsc.signals as signals
print(dir(signals))
```

#### 自定义信号函数

### 3. 完整策略示例

```python
# -*- coding: utf-8 -*-
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, Event
from czsc.connectors import research
from pathlib import Path
from loguru import logger

def create_position(symbol, base_freq='30分钟', **kwargs):
    """创建持仓策略"""
    opens = [
        {
            "operate": "开多",
            "signals_all": [],
            "signals_any": [],
            "signals_not": [],
            "factors": [
                {
                    "signals_all": [f"{base_freq}_D1_表里关系V230101_向上_任意_任意_0"],
                    "signals_any": [],
                    "signals_not": [f"{base_freq}_D1_涨跌停V230331_涨停_任意_任意_0"],
                }
            ],
        },
        {
            "operate": "开空",
            "signals_all": [],
            "signals_any": [],
            "signals_not": [],
            "factors": [
                {
                    "signals_all": [f"{base_freq}_D1_表里关系V230101_向下_任意_任意_0"],
                    "signals_any": [],
                    "signals_not": [f"{base_freq}_D1_涨跌停V230331_跌停_任意_任意_0"],
                }
            ],
        },
    ]
    
    pos = Position(
        name=f"{base_freq}笔非多即空",
        symbol=symbol,
        opens=[Event.load(x) for x in opens],
        exits=[],
        interval=3600 * 4,
        timeout=16 * 30,
        stop_loss=500,
    )
    return pos

class MyStrategy(CzscStrategyBase):
    """我的策略"""
    
    @property
    def positions(self):
        """持仓策略列表"""
        return [
            create_position(self.symbol, base_freq='30分钟'),
            create_position(self.symbol, base_freq='60分钟'),
        ]

if __name__ == '__main__':
    # 配置日志
    results_path = Path("./results")
    results_path.mkdir(exist_ok=True)
    logger.add(results_path / "strategy.log", rotation="1 week")
    
    # 创建策略
    symbol = "000001.SH"
    strategy = MyStrategy(symbol=symbol)
    
    # 获取数据
    bars = research.get_raw_bars(
        symbol=symbol,
        freq=strategy.base_freq,
        sdt='20200101',
        edt='20231231'
    )
    
    # 回测
    trader = strategy.replay(
        bars=bars,
        sdt='20210101',
        res_path=results_path / "replay",
        refresh=True
    )
    
    # 保存策略
    strategy.save_positions(results_path / "positions")
```

---

## 回测与优化

### 1. 基础回测

```python
from czsc.traders import CzscTrader
from czsc.strategies import CzscStrategyBase

# 创建策略
strategy = MyStrategy(symbol="000001.SH")

# 获取数据
bars = research.get_raw_bars(...)

# 回测
trader = strategy.replay(
    bars=bars,
    sdt="20210101",  # 回测开始日期
    res_path="./results",
    refresh=True     # 是否刷新结果
)

# 查看结果
print(trader.pairs)  # 回测结果字典
```

### 2. 回测结果分析

```python
# 回测结果包含以下信息
trader.pairs['累计收益']      # 累计收益率
trader.pairs['最大回撤']      # 最大回撤
trader.pairs['年化收益']      # 年化收益率
trader.pairs['夏普比率']      # 夏普比率
trader.pairs['胜率']          # 胜率
trader.pairs['盈亏比']        # 盈亏比

# 交易记录
trader.operates  # 所有交易操作
trader.positions # 持仓记录
```

### 3. 参数优化

```python
from czsc.traders import OpensOptimize, ExitsOptimize

# 开仓优化
opens_opt = OpensOptimize(
    strategy=MyStrategy,
    symbols=["000001.SH", "000002.SH"],
    sdt="20200101",
    edt="20231231",
    params={
        'base_freq': ['30分钟', '60分钟', '日线'],
        'stop_loss': [300, 500, 700]
    }
)

results = opens_opt.optimize()
print(results)
```

### 4. 批量回测

```python
from czsc.traders import DummyBacktest
from czsc.connectors import research

# 获取股票列表
symbols = research.get_symbols('中证500成分股')[:10]

# 批量回测
backtest = DummyBacktest(
    strategy=MyStrategy,
    symbols=symbols,
    sdt="20200101",
    edt="20231231"
)

results = backtest.run()
print(results)
```

---

## 实战案例

### 案例 1：30分钟笔非多即空策略

完整代码见 `examples/30分钟笔非多即空.py`

```python
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, Event
from czsc.connectors import research

class Strategy30Min(CzscStrategyBase):
    @property
    def positions(self):
        opens = [
            {
                "operate": "开多",
                "factors": [{
                    "signals_all": ["30分钟_D1_表里关系V230101_向上_任意_任意_0"],
                    "signals_not": ["30分钟_D1_涨跌停V230331_涨停_任意_任意_0"],
                }]
            },
            {
                "operate": "开空",
                "factors": [{
                    "signals_all": ["30分钟_D1_表里关系V230101_向下_任意_任意_0"],
                    "signals_not": ["30分钟_D1_涨跌停V230331_跌停_任意_任意_0"],
                }]
            }
        ]
        
        pos = Position(
            name="30分钟笔非多即空",
            symbol=self.symbol,
            opens=[Event.load(x) for x in opens],
            exits=[],
            interval=3600 * 4,
            timeout=16 * 30,
            stop_loss=500
        )
        return [pos]
```

### 案例 2：多周期联立策略

```python
class MultiFreqStrategy(CzscStrategyBase):
    @property
    def positions(self):
        # 30分钟周期策略
        pos_30m = create_position(self.symbol, '30分钟')
        
        # 60分钟周期策略
        pos_60m = create_position(self.symbol, '60分钟')
        
        # 日线周期策略
        pos_d = create_position(self.symbol, '日线')
        
        return [pos_30m, pos_60m, pos_d]
```

### 案例 3：形态选股

```python
from czsc.connectors import research
from czsc.analyze import CZSC
from czsc.objects import Freq

def find_stocks_by_pattern():
    """根据形态选股"""
    symbols = research.get_symbols('中证500成分股')
    selected = []
    
    for symbol in symbols[:100]:  # 测试前100只
        try:
            bars = research.get_raw_bars(
                symbol=symbol,
                freq=Freq.D,
                sdt="20230101",
                edt="20231231"
            )
            
            czsc = CZSC(bars)
            
            # 判断条件：最后一笔向上，且幅度大于5%
            if czsc.finished_bis:
                last_bi = czsc.finished_bis[-1]
                if (last_bi.direction.value == "向上" and 
                    last_bi.power > 5.0):
                    selected.append(symbol)
                    print(f"选中：{symbol}")
        except Exception as e:
            continue
    
    return selected
```

---

## 最佳实践

### 1. 代码组织

```
project/
├── strategies/          # 策略目录
│   ├── __init__.py
│   ├── strategy1.py
│   └── strategy2.py
├── signals/             # 自定义信号
│   ├── __init__.py
│   └── my_signals.py
├── data/                # 数据目录
├── results/             # 回测结果
└── main.py             # 主程序
```

### 2. 日志管理

```python
from loguru import logger
from pathlib import Path

# 配置日志
log_path = Path("./logs")
log_path.mkdir(exist_ok=True)

logger.add(
    log_path / "czsc_{time}.log",
    rotation="1 week",
    retention="1 month",
    encoding="utf-8"
)
```

### 3. 错误处理

```python
try:
    bars = research.get_raw_bars(...)
    czsc = CZSC(bars)
except Exception as e:
    logger.error(f"分析失败：{e}")
    continue
```

### 4. 性能优化

- 使用缓存减少重复计算
- 批量处理多个标的
- 合理设置K线数量限制
- 使用多进程并行回测

### 5. 数据质量检查

```python
from czsc.utils.kline_quality import check_kline_quality

# 检查K线质量
quality = check_kline_quality(bars)
if not quality['is_valid']:
    print(f"数据质量问题：{quality['issues']}")
```

---

## 常见问题

### Q1: 如何更新K线数据？

```python
# 方法1：使用update方法
czsc.update(new_bar)

# 方法2：重新创建对象
bars.append(new_bar)
czsc = CZSC(bars)
```

### Q2: 如何自定义信号函数？

参考"策略开发"章节中的"自定义信号函数"部分。

### Q3: 回测结果如何保存？

```python
# 保存策略配置
strategy.save_positions("./positions")

# 保存回测结果
import json
with open("results.json", "w") as f:
    json.dump(trader.pairs, f, indent=2, ensure_ascii=False)
```

### Q4: 如何可视化分析结果？

```python
# 使用ECharts
chart = czsc.to_echarts()
czsc.open_in_browser()

# 使用信号快照
from czsc.traders import CzscSignals
cs = CzscSignals(bg=bg, signals_config=signals_config)
cs.take_snapshot("snapshot.html")
```

### Q5: 如何处理多周期数据？

```python
from czsc.utils import BarGenerator
from czsc.objects import Freq

# 创建K线合成器
bg = BarGenerator(
    base_freq=Freq.F30,
    freqs=[Freq.F30, Freq.F60, Freq.D, Freq.W]
)

# 更新基础周期K线，自动合成其他周期
for bar in bars_30m:
    bg.update(bar)

# 获取各周期K线
bars_30m = bg.bars[Freq.F30]
bars_60m = bg.bars[Freq.F60]
bars_d = bg.bars[Freq.D]
bars_w = bg.bars[Freq.W]
```

### Q6: 如何批量处理多个标的？

```python
from czsc.connectors import research
from czsc.analyze import CZSC
from tqdm import tqdm

symbols = research.get_symbols('中证500成分股')[:100]
results = []

for symbol in tqdm(symbols):
    try:
        bars = research.get_raw_bars(
            symbol=symbol,
            freq=Freq.D,
            sdt="20200101",
            edt="20231231"
        )
        czsc = CZSC(bars)
        results.append({
            'symbol': symbol,
            'bi_count': len(czsc.finished_bis),
            'fx_count': len(czsc.fxs)
        })
    except Exception as e:
        logger.error(f"{symbol} 处理失败: {e}")
        continue
```

---

## 项目架构说明

### 整体架构

```
CZSC 项目架构
├── 数据层 (Data Layer)
│   ├── connectors/          # 数据连接器
│   │   ├── research.py     # 研究数据源
│   │   ├── ts_connector.py # Tushare
│   │   ├── jq_connector.py # 聚宽
│   │   └── ...
│   └── objects.py          # 数据对象定义
│
├── 分析层 (Analysis Layer)
│   ├── analyze.py          # 缠论分析核心
│   ├── signals/            # 信号函数库
│   └── features/          # 特征工程
│
├── 策略层 (Strategy Layer)
│   ├── strategies.py       # 策略基类
│   ├── traders/           # 交易执行
│   │   ├── base.py        # 交易者基类
│   │   ├── cwc.py         # 客户端权重客户端
│   │   └── rwc.py         # Redis权重客户端
│   └── sensors/           # 传感器/研究工具
│
├── 工具层 (Utils Layer)
│   ├── utils/             # 工具函数
│   ├── svc/               # Streamlit可视化组件
│   └── eda.py             # 探索性数据分析
│
└── 应用层 (Application Layer)
    ├── examples/          # 示例代码
    ├── modules/           # 封装模块
    └── test/              # 测试代码
```

### 核心模块关系

```
RawBar (原始K线)
    ↓
BarGenerator (K线合成器)
    ↓
CZSC (缠论分析)
    ↓
CzscSignals (信号计算)
    ↓
CzscTrader (交易执行)
    ↓
回测结果
```

### 数据流

```
数据源 → RawBar → BarGenerator → CZSC → Signals → Events → Positions → Trades
```

---

## 高级功能

### 1. 自定义信号函数开发

```python
# -*- coding: utf-8 -*-
from czsc.objects import Signal
from czsc.analyze import CZSC
from typing import Dict

def custom_signal_V001(czsc: CZSC, di: int = 1, **kwargs) -> Dict[str, str]:
    """自定义信号函数示例
    
    :param czsc: CZSC分析对象
    :param di: 倒数第几笔，默认1表示最后一笔
    :return: 信号字典
    """
    s = {}
    
    # 检查是否有足够的笔
    if len(czsc.finished_bis) < di:
        return s
    
    # 获取倒数第di笔
    bi = czsc.finished_bis[-di]
    
    # 计算信号
    freq = czsc.freq.value
    signal_name = f"{freq}_自定义信号V001"
    
    if bi.direction.value == "向上":
        s[f"{signal_name}_向上"] = "向上"
    else:
        s[f"{signal_name}_向下"] = "向下"
    
    return s

# 使用自定义信号
signals_config = [
    {
        'name': 'custom_signal_V001',  # 或使用完整路径
        'freq': '日线',
        'di': 1
    }
]
```

### 2. 策略参数优化

```python
from czsc.traders import OpensOptimize
from czsc.strategies import CzscStrategyBase
from czsc.objects import Position, Event

class OptimizableStrategy(CzscStrategyBase):
    def __init__(self, base_freq='30分钟', stop_loss=500, **kwargs):
        super().__init__(**kwargs)
        self.base_freq = base_freq
        self.stop_loss = stop_loss
    
    @property
    def positions(self):
        # 使用self.base_freq和self.stop_loss构建策略
        opens = [{
            "operate": "开多",
            "factors": [{
                "signals_all": [f"{self.base_freq}_D1_表里关系V230101_向上_任意_任意_0"]
            }]
        }]
        
        pos = Position(
            name=f"{self.base_freq}策略",
            symbol=self.symbol,
            opens=[Event.load(x) for x in opens],
            exits=[],
            stop_loss=self.stop_loss
        )
        return [pos]

# 参数优化
opt = OpensOptimize(
    strategy=OptimizableStrategy,
    symbols=["000001.SH"],
    sdt="20200101",
    edt="20231231",
    params={
        'base_freq': ['30分钟', '60分钟', '日线'],
        'stop_loss': [300, 500, 700, 1000]
    }
)

results = opt.optimize()
print("最优参数：", results)
```

### 3. 实时交易监控

```python
from czsc.traders import CzscTrader
from czsc.strategies import CzscStrategyBase
from czsc.connectors import research
import time

class RealTimeStrategy(CzscStrategyBase):
    @property
    def positions(self):
        # 策略定义
        return [position]

# 初始化
strategy = RealTimeStrategy(symbol="000001.SH")
bars = research.get_raw_bars(
    symbol="000001.SH",
    freq=strategy.base_freq,
    sdt="20200101",
    edt="20231231"
)

trader = strategy.replay(bars, sdt="20230101")

# 实时更新
while True:
    # 获取最新K线
    latest_bars = research.get_raw_bars(
        symbol="000001.SH",
        freq=strategy.base_freq,
        sdt="20231231",
        edt="20240101"
    )
    
    if latest_bars:
        new_bar = latest_bars[-1]
        trader.update(new_bar)
        
        # 检查是否有新操作
        if trader.operates:
            latest_op = trader.operates[-1]
            print(f"新操作：{latest_op}")
    
    time.sleep(60)  # 每分钟更新一次
```

### 4. 多策略组合

```python
from czsc.traders import get_ensemble_weight
from czsc.strategies import CzscStrategyBase

# 定义多个策略
strategies = [
    Strategy30Min(symbol="000001.SH"),
    Strategy60Min(symbol="000001.SH"),
    StrategyDaily(symbol="000001.SH")
]

# 获取各策略权重
weights = get_ensemble_weight(
    strategies=strategies,
    bars=bars,
    sdt="20210101",
    edt="20231231"
)

print(f"策略权重：{weights}")
```

---

## 性能优化建议

### 1. 缓存使用

```python
from czsc.utils import disk_cache

@disk_cache(expire=3600)  # 缓存1小时
def get_expensive_data(symbol, sdt, edt):
    # 耗时操作
    return research.get_raw_bars(symbol, Freq.D, sdt, edt)
```

### 2. 批量处理

```python
from czsc.connectors import research

# 批量获取数据
all_bars = research.get_raw_bars_multi(
    symbols=["000001.SH", "000002.SH", "000003.SH"],
    freq=Freq.D,
    sdt="20200101",
    edt="20231231"
)
```

### 3. 并行回测

```python
from multiprocessing import Pool
from czsc.traders import DummyBacktest

def backtest_symbol(symbol):
    backtest = DummyBacktest(
        strategy=MyStrategy,
        symbols=[symbol],
        sdt="20200101",
        edt="20231231"
    )
    return backtest.run()

# 并行执行
with Pool(processes=4) as pool:
    results = pool.map(backtest_symbol, symbols)
```

---



