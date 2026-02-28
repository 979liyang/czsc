# TradingView Charting Library 中文文档

本文档基于 `charting_library.d.ts` 类型声明，对 TradingView 高级图表的 API 做结构化中文说明，便于在 npc-czsc 项目中集成与二次开发。

---

## 一、概述与入口

### 1.1 模块说明

- **包名**：Charting Library（Advanced Charts）
- **声明文件**：`charting_library.d.ts`
- **入口**：通过构造函数创建图表 Widget，并实现 UDF 风格的数据源（Datafeed）向图表提供 K 线等数据。

### 1.2 全局导出

| 名称 | 类型 | 说明 |
|------|------|------|
| `widget` | `ChartingLibraryWidgetConstructor` | 图表库的构造函数，用于创建 Widget 实例 |
| `version()` | `() => string` | 返回构建版本字符串，如 `"CL v23.012 (internal id ...)"` |

### 1.3 创建图表

```ts
import { widget } from '@/charting_library/charting_library';

const chartWidget = new widget({
  container: document.getElementById('tv_chart_container') ?? 'tv_chart_container',
  datafeed: myDatafeed,  // 实现 IBasicDataFeed
  symbol: '000001.SZ',
  interval: '1D',
  locale: 'zh',
  // ... 其他选项见 ChartingLibraryWidgetOptions
});

// 返回 IChartingLibraryWidget 实例
chartWidget.onChartReady(() => {
  const chart = chartWidget.activeChart();  // IChartWidgetApi
});
```

---

## 二、构造函数选项（ChartingLibraryWidgetOptions）

`new widget(options)` 的 `options` 类型为 `ChartingLibraryWidgetOptions`，常用属性如下。

### 2.1 必填与常用

| 属性 | 类型 | 说明 |
|------|------|------|
| `container` | `HTMLElement \| string` | 挂载图表的 DOM 元素或元素 id |
| `datafeed` | `IBasicDataFeed \| (IBasicDataFeed & IDatafeedQuotesApi)` | 数据源，需实现 K 线、解析标的等接口 |
| `interval` | `ResolutionString` | 默认周期，如 `'1'`、`'60'`、`'1D'`、`'1W'` |
| `locale` | `LanguageCode` | 语言，如 `'zh'`、`'en'` |
| `symbol` | `string` | 可选，默认标的代码 |

### 2.2 尺寸与布局

| 属性 | 类型 | 说明 |
|------|------|------|
| `width` | `number` | 图表宽度（像素） |
| `height` | `number` | 图表高度（像素） |
| `fullscreen` | `boolean` | 是否占满窗口，默认 `false` |
| `autosize` | `boolean` | 是否随容器尺寸变化而自适应，默认 `false` |

### 2.3 功能开关

| 属性 | 类型 | 说明 |
|------|------|------|
| `disabled_features` | `ChartingLibraryFeatureset[]` | 需要关闭的功能列表 |
| `enabled_features` | `ChartingLibraryFeatureset[]` | 需要开启的功能列表 |
| `studies_access` | `AccessList` | 指标白名单/黑名单及是否灰显 |
| `drawings_access` | `AccessList` | 绘图工具白名单/黑名单及是否灰显 |
| `study_count_limit` | `number` | 最多允许的指标数量，最小 2 |

### 2.4 时间与样式

| 属性 | 类型 | 说明 |
|------|------|------|
| `timezone` | `"exchange" \| Timezone` | 时区，如 `"Asia/Shanghai"` |
| `timeframe` | `TimeframeOption` | 默认时间范围，如 `'3M'` 或 `{ from, to }`（Unix 秒） |
| `toolbar_bg` | `string` | 工具栏背景色 |
| `overrides` | `Partial<ChartPropertiesOverrides>` | 图表样式覆盖（背景、网格等） |
| `studies_overrides` | `Partial<StudyOverrides>` | 指标默认样式/输入覆盖 |

### 2.5 存储与调试

| 属性 | 类型 | 说明 |
|------|------|------|
| `charts_storage_url` | `string` | 图表存储服务地址（高层保存/加载） |
| `client_id` | `string` | 存储 API 的 client id |
| `user_id` | `string` | 存储 API 的 user id |
| `load_last_chart` | `boolean` | 是否自动加载上次保存的图表 |
| `debug` | `boolean` | 是否在控制台输出 Datafeed 调试日志 |
| `saved_data` | `object` | 初始加载的已保存图表状态（低层 API） |

