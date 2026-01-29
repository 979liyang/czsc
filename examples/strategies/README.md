# 策略示例目录

本目录包含多个策略示例，按市场类型分类组织。

## 目录结构

```
strategies/
├── stock/          # 股票策略
├── future/         # 期货策略
└── etf/            # ETF策略
```

## 股票策略

### strategy_01_third_buy.py
- **名称**: 日线三买多头策略
- **说明**: 基于缠论三买信号的股票多头策略
- **周期**: 日线、30分钟
- **文档**: [strategy_01_third_buy_README.md](stock/strategy_01_third_buy_README.md)

## 期货策略

### strategy_01_30min_bi.py
- **名称**: 30分钟笔非多即空策略
- **说明**: 基于30分钟笔方向的期货多空策略
- **周期**: 30分钟
- **文档**: [strategy_01_30min_bi_README.md](future/strategy_01_30min_bi_README.md)

## 使用方法

### 1. 导入策略

```python
from examples.strategies.stock.strategy_01_third_buy import Strategy
```

### 2. 创建策略实例

```python
tactic = Strategy(symbol="000001.SH")
```

### 3. 获取K线数据

```python
from czsc.connectors.research import get_raw_bars

bars = get_raw_bars("000001.SH", freq="30分钟", sdt="2015-01-01", edt="2022-07-01")
```

### 4. 执行回测

```python
trader = tactic.backtest(bars, sdt="20200101")
```

## 策略开发指南

### 策略类结构

所有策略必须继承 `CzscStrategyBase` 并实现 `positions` 属性：

```python
from czsc import CzscStrategyBase
from czsc.objects import Position
from typing import List

class Strategy(CzscStrategyBase):
    @property
    def positions(self) -> List[Position]:
        # 返回持仓策略列表
        return [pos1, pos2, ...]
```

### 持仓策略创建

使用 `Position` 类创建持仓策略，定义开仓和平仓条件：

```python
from czsc.objects import Position, Event

pos = Position(
    name="策略名称",
    symbol=symbol,
    opens=[Event.load({...})],  # 开仓条件
    exits=[Event.load({...})],  # 平仓条件
    interval=3600,              # 操作间隔
    timeout=480,                # 超时时间
    stop_loss=300,              # 止损点数
)
```

## 注意事项

1. 所有策略示例仅供参考，实际使用前请充分测试
2. 策略参数需要根据实际市场情况调整
3. 建议在模拟环境中测试后再用于实盘
