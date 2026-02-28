# Tasks: ChartShapesDemo 图形属性精简（去除没必要属性）

**Input**: 用户需求「完善图形和去除没必要的属性，比如圆形没有 italic bold」。  
**Prerequisites**: 现有 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`、`frontend/src/tv/README-shapes.md`、`frontend/charting_library/charting_library.d.ts` 及已完成属性审计（tasks_chart_shapes_audit.md）。

**Organization**: 按图形逐项去除“对该图形无视觉影响”的 override 与侧栏项，使每类图形仅保留必要属性。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行
- **[Story]**: US1 = 图形属性精简
- 描述中需包含具体文件路径

---

## Phase 1: 必要属性清单

**Purpose**: 对照 d.ts 与图形实际视觉效果，确定每类图形“必须保留”的 override 键；其余（如圆形的 bold/italic/fontSize/textColor）标记为去除。

- [x] T001 确定圆（circle）必要属性：createMultipointShape(shape:'circle') 仅绘制圆与填充，不显示文字时，仅保留 color、backgroundColor、fillBackground、linewidth；从 Demo 与 chartShapes 中移除 bold、italic、fontSize、textColor 的 cfg、侧栏、style 与 overrides。将结论写入 `frontend/src/tv/README-shapes.md` 的「属性审计结果」或新增「各图形必要属性」小节
- [x] T002 确定其余图形必要属性：对 triangle、arrow、verticalLine、horizontalLine、flag、rect、ray、text 逐一判断——仅保留对该图形有直接视觉影响的键（如 triangle 保留 color/backgroundColor/fillBackground/linewidth/transparency，不保留文字相关键若该图形不显示文字）。列出「保留」与「去除」清单，写入 `frontend/src/tv/README-shapes.md`

---

## Phase 2: User Story 1 - 圆（circle）去除多余属性

**Goal**: 圆仅保留边框/填充相关属性，去除 bold、italic、fontSize、textColor。

**Independent Test**: 打开 ChartShapesDemo，选择「圆」，侧栏无 bold/italic/fontSize/textColor 控件；刷新图形后圆显示正常，控制台无报错。

- [x] T003 [US1] 在 `frontend/src/views/ChartShapesDemo.vue` 中从 cfg.circle 移除 bold、italic、fontSize、textColor；从圆形的侧栏模板中删除上述四项的表单项（label+input）；在 buildShapesFromPoints 中构造 circle 的 style 时不再传入 bold、italic、fontSize、textColor
- [x] T004 [US1] 在 `frontend/src/tv/chartShapes.ts` 中：从 ShapeCircle.style 类型中移除 bold、italic、fontSize、textColor；在 drawCircle 的 withPrefix 与 overrides 中仅保留 backgroundColor、color、fillBackground、linewidth，不再传入 bold、italic、fontSize、textColor

---

## Phase 3: User Story 1 - 其余图形去除多余属性

**Goal**: 三角形、箭头、竖线、水平线、旗帜、矩形、射线、文案等仅保留对各自有视觉影响的属性。

**Independent Test**: 各图形侧栏无“对该图形无影响”的控件；刷新图形后显示与行为正常。

- [x] T005 [US1] 三角形（triangle）：若 d.ts 的 TriangleLineToolOverrides 无文字相关键，则 `frontend/src/views/ChartShapesDemo.vue` 与 `frontend/src/tv/chartShapes.ts` 中不暴露/不传入文字相关 override；若有则保留。当前 triangle 仅有 backgroundColor、color、fillBackground、linewidth、transparency、sizePercent，无文字键则无需改
- [x] T006 [US1] 箭头（arrow）、竖线（verticalLine）、水平线（horizontalLine）、旗帜（flag）：对照 T002 清单，在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg 与侧栏、以及 `frontend/src/tv/chartShapes.ts` 的 shape.style 与 draw 中移除对该图形无视觉影响的键（例如某图形不显示标签则移除 fontsize、textcolor、horzLabelsAlign 等）
- [x] T007 [US1] 矩形（rect）、射线（ray）、文案（text）：文案保留全部 TextLineToolOverrides；矩形与射线仅保留与线段/填充相关的键，去除多余项（若有）。文件路径同上

---

## Phase 4: Polish & 文档

**Purpose**: 文档与类型定义一致，侧栏说明简洁。

- [x] T008 在 `frontend/src/tv/README-shapes.md` 中更新「各图形必要属性」或「属性审计结果」：标明圆仅保留 color、backgroundColor、fillBackground、linewidth；已去除 bold、italic、fontSize、textColor；其余图形按 T002/T005–T007 结论更新
- [x] T009 [P] 在 `frontend/src/views/ChartShapesDemo.vue` 中为「圆」侧栏增加简短说明（如「仅边框与填充，无文字样式」），避免用户误以为缺少配置

---

## Dependencies & Execution Order

- **Phase 1**：T001、T002 可并行。
- **Phase 2**：依赖 Phase 1 结论；T003、T004 顺序执行（先 Vue 再 chartShapes）。
- **Phase 3**：依赖 Phase 2；T005、T006、T007 可按图形并行。
- **Phase 4**：依赖 Phase 2、3；T008、T009 可并行。

---

## Implementation Strategy

### MVP（优先）

1. Phase 1：完成圆与其余图形的必要属性清单。
2. Phase 2：圆去除 bold、italic、fontSize、textColor（代码 + 侧栏）。
3. Phase 3：其余图形按清单精简。
4. Phase 4：更新文档与说明。

### 验收要点

- 圆：侧栏无 bold、italic、fontSize、textColor；overrides 仅含 color、backgroundColor、fillBackground、linewidth。
- 其他图形：仅保留有视觉影响的属性，无多余控件与传参。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T003–T007；Phase 1、Phase 4 无 Story 标签。
