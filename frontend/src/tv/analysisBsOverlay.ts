/**
 * 麒麟分析买卖点叠加：拉取 /analysis 同源数据，产出供 K 线图绘制的锚点列表。
 * 仅一买一卖（BS1）：数据来自 analysis API 的 buy1_events/sell1_events。
 *
 * 一买一卖如何画到 K 线图上（流程）：
 * 1. 数据：fetchBs1Points() 调用 analysisApi.analyze，只取 buy1_events/sell1_events → (time, price, dt)
 * 2. 对齐：用当前图表的 bars 按「日历日」对齐事件与 K 线，避免错位一天；缺失 price 用 bar.low(买)/bar.high(卖) 补全
 * 3. 图形：一买用 buildBuyShapesFromPoints(买点数组, opts, context)，一卖用 buildSellShapesFromPoints(卖点数组, opts, context)，给数据即自动绘制
 * 4. 样式：买卖基类默认 lineGapPercent=4，仅竖线、虚线、浅灰引线；同天多点自动错位。后续若重叠可传 context.lineGapPercentPerIndex 拉长连接线避免交叉
 * 5. 绘制：drawChartShapes(chart, shapes) 得到 entity id，关闭时 clearBs1Overlay(chart, entityIds) 清除
 */
import { analysisApi } from '../api/analysis';
import type { ChartPoint, ChartShape } from './chartShapes';
import { drawChartShapes, clearChartShapes } from './chartShapes';
import { buildBuyShapesFromPoints, buildSellShapesFromPoints } from './bullBearShapes';

/** Bar 最小形状（用于 drawBs1Overlay 的 fetchBars 返回类型） */
export interface BarLike {
  time: number;
  low: number;
  high: number;
}

/** TV interval 到麒麟分析 freq 的映射 */
const INTERVAL_TO_FREQ: Record<string, string> = {
  '1D': '日线',
  '1W': '周线',
  '1M': '月线',
  '60': '60分钟',
  '30': '30分钟',
  '15': '15分钟',
};

/**
 * 将分析 API 返回的 dt 字符串解析为 Unix 秒。
 * dt 格式：YYYY-MM-DD 或 YYYY-MM-DD HH:mm
 */
function parseDtToUnixSec(dt: string): number {
  const s = String(dt || '').trim();
  if (!s) return 0;
  const normalized = s.length <= 10 ? `${s}T00:00:00` : s.replace(' ', 'T');
  const ms = new Date(normalized).getTime();
  return Number.isFinite(ms) ? Math.floor(ms / 1000) : 0;
}

/**
 * 将 YYYYMMDD 或 YYYY-MM-DD 转为 YYYYMMDD（分析 API 入参格式以 backend 为准，此处统一为 8 位）
 */
