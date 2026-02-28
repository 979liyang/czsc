# Tasks: ChartShapesDemo 图形与参数补全（datafeed-api + charting_library）

**Input**: 用户需求「学习一下 datafeed-api.d.ts 都能画哪些图，并把 ChartShapesDemo.vue 能画的图和参数补充完整」。  
**Prerequisites**: 现有 `frontend/charting_library/datafeed-api.d.ts`、`frontend/charting_library/charting_library.d.ts`、`frontend/src/views/ChartShapesDemo.vue`、`frontend/src/tv/chartShapes.ts`。

**Organization**: 按“数据源图形（datafeed）”与“绘图 API 图形（charting_library）”分组，便于独立实现与验收。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 所属用户故事（US1= datafeed 图形文档，US2= createShape 单点补全，US3= createMultipointShape 与参数补全）
- 描述中需包含具体文件路径

## 路径约定

- 前端：`frontend/src/`
- 类型定义：`frontend/charting_library/*.d.ts`
- 文档：`specs/001-czsc-api-ui/` 或 `frontend/` 下 README

---

## Phase 1: Setup（梳理 API 与类型）

**Purpose**: 明确 datafeed-api.d.ts 与 charting_library.d.ts 中“能画的图”及参数来源，为后续补全提供依据。

- [x] T001 梳理 `frontend/charting_library/datafeed-api.d.ts` 中与“画图”相关的接口：`Mark`（getMarks，K 线标记）、`TimescaleMark`（getTimescaleMarks，时间轴标记）；在 `frontend/src/views/ChartShapesDemo.vue` 的「可绘制图形一览」或新建 `frontend/src/tv/README-shapes.md` 中补充说明：datafeed 仅提供 **K 线标记** 与 **时间轴标记**，字段列表（Mark: id, time, color, text, label, labelFontColor, minSize, borderWidth, imageUrl 等；TimescaleMark: id, time, color, labelFontColor, label, tooltip, shape, imageUrl 等）及与 `supports_marks` / `supports_timescale_marks` 的对应关系
- [x] T002 梳理 `frontend/charting_library/charting_library.d.ts` 中 `CreateShapeOptions.shape`（单点）与 `CreateMultipointShapeOptions.shape`（多点，即 `SupportedLineTools` 排除 cursor/dot/eraser 等）的完整枚举；在同上文档中列出：createShape 支持 arrow_up, arrow_down, flag, vertical_line, horizontal_line, long_position, short_position, icon, emoji, sticker, text, anchored_text, note, anchored_note；createMultipointShape 支持 trend_line, horizontal_ray, rectangle, circle, ellipse, triangle, polyline, path, curve, ray, extended 等（以 d.ts 中 SupportedLineTools 为准）

---

## Phase 2: Foundational（chartShapes 与 Overrides 映射）

**Purpose**: 确保 chartShapes.ts 与 d.ts 的 Overrides 键名一致，便于 Demo 侧栏参数与绘图 API 一一对应。

- [x] T003 在 `frontend/src/tv/chartShapes.ts` 中确认并补齐 PREFIX 与 charting_library.d.ts 的 linetool 前缀一致；对已支持的 shape（text, rectangle, trend_line, arrowmarkup/arrowmarkdown, triangle, vertline, circle）对应的 LineToolOverrides 接口名与键名在注释或 README-shapes.md 中列出，便于 Demo 补充参数时引用
- [x] T004 [P] 从 `frontend/charting_library/charting_library.d.ts` 中提取 HorzlineLineToolOverrides、HorzrayLineToolOverrides、TrendlineLineToolOverrides、RectangleLineToolOverrides（若存在）、EllipseLineToolOverrides、PolylineLineToolOverrides、PathLineToolOverrides、RayLineToolOverrides、ExtendedLineToolOverrides 等与 ChartShapesDemo 已用或待用图形相关的属性列表（键名及默认值），写入 `frontend/src/tv/README-shapes.md` 或 ChartShapesDemo.vue 内联注释

---

## Phase 3: User Story 1 - datafeed 图形文档与可选示例 (P2)

**Goal**: 明确 datafeed-api.d.ts 能“画”的只有 K 线标记与时间轴标记；在 Demo 中文档化并在可选情况下增加示例（若当前 datafeed 已开启 supports_marks/supports_timescale_marks）。

**Independent Test**: 打开 ChartShapesDemo 页面，“可绘制图形一览”中能区分“数据源标记（datafeed）”与“绘图 API（createShape/createMultipointShape）”；若实现可选示例，切换标的或时间范围时 K 线/时间轴上能出现示例 Mark 或 TimescaleMark。

