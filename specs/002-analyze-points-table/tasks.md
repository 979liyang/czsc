# Tasks: 麒麟分析增加涨停跌停与买卖点时间节点表格

**Input**: Design documents from `specs/002-analyze-points-table/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by layer (czsc → backend → frontend) and by user story where applicable. Foundation (czsc + backend 契约/序列化) 完成后，前端可按 US1/US2 分步交付。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: US1=涨停跌停表格, US2=买卖点表格, US3=时间粒度与无数据提示, US4=Demo 看多/看空基类, US5=K 线图买卖点叠加与开关, US6=全盘扫描（仅第一类买卖点+历史记录）
- 描述中给出具体文件路径

## Path Conventions

- **czsc**: `czsc/` 位于仓库根
- **backend**: `backend/src/`
- **frontend**: `frontend/src/`

---

## Phase 1: Foundation（czsc 层 — 阻塞后续）

**Purpose**: CZSC 具备八类事件列表的计算能力，供 backend 调用。无此阶段则 API 无法返回新字段。

- [x] **T001** [US1] 在 `czsc/analyze.py` 中实现涨停/跌停事件扫描：对 `bars_raw` 全量遍历，按 research.md 中 bar_zdt_V230331 逻辑（close==high>=前close→涨停，close==low<=前close→跌停）收集每根 K 线的 `dt`，返回两个列表（可封装为 CZSC 的属性或方法，如 `limit_up_dts` / `limit_down_dts` 或统一方法返回 8 类）。
- [x] **T002** [US2] 在 `czsc/analyze.py` 中实现买卖点事件收集：在 CZSC 构造完成后，对 `bars_raw` 按时间顺序回放（或逐 bar 更新 CZSC 副本），在每根 K 线处调用 `zdy_macd_bs1_V230422`、`cxt_second_bs_V230320`、`cxt_third_bs_V230319`，根据 v1 为「看多/看空」「二买/二卖」「三买/三卖」将当前 bar 的 `dt` 加入对应列表；返回六类买卖点的 dt 列表（可与 T001 合并为同一接口，如 `get_event_dts()` 返回 8 个 list）。
- [x] **T003** [P] 在 czsc 或 backend 中实现时间节点格式化：根据 `freq`（日线/周线/月线 vs 15/30/60 分钟）将 dt 格式化为 YYYY-MM-DD 或 YYYY-MM-DD HH:mm，供序列化使用（可放在 backend 序列化层，见 T005）。

**Checkpoint**: czsc 层可对任意 bars 输出八类事件的 dt 列表（或原始 dt，由 backend 统一格式化）。

---

## Phase 2: Backend（API 契约与序列化）

**Purpose**: 分析接口响应中增加八类事件列表，默认 []，不破坏现有客户端。

- [x] **T004** [P] 在 `backend/src/models/schemas.py` 的 `AnalysisResponse` 中新增 8 个可选字段：`limit_up_events`、`limit_down_events`、`buy1_events`、`buy2_events`、`buy3_events`、`sell1_events`、`sell2_events`、`sell3_events`，类型为 `List[Dict[str, Any]]`，默认 `[]`；单条结构含 `dt`（必填），可选 `price`、`pct`（见 contracts/analysis-czsc-response-extension.md）。
- [x] **T005** 在 `backend/src/models/serializers.py` 中新增事件列表序列化：输入为 (dt, price?, pct?) 的列表，根据 `freq` 将 dt 格式化为日期或日期+时间字符串，输出 `[{"dt": "...", "price": ..., "pct": ...}, ...]`；可封装为 `serialize_event_events(events, freq)` 供多处复用。
- [x] **T006** 在 `backend/src/services/analysis_service.py` 的 `analyze()` 中：调用 CZSC 的涨停/跌停与买卖点事件列表（T001/T002），经 T005 序列化后写入 result 的 8 个新字段；若 czsc 未实现则写入空列表，不抛错。

**Checkpoint**: `POST /api/v1/analysis/czsc` 响应中包含八类事件数组，时间格式按周期区分；无数据时为 []。

---

## Phase 3: User Story 1 + User Story 2 — 前端表格（MVP）

**Goal**: 麒麟分析页展示涨停、跌停与六类买卖点表格，每表至少含时间节点列；无数据时表格为空或明确提示。

**Independent Test**: 选择标的/周期/时间范围并分析，结果区出现「涨停」「跌停」「第一/二/三类买点」「第一/二/三类卖点」表格；切换周期重新分析后表格更新。

- [x] **T007** [P] 在 `frontend/src/api/analysis.ts` 的 `AnalysisResponseData` 接口中增加 8 个可选字段：`limit_up_events`、`limit_down_events`、`buy1_events`、`buy2_events`、`buy3_events`、`sell1_events`、`sell2_events`、`sell3_events`，类型为 `Array<{ dt: string; price?: number; pct?: number }>`，与 contracts 一致。
- [x] **T008** [US1] 在 `frontend/src/views/Analysis.vue` 结果区域增加「涨停」与「跌停」两个表格：数据来自 `store.analysisResult?.limit_up_events` / `limit_down_events`，列至少包含「时间节点」（展示 `dt`）；无数据时表格为空或显示「该区间内无涨停/跌停」。
- [x] **T009** [US2] 在 `frontend/src/views/Analysis.vue` 结果区域增加六类买卖点表格：第一/二/三类买点、第一/二/三类卖点，数据来自 `buy1_events`～`sell3_events`，列至少包含「时间节点」；某类无数据时该表为空或显示「该区间内无此类买点/卖点」。
- [x] **T010** [US3] 确保表格中时间列直接使用后端返回的 `dt` 字符串展示（后端已按周期格式化）；无数据提示与 FR-007、SC-003 一致，不因空数组报错或隐藏结果区。

**Checkpoint**: 用户完成一次分析后，可在同一页看到全部 8 类表格，时间可读；切换周期后表格内容与格式更新。

---

## Phase 4: Polish & Validation

**Purpose**: 代码规范、边界与 quickstart 验收。

- [x] **T011** [P] 代码规范：czsc/analyze.py 与 backend 新增代码符合 .cursor/rules/czsc-coding-standards.mdc（loguru、函数≤30 行、120 字符/行、中文注释与文档字符串）。
- [x] **T012** 边界与无数据：确认分析区间内无任何涨停/跌停/买卖点时，八表均为空或带文案提示；快速连续切换标的或周期时，结果区仅展示最近一次分析数据（无旧数据残留）。
- [ ] **T013** 按 quickstart.md 执行本地验证：后端 `POST /api/v1/analysis/czsc` 返回含 8 个事件字段；前端麒麟分析页选择不同周期（日线、15 分钟等）分析，检查表格与时间格式。

---

## Phase 5: Fix 买卖点无数据（问题：一二三类买卖点表格始终为空）

**Context**: 用户反馈「目前第一类、第二类、第三类的买卖点都没有数据」。根因：信号函数（如 `zdy_macd_bs1_V230422`）通过 `create_single_signal` 返回的是 `OrderedDict`，key 为信号 key，value 为字符串 `"v1_v2_v3_score"`（如 `"看多_下跌5笔_任意_0"`），**没有** `"v1"` 键；原逻辑用 `s1.get("v1")` 始终为 None，导致从未命中买/卖点。

- [x] **T014** [US2] 在 `czsc/analyze.py` 的 `_collect_bs_events` 中修复 v1 解析：从信号返回的 OrderedDict 的 value 字符串中解析第一段作为 v1（即 `value.split("_")[0]`），新增 `_v1_from_signal(sig)` 辅助函数，并用其替代对 `s1.get("v1")` / `s2.get("v1")` / `s3.get("v1")` 的依赖，使 看多/看空/二买/二卖/三买/三卖 能正确落入对应列表。

**Checkpoint**: 重新执行麒麟分析后，当 K 线与笔结构满足各信号触发条件时，前端六类买卖点表格应出现对应时间节点；若仍无数据，多为信号本身条件苛刻（如 BS1 要求 bars_ubi≤9、BS2/BS3 要求至少 7 笔），属业务预期。

---

## Phase 6: Fix 第一类买卖点没有数据

**Context**: 用户反馈「第一类买卖点没有数据」。BS1 信号（zdy_macd_bs1_V230422）触发条件苛刻：`len(c.bi_list)>=7` 且 `len(c.bars_ubi)<=9`，并需 MACD 背驰形态，回放时多数 K 线不满足，导致一买/一卖表常为空。

- [x] **T015** [US2] 在 `czsc/analyze.py` 的 `_collect_bs_events` 中为第一类买卖点增加结构备选：在回放结束后，遍历当前 CZSC 的 `finished_bis`，将**向下笔**的底分型端点（fx_b.mark==Mark.D）的 dt 加入 buy1_dts，将**向上笔**的顶分型端点（fx_b.mark==Mark.G）的 dt 加入 sell1_dts；与 BS1 结果去重并按时间排序，保证第一类买卖点表格在有笔数据时不再长期为空。实现时在 return 前追加上述逻辑，使用 set 去重后合并并 sort。

**Checkpoint**: 再次麒麟分析后，第一类买点/卖点表格应出现若干时间节点（至少包含每段向下/向上笔的端点）；BS1 触发的点仍保留，与结构备选合并去重。

---

## Phase 7: User Story 4 — Demo Shapes 看多/看空基类 (Priority: P2)

**Goal**: 在前端 `/demo/shapes`（ChartShapesDemo）中提供两类基类：看多、看空。二者均支持传入文案（居中对齐）和连接线；看多默认文案在连接线下方、红色文案、连接线距最低 K 线 0.2%、连接线红色；看空默认文案在连接线上方、绿色文案、连接线距最高 K 线 0.2%、连接线绿色。前端可手动调整上述属性，点击保存生成配置（JSON）。

**Independent Test**: 打开 `/demo/shapes`，在侧栏找到「看多/看空基类」区块，修改文案、连接线距离、颜色等，图表上可见预览；点击保存后得到可复用的 JSON 配置。

- [x] **T016** [P] [US4] 在 `frontend/src/tv/chartShapes.ts`（或新建 `frontend/src/views/demo/shapes/bullBearShapes.ts`）中定义**看多基类**：类型/接口支持文案（必填）、文案居中对齐（hAlign/vAlign 为 center/middle）、连接线；默认：文案在连接线下方、文案颜色红色、连接线相对锚点（最低 K 线）向下偏移 0.2%（即线在最低价下方 0.2%）、连接线颜色红色；产出为可被 `drawChartShapes` 或现有绘制逻辑消费的图形描述（如基于 `ShapeHorizontalRay` + 文案或等价结构）。
- [x] **T017** [P] [US4] 在同一模块中定义**看空基类**：支持文案（居中对齐）、连接线；默认：文案在连接线上方、文案颜色绿色、连接线相对锚点（最高 K 线）向上偏移 0.2%、连接线颜色绿色；产出同上，可供绘制层统一使用。
- [x] **T018** [US4] 在 `frontend/src/views/ChartShapesDemo.vue` 中集成看多/看空基类：在侧栏「图形参数调整」中增加「看多/看空基类」区块；表单字段包含：文案、连接线距离（%，默认 0.2）、文案颜色、连接线颜色、文案位置（线上/线下）；支持实时预览（修改后图表重绘）；提供「保存」按钮，点击后生成当前配置的 JSON 并展示（可复制），便于导出或后续接入其他页。

**Checkpoint**: 用户在 `/demo/shapes` 可切换看多/看空、编辑文案与样式、保存得到配置 JSON；图表上正确显示连接线与居中文案（看多：线下红字红线，看空：线上绿字绿线）。

---

## Phase 8: Fix 看多/看空基类 — 字体颜色与连接线间隙

**Goal**: 1) 看多/看空文案颜色设置在前端修改后能在图表上生效；2) 连接线与 K 线之间保留 0.2% 价格间隙（连接线不贴 K 线）。

**Independent Test**: 在 `/demo/shapes` 选择「看多/看空基类」，修改文案颜色并刷新图形，文案颜色应更新；连接线起点与 K 线最低/最高价之间应有可见 0.2% 间隙。

- [x] **T019** [US4] 在 `frontend/src/tv/chartShapes.ts` 的 `drawHorizontalRay` 中修复水平射线文案颜色不生效：创建 text 形状时除 `buildTextLineToolOverrides` 的带前缀 overrides 外，合并顶层 `color`（或 TradingView 所需键），并在 `createShape` 后对 entity 调用 `setProperties(overrides)`（与 `drawText` 一致），确保 `shape.label.color` 在图表上生效。
- [x] **T020** [US4] 在 `frontend/src/tv/bullBearShapes.ts` 中为连接线增加与 K 线的 0.2% 间隙：看多时连接线 p1 从「锚点最低价」改为「最低价下方 0.2%」处起点、p2 仍为水平线价格；看空时 p1 从「最高价上方 0.2%」处起点、p2 仍为水平线价格，使连接线不贴 K 线，始终保留 0.2% 间隙。

**Checkpoint**: 修改看多/看空文案颜色后图表文案颜色立即生效；连接线起点与 K 线之间有 0.2% 价格间隙。

---

## Phase 9: User Story 5 — K 线图标记分析买卖点 (Priority: P2)

**Goal**: 在 TradingViewChart.vue 的 K 线图上叠加麒麟分析（/analysis 同源数据）的第一、二、三类买卖点；买卖点样式使用 ChartShapesDemo 的看多/看空基类（buildBullishShapes / buildBearishShapes）；工具栏增加一个开关控制这三类买卖点的显示与隐藏。

**Independent Test**: 打开 K 线图页，在工具栏打开「分析买卖点」开关并保证当前标的/周期与麒麟分析可请求一致时，图表上出现一买/二买/三买（看多样式）、一卖/二卖/三卖（看空样式）；关闭开关后标记消失。

- [x] **T021** [US5] 在 `frontend/src/views/TradingViewChart.vue` 或新建 `frontend/src/tv/analysisBsOverlay.ts` 中接入麒麟分析买卖点数据：根据当前图表的 symbol、interval 与可见时间范围（或固定最近 N 日）调用 `frontend/src/api/analysis.ts` 的 `analysisApi.analyze`，获取 `buy1_events`、`buy2_events`、`buy3_events`、`sell1_events`、`sell2_events`、`sell3_events`；将每条事件的 `dt` 字符串解析为图表所需的 Unix 秒时间戳，锚点价格优先使用事件中的 `price`，缺失时需从图表当前 K 线数据中取该时间对应的 low（买点）/high（卖点）。输出结构可供绘制层消费（如 `{ time, price }[]` 按类型分组）。
- [x] **T022** [US5] 在 K 线图上绘制买卖点标记：使用 `frontend/src/tv/bullBearShapes.ts` 的 `buildBullishShapes`（买点，文案「一买」「二买」「三买」）与 `buildBearishShapes`（卖点，文案「一卖」「二卖」「三卖」），通过 `frontend/src/tv/chartShapes.ts` 的 `drawChartShapes` 在图表上绘制；买点锚点为 `(time, price)`（price 为事件 price 或该 K 的 low），卖点为该 K 的 high。在图表 ready 且「分析买卖点」开关打开时绘制，开关关闭或 symbol/interval 变更时调用 `clearChartShapes` 清除。实现于 TradingViewChart.vue 的 onChartReady/watch 或 analysisBsOverlay 模块。
- [x] **T023** [US5] 在工具栏增加「分析买卖点」开关：在 `frontend/src/components/ChartRightTools.vue` 中增加一个开关（如「分析买卖点」或「一二三类买卖点」），在 `frontend/src/components/ChartRightSidebar.vue` 中增加对应 `v-model:show-analysis-bs`（或等效命名）并传给 ChartRightTools；在 `frontend/src/views/TradingViewChart.vue` 中增加状态 `showAnalysisBs`，与 ChartRightSidebar 双向绑定，并驱动 T021/T022 的拉取与绘制/清除逻辑。

**Checkpoint**: 工具栏有「分析买卖点」开关；打开后 K 线图显示一/二/三类买卖点（看多红、看空绿），关闭后标记清除；标的/周期与分析 API 一致时数据正确对应。

---

## Phase 10: Fix 分析买卖点点击后未绘制

**Goal**: 用户点击「分析买卖点」开关后，图表上能正确出现买卖点标记。

**Independent Test**: 打开 K 线图页，等待图表加载完成，打开「分析买卖点」开关；数秒内应出现一买/二买/三买、一卖/二卖/三卖标记（若当前区间有数据）；无数据时无报错、不绘制。

- [x] **T024** [US5] 在 `frontend/src/views/TradingViewChart.vue` 中修复「分析买卖点」不绘制：① 当 `getVisibleRange()` 返回无效（from≤0 或 from≥to）时改用默认范围（最近 365 天）；② 调用 `fetchBars` 时使用 `intervalToResolution(interval)` 与后端 UDF 一致（如 1D→D）；③ 用「按日」匹配补全事件 price（`dayToBars`）以应对时区/时间格式差异；④ 打开开关时延迟约 200ms 再执行 `drawAnalysisBsOverlay`，确保图表可见范围已就绪。

**Checkpoint**: 点击「分析买卖点」后，在支持的周期（日/周/月/15/30/60 分钟）与有数据的标的下，图表上能看到买卖点标记。

---

## Phase 11: Fix 连接线距离 K 线太近与重叠

**Goal**: 买卖点连接线与 K 线之间保留更大、可见的间隙；同一时间附近多个买卖点之间不重叠（通过垂直错位区分）。

**Independent Test**: 在 K 线图打开「分析买卖点」；连接线起点与 K 线最低/最高价之间应有明显间隙（不贴线）；当同一根或相邻 K 线上存在多个买卖点时，各标记的连接线与水平线不重叠、可区分。

- [x] **T025** [US5] 在 `frontend/src/tv/bullBearShapes.ts` 中增大连接线与 K 线的默认间隙：将 `CONNECTOR_KLINE_GAP_PERCENT` 从 0.002（0.2%）调整为 0.005～0.01（0.5%～1%），或提高 `lineGapPercent` 默认值，使连接线明显远离 K 线；在 `frontend/src/views/TradingViewChart.vue` 的 `drawAnalysisBsOverlay` 中，对同一时间窗口内多个买点/卖点按时间或索引做垂直错位（如为每个点传入递增的 `lineGapPercent` 或等价的价格偏移），使相邻买卖点的水平线与连接线不重叠、可区分。

**Checkpoint**: 连接线距 K 线有可见间隙；多买卖点密集时无重叠现象。

---

## Phase 12: 买卖点连接线长度 2%（买点 K 线下、卖点 K 线上，相邻错开）

**Goal**: 买点标记在 K 线下方、连接线长度（锚点到水平线）为价格的 2%；卖点标记在 K 线上方、连接线长度为 2%；当买卖点相邻（同一根或相邻 K 线）时，增加各点的连接线距离（垂直错位）保证不重叠、可区分。

**Independent Test**: 在 K 线图打开「分析买卖点」；买点（一买/二买/三买）的锚点在 K 线最低价，连接线向下延伸至水平线，垂直距离为锚点价格的 2%；卖点（一卖/二卖/三卖）的锚点在 K 线最高价，连接线向上延伸 2%；当同一时间附近存在多个买卖点时，各标记的连接线在 2% 基础上递增错位（如 2% + index × 步长），无重叠。

- [x] **T026** [US5] 在 `frontend/src/tv/bullBearShapes.ts` 中将看多/看空默认连接线长度设为 2%：将 `defaultBullish.lineGapPercent` 与 `defaultBearish.lineGapPercent` 设为 `2`（即水平线相对锚点的距离为价格的 2%），保证买点在 K 线下、卖点在 K 线上且连接线长度均为 2%；在 `frontend/src/views/TradingViewChart.vue` 的 `drawAnalysisBsOverlay` 中，将 `baseGapPercent` 与垂直错位基准改为 `2`，当买卖点相邻（同一根或相邻 K 线）时为每个点传入递增的 `lineGapPercent`（如 2 + index × 0.4），使连接线错开、不重叠。

**Checkpoint**: 买点连接线长 2%（K 线下），卖点连接线长 2%（K 线上）；相邻买卖点通过增加连接线距离错开、无重叠；Demo 看多/看空基类默认仍可通过表单调整，K 线图叠加固定为 2% 并支持相邻错位。

---

## Phase 13: 上升趋势时买卖点置于 K 线图上方（单点文案，连接线按附近高点与邻近买卖点错开）

**Goal**: 当可见区间判定为上升趋势时，将买卖点标记统一放在 K 线图上方；使用单点文案（仅一点标注，无长水平射线）；连接线长度根据附近最高点与附近买卖点动态计算，保证错开、不重叠。

**Independent Test**: 在 K 线图打开「分析买卖点」，选择一段明显上升趋势的标的/区间；买卖点（一买/二买/三买、一卖/二卖/三卖）应出现在 K 线图上方，文案为单点标注；连接线长度随附近高点与邻近买卖点自适应，多标记时错开无重叠。非上升趋势时保持现有行为（买点 K 线下、卖点 K 线上）。

- [ ] **T027** [US5] 在 `frontend/src/views/TradingViewChart.vue` 或 `frontend/src/tv/analysisBsOverlay.ts` 中实现上升趋势判定与上方绘制逻辑：① 根据当前可见 K 线数据计算趋势（如近期高点/低点比较、或短期均线斜率），判定是否为上升趋势；② 若为上升趋势，在 `drawAnalysisBsOverlay` 中改为将买点与卖点均绘制在 K 线图上方（锚点仍为 (time, low) / (time, high)，连接线向上延伸至文案）；③ 使用单点文案样式（单点标注，可复用或扩展 `frontend/src/tv/chartShapes.ts` 的 text 形状，无需长水平射线）；④ 连接线长度根据「该点附近 N 根 K 的最高价」与「邻近买卖点已占用的垂直位置」动态计算，使每条连接线终点错开、不重叠。非上升趋势时保持 Phase 12 行为不变。

**Checkpoint**: 上升趋势区间内买卖点显示在 K 线图上方、单点文案、连接线按附近高点与邻近买卖点错开；非上升趋势时仍为买点 K 下、卖点 K 上、2% 连接线。

---

## Phase 14: 买卖点【上下分离】模式 — 尺寸 70%、向右偏移防重叠、浅灰引线指 K 线实体

**Goal**: 买卖点标记采用【上下分离】模式：买入点放在 K 线下方，卖出点放在 K 线上方；标记尺寸缩小至 K 线宽度的 70%；信号密集时自动向右偏移避免重叠；添加浅灰色引线从标记指向对应 K 线实体。

**Independent Test**: 在 K 线图打开「分析买卖点」；买点（一买/二买/三买）在 K 线下方、卖点（一卖/二卖/三卖）在 K 线上方；标记视觉尺寸约为 K 线宽度的 70%；多信号密集时标记在时间轴上向右错开、不叠在一起；每条标记有浅灰色引线连接至对应 K 线的实体（买点引线至该根 K 的 low/实体下沿，卖点引线至该根 K 的 high/实体上沿）。

- [x] **T028** [US5] 在 `frontend/src/views/TradingViewChart.vue` 与 `frontend/src/tv/bullBearShapes.ts` 或 `frontend/src/tv/chartShapes.ts` 中实现上下分离 + 尺寸 + 偏移 + 引线：① 确认并保持**上下分离**（买点锚点在 K 下方绘制、卖点锚点在 K 上方绘制，与 Phase 12 一致）；② 将买卖点标记的**尺寸**设为当前 K 线宽度的 70%（文案字号或形状宽度按 K 线宽度缩放，可在 `drawAnalysisBsOverlay` 中根据可见 bar 数量估算单根 K 宽度，或使用 TradingView 的 barSpacing/scale 信息）；③ 当同一时间附近信号密集时，在**时间轴方向**上对标记做**向右偏移**（如按索引增加 time 偏移，或将文案/形状的绘制位置向右平移若干 bar），避免重叠；④ 为每个买卖点添加**浅灰色引线**（线段）：买点从标记位置连到该 K 的 low（或实体下沿），卖点从标记位置连到该 K 的 high（或实体上沿），引线样式为浅灰色（如 `#b0b0b0`），在 `bullBearShapes` 或 `drawChartShapes` 中增加并绘制该线段。

