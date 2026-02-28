# 日线均线多头策略

## 策略说明

基于日线均线金叉/死叉的股票多头策略示例。

## 适用市场

- 股票

## 适用周期

- 日线

## 使用方法

```python
from examples.strategies.stock.strategy_02_ma_long import Strategy
from czsc.connectors.research import get_raw_bars

tactic = Strategy(symbol="000001.SZ")
bars = get_raw_bars("000001.SZ", freq="日线", sdt="2020-01-01", edt="2024-01-01")
```
