# Tasks: 根据信号、因子、策略完善前端（单股分析 + 全盘扫描）

**Input**: 根据信号、因子、策略完善前端代码。1. 可以分析单个股票，可选择多种信号、因子、策略进行分析。2. 可以全盘扫描满足信号、因子、策略的股票。  
**Path Conventions**: 后端 `backend/src/`，前端 `frontend/src/`，文档 `docs/`（与 plan.md 一致）。

**现状简述**:
- 后端已有：GET/POST/PUT/DELETE /factor-defs、GET/POST /signals-config、GET /examples、GET/POST /signals/calculate|batch、POST /backtest/run；筛选逻辑在 `screen_service.run_signal_screen` / `run_factor_screen`，仅通过 CLI 调用，无 HTTP 接口。
- 前端已有：`frontend/src/api/` 下 examples.ts、signals.ts、backtest.ts；缺 factor-defs、signals-config、screen 的 API 封装；Analysis.vue 仅缠论分析，Backtest.vue 为占位；无「单股多信号/因子/策略分析」页与「全盘扫描」页。

---

## Phase 1: 前置确认（必做）

**Purpose**: 确认后端能力与前端约定，避免重复造轮子。

- [X] T001 确认后端 API 与筛选能力：确认 GET /factor-defs、GET /signals-config、GET /examples、GET/POST /signals/calculate|batch、POST /backtest/run 可用；确认 screen_result、screen_task_run 表与 `backend/src/services/screen_service.py` 的 run_signal_screen、run_factor_screen 行为（`backend/src/api/v1/`、`backend/src/services/screen_service.py`）
- [X] T002 [P] 确认前端 API 与路由：确认 `frontend/src/api/` 中 examples、signals、backtest 已对接上述接口；确认 `frontend/src/router/routes.ts` 中 /analysis、/backtest、/examples、/signals 等路径（`frontend/src/api/`、`frontend/src/router/routes.ts`）

---

## Phase 2: 基础设施（阻塞后续）

**Purpose**: 补齐筛选 HTTP 接口与前端 API 封装，供单股分析与全盘扫描使用。

**Independent Test**: 可调用 POST /api/v1/screen/run 触发一次信号或因子筛选（或返回 202 异步）；可调用 GET /api/v1/screen/results 按 trade_date 等条件查询筛选结果列表。

- [X] T003 后端筛选 API：在 `backend/src/api/v1/screen.py` 中新增路由：POST /screen/run（body: trade_date、task_type=signal|factor、market 可选、max_symbols 可选），调用 `screen_service.run_signal_screen` 或 `run_factor_screen`；GET /screen/results（query: trade_date、task_type 可选、task_run_id 可选、limit），从 screen_result 表查询并返回列表；在 `backend/src/main.py` 中挂载 screen 路由（`backend/src/api/v1/screen.py`、`backend/src/main.py`）
- [X] T004 [P] 前端 factor-defs 与 signals-config API：在 `frontend/src/api/factorDefs.ts` 中封装 GET /factor-defs（支持 active_only）、POST/PUT/DELETE（若需管理）；在 `frontend/src/api/signalsConfig.ts` 中封装 GET /signals-config 列表、GET by name 或 getConfigAsList（`frontend/src/api/factorDefs.ts`、`frontend/src/api/signalsConfig.ts`）
- [X] T005 [P] 前端 screen API：在 `frontend/src/api/screen.ts` 中封装 POST /screen/run、GET /screen/results，类型与后端一致（`frontend/src/api/screen.ts`）

---

## Phase 3: User Story 1 - 单股分析（多信号、因子、策略）(P1)

**Goal**: 用户可选择一只股票，选择多种信号、因子或策略，进行分析或回测，并查看结果。

**Independent Test**: 打开单股分析页，选择股票 000001.SH、周期与时间范围，勾选若干信号、若干因子、选择一种策略；点击「分析」或「回测」，页面展示信号计算结果、因子值、回测摘要（可链到详情）。