- [x] T005 [US1] 在 `frontend/src/views/ChartShapesDemo.vue` 的「可绘制图形一览」中增加一节“数据源标记（datafeed-api.d.ts）”：说明 getMarks 返回 Mark[]、getTimescaleMarks 返回 TimescaleMark[]；列出 Mark 与 TimescaleMark 的字段（id, time, color, text/label, labelFontColor, shape 等）及 TimeScaleMarkShape 枚举（circle, earningUp, earningDown, earning），并注明需 DatafeedConfiguration.supports_marks / supports_timescale_marks 为 true
- [x] T006 [US1] （可选）若项目 datafeed 已实现 getMarks 或 getTimescaleMarks，在 ChartShapesDemo 或 UDF datafeed 中增加示例数据（如某几根 K 的 Mark、某几个时间的 TimescaleMark），并在 Demo 页说明“数据源标记由 datafeed 提供”；若未实现则仅在文档中说明，不新增接口调用

---

## Phase 4: User Story 2 - createShape 单点图形补全 (P1)

**Goal**: ChartShapesDemo 覆盖 charting_library createShape 的全部单点图形类型，每种具备可调参数（来自对应 LineToolOverrides）。

**Independent Test**: 在 ChartShapesDemo 侧栏选择“单点图形”后，可切换 shape 类型：text, arrow_up, arrow_down, flag, vertical_line, horizontal_line, icon, emoji, sticker, note 等；每种类型下展示该类型在 d.ts 中的主要 Overrides 参数并可调，图表上实时绘制对应图形。

- [x] T007 [US2] 在 `frontend/src/views/ChartShapesDemo.vue` 的 SHAPE_SECTIONS 与 cfg 中增加 createShape 当前未覆盖的类型：flag（linetoolflagmark）、horizontal_line（linetoolhorzline）、icon（linetoolicon）、emoji（linetoolemoji）、sticker（linetoolsticker）、note（linetoolcomment 或 note）；在 `frontend/src/tv/chartShapes.ts` 中为上述类型增加 Shape 接口与 draw 分支（若尚未支持），并在 buildShapesFromPoints 中根据 activeShapeKey 生成对应 shape 数据
- [x] T008 [US2] 为新增的 flag、horizontal_line、icon、emoji、sticker、note 在 ChartShapesDemo.vue 侧栏增加参数面板：从 charting_library.d.ts 的 FlagmarkLineToolOverrides、HorzlineLineToolOverrides、IconLineToolOverrides、EmojiLineToolOverrides、StickerLineToolOverrides、CommentLineToolOverrides 中抽取主要属性（如 color, linecolor, linewidth, bold, fontsize, angle 等），以与现有 text/arrow/verticalLine 一致的控件形式展示并写入 cfg，刷新图形时传入 overrides
- [x] T009 [US2] 在「可绘制图形一览」中更新 createShape 列表：arrow_up, arrow_down, flag, vertical_line, horizontal_line, long_position, short_position, icon, emoji, sticker, text, anchored_text, note, anchored_note；注明 long_position/short_position 与 anchored_text/anchored_note 需 createAnchoredShape，本 Demo 仅做 createShape 单点类型

---

## Phase 5: User Story 3 - createMultipointShape 与参数补全 (P1)

**Goal**: 补全 ChartShapesDemo 中已有图形的 d.ts 全量 Overrides 参数，并增加 ellipse、ray、extended、polyline、path、curve 等常用多点图形及参数。

**Independent Test**: 侧栏“矩形”“圆”“三角形”“水平射线”“箭头”“竖线”“文案”等已有图形下，参数与 charting_library.d.ts 对应 LineToolOverrides 一致且可调；新增“椭圆”“射线”“延长线”“折线”“路径”“曲线”等节后，可选择并在图上绘制，且具备主要可调参数。

