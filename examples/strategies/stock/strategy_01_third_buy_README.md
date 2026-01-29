# 日线三买多头策略

## 策略说明

这是一个基于缠论三买信号的股票多头策略。

## 策略逻辑

### 开多条件
- 日线出现三买信号：`日线_D1_三买辅助V230228_三买_任意_任意_0`
- 排除涨跌停：`{base_freq}_D1_涨跌停V230331_任意_任意_任意_0`

### 平多条件
- 30分钟出现一卖信号：`30分钟_D1B_SELL1_一卖_任意_任意_0`
- 或特定笔数的一卖信号（9笔、11笔、13笔）

## 参数说明

- `base_freq`: 基础周期，默认"30分钟"
- `interval`: 操作间隔，默认7200秒（2小时）
- `timeout`: 超时时间，默认480分钟（16*30）
- `stop_loss`: 止损点数，默认300点
- `T0`: 是否T+0交易，默认False

## 使用方法

```python
from examples.strategies.stock.strategy_01_third_buy import Strategy
from czsc.connectors.research import get_raw_bars

# 创建策略实例
tactic = Strategy(symbol="000001.SH")

# 获取K线数据
bars = get_raw_bars("000001.SH", freq="30分钟", sdt="2015-01-01", edt="2022-07-01")

# 执行回测
trader = tactic.backtest(bars, sdt="20200101")
```

## 适用市场

- 股票市场

## 适用周期

- 日线（开仓信号）
- 30分钟（平仓信号）
