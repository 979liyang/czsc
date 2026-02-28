# Tasks: 策略全量入库与个股策略分析（参数选择与前端默认值）

**Input**: 把所有策略都入库；支持个股策略分析，选择不同策略时展示对应策略参数表单并带默认值。  
**Path Conventions**: 后端 `backend/src/`，前端 `frontend/src/`，脚本 `scripts/`（与 plan.md 一致）。

**现状简述**:
- 已有 strategies 表、StrategiesRepo、GET/POST/PUT/DELETE /api/v1/strategies；seed_strategies.py 仅入库部分策略（单均线 2 种、MACD、三买/三卖），未覆盖 CCI、EMV 等。
- 回测当前为 strategy_config（strategy_class + strategy_kwargs），未支持「从策略库选策略 + 填参数」的个股分析流程。
- 需：全量策略入库、按 strategy_type 提供参数 schema 与默认值、后端支持按策略+参数执行个股回测、前端策略分析页（选策略→展示参数表单默认值→提交分析）。

---

## Phase 1: 策略全量入库（Foundational）

**Purpose**: 将 czsc.strategies 中全部 create_* 策略（含 CCI、EMV 及单均线/MACD/三买三卖的所有合理变体）写入 strategies 表。

**Independent Test**: 执行 `python scripts/seed_strategies.py` 后，strategies 表包含至少 10 类策略类型对应的多条记录（单均线多种 ma_name、MACD、CCI、EMV、三买、三卖等）；GET /api/v1/strategies 返回完整列表。

- [x] T001 扩展种子脚本覆盖全部策略：在 `scripts/seed_strategies.py` 中补充 create_cci_long、create_cci_short、create_emv_long、create_emv_short 的入库；对 create_single_ma_long/short 增加常用 ma_name 变体（如 SMA#10、SMA#40）；保证每种 strategy_type 至少有一条 A 股 is_stocks=True 的模板记录，写入 `backend` 的 strategies 表（`scripts/seed_strategies.py`）
- [x] T002 可选：策略去重与幂等：在 `scripts/seed_strategies.py` 中按策略 name 或 (strategy_type + 关键参数) 做 upsert，避免重复插入；支持 `--dry-run` 与 `--force`（`scripts/seed_strategies.py`）

---

## Phase 2: 策略参数 Schema 与默认值（Backend）

**Purpose**: 后端为每种 strategy_type 定义可展示的参数列表（名称、类型、默认值、说明），供前端渲染表单并预填默认值。

**Independent Test**: 调用 GET /api/v1/strategies 或 GET /api/v1/strategies/{id}/params-schema 能返回各策略的 params_schema（含默认值）；前端可根据该 schema 生成表单项。

- [x] T003 定义策略参数 Schema 与默认值：在 `backend/src/services/strategy_params_schema.py`（或 `backend/src/utils/strategy_params_schema.py`）中定义常量或函数，按 strategy_type（如 single_ma_long、single_ma_short、macd_long、macd_short、cci_long、cci_short、emv_long、emv_short、third_buy_long、third_sell_short）返回参数列表，每项含 name、type、default、description、可选 options；与 czsc 各 create_* 的 kwargs 一致（如 ma_name、freq、base_freq、is_stocks、T0、interval、timeout、stop_loss、max_overlap、cci_timeperiod、di 等）（`backend/src/services/strategy_params_schema.py` 或 `backend/src/utils/strategy_params_schema.py`）
- [x] T004 策略列表/详情 API 返回 params_schema：在 `backend/src/api/v1/strategies.py` 中，GET /strategies 的响应项或 GET /strategies/{name} 的响应中增加 params_schema 字段（由 strategy_type 查 T003 的 schema）；或新增 GET /strategies/{id}/params-schema 返回该策略的参数定义与默认值（`backend/src/api/v1/strategies.py`）

---

## Phase 3: 按策略+参数执行个股回测（Backend）

**Purpose**: 支持「选择策略库中的策略 + 传入 symbol、sdt、edt 与参数覆盖」执行回测，供前端个股策略分析调用。

**Independent Test**: 使用 POST /api/v1/backtest/run-by-strategy（或扩展现有 backtest 接口）传入 strategy_id/strategy_name、symbol、sdt、edt、params，能返回与当前 backtest 一致的 pairs/operates/positions 结构。

