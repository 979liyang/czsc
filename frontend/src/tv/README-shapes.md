# TradingView 图形 API 梳理（datafeed-api.d.ts + charting_library.d.ts）

本文档说明 datafeed-api.d.ts 与 charting_library.d.ts 中“能画的图”及参数来源，供 ChartShapesDemo.vue 与 chartShapes.ts 对接参考。

---

## 一、datafeed-api.d.ts：数据源标记（非绘图 API）

datafeed **不提供** createShape/createMultipointShape，仅提供两类“标记”数据，由 datafeed 的 `getMarks` / `getTimescaleMarks` 返回，需在 `DatafeedConfiguration` 中开启对应开关。

### 1.1 配置开关

- **supports_marks**: `true` 时库会调用 `IDatafeedChartApi.getMarks`
- **supports_timescale_marks**: `true` 时库会调用 `IDatafeedChartApi.getTimescaleMarks`

### 1.2 K 线标记：Mark（getMarks）

用于在 K 线柱上显示标记（如事件、财报等）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string \| number | 标记 ID |
| time | number | Unix 时间戳（秒） |
| color | MarkConstColors \| MarkCustomColor | 颜色（red/green/blue/yellow 或 { border, background }） |
| text | string | 文本内容 |
| label | string | 标签 |
| labelFontColor | string | 标签字体颜色 |
| minSize | number | 最小尺寸 |
| borderWidth | number | 可选，边框宽度 |
| hoveredBorderWidth | number | 可选，悬停时边框宽度 |
| imageUrl | string | 可选，图片 URL |
| showLabelWhenImageLoaded | boolean | 可选，有图时是否仍显示文字 |

### 1.3 时间轴标记：TimescaleMark（getTimescaleMarks）

用于在时间轴（横轴）上显示标记。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string \| number | 标记 ID |
| time | number | Unix 时间戳（秒） |
| color | MarkConstColors \| string | 颜色 |
| labelFontColor | string | 可选，标签字体颜色 |
| label | string | 标签 |
| tooltip | string[] | 提示内容数组 |
| shape | TimeScaleMarkShape | 可选，形状 |
| imageUrl | string | 可选，图片 URL |
| showLabelWhenImageLoaded | boolean | 可选，有图时是否仍显示文字 |

**TimeScaleMarkShape** 枚举：`"circle"` \| `"earningUp"` \| `"earningDown"` \| `"earning"`

---

## 二、charting_library.d.ts：绘图 API（createShape / createMultipointShape）

图表上的“画图”由 **charting_library** 的 Drawings API 提供，与 datafeed 无关。

### 2.1 createShape（单点图形）

`chart.createShape(point, { shape, text?, overrides, ... })`

**CreateShapeOptions.shape** 枚举：

- `arrow_up` | `arrow_down` | `flag` | `vertical_line` | `horizontal_line`
- `long_position` | `short_position` | `icon` | `emoji` | `sticker`
- `text` | `anchored_text` | `note` | `anchored_note`

说明：`long_position` / `short_position` 与 `anchored_text` / `anchored_note` 通常需配合 `createAnchoredShape`（锚定坐标），本 Demo 仅做 createShape 单点类型。

### 2.2 createMultipointShape（多点图形）

`chart.createMultipointShape(points, { shape, overrides, ... })`

**CreateMultipointShapeOptions.shape** 来自 `SupportedLineTools`，排除 `cursor`、`dot`、`arrow_cursor`、`eraser`、`measure`、`zoom` 等。

常用多点 shape（节选）：

- 线段/射线：`trend_line` | `horizontal_ray` | `ray` | `extended` | `horizontal_line` | `cross_line`
- 形状：`rectangle` | `rotated_rectangle` | `circle` | `ellipse` | `triangle`
- 折线/曲线：`polyline` | `path` | `curve` | `arc` | `double_curve`
- 箭头/标记：`arrow` | `arrow_marker` | `flag` | `price_label` | `price_note`
- 斐波那契/形态等：`fib_retracement` | `fib_channel` | `fib_timezone` | `parallel_channel` | `head_and_shoulders` | `abcd_pattern` 等

完整列表以 `charting_library.d.ts` 中的 **SupportedLineTools** 类型为准。

### 2.3 Overrides 键名格式

- 格式：`linetool<工具名>.<属性>`（工具名为小写，如 linetooltext、linetoolvertline）
- 完整属性列表见 `charting_library.d.ts` 中的 `DrawingOverrides` 及各个 `*LineToolOverrides` 接口（如 TextLineToolOverrides、VertlineLineToolOverrides、CircleLineToolOverrides 等）

---

## 三、chartShapes.ts 已对接的 PREFIX 与接口

