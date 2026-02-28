# Tasks: 信号分析页——去除默认周期、选择时展示信号详细说明与 outputs 选择

**Input**: signal-analyze 去除默认周期；选择信号时先选类型，再选具体信号时展示该信号的详细说明，并提供具体的 signals（输出键）选择。  
**Path Conventions**: 前端 `frontend/src/`（与 plan.md 一致）。

**现状简述**:
- 当前信号分析页有「默认周期」表单项，添加信号弹窗中有「周期」下拉，新加信号会使用 data_requirements.freq 或该周期。
- 选择类型后信号列表已展示名称+一行描述；SignalInfo 含 description、params、signals（该函数产出的信号键名列表），尚未在选信号时展示完整说明及 outputs 选择。

---

## Phase 1: 去除默认周期

**Purpose**: 主表单不再展示「默认周期」；添加信号时周期仅来源于弹窗内选择或信号 data_requirements。

- [X] T001 去除主表单默认周期：在信号分析页主表单中删除「默认周期」表单项（el-form-item + el-select）；添加信号弹窗内保留「周期」选择，新加信号的 freq 使用弹窗所选周期或该信号的 data_requirements.freq（`frontend/src/views/StockAnalyze.vue`）

---

## Phase 2: 选择具体信号时展示详细说明与 signals 选择

**Purpose**: 先选类型再选具体信号；选中或悬停某信号时展示其详细说明（描述、参数）；并提供该信号函数产出的一组 signals（输出键）供用户勾选，仅将用户勾选的 output 纳入展示或请求（若后端支持按 key 过滤则传参，否则前端按 key 过滤展示）。

- [X] T002 选中信号时展示详细说明：在「添加信号」弹窗中，当用户选中（或点击）某一信号时，在下方或侧旁展示该信号的详细说明：完整 description、params 列表（名称、类型、默认值）、以及该信号函数返回的 signals 列表（输出键名）。数据来自当前已加载的 addDialogSignalList 中对应项，无需额外请求；若需完整详情可调用 GET /docs/signals/{name}（`frontend/src/views/StockAnalyze.vue`）
- [X] T003 提供具体的 signals（输出键）选择：在添加信号流程中，当用户已选一个或多个信号函数后，对每个信号函数展示其 signals（输出键）列表，支持多选；确认添加时，将「信号函数 + 所选 outputs」一并加入已选列表（数据结构需含 selectedOutputs: string[]）。分析请求仍按当前 POST /signals/batch 发送，结果区展示时若存在 selectedOutputs 则仅展示这些 key 的 value，否则展示该信号函数返回的全部 key（`frontend/src/views/StockAnalyze.vue`）

---

## Dependencies & Execution Order

- **Phase 1**：无依赖。
- **Phase 2**：T002 与 T003 可同文件内顺序实现：先 T002（展示详细说明），再 T003（outputs 多选与结果过滤）。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_signal_analyze_no_default_freq_detail.md` |
| **总任务数** | 3 |
| **Phase 1** | 去除主表单「默认周期」 |
| **Phase 2** | 选信号时展示详细说明；提供 signals（输出键）多选并与结果展示联动 |
| **建议顺序** | T001 → T002 → T003 |