**Checkpoint**: 买卖点上下分离、尺寸为 K 线宽度 70%、密集时向右偏移、浅灰引线指向 K 线实体。

---

## Phase 15: 分析买卖点 — 一买/一卖/二买/二卖/三买/三卖 分别是否显示的开关（默认均显示）

**Goal**: 在「分析买卖点」总开关下，增加一买、一卖、二买、二卖、三买、三卖共六项是否显示的独立开关；默认全部为显示；用户可单独关闭某类买卖点在 K 线图上的绘制。

**Independent Test**: 打开 K 线图并打开「分析买卖点」；侧栏或工具栏中有六个开关（一买、一卖、二买、二卖、三买、三卖），默认均为开启；关闭「二买」后图表上仅剩一买、三买与全部卖点；关闭某类后重新打开，该类标记再次出现。

- [x] **T029** [US5] 在 `frontend/src/components/ChartRightTools.vue` 与 `frontend/src/components/ChartRightSidebar.vue` 中增加六个可选开关：一买、一卖、二买、二卖、三买、三卖（对应 `showBuy1`、`showSell1`、`showBuy2`、`showSell2`、`showBuy3`、`showSell3` 或等效命名），默认值均为 `true`；在 `frontend/src/views/TradingViewChart.vue` 中增加上述状态并与侧栏双向绑定，在 `drawAnalysisBsOverlay` 中根据六个开关过滤 `points.buy1` / `points.sell1` / … / `points.sell3`，仅将开启类型对应的点加入 `shapes` 绘制；开关变更时重新执行 `drawAnalysisBsOverlay` 更新图表。

