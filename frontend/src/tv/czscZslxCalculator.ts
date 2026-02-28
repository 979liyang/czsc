/**
 * 麒麟 ZSLX 递归版（旗舰版）前端实现
 *
 * 实现原文核心：K 线包含处理、分型、笔（老笔/新笔/分型笔）、笔中枢、买卖点（一二三 + 类二）。
 * 参考：Chanzhongshuochan (CZSC) ZSLX Recursive Version Indicator - Flagship Edition
 */

import type { Bar } from './czscBsCalculator';
import type { CzscFxPoint, CzscBiSegment, CzscZsBox } from './czscBsCalculator';

/** ZSLX 买卖点类型（含类二买/类二卖） */
export type CzscZslxEventType =
  | '一买'
  | '二买'
  | '类二买'
  | '三买'
  | '一卖'
  | '二卖'
  | '类二卖'
  | '三卖';

export interface CzscZslxEvent {
  dt: string;
  price: number;
  type: CzscZslxEventType;
}

export interface CzscZslxConfig {
  /** 每笔最少 K 线数（原文默认 5，可设宽笔/随笔/任意笔） */
  minKlinesPerPen?: number;
  /** 笔类型：old=老笔严格, new=新笔宽松, fractal=分型笔 */
  penType?: 'old' | 'new' | 'fractal';
}

export interface CzscZslxResult {
  fxs: CzscFxPoint[];
  bis: CzscBiSegment[];
  zsList: CzscZsBox[];
  events: CzscZslxEvent[];
}

const DEFAULT_MIN_KLINES_PER_PEN = 5;
const MIN_FX_GAP_FRACTAL_PEN = 1;
const MIN_FX_GAP_STRICT = 2;

function timeToDtStr(ms: number): string {
  return new Date(ms).toISOString();
}

/** 无包含关系 K 线（合并后） */
interface MergeBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  /** 在原始 bars 中的结束索引（含） */
  endIdx: number;
}

/**
 * K 线包含处理：上涨取高高/低高，下跌取低高/低低
 * 与 czsc analyze.remove_include 逻辑一致
 */
function mergeContainment(bars: Bar[]): MergeBar[] {
  if (!bars.length) return [];
  const out: MergeBar[] = [
    {
      time: bars[0].time,
      open: bars[0].open,
      high: bars[0].high,
      low: bars[0].low,
      close: bars[0].close,
      endIdx: 0,
    },
  ];
  for (let i = 1; i < bars.length; i++) {
    const k2 = out[out.length - 1];
    const k3 = bars[i];
    const k1Idx = out.length >= 2 ? out.length - 2 : -1;
    const k1 = k1Idx >= 0 ? out[k1Idx] : out[0];

    const dirUp = k1.high < k2.high;
    const dirDown = k1.high > k2.high;

    const contained =
      (k2.high <= k3.high && k2.low >= k3.low) || (k2.high >= k3.high && k2.low <= k3.low);

    if (contained && (dirUp || dirDown)) {
      if (dirUp) {
        const high = Math.max(k2.high, k3.high);
        const low = Math.max(k2.low, k3.low);
        const dt = k2.high > k3.high ? k2.time : k3.time;
        out[out.length - 1] = {
          time: dt,
          open: out[out.length - 1].open,
          high,
          low,
          close: k3.close,
          endIdx: i,
        };
      } else {
        const high = Math.min(k2.high, k3.high);
        const low = Math.min(k2.low, k3.low);
        const dt = k2.low < k3.low ? k2.time : k3.time;
        out[out.length - 1] = {
          time: dt,
          open: out[out.length - 1].open,
          high,
          low,
          close: k3.close,
          endIdx: i,
        };
      }
    } else {
      out.push({
        time: k3.time,
        open: k3.open,
        high: k3.high,
        low: k3.low,
        close: k3.close,
        endIdx: i,
      });
    }
  }
  return out;
}

type FxMark = 'G' | 'D';

interface Fx {
  idx: number;
  time: number;
  mark: FxMark;
  price: number;
  high: number;
  low: number;
}

