# Tasks: 单股分析改为「信号分析」——仅信号、按类型添加、支持每信号周期

**Input**: 单股分析改成 Signal 分析，删除因子和策略，只选择信号；按信号类型展示与添加（加号弹窗：类型筛选 + 具体信号选择）；默认开始时间为半年前、结束时间为今天；不同信号可有不同周期；学习理解信号入参与返回。  
**Path Conventions**: 前端 `frontend/src/`，后端 `backend/src/`（与 plan.md 一致）。

**现状简述**:
- 当前「单股分析」页（`StockAnalyze.vue`）包含：股票、周期、时间、多选信号、多选因子、单选策略，「分析」与「回测」两个动作。
- 后端 GET /docs/signals 返回信号列表，含 category、params、data_requirements（freq、needed_bars）、signals（输出键）；POST /signals/batch 的 signal_configs 中每项可带 name、freq、di 等，即支持「每信号不同周期」。

---

## Phase 1: 理解信号入参与返回（文档与约定）

**Purpose**: 明确信号 API 的入参、返回及周期约定，便于前端按类型展示与传参。

- [X] T001 梳理信号 API 与文档结构：确认 GET /docs/signals（及 GET /docs/signals/{name}）返回的 category、params、data_requirements、signals 字段含义；确认 POST /signals/batch 的 signal_configs 每项格式（name、freq、di 等），以及返回的 signals 结构与各信号周期关系（`backend/src/api/v1/docs.py`、`backend/src/api/v1/signals.py`、`backend/src/services/doc_service.py`）
- [X] T002 [P] 文档化「信号入参与返回」：在 `docs/` 下新增或补充一节（如 `docs/signals_and_factors.md` 或 `docs/learning/czsc_signals.md`）：说明信号函数的入参（freq、di、及各信号特有参数）、返回（signals 字典的 key 与含义）、data_requirements 与「建议周期」的对应关系，供前端与联调使用（`docs/`）

---

## Phase 2: 前端改造——信号分析页（仅信号、按类型、加号添加）

**Purpose**: 将单股分析改为「信号分析」：仅保留信号选择与计算，按类型展示已选信号，通过加号弹窗按类型筛选并选择具体信号，默认时间半年前至今，支持每信号不同周期。

**Independent Test**: 打开信号分析页，默认时间为半年前～今天；已选信号按类型分组展示；点击加号可先选类型再选信号并确认添加；可为不同信号选择不同周期；点击「分析」仅调用 POST /signals/batch，结果区展示各信号返回值（含类型/周期信息）。

- [X] T003 重命名与路由：将「单股分析」改为「信号分析」；路由保留 /stock-analyze 或改为 /signal-analyze（二选一，与产品约定一致）；侧栏与首页入口文案改为「信号分析」；页面标题与卡片标题改为「信号分析」（`frontend/src/router/routes.ts`、`frontend/src/layouts/Dashboard.vue`、`frontend/src/views/Home.vue`、`frontend/src/views/StockAnalyze.vue` 或新 `SignalAnalyze.vue`）
- [X] T004 默认时间与表单精简：在信号分析页中，默认开始时间设为半年前、结束时间设为今天（初始化时用 JS 计算并写入 form）；删除「因子」「策略」表单项及「回测」按钮；保留股票代码、开始/结束时间；若保留「全局周期」作为默认周期，可保留一处周期选择，用于在加号弹窗中作为新添加信号的默认周期（`frontend/src/views/StockAnalyze.vue` 或 `frontend/src/views/SignalAnalyze.vue`）
- [X] T005 已选信号按类型展示与加号添加：在「信号」区域，已选信号按 category 分组展示（显示类型名 + 该类型下已选信号列表，每项可展示信号名、可选展示周期）；下方或组内提供「加号」按钮，点击后打开弹窗（Dialog/Drawer）：先按类型筛选（如下拉或 Tab 选 category），再展示该类型下的信号列表供多选，确认后将选中信号加入已选列表；新加入的每项需包含 signal name、category、以及该信号使用的周期（可从 data_requirements 取默认或由用户选择）（`frontend/src/views/StockAnalyze.vue` 或 `SignalAnalyze.vue`、可选 `frontend/src/components/SignalAddDialog.vue`）
- [X] T006 分析请求与结果展示：点击「分析」时，根据已选信号列表构建 signal_configs（每项含 name、freq 使用该信号配置的周期、以及从信号 params 来的可选参数）；调用 POST /signals/batch，传入 symbol、sdt、edt 与 signal_configs；结果区展示返回的 signals 字典，并按信号类型或信号名分组展示，可选展示每信号对应周期（`frontend/src/views/StockAnalyze.vue` 或 `SignalAnalyze.vue`、`frontend/src/api/signals.ts`）

---

## Phase 3: Polish（文案与自检）

**Purpose**: 统一文案、移除对因子/策略的残留引用，自检清单可验证。

- [X] T007 [P] 文案与入口统一：全文将「单股分析」替换为「信号分析」（含 README、docs、侧栏、首页）；确保无「因子」「策略」在该页的入口或说明（`README.md`、`docs/README.md`、`frontend/src/views/StockAnalyze.vue` 或 `SignalAnalyze.vue`）
- [X] T008 自检项：在 `specs/001-czsc-api-ui/` 或 `docs/` 的自检清单中增加「信号分析页：仅信号、按类型添加、加号弹窗、默认半年前至今、可设每信号周期、分析结果正确」的验证项（`specs/001-czsc-api-ui/CHECKLIST_*.md` 或 `docs/`）

---

## Dependencies & Execution Order

- **Phase 1**：无依赖，建议先完成以统一对信号入参/返回的认知。
- **Phase 2**：依赖 Phase 1；T003 与 T004 可并行或 T003 先做；T005 依赖 T004；T006 依赖 T005。
- **Phase 3**：依赖 Phase 2 主体完成；T007 与 T008 可并行。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 描述 + 文件路径。
- 本清单为重构类任务，未使用 [USn] 标签。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_signal_analysis_refactor.md` |
| **总任务数** | 8 |
| **Phase 1** | 理解信号 API 与文档（入参、返回、周期） |
| **Phase 2** | 前端：重命名、默认时间、删因子/策略、按类型展示、加号弹窗添加、每信号周期、分析请求与结果 |
| **Phase 3** | 文案统一与自检项 |
| **并行** | T002、T007、T008 标 [P] |
| **建议顺序** | Phase 1 → T003/T004 → T005 → T006 → Phase 3 |