- [ ] T010 [US3] 在 `frontend/src/tv/chartShapes.ts` 中为 ellipse、ray、extended、polyline、path、curve 增加 Shape 类型与 draw 实现（createMultipointShape 的 shape 名以 d.ts 为准，如 horizontal_ray、ray、extended、polyline、path、curve、ellipse）；在 `frontend/src/views/ChartShapesDemo.vue` 的 SHAPE_SECTIONS 与 buildShapesFromPoints 中增加上述类型的入口与点位逻辑（ellipse 需 4 点或等价、path/curve 需多点）
- [ ] T011 [US3] 为 ChartShapesDemo.vue 中已有图形（text, rect, ray, arrow, triangle, verticalLine, circle）的 cfg 与侧栏参数查漏补缺：对照 charting_library.d.ts 的 TextLineToolOverrides、Rectangle 相关、HorzrayLineToolOverrides、Arrowmarkup/Arrowmarkdown、TriangleLineToolOverrides、VertlineLineToolOverrides、CircleLineToolOverrides 全量属性，将尚未暴露的键（如 transparency、linestyle、showLabel、fontSize 等）补充到 cfg 与模板中，确保“刷新图形”时传入完整 overrides
- [ ] T012 [US3] 为新增的 ellipse、ray、extended、polyline、path、curve 在 ChartShapesDemo.vue 侧栏增加参数面板：从 EllipseLineToolOverrides、RayLineToolOverrides、ExtendedLineToolOverrides、PolylineLineToolOverrides、PathLineToolOverrides 等抽取主要属性（color, linecolor, linewidth, linestyle, fillBackground, transparency 等），与现有矩形/圆/三角形一致风格展示并写入 cfg
- [ ] T013 [US3] 更新「可绘制图形一览」中 createMultipointShape 列表：trend_line, horizontal_ray, rectangle, triangle, circle, ellipse, arrow, ray, extended, polyline, path, curve 及 fib、pattern 等；注明 override 键名格式为 `linetool<工具名>.<属性>`，完整列表以 charting_library.d.ts 的 DrawingOverrides 为准；「所有图形」列表与 d.ts 全量 linetool 前缀保持一致

---

## Phase 6: Polish & 一致性

**Purpose**: 文档与列表与 d.ts 一致，便于后续维护与扩展。

- [x] T014 在 `frontend/src/views/ChartShapesDemo.vue` 中统一“可绘制图形一览”与“所有图形”的表述：datafeed 的 Mark/TimescaleMark 与 charting_library 的 createShape/createMultipointShape 分开说明；本页已对接的图形列出对应 linetool 前缀及 d.ts 接口名（如 linetooltext → TextLineToolOverrides）
- [x] T015 [P] 若存在 `frontend/src/tv/tv_overrides.md` 或项目内 TradingView 图形文档，同步更新：补充 datafeed-api.d.ts 的 Mark/TimescaleMark 与 charting_library createShape/createMultipointShape 的 shape 枚举及主要 Overrides 来源文件（datafeed-api.d.ts / charting_library.d.ts）

---

## Dependencies & Execution Order

- **Phase 1**：无依赖，T001、T002 可并行。
- **Phase 2**：依赖 Phase 1 的梳理结果；T003、T004 可并行。
- **Phase 3 (US1)**：依赖 Phase 1；T005、T006 可顺序执行（T006 可选）。
- **Phase 4 (US2)**：依赖 Phase 2；T007 先于 T008、T009（先有 shape 类型与 draw，再补参数与文档）。
- **Phase 5 (US3)**：依赖 Phase 2；T010 先于 T011、T012、T013；T011 与 T012 可并行（已有图形补参 vs 新图形加参）。
- **Phase 6**：依赖 Phase 3、4、5 完成；T014、T015 可并行。

### Parallel Opportunities

- T001 与 T002；T003 与 T004；T008 与 T009（同 Phase 内）；T011 与 T012；T014 与 T015。

---

## Implementation Strategy

### MVP（优先）

1. Phase 1 + Phase 2：梳理 datafeed 与 charting_library 的“能画的图”及 Overrides 来源。
2. Phase 4 (US2)：createShape 单点图形补全（flag, horizontal_line, icon, emoji, sticker, note）及侧栏参数。
3. Phase 5 (US3)：已有图形参数补全（T011）+ 常用多点图形 ellipse, ray, extended, polyline, path, curve（T010、T012、T013）。

### 验收要点

- **datafeed-api.d.ts**：文档明确仅包含 K 线标记（Mark）与时间轴标记（TimescaleMark），参数与 getMarks/getTimescaleMarks 一致。
- **ChartShapesDemo.vue**：单点图形覆盖 createShape 所列类型（除 long_position/short_position/anchored_*）；多点图形覆盖 trend_line, horizontal_ray, rectangle, triangle, circle, ellipse, ray, extended, polyline, path, curve 等；每种图形的侧栏参数与 charting_library.d.ts 对应 LineToolOverrides 一致且可调。
- **chartShapes.ts**：新增 shape 类型与 PREFIX/overrides 与 d.ts 一致，drawChartShapes 与 clearChartShapes 行为不变。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T005、T006；US2: T007、T008、T009；US3: T010、T011、T012、T013；Setup/Foundational/Polish 无 Story 标签。