---

## 三、Widget 主接口（IChartingLibraryWidget）

由 `new widget(options)` 返回，是与整个图表库交互的主入口。

### 3.1 生命周期与图表 API

| 方法 | 签名/说明 |
|------|-----------|
| `headerReady()` | `(): Promise<void>` 头部就绪的 Promise |
| `onChartReady(callback)` | 图表可用时调用 `callback` |
| `chart(index?)` | `(index?: number): IChartWidgetApi` 获取指定索引的图表 API，不传为当前 |
| `activeChart()` | `(): IChartWidgetApi` 当前激活图表的 API |
| `activeChartIndex()` | `(): number` 当前激活图表索引 |
| `setActiveChart(index)` | 设置当前激活图表 |
| `chartsCount()` | `(): number` 当前布局下的图表数量 |
| `remove()` | 移除 Widget，释放资源 |

### 3.2 标的与周期

| 方法 | 签名/说明 |
|------|-----------|
| `setSymbol(symbol, interval, callback)` | 设置当前图表的标的与周期，数据加载完成后调用 `callback` |
| `symbolInterval()` | `(): SymbolIntervalResult` 当前标的与周期 `{ symbol, interval }` |
| `getIntervals()` | `(): string[]` 支持的周期列表 |
| `mainSeriesPriceFormatter()` | `(): INumberFormatter` 主图价格格式化器 |

### 3.3 保存与加载

| 方法 | 签名/说明 |
|------|-----------|
| `save(callback, options?)` | 低层：将图表状态通过 `callback(state)` 返回 |
| `load(state, extendedData?)` | 低层：从 `state` 加载图表 |
| `getSavedCharts(callback)` | 高层：从服务器获取已保存图表列表，结果通过 `callback(chartRecords)` 返回 |
| `loadChartFromServer(chartRecord)` | 高层：从服务器加载指定图表 |
| `saveChartToServer(onComplete?, onFail?, options?)` | 高层：保存当前图表到服务器 |
| `removeChartFromServer(chartId, onComplete)` | 高层：从服务器删除已保存图表 |

### 3.4 UI 与交互

| 方法 | 签名/说明 |
|------|-----------|
| `createButton(options?)` | 在顶部工具栏创建按钮，返回 `HTMLElement` 或按钮 id |
| `removeButton(buttonIdOrHtmlElement)` | 移除按钮 |
| `createDropdown(params)` | 创建下拉菜单，返回 `Promise<IDropdownApi>` |
| `selectLineTool(linetool, options?)` | 选中指定绘图工具或光标 |
| `selectedLineTool()` | `(): SupportedLineTools` 当前选中的绘图/光标 |
| `onContextMenu(callback)` | 自定义右键菜单，`callback(unixTime, price)` 返回菜单项数组 |
| `onShortcut(shortCut, callback)` | 注册快捷键 |
| `subscribe(event, callback)` | 订阅库事件 |
| `unsubscribe(event, callback)` | 取消订阅 |
| `closePopupsAndDialogs()` | 关闭所有弹窗与对话框 |
| `showNoticeDialog(params)` | 显示仅“确定”的提示框 |
| `showConfirmDialog(params)` | 显示“确定/取消”确认框 |

### 3.5 主题与覆盖

| 方法 | 签名/说明 |
|------|-----------|
| `applyOverrides(overrides)` | 应用图表属性覆盖（不重新加载） |
| `applyStudiesOverrides(overrides)` | 应用指标样式/输入覆盖 |
| `changeTheme(themeName, options?)` | 切换主题 |
| `getTheme()` | `(): ThemeName` 当前主题名 |
| `getLanguage()` | `(): LanguageCode` 当前语言 |

### 3.6 布局（多图）

| 方法 | 签名/说明 |
|------|-----------|
| `layout()` | `(): LayoutType` 当前布局类型，如 `'2h'` |
| `setLayout(layout)` | 设置布局类型 |
| `layoutName()` | 当前布局名称（若已保存） |
| `resetLayoutSizes(disableUndo?)` | 重置多图尺寸 |
| `setLayoutSizes(sizes, disableUndo?)` | 设置各图尺寸 |
| `unloadUnusedCharts()` | 卸载不可见图表，释放资源 |