**Checkpoint**: 六个买卖点类型各有独立开关、默认均显示；关闭某类后 K 线图上该类型标记消失，重新开启后恢复。

---

## Phase 16: 一买、一卖连接线高度设为 3%

**Goal**: K 线图分析买卖点叠加时，一买、一卖的连接线长度（锚点到水平线）为价格的 3%；二买/二买/三买/三卖仍为 2%（及相邻错位）。同一天内多个一买/一卖时在 3% 基础上递增错位。

**Independent Test**: 打开「分析买卖点」；一买、一卖标记的连接线垂直长度为锚点价格的 3%；二买、二卖、三买、三卖为 2%（或 2% + 错位）。

- [x] **T030** [US5] 在 `frontend/src/views/TradingViewChart.vue` 的 `drawAnalysisBsOverlay` 中为一买、一卖单独设置连接线高度 3%：构建买点/卖点 shapes 时，对 `buy1`（一买）使用 `baseGapPercentBuy1 = 3`、对 `sell1`（一卖）使用 `baseGapPercentSell1 = 3`，同一天内多点时在 3% 基础上加 `idx * stackStepPercent`；对 `buy2`/`buy3` 与 `sell2`/`sell3` 仍使用 `baseGapPercent = 2` 及既有错位逻辑。传入 `buildBullishShapes` / `buildBearishShapes` 的 `lineGapPercent` 按类型区分（一买/一卖基准 3%，二买/二卖/三买/三卖基准 2%）。