/** 在无包含 K 线上识别顶底分型：中间 K 线为极值 */
function findFxs(merged: MergeBar[]): Fx[] {
  const fxs: Fx[] = [];
  for (let i = 1; i < merged.length - 1; i++) {
    const k1 = merged[i - 1];
    const k2 = merged[i];
    const k3 = merged[i + 1];
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

/** 顶底交替分型序列；fractal 笔最小间隔 1，老笔/新笔用 2 或满足 minKlines */
function alternatingFxs(
  fxs: Fx[],
  merged: MergeBar[],
  penType: 'old' | 'new' | 'fractal',
  minKlinesPerPen: number
): Fx[] {
  if (fxs.length <= 1) return fxs;
  const out: Fx[] = [fxs[0]];
  const minGap = penType === 'fractal' ? MIN_FX_GAP_FRACTAL_PEN : MIN_FX_GAP_STRICT;
  for (let i = 1; i < fxs.length; i++) {
    const cur = fxs[i];
    const last = out[out.length - 1];
    if (cur.mark === last.mark) continue;
    const barGap = Math.abs(merged[cur.idx].endIdx - merged[last.idx].endIdx);
    const idxGap = cur.idx - last.idx;
    if (penType === 'fractal') {
      if (idxGap >= minGap) out.push(cur);
    } else {
      if (idxGap >= minGap && barGap >= minKlinesPerPen) out.push(cur);
    }
  }
  return out;
}

/** 老笔：顶底分型间无包含关系且 K 线数 >= minKlinesPerPen */
function canFormBiOld(
  fa: Fx,
  fb: Fx,
  merged: MergeBar[],
  minKlinesPerPen: number
): boolean {
  const barGap = Math.abs(merged[fb.idx].endIdx - merged[fa.idx].endIdx);
  if (barGap < minKlinesPerPen) return false;
  const ha = fa.high;
  const la = fa.low;
  const hb = fb.high;
  const lb = fb.low;
  const include = (ha > hb && la < lb) || (ha < hb && la > lb);
  return !include;
}

/** 新笔：宽松，允许轻微包含或满足最小 K 数即可 */
function canFormBiNew(
  fa: Fx,
  fb: Fx,
  merged: MergeBar[],
  minKlinesPerPen: number
): boolean {
  const barGap = Math.abs(merged[fb.idx].endIdx - merged[fa.idx].endIdx);
  return barGap >= minKlinesPerPen;
}

interface Bi {
  start: Fx;
  end: Fx;
  direction: 'up' | 'down';
  barsCount: number;
}

function buildBis(
  alt: Fx[],
  merged: MergeBar[],
  penType: 'old' | 'new' | 'fractal',
  minKlinesPerPen: number
): Bi[] {
  const bis: Bi[] = [];
  for (let i = 0; i + 1 < alt.length; i++) {
    const a = alt[i];
    const b = alt[i + 1];
    const barsCount = Math.abs(merged[b.idx].endIdx - merged[a.idx].endIdx);
    const idxGap = b.idx - a.idx;
    let ok = false;
    if (penType === 'fractal') {
      ok = barsCount >= 1 && idxGap >= MIN_FX_GAP_FRACTAL_PEN;
    } else if (penType === 'old') {
      ok = canFormBiOld(a, b, merged, minKlinesPerPen);
    } else {
      ok = canFormBiNew(a, b, merged, minKlinesPerPen);
    }
    if (!ok) continue;
    const direction = a.mark === 'D' ? 'up' : 'down';
    bis.push({ start: a, end: b, direction, barsCount });
  }
  return bis;
}

/** 笔中枢：连续 3 笔有重叠，ZG = min(高点)，ZD = max(低点) */
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
 * 一二三买/卖 + 类二买/类二卖
 * - 一买：向下笔结束底分型 + 背驰（当前底未创新低或前笔向下结束）
 * - 二买：一买后第一个不破一买低的底
 * - 类二买：一买后第一次回调低点（可破一买低一次后再抬升）
 * - 三买：二买后不破二买低的底（或突破中枢后回踩）
 */
function classifyZslxEvents(
  alt: Fx[],
  bis: Bi[],
  zsList: CzscZsBox[]
): CzscZslxEvent[] {
  const events: CzscZslxEvent[] = [];
  let lastBuy1: { price: number; idx: number } | null = null;
  let lastBuy2: { price: number; idx: number } | null = null;
  let lastSell1: { price: number; idx: number } | null = null;
  let lastSell2: { price: number; idx: number } | null = null;

  for (let i = 0; i < alt.length; i++) {
    const fx = alt[i];
    const prevBi = i >= 1 ? bis[i - 1] : null;
    const nextBi = i < bis.length ? bis[i] : null;

    if (fx.mark === 'D') {
      const price = fx.low;
      if (prevBi?.direction === 'down' && nextBi?.direction === 'up') {
        const prevDown = i >= 2 ? bis[i - 2] : null;
        const isFirst = !prevDown || prevDown.direction === 'up';
        const noNewLow =
          prevDown?.end.mark === 'D' && prevDown.end.low <= price + price * 0.002;
        if (isFirst || noNewLow || (prevDown && prevDown.end.low >= price * 0.998)) {
          events.push({
            dt: timeToDtStr(fx.time),
            price,
            type: '一买',
          });
          lastBuy1 = { price, idx: fx.idx };
          lastBuy2 = null;
        }
      }
      if (lastBuy1 != null && fx.idx > lastBuy1.idx) {
        if (price >= lastBuy1.price * 0.998) {
          if (lastBuy2 == null) {
            events.push({ dt: timeToDtStr(fx.time), price, type: '二买' });
            lastBuy2 = { price, idx: fx.idx };
          } else if (fx.idx > lastBuy2.idx && price >= lastBuy2.price * 0.998) {
            events.push({ dt: timeToDtStr(fx.time), price, type: '三买' });
          }
        } else if (price <= lastBuy1.price * 1.002 && price >= lastBuy1.price * 0.99) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '类二买' });
        }
      }
    } else {
      const price = fx.high;
      if (prevBi?.direction === 'up' && nextBi?.direction === 'down') {
        const prevUp = i >= 2 ? bis[i - 2] : null;
        const isFirst = !prevUp || prevUp.direction === 'down';
        const noNewHigh =
          prevUp?.end.mark === 'G' && prevUp.end.high >= price - price * 0.002;
        if (isFirst || noNewHigh || (prevUp && prevUp.end.high <= price * 1.002)) {
          events.push({
            dt: timeToDtStr(fx.time),
            price,
            type: '一卖',
          });
          lastSell1 = { price, idx: fx.idx };
          lastSell2 = null;
        }
      }
      if (lastSell1 != null && fx.idx > lastSell1.idx) {
        if (price <= lastSell1.price * 1.002) {
          if (lastSell2 == null) {
            events.push({ dt: timeToDtStr(fx.time), price, type: '二卖' });
            lastSell2 = { price, idx: fx.idx };
          } else if (fx.idx > lastSell2.idx && price <= lastSell2.price * 1.002) {
            events.push({ dt: timeToDtStr(fx.time), price, type: '三卖' });
          }
        } else if (price >= lastSell1.price * 0.998 && price <= lastSell1.price * 1.01) {
          events.push({ dt: timeToDtStr(fx.time), price, type: '类二卖' });
        }
      }
    }
  }

  return events;
}

