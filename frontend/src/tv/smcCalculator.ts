/**
 * 前端 SMC 计算（与 czsc/indicators/smart_money.py 对齐）。
 * 输入：K 线 bars（time 为 UTC 毫秒），输出：areas + events 供 smcOverlay 绘制。
 */

import type { SmcArea, SmcEvent } from './smcOverlay';

/** 前端 K 线 Bar（time 毫秒） */
export interface Bar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SmcConfig {
  show_fair_value_gaps?: boolean;
  show_premium_discount_zones?: boolean;
  show_swing_order_blocks?: boolean;
  show_internal_order_blocks?: boolean;
  internal_size?: number;
  swing_size?: number;
  internal_order_blocks_size?: number;
  swing_order_blocks_size?: number;
  order_block_filter?: 'atr' | 'cmr';
  order_block_mitigation?: 'close' | 'highlow';
  show_equal_highs_lows?: boolean;
  equal_highs_lows_length?: number;
  equal_highs_lows_threshold?: number;
  show_high_low_swings?: boolean;
  fair_value_gaps_auto_threshold?: boolean;
  fair_value_gaps_extend?: number;
  style?: 'colored' | 'monochrome';
}

type Bias = 'bull' | 'bear';
type Scope = 'internal' | 'swing' | 'other';
type EventType = 'BOS' | 'CHoCH' | 'EQH' | 'EQL' | 'StrongHigh' | 'WeakHigh' | 'StrongLow' | 'WeakLow';

function timeToDtStr(ms: number): string {
  return new Date(ms).toISOString();
}

function trueRange(bars: Bar[]): number[] {
  const n = bars.length;
  const tr: number[] = [];
  for (let i = 0; i < n; i++) {
    const prevC = i > 0 ? bars[i - 1].close : bars[i].close;
    const a = bars[i].high - bars[i].low;
    const b = Math.abs(bars[i].high - prevC);
    const c = Math.abs(bars[i].low - prevC);
    tr.push(Math.max(a, b, c));
  }
  return tr;
}

function rma(values: number[], period: number): number[] {
  const out: number[] = [];
  if (values.length === 0) return out;
  const alpha = 1 / period;
  out[0] = values[0];
  for (let i = 1; i < values.length; i++) {
    out[i] = alpha * values[i] + (1 - alpha) * out[i - 1];
  }
  return out;
}

function atrWilder(bars: Bar[], period: number = 200): number[] {
  return rma(trueRange(bars), period);
}

function cumulativeMeanRange(bars: Bar[]): number[] {
  const tr = trueRange(bars);
  const out: number[] = [];
  let sum = 0;
  for (let i = 0; i < tr.length; i++) {
    sum += tr[i];
    out.push(sum / (i + 1));
  }
  return out;
}

function detectPivotAt(
  bars: Bar[],
  i: number,
  size: number
): { isPh: boolean; isPl: boolean; p: number } {
  const p = i - size;
  if (p < 0) return { isPh: false, isPl: false, p: -1 };
  let maxH = -Infinity;
  let minL = Infinity;
  for (let k = p + 1; k <= i; k++) {
    if (bars[k].high > maxH) maxH = bars[k].high;
    if (bars[k].low < minL) minL = bars[k].low;
  }
  const isPh = bars[p].high > maxH;
  const isPl = bars[p].low < minL;
  return { isPh, isPl, p };
}

interface Pivot {
  current: number;
  last: number;
  crossed: boolean;
  dt: number | null;
  idx: number;
}

interface OrderBlock {
  top: number;
  bottom: number;
  bias: Bias;
  sdt: number;
  sidx: number;
}

interface FVG {
  top: number;
  bottom: number;
  bias: Bias;
  sdt: number;
  sidx: number;
  edt: number | null;
}

interface Trailing {
  top: number;
  bottom: number;
  anchorDt: number;
  lastTopDt: number;
  lastBottomDt: number;
}

function parsedHilo(bars: Bar[], volMeasure: number[]): { parsedHigh: number[]; parsedLow: number[] } {
  const parsedHigh: number[] = [];
  const parsedLow: number[] = [];
  for (let i = 0; i < bars.length; i++) {
    const rng = bars[i].high - bars[i].low;
    const hv = rng >= 2 * (volMeasure[i] ?? 0);
    parsedHigh.push(hv ? bars[i].low : bars[i].high);
    parsedLow.push(hv ? bars[i].high : bars[i].low);
  }
  return { parsedHigh, parsedLow };
}

