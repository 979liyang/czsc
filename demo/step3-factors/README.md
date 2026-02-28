# Step3: 因子使用

本目录演示如何将 CZSC 信号作为「因子」使用：对单只标的计算多个因子（信号），查看因子值与分数，并做简单筛选。

- **factor_usage_demo.py**：本地用 czsc 计算因子、打印结果、按分数筛选示例。
- 后端 API 的因子定义与全市场筛选见：`/api/v1/factor-defs`、筛选任务（按 factor_def 表跑 run_factor_screen）。
