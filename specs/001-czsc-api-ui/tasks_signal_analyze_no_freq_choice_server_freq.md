# Tasks: 信号分析页——去除周期选择，由服务端按信号周期取数

**Input**: 去除前端的周期选择；输出键（signals）或信号定义中已包含周期信息，由服务端解析周期并拉取对应 K 线数据。  
**Path Conventions**: 前端 `frontend/src/`，后端 `backend/src/`（与 plan.md 一致）。

**现状简述**:
- 添加信号弹窗中有「周期」下拉，用户手动选择；已选信号按 `freq` 分组后，前端按周期多次调用 POST /signals/batch（每次一个 freq）。
- 信号文档（GET /docs/signals 或 /docs/signals/{name}）返回的 `data_requirements.freq` 及输出键名（如 `日线_xxx_yyy`）已包含周期信息，可由服务端据此取数。

---

## Phase 1: 前端去除周期选择

**Purpose**: 添加信号时不再展示「周期」表单项；每条信号的周期由该信号的 `data_requirements.freq` 决定（无则默认「日线」），前端仍按周期分组调用批量接口。

- [X] T001 去除添加信号弹窗中的「周期」表单项：在「添加信号」弹窗中删除「周期」的 `el-form-item` 与 `el-select`，移除 `addDialogFreq` 的 ref、初始化及表单项绑定（`frontend/src/views/StockAnalyze.vue`）
- [X] T002 添加信号时周期取自 data_requirements：在 `confirmAdd` 中，每条已选信号的 `freq` 使用 `s.data_requirements?.freq ?? '日线'`，不再使用弹窗周期；`openAddDialog` 中不再设置 `addDialogFreq`（`frontend/src/views/StockAnalyze.vue`）
- [X] T003 已选信号展示保留周期标签：已选信号 tag 中继续展示 `({{ item.freq }})`，便于用户确认该信号将使用的 K 线周期（数据来自 data_requirements 或默认）（`frontend/src/views/StockAnalyze.vue`）

---

## Phase 2: 服务端按信号周期取数（可选增强）

**Purpose**: 批量接口支持「按配置周期」取数：请求体可包含多条不同周期的信号配置，服务端按周期分组、分别拉取 K 线并计算，前端可一次请求多周期信号。

- [ ] T004 批量请求支持按配置的 freq 分组：扩展 `BatchSignalRequest`，使 `freq` 变为可选；若未传，则从 `signal_configs` 中每条配置的 `freq` 字段解析周期（若配置无 `freq`，则通过 doc 服务查询该信号名的 `data_requirements.freq`），按 freq 分组（`backend/src/models/schemas.py`）
- [ ] T005 服务端按周期分组拉取 K 线并计算：在 `SignalService.calculate_batch` 中，若请求未带顶层 `freq`，则按 T004 得到的分组，对每个 freq 分别调用现有「单 freq + 多 config」逻辑（get_bars + calculate_signals），合并多组信号的返回结果后返回（`backend/src/services/signal_service.py`）
- [ ] T006 前端可选一次提交多周期信号：若保留当前「按 freq 分组、多次调用 batch」的方式，则 Phase 1 已满足「去除周期选择、由 data_requirements 决定周期」；若需改为单次 batch 提交所有信号，则前端将已选列表按 `item.freq` 填入各 `signal_configs[].freq`，并调用支持「无顶层 freq」的 batch 接口（`frontend/src/views/StockAnalyze.vue`、`frontend/src/api/signals.ts`）

---

## Dependencies & Execution Order

- **Phase 1**：无依赖，T001 → T002 → T003 顺序执行即可。
- **Phase 2**：依赖 Phase 1；T004 → T005，T006 依赖 T004/T005（若不做 T006，仅后端扩展也可由其他客户端使用）。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_signal_analyze_no_freq_choice_server_freq.md` |
| **总任务数** | 6 |
| **Phase 1** | 前端去除周期选择，周期由 data_requirements 决定 |
| **Phase 2** | 服务端按信号周期分组取数（可选） |
| **建议顺序** | T001 → T002 → T003；可选 T004 → T005 → T006 |