function crossOver(a0: number, a1: number, level: number): boolean {
  return a0 <= level && a1 > level;
}
function crossUnder(a0: number, a1: number, level: number): boolean {
  return a0 >= level && a1 < level;
}

function obStyle(
  scope: Scope,
  bias: Bias,
  style: string
): { color: string; border: string } {
  if (style === 'monochrome') {
    return bias === 'bull'
      ? { color: 'rgba(189, 189, 189, 0.18)', border: '#b2b5be' }
      : { color: 'rgba(93, 96, 107, 0.18)', border: '#5d606b' };
  }
  if (scope === 'swing') {
    return bias === 'bull'
      ? { color: 'rgba(24, 72, 204, 0.22)', border: '#1848cc' }
      : { color: 'rgba(178, 40, 51, 0.22)', border: '#b22833' };
  }
  return bias === 'bull'
    ? { color: 'rgba(49, 121, 245, 0.22)', border: '#3179f5' }
    : { color: 'rgba(247, 124, 128, 0.22)', border: '#f77c80' };
}

function fvgStyle(bias: Bias, style: string): { color: string; border: string } {
  if (style === 'monochrome') {
    return bias === 'bull'
      ? { color: 'rgba(189, 189, 189, 0.18)', border: '#b2b5be' }
      : { color: 'rgba(93, 96, 107, 0.18)', border: '#5d606b' };
  }
  return bias === 'bull'
    ? { color: 'rgba(0, 255, 104, 0.20)', border: '#00ff68' }
    : { color: 'rgba(255, 0, 8, 0.20)', border: '#ff0008' };
}

function zoneStyle(kind: string): { color: string; border: string } {
  if (kind === 'premium') return { color: 'rgba(242, 54, 69, 0.10)', border: '#F23645' };
  if (kind === 'discount') return { color: 'rgba(8, 153, 129, 0.10)', border: '#089981' };
  return { color: 'rgba(135, 139, 148, 0.08)', border: '#878b94' };
}

function makeArea(
  sdt: number,
  edt: number,
  top: number,
  bottom: number,
  name: string,
  kind: string,
  color: string,
  border: string
): SmcArea {
  return {
    sdt: timeToDtStr(sdt),
    edt: timeToDtStr(edt),
    top,
    bottom,
    name,
    kind,
    color_rgba: color,
    border_color: border,
  };
}

function appendZoneAreas(
  areas: SmcArea[],
  sdt: number,
  edt: number,
  top: number,
  bottom: number
): void {
  if (!Number.isFinite(top) || !Number.isFinite(bottom) || top <= bottom) return;
  const premiumBottom = 0.95 * top + 0.05 * bottom;
  const discountTop = 0.95 * bottom + 0.05 * top;
  const eq = 0.5 * (top + bottom);
  const eqTop = 0.525 * top + 0.475 * bottom;
  const eqBottom = 0.525 * bottom + 0.475 * top;
  const p = zoneStyle('premium');
  areas.push(makeArea(sdt, edt, top, premiumBottom, 'Premium', 'zone_premium', p.color, p.border));
  const e = zoneStyle('equilibrium');
  areas.push(makeArea(sdt, edt, eqTop, eqBottom, 'Equilibrium', 'zone_eq', e.color, e.border));
  const d = zoneStyle('discount');
  areas.push(makeArea(sdt, edt, discountTop, bottom, 'Discount', 'zone_discount', d.color, d.border));
}

function makeOrderBlockFromPivot(
  pivot: Pivot,
  i: number,
  dts: number[],
  parsedHigh: number[],
  parsedLow: number[],
  bias: Bias
): OrderBlock | null {
  if (pivot.idx < 0 || pivot.idx >= i) return null;
  const s = pivot.idx;
  let idx: number;
  if (bias === 'bear') {
    let max = -Infinity;
    idx = s;
    for (let k = s; k < i; k++) {
      const v = parsedHigh[k];
      if (v > max) {
        max = v;
        idx = k;
      }
    }
  } else {
    let min = Infinity;
    idx = s;
    for (let k = s; k < i; k++) {
      const v = parsedLow[k];
      if (v < min) {
        min = v;
        idx = k;
      }
    }
  }
  const top = parsedHigh[idx];
  const bottom = parsedLow[idx];
  if (!Number.isFinite(top) || !Number.isFinite(bottom) || top <= bottom) return null;
  return { top, bottom, bias, sdt: dts[idx], sidx: idx };
}

function filterActiveObs(
  obs: OrderBlock[],
  bearSrc: number,
  bullSrc: number
): OrderBlock[] {
  return obs.filter((ob) => {
    if (ob.bias === 'bear' && bearSrc > ob.top) return false;
    if (ob.bias === 'bull' && bullSrc < ob.bottom) return false;
    return true;
  });
}

