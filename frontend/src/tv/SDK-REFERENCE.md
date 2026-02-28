# TradingView Charting Library SDK 参考

本文档与 `charting_library.d.ts` 对应，给出常用 API 的**类型签名**与**简要说明**，便于在 TypeScript 中查阅。完整中文说明见 [CHARTING_LIBRARY_CN.md](./CHARTING_LIBRARY_CN.md)，业务封装用法见 [README-SDK.md](./README-SDK.md)。

---

## 1. 入口与构造

```ts
import { widget } from '@/charting_library/charting_library';

// 类型
declare const widget: ChartingLibraryWidgetConstructor;

interface ChartingLibraryWidgetConstructor {
  new (options: ChartingLibraryWidgetOptions | TradingTerminalWidgetOptions): IChartingLibraryWidget;
}
```

---

## 2. 构造选项（ChartingLibraryWidgetOptions）核心字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `container` | `HTMLElement \| string` | ✓ | 挂载容器 |
| `datafeed` | `IBasicDataFeed \| (IBasicDataFeed & IDatafeedQuotesApi)` | ✓ | 数据源 |
| `interval` | `ResolutionString` | ✓ | 默认周期 |
| `locale` | `LanguageCode` | ✓ | 语言 |
| `symbol` | `string` | | 默认标的 |
| `width` | `number` | | 宽度 |
| `height` | `number` | | 高度 |
| `timezone` | `"exchange" \| Timezone` | | 时区 |
| `fullscreen` | `boolean` | | 全屏 |
| `autosize` | `boolean` | | 随容器缩放 |
| `debug` | `boolean` | | Datafeed 调试日志 |
| `disabled_features` | `ChartingLibraryFeatureset[]` | | 禁用功能 |
| `enabled_features` | `ChartingLibraryFeatureset[]` | | 启用功能 |
| `overrides` | `Partial<ChartPropertiesOverrides>` | | 图表样式覆盖 |
| `studies_overrides` | `Partial<StudyOverrides>` | | 指标默认覆盖 |
| `saved_data` | `object` | | 初始图表状态（低层） |
| `charts_storage_url` | `string` | | 存储服务地址 |
| `client_id` | `string` | | 存储 client id |
| `user_id` | `string` | | 存储 user id |

---

## 3. IChartingLibraryWidget（Widget 实例）

```ts
// 生命周期与图表
headerReady(): Promise<void>;
onChartReady(callback: EmptyCallback): void;
chart(index?: number): IChartWidgetApi;
activeChart(): IChartWidgetApi;
activeChartIndex(): number;
setActiveChart(index: number): void;
chartsCount(): number;
remove(): void;

// 标的与周期
setSymbol(symbol: string, interval: ResolutionString, callback: EmptyCallback): void;
symbolInterval(): SymbolIntervalResult;  // { symbol, interval }
getIntervals(): string[];
mainSeriesPriceFormatter(): INumberFormatter;

// 保存/加载（低层）
save(callback: (state: object) => void, options?: SaveChartOptions): void;
load(state: object, extendedData?: SavedStateMetaInfo): Promise<void>;

// 保存/加载（高层）
getSavedCharts(callback: (chartRecords: SaveLoadChartRecord[]) => void): void;
loadChartFromServer(chartRecord: SaveLoadChartRecord): Promise<void>;
saveChartToServer(onComplete?: EmptyCallback, onFail?: (error: SaveChartErrorInfo) => void, options?: SaveChartToServerOptions): void;
removeChartFromServer(chartId: string | number, onCompleteCallback: EmptyCallback): void;

// UI
createButton(options?: CreateButtonOptions): HTMLElement | string;
removeButton(buttonIdOrHtmlElement: HTMLElement | string): void;
createDropdown(params: DropdownParams): Promise<IDropdownApi>;
selectLineTool(linetool: SupportedLineTools, options?: IconOptions | EmojiOptions): Promise<void>;
selectedLineTool(): SupportedLineTools;
onContextMenu(callback: (unixTime: number, price: number) => ContextMenuItem[]): void;
onShortcut(shortCut: string | number | (string | number)[], callback: EmptyCallback): void;
subscribe<EventName extends keyof SubscribeEventsMap>(event: EventName, callback: SubscribeEventsMap[EventName]): void;
unsubscribe<EventName extends keyof SubscribeEventsMap>(event: EventName, callback: SubscribeEventsMap[EventName]): void;
closePopupsAndDialogs(): void;
showNoticeDialog(params: DialogParams<() => void>): void;
showConfirmDialog(params: DialogParams<(confirmed: boolean) => void>): void;

// 主题与覆盖
applyOverrides<TOverrides extends Partial<ChartPropertiesOverrides>>(overrides: TOverrides): void;
applyStudiesOverrides(overrides: object): void;
changeTheme(themeName: ThemeName, options?: ChangeThemeOptions): Promise<void>;
getTheme(): ThemeName;
getLanguage(): LanguageCode;

// 布局
layout(): LayoutType;
setLayout(layout: LayoutType): void;
layoutName(): string;
resetLayoutSizes(disableUndo?: boolean): void;
setLayoutSizes(sizes: Partial<LayoutSizes>, disableUndo?: boolean): void;
unloadUnusedCharts(): void;

// 截图与调试
takeScreenshot(): void;
takeClientScreenshot(options?: Partial<ClientSnapshotOptions>): Promise<HTMLCanvasElement>;
setDebugMode(enable?: boolean): void;

// 指标元数据
getStudiesList(): string[];
getStudyInputs(studyName: string): StudyInputInformation[];
getStudyStyles(studyName: string): StudyStyleInfo;
```

