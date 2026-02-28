# Tasks: 文案图形增强（hAlign/vAlign + 上下位置与距离 + 连接线）

**Input**: 用户需求「文案的是否有 hAlign、vAlign 属性，增加一个文案在 k 线图上方、下方的属性及距离，再画一条链接文字的线」。  
**Prerequisites**: 现有 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`，文案（text）已支持 createShape(shape:'text') 及 TextLineToolOverrides。

**Organization**: US1 确认并完善文案对齐与位置；US2 增加“上下位置+距离”与“锚点→文案”连接线。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行
- **[Story]**: US1 = 文案对齐与属性确认，US2 = 上下位置、距离与连接线
- 描述中需包含具体文件路径

---

## Phase 1: 文案 hAlign / vAlign 确认与文档

**Purpose**: 确认文案已暴露 hAlign、vAlign，并在文档中说明含义；若 d.ts 有对应 override 键则一并对接。

**Independent Test**: 侧栏可调 hAlign（left/center/right）、vAlign（top/middle/bottom），刷新后文案对齐方式生效。

- [x] T001 确认 `frontend/src/views/ChartShapesDemo.vue` 中 cfg.text 已包含 hAlign、vAlign，且 buildShapesFromPoints 中 text 的 style 已传入二者；若未传入 createShape 的 overrides，则对照 `frontend/charting_library/charting_library.d.ts` 的 TextLineToolOverrides 检查是否有 horizontalAlignment/verticalAlignment 等键需映射，并在 `frontend/src/tv/chartShapes.ts` 的 buildTextLineToolOverrides 或 drawText 中按需传入
- [x] T002 在 `frontend/src/tv/README-shapes.md` 的 TextLineToolOverrides 或「各图形必要属性」中注明：文案支持 hAlign（文案自身相对锚点水平对齐）、vAlign（文案自身相对锚点垂直对齐）；若 TV 库不支持 override 则说明为 Demo 侧逻辑（锚点+偏移计算）

---

## Phase 2: User Story 1 - 文案对齐与属性（P1）

**Goal**: 文案具备 hAlign、vAlign 且行为与侧栏一致；文档已更新。

**Independent Test**: 修改 hAlign/vAlign 后刷新图形，文案相对锚点对齐方式正确。

- [x] T003 [US1] 在 `frontend/src/tv/chartShapes.ts` 中确保 ShapeText.style 的 hAlign、vAlign 在 drawText 时被使用：若 charting_library 的 createShape(text) 支持文本对齐 override，则通过 withPrefix(PREFIX.text, { … }) 传入；若不支持，则在 `frontend/src/views/ChartShapesDemo.vue` 侧栏对 hAlign/vAlign 增加简短说明（如「部分版本由锚点与 fixedSize 决定，以实际效果为准」），文件路径 `frontend/src/tv/chartShapes.ts`、`frontend/src/views/ChartShapesDemo.vue`

---

## Phase 3: User Story 2 - 文案在 K 线图上方/下方及距离（P1）

**Goal**: 侧栏可选项：文案相对锚点置于「上方」或「下方」，以及偏移距离（如价格比例或像素）；文案绘制位置 = 锚点 + 垂直偏移。

**Independent Test**: 选择「上方」+ 距离 2%，文案出现在锚点上方且与锚点保持约 2% 价格差；选择「下方」同理。

- [x] T004 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg.text 中新增 verticalPlacement（'on' | 'above' | 'below'）与 offsetPercent（数字，如 1 表示 1% 价格距离）；在侧栏增加两个表单项：文案相对锚点「上下」选择（on/above/below）、「距离(%)」数字输入；在 buildShapesFromPoints 中计算文案显示点：当 verticalPlacement 为 above 时 point = 锚点 + (price * offsetPercent/100)；为 below 时 point = 锚点 - (price * offsetPercent/100)；on 时保持原锚点，文件路径 `frontend/src/views/ChartShapesDemo.vue`
- [x] T005 [US2] 在 `frontend/src/tv/chartShapes.ts` 中扩展 ShapeText：增加可选字段 anchorPoint（ChartPoint）、verticalPlacement（'on'|'above'|'below'）、offsetPercent（number）；当 anchorPoint 与 verticalPlacement 存在且非 'on' 时，由 anchorPoint 与 offsetPercent 计算实际绘制点 point，再调用 createShape(point, text)。若 Demo 采用「单点 + 偏移」方案（无 anchorPoint 分离），则仅在 Vue 中计算新 point 传入现有 ShapeText.point 即可，文件路径 `frontend/src/tv/chartShapes.ts`

---

## Phase 4: User Story 2 - 画一条连接文字的线（P1）

**Goal**: 当文案使用「上方」或「下方」偏移时，自动绘制一条从锚点到文案位置的线段（trend_line），形成“锚点—线—文案”的标注效果。

**Independent Test**: 选择文案 above/below + 距离后刷新，图上出现从锚点指向文案的一条线段，且文案在线段末端。

- [x] T006 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 的 buildShapesFromPoints 中，当文案的 verticalPlacement 为 'above' 或 'below' 且 offsetPercent > 0 时，除添加 ShapeText 外，添加一条 ShapeLine（或 trend_line 两点）：p1 = 锚点，p2 = 计算出的文案显示点；线样式可与文案颜色一致或使用 cfg 中新增的 connectorLineColor/connectorLineWidth，文件路径 `frontend/src/views/ChartShapesDemo.vue`
- [x] T007 [US2] 在 `frontend/src/tv/chartShapes.ts` 的 drawChartShapes 中保证顺序：若 shapes 数组内同一“标注”包含一条 line 与一个 text，先绘制 line 再绘制 text，使连接线在文案下层；若 Demo 采用「单次 buildShapes 返回 [line, text]」则无需改 drawChartShapes 顺序，文件路径 `frontend/src/tv/chartShapes.ts`
- [x] T008 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 侧栏为「连接线」增加可选样式：连接线颜色、线宽（或复用 ray 的 color/width）；默认与文案 color 一致、线宽 1，文件路径 `frontend/src/views/ChartShapesDemo.vue`

---

## Phase 5: Polish & 文档

**Purpose**: 侧栏说明清晰、README 与类型定义一致。

- [x] T009 在 `frontend/src/tv/README-shapes.md` 中更新文案一节：说明文案支持 hAlign、vAlign；支持 verticalPlacement（on/above/below）与 offsetPercent；当 above/below 时可选绘制锚点至文案的连接线；连接线样式可配置
- [x] T010 [P] 在 `frontend/src/views/ChartShapesDemo.vue` 的「单点文案」侧栏顶部增加一两句说明：hAlign/vAlign 为文案相对锚点对齐；上下与距离用于将文案放在锚点上方或下方；勾选或选择「上方/下方」时可显示连接线

---

## Dependencies & Execution Order

- **Phase 1**：T001、T002 可并行。
- **Phase 2 (US1)**：依赖 Phase 1；T003 单任务。
- **Phase 3 (US2)**：T004、T005 顺序或并行（Vue 计算 point 与 chartShapes 扩展类型）。
- **Phase 4 (US2)**：依赖 Phase 3；T006、T007、T008 顺序执行（先 Vue 再 chartShapes 再 Vue 样式）。
- **Phase 5**：依赖 Phase 2、3、4；T009、T010 可并行。

---

## Implementation Strategy

### MVP（优先）

1. Phase 1–2：确认 hAlign/vAlign 并文档化。
2. Phase 3：实现文案「上方/下方」与距离（offsetPercent）。
3. Phase 4：实现锚点→文案连接线及可选样式。
4. Phase 5：文档与侧栏说明。

### 验收要点

- 文案有 hAlign、vAlign 且行为符合预期。
- 文案可置于锚点上方或下方，距离可调（如 offsetPercent）。
- 当使用 above/below 时，可画一条从锚点到文案的连接线，线样式可配。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T003；US2: T004–T008；Phase 1、Phase 5 无 Story 标签。
