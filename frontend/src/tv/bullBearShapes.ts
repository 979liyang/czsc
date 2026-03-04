/**
 * 买卖点基类：买点（锚点 K 线 low、连接线向下、文案在连接线下方），卖点（锚点 K 线 high、连接线向上、文案在连接线上方）。
 * 一买一卖、二买二卖等信号均可复用本基类，通过 text 与 options 区分样式。
 */
import type { ChartPoint, ChartShape } from './chartShapes';

/** 默认水平射线长度（与 chartShapes 一致，约 5 根日 K） */
const DEFAULT_RAY_LENGTH_SEC = 5 * 86400;

/**
 * 买卖点形状统一入参，买/卖共用，其他信号可只传需要覆盖的字段。
 * 默认连接线长度 4%（lineGapPercent: 4）。
 */
export interface BuySellShapeOptions {
  /** 连接线长度（相对锚点价格的百分比），默认 4 */
  lineGapPercent?: number;
  /** 文案颜色 */
  textColor?: string;
  /** 连接线颜色 */
  lineColor?: string;
  /** 文案相对连接线的距离（价格比例 %）；卖点竖线模式下表示连接线与文案底部的间距，并会再加上约一行字高（按 fontSize 折算） */
  textOffsetPercent?: number;
  /** 射线长度（秒），非竖线模式用 */
  lengthSeconds?: number;
  /** 文案字号 */
  fontSize?: number;
  /** 时间轴向右偏移（秒），密集时错开用 */
  timeOffsetSeconds?: number;
  /** 是否绘制指向 K 线实体的浅灰引线，默认 true */
  addLeaderLine?: boolean;
  /** 引线颜色，默认浅灰 */
  leaderLineColor?: string;
  /** 仅竖向连接线（无横向射线），默认 false */
  verticalOnly?: boolean;
  /** 连接线为虚线，默认 false */
  connectorDashed?: boolean;
}

/** 买点默认样式：红、连接线 4% */
const DEFAULT_BUY_OPTIONS: Required<Omit<BuySellShapeOptions, 'lengthSeconds'>> & {
  lengthSeconds?: number;
} = {
  lineGapPercent: 4,
  textColor: '#CC2F3C',
  lineColor: '#CC2F3C',
  textOffsetPercent: 0.2,
  lengthSeconds: DEFAULT_RAY_LENGTH_SEC,
  fontSize: 12,
  timeOffsetSeconds: 0,
  addLeaderLine: true,
  leaderLineColor: '#b0b0b0',
  verticalOnly: false,
  connectorDashed: false,
};

/** 卖点默认样式：绿、连接线 4%，卖点文案在连接线上方 */
const DEFAULT_SELL_OPTIONS: Required<Omit<BuySellShapeOptions, 'lengthSeconds'>> & {
  lengthSeconds?: number;
} = {
  lineGapPercent: 4,
  textColor: '#089981',
  lineColor: '#089981',
  textOffsetPercent: 0.2,
  lengthSeconds: DEFAULT_RAY_LENGTH_SEC,
  fontSize: 12,
  timeOffsetSeconds: 0,
  addLeaderLine: true,
  leaderLineColor: '#b0b0b0',
  verticalOnly: false,
  connectorDashed: false,
};

/** 连接线与 K 线之间的价格间隙比例，0.008 = 0.8%，避免贴线与重叠 */
const CONNECTOR_KLINE_GAP_PERCENT = 0.008;

/** 卖点竖线模式：将字号折算为价格比例（约一行字高），用于文案在连接线上方时的总偏移 = textOffsetPercent + 字高 */
const FONT_HEIGHT_PERCENT_PER_PX = 0.2;

/**
 * 买点基类：锚点为最低价；连接线在最低价下方 lineGapPercent%；文案在连接线下方。
 * 其他信号调用时传入 text（如「一买」「二买」）和可选 options 覆盖默认即可。
 */
