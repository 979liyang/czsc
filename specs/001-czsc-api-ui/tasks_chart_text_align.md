# Tasks: 文案图形对齐与连接线距离细化

**Input**: 用户需求「文案图形，自身的 hAlign、vAlign 没有生效，连接线距离 k 线图上方和下方可以设置距离，如果文案在上方时文案在连接线的上方并且能设置距离连接线的距离，我希望文案居中对齐」。  
**Prerequisites**: 现有 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`，文案已支持 verticalPlacement、offsetPercent、连接线及 hAlign/vAlign 传入 style。

**Organization**: US1 让 hAlign/vAlign 生效并默认居中对齐；US2 拆分“连接线长度”与“文案距连接线距离”，并保证上方时文案在连接线之上且可设间距。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行
- **[Story]**: US1 = 文案对齐生效与居中，US2 = 连接线/文案距离拆分
- 描述中需包含具体文件路径

---

## Phase 1: 文案 hAlign/vAlign 生效（US1）

**Purpose**: 查清 charting_library 对 createShape(shape:'text') 是否支持对齐 override；若支持则传入并生效，若不支持则通过“锚点偏移”模拟居中并文档说明。

**Independent Test**: 侧栏选择 hAlign center、vAlign middle 后刷新，文案相对锚点呈居中对齐；修改为 left/top 后文案相对锚点左/上对齐。

- [x] T001 在 `frontend/charting_library/charting_library.d.ts` 中搜索与 text 相关的 override 键（如 linetooltext.*、text.*、alignment、anchor、pivot 等）；若存在水平/垂直对齐相关键，在 `frontend/src/tv/chartShapes.ts` 的 buildTextLineToolOverrides 或 drawText 的 overrides 中传入 hAlign、vAlign（或库要求的键名），并在 `frontend/src/views/ChartShapesDemo.vue` 侧栏说明「对齐由 override 控制」
- [x] T002 [US1] 若 d.ts 无对齐键：在 `frontend/src/tv/chartShapes.ts` 的 drawText 中，将 shape.style.hAlign、shape.style.vAlign 尝试以 linetooltext.hAlign、linetooltext.vAlign 或库文档中的键名加入 overrides 并 setProperties；若仍不生效，在 `frontend/src/tv/README-shapes.md` 中注明「hAlign/vAlign 当前由 Demo 传入，部分 TV 版本可能不生效，建议使用居中以减少偏差」，并将默认值设为 hAlign: 'center'、vAlign: 'middle'，文件路径 `frontend/src/tv/chartShapes.ts`、`frontend/src/views/ChartShapesDemo.vue`
- [x] T003 [US1] 在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg.text 中将 hAlign、vAlign 默认值设为 'center'、'middle'，并在侧栏文案说明中写「希望文案居中对齐时请选 center / middle」，文件路径 `frontend/src/views/ChartShapesDemo.vue`

---

## Phase 2: 连接线长度与“文案距连接线”距离拆分（US2）

**Purpose**: 将当前“一个 offsetPercent”拆为两项：① 连接线长度（锚点到线末端的距离，占价格比例）；② 文案距连接线的距离（线末端到文案位置的距离）。上方时：锚点 → 连接线 → 再向上偏移一段为文案位置。

**Independent Test**: 设置「连接线长度 2%」「文案距连接线 0.5%」、选择上方后，连接线长度为锚点价格的 2%，文案在线末端上方 0.5% 价格处且居中对齐。

- [x] T004 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 的 cfg.text 中新增 connectorLengthPercent（连接线长度，价格比例，如 2 表示 2%）与 textGapPercent（文案距连接线距离，价格比例，如 0.5 表示 0.5%）；保留原 offsetPercent 作为兼容或重命名为仅用于“仅文案偏移无连接线”的简用；侧栏表单项改为「连接线长度(%)」「文案距连接线(%)」，并加简短说明，文件路径 `frontend/src/views/ChartShapesDemo.vue`
- [x] T005 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 的 buildShapesFromPoints 中重算文案与连接线逻辑：当 verticalPlacement 为 'above' 时，lineEnd = 锚点 + (锚点价格 * connectorLengthPercent/100)；textPoint = lineEnd + (锚点价格 * textGapPercent/100)；连接线为 anchor → lineEnd；文案在 textPoint。当为 'below' 时，lineEnd = 锚点 - connectorLengthPercent；textPoint = lineEnd - textGapPercent。当为 'on' 时保持原逻辑（无连接线）。保证「上方时文案在连接线的上方并可设距离」，文件路径 `frontend/src/views/ChartShapesDemo.vue`
- [x] T006 [US2] 若保留 offsetPercent 单参数兼容：当 connectorLengthPercent 与 textGapPercent 未设置时，用 offsetPercent 作为连接线长度、textGapPercent 取 0；或在侧栏隐藏 offsetPercent，统一使用 connectorLengthPercent + textGapPercent，文件路径 `frontend/src/views/ChartShapesDemo.vue`

---

## Phase 3: Polish & 文档

**Purpose**: 侧栏与 README 表述一致，默认居中对齐。

- [x] T007 在 `frontend/src/tv/README-shapes.md` 中更新文案一节：说明 hAlign/vAlign 若库支持则传入 overrides 生效，否则默认 center/middle；连接线长度与文案距连接线距离分别由 connectorLengthPercent、textGapPercent 控制；上方时文案在连接线之上、下方时在连接线之下，文件路径 `frontend/src/tv/README-shapes.md`
- [x] T008 [P] 在 `frontend/src/views/ChartShapesDemo.vue` 侧栏「单点文案」中补充一句：居中对齐请选 hAlign=center、vAlign=middle；连接线长度与文案距连接线的距离可分别调节，文件路径 `frontend/src/views/ChartShapesDemo.vue`

---

## Dependencies & Execution Order

- **Phase 1**：T001 先查 d.ts；T002、T003 依赖 T001 结论，可顺序执行。
- **Phase 2**：T004、T005、T006 顺序执行（先 cfg 与侧栏，再 buildShapesFromPoints 逻辑）。
- **Phase 3**：T007、T008 可并行。

---

## Implementation Strategy

### MVP（优先）

1. Phase 1：查库是否支持对齐 → 传入 overrides 或默认 center/middle 并文档说明。
2. Phase 2：拆分连接线长度与文案距连接线距离，上方时文案在线之上且可设间距。
3. Phase 3：文档与侧栏说明更新。

### 验收要点

- 文案 hAlign、vAlign 能生效或默认居中（center/middle）。
- 连接线长度（相对 K 线图锚点）可单独设置；文案距连接线的距离可单独设置。
- 文案在上方时位于连接线上方，且可调该距离；居中对齐可用。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T002、T003；US2: T004、T005、T006；Phase 1（T001）、Phase 3 无 Story 标签。
