/**
 * SmartMoney 覆盖绘制（Charting Library Drawings API）。
 *
 * 后端接口：GET /api/v1/indicators/smc
 * 返回：areas/events
 *
 * 使用通用 chartShapes：区域为无边框矩形；BOS/CHoCH 为虚线+文案；其余事件为 K 线高点向右实线+右端文案。
 */

import type { ChartShape } from './chartShapes';
import { drawChartShapes, clearChartShapes } from './chartShapes';

export interface SmcArea {
  sdt: string;
  edt: string;
  top: number;
  bottom: number;
  name: string;
  kind: string;
  color_rgba: string;
  border_color: string;
}

export interface SmcEvent {
  dt: string;
  price: number;
  etype: string;
  bias: string;
  text: string;
  scope?: string;
}

export interface SmcPayload {
  areas: SmcArea[];
  events: SmcEvent[];
}

function toUnixSeconds(dt: string): number {
  return Math.floor(new Date(dt).getTime() / 1000);
}

/** BOS/CHoCH 虚线向右延伸的秒数（约 1 根日 K） */
const DASHED_LINE_LENGTH_SEC = 86400;
/** 事件文案默认字号 */
const EVENT_FONT_SIZE = 11;
/** 事件线/文案颜色：与 bias 简单区分 */
const COLOR_BULL = '#43a047';
const COLOR_BEAR = '#e53935';

export class SmcOverlayManager {
  private entityIds: string[] = [];

  clear(widget: any): void {
    try {
      const chart = widget?.activeChart?.();
      if (chart) clearChartShapes(chart, this.entityIds);
    } finally {
      this.entityIds = [];
    }
  }

  async draw(widget: any, payload: SmcPayload): Promise<void> {
    const chart = widget?.activeChart?.();
    if (!chart) return;

    const shapes: ChartShape[] = [];

    // 区域：无边框矩形（纯色块）
    for (const a of payload.areas || []) {
      shapes.push({
        kind: 'rectangle',
        p1: { time: toUnixSeconds(a.sdt), price: Number(a.bottom) },
        p2: { time: toUnixSeconds(a.edt), price: Number(a.top) },
        style: {
          fillColor: a.color_rgba,
          borderWidth: 0,
          transparency: 85,
        },
      });
    }

    // 事件：BOS/CHoCH 用虚线+文案；其余用 K 线高点向右实线+右端文案
    for (const e of payload.events || []) {
      const time = toUnixSeconds(e.dt);
      const price = Number(e.price);
      const color = e.bias === 'bull' ? COLOR_BULL : COLOR_BEAR;
      const labelText = e.etype;
      const textStyle = { color, fontSize: EVENT_FONT_SIZE, bold: true };

      const isBosOrChoch =
        e.etype.toUpperCase() === 'BOS' || e.etype.toUpperCase() === 'CHOCH';

      if (isBosOrChoch) {
        shapes.push({
          kind: 'line',
          p1: { time, price },
          p2: { time: time + DASHED_LINE_LENGTH_SEC, price },
          style: { color, width: 1.5, dashed: true },
          label: { text: labelText, at: 'end', ...textStyle },
        });
      } else {
        shapes.push({
          kind: 'horizontal_ray',
          start: { time, price },
          direction: 'right',
          style: { color, width: 1 },
          label: { text: labelText, ...textStyle },
        });
      }
    }

    const ids = await drawChartShapes(chart, shapes);
    this.entityIds.push(...ids);
  }
}