export function buildBuyShapes(
  anchor: ChartPoint,
  text: string,
  options?: BuySellShapeOptions
): ChartShape[] {
  const opt = { ...DEFAULT_BUY_OPTIONS, ...options };
  const t = anchor.time + (opt.timeOffsetSeconds ?? 0);
  const pct = (opt.lineGapPercent ?? 4) / 100;
  const textPct = (opt.textOffsetPercent ?? 0.2) / 100;
  const linePrice = anchor.price * (1 - pct);
  const len = opt.lengthSeconds ?? DEFAULT_RAY_LENGTH_SEC;
  const endTime = t + len;
  const gapPrice = anchor.price * CONNECTOR_KLINE_GAP_PERCENT;
  const connectorStartPrice = anchor.price - gapPrice;

  const out: ChartShape[] = [];

  if (opt.verticalOnly) {
    const lineColor = opt.leaderLineColor ?? opt.lineColor;
    out.push({
      kind: 'line',
      p1: { time: t, price: anchor.price },
      p2: { time: t, price: linePrice },
      style: { color: lineColor, width: 1, dashed: opt.connectorDashed ?? false },
    });
    out.push({
      kind: 'text',
      point: { time: t, price: linePrice },
      text,
      style: {
        color: opt.textColor,
        fontSize: opt.fontSize,
        hAlign: 'center',
        vAlign: 'middle',
      },
    });
    return out;
  }

  if (opt.addLeaderLine !== false) {
    const leaderColor = opt.leaderLineColor ?? '#b0b0b0';
    out.push({
      kind: 'line',
      p1: { time: t, price: linePrice },
      p2: { time: anchor.time, price: anchor.price },
      style: { color: leaderColor, width: 1 },
    });
  }

  out.push({
    kind: 'line',
    p1: { time: t, price: connectorStartPrice },
    p2: { time: t, price: linePrice },
    style: { color: opt.lineColor, width: 1 },
  });

  out.push({
    kind: 'horizontal_ray',
    start: { time: t, price: linePrice },
    end: { time: endTime, price: linePrice },
    lengthSeconds: len,
    style: { color: opt.lineColor, width: 1 },
    label: {
      text,
      align: 'middle',
      vertical: 'below',
      offsetPercent: textPct,
      color: opt.textColor,
      fontSize: opt.fontSize,
      hAlign: 'center',
      vAlign: 'middle',
    },
  });

  return out;
}

/**
 * 卖点基类：锚点为最高价；连接线在最高价上方 lineGapPercent%；文案在连接线上方（竖线模式下避免连接线穿过文字）。
 * 其他信号调用时传入 text（如「一卖」「二卖」）和可选 options 覆盖默认即可。
 */
export function buildSellShapes(
  anchor: ChartPoint,
  text: string,
  options?: BuySellShapeOptions
): ChartShape[] {
  const opt = { ...DEFAULT_SELL_OPTIONS, ...options };
  const t = anchor.time + (opt.timeOffsetSeconds ?? 0);
  const pct = (opt.lineGapPercent ?? 4) / 100;
  const textPct = (opt.textOffsetPercent ?? 0.2) / 100;
  const linePrice = anchor.price * (1 + pct);
  const len = opt.lengthSeconds ?? DEFAULT_RAY_LENGTH_SEC;
  const endTime = t + len;
  const gapPrice = anchor.price * CONNECTOR_KLINE_GAP_PERCENT;
  const connectorStartPrice = anchor.price + gapPrice;

  const out: ChartShape[] = [];

  if (opt.verticalOnly) {
    const lineColor = opt.leaderLineColor ?? opt.lineColor;
    out.push({
      kind: 'line',
      p1: { time: t, price: anchor.price },
      p2: { time: t, price: linePrice },
      style: { color: lineColor, width: 1, dashed: opt.connectorDashed ?? false },
    });
    // 卖点文案放在连接线上方：偏移 = textOffsetPercent（间距）+ 字体高度（按 fontSize 折算），文案底部对齐该点
    const gapOffset = anchor.price * (opt.textOffsetPercent ?? 0.2) / 100;
    const fontHeightOffset = anchor.price * ((opt.fontSize ?? 12) * FONT_HEIGHT_PERCENT_PER_PX) / 100;
    const textOffset = gapOffset + fontHeightOffset;
    const textPrice = linePrice + textOffset;
    out.push({
      kind: 'text',
      point: { time: t, price: textPrice },
      text,
      style: {
        color: opt.textColor,
        fontSize: opt.fontSize,
        hAlign: 'center',
        vAlign: 'bottom',
      },
    });
    return out;
  }

  if (opt.addLeaderLine !== false) {
    const leaderColor = opt.leaderLineColor ?? '#b0b0b0';
    out.push({
      kind: 'line',
      p1: { time: t, price: linePrice },
      p2: { time: anchor.time, price: anchor.price },
      style: { color: leaderColor, width: 1 },
    });
  }

  out.push({
    kind: 'line',
    p1: { time: t, price: connectorStartPrice },
    p2: { time: t, price: linePrice },
    style: { color: opt.lineColor, width: 1 },
  });

  out.push({
    kind: 'horizontal_ray',
    start: { time: t, price: linePrice },
    end: { time: endTime, price: linePrice },
    lengthSeconds: len,
    style: { color: opt.lineColor, width: 1 },
    label: {
      text,
      align: 'middle',
      vertical: 'above',
      offsetPercent: textPct,
      color: opt.textColor,
      fontSize: opt.fontSize,
      hAlign: 'center',
      vAlign: 'middle',
    },
  });

  return out;
}

