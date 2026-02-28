/**
 * 麒麟叠加：分型（三角形）、笔（线段）、中枢（矩形+可选文案）、买卖点（线+文字）
 *
 * 图形按类型抽象为可配置、可扩展的 CzscOverlayConfig；实际绘制走通用 chartShapes 层。
 */

import type { CzscFullResult } from './czscBsCalculator';
import type { ChartShape, ChartPoint } from './chartShapes';
import { drawChartShapes, clearChartShapes } from './chartShapes';

export type { CzscBsEvent } from './czscBsCalculator';

/** 买卖点事件（含 ZSLX 类二买/类二卖） */
export interface CzscBsEventLike {
  dt: string;
  price: number;
  type: string;
}

// ============= 可扩展图形配置（按形状分块） =============

/** 分型-三角形：顶分型 ▼ 尖朝下，底分型 ▲ 尖朝上，与 K 线有距离 */
export interface CzscShapeFxTriangle {
  /** 三角形大小（价格比例，如 0.006） */
  sizePercent?: number;
  /** 三角形中心离 K 线价格的距离比例（如 0.01 = 1%） */
  distancePercent?: number;
  /** 时间半宽（秒），左右两脚的时间跨度 */
  timeHalfSec?: number;
  /** 顶分型颜色 */
  topColor?: string;
  /** 底分型颜色 */
  bottomColor?: string;
  /** 三角形边线宽 */
  lineWidth?: number;
}

/** 中枢-矩形（可带提示文案） */
export interface CzscShapeZsRect {
  /** 背景填充色（支持 rgba） */
  fillColor?: string;
  /** 边框颜色 */
  borderColor?: string;
  /** 边框线宽 */
  borderWidth?: number;
  /** 填充透明度 0–100 */
  transparency?: number;
  /** 中枢提示文案（不设则不画文案） */
  label?: {
    /** 位置：相对矩形 */
    position?: 'top' | 'bottom' | 'inside' | 'left' | 'right';
    /** 文案颜色 */
    color?: string;
    /** 字号 */
    fontSize?: number;
    /** 文案内容，如 "中枢"；空则用默认 */
    text?: string;
  };
}

/** 笔-线段 */
export interface CzscShapeBiLine {
  color?: string;
  lineWidth?: number;
}

/** 买卖点-线+文字 */
export interface CzscShapeBsMarker {
  /** 指示线线宽 */
  lineWidth?: number;
  /** 线末端/文字相对 K 线的价格偏移比例 */
  lineOffsetPercent?: number;
  /** 买点颜色（线+文字） */
  buyColor?: string;
  /** 卖点颜色（线+文字） */
  sellColor?: string;
  /** 文字字号 */
  textFontSize?: number;
  /** 文字相对 K 线的距离比例（不设则用 lineOffsetPercent） */
  textOffsetPercent?: number;
}

/** 麒麟叠加整体配置：按图形类型分块，可扩展（如后续增加 circle?: CzscShapeCircle） */
export interface CzscOverlayConfig {
  fxTriangle?: CzscShapeFxTriangle;
  zsRect?: CzscShapeZsRect;
  biLine?: CzscShapeBiLine;
  bsMarker?: CzscShapeBsMarker;
}

/** 兼容旧命名 */
export type CzscBsOverlayStyle = CzscOverlayConfig;

// ---------- 各图形默认值 ----------

const DEFAULT_FX_TRIANGLE: Required<CzscShapeFxTriangle> = {
  sizePercent: 0.006,
  distancePercent: 0.01,
  timeHalfSec: 43200,
  topColor: '#ff9800',
  bottomColor: '#00acc1',
  lineWidth: 1,
};

const DEFAULT_ZS_RECT: Required<Omit<CzscShapeZsRect, 'label'>> & {
  label?: CzscShapeZsRect['label'];
} = {
  fillColor: 'rgba(123, 31, 162, 0.15)',
  borderColor: '#7b1fa2',
  borderWidth: 1,
  transparency: 80,
};

