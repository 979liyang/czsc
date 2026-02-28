/**
 * 前端麒麟计算（简化版）：分型、笔、中枢、买卖点
 * 输入：K 线 bars（time 为 UTC 毫秒），输出供 czscBsOverlay 在 TV 上绘制。
 */

/** 前端 K 线 Bar（time 毫秒） */
export interface Bar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

/** 买卖点事件 */
export interface CzscBsEvent {
  dt: string;
  price: number;
  type: '一买' | '二买' | '三买' | '一卖' | '二卖' | '三卖';
}

/** 分型点（供绘图：顶 G / 底 D） */
export interface CzscFxPoint {
  dt: string;
  price: number;
  mark: 'G' | 'D';
}

/** 笔线段（供绘图：起点 -> 终点） */
export interface CzscBiSegment {
  startDt: string;
  startPrice: number;
  endDt: string;
  endPrice: number;
  direction: 'up' | 'down';
}

/** 中枢区间（供绘图：矩形 [startDt,endDt] x [low, high]） */
export interface CzscZsBox {
  startDt: string;
  endDt: string;
  low: number;
  high: number;
}

/** 完整麒麟结果 */
export interface CzscFullResult {
  fxs: CzscFxPoint[];
  bis: CzscBiSegment[];
  zsList: CzscZsBox[];
  events: CzscBsEvent[];
}

const MIN_BI_BARS = 4;
const MIN_FX_GAP_BARS = 2;

function timeToDtStr(ms: number): string {
  return new Date(ms).toISOString();
}

/** 分型类型 */
type FxMark = 'G' | 'D';

interface Fx {
  idx: number;
  time: number;
  mark: FxMark;
  price: number;
  high: number;
  low: number;
}

/** 在无包含处理的 K 线上找顶底分型（与 czsc analyze.check_fx 一致：中间 K 线为极值） */
function findFxs(bars: Bar[]): Fx[] {
  const fxs: Fx[] = [];
  for (let i = 1; i < bars.length - 1; i++) {
    const k1 = bars[i - 1];
    const k2 = bars[i];
    const k3 = bars[i + 1];
    if (k1.high < k2.high && k2.high > k3.high && k1.low < k2.low && k2.low > k3.low) {
      fxs.push({
        idx: i,
        time: k2.time,
        mark: 'G',
        price: k2.high,
        high: k2.high,
        low: k2.low,
      });
    }
    if (k1.low > k2.low && k2.low < k3.low && k1.high > k2.high && k2.high < k3.high) {
      fxs.push({
        idx: i,
        time: k2.time,
        mark: 'D',
        price: k2.low,
        high: k2.high,
        low: k2.low,
      });
    }
  }
  return fxs;
}

/** 从分型序列中过滤为顶底交替，并满足最小 K 线数间隔 */
function alternatingFxs(fxs: Fx[]): Fx[] {
  if (fxs.length <= 1) return fxs;
  const out: Fx[] = [fxs[0]];
  for (let i = 1; i < fxs.length; i++) {
    const cur = fxs[i];
    const last = out[out.length - 1];
    if (cur.mark === last.mark) continue;
    const gap = cur.idx - last.idx;
    if (gap >= MIN_FX_GAP_BARS) out.push(cur);
  }
  return out;
}

/** 笔：相邻顶-底或底-顶之间的区间 */
interface Bi {
  start: Fx;
  end: Fx;
  direction: 'up' | 'down';
  barsCount: number;
}

function buildBis(fxs: Fx[]): Bi[] {
  const bis: Bi[] = [];
  for (let i = 0; i + 1 < fxs.length; i++) {
    const a = fxs[i];
    const b = fxs[i + 1];
    const barsCount = Math.abs(b.idx - a.idx);
    if (barsCount < MIN_BI_BARS) continue;
    const direction = a.mark === 'D' ? 'up' : 'down';
    bis.push({ start: a, end: b, direction, barsCount });
  }
  return bis;
}

/** 连续 3 笔有价格重叠则形成中枢，ZG = min(三笔高点)，ZD = max(三笔低点) */
function buildZsList(bis: Bi[]): CzscZsBox[] {
  const list: CzscZsBox[] = [];
  for (let i = 0; i + 2 < bis.length; i++) {
    const b0 = bis[i];
    const b1 = bis[i + 1];
    const b2 = bis[i + 2];
    const high0 = Math.max(b0.start.price, b0.end.price);
    const low0 = Math.min(b0.start.price, b0.end.price);
    const high1 = Math.max(b1.start.price, b1.end.price);
    const low1 = Math.min(b1.start.price, b1.end.price);
    const high2 = Math.max(b2.start.price, b2.end.price);
    const low2 = Math.min(b2.start.price, b2.end.price);
    const ZG = Math.min(high0, high1, high2);
    const ZD = Math.max(low0, low1, low2);
    if (ZG <= ZD) continue;
    list.push({
      startDt: timeToDtStr(b0.start.time),
      endDt: timeToDtStr(b2.end.time),
      low: ZD,
      high: ZG,
    });
  }
  return list;
}

