# Tasks: 信号分析页——选择类型后信号列表展示名称与详情

**Input**: 在 http://localhost:5173/signal-analyze 添加信号弹窗中，选择类型之后，信号选择区除展示信号名称外，同时展示信号详情（如描述、参数摘要等）。  
**Path Conventions**: 前端 `frontend/src/`（与 plan.md 一致）。

**现状简述**:
- 当前「添加信号」弹窗中，选类型后信号下拉为 `el-select` + `el-option`，`:label="s.name"` 仅展示信号名，无描述等详情。
- GET /docs/signals 返回的 SignalInfo 已含 name、description、params、signals（输出键）等，可直接用于展示。

---

## Phase 1: 实现（单阶段）

**Purpose**: 选择类型后，信号选择区展示信号名称与详情，便于用户区分与选择。

**Independent Test**: 打开 /signal-analyze → 点击加号 → 选择某一类型 → 信号列表可见每项为「名称 + 详情」（如一行描述或参数摘要）；多选、添加、分析流程不受影响。

- [X] T001 信号选项展示名称与详情：在「添加信号」弹窗的信号选择区，由单一 `el-select`+`el-option`（仅 name）改为支持展示详情：要么使用 `el-option` 的自定义 slot 在每项中展示信号名 + 一行描述（或 description 截断），要么改为「类型下信号列表」用 `el-scrollbar`+ 卡片/列表项展示 name 与 description（及可选 params 摘要），选择方式保持多选（如 checkbox）。确保已选信号仍可正确加入、分析请求不变（`frontend/src/views/StockAnalyze.vue`）

---

## Dependencies & Execution Order

- 无依赖，单任务即可完成。

---

## 格式校验

- 任务满足：`- [ ]` + TaskID + 描述 + 文件路径。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_signal_analyze_option_detail.md` |
| **总任务数** | 1 |
| **建议** | 实现后勾选 T001 为 [X]，自测添加信号与分析流程 |