**Checkpoint**: 一买、一卖连接线长 3%；二买/二卖/三买/三卖连接线长 2%（及错位不变）。

---

## Phase 17: 买卖点仅保留竖向连接线且为虚线（取消横向连接线）

**Goal**: K 线图分析买卖点叠加时，不绘制横向连接线（水平射线）；仅保留从 K 线实体指向标记的竖向连接线，且该竖线为虚线。

**Independent Test**: 打开「分析买卖点」；每个买卖点仅有一条竖向连接线（买点从 K 的 low 向下至文案/标记，卖点从 K 的 high 向上至文案/标记），无向右延伸的水平线；竖线为虚线样式。

- [x] **T031** [US5] 在 `frontend/src/tv/bullBearShapes.ts` 中为分析叠加提供「仅竖线+虚线」模式：新增可选参数（如 `verticalOnly?: boolean`、`connectorDashed?: boolean`），当 `verticalOnly` 为 true 时，`buildBullishShapes` / `buildBearishShapes` 不产出 `horizontal_ray` 形状，仅产出从 K 线实体到标记位置的竖向线段（即现有浅灰引线 + 从锚点到水平线价格的竖线合并为一条竖线，或仅保留一条从锚点到文案位置的竖线）；当 `connectorDashed` 为 true 时，该竖线使用 `style.dashed: true`。在 `frontend/src/views/TradingViewChart.vue` 的 `drawAnalysisBsOverlay` 中调用时传入 `verticalOnly: true` 与 `connectorDashed: true`，使分析买卖点只显示虚线竖向连接线、无横向线。