const DEFAULT_BI_LINE: Required<CzscShapeBiLine> = {
  color: '#78909c',
  lineWidth: 1,
};

const DEFAULT_BS_MARKER: Required<CzscShapeBsMarker> = {
  lineWidth: 1.5,
  lineOffsetPercent: 0.018,
  buyColor: '#e53935',
  sellColor: '#43a047',
  textFontSize: 11,
  textOffsetPercent: 0.018,
};

function mergeFxTriangle(partial?: CzscShapeFxTriangle): Required<CzscShapeFxTriangle> {
  if (!partial) return { ...DEFAULT_FX_TRIANGLE };
  return {
    sizePercent: partial.sizePercent ?? DEFAULT_FX_TRIANGLE.sizePercent,
    distancePercent: partial.distancePercent ?? DEFAULT_FX_TRIANGLE.distancePercent,
    timeHalfSec: partial.timeHalfSec ?? DEFAULT_FX_TRIANGLE.timeHalfSec,
    topColor: partial.topColor ?? DEFAULT_FX_TRIANGLE.topColor,
    bottomColor: partial.bottomColor ?? DEFAULT_FX_TRIANGLE.bottomColor,
    lineWidth: partial.lineWidth ?? DEFAULT_FX_TRIANGLE.lineWidth,
  };
}

function mergeZsRect(partial?: CzscShapeZsRect) {
  const fill = partial?.fillColor ?? DEFAULT_ZS_RECT.fillColor;
  const border = partial?.borderColor ?? DEFAULT_ZS_RECT.borderColor;
  const width = partial?.borderWidth ?? DEFAULT_ZS_RECT.borderWidth;
  const trans = partial?.transparency ?? DEFAULT_ZS_RECT.transparency;
  const label = partial?.label;
  return { fillColor: fill, borderColor: border, borderWidth: width, transparency: trans, label };
}

function mergeBiLine(partial?: CzscShapeBiLine): Required<CzscShapeBiLine> {
  if (!partial) return { ...DEFAULT_BI_LINE };
  return {
    color: partial.color ?? DEFAULT_BI_LINE.color,
    lineWidth: partial.lineWidth ?? DEFAULT_BI_LINE.lineWidth,
  };
}

function mergeBsMarker(partial?: CzscShapeBsMarker): Required<CzscShapeBsMarker> {
  if (!partial) return { ...DEFAULT_BS_MARKER };
  return {
    lineWidth: partial.lineWidth ?? DEFAULT_BS_MARKER.lineWidth,
    lineOffsetPercent: partial.lineOffsetPercent ?? DEFAULT_BS_MARKER.lineOffsetPercent,
    buyColor: partial.buyColor ?? DEFAULT_BS_MARKER.buyColor,
    sellColor: partial.sellColor ?? DEFAULT_BS_MARKER.sellColor,
    textFontSize: partial.textFontSize ?? DEFAULT_BS_MARKER.textFontSize,
    textOffsetPercent: partial.textOffsetPercent ?? partial.lineOffsetPercent ?? DEFAULT_BS_MARKER.textOffsetPercent,
  };
}

/** Payload：数据 + 可选配置 */
export interface CzscBsPayload {
  events: CzscBsEventLike[];
  count?: number;
  fxs?: CzscFullResult['fxs'];
  bis?: CzscFullResult['bis'];
  zsList?: CzscFullResult['zsList'];
  /** 可选：按图形类型覆盖，未传则用默认 */
  style?: CzscOverlayConfig;
}

function toUnixSeconds(dt: string): number {
  return Math.floor(new Date(dt).getTime() / 1000);
}

export class CzscBsOverlayManager {
  private entityIds: string[] = [];

  clear(widget: any): void {
    try {
      const chart = widget?.activeChart?.();
      if (chart) clearChartShapes(chart, this.entityIds);
    } finally {
      this.entityIds = [];
    }
  }