---

## 4. IChartWidgetApi（单图 API）

```ts
// 标的 / 周期 / 类型
setSymbol(symbol: string, options?: SetSymbolOptions | (() => void)): Promise<boolean>;
setResolution(resolution: ResolutionString, options?: SetResolutionOptions | (() => void)): Promise<boolean>;
setChartType(type: SeriesType, callback?: () => void): void;
symbol(): string;
resolution(): ResolutionString;

// 可见范围与数据
setVisibleRange(range: SetVisibleTimeRange, options?: SetVisibleRangeOptions): Promise<void>;
getVisibleRange(): VisibleBarsTimeRange | null;
onDataLoaded(): ISubscription<() => void>;
dataReady(callback?: () => void): boolean;
resetData(): void;
resetCache(): void;

// 事件
onSymbolChanged(): ISubscription<(symbol: LibrarySymbolInfo) => void>;
onIntervalChanged(): ISubscription<(interval: ResolutionString, timeFrameParameters: { timeframe?: TimeFrameValue }) => void>;
onVisibleRangeChanged(): ISubscription<(range: VisibleTimeRange) => void>;
onChartTypeChanged(): ISubscription<(chartType: SeriesType) => void>;
crossHairMoved(): ISubscription<(params: CrossHairMovedEventParams) => void>;
onHoveredSourceChanged(): ISubscription<(sourceId: EntityId) => void>;

// 指标
createStudy<TOverrides>(name: string, forceOverlay?: boolean, lock?: boolean, inputs?: Record<string, StudyInputValue>, overrides?: TOverrides, options?: CreateStudyOptions): Promise<EntityId | null>;
getStudyById(entityId: EntityId): IStudyApi;
getAllStudies(): EntityInfo[];
removeEntity(entityId: EntityId): void;
removeAllStudies(): void;

// 图形
createShape<TOverrides>(point: ShapePoint, options: CreateShapeOptions<TOverrides>): Promise<EntityId>;
createMultipointShape<TOverrides>(points: ShapePoint[], options: CreateMultipointShapeOptions<TOverrides>): Promise<EntityId>;
createAnchoredShape<TOverrides>(position: Position, options: CreateAnchoredShapeOptions<TOverrides>): Promise<EntityId>;
getShapeById(entityId: EntityId): ILineDataSourceApi;
getAllShapes(): EntityInfo[];
removeAllShapes(): void;
refreshMarks(): void;
clearMarks(marksToClear?: ClearMarksMode): void;

// 主图与 Z 序
getSeries(): ISeriesApi;
sendToBack(entities: readonly EntityId[]): void;
bringToFront(sources: readonly EntityId[]): void;
bringForward(sources: readonly EntityId[]): void;
sendBackward(sources: readonly EntityId[]): void;
availableZOrderOperations(sources: readonly EntityId[]): AvailableZOrderOperations;

// 操作与比例
executeActionById(actionId: ChartActionId): void;
getCheckableActionState(actionId: ChartActionId): boolean | null;
getPriceToBarRatio(): number | null;
setPriceToBarRatio(ratio: number, options?: UndoOptions): void;
isPriceToBarRatioLocked(): boolean;
setPriceToBarRatioLocked(value: boolean, options?: UndoOptions): void;
maximizeChart(): void;
isMaximized(): boolean;
restoreChart(): void;
getAllPanesHeight(): number[];
setAllPanesHeight(heights: readonly number[]): void;
```