**Checkpoint**: 分析买卖点仅显示竖向虚线连接线，无横向连接线；Demo 看多/看空基类可保持原有横线+竖线（不传 verticalOnly 或传 false）。

---

## Phase 18: 检测第一类买、卖点画的是否正确

**Goal**: 确认 K 线图上一买、一卖标记的绘制符合规格：锚点、连接线长度与样式、文案位置均正确。

**Independent Test**: 打开「分析买卖点」并确保一买、一卖开关开启；选取有第一类买卖点数据的标的与区间；人工或自动化核对：① 一买锚点在该根 K 线的 low（或对应事件 price），连接线向下、长度为该锚点价格的 3%，竖线为虚线，文案「一买」在连接线下方端点；② 一卖锚点在该根 K 线的 high（或对应事件 price），连接线向上、长度为 3%，竖线为虚线，文案「一卖」在连接线上方端点；③ 无横向射线；④ 与麒麟分析页表格中一买/一卖时间节点一致。

- [X] **T032** [US5] 在 `specs/002-analyze-points-table/` 的 quickstart.md 或新建 `specs/002-analyze-points-table/checklists/` 下增加「第一类买卖点绘制验证」检查项：列出上述验收要点（锚点、3% 竖线、虚线、文案、与表格一致）；和/或在 `frontend/src/views/TradingViewChart.vue` 的 `drawAnalysisBsOverlay` 中增加可选开发环境自检（如 `import.meta.env.DEV` 时对前 N 个一买/一卖点断言锚点 price 与 bars 中对应 time 的 low/high 一致、连接线长度约 3%），便于回归时快速发现绘制错误。

**Checkpoint**: 有明确的第一类买卖点绘制验收标准；可选的自检逻辑在开发环境下可运行，或文档中记录人工检查步骤。

---

## Phase 19: Fix 买卖点绘制日期错位一天（20260213 画到 20260212 上）

**Goal**: 修复买卖点标记在 K 线图上错位一天的问题：例如事件日期为 2026-02-13 时，标记应绘制在 2026-02-13 的 K 线上，而非 2026-02-12。根因通常为事件 `dt` 解析出的时间戳与 K 线 bar 的时间约定不一致（时区/UTC 与本地午夜等）。

**Independent Test**: 打开「分析买卖点」，选择日线及包含已知一买/一卖日期的标的与区间；核对麒麟分析表格中某日（如 2026-02-13）的一买/一卖，在 K 线图上应绘制在该日对应的 K 线上，而非前一日或后一日。

- [X] **T033** [US5] 在 `frontend/src/tv/analysisBsOverlay.ts` 与 `frontend/src/views/TradingViewChart.vue` 中修复绘制日期错位：① 将事件与 K 线按「日历日」匹配而非按精确时间戳匹配——用事件 `dt` 得到日历日（YYYYMMDD，可用本地或与 bar 一致的时区），在 `drawAnalysisBsOverlay` 中根据 bars 构建「日历日 → bar」映射（bar 的 time 转为同一时区的日期再映射）；② 绘制时锚点时间采用「匹配到的 bar 的 time」而非 `parseDtToUnixSec(dt)` 的原始值，锚点价格仍用该 bar 的 low/high 或事件 price；③ 若 `analysisBsOverlay` 仍返回 (time, price)，则可在 overlay 内根据 bars 做「dt → 对应 bar 的 time」的转换后返回，或由 TradingViewChart 在拿到 points 后、绘制前将每个 point.time 替换为匹配 bar 的 time。确保日线/分钟线下事件日期与图上 K 线日期一致。

**Checkpoint**: 事件日期 2026-02-13 的买卖点绘制在 2026-02-13 的 K 线上；与麒麟分析表格中的时间节点一致，无错位一天。

---

## Phase 20: 全盘扫描 — 仅第一类买卖点并入库、可查看所有扫描历史 (User Story 6)

