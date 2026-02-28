# Tasks: 信号周期与基础周期改为 select 可选

**Input**: 策略分析页中「信号周期」「基础周期」由输入框改为下拉选择（select），选项与 czsc 常用周期一致。

**Path Conventions**: 后端 `backend/src/`，前端 `frontend/src/`。

**现状简述**:
- `backend/src/services/strategy_params_schema.py` 中 `freq`、`base_freq` 为 string 类型、无 options，前端策略分析页渲染为 el-input。
- 需：为 freq/base_freq 提供 options（如 1分钟、5分钟、15分钟、30分钟、60分钟、日线），前端对带 options 的参数优先渲染为 el-select。

---

## Phase 1: 后端 schema 为 freq/base_freq 增加 options

**Purpose**: 通用参数中 freq、base_freq 增加 options 列表，供前端下拉展示。

**Independent Test**: GET /api/v1/strategies 任一条策略的 params_schema 中，freq 与 base_freq 项均含 options 数组（如 ["1分钟","5分钟","15分钟","30分钟","60分钟","日线"]）。

- [x] T001 在 `backend/src/services/strategy_params_schema.py` 的 _COMMON 中，将 freq 与 base_freq 两项改为带 options：options 为 ["1分钟", "5分钟", "15分钟", "30分钟", "60分钟", "日线"]，default 保持 "15分钟"（`backend/src/services/strategy_params_schema.py`）

---

## Phase 2: 前端策略参数对带 options 的项渲染为 select

**Purpose**: 策略分析页中，凡 params_schema 中带 options 的字段（含 freq、base_freq）均用 el-select 展示，而非输入框。

**Independent Test**: 打开策略分析页、选择任意策略后，参数区「信号周期」「基础周期」为下拉选择框，可选 1分钟/5分钟/15分钟/30分钟/60分钟/日线。

- [x] T002 在 `frontend/src/views/StrategyAnalyze.vue` 策略参数表单项中，将「带 options 的项用 el-select」分支放在「string 用 el-input」之前（即先判断 `p.options && p.options.length`，再判断 type），使 freq/base_freq 等带 options 的 string 渲染为下拉（`frontend/src/views/StrategyAnalyze.vue`）

---

## Dependencies & Execution Order

- **Phase 1** → **Phase 2**：先有 schema 的 options，前端才能展示 select。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。