---

## 5. 数据源（Datafeed）

### 5.1 类型定义

```ts
type IBasicDataFeed = IDatafeedChartApi & IExternalDatafeed;

// 必须实现
interface IExternalDatafeed {
  onReady(callback: OnReadyCallback): void;
}

interface IDatafeedChartApi {
  resolveSymbol(symbolName: string, onResolve: ResolveCallback, onError: DatafeedErrorCallback, extension?: SymbolResolveExtension): void;
  getBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, periodParams: PeriodParams, onResult: HistoryCallback, onError: DatafeedErrorCallback): void;
  subscribeBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, onTick: SubscribeBarsCallback, listenerGuid: string, onResetCacheNeededCallback: () => void): void;
  unsubscribeBars(listenerGuid: string): void;
}
```

### 5.2 核心类型

```ts
// 单根 K 线（time 为毫秒 UTC）
interface Bar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

// getBars 请求参数（from/to 为秒）
interface PeriodParams {
  from: number;
  to: number;
  countBack: number;
  firstDataRequest: boolean;
}

// getBars 回调：onResult(bars, meta?)
type HistoryCallback = (bars: Bar[], meta?: HistoryMetadata) => void;

interface HistoryMetadata {
  noData?: boolean;
  nextTime?: number | null;  // 毫秒，下一根可用 bar 时间
}

// 周期字符串
type ResolutionString = string;  // '1' | '5' | '60' | '1D' | '1W' | '1M' 等
```

### 5.3 配置（onReady 回调参数）

```ts
interface DatafeedConfiguration {
  supported_resolutions?: ResolutionString[];
  exchanges?: Exchange[];
  symbols_types?: DatafeedSymbolType[];
  supports_marks?: boolean;
  supports_timescale_marks?: boolean;
  supports_time?: boolean;
  // ... 更多见 d.ts
}
```

---

## 6. 常用枚举与类型名

| 类型名 | 用途 |
|--------|------|
| `ResolutionString` | 周期字符串 |
| `SeriesType` | 图表类型（Bars, Candles, Line, Area, HeikenAshi 等） |
| `ChartStyle` | 图表样式枚举（与 UI 对应） |
| `EntityId` | 指标/图形实体 id |
| `ChartActionId` | 执行操作的 id（如 `'undo'`、`'drawingToolbarAction'`） |
| `ActionId` | 预定义操作枚举 |
| `LineStyle` / `OverrideLineStyle` | 线型 Solid/Dotted/Dashed |
| `ClearMarksMode` | All / BarMarks / TimeScaleMarks |
| `ThemeName` | 主题名 |
| `LanguageCode` | 语言代码 |
| `SymbolIntervalResult` | `{ symbol: string; interval: string }` |
| `ShapePoint` | `{ time: number; price: number }` 或时间+其他 |
| `LibrarySymbolInfo` | 标的元信息（resolveSymbol 返回） |

---

## 7. 订阅对象（ISubscription）

事件类方法（如 `onIntervalChanged()`）返回 `ISubscription<T>`，用法示例：

```ts
const sub = chart.onIntervalChanged().subscribe(
  null,           // listener 对象（用于 unsubscribe）
  (interval, tf) => { console.log(interval); },
  false           // 是否只触发一次
);
// 取消：sub.unsubscribe(null);
```

---

## 8. 本仓库相关文件

| 文件 | 说明 |
|------|------|
| `charting_library/charting_library.d.ts` | 完整类型声明（约 3 万行） |
| `src/tv/CHARTING_LIBRARY_CN.md` | 详细中文说明（本文档的详细版） |
| `src/tv/README-SDK.md` | chartWidgetSdk 用法与业务集成 |
| `src/tv/udfDatafeed.ts` | UDF 数据源实现（getBars / resolveSymbol 等） |
| `src/tv/chartWidgetSdk.ts` | Widget 封装：setSymbolAndInterval、getActiveChart 等 |

具体方法重载、可选参数和更多接口以 `charting_library.d.ts` 为准。