**Goal**: 在 `/screen` 全盘扫描中，当前仅扫描第一类买卖点（一买、一卖）并入库；用户可查看所有扫描的历史记录（任务列表 + 按次查看结果）。

**Context**: 现有 `backend` 有 `run_signal_screen`（按 signals 表全部启用信号）、`run_factor_screen`；`frontend` 有 `ScreenScan.vue` 与 `screenApi.run` / `screenApi.getResults`。需限定为「仅第一类买卖点」扫描并落库，并支持「扫描历史」列表与按次查看。

**Independent Test**: 打开 http://localhost:5173/screen；选择交易日并执行扫描，仅第一类买卖点被计算并写入；在「扫描历史」中能看到所有历史任务（任务 ID、类型、交易日、运行时间、状态、条数），点击某次可查看该次结果列表。

- [X] **T034** [US6] 在 `backend/src/services/screen_service.py` 中新增第一类买卖点专用扫描：新增 `run_bs1_screen(session, trade_date, market=None, max_symbols=0)`，仅计算一买、一卖（复用 czsc 分析链路或 `analysis_service` 的 CZSC buy1/sell1 事件列表），对股票池逐只调用并在有 buy1_events 或 sell1_events 时写入 `ScreenResult`（task_type 可新增 `"bs1"` 或复用 `"signal"` 并在 params_json/signal_name 中标明一买一卖）；在 `backend/src/api/v1/screen.py` 的 `ScreenRunBody.task_type` 中增加 `bs1` 选项，`run_screen` 中当 `task_type=="bs1"` 时调用 `run_bs1_screen`。确保全盘扫描可仅执行第一类买卖点并入库。
- [X] **T035** [US6] 在 `backend/src/api/v1/screen.py` 中新增扫描历史列表接口：`GET /screen/runs`，支持分页（limit/offset 或 limit/page），返回 `ScreenTaskRun` 列表（id、task_type、run_at、status、params_json、以及该 run 的 result 条数 count）；供前端展示「所有扫描的历史记录」。
- [X] **T036** [US6] 在 `frontend/src/api/screen.ts` 中增加 `getRuns(params?: { limit?: number; offset?: number })` 调用 `GET /screen/runs`；在 `frontend/src/views/ScreenScan.vue` 中增加「扫描历史」区块：展示历史任务列表（任务 ID、类型、交易日、运行时间、状态、写入条数），支持「查看该次结果」按钮（调用现有 `getResults({ task_run_id })` 并展示）；任务类型选择中增加「第一类买卖点」（对应 task_type=bs1）。确保可查看所有扫描的历史记录。

**Checkpoint**: 全盘扫描可仅扫描第一类买卖点并入库；/screen 页可查看所有扫描历史并按次查看结果。

---

## Phase 21: 全盘扫描结果 — 第一买点/第一卖点时间排序 (User Story 6)

**Goal**: /screen 查看第一类买卖点扫描结果时，表格展示「第一买点时间」「第一卖点时间」列，并支持按第一买点时间排序、按第一卖点时间排序。

**Context**: BS1 扫描结果每条为 `value_result = {"buy1_events": [{dt, price?, pct?}, ...], "sell1_events": [...]}`；需解析后展示可读的一买/一卖时间，并支持列排序。

**Independent Test**: 在 /screen 点击「查看该次结果」查看某次 BS1 扫描；表格出现「第一买点时间」「第一卖点时间」列（如取该股最近一条一买/一卖的 dt）；点击列头可按第一买点时间或第一卖点时间升序/降序排序。

- [x] **T037** [US6] 在 `frontend/src/views/ScreenScan.vue` 中为 BS1 结果增加可排序列与排序：① 当当前展示的结果为 BS1 类型（如 `signal_name==='bs1'` 或根据查看历史时 task_type 为 bs1）时，解析每条 `value_result` JSON，取出 `buy1_events` 与 `sell1_events`；② 表格增加列「第一买点时间」「第一卖点时间」，显示该股最近一条一买/一卖事件的 `dt`（若无则显示「—」）；③ 上述两列设置 `sortable="custom"` 或等效，实现按第一买点时间、第一卖点时间的升序/降序排序（排序时按 dt 字符串或解析后的时间比较）。若后端 `GET /screen/results` 已返回扩展字段（如 `buy1_latest_dt`、`sell1_latest_dt`）则可直接使用，否则在前端解析 `value_result` 后计算并排序。

**Checkpoint**: BS1 扫描结果表格展示第一买点时间、第一卖点时间列，并支持按这两列排序。

---

## Phase 22: 全盘扫描 BS1 使用 research.get_raw_bars 获取日线数据 (User Story 6)

**Goal**: http://localhost:5173/screen 执行第一类买卖点扫描时，K 线日线数据统一从 `czsc/connectors/research.py` 的 `get_raw_bars`（日线走 `get_raw_bars_daily`）获取，而非优先从 backend 本地 KlineStorage（data/klines）读取。

**Context**: 当前 `run_bs1_screen` 使用 `CZSCAdapter(KlineStorage(...))`，会优先从本地存储读日线；用户要求 /screen 的 BS1 扫描数据源改为 research 的 get_raw_bars（数据路径为 cache_path/daily/by_stock，由环境变量 czsc_research_cache 配置）。

**Independent Test**: 配置好 czsc_research_cache 指向含 daily/by_stock 的目录后，在 /screen 选择「第一类买卖点」执行扫描；后端应通过 `czsc.connectors.research.get_raw_bars(symbol, "日线", sdt, edt)` 获取日线并计算一买一卖，不依赖 data/klines 或 UDF 拉取的 K 线。

- [x] **T038** [US6] 在 `backend/src/services/screen_service.py` 的 `run_bs1_screen` 中，创建 AnalysisService 时改为使用「仅从 research 获取日线」的适配器：当 `analysis_service` 为 None 时，不再使用 `KlineStorage(_default_data_path() / "klines")`，改为 `adapter = CZSCAdapter(kline_storage=None)` 并 `analysis_service = AnalysisService(czsc_adapter=adapter)`，使 `get_bars` 不读本地 KlineStorage，统一走 `czsc.connectors.research.get_raw_bars(symbol, "日线", sdt, edt)`（即 research.py 中日线由 `get_raw_bars_daily` 提供）。确保 backend 能正确 import `czsc.connectors.research`（或 `from czsc.connectors import research`），且 run_bs1_screen 仅在此路径下使用 research 作为日线数据源。

**Checkpoint**: /screen 第一类买卖点扫描的日线数据来自 czsc research.get_raw_bars（get_raw_bars_daily），与 research.py 数据源一致。

---

