# Step4: 策略 Demo

本目录演示如何使用 CZSC 策略：定义策略（持仓规则）、加载 K 线、回放/回测并查看开平仓与绩效。

- **strategy_demo.py**：单均线多头策略示例，日线数据 + replay 回放，输出操作记录与简单评估。
- 更多策略定义见 `czsc.strategies`（如 create_single_ma_long、create_third_buy_long 等），回测 API 见后端 `/api/v1/backtest`。