### 3.7 截图与状态

| 方法 | 签名/说明 |
|------|-----------|
| `takeScreenshot()` | 截图并上传，通过 `subscribe('onScreenshotReady', cb)` 取 URL |
| `takeClientScreenshot(options?)` | 返回 `Promise<HTMLCanvasElement>` 本地截图 |
| `lockAllDrawingTools()` | `(): IWatchedValue<boolean>` 锁定绘图状态 |
| `hideAllDrawingTools()` | `(): IWatchedValue<boolean>` 隐藏绘图状态 |
| `setDebugMode(enable?)` | 开启/关闭调试模式 |

### 3.8 指标与学习

| 方法 | 签名/说明 |
|------|-----------|
| `getStudiesList()` | `(): string[]` 所有支持的指标名称 |
| `getStudyInputs(studyName)` | 指定指标的输入项信息 |
| `getStudyStyles(studyName)` | 指定指标的样式/元信息 |

---

## 四、图表 API（IChartWidgetApi）

通过 `widget.chart(index)` 或 `widget.activeChart()` 获得，用于单张图表的操作。

### 4.1 标的、周期与图表类型

| 方法 | 签名/说明 |
|------|-----------|
| `setSymbol(symbol, options?)` | 切换标的，返回 `Promise<boolean>` |
| `setResolution(resolution, options?)` | 切换周期，返回 `Promise<boolean>` |
| `setChartType(type, callback?)` | 设置图表类型（K 线/折线等），`type` 为 `SeriesType` |
| `symbol()` | `(): string` 当前标的 |
| `resolution()` | `(): ResolutionString` 当前周期 |

### 4.2 数据与可见范围

| 方法 | 签名/说明 |
|------|-----------|
| `setVisibleRange(range, options?)` | 设置可见时间范围，`range: { from, to }`（Unix 秒） |
| `getVisibleRange()` | 当前可见范围 |
| `onDataLoaded()` | `(): ISubscription<() => void>` 新数据加载完成 |
| `dataReady(callback?)` | 数据就绪时调用回调或返回是否已就绪 |
| `resetData()` | 强制重新请求数据（通常先 `resetCache()`） |
| `resetCache()` | 清除缓存 |

### 4.3 事件订阅

| 方法 | 返回 | 说明 |
|------|------|------|
| `onSymbolChanged()` | `ISubscription<(symbol: LibrarySymbolInfo) => void>` | 标的解析完成（含周期等变化） |
| `onIntervalChanged()` | `ISubscription<(interval, timeframeObj) => void>` | 周期或时间范围变化 |
| `onVisibleRangeChanged()` | `ISubscription<(range) => void>` | 可见范围变化 |
| `onChartTypeChanged()` | `ISubscription<(chartType) => void>` | 图表类型变化 |
| `crossHairMoved()` | `ISubscription<(params) => void>` | 十字光标移动 |
| `onHoveredSourceChanged()` | `ISubscription<(sourceId) => void>` | 悬停的指标/序列变化 |

### 4.4 指标（Study）

| 方法 | 签名/说明 |
|------|-----------|
| `createStudy(name, forceOverlay?, lock?, inputs?, overrides?, options?)` | 添加指标，返回 `Promise<EntityId \| null>` |
| `getStudyById(entityId)` | `(): IStudyApi` 获取指标 API |
| `getAllStudies()` | `(): EntityInfo[]` 所有指标 id/name |
| `removeEntity(entityId)` | 删除指定实体（指标或图形） |
| `removeAllStudies()` | 删除全部指标 |

### 4.5 图形（Drawing）

| 方法 | 签名/说明 |
|------|-----------|
| `createShape(point, options)` | 单点图形，如竖线、箭头、文字 |
| `createMultipointShape(points, options)` | 多点图形，如趋势线、矩形 |
| `createAnchoredShape(position, options)` | 锚定图形（随比例位置） |
| `getShapeById(entityId)` | 获取图形 API |
| `getAllShapes()` | `(): EntityInfo[]` 所有图形 |
| `removeAllShapes()` | 删除全部图形 |
| `refreshMarks()` | 重新请求 bar marks 与 timescale marks |
| `clearMarks(marksToClear?)` | 清除标记 |