function mergeSmallAreas(areas: SmcArea[]): SmcArea[] {
  if (areas.length === 0) return [];
  const sorted = [...areas].sort(
    (a, b) =>
      (a.kind as string).localeCompare(b.kind) ||
      a.bottom - b.bottom ||
      a.top - b.top ||
      a.sdt.localeCompare(b.sdt)
  );
  const out: SmcArea[] = [];
  let cur = { ...sorted[0] };
  for (let i = 1; i < sorted.length; i++) {
    const a = sorted[i];
    const sameBand =
      a.kind === cur.kind &&
      Math.abs(a.top - cur.top) < 1e-6 &&
      Math.abs(a.bottom - cur.bottom) < 1e-6 &&
      a.sdt <= cur.edt;
    if (sameBand) {
      cur.edt = a.edt > cur.edt ? a.edt : cur.edt;
      continue;
    }
    out.push(cur);
    cur = { ...a };
  }
  out.push(cur);
  return out;
}

/**
 * 前端计算 SMC，与后端 czsc/indicators/smart_money.py 输出格式一致。
 */
export function smartMoneyConcepts(
  bars: Bar[],
  config: SmcConfig = {}
): { areas: SmcArea[]; events: SmcEvent[] } {
  const cfg: Required<SmcConfig> = {
    show_fair_value_gaps: config.show_fair_value_gaps ?? false,
    show_premium_discount_zones: config.show_premium_discount_zones ?? false,
    show_swing_order_blocks: config.show_swing_order_blocks ?? false,
    show_internal_order_blocks: config.show_internal_order_blocks ?? true,
    internal_size: config.internal_size ?? 5,
    swing_size: config.swing_size ?? 50,
    internal_order_blocks_size: config.internal_order_blocks_size ?? 5,
    swing_order_blocks_size: config.swing_order_blocks_size ?? 5,
    order_block_filter: config.order_block_filter ?? 'atr',
    order_block_mitigation: config.order_block_mitigation ?? 'highlow',
    show_equal_highs_lows: config.show_equal_highs_lows ?? true,
    equal_highs_lows_length: config.equal_highs_lows_length ?? 3,
    equal_highs_lows_threshold: config.equal_highs_lows_threshold ?? 0.1,
    show_high_low_swings: config.show_high_low_swings ?? true,
    fair_value_gaps_auto_threshold: config.fair_value_gaps_auto_threshold ?? true,
    fair_value_gaps_extend: config.fair_value_gaps_extend ?? 1,
    style: config.style ?? 'colored',
  };

  const n = bars.length;
  const minLen = Math.max(cfg.swing_size, cfg.internal_size) + 10;
  if (n < minLen) return { areas: [], events: [] };

  const dts = bars.map((b) => b.time);
  const atr200 = atrWilder(bars, 200);
  const cmr = cumulativeMeanRange(bars);
  const volMeasure =
    cfg.order_block_filter === 'atr' ? atr200 : cmr;
  const meanVol = volMeasure.reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0) / n;
  const vm = volMeasure.map((v) => (Number.isFinite(v) ? v : meanVol));
  const { parsedHigh, parsedLow } = parsedHilo(bars, vm);

  const swHigh: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  const swLow: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  const inHigh: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  const inLow: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  const eqHigh: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  const eqLow: Pivot = { current: NaN, last: NaN, crossed: false, dt: null, idx: -1 };
  let swTrend: Bias = 'bear';
  let inTrend: Bias = 'bear';
  const internalObs: OrderBlock[] = [];
  const swingObs: OrderBlock[] = [];
  const fvgs: FVG[] = [];
  let fvgCumAbsDelta = 0;
  const areas: SmcArea[] = [];
  const events: SmcEvent[] = [];
  const trailing: Trailing = {
    top: bars[0].high,
    bottom: bars[0].low,
    anchorDt: dts[0],
    lastTopDt: dts[0],
    lastBottomDt: dts[0],
  };

  function updateStructurePivots(
    i: number,
    size: number,
    pHigh: Pivot,
    pLow: Pivot
  ): { side: string; dt: number; price: number } | null {
    const { isPh, isPl, p } = detectPivotAt(bars, i, size);
    if (p < 0 || (!isPh && !isPl)) return null;
    const dtp = dts[p];
    if (isPl) {
      pLow.last = pLow.current;
      pLow.current = bars[p].low;
      pLow.crossed = false;
      pLow.dt = dtp;
      pLow.idx = p;
      return { side: 'low', dt: dtp, price: pLow.current };
    }
    if (isPh) {
      pHigh.last = pHigh.current;
      pHigh.current = bars[p].high;
      pHigh.crossed = false;
      pHigh.dt = dtp;
      pHigh.idx = p;
      return { side: 'high', dt: dtp, price: pHigh.current };
    }
    return null;
  }

  function tryBreakLevel(
    i: number,
    scope: Scope,
    pivot: Pivot,
    trend: Bias,
    side: 'high' | 'low'
  ): void {
    if (pivot.crossed || !Number.isFinite(pivot.current)) return;
    const prevClose = bars[i - 1].close;
    const curClose = bars[i].close;
    const level = pivot.current;
    const crossed =
      side === 'high' ? crossOver(prevClose, curClose, level) : crossUnder(prevClose, curClose, level);
    if (!crossed) return;
    const bullish = side === 'high';
    const etype: EventType = (trend === 'bear') === bullish ? 'CHoCH' : 'BOS';
    const newTrend: Bias = bullish ? 'bull' : 'bear';
    if (scope === 'swing') swTrend = newTrend;
    else inTrend = newTrend;
    pivot.crossed = true;
    events.push({
      dt: timeToDtStr(dts[i]),
      price: curClose,
      etype,
      bias: newTrend,
      text: `${scope}:${etype}`,
      scope,
    });
    const wantOb = (scope === 'internal' && cfg.show_internal_order_blocks) || (scope === 'swing' && cfg.show_swing_order_blocks);
    if (wantOb) {
      const ob = makeOrderBlockFromPivot(pivot, i, dts, parsedHigh, parsedLow, newTrend);
      if (ob) {
        const target = scope === 'internal' ? internalObs : swingObs;
        target.unshift(ob);
        if (target.length > 100) target.pop();
      }
    }
  }

  for (let i = 1; i < n; i++) {
    const needInternal = cfg.show_internal_order_blocks;
    const needSwing =
      cfg.show_swing_order_blocks ||
      cfg.show_equal_highs_lows ||
      cfg.show_premium_discount_zones ||
      cfg.show_high_low_swings;

    if (needInternal) {
      updateStructurePivots(i, cfg.internal_size, inHigh, inLow);
    }
    if (needSwing) {
      const up = updateStructurePivots(i, cfg.swing_size, swHigh, swLow);
      if (up) {
        trailing.anchorDt = up.dt;
        if (up.side === 'high') {
          trailing.top = up.price;
          trailing.lastTopDt = up.dt;
        } else {
          trailing.bottom = up.price;
          trailing.lastBottomDt = up.dt;
        }
      }
    }

    if (cfg.show_equal_highs_lows) {
      const eqUp = updateStructurePivots(i, cfg.equal_highs_lows_length, eqHigh, eqLow);
      if (eqUp) {
        const thr =
          (Number.isFinite(atr200[i]) ? atr200[i] : 0) * cfg.equal_highs_lows_threshold;
        if (thr > 0) {
          if (eqUp.side === 'high' && Number.isFinite(eqHigh.last) && Math.abs(eqHigh.current - eqHigh.last) < thr) {
            events.push({
              dt: timeToDtStr(eqUp.dt),
              price: eqUp.price,
              etype: 'EQH',
              bias: 'bear',
              text: 'EQH',
              scope: 'other',
            });
          }
          if (eqUp.side === 'low' && Number.isFinite(eqLow.last) && Math.abs(eqLow.current - eqLow.last) < thr) {
            events.push({
              dt: timeToDtStr(eqUp.dt),
              price: eqUp.price,
              etype: 'EQL',
              bias: 'bull',
              text: 'EQL',
              scope: 'other',
            });
          }
        }
      }
    }

    if (cfg.show_high_low_swings || cfg.show_premium_discount_zones) {
      const h = bars[i].high;
      const l = bars[i].low;
      if (h >= trailing.top) {
        trailing.top = h;
        trailing.lastTopDt = dts[i];
      }
      if (l <= trailing.bottom) {
        trailing.bottom = l;
        trailing.lastBottomDt = dts[i];
      }
    }

    tryBreakLevel(i, 'internal', inHigh, inTrend, 'high');
    tryBreakLevel(i, 'internal', inLow, inTrend, 'low');
    tryBreakLevel(i, 'swing', swHigh, swTrend, 'high');
    tryBreakLevel(i, 'swing', swLow, swTrend, 'low');

    const bearSrc = cfg.order_block_mitigation === 'close' ? bars[i].close : bars[i].high;
    const bullSrc = cfg.order_block_mitigation === 'close' ? bars[i].close : bars[i].low;
    const filteredInternal = filterActiveObs(internalObs, bearSrc, bullSrc);
    internalObs.length = 0;
    filteredInternal.forEach((o) => internalObs.push(o));
    const filteredSwing = filterActiveObs(swingObs, bearSrc, bullSrc);
    swingObs.length = 0;
    filteredSwing.forEach((o) => swingObs.push(o));

    if (cfg.show_fair_value_gaps && i >= 2) {
      for (let g = fvgs.length - 1; g >= 0; g--) {
        const curLow = bars[i].low;
        const curHigh = bars[i].high;
        if ((fvgs[g].bias === 'bull' && curLow < fvgs[g].bottom) || (fvgs[g].bias === 'bear' && curHigh > fvgs[g].top)) {
          fvgs.splice(g, 1);
        }
      }
      const lastClose = bars[i - 1].close;
      const lastOpen = bars[i - 1].open;
      const last2High = bars[i - 2].high;
      const last2Low = bars[i - 2].low;
      const curHigh = bars[i].high;
      const curLow = bars[i].low;
      const barDeltaPercent = lastOpen !== 0 ? (lastClose - lastOpen) / (lastOpen * 100) : 0;
      fvgCumAbsDelta += Math.abs(barDeltaPercent);
      const threshold = cfg.fair_value_gaps_auto_threshold ? (fvgCumAbsDelta / i) * 2 : 0;
      const extend = Math.max(cfg.fair_value_gaps_extend, 0);
      const endI = Math.min(i + extend, n - 1);
      if (curLow > last2High && lastClose > last2High && barDeltaPercent > threshold) {
        fvgs.unshift({
          top: curLow,
          bottom: last2High,
          bias: 'bull',
          sdt: dts[i - 1],
          sidx: i - 1,
          edt: dts[endI],
        });
      }
      if (curHigh < last2Low && lastClose < last2Low && -barDeltaPercent > threshold) {
        fvgs.unshift({
          top: last2Low,
          bottom: curHigh,
          bias: 'bear',
          sdt: dts[i - 1],
          sidx: i - 1,
          edt: dts[endI],
        });
      }
      if (fvgs.length > 200) fvgs.splice(200);
    }
  }

  const lastDt = dts[n - 1];
  if (cfg.show_internal_order_blocks && internalObs.length > 0) {
    const list = internalObs.slice(0, cfg.internal_order_blocks_size);
    for (const ob of list) {
      const { color, border } = obStyle('internal', ob.bias, cfg.style);
      areas.push(
        makeArea(ob.sdt, lastDt, ob.top, ob.bottom, 'OrderBlock', `ob_internal_${ob.bias}`, color, border)
      );
    }
  }
  if (cfg.show_swing_order_blocks && swingObs.length > 0) {
    const list = swingObs.slice(0, cfg.swing_order_blocks_size);
    for (const ob of list) {
      const { color, border } = obStyle('swing', ob.bias, cfg.style);
      areas.push(
        makeArea(ob.sdt, lastDt, ob.top, ob.bottom, 'OrderBlock', `ob_swing_${ob.bias}`, color, border)
      );
    }
  }
  if (cfg.show_fair_value_gaps && fvgs.length > 0) {
    for (const g of fvgs) {
      const { color, border } = fvgStyle(g.bias, cfg.style);
      areas.push(
        makeArea(g.sdt, g.edt ?? g.sdt, g.top, g.bottom, 'FVG', `fvg_${g.bias}`, color, border)
      );
    }
  }
  if (cfg.show_premium_discount_zones) {
    appendZoneAreas(areas, trailing.anchorDt, lastDt, trailing.top, trailing.bottom);
  }
  if (cfg.show_high_low_swings) {
    const etHi: EventType = swTrend === 'bear' ? 'StrongHigh' : 'WeakHigh';
    const etLo: EventType = swTrend === 'bull' ? 'StrongLow' : 'WeakLow';
    events.push({
      dt: timeToDtStr(lastDt),
      price: trailing.top,
      etype: etHi,
      bias: 'bear',
      text: etHi,
      scope: 'swing',
    });
    events.push({
      dt: timeToDtStr(lastDt),
      price: trailing.bottom,
      etype: etLo,
      bias: 'bull',
      text: etLo,
      scope: 'swing',
    });
  }

  return {
    areas: mergeSmallAreas(areas),
    events,
  };
}
