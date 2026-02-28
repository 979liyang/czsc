/**
 * TradingView Chart Widget 前端 SDK
 *
 * 封装 widget 实例，提供两类能力：
 * 1. 更换 K 线周期、更换股票（无需销毁重建 widget）
 * 2. 通知图表：新增/修改/删除 指标、图形、覆盖层等
 *
 * 底层为 charting_library 的 IChartingLibraryWidget 与 IChartWidgetApi，
 * 详见 charting_library.d.ts 与 docs/tv-chart-sdk.md。
 */

/** 库返回的 widget 实例类型（来自 TradingView.widget） */
export type TVWidget = any;

/** 库返回的当前图表 API（widget.activeChart()） */
export type TVChartApi = any;

/** K 线周期字符串：'1' | '5' | '15' | '30' | '60' | 'D' | 'W' | 'M' 等 */
export type ResolutionString = string;

/** 图表上实体（指标/图形）的 ID */
export type EntityId = string;

/** 图形上的点：时间（Unix 秒） + 价格 */
export interface ShapePoint {
  time: number;
  price: number;
}

/**
 * Widget SDK 封装
 *
 * 使用方式：
 *   const sdk = createChartWidgetSdk();
 *   // 创建 widget 后注入
 *   sdk.setWidget(widgetRef.value);
 *   // 更换股票与周期
 *   sdk.setSymbolAndInterval('600078.SH', '30', () => console.log('done'));
 *   // 在 K 线上添加数据
 *   const chart = sdk.getActiveChart();
 *   if (chart) chart.createStudy('Moving Average', false, false, { length: 10 });
 */
export interface IChartWidgetSdk {
  /** 注入 widget 实例（在 onChartReady 或之后调用） */
  setWidget(widget: TVWidget | null): void;

  /** 当前是否已有可用 widget */
  isReady(): boolean;

  /**
   * 更换标的与 K 线周期（不销毁 widget，仅刷新数据）
   * 对应库方法：widget.setSymbol(symbol, interval, callback)
   */
  setSymbolAndInterval(symbol: string, interval: ResolutionString, onDone?: () => void): void;

  /**
   * 仅更换标的
   * 对应：widget.activeChart().setSymbol(symbol, options?)
   */
  setSymbol(symbol: string, onDone?: () => void): Promise<boolean>;

  /**
   * 仅更换 K 线周期
   * 对应：widget.activeChart().setResolution(resolution, options?)
   */
  setResolution(resolution: ResolutionString, onDone?: () => void): Promise<boolean>;

  /**
   * 获取当前图表的 API，用于添加指标、图形、监听事件等
   * 对应：widget.activeChart()
   */
  getActiveChart(): TVChartApi | null;

  /**
   * 获取当前标的与周期
   * 对应：widget.symbolInterval()
   */
  getSymbolInterval(): { symbol: string; interval: ResolutionString } | null;

  /** 销毁 widget（如切换页面时） */
  remove(): void;
}

/**
 * 创建 Chart Widget SDK 实例
 */
export function createChartWidgetSdk(): IChartWidgetSdk {
  let widget: TVWidget | null = null;

  return {
    setWidget(w: TVWidget | null) {
      widget = w;
    },

    isReady() {
      return widget != null && typeof widget.activeChart === 'function';
    },

    setSymbolAndInterval(symbol: string, interval: ResolutionString, onDone?: () => void) {
      if (!widget) return;
      widget.setSymbol(symbol, interval, onDone ?? (() => {}));
    },

    async setSymbol(symbol: string, onDone?: () => void) {
      const chart = widget?.activeChart?.();
      if (!chart) return false;
      const ok = await chart.setSymbol(symbol, onDone ? { callback: onDone } : undefined);
      return ok ?? false;
    },

    async setResolution(resolution: ResolutionString, onDone?: () => void) {
      const chart = widget?.activeChart?.();
      if (!chart) return false;
      const ok = await chart.setResolution(resolution, onDone ? { callback: onDone } : undefined);
      return ok ?? false;
    },

    getActiveChart(): TVChartApi | null {
      if (!widget?.activeChart) return null;
      return widget.activeChart();
    },

    getSymbolInterval() {
      if (!widget?.symbolInterval) return null;
      const r = widget.symbolInterval();
      return r ? { symbol: r.symbol ?? '', interval: r.interval ?? '' } : null;
    },

    remove() {
      try {
        widget?.remove?.();
      } finally {
        widget = null;
      }
    },
  };
}

/**
 * 当前图表 API（activeChart）常用方法速查
 *
 * 更换标的/周期：
 *   - setSymbol(symbol: string, options?: { callback }): Promise<boolean>
 *   - setResolution(resolution: string, options?: { callback }): Promise<boolean>
 *
 * 指标（Study）：
 *   - createStudy(name, forceOverlay?, lock?, inputs?, overrides?, options?): Promise<EntityId | null>
 *   - getStudyById(entityId): IStudyApi
 *   - getAllStudies(): { id: EntityId; name: string }[]
 *   - removeEntity(entityId)
 *   - removeAllStudies()
 *
 * 图形（Drawing）：
 *   - createShape(point: { time, price }, options: { shape, ... }): Promise<EntityId>
 *   - createMultipointShape(points: ShapePoint[], options): Promise<EntityId>
 *   - createAnchoredShape(position: { x, y }, options): Promise<EntityId>
 *   - getShapeById(entityId): ILineDataSourceApi
 *   - getAllShapes(): { id: EntityId; name: string }[]
 *   - removeEntity(entityId)
 *   - removeAllShapes()
 *
 * 图表状态与覆盖：
 *   - applyOverrides(overrides): 图表样式覆盖
 *   - setVisibleRange(range: { from, to }, options?): 设置可见时间范围
 *
 * 事件订阅（需在 onChartReady 后调用）：
 *   - onDataLoaded(): ISubscription
 *   - onSymbolChanged(): ISubscription<(symbol: LibrarySymbolInfo) => void>
 *   - onIntervalChanged(): ISubscription<(interval, timeframeObj) => void>
 *   - onVisibleRangeChanged(): ISubscription<(range) => void>
 *   - crossHairMoved(): ISubscription<(params) => void>
 *
 * 完整类型见 charting_library.d.ts 中的 IChartWidgetApi、IChartingLibraryWidget。
 */
export const CHART_API_CHEATSHEET = true;
