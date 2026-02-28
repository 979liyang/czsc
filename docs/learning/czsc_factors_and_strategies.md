# CZSC 中的因子与策略

本文说明在 CZSC 及本项目中「因子」与「策略」的含义、对应表与接口，便于学习 czsc 与完善数据库和代码。

## 1. 因子（Factor）

### 在 CZSC 中的含义

- 在 czsc 中，**因子**多指「可计算的指标/信号」：对标的在某一时点可算出一个或多个值，用于选股、排序或归因。
- 因子通常对应某个**信号函数**（如 `czsc.signals.tas_ma_base_V230313`）或自定义表达式，在回测或筛选中按「因子维度」统计。

### 在本项目中的对应

| 概念 | 表/代码 | 说明 |
|------|---------|------|
| 因子定义 | `factor_def` 表 | 存因子名称、关联的信号函数全名（`expression_or_signal_ref`）、说明、是否启用。 |
| 因子筛选 | `run_factor_screen`（`backend/src/services/screen_service.py`） | 按 factor_def 表对股票池逐只、逐因子计算，结果写入 `screen_result`（带 `factor_id`）。 |
| 信号函数元数据 | `signal_func` 表 | 存 czsc.signals 中信号函数的元数据（名、模块、分类等）。因子可**引用**信号：factor_def.expression_or_signal_ref 填信号全名即可。 |

**关系**：`signal_func` 描述「有哪些信号」；`factor_def` 描述「业务侧命名的因子」，当前通过 `expression_or_signal_ref` 引用信号函数参与筛选。可用 `scripts/sync_factor_def_from_signal_func.py` 从 signal_func 全量同步到 factor_def。

---

## 2. 策略（Strategy）

### 在 CZSC 中的含义

- 在 czsc 中，**策略**是一套完整逻辑：**标的 + 周期 + positions（开平规则）+ signals_config（要算哪些信号）+ 回测**。
- 策略类通常继承 czsc 的 BaseStrategy，包含 `positions`、`signals_config`，并通过 `backtest(bars, sdt=...)` 得到交易记录与绩效。

### 在本项目中的对应

| 概念 | 位置/代码 | 说明 |
|------|-----------|------|
| 策略示例 | `examples/strategies/` 目录 | 按分类（如 stock、future、etf）存放 `strategy_*.py`，每个文件为一条策略示例。 |
| 策略回测 | `BacktestService`（`backend/src/services/backtest_service.py`） | 接收 `strategy_config`（含 `strategy_class`、`strategy_kwargs` 等），拉取 K 线后调用策略的 `backtest()`。 |
| 策略配置 | API 请求体 `strategy_config` | 通常含 `strategy_class`（策略类全限定名）、`signals_config`（信号配置列表）、`strategy_kwargs` 等。 |
| 策略示例列表 | `ExampleService`、GET /api/v1/examples | 扫描 `examples/strategies/` 目录，解析策略文件元信息（名称、描述、适用市场、周期），不建策略表。 |

**说明**：当前策略示例**仅来自 examples/strategies 目录扫描**，未在数据库中建「策略元数据表」；若后续需要策略入库，可增加 StrategyMeta 表与对应 API。策略示例目录由环境变量 **EXAMPLES_PATH** 指定（默认 `examples`），其下 `strategies/` 按分类（如 stock、future、etf）存放 `strategy_*.py` 文件，与 `ExampleService` 约定一致。

---

## 3. 因子与策略的关系

- **策略**使用 **signals_config**：决定回测时算哪些信号、用哪些参数；signals_config 可来自请求体，也可从 `signals_config` 表按名称加载。
- **因子**用于**筛选维度**：在 `run_factor_screen` 中按 factor_def 对股票池计算，结果写入 screen_result，供选股/报表使用，不直接参与单策略回测逻辑。
- **共同点**：都依赖「信号函数」；因子通过 expression_or_signal_ref 指向信号，策略通过 signals_config 指定要算的信号列表。

---

## 4. 相关文档与接口

- 信号函数学习：[czsc_signals.md](./czsc_signals.md)
- 信号配置与因子库说明（表、API、入库顺序）：[../signals_and_factors.md](../signals_and_factors.md)
- 因子筛选任务：`backend/src/services/screen_service.py`（`run_signal_screen`、`run_factor_screen`）
- 策略回测 API：POST /api/v1/backtest/run，body 含 `strategy_config`
- 策略示例 API：GET /api/v1/examples、GET /api/v1/examples/{example_id}
