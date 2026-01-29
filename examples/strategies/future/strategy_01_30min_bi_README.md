# 30分钟笔非多即空策略

## 策略说明

这是一个基于30分钟笔方向的期货多空策略。

## 策略逻辑

### 开多条件
- 30分钟笔向上：`30分钟_D1_表里关系V230102_向上_任意_任意_0`

### 开空条件
- 30分钟笔向下：`30分钟_D1_表里关系V230102_向下_任意_任意_0`

### 平多条件
- 30分钟笔转为向下：`30分钟_D1_表里关系V230102_向下_任意_任意_0`

### 平空条件
- 30分钟笔转为向上：`30分钟_D1_表里关系V230102_向上_任意_任意_0`

## 参数说明

- `base_freq`: 基础周期，默认"30分钟"
- `interval`: 操作间隔，默认3600秒（1小时）
- `timeout`: 超时时间，默认480分钟（16*30）
- `stop_loss`: 止损点数，默认500点

## 使用方法

```python
from examples.strategies.future.strategy_01_30min_bi import Strategy
from czsc.connectors.research import get_raw_bars

# 创建策略实例
tactic = Strategy(symbol="RB888")

# 获取K线数据
bars = get_raw_bars("RB888", freq="30分钟", sdt="2015-01-01", edt="2022-07-01")

# 执行回测
trader = tactic.backtest(bars, sdt="20200101")
```

## 适用市场

- 期货市场

## 适用周期

- 30分钟