  async draw(widget: any, payload: CzscBsPayload): Promise<void> {
    const chart = widget?.activeChart?.();
    if (!chart) return;

    const fxTri = mergeFxTriangle(payload.style?.fxTriangle);
    const zsRect = mergeZsRect(payload.style?.zsRect);
    const biLine = mergeBiLine(payload.style?.biLine);
    const bsMarker = mergeBsMarker(payload.style?.bsMarker);
    const t = (dt: string) => toUnixSeconds(dt);
    const shapes: ChartShape[] = [];

    // 1. 中枢（矩形 + 可选文案）
    if (payload.zsList?.length) {
      for (const z of payload.zsList) {
        const tStart = t(z.startDt);
        const tEnd = t(z.endDt);
        const midTime = Math.floor((tStart + tEnd) / 2);
        const low = z.low;
        const high = z.high;
        const midPrice = (low + high) / 2;
        shapes.push({
          kind: 'rectangle',
          p1: { time: tStart, price: low },
          p2: { time: tEnd, price: high },
          style: {
            fillColor: zsRect.fillColor,
            borderColor: zsRect.borderColor,
            borderWidth: zsRect.borderWidth,
            transparency: zsRect.transparency,
          },
        });
        if (zsRect.label) {
          const pos = zsRect.label.position ?? 'top';
          const labelColor = zsRect.label.color ?? zsRect.borderColor;
          const fontSize = zsRect.label.fontSize ?? 11;
          const text = zsRect.label.text ?? '中枢';
          let price = midPrice;
          if (pos === 'top') price = high;
          else if (pos === 'bottom') price = low;
          shapes.push({
            kind: 'text',
            point: { time: midTime, price },
            text,
            style: { color: labelColor, fontSize, bold: false },
          });
        }
      }
    }

    // 2. 笔（线段）
    if (payload.bis?.length) {
      for (const bi of payload.bis) {
        shapes.push({
          kind: 'line',
          p1: { time: t(bi.startDt), price: bi.startPrice },
          p2: { time: t(bi.endDt), price: bi.endPrice },
          style: { color: biLine.color, width: biLine.lineWidth },
        });
      }
    }

    // 3. 分型（三角形：顶 ▼ 底 ▲，折线三点）
    if (payload.fxs?.length) {
      const halfSec = fxTri.timeHalfSec;
      const dist = fxTri.distancePercent;
      const size = fxTri.sizePercent;
      for (const fx of payload.fxs) {
        const timeSec = t(fx.dt);
        const centerPrice = fx.price;
        const color = fx.mark === 'G' ? fxTri.topColor : fxTri.bottomColor;
        const baseY =
          fx.mark === 'G'
            ? centerPrice + centerPrice * dist
            : centerPrice - centerPrice * dist;
        const tipY =
          fx.mark === 'G'
            ? baseY - centerPrice * size
            : baseY + centerPrice * size;
        shapes.push({
          kind: 'polyline',
          points: [
            { time: timeSec - halfSec, price: baseY },
            { time: timeSec, price: tipY },
            { time: timeSec + halfSec, price: baseY },
          ],
          style: { color, width: fxTri.lineWidth },
        });
      }
    }

    // 4. 买卖点（线 + 文字）
    if (payload.events?.length) {
      for (const e of payload.events) {
        const isBuy =
          e.type === '一买' || e.type === '二买' || e.type === '类二买' || e.type === '三买';
        const price = Number(e.price);
        const time = t(e.dt);
        const barPoint: ChartPoint = { time, price };
        const textOffset = price * bsMarker.textOffsetPercent;
        const textPrice = isBuy ? price + textOffset : price - textOffset;
        const textPoint: ChartPoint = { time, price: textPrice };
        const color = isBuy ? bsMarker.buyColor : bsMarker.sellColor;
        shapes.push({
          kind: 'line',
          p1: barPoint,
          p2: textPoint,
          style: { color, width: bsMarker.lineWidth },
        });
        shapes.push({
          kind: 'text',
          point: textPoint,
          text: e.type,
          style: {
            color,
            fontSize: bsMarker.textFontSize,
            bold: true,
          },
        });
      }
    }

    const ids = await drawChartShapes(chart, shapes);
    this.entityIds.push(...ids);
  }
}