- [X] T006 [P] [US1] 单股分析页骨架与表单：新增 `frontend/src/views/StockAnalyze.vue`（或增强 `frontend/src/views/Analysis.vue`），包含：股票代码、周期、时间范围、多选信号（下拉/多选，数据来自 signal_func 或 GET /docs/signals / factor-defs 关联）、多选因子（来自 GET /factor-defs）、单选策略（来自 GET /examples）；「分析」/「回测」按钮（`frontend/src/views/StockAnalyze.vue` 或 `frontend/src/views/Analysis.vue`）
- [X] T007 [US1] 单股分析请求与展示：在单股分析页中，点击「分析」时调用 POST /signals/batch 计算所选信号、对所选因子逐条用对应信号计算（或调用现有批量接口）；点击「回测」时调用 POST /backtest/run（strategy_config 含所选策略与可选 signals_config_name）；结果区展示信号结果表/卡片、因子值列表、回测摘要（收益/回撤等）及跳转链接（`frontend/src/views/StockAnalyze.vue`、`frontend/src/api/`）
- [X] T008 [US1] 单股分析路由与导航：在 `frontend/src/router/routes.ts` 中增加 /stock-analyze（或 /analysis/stock）指向 StockAnalyze；在侧栏或首页增加「单股分析」入口（`frontend/src/router/routes.ts`、侧栏组件如 `frontend/src/layouts/components/Sidebars/DashboardSidebar.vue`）

---

## Phase 4: User Story 2 - 全盘扫描 (P2)

**Goal**: 用户可选择按信号或因子条件，执行全市场（或指定市场）扫描，查看满足条件的股票列表。

**Independent Test**: 打开全盘扫描页，选择交易日、任务类型（按信号 / 按因子），可触发扫描或直接选择已有扫描结果；页面展示结果列表（股票代码、信号名或因子名、结果值、交易日），支持按交易日筛选。

- [X] T009 [P] [US2] 全盘扫描页骨架与表单：新增 `frontend/src/views/ScreenScan.vue`，包含：交易日选择、任务类型（信号 / 因子）、市场可选、「执行扫描」与「查看结果」；说明文案：扫描由后端任务执行，结果写入后可在「查看结果」中按交易日查询（`frontend/src/views/ScreenScan.vue`）
- [X] T010 [US2] 全盘扫描请求与列表：在 ScreenScan 中，「执行扫描」调用 POST /screen/run（trade_date、task_type、market、max_symbols 可选）；「查看结果」调用 GET /screen/results（trade_date、task_type、limit）；表格展示 symbol、signal_name 或 factor_name、value_result、trade_date，支持按 trade_date 筛选（`frontend/src/views/ScreenScan.vue`、`frontend/src/api/screen.ts`）
- [X] T011 [US2] 全盘扫描路由与导航：在 `frontend/src/router/routes.ts` 中增加 /screen 或 /scan 指向 ScreenScan；在侧栏或首页增加「全盘扫描」入口（`frontend/src/router/routes.ts`、侧栏组件）

---

## Phase 5: Polish（文档与收尾）

**Purpose**: 文档可发现、入口统一。

- [X] T012 [P] 文档与自检：在 `docs/` 或 `README.md` 中补充「单股分析」「全盘扫描」功能说明及入口（单股分析页、全盘扫描页）；可选在 `specs/001-czsc-api-ui/CHECKLIST_*.md` 中增加「GET /screen/results、单股分析页、全盘扫描页可用」的自检项（`docs/`、`README.md`、`specs/001-czsc-api-ui/`）

---

## Dependencies & Execution Order

- **Phase 1**: 无依赖，建议先完成以统一认知。
- **Phase 2**: 依赖 Phase 1；T003 与 T004、T005 可并行（T004、T005 为前端，T003 为后端）。
- **Phase 3**: 依赖 Phase 2（screen 可先不做，单股分析不依赖 GET /screen/results）；T006 先做，T007 依赖 T006，T008 可与 T007 并行或其后。
- **Phase 4**: 依赖 Phase 2（尤其 T003、T005）；T009 先做，T010 依赖 T009，T011 可与 T010 并行或其后。
- **Phase 5**: 依赖 Phase 3、4 主体完成；T012 可最后做。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 可选 `[USn]` + 描述 + 文件路径。
- Phase 3 为 US1（单股分析），Phase 4 为 US2（全盘扫描），各自具备独立验收标准。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_frontend_signals_factors_scan.md` |
| **总任务数** | 12 |
| **Phase 1** | 前置确认：后端 API 与筛选能力、前端 API 与路由 |
| **Phase 2** | 基础设施：后端 screen API、前端 factorDefs/signalsConfig/screen API |
| **Phase 3 (US1)** | 单股分析：多信号、因子、策略选择与结果展示 |
| **Phase 4 (US2)** | 全盘扫描：触发扫描与结果列表 |
| **Phase 5** | 文档与收尾 |
| **并行** | T002、T004、T005、T006、T009、T012 标 [P] |
| **建议 MVP** | Phase 1 + Phase 2 + Phase 3（单股分析）先交付，再做 Phase 4（全盘扫描） |
