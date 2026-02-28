# Tasks: ChartShapesDemo 图形属性检测与查漏补缺

**Input**: 用户需求「再检测这些图形属性，如果没有则去除，如果缺少则增加；是否有遗漏的图形或其他信号标记」。  
**Prerequisites**: 现有 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`、`frontend/src/tv/README-shapes.md`、`frontend/charting_library/charting_library.d.ts`。

**Organization**: 按“属性审计”“去除无效”“补全缺失”“遗漏图形/信号标记”分阶段，便于逐项执行与验收。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: US1= 去除无效属性，US2= 补全缺失属性，US3= 遗漏图形与信号标记
- 描述中需包含具体文件路径

## 路径约定

- 前端：`frontend/src/`
- 类型定义：`frontend/charting_library/charting_library.d.ts`

---

## Phase 1: 属性检测（对照 d.ts）

**Purpose**: 逐图形对照 charting_library.d.ts 的 *LineToolOverrides，列出 Demo 中“多出的属性”（d.ts 不存在则标记去除）与“缺失的属性”（d.ts 有但 Demo 未暴露则标记补全）。

- [x] T001 对照 `frontend/charting_library/charting_library.d.ts` 中 TextLineToolOverrides（linetooltext.*）：列出 `frontend/src/views/ChartShapesDemo.vue` 的 cfg.text 及模板绑定；若存在 d.ts 中无的键（如 fontsize 与 fontSize 重复则统一为 fontsize）则标记为待去除；若 d.ts 有但 cfg 未暴露则标记为待补全（如无则无需改）
- [x] T002 对照 VertlineLineToolOverrides（linetoolvertline.*）、HorzlineLineToolOverrides（linetoolhorzline.*）、FlagmarkLineToolOverrides（linetoolflagmark.*）、Arrowmarkup/ArrowmarkdownLineToolOverrides、TriangleLineToolOverrides、CircleLineToolOverrides：对每个图形在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg 与侧栏列出当前键，与 d.ts 属性逐一对比，产出清单「多出：xxx」「缺失：xxx」写入 `frontend/src/tv/README-shapes.md` 或临时文档
- [x] T003 对照 TrendlineLineToolOverrides（本 Demo 用于 trend_line 与水平射线）：检查 cfg.ray 与 chartShapes 中 horizontal_ray 使用的 overrides 键是否均在 d.ts 中存在；若 Demo 使用 lengthDays/labelText 等非 override 的 UI 逻辑则保留；若传入的 overrides 中有 d.ts 不存在的键则标记去除
- [x] T004 对照矩形：charting_library.d.ts 中无独立 RectangleLineToolOverrides 时，确认 `frontend/src/tv/chartShapes.ts` 中 rectangle 使用的 overrides（如 fillBackground、backgroundColor、transparency、linewidth、color）是否与 d.ts 中 Dateandpricerange/Daterange 或实际可用的键一致；若当前键在库中有效则保留，否则在 T002 清单中注明

---

## Phase 2: User Story 1 - 去除无效属性 (P1)

**Goal**: 从 cfg、模板及 chartShapes 的 overrides 构建逻辑中移除 d.ts 不存在的属性，避免无效传参。

**Independent Test**: 打开 ChartShapesDemo，切换各图形并“刷新图形”，控制台无报错；修改任意已保留参数后图形样式按预期变化。

- [x] T005 [US1] 根据 T001–T004 的「多出」清单，在 `frontend/src/views/ChartShapesDemo.vue` 中从 cfg 与对应模板（v-model 及 buildShapesFromPoints 中的 style 引用）移除 d.ts 不存在的 override 键；若某键为“展示用”且不传入 overrides（如 content、radiusPercent）则保留 cfg 与 UI，仅确保不将其作为 linetool 键传入
- [x] T006 [US1] 在 `frontend/src/tv/chartShapes.ts` 中检查各 draw 函数（drawText、drawRectangle、drawHorizontalRay、drawArrow、drawTriangle、drawVerticalLine、drawHorizontalLine、drawFlag、drawCircle）传入的 withPrefix 对象：移除 d.ts 对应 *LineToolOverrides 中不存在的键，保留键名与 d.ts 一致（如 linecolor 而非 color，若库同时接受短名则可保留短名）

---

## Phase 3: User Story 2 - 补全缺失属性 (P1)

**Goal**: 为每个已支持图形补全 d.ts 中有但 Demo 未暴露的 Overrides 属性，使侧栏可调项与 d.ts 一致。

**Independent Test**: 每个图形在侧栏均有 d.ts 所列主要可调项（如 horzline 的 fontsize、horzLabelsAlign、italic、textcolor、vertLabelsAlign）；刷新图形后 overrides 生效。

- [x] T007 [US2] 为水平线（horizontalLine）在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg 与侧栏补全 HorzlineLineToolOverrides 缺失项：fontsize、horzLabelsAlign、italic、textcolor、vertLabelsAlign（若尚未存在）；在 buildShapesFromPoints 中将这些键传入 shape.style，并在 `frontend/src/tv/chartShapes.ts` 的 drawHorizontalLine 中写入 overrides
- [x] T008 [US2] 为竖线（verticalLine）、箭头（arrow）、三角形（triangle）、圆（circle）、射线（ray）同理补全：对照 VertlineLineToolOverrides、Arrowmarkup/Arrowmarkdown、TriangleLineToolOverrides、CircleLineToolOverrides、TrendlineLineToolOverrides 与 HorzrayLineToolOverrides，将缺失的键加入 cfg、侧栏与 draw 中的 overrides，文件路径 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`
- [x] T009 [US2] 为矩形（rect）补全：若 d.ts 中矩形类图形有 transparency 以外的键（如 linecolor、linestyle 等），在 cfg.rect 与 drawRectangle 的 withPrefix 中补全，文件路径同上