**createShape 可画的单点图形**（`options.shape`）：

`arrow_up` \| `arrow_down` \| `flag` \| `vertical_line` \| `horizontal_line` \| `long_position` \| `short_position` \| `icon` \| `emoji` \| `sticker` \| `text` \| `anchored_text` \| `note` \| `anchored_note`

**createMultipointShape 可画的多点图形**（`options.shape` 为 `SupportedLineTools` 中除 `cursor`、`dot`、`arrow_cursor`、`eraser`、`measure`、`zoom` 外的类型），常见有：

- 线类：`trend_line`、`horizontal_ray`、`ray`、`extended`、`arrow`、`info_line`、`trend_angle`、`parallel_channel`、`cross_line`
- 形状：`rectangle`、`rotated_rectangle`、`circle`、`ellipse`、`triangle`、`polyline`、`path`、`curve`、`arc`、`double_curve`
- 斐波那契/形态等：`fib_retracement`、`fib_trend_ext`、`fib_channel`、`triangle_pattern`、`head_and_shoulders`、`xabcd_pattern`、`abcd_pattern` 等

样式通过 `options.overrides` 传入，键名一般为 `linetool<工具名>.<属性>`（如 `linetoolarrowmarkup.arrowColor`、`linetooltext.color`），具体见 `charting_library.d.ts` 中的 `ChartCustomizationOptions`。

### 4.6 主图与 Z 序

| 方法 | 签名/说明 |
|------|-----------|
| `getSeries()` | `(): ISeriesApi` 主图序列 API |
| `sendToBack(entities)` | 置于底层 |
| `bringToFront(sources)` | 置于顶层 |
| `bringForward(sources)` | 上移一层 |
| `sendBackward(sources)` | 下移一层 |
| `availableZOrderOperations(sources)` | 查询可用的 Z 序操作 |

### 4.7 操作与比例

| 方法 | 签名/说明 |
|------|-----------|
| `executeActionById(actionId)` | 执行指定操作（如撤销、显示绘图工具栏） |
| `getCheckableActionState(actionId)` | 可勾选操作的当前状态 |
| `getPriceToBarRatio()` / `setPriceToBarRatio(ratio, options?)` | 价格与 K 线高度比 |
| `isPriceToBarRatioLocked()` / `setPriceToBarRatioLocked(value, options?)` | 锁定/解锁该比例 |
| `maximizeChart()` / `restoreChart()` | 最大化/还原图表 |
| `isMaximized()` | 是否已最大化 |
| `getAllPanesHeight()` / `setAllPanesHeight(heights)` | 各窗格高度 |

---

## 五、数据源（Datafeed）

图表库通过数据源获取 K 线与标的信息。数据源需实现 **IBasicDataFeed**（即 `IDatafeedChartApi & IExternalDatafeed`）。

### 5.1 必须实现（IExternalDatafeed）

| 方法 | 说明 |
|------|------|
| `onReady(callback)` | 库初始化时调用，需调用 `callback(config)` 并传入 `DatafeedConfiguration`（如 `supported_resolutions`、`supports_marks` 等） |

### 5.2 必须实现（IDatafeedChartApi）

| 方法 | 说明 |
|------|------|
| `resolveSymbol(symbolName, onResolve, onError, extension?)` | 解析标的名称，通过 `onResolve(LibrarySymbolInfo)` 返回标的元信息，失败时 `onError(message)` |
| `getBars(symbolInfo, resolution, periodParams, onResult, onError)` | 按时间范围/数量请求历史 K 线，通过 `onResult(bars, meta)` 返回，无数据时可传 `meta: { noData: true }` 或 `nextTime` |
| `subscribeBars(symbolInfo, resolution, onTick, listenerGuid, onResetCacheNeededCallback)` | 订阅实时推送，有新 bar 或 tick 时调用 `onTick(bar)` |
| `unsubscribeBars(listenerGuid)` | 取消订阅 |

### 5.3 常用类型

**Bar**（单根 K 线）：

```ts
interface Bar {
  time: number;   // 毫秒级 Unix 时间戳 (UTC)
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}
```

**PeriodParams**（getBars 请求参数）：