| 图形 | create 方式 | shape 名 | linetool 前缀 | d.ts Overrides 接口 |
|------|-------------|----------|----------------|---------------------|
| 文案 | createShape | text | linetooltext | TextLineToolOverrides |
| 矩形 | createMultipointShape | rectangle | linetoolrectangle | （Rectangle 相关） |
| 趋势线 | createMultipointShape | trend_line | linetooltrendline | TrendlineLineToolOverrides |
| 箭头上/下 | createShape | arrow_up / arrow_down | linetoolarrowmarkup / linetoolarrowmarkdown | Arrowmarkup/ArrowmarkdownLineToolOverrides |
| 三角形 | createMultipointShape | triangle | linetooltriangle | TriangleLineToolOverrides |
| 竖线 | createShape | vertical_line | linetoolvertline | VertlineLineToolOverrides |
| 圆 | createMultipointShape | circle | linetoolcircle | CircleLineToolOverrides |
| 水平射线 | createMultipointShape | trend_line（两点） | linetoolhorzray / linetooltrendline | HorzrayLineToolOverrides / TrendlineLineToolOverrides |

---

## 四、ChartShapesDemo 常用 Overrides 属性摘要（来自 charting_library.d.ts）

以下为 Demo 已用或待用图形对应的 LineToolOverrides 主要键名（前缀 linetoolxxx，省略前缀时以“短名”在 overrides 中亦可生效的部分）。

### HorzlineLineToolOverrides（水平线 createShape: horizontal_line）

| 短名 | 默认值 | 说明 |
|------|--------|------|
| bold | false | 粗体 |
| fontsize | 12 | 字号 |
| horzLabelsAlign | center | 水平对齐 |
| italic | false | 斜体 |
| linecolor | #2962FF | 线色 |
| linestyle | 0 | 线型 0 实线 1 虚线 |
| linewidth | 2 | 线宽 |
| showPrice | true | 显示价格 |
| textcolor | #2962FF | 文字颜色 |
| vertLabelsAlign | middle | 垂直对齐 |

### HorzrayLineToolOverrides（水平射线，本 Demo 用 trend_line 两点模拟）

| 短名 | 默认值 |
|------|--------|
| bold, fontsize, horzLabelsAlign, italic | 同 Horzline |
| linecolor | #2962FF |
| linestyle | 0 |
| linewidth | 2 |
| showPrice | true |
| textcolor | #2962FF |
| vertLabelsAlign | top |

### TrendlineLineToolOverrides（趋势线 / 线段）

| 短名 | 默认值 |
|------|--------|
| alwaysShowStats, bold, extendLeft, extendRight | false |
| fontsize | 14 |
| horzLabelsAlign | center |
| italic | false |
| leftEnd, rightEnd | 0 |
| linecolor | #2962FF |
| linestyle | 0 |
| linewidth | 2 |
| showAngle, showBarsRange, showDateTimeRange, showDistance 等 | false |
| textcolor | #2962FF |
| vertLabelsAlign | bottom |

### EllipseLineToolOverrides（椭圆）

| 短名 | 默认值 |
|------|--------|
| backgroundColor | rgba(242, 54, 69, 0.2) |
| bold, italic | false |
| color | #F23645 |
| fillBackground | true |
| fontSize | 14 |
| linewidth | 2 |
| textColor | #F23645 |
| transparency | 50 |

### PolylineLineToolOverrides（折线）

| 短名 | 默认值 |
|------|--------|
| backgroundColor | rgba(0, 188, 212, 0.2) |
| fillBackground | true |
| filled | false |
| linecolor | #00bcd4 |
| linestyle | 0 |
| linewidth | 2 |
| transparency | 80 |

### PathLineToolOverrides（路径）

| 短名 | 默认值 |
|------|--------|
| leftEnd | 0 |
| lineColor | #2962FF |
| lineStyle | 0 |
| lineWidth | 2 |
| rightEnd | 1 |

### RayLineToolOverrides（射线）

与 Trendline 类似，含 extendLeft、extendRight、linecolor、linewidth、linestyle、fontsize、textcolor、horzLabelsAlign、vertLabelsAlign 等，前缀 `linetoolray.`。

### ExtendedLineToolOverrides（延长线）

与 Ray 类似，前缀 `linetoolextended.`，默认 extendLeft、extendRight 为 true。

---

## 五、参考文件

- 数据源标记类型：`frontend/charting_library/datafeed-api.d.ts`（Mark, TimescaleMark, TimeScaleMarkShape, getMarks, getTimescaleMarks）
- 绘图 API 与 Overrides：`frontend/charting_library/charting_library.d.ts`（CreateShapeOptions, CreateMultipointShapeOptions, SupportedLineTools, DrawingOverrides, *LineToolOverrides）

---

## 六、属性审计结果（与 d.ts 对照）

**本次检测结论**：已去除 text 的重复键 `fontSize`（仅保留 `fontsize` 传入 overrides）。已补全 horzline 的 fontsize、horzLabelsAlign、italic、textcolor、vertLabelsAlign。**文案**：支持 hAlign（文案相对锚点水平对齐）、vAlign（文案相对锚点垂直对齐）；d.ts 的 TextLineToolOverrides 无此二键，由 Demo 侧传入 style 供后续扩展，实际效果以 TV 版本为准。未实现的图形与信号标记见 §6.10。

### 6.1 TextLineToolOverrides（linetooltext）