---

## Phase 4: User Story 3 - 遗漏图形与信号标记 (P2)

**Goal**: 补全 createShape/createMultipointShape 中尚未在 Demo 支持的图形，以及常用“信号标记”类 shape（如 price_label、arrow_marker、cross_line 等）。

**Independent Test**: 侧栏可选新增图形类型；选择后图上能正确绘制；新增图形具备至少 1 个可调参数。

- [ ] T010 [US3] 在 `frontend/src/tv/chartShapes.ts` 中为 createShape 尚未支持的 icon、emoji、sticker、note 增加 Shape 类型与 draw 实现（shape 名分别为 icon、emoji、sticker、note；overrides 前缀 linetoolicon、linetoolemoji、linetoolsticker、linetoolcomment）；在 `frontend/src/views/ChartShapesDemo.vue` 的 SHAPE_SECTIONS、cfg 与 buildShapesFromPoints 中增加上述四项的入口与参数（至少 color/angle/text 等主要键），文件路径 `frontend/src/tv/chartShapes.ts`、`frontend/src/views/ChartShapesDemo.vue`
- [ ] T011 [US3] 在 `frontend/src/tv/chartShapes.ts` 中为 ellipse、ray、extended、polyline、path、curve 增加 Shape 类型与 draw 实现（createMultipointShape，shape 名以 SupportedLineTools 为准）；在 `frontend/src/views/ChartShapesDemo.vue` 的 SHAPE_SECTIONS 与 buildShapesFromPoints 中增加上述类型的入口与点位逻辑（ellipse 至少两点、polyline/path/curve 多点），文件路径同上
- [x] T012 [US3] 检查 charting_library.d.ts 的 SupportedLineTools 与 CreateShapeOptions.shape：列出“信号标记”类（如 price_label、price_note、arrow_marker、cross_line、signpost 等）；若需在 Demo 中支持，在 `frontend/src/tv/chartShapes.ts` 与 `frontend/src/views/ChartShapesDemo.vue` 中增加对应 Shape、draw、SHAPE_SECTIONS、cfg 与 buildShapesFromPoints 分支；若本迭代不实现则仅在 `frontend/src/tv/README-shapes.md` 中注明“未实现信号标记：price_label, arrow_marker, cross_line, signpost…”
- [x] T013 [US3] 更新「可绘制图形一览」与 README-shapes.md：已对接的 createShape 列表含 icon、emoji、sticker、note；createMultipointShape 列表含 ellipse、ray、extended、polyline、path、curve；若有遗漏的图形或信号标记在文档中单独列出，文件路径 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/README-shapes.md`

---

## Phase 5: Polish & 一致性

**Purpose**: 确保 ALL_LINETOOLS、可绘制图形一览与 d.ts 一致；属性检测结果归档。

- [x] T014 在 `frontend/src/views/ChartShapesDemo.vue` 中核对 ALL_LINETOOLS 数组与 `frontend/charting_library/charting_library.d.ts` 的 DrawingOverrides 联合类型：若有 d.ts 已删除的 linetool 则从 ALL_LINETOOLS 移除；若有新增的 *LineToolOverrides 则补入，保证「所有图形」列表与 d.ts 全量一致
- [x] T015 [P] 在 `frontend/src/tv/README-shapes.md` 中增加一节「属性审计结果」：记录本次检测中“已去除的无效属性”与“已补全的缺失属性”及对应图形；并列出“未实现的图形/信号标记”（若有），便于后续迭代

---

## Dependencies & Execution Order

- **Phase 1**：无依赖，T001–T004 可并行（按图形分工）。
- **Phase 2 (US1)**：依赖 Phase 1 的清单；T005、T006 可顺序执行（先 Vue 再 chartShapes，或先 chartShapes 再 Vue）。
- **Phase 3 (US2)**：依赖 Phase 2；T007、T008、T009 可按图形并行。
- **Phase 4 (US3)**：依赖 Phase 2；T010、T011 可并行；T012、T013 依赖 T010/T011 或与文档同步。
- **Phase 5**：依赖 Phase 2、3、4；T014、T015 可并行。

### Parallel Opportunities

- T001 与 T002、T003、T004；T007 与 T008、T009（按图形）；T010 与 T011；T014 与 T015。

---

## Implementation Strategy

### MVP（优先）

1. Phase 1：完成属性检测清单（多出/缺失）。
2. Phase 2：去除无效属性，避免传错键。
3. Phase 3：补全缺失属性，使已有图形参数完整。
4. Phase 4、5：按需补充遗漏图形与文档。

### 验收要点

- **属性**：每个已支持图形的 cfg 与传入 overrides 的键均在 d.ts 对应 *LineToolOverrides 中存在；d.ts 有且常用的键在侧栏可调。
- **图形**：无遗漏的 createShape 单点类型（或已在文档标明未实现）；多点类型 ellipse、ray、extended、polyline、path、curve 至少部分实现或文档说明。
- **信号标记**：若实现则 Demo 可选；若不实现则 README-shapes 中列出 price_label、arrow_marker、cross_line 等供后续扩展。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T005、T006；US2: T007、T008、T009；US3: T010、T011、T012、T013；Phase 1、Phase 5 无 Story 标签。