/**
 * 根据笔序列与当前分型，判定买卖点类型（简化规则）
 * - 一买：底分型，且为向下笔的终点，且前一笔向下（背驰：当前底未创新低或幅度缩小）
 * - 一卖：顶分型，且为向上笔的终点，且前一笔向上背驰
 * - 二买：一买之后第一个底分型且低点 >= 一买低点
 * - 三买：二买之后第一个底分型且低点 >= 二买低点
 * - 二卖/三卖对称
 */
function classifyEvents(fxs: Fx[], bis: Bi[]): CzscBsEvent[] {
  const events: CzscBsEvent[] = [];
  let lastBuy1: { price: number; idx: number } | null = null;
  let lastBuy2: { price: number; idx: number } | null = null;
  let lastSell1: { price: number; idx: number } | null = null;
  let lastSell2: { price: number; idx: number } | null = null;

  for (let i = 0; i < fxs.length; i++) {
    const fx = fxs[i];
    const prevBi = i >= 1 ? bis[i - 1] : null;
    const nextBi = i < bis.length ? bis[i] : null;

    if (fx.mark === 'D') {
      const price = fx.low;
      if (prevBi?.direction === 'down' && nextBi?.direction === 'up') {
        const prevDownBi = i >= 2 ? bis[i - 2] : null;
        const isFirstDown = !prevDownBi || prevDownBi.direction === 'up';
        const noNewLow =
          !prevDownBi || prevDownBi.end.mark === 'D' && prevDownBi.end.low <= price;
        if (isFirstDown || noNewLow || prevDownBi!.end.low >= price - (price * 0.002)) {
          events.push({
            dt: timeToDtStr(fx.time),
            price,
            type: '一买',
          });
          lastBuy1 = { price, idx: fx.idx };
          lastBuy2 = null;
        }
      }
      if (lastBuy1 != null && fx.idx > lastBuy1.idx && price >= lastBuy1.price * 0.998) {
        if (lastBuy2 == null) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '二买' });
          lastBuy2 = { price, idx: fx.idx };
        } else if (fx.idx > lastBuy2.idx && price >= lastBuy2.price * 0.998) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '三买' });
        }
      }
    } else {
      const price = fx.high;
      if (prevBi?.direction === 'up' && nextBi?.direction === 'down') {
        const prevUpBi = i >= 2 ? bis[i - 2] : null;
        const isFirstUp = !prevUpBi || prevUpBi.direction === 'down';
        const noNewHigh =
          !prevUpBi || (prevUpBi.end.mark === 'G' && prevUpBi.end.high >= price);
        if (isFirstUp || noNewHigh || (prevUpBi && prevUpBi.end.high <= price + price * 0.002)) {
          events.push({
            dt: timeToDtStr(fx.time),
            price,
            type: '一卖',
          });
          lastSell1 = { price, idx: fx.idx };
          lastSell2 = null;
        }
      }
      if (lastSell1 != null && fx.idx > lastSell1.idx && price <= lastSell1.price * 1.002) {
        if (lastSell2 == null) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '二卖' });
          lastSell2 = { price, idx: fx.idx };
        } else if (fx.idx > lastSell2.idx && price <= lastSell2.price * 1.002) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '三卖' });
        }
      }
    }
  }

  return events;
}

/** 分型转为绘图用点（时间用 ISO 字符串） */
function toFxPoints(fxs: Fx[]): CzscFxPoint[] {
  return fxs.map((fx) => ({
    dt: timeToDtStr(fx.time),
    price: fx.price,
    mark: fx.mark,
  }));
}

/** 笔转为绘图用线段 */
function toBiSegments(bis: Bi[]): CzscBiSegment[] {
  return bis.map((bi) => ({
    startDt: timeToDtStr(bi.start.time),
    startPrice: bi.start.price,
    endDt: timeToDtStr(bi.end.time),
    endPrice: bi.end.price,
    direction: bi.direction,
  }));
}

/**
 * 根据 K 线计算麒麟完整结果：分型、笔、中枢、买卖点（前端简化实现）
 */
export function calcCzscFull(bars: Bar[]): CzscFullResult {
  const empty: CzscFullResult = { fxs: [], bis: [], zsList: [], events: [] };
  if (!bars || bars.length < 5) return empty;
  const fxs = findFxs(bars);
  const alt = alternatingFxs(fxs);
  if (alt.length < 2) return empty;
  const bis = buildBis(alt);
  return {
    fxs: toFxPoints(alt),
    bis: toBiSegments(bis),
    zsList: buildZsList(bis),
    events: classifyEvents(alt, bis),
  };
}

/** 仅计算买卖点（兼容旧调用） */
export function calcCzscBs(bars: Bar[]): CzscBsEvent[] {
  return calcCzscFull(bars).events;
}