```ts
interface PeriodParams {
  from: number;           // 左边界 Unix 秒
  to: number;             // 右边界 Unix 秒（不包含）
  countBack: number;      // 请求的 bar 数量（若支持可优先）
  firstDataRequest: boolean;
}
```

**HistoryCallback**：`(bars: Bar[], meta?: HistoryMetadata) => void`。  
**HistoryMetadata**：`{ noData?: boolean; nextTime?: number | null }`，用于告知“没有更多历史”或下一根可用 bar 的时间（毫秒）。

**ResolutionString**：周期字符串，如 `'1'`、`'5'`、`'60'`、`'1D'`、`'1W'`、`'1M'`。

**LibrarySymbolInfo**：标的元信息，包含 `ticker`、`name`、`exchange`、`session`、`timezone`、`supported_resolutions`、`has_intraday`、`pricescale`、`minmov` 等，详见 d.ts。

### 5.4 配置（DatafeedConfiguration）

在 `onReady(callback)` 中传入的对象常用字段：

| 属性 | 类型 | 说明 |
|------|------|------|
| `supported_resolutions` | `ResolutionString[]` | 支持的周期列表 |
| `exchanges` | `Exchange[]` | 交易所列表，空数组则无交易所筛选 |
| `symbols_types` | `DatafeedSymbolType[]` | 标的类型筛选 |
| `supports_marks` | `boolean` | 是否支持 bar 标记 |
| `supports_timescale_marks` | `boolean` | 是否支持时间轴标记 |
| `supports_time` | `boolean` | 是否提供服务器时间 |

---

## 六、常用枚举与类型索引

### 6.1 图表类型

- **ChartStyle**：UI 展示用（Bar、Candle、Line、Area、HeikinAshi 等）。
- **SeriesType**：API 用（Bars、Candles、Line、Area、HeikenAshi、HollowCandles、Baseline、HiLo、Column 等）。

### 6.2 线条与样式

- **LineStyle** / **OverrideLineStyle**：`Solid = 0`、`Dotted = 1`、`Dashed = 2`。
- **LineStudyPlotStyle**：指标绘图样式（Line、Histogram、Cross、Area、Columns、Circles 等）。

### 6.3 价格与坐标

- **PriceScaleMode**：`Normal`、`Log`、`Percentage`、`IndexedTo100`。
- **MarkLocation**：标记位置（AboveBar、BelowBar、Top、Bottom、Left、Right、Absolute 等）。

### 6.4 操作 ID

- **ActionId**：大量预定义操作 id，如 `Chart.Undo`、`Chart.Redo`、`Chart.Dialogs.ShowChangeSymbol`、`Chart.LineTool.Templates`、`Trading.AddOrder` 等。通过 `IChartWidgetApi.executeActionById(actionId)` 执行。
- **ChartActionId**：图表相关操作的 id 类型（含字符串形式的 id）。

### 6.5 其他常用

- **ClearMarksMode**：清除标记范围（All、BarMarks、TimeScaleMarks）。
- **ThemeName**：主题名，如 `'Light'`、`'Dark'`。
- **LanguageCode**：语言代码，如 `'zh'`、`'en'`。
- **EntityId**：实体（指标、图形）的唯一 id 类型。
- **ISubscription\<T\>**：订阅对象，通常有 `subscribe(listener, handler, once?)`、`unsubscribe(listener)` 等。

---

## 七、与本项目的关系

- **UDF 数据源**：`frontend/src/tv/udfDatafeed.ts` 实现 `getBars`、`resolveSymbol`、`subscribeBars`、`unsubscribeBars`、`onReady`，对接后端 `/api/v1/tv/minute-bars` 与 `/api/v1/tv/history`。
- **Widget 封装**：Vue 组件中创建 `new widget(...)`，并在 `onChartReady` 后通过 **chartWidgetSdk**（`chartWidgetSdk.ts`）调用 `setSymbol`、`setResolution`、`setSymbolAndInterval` 等，避免重复创建/销毁图表。
- **类型**：开发时直接引用 `charting_library.d.ts` 中的 `IChartingLibraryWidget`、`IChartWidgetApi`、`Bar`、`LibrarySymbolInfo`、`ResolutionString` 等即可。

更细的方法签名、可选参数和更多接口请以 `charting_library.d.ts` 为准；官方英文文档见 [TradingView Charting Library Docs](https://www.tradingview.com/charting-library-docs/)。
