# 自检清单：因子/策略与数据库（tasks_czsc_factors_strategies_db）

按以下顺序执行可验证「因子与策略」相关表与 API 是否就绪。建议在本地或 CI 回归时使用。

## 1. 数据库与入库脚本（顺序执行）

1. **建表**：`python scripts/db_init_mysql.py`（创建 signal_func、signals_config、factor_def、my_singles 等表）
2. **同步信号函数**：`python scripts/sync_czsc_signals_to_db.py`（可选，将 czsc.signals 写入 signal_func）
3. **同步因子定义**：`python scripts/sync_factor_def_from_signal_func.py`（从 signal_func 同步到 factor_def，建议在步骤 2 之后）
4. **种子信号配置**：`python scripts/seed_signals_config.py`（向 signals_config 写入预设配置）

## 2. API 可用性

- **GET /api/v1/factor-defs**：返回因子列表（可选 `active_only=true`）
- **GET /api/v1/signals-config**：返回信号配置列表
- **GET /api/v1/examples**：返回策略示例列表（来自 examples/strategies 下 strategy_*.py）
- **POST /api/v1/screen/run**、**GET /api/v1/screen/results**：全盘扫描触发与结果查询
- **前端**：信号分析页（/signal-analyze）、全盘扫描页（/screen）可访问且功能可用
- **信号分析页**：仅信号、按类型添加、加号弹窗选类型与信号、默认半年前至今、可设每信号周期、分析结果正确

以上通过即表示因子、信号配置、策略示例与信号分析/全盘扫描链路正常。