function toFxPoints(fxs: Fx[]): CzscFxPoint[] {
  return fxs.map((fx) => ({
    dt: timeToDtStr(fx.time),
    price: fx.price,
    mark: fx.mark,
  }));
}

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
 * ZSLX 麒麟完整计算：包含处理 -> 分型 -> 笔（老/新/分型笔）-> 笔中枢 -> 买卖点（含类二）
 */
export function calcCzscZslxFull(
  bars: Bar[],
  config: CzscZslxConfig = {}
): CzscZslxResult {
  const empty: CzscZslxResult = { fxs: [], bis: [], zsList: [], events: [] };
  if (!bars || bars.length < 5) return empty;

  const minKlinesPerPen = config.minKlinesPerPen ?? DEFAULT_MIN_KLINES_PER_PEN;
  const penType = config.penType ?? 'new';

  const merged = mergeContainment(bars);
  if (merged.length < 5) return empty;

  const fxs = findFxs(merged);
  const alt = alternatingFxs(fxs, merged, penType, minKlinesPerPen);
  if (alt.length < 2) return empty;

  const bis = buildBis(alt, merged, penType, minKlinesPerPen);
  const zsList = buildZsList(bis);

  return {
    fxs: toFxPoints(alt),
    bis: toBiSegments(bis),
    zsList,
    events: classifyZslxEvents(alt, bis, zsList),
  };
}