- [x] T005 按 strategy_type 动态构建 Position：在 `backend/src/services/backtest_service.py` 或新建 `backend/src/services/strategy_runner.py` 中，根据 strategy_type 调用对应 czsc.strategies.create_*（如 create_single_ma_long(symbol, **kwargs)），传入前端提交的 params（与 schema 默认值合并），得到 Position 实例（`backend/src/services/backtest_service.py` 或 `backend/src/services/strategy_runner.py`）
- [x] T006 支持「策略库 + 参数」的回测入口：在 `backend/src/api/v1/backtest.py` 中新增 POST /backtest/run-by-strategy（或扩展 POST /backtest/run），请求体含 strategy_id 或 strategy_name、symbol、sdt、edt、params（可选，覆盖默认值）；从 strategies 表取 strategy_type 与 config_json，用 T005 构建 Position，封装为单 Position 的 CzscStrategyBase 或直接用现有回测逻辑（BarGenerator + 逐 K 线 on_bar）执行回测并返回统一结果结构（`backend/src/api/v1/backtest.py`）
- [x] T007 回测服务集成：在 `backend/src/services/backtest_service.py` 中增加 run_backtest_by_strategy(strategy_id/name, symbol, sdt, edt, params) 方法，内部调用 T005 与现有 K 线获取、trader 执行逻辑（`backend/src/services/backtest_service.py`）

---

## Phase 4: 前端策略分析页（选策略、参数表单默认值、提交分析）

**Purpose**: 前端提供个股策略分析页，选择股票与策略后展示该策略的参数表单（带默认值），提交后调用回测接口并展示结果。

**Independent Test**: 打开策略分析页，选择一只股票与一个策略（如「A股15分钟SMA#5多头基准」），页面展示该策略的参数（如 freq、ma_name、T0 等）并带默认值；用户可修改后点击「运行分析」，结果区展示回测结果（操作记录、绩效等）。

- [x] T008 策略与回测 API 客户端：在 `frontend/src/api/strategies.ts` 中封装 getStrategies、getStrategyByName、getParamsSchema（若单独接口）；在 `frontend/src/api/backtest.ts` 中增加 runBacktestByStrategy(strategyId, symbol, sdt, edt, params)（`frontend/src/api/strategies.ts`、`frontend/src/api/backtest.ts`）
- [x] T009 策略分析页：新增 `frontend/src/views/StrategyAnalyze.vue`（或复用/重命名现有分析页），包含：股票选择（代码或下拉）、策略选择（下拉，数据来自 GET /strategies）、参数区域（根据 GET /strategies/{id} 或 params-schema 动态渲染表单项，并赋默认值）、日期范围 sdt/edt、提交按钮；提交后调用 runBacktestByStrategy，展示返回的 operates、positions 或绩效摘要（`frontend/src/views/StrategyAnalyze.vue`）
- [x] T010 路由与导航：在 `frontend/src/router/routes.ts` 中增加策略分析页路由（如 /strategy-analyze）；在主导航或首页添加入口（`frontend/src/router/routes.ts`、`frontend/src/views/Home.vue` 或布局组件）

---

## Phase 5: 收尾与一致性

**Purpose**: 文档与默认值校验，确保参数与 czsc 一致。

- [x] T011 文档与默认值说明：在 `backend/README.md` 或 `docs/` 中补充「策略库与个股策略分析」说明，包含如何运行 seed_strategies、各 strategy_type 对应参数及默认值来源（czsc.strategies）；若有 GET /strategies/{id}/params-schema，在 API 文档中注明（`backend/README.md` 或 `docs/`）
- [x] T012 默认值校验：核对 `backend` 中 strategy_params_schema 的默认值与 czsc.strategies 中各 create_* 的 kwargs 默认值一致（如 freq="15分钟"、interval=7200、T0=False 等），避免前端提交后后端报错或行为不符（`backend/src/services/strategy_params_schema.py` 或 `backend/src/utils/strategy_params_schema.py`）

---

## Dependencies & Execution Order

- **Phase 1**：T001 → T002（可省略）。先完成全量入库，再做参数与回测。
- **Phase 2**：T003 → T004，依赖 Phase 1 的 strategy_type 稳定。
- **Phase 3**：T005 → T007（T006 依赖 T005/T007）。可与 Phase 2 并行开发。
- **Phase 4**：依赖 Phase 2（前端需 params_schema）与 Phase 3（需 run-by-strategy 接口）；T008 → T009 → T010。
- **Phase 5**：T011、T012 在 Phase 2/3/4 完成后执行。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_strategy_full_seed_and_analysis.md` |
| **总任务数** | 12 |
| **Phase 1** | 策略全量入库（扩展 seed，含 CCI/EMV 及变体） |
| **Phase 2** | 策略参数 schema 与默认值（后端定义 + API 暴露） |
| **Phase 3** | 按策略+参数执行个股回测（Position 构建 + run-by-strategy 接口） |
| **Phase 4** | 前端策略分析页（选策略、参数表单默认值、调用回测） |
| **Phase 5** | 文档与默认值校验 |
| **建议顺序** | Phase 1 → Phase 2 与 Phase 3（可部分并行）→ Phase 4 → Phase 5 |