## Phase 23: GET /screen/results 按 task_run_id 全量返回 (User Story 6)

**Goal**: 请求 `GET /api/v1/screen/results?task_run_id=8&limit=500`（或仅 task_run_id）时，支持全量返回该次任务的所有结果，不受 500/5000 条上限截断。

**Context**: 当前 `limit` 为 Query(500, ge=1, le=5000)，单次 run 结果可能超过 5000 条，用户需要查看某次扫描的完整结果列表。

**Independent Test**: 对某次 BS1 扫描（如 task_run_id=8）请求 `GET /api/v1/screen/results?task_run_id=8`；响应应包含该 run 的全部 result 条（或支持 limit=0 表示不限制），前端可一次拿到全量数据。

- [x] **T039** [US6] 在 `backend/src/api/v1/screen.py` 的 `list_screen_results` 中支持全量返回：当传入 `task_run_id` 时，若 `limit` 为 0 或未传则返回该 task_run_id 下的全部结果（不施加 limit）；或将 `limit` 上限提高至 50000、且当仅按 task_run_id 查询时默认使用全量（如 limit 默认改为 50000）。实现时保持 `limit` 的 ge=1 时可改为 ge=0，le=5000 改为 le=100000；当 limit=0 且 task_run_id 有值时执行查询不加 .limit()，否则 .limit(limit)。响应中 `count` 为当前返回条数。确保 `GET /api/v1/screen/results?task_run_id=8&limit=500` 或 `?task_run_id=8` 可全量返回该次任务结果。

**Checkpoint**: 按 task_run_id 查询筛选结果时可全量返回，无 500/5000 条截断。

---

## Phase 24: K 线图分析买卖点 — 仅一买一卖、开关合并、数据来自 BS1 信号 (User Story 5)

**Goal**: TradingViewChart.vue 中「分析买卖点」仅展示一买、一卖；去掉二买二卖三买三卖；开关改为一个（开启时一买一卖同时显示）；叠加逻辑分离到独立模块；买卖点数据改为从 signals 信号 zdy_macd_bs1_V230422 直接获取（或从现有 analysis API 仅取 buy1_events/sell1_events，逻辑上视为 BS1 数据）。

**Context**: 当前为六类买卖点+六个子开关，数据来自 analysisApi.analyze；需简化为仅一买一卖、单开关，并尽量从「信号 zdy_macd_bs1_V230422」链路获取数据。

**Independent Test**: 打开 K 线图，仅有一个「分析买卖点（一买一卖）」开关；打开后只显示一买、一卖标记，无二买二卖三买三卖；数据来源为 BS1 信号（后端 BS1 事件接口或 analysis 仅用 buy1/sell1）；叠加逻辑在独立模块中，TradingViewChart 仅调用该模块。

- [x] **T040** [US5] 在 `frontend/src/views/TradingViewChart.vue` 与 `frontend/src/tv/analysisBsOverlay.ts`（及可选 `frontend/src/api/signals.ts`）中完成：① **去除二买二卖三买三卖**：K 线图只绘制一买、一卖，移除对 buy2/buy3/sell2/sell3 的获取与绘制；侧栏/工具栏去掉二买、二卖、三买、三卖四个子开关，仅保留一个「分析买卖点（一买一卖）」总开关，开启时一买一卖同时显示。② **代码分离**：将「获取 BS1 数据 + 补全 price + 构建 shapes + 绘制」的流程收口到 `frontend/src/tv/analysisBsOverlay.ts`（或新建 `frontend/src/tv/bs1ChartOverlay.ts`），TradingViewChart.vue 中只保留 showAnalysisBs 状态、调用 overlay 的 draw/clear 与 watch。③ **数据来源**：优先改为从 signals 直接获取一买一卖——若后端提供「仅 BS1 事件」接口（如 `GET /api/v1/signals/bs1-events?symbol=&freq=&sdt=&edt=` 返回 `{ buy1_events, sell1_events }`），则 `analysisBsOverlay.ts` 调用该接口；否则保留从 `analysisApi.analyze` 仅取 `buy1_events`、`sell1_events` 作为数据源（不再使用 buy2/buy3/sell2/sell3）。若需后端新接口，在 `backend/src/api/v1/signals.py` 新增 `GET /signals/bs1-events`，内部调用与 czsc 一买一卖相同逻辑（zdy_macd_bs1_V230422 或 analysis 的 buy1/sell1 事件列表），返回 `{ buy1_events: [...], sell1_events: [...] }`。

**Checkpoint**: K 线图仅展示一买一卖、单开关控制；叠加逻辑在独立模块；数据来自 BS1（新 signals/bs1-events 或 analysis 仅 buy1/sell1）。

---

## Dependencies & Execution Order

### Phase 依赖