/** @deprecated 请使用 buildBuyShapes，入参一致 */
export const buildBullishShapes = buildBuyShapes;

/** @deprecated 请使用 buildSellShapes，入参一致 */
export const buildBearishShapes = buildSellShapes;

/**
 * 批量绘制时的可选上下文。传入后由基类按「同天多点」自动错位；
 * 后续若做重叠判断，可传入 lineGapPercentPerIndex 拉长重叠点的连接线避免交叉。
 */
export interface BuySellBatchContext {
  /** 单根 K 在时间轴上的跨度（秒），用于同天多点时 timeOffsetSeconds = idx * barWidthSec * 0.4 */
  barWidthSec?: number;
  /** 同一天内多点垂直错位步长（%），默认 0.4 */
  stackStepPercent?: number;
  /** 可选：每个锚点单独指定连接线长度（%），若提供则覆盖默认的 base + idx*stackStepPercent，用于重叠时拉长避免交叉 */
  lineGapPercentPerIndex?: number[];
}

/**
 * 根据锚点数组批量绘制买点：同一天内自动垂直错位与时间偏移，返回合并后的 shapes。
 * 直接传入数据即可自动绘制；后续若需重叠判断，可先计算 lineGapPercentPerIndex 再传入 context。
 */
export function buildBuyShapesFromPoints(
  anchors: ChartPoint[],
  options: BuySellShapeOptions & { label?: string },
  context?: BuySellBatchContext
): ChartShape[] {
  const sorted = [...anchors].filter((a) => a.price > 0).sort((a, b) => a.time - b.time);
  const barWidthSec = context?.barWidthSec ?? 60;
  const stackStep = context?.stackStepPercent ?? 0.4;
  const baseGap = options.lineGapPercent ?? 4;
  const dayToIndex = new Map<number, number>();
  const label = options.label ?? '买';
  const shapes: ChartShape[] = [];
  sorted.forEach((anchor, i) => {
    const day = Math.floor(anchor.time / 86400);
    const idx = dayToIndex.get(day) ?? 0;
    dayToIndex.set(day, idx + 1);
    const lineGapPercent = context?.lineGapPercentPerIndex?.[i] ?? baseGap + idx * stackStep;
    const timeOffsetSeconds = idx * barWidthSec * 0.4;
    shapes.push(
      ...buildBuyShapes(anchor, label, {
        ...options,
        lineGapPercent,
        timeOffsetSeconds,
      })
    );
  });
  return shapes;
}

/**
 * 根据锚点数组批量绘制卖点：同一天内自动垂直错位与时间偏移，返回合并后的 shapes。
 * 直接传入数据即可自动绘制；后续若需重叠判断，可先计算 lineGapPercentPerIndex 再传入 context。
 */
export function buildSellShapesFromPoints(
  anchors: ChartPoint[],
  options: BuySellShapeOptions & { label?: string },
  context?: BuySellBatchContext
): ChartShape[] {
  const sorted = [...anchors].filter((a) => a.price > 0).sort((a, b) => a.time - b.time);
  const barWidthSec = context?.barWidthSec ?? 60;
  const stackStep = context?.stackStepPercent ?? 0.4;
  const baseGap = options.lineGapPercent ?? 4;
  const dayToIndex = new Map<number, number>();
  const label = options.label ?? '卖';
  const shapes: ChartShape[] = [];
  sorted.forEach((anchor, i) => {
    const day = Math.floor(anchor.time / 86400);
    const idx = dayToIndex.get(day) ?? 0;
    dayToIndex.set(day, idx + 1);
    const lineGapPercent = context?.lineGapPercentPerIndex?.[i] ?? baseGap + idx * stackStep;
    const timeOffsetSeconds = idx * barWidthSec * 0.4;
    shapes.push(
      ...buildSellShapes(anchor, label, {
        ...options,
        lineGapPercent,
        timeOffsetSeconds,
      })
    );
  });
  return shapes;
}

/** 兼容旧类型名，指向统一入参 */
export type BullishOptions = BuySellShapeOptions;
export type BearishOptions = BuySellShapeOptions;

/** 前端表单可编辑的买卖点配置（用于保存 JSON） */
export interface BullBearFormConfig {
  type: 'bullish' | 'bearish';
  text: string;
  lineGapPercent: number;
  textColor: string;
  lineColor: string;
  textPosition: 'above' | 'below';
  fontSize?: number;
}