function toSdtEdt(unixSec: number): string {
  const d = new Date(unixSec * 1000);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}${m}${day}`;
}

export interface AnalysisBsPoints {
  buy1: ChartPointWithDt[];
  buy2: ChartPointWithDt[];
  buy3: ChartPointWithDt[];
  sell1: ChartPointWithDt[];
  sell2: ChartPointWithDt[];
  sell3: ChartPointWithDt[];
}

/** 带原始 dt 的锚点，便于按日历日匹配 K 线（修复错位一天） */
export interface ChartPointWithDt extends ChartPoint {
  dt: string;
}

/** 仅一买一卖的点位（BS1） */
export interface Bs1Points {
  buy1: ChartPointWithDt[];
  sell1: ChartPointWithDt[];
}

/**
 * 拉取 BS1 一买一卖点位（从 analysis API 的 buy1_events/sell1_events）。
 */
export async function fetchBs1Points(
  symbol: string,
  interval: string,
  fromSec: number,
  toSec: number
): Promise<Bs1Points> {
  const freq = INTERVAL_TO_FREQ[interval] || null;
  if (!freq) return { buy1: [], sell1: [] };
  const sdt = toSdtEdt(fromSec);
  const edt = toSdtEdt(toSec);
  const res = await analysisApi.analyze({ symbol, freq, sdt, edt });
  const toPoint = (e: { dt: string; price?: number }): ChartPointWithDt => ({
    time: parseDtToUnixSec(e.dt),
    price: typeof e.price === 'number' && Number.isFinite(e.price) ? e.price : 0,
    dt: e.dt,
  });
  return {
    buy1: (res.buy1_events ?? []).map(toPoint),
    sell1: (res.sell1_events ?? []).map(toPoint),
  };
}

/**
 * 根据当前图表 symbol、interval 与时间范围拉取麒麟分析买卖点，并转为图表锚点 (time, price)。
 * 若 interval 无法映射到 freq 则返回空数据。price 优先用事件中的 price，缺失时由调用方用 K 线补全。
 */
export async function fetchAnalysisBsPoints(
  symbol: string,
  interval: string,
  fromSec: number,
  toSec: number
): Promise<AnalysisBsPoints> {
  const freq = INTERVAL_TO_FREQ[interval] || null;
  if (!freq) {
    return { buy1: [], buy2: [], buy3: [], sell1: [], sell2: [], sell3: [] };
  }
  const sdt = toSdtEdt(fromSec);
  const edt = toSdtEdt(toSec);
  const res = await analysisApi.analyze({ symbol, freq, sdt, edt });

  const toPoint = (e: { dt: string; price?: number }): ChartPointWithDt => ({
    time: parseDtToUnixSec(e.dt),
    price: typeof e.price === 'number' && Number.isFinite(e.price) ? e.price : 0,
    dt: e.dt,
  });

  return {
    buy1: (res.buy1_events ?? []).map(toPoint),
    buy2: (res.buy2_events ?? []).map(toPoint),
    buy3: (res.buy3_events ?? []).map(toPoint),
    sell1: (res.sell1_events ?? []).map(toPoint),
    sell2: (res.sell2_events ?? []).map(toPoint),
    sell3: (res.sell3_events ?? []).map(toPoint),
  };
}

export interface DrawBs1OverlayParams {
  chart: any;
  symbol: string;
  interval: string;
  /** 由调用方提供：从图表取当前可见时间范围，返回 Unix 秒 fromSec/toSec */
  getVisibleRange: () => { fromSec: number; toSec: number };
  /** 由调用方提供：拉取 K 线 bars，用于按日对齐与补全买卖点 price；bar.time 为毫秒 */
  fetchBars: (
    symbol: string,
    resolution: string,
    fromSec: number,
    toSec: number
  ) => Promise<BarLike[]>;
  /** 由调用方提供：TV interval 转 UDF resolution，如 1D→D */
  intervalToResolution: (interval: string) => string;
}

/**
 * 在 K 线图上绘制一买一卖叠加层（BS1）。含：取可见范围、拉取 BS1 数据、拉取 bars、
 * 按日对齐与补全 price、构建 shapes、绘制。返回本次绘制的 entity id 列表。
 */
export async function drawBs1Overlay(params: DrawBs1OverlayParams): Promise<string[]> {
  const { chart, symbol, interval, getVisibleRange, fetchBars, intervalToResolution } = params;
  // ---------- 1. 可见时间范围（Unix 秒） ----------
  let fromSec: number;
  let toSec: number;
  try {
    const range = getVisibleRange();
    fromSec = range.fromSec;
    toSec = range.toSec;
    if (fromSec <= 0 || fromSec >= toSec) {
      toSec = Math.floor(Date.now() / 1000);
      fromSec = toSec - 365 * 86400;
    }
  } catch {
    toSec = Math.floor(Date.now() / 1000);
    fromSec = toSec - 365 * 86400;
  }
  const resolution = intervalToResolution(interval);
  // ---------- 2. 拉取一买一卖点位（analysis API buy1_events/sell1_events） ----------
  const points = await fetchBs1Points(symbol, interval, fromSec, toSec);
  const bars = await fetchBars(symbol, resolution, fromSec, toSec);
  // ---------- 3. 时间→bar、日历日→bar 映射（用于对齐与补价） ----------
  const timeToBar = new Map<number, { low: number; high: number }>();
  bars.forEach((b) => {
    const tSec = Math.floor(b.time / 1000);
    timeToBar.set(tSec, { low: b.low, high: b.high });
  });
  const toLocalYYYYMMDD = (ms: number) => {
    const d = new Date(ms);
    return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
  };
  const dateStrFromDt = (dt: string) => String(dt || '').trim().slice(0, 10).replace(/-/g, '');
  const dateStrToBar = new Map<string, { timeSec: number; low: number; high: number }>();
  bars.forEach((b) => {
    const ymd = toLocalYYYYMMDD(b.time);
    dateStrToBar.set(ymd, { timeSec: Math.floor(b.time / 1000), low: b.low, high: b.high });
  });
  /** 按日历日把事件对齐到对应 K 线：用 bar 的 time 替换 point.time，缺失 price 用 bar.low/bar.high */
  const alignPointToBarByDate = (
    p: { time: number; price: number; dt?: string },
    useLow: boolean
  ) => {
    if (!p.dt) return;
    const bar = dateStrToBar.get(dateStrFromDt(p.dt));
    if (bar) {
      p.time = bar.timeSec;
      if (p.price <= 0) p.price = useLow ? bar.low : bar.high;
    }
  };
  const isDayLevel = resolution === 'D' || resolution === 'W' || resolution === 'M';
  if (isDayLevel) {
    points.buy1.forEach((p) => alignPointToBarByDate(p, true));
    points.sell1.forEach((p) => alignPointToBarByDate(p, false));
  }
  /** 按时间戳补全缺失的 price：买点用 bar.low，卖点用 bar.high */
  const fillPrice = (p: { time: number; price: number }, useLow: boolean) => {
    if (p.price > 0) return;
    const bar =
      timeToBar.get(p.time) || timeToBar.get(p.time - 1) || timeToBar.get(p.time + 1);
    if (bar) p.price = useLow ? bar.low : bar.high;
  };
  points.buy1.forEach((p) => fillPrice(p, true));
  points.sell1.forEach((p) => fillPrice(p, false));

  // ---------- 4. 构建一买一卖 shapes：给数据 bullBearShapes 批量自动绘制（同天错位、时间偏移）；后续可传 lineGapPercentPerIndex 做重叠拉长 ----------
  const barCount = bars.length || 1;
  const barWidthSec = Math.max(1, Math.floor((toSec - fromSec) / barCount));
  const batchContext = { barWidthSec, stackStepPercent: 0.4 };
  const styleOptions = {
    fontSize: 9,
    leaderLineColor: '#b0b0b0',
    verticalOnly: true,
    connectorDashed: true,
  };
  const shapes: ChartShape[] = [];
  shapes.push(
    ...buildBuyShapesFromPoints(points.buy1, { label: '一买', ...styleOptions }, batchContext)
  );
  shapes.push(
    ...buildSellShapesFromPoints(points.sell1, { label: '一卖', ...styleOptions }, batchContext)
  );
  // ---------- 5. 绘制到图表并返回 entity id（供关闭时清除） ----------
  return drawChartShapes(chart, shapes);
}

/**
 * 清除一买一卖叠加层。
 */
export function clearBs1Overlay(chart: any, entityIds: string[]): void {
  clearChartShapes(chart, entityIds);
}