- **Phase 1 (czsc)**：无前置，可立即开始；完成后 backend 才能写入真实事件数据。
- **Phase 2 (backend)**：依赖 Phase 1（T001/T002 产出）；T004 与 T005 可并行，T006 依赖 T004/T005。
- **Phase 3 (frontend)**：依赖 Phase 2（API 已返回 8 个字段）；T007 可与 T008/T009 并行，T008 与 T009 可并行。
- **Phase 4**：依赖 Phase 3 完成。
- **Phase 5 (Fix 买卖点无数据)**：依赖 Phase 1 完成；T014 为 bug 修复，完成后买卖点表格在满足信号条件时应有数据。
- **Phase 6 (Fix 第一类买卖点没有数据)**：依赖 Phase 5；T015 为第一类买卖点补充结构备选（笔端点），使一买/一卖表在有笔时不再长期为空。
- **Phase 7 (Demo 看多/看空基类)**：仅依赖前端既有 `/demo/shapes` 与 `chartShapes.ts`；T016 与 T017 可并行，T018 依赖 T016/T017 的类型或工厂。
- **Phase 8 (Fix 看多/看空 字体颜色与间隙)**：依赖 Phase 7；T019 在 chartShapes.ts 中修复文案颜色生效，T020 在 bullBearShapes.ts 中为连接线增加 0.2% 间隙，二者可并行。
- **Phase 9 (K 线图分析买卖点叠加)**：依赖 Phase 7/8（看多/看空基类与 chartShapes 可用）；T021 与 T023 可先做（数据接入 + 开关 UI），T022 依赖 T021 的数据结构；T023 与 T021 可并行开发（不同文件）。
- **Phase 10 (Fix 分析买卖点未绘制)**：依赖 Phase 9；T024 为单文件修复，完成后点击开关应能绘制。
- **Phase 11 (Fix 连接线距离与重叠)**：依赖 Phase 9/10；T025 调整 bullBearShapes 默认间隙并在 TradingViewChart 中为多点做垂直错位。
- **Phase 12 (连接线长度 2% + 相邻错开)**：依赖 Phase 11；T026 将默认连接线长度设为 2%（买点 K 线下、卖点 K 线上），并在相邻买卖点时增加连接线距离错开、避免重叠。
- **Phase 13 (上升趋势上方单点 + 连接线错开)**：依赖 Phase 12；T027 在上升趋势时将买卖点置于 K 线图上方、使用单点文案，连接线长度根据附近最高点与邻近买卖点设置并错开。
- **Phase 14 (上下分离 + 70% 尺寸 + 向右偏移 + 浅灰引线)**：依赖 Phase 12（或 Phase 13 若已实现）；T028 实现上下分离模式、标记尺寸 K 线宽度 70%、密集时向右偏移、浅灰色引线指向 K 线实体。
- **Phase 15 (一买/一卖/二买/二卖/三买/三卖 显示开关)**：依赖 Phase 9（分析买卖点叠加已存在）；T029 增加六个独立开关、默认均显示，绘制时按开关过滤。
- **Phase 16 (一买一卖连接线 3%)**：依赖 Phase 12/14；T030 在 TradingViewChart 绘制时为一买/一卖使用 3% 连接线高度，二买/二卖/三买/三卖保持 2%。
- **Phase 17 (仅竖线+虚线)**：依赖 Phase 14/16；T031 在 bullBearShapes 中支持 verticalOnly 与 connectorDashed，K 线图叠加仅绘制虚线竖向连接线、取消横向线。
- **Phase 18 (一买一卖绘制正确性检测)**：依赖 Phase 16/17；T032 增加验收文档或可选自检，确保第一类买、卖点画得正确。
- **Phase 19 (买卖点绘制日期错位一天)**：依赖 Phase 9/18；T033 按日历日匹配事件与 K 线、用 bar 的 time 绘制，修复 20260213 画到 20260212 上的问题。
- **Phase 20 (全盘扫描仅第一类买卖点+历史记录)**：依赖 Phase 1/2（czsc 与分析能力）；T034 后端 BS1 专用扫描并入库，T035 后端 GET /screen/runs 历史列表，T036 前端 /screen 历史区块与 BS1 选项。
- **Phase 21 (扫描结果一买/一卖时间排序)**：依赖 Phase 20；T037 前端 BS1 结果表格增加第一买点时间、第一卖点时间列并支持排序。
- **Phase 22 (BS1 使用 research.get_raw_bars 日线)**：依赖 Phase 20；T038 在 run_bs1_screen 中使用 CZSCAdapter(kline_storage=None)，使日线数据从 czsc.connectors.research.get_raw_bars 获取。
- **Phase 23 (results 全量返回)**：依赖 Phase 20；T039 在 list_screen_results 中当 task_run_id 传入时支持 limit=0 或提高上限以全量返回。
- **Phase 24 (分析买卖点仅一买一卖+BS1 数据源)**：依赖 Phase 9/17；T040 去除二买二卖三买三卖、单开关、逻辑分离、数据从 signals BS1 或 analysis 仅 buy1/sell1 获取。

### 建议执行顺序

1. T001 → T002（或合并为单一方法）→ T003 若在 czsc 则与 T001 同文件。
2. T004、T005 并行 → T006。
3. T007 与 T008、T009 并行（T008/T009 均依赖 T007 类型定义时可先做 T007）。
4. T010～T013 收尾。

### Parallel 建议

- T004 与 T005 可并行（不同文件）。
- T008（涨停跌停表）与 T009（买卖点表）可并行（同一 Vue 文件内不同区块，注意合并时无冲突）。
- T011 与 T012、T013 可部分并行。
- **Phase 7**：T016 与 T017 可并行（同模块内看多/看空两套定义）；T018 依赖 T016/T017 完成后在 ChartShapesDemo.vue 中集成。
- **Phase 8**：T019（chartShapes 文案颜色）与 T020（bullBearShapes 连接线间隙）可并行。
- **Phase 9**：T021（分析数据接入）与 T023（工具栏开关）可并行；T022（绘制）依赖 T021 产出的事件数据结构。
- **Phase 10**：T024 修复点击后未绘制（可见范围、resolution、按日匹配、延迟绘制）。
- **Phase 11**：T025 增大连接线距 K 线间隙并做多点垂直错位防重叠。
- **Phase 12**：T026 买点 K 线下、卖点 K 线上，连接线长度 2%；买卖点相邻时增加连接线距离错开。
- **Phase 13**：T027 上升趋势时买卖点置于 K 线图上方，单点文案，连接线按附近高点与邻近买卖点错开。
- **Phase 14**：T028 买卖点上下分离、尺寸 K 线宽度 70%、密集向右偏移、浅灰引线指 K 线实体。
- **Phase 15**：T029 一买/一卖/二买/二卖/三买/三卖 是否显示的按钮，默认都显示。
- **Phase 16**：T030 一买、一卖连接线高度设为 3%。
- **Phase 17**：T031 买卖点仅竖向连接线且为虚线，取消横向连接线。
- **Phase 18**：T032 检测第一类买、卖点画的是否正确（验收项或自检）。
- **Phase 19**：T033 修复买卖点绘制错位一天（按日历日匹配 bar、用 bar time 绘制）。
- **Phase 20**：T034 全盘扫描仅第一类买卖点（run_bs1_screen + task_type=bs1）；T035 GET /screen/runs 历史列表；T036 /screen 页扫描历史区块与 BS1 选项。
- **Phase 21**：T037 BS1 结果表格展示第一买点时间、第一卖点时间列，并支持按第一买点时间、第一卖点时间排序。
- **Phase 22**：T038 全盘扫描 BS1 从 czsc research.get_raw_bars 获取日线数据（run_bs1_screen 使用 adapter 不挂 KlineStorage）。
- **Phase 23**：T039 GET /screen/results 按 task_run_id 全量返回（limit=0 或提高上限）。
- **Phase 24**：T040 K 线图分析买卖点仅一买一卖、单开关、逻辑分离、数据从 signals zdy_macd_bs1_V230422 或 analysis 仅 buy1/sell1 获取。

---

## Notes

- 规格未强制要求单元测试，故未单独列测试任务；若需补充，可在 Phase 4 增加「czsc 涨停/跌停/买卖点列表的单元测试」与「analysis API 响应包含 8 字段的契约/集成测试」。
- 每完成一阶段可提交一次，便于回滚与 Code Review。
- 时间格式（US3）由后端序列化（T005）与 czsc 层可选格式化（T003）满足，前端仅展示 `dt`，无需再按周期分支。
