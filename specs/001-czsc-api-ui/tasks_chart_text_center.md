# Tasks: 文案自身居中修复

**Input**: 用户需求「文案没有自身居中」；当前状态「文案还是没有居中」（T001–T005 已完成仍不生效）。  
**Prerequisites**: 现有 `frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`，文案已传 linetooltext.hAlign、linetooltext.vAlign，默认 cfg 为 center/middle，并已调用 entity.centerPosition?.()。

**Goal**: 使文案相对锚点呈现“自身居中”（水平居中 + 垂直居中）；若 TV 库 override 与 centerPosition 均不生效，则通过**选中居中时向左偏移锚点**（按文案宽度与时间轴坐标换算）保证水平居中。

## 格式说明：`[ID] [P?] [Story?] 描述`

- 描述中需包含具体文件路径

---

## Phase 1: 排查与尝试替代键

**Independent Test**: 选择「单点文案」、默认 center/middle，刷新后文案框相对锚点居中；改 left/top 后文案相对锚点左/上对齐。

- [x] T001 在 `frontend/charting_library/charting_library.d.ts` 中确认 TextLineToolOverrides 无 hAlign/vAlign 后，尝试其他线工具常用对齐键名：在 `frontend/src/tv/chartShapes.ts` 的 drawText 中除 linetooltext.hAlign、linetooltext.vAlign 外，增加尝试 linetooltext.horzLabelsAlign（值 center）、linetooltext.vertLabelsAlign（值 middle）；若库接受则保留并优先使用，使文案自身居中生效，文件路径 `frontend/src/tv/chartShapes.ts`
- [x] T002 在 `frontend/src/tv/chartShapes.ts` 的 drawText 中确保 createShape 后对同一 entity 调用 setProperties(overrides)，且 overrides 中包含所有已设置的对齐键（hAlign、vAlign 或 horzLabelsAlign、vertLabelsAlign）；若 TV 要求键名带 linetooltext 前缀则统一使用带前缀形式，文件路径 `frontend/src/tv/chartShapes.ts`
- [x] T003 在 `frontend/src/views/ChartShapesDemo.vue` 中强制默认 cfg.text.hAlign 为 'center'、cfg.text.vAlign 为 'middle'（若已为默认则保持不变）；侧栏在 hAlign/vAlign 旁增加提示「居中请选 center / middle，部分 TV 版本可能不生效」，文件路径 `frontend/src/views/ChartShapesDemo.vue`

---

## Phase 2: 文档与兜底说明

- [x] T004 在 `frontend/src/tv/README-shapes.md` 的文案一节注明：文案自身居中依赖 linetooltext 对齐键（hAlign/vAlign 或 horzLabelsAlign/vertLabelsAlign）；若当前 TV 版本不生效，属库限制，Demo 已传 center/middle，文件路径 `frontend/src/tv/README-shapes.md`

---

## Phase 3: 调用库内部 centerPosition 使居中生效

**Independent Test**: 同 Phase 1；选择 center/middle 并刷新后，文案框应相对锚点居中。

- [x] T005 在 `frontend/src/tv/chartShapes.ts` 的 drawText 中，createShape 且 setProperties 后，当 hAlign 为 'center' 且 vAlign 为 'middle' 时，对 getShapeById 得到的 entity 调用 `(entity as any).centerPosition?.()`（LineToolText 内部方法，会在下次渲染时按文本尺寸重算锚点使视觉居中）；若 entity 未暴露该方法则无副作用，文件路径 `frontend/src/tv/chartShapes.ts`

---

## Phase 4: 文案居中仍不生效时的跟进（延迟与锚点补偿）

**Independent Test**: 单点文案选择 center/middle 并刷新后，文案框视觉上相对锚点居中（或与锚点中心重合）。

- [x] T006 在 `frontend/src/tv/chartShapes.ts` 的 drawText 中，当 hAlign 为 'center' 且 vAlign 为 'middle' 时，在 createShape 与 setProperties 之后，用双次 `requestAnimationFrame` 及 `setTimeout(tryCenter, 80)` 兜底再调用 `(entity as any).centerPosition?.()`，确保在 TV 完成布局后再执行，使居中生效，文件路径 `frontend/src/tv/chartShapes.ts`
- [x] T006b 在 `frontend/src/tv/chartShapes.ts` 中当 hAlign 为 'center' 时，通过 timeToCoordinateX 与 measureTextWidthPx 计算锚点向左偏移（中心 x - 文案宽度/2 对应的时间），用偏移后的 (time, price) 调用 createShape，使文案视觉居中；已采用左偏移时不再调用 centerPosition，文件路径 `frontend/src/tv/chartShapes.ts`
- [ ] T007 若 T006 仍不生效：在 `frontend/src/tv/chartShapes.ts` 中查阅 chart 是否暴露时间/价格与坐标的转换（如 getTimeScale().timeToCoordinate、priceScale 的 priceToCoordinate 及反向）；若有，在 drawText 中根据 shape.text 与 font 用 canvas measureText 估算宽高，计算使“文案左上角”落在 (time, price) 时视觉中心等于锚点的偏移量，用偏移后的 (time, price) 调用 createShape，实现不依赖 TV 对齐的自身居中，文件路径 `frontend/src/tv/chartShapes.ts`
- [ ] T008 若 T007 因无坐标转换 API 无法实现：在 `frontend/src/tv/chartShapes.ts` 中为单点文案增加可选分支，使用 `chart.createAnchoredShape` 与 shape `anchored_text`，将期望的“锚点”对应到图表上的 (time, price)，再换算为相对图表的百分比位置 (xPct, yPct)，用 (0.5, 0.5) 等居中参数创建 anchored 文案并验证是否视觉居中；若效果可接受则作为居中时的备选实现，文件路径 `frontend/src/tv/chartShapes.ts`
- [ ] T009 在 `frontend/src/views/ChartShapesDemo.vue` 单点文案侧栏或文案说明中，更新提示：居中已通过延迟 centerPosition 或锚点偏移/anchored_text 实现，若仍异常请说明 TV 版本与现象，文件路径 `frontend/src/views/ChartShapesDemo.vue`
- [ ] T010 在 `frontend/src/tv/README-shapes.md` 的文案居中一节补充：若 override 与同步 centerPosition 无效，已采用延迟调用 centerPosition；若仍无效则采用锚点偏移或 anchored_text 方案，并注明当前采用方案，文件路径 `frontend/src/tv/README-shapes.md`

---

## Dependencies & Execution Order

- T001 → T002（先尝试键名再确保 setProperties）；T003 可与 T001 并行；T004 在 T001–T003 之后；T005 在 T002 之后（createShape 与 setProperties 完成后调用 centerPosition）。
- T006 在 T005 之后（延迟 centerPosition）；T007 在 T006 验证仍不生效后；T008 在 T007 不可行时；T009、T010 在 T006 或 T007/T008 方案落地后更新说明。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] 描述（含文件路径）` 或已完成 `- [x]`。