| 类型 | 键 | 说明 |
|------|----|------|
| 扩展 | hAlign、vAlign | 文案相对锚点水平/垂直对齐；d.ts 无此二键；Demo 同时传入 linetooltext.hAlign/vAlign 与 linetooltext.horzLabelsAlign/vertLabelsAlign。**文案自身居中**：当 hAlign=center 且 vAlign=middle 时，在 createShape 后对 entity 调用内部方法 `centerPosition()`（若存在），库会在下次渲染时按文本尺寸重算锚点使视觉居中；若当前 TV 版本 entity 未暴露该方法则仍依赖 override 键 |
| 扩展 | verticalPlacement、connectorLengthPercent、textGapPercent、connectorChartGapPercent | 文案置于锚点「上方」或「下方」；上方时连接线锚点为 K 线最高点、下方时为最低点；连接线长度、文案距连接线、连接线起点距 K 线图（价格%）可调，默认间距 1% 防重叠；上方时文案在连接线之上 |
| 扩展 | 连接线 | 连接线颜色 connectorLineColor、线宽 connectorLineWidth，起点距 K 线图 connectorChartGapPercent（价格%），默认与文案 color 一致、线宽 1 |

### 6.2 VertlineLineToolOverrides（linetoolvertline）

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | color/width/dashed 映射为 linecolor/linewidth/linestyle |
| 缺失 | （无） | 全部 11 属性已对接 |

### 6.3 HorzlineLineToolOverrides（linetoolhorzline）

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | |
| 缺失 | fontsize, horzLabelsAlign, italic, textcolor, vertLabelsAlign | 需在 cfg 与 drawHorizontalLine 中补全 |

### 6.4 FlagmarkLineToolOverrides（linetoolflagmark）

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | |
| 缺失 | （无） | 仅 flagColor，已对接 |

### 6.5 Arrowmarkup/ArrowmarkdownLineToolOverrides

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | |
| 缺失 | （无） | 全部已对接 |

### 6.6 TriangleLineToolOverrides（linetooltriangle）

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | sizePercent 为 UI 计算用，不传入 overrides |
| 缺失 | （无） | 全部已对接 |

### 6.7 CircleLineToolOverrides（linetoolcircle）

| 类型 | 键 | 说明 |
|------|----|------|
| 精简 | 已去除 bold、italic、fontSize、textColor | 圆仅绘制边框与填充，不显示文字；Demo 仅保留 color、backgroundColor、fillBackground、linewidth，见 §6.10 |
| 多出 | （无） | radiusPercent 为 UI 计算 onCircle 用，不传入 overrides |
| 缺失 | （无） | 保留项已对接 |

### 6.8 TrendlineLineToolOverrides（射线/线段 ray）

| 类型 | 键 | 说明 |
|------|----|------|
| 多出 | （无） | lengthDays、labelText 等为 UI/逻辑用 |
| 缺失 | （无） | 当前仅用 linecolor、linewidth、linestyle，符合 |

### 6.9 矩形（rectangle）

| 类型 | 键 | 说明 |
|------|----|------|
| 说明 | — | d.ts 无独立 RectangleLineToolOverrides；有 DateandpricerangeLineToolOverrides（linetooldateandpricerange）。当前使用 linetoolrectangle + fillBackground、backgroundColor、transparency、linewidth、color；若库不认则改用 linetooldateandpricerange 前缀及对应键。 |

### 6.10 各图形必要属性（精简后）

Demo 仅保留对图形有直接视觉影响的属性，去除无影响项：

| 图形 | 保留属性 | 已去除 |
|------|----------|--------|
| 圆 circle | color、backgroundColor、fillBackground、linewidth；radiusPercent 仅作 UI 计算 | bold、italic、fontSize、textColor（圆不显示文字） |
| 三角形 triangle | backgroundColor、color、fillBackground、linewidth、transparency、sizePercent | 无文字键 |
| 箭头 arrow | arrowColor、color、bold、fontsize、italic、showLabel | — |
| 竖线 verticalLine | linecolor、linewidth、linestyle、bold、extendLine、fontsize、showTime、textcolor、horzLabelsAlign、vertLabelsAlign、textOrientation、italic | — |
| 水平线 horizontalLine | linecolor、linewidth、linestyle、bold、showPrice、fontsize、textcolor、horzLabelsAlign、vertLabelsAlign、italic | — |
| 旗帜 flag | flagColor | — |
| 矩形 rect | fillColor、borderColor、borderWidth、transparency | — |
| 射线 ray | color、width、dashed、label*（线段+文案） | — |
| 文案 text | TextLineToolOverrides 全部 12 属性 | — |

### 6.11 未实现的图形/信号标记

以下在 d.ts 中存在，本 Demo 暂未对接：

- **createShape 单点**：icon、emoji、sticker、note（linetoolicon、linetoolemoji、linetoolsticker、linetoolcomment）
- **createMultipointShape 多点**：ellipse、ray、extended、polyline、path、curve（linetoolellipse、linetoolray、linetoolextended、linetoolpolyline、linetoolpath、linetoolcurve 等）
- **信号标记**：price_label、price_note、arrow_marker、cross_line、signpost 等（若需可后续扩展）
