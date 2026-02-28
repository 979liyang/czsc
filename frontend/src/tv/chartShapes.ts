/**
 * 通用图表图形层：与 CZSC/SMC 等指标解耦，供叠加层统一绘制。
 *
 * 支持：线段（实线/虚线）、文案、矩形（可无边框）、水平向右/左射线+右端文案、折线等。
 */

/** 图表上的点（时间 Unix 秒，价格） */
export interface ChartPoint {
  time: number;
  price: number;
}

/** 线样式 */
export interface LineStyle {
  color: string;
  width: number;
  /** 是否为虚线；默认 false 为实线 */
  dashed?: boolean;
}

/** 文案样式 */
export interface TextStyle {
  color: string;
  fontSize: number;
  bold?: boolean;
}

/** 文案自身水平对齐（相对锚点） */
export type LabelHAlign = 'left' | 'center' | 'right';
/** 文案自身垂直对齐（相对锚点） */
export type LabelVAlign = 'top' | 'middle' | 'bottom';

/** 线段 + 可选一端文案（如 BOS/CHoCH 的虚线+文字） */
export interface ShapeLine {
  kind: 'line';
  p1: ChartPoint;
  p2: ChartPoint;
  style: LineStyle;
  /** 连接线起点距 K 线图距离（价格百分比），用于锚点→文案连接线；设后会将 p1 沿 p2 方向偏移 anchorPrice * (percent/100) */
  connectorChartGapPercent?: number;
  /** 在起点或终点附加文案 */
  label?: {
    text: string;
    at: 'start' | 'end';
  } & TextStyle;
}

/** 单点文案，style 可包含 TextLineToolOverrides 全部属性（与 d.ts 一致） */
export interface ShapeText {
  kind: 'text';
  point: ChartPoint;
  text: string;
  style: TextStyle & TextLineToolOverridesPart & {
    hAlign?: LabelHAlign;
    vAlign?: LabelVAlign;
  };
}

/** 矩形；borderWidth 为 0 或不设表示无边框 */
export interface ShapeRectangle {
  kind: 'rectangle';
  p1: ChartPoint;
  p2: ChartPoint;
  style: {
    fillColor: string;
    borderColor?: string;
    /** 0 表示无边框 */
    borderWidth?: number;
    transparency?: number;
  };
}

/** 水平射线文案相对线段的对齐：线段左侧 / 中间 / 右侧 */
export type HorizontalRayLabelAlign = 'left' | 'middle' | 'right';
/** 文案相对线段的上下位置 */
export type HorizontalRayLabelVertical = 'above' | 'below';

/** 从某点水平向右/左的线段 + 可选文案（可置于线段中间或右端，线上或线下） */
export interface ShapeHorizontalRay {
  kind: 'horizontal_ray';
  start: ChartPoint;
  end?: ChartPoint;
  direction?: 'left' | 'right';
  /** 射线长度（秒）；不传则用默认（如约 5 根 K 的跨度） */
  lengthSeconds?: number;
  style: LineStyle;
  /** 文案：可设置对齐方式、上下位置、距离线段的距离、文案自身水平/垂直居中 */
  label?: {
    text: string;
    /** 文案在线段上的位置：左侧 | 中间 | 右侧 */
    align?: HorizontalRayLabelAlign;
    /** 相对线段上下：线上 | 线下 */
    vertical?: HorizontalRayLabelVertical;
    /** 距离线段的价格比例，如 0.002 表示 0.2%；above 时为正则文案在线段上方 */
    offsetPercent?: number;
    /** 文案自身水平对齐：左 | 居中 | 右（相对锚点） */
    hAlign?: LabelHAlign;
    /** 文案自身垂直对齐：上 | 居中 | 下（相对锚点） */
    vAlign?: LabelVAlign;
  } & TextStyle;
}

/** 折线（多点连线，不闭合） */
export interface ShapePolyline {
  kind: 'polyline';
  points: ChartPoint[];
  style: LineStyle;
}

/** 单点箭头 Arrowmarkup/Arrowmarkdown（d.ts）全量可选 */
export interface ShapeArrow {
  kind: 'arrow';
  point: ChartPoint;
  direction: 'up' | 'down';
  style: {
    arrowColor?: string;
    bold?: boolean;
    color: string;
    fontsize?: number;
    italic?: boolean;
    showLabel?: boolean;
  };
}

/** 等腰三角形，TriangleLineToolOverrides（d.ts）全量可选 + sizePercent */
export interface ShapeTriangle {
  kind: 'triangle';
  point: ChartPoint;
  direction: 'up' | 'down';
  style: {
    backgroundColor?: string;
    color: string;
    fillBackground?: boolean;
    linewidth?: number;
    transparency?: number;
    sizePercent?: number;
  };
}

/** 竖线 VertlineLineToolOverrides（d.ts）全量可选 + 兼容 LineStyle */
export interface ShapeVerticalLine {
  kind: 'vertical_line';
  point: ChartPoint;
  style: LineStyle & {
    bold?: boolean;
    extendLine?: boolean;
    fontsize?: number;
    horzLabelsAlign?: string;
    italic?: boolean;
    showTime?: boolean;
    textcolor?: string;
    textOrientation?: string;
    vertLabelsAlign?: string;
  };
}

/** 圆：仅边框与填充，仅保留 color、backgroundColor、fillBackground、linewidth（无文字样式） */
export interface ShapeCircle {
  kind: 'circle';
  center: ChartPoint;
  onCircle: ChartPoint;
  style: {
    backgroundColor?: string;
    color: string;
    fillBackground?: boolean;
    linewidth?: number;
  };
}

/** 水平线 createShape(shape: 'horizontal_line')，HorzlineLineToolOverrides */
export interface ShapeHorizontalLine {
  kind: 'horizontal_line';
  point: ChartPoint;
  style: {
    linecolor?: string;
    linewidth?: number;
    linestyle?: number;
    bold?: boolean;
    showPrice?: boolean;
    fontsize?: number;
    textcolor?: string;
    horzLabelsAlign?: string;
    vertLabelsAlign?: string;
    italic?: boolean;
  };
}

/** 旗帜 createShape(shape: 'flag')，FlagmarkLineToolOverrides */
export interface ShapeFlag {
  kind: 'flag';
  point: ChartPoint;
  text: string;
  style: { flagColor?: string };
}

export type ChartShape =
  | ShapeLine
  | ShapeText
  | ShapeRectangle
  | ShapeHorizontalRay
  | ShapePolyline
  | ShapeArrow
  | ShapeTriangle
  | ShapeVerticalLine
  | ShapeCircle
  | ShapeHorizontalLine
  | ShapeFlag;

/** 默认水平射线长度（约 5 根日 K 的秒数） */
const DEFAULT_RAY_LENGTH_SEC = 5 * 86400;

/** TV 线型：0 实线，1 虚线（以库实际为准） */
const LINESTYLE_SOLID = 0;
const LINESTYLE_DASHED = 1;

/** linetool 前缀，与 charting_library.d.ts 的 DrawingOverrides 一致。
 * 已对接图形与 d.ts 接口：text→TextLineToolOverrides, rectangle→(无独立 Rectangle 接口，可用 fillBackground/backgroundColor 等),
 * trendline→TrendlineLineToolOverrides, arrowmarkup/arrowmarkdown→Arrowmarkup/ArrowmarkdownLineToolOverrides,
 * triangle→TriangleLineToolOverrides, vertline→VertlineLineToolOverrides, circle→CircleLineToolOverrides.
 * 完整列表与键名见 frontend/src/tv/README-shapes.md */
const PREFIX = {
  text: 'linetooltext',
  rectangle: 'linetoolrectangle',
  trendline: 'linetooltrendline',
  arrowmarkup: 'linetoolarrowmarkup',
  arrowmarkdown: 'linetoolarrowmarkdown',
  triangle: 'linetooltriangle',
  vertline: 'linetoolvertline',
  circle: 'linetoolcircle',
  horzline: 'linetoolhorzline',
  flagmark: 'linetoolflagmark',
} as const;

const LOCK_OPTS = {
  lock: true,
  disableSelection: true,
  disableSave: true,
  disableUndo: true,
};

/** 颜色字符串，避免空串或前后空格导致 TV 不生效 */
function toColor(v: string | undefined, fallback: string): string {
  return String(v || fallback).trim();
}

/** 将扁平键对象转为带 linetool 前缀的 overrides（键名不加前缀，如 backgroundColor -> linetoolxxx.backgroundColor） */
function withPrefix(prefix: string, o: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(o).map(([k, v]) => [`${prefix}.${k}`, v]));
}

/** 取 fontsize，兼容 fontSize / fontsize */
function pickFontSize(part?: { fontsize?: number; fontSize?: number }): number {
  return part?.fontsize ?? (part as { fontSize?: number })?.fontSize ?? 14;
}

/** TextLineToolOverrides 全量可选，与 charting_library.d.ts 一致，默认值见 d.ts */
export type TextLineToolOverridesPart = Partial<{
  backgroundColor: string;
  backgroundTransparency: number;
  bold: boolean;
  borderColor: string;
  color: string;
  drawBorder: boolean;
  fillBackground: boolean;
  fixedSize: boolean;
  fontsize: number;
  italic: boolean;
  wordWrap: boolean;
  wordWrapWidth: number;
}>;

/**
 * 按 charting_library.d.ts 的 TextLineToolOverrides 构建文案 overrides，仅使用其中定义的 12 个属性。
 * 默认值来自 d.ts 注释；传入的 part 覆盖对应键。
 */
function buildTextLineToolOverrides(part?: TextLineToolOverridesPart & { fontSize?: number }): Record<string, unknown> {
  return withPrefix(PREFIX.text, {
    backgroundColor: part?.backgroundColor ?? 'rgba(41, 98, 255, 0.25)',
    backgroundTransparency: part?.backgroundTransparency ?? 70,
    bold: part?.bold ?? false,
    borderColor: part?.borderColor ?? '#707070',
    color: toColor(part?.color, '#2962FF'),
    drawBorder: part?.drawBorder ?? false,
    fillBackground: part?.fillBackground ?? false,
    fixedSize: part?.fixedSize ?? true,
    fontsize: pickFontSize(part),
    italic: part?.italic ?? false,
    wordWrap: part?.wordWrap ?? false,
    wordWrapWidth: part?.wordWrapWidth ?? 200,
  });
}

/** 用 canvas 测量单行文案宽度（像素），用于居中时锚点左偏移。 */
function measureTextWidthPx(text: string, fontSize: number, bold?: boolean, italic?: boolean): number {
  if (typeof document === 'undefined' || !text) return 0;
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (!ctx) return 0;
  const font = [
    italic ? 'italic' : '',
    bold ? 'bold' : '',
    `${fontSize}px`,
    'sans-serif',
  ]
    .filter(Boolean)
    .join(' ');
  ctx.font = font || `${fontSize}px sans-serif`;
  return ctx.measureText(text).width;
}

/**
 * 根据时间近似得到时间轴上的 x 坐标（像素）。用于居中时由 (time - 半宽) 反算 time。
 * 使用 getTimeScale().coordinateToTime 二分查找使 coordinateToTime(x) ≈ time 的 x。
 */
function timeToCoordinateX(chart: any, time: number): number | null {
  try {
    const ts = chart.getTimeScale?.();
    if (!ts?.coordinateToTime || typeof ts.width !== 'function') return null;
    const w = ts.width();
    let lo = 0;
    let hi = w;
    const tol = 1;
    for (let i = 0; i < 30; i++) {
      const x = (lo + hi) / 2;
      const t = ts.coordinateToTime(x);
      if (t == null) return null;
      const diff = t - time;
      if (Math.abs(diff) < tol) return x;
      if (diff > 0) hi = x;
      else lo = x;
    }
    return (lo + hi) / 2;
  } catch {
    return null;
  }
}

async function drawLine(chart: any, shape: ShapeLine): Promise<string[]> {
  const ids: string[] = [];
  let p1 = shape.p1;
  const p2 = shape.p2;
  const gapPercent = shape.connectorChartGapPercent ?? 0;
  if (gapPercent > 0) {
    const priceDelta = p1.price * (gapPercent / 100);
    const sign = p2.price >= p1.price ? 1 : -1;
    p1 = { time: p1.time, price: p1.price + sign * priceDelta };
  }
  const lineStyle = shape.style.dashed ? LINESTYLE_DASHED : LINESTYLE_SOLID;
  const overrides: Record<string, unknown> = {
    ...withPrefix(PREFIX.trendline, {
      linecolor: shape.style.color,
      linewidth: shape.style.width,
      linestyle: lineStyle,
    }),
    linecolor: shape.style.color,
    linewidth: shape.style.width,
    linestyle: lineStyle,
  };
  const id = await chart.createMultipointShape([p1, p2], {
    shape: 'trend_line',
    ...LOCK_OPTS,
    overrides,
  });
  ids.push(id);
  if (shape.label) {
    const pt = shape.label.at === 'end' ? shape.p2 : shape.p1;
    const labelOverrides = buildTextLineToolOverrides({
      color: shape.label.color,
      fontsize: shape.label.fontSize,
      bold: shape.label.bold,
    });
    const idText = await chart.createShape(pt, {
      shape: 'text',
      ...LOCK_OPTS,
      text: shape.label.text,
      overrides: labelOverrides,
    });
    ids.push(idText);
  }
  return ids;
}

/**
 * 文案 overrides 严格按 charting_library.d.ts 的 TextLineToolOverrides；
 * 同时传带前缀 + 短名，创建后 setProperties，与圆形一致保证样式生效。
 */
async function drawText(chart: any, shape: ShapeText): Promise<string[]> {
  const s = shape.style;
  const color = toColor(s.color, '#2962FF');
  const fontsize = pickFontSize(s);
  const prefixed = buildTextLineToolOverrides(s);
  const short: Record<string, unknown> = {
    color,
    fontsize,
    bold: s.bold ?? false,
    italic: s.italic ?? false,
    backgroundColor: s.backgroundColor ?? 'rgba(41, 98, 255, 0.25)',
    backgroundTransparency: s.backgroundTransparency ?? 70,
    borderColor: s.borderColor ?? '#707070',
    drawBorder: s.drawBorder ?? false,
    fillBackground: s.fillBackground ?? false,
    fixedSize: s.fixedSize ?? true,
    wordWrap: s.wordWrap ?? false,
    wordWrapWidth: s.wordWrapWidth ?? 200,
  };
  const overrides: Record<string, unknown> = { ...prefixed, ...short };
  const hAlign = s.hAlign ?? 'center';
  const vAlign = s.vAlign ?? 'middle';
  overrides[`${PREFIX.text}.hAlign`] = hAlign;
  overrides[`${PREFIX.text}.vAlign`] = vAlign;
  overrides[`${PREFIX.text}.horzLabelsAlign`] = hAlign;
  overrides[`${PREFIX.text}.vertLabelsAlign`] = vAlign;

  // 选中居中对齐时，若 TV 自身不生效，则向左偏移锚点使文案视觉居中（锚点在文案左侧时左移半宽）。
  let pointToUse: ChartPoint = shape.point;
  if (hAlign === 'center') {
    const centerX = timeToCoordinateX(chart, shape.point.time);
    if (centerX != null) {
      const textWidth = measureTextWidthPx(shape.text, fontsize, s.bold, s.italic);
      const leftX = centerX - textWidth / 2;
      const ts = chart.getTimeScale?.();
      const newTime = ts?.coordinateToTime?.(Math.max(0, leftX));
      if (typeof newTime === 'number') {
        pointToUse = { time: newTime, price: shape.point.price };
      }
    }
  }

  const id = await chart.createShape(pointToUse, {
    shape: 'text',
    ...LOCK_OPTS,
    text: shape.text,
    overrides,
  });
  try {
    const entity = chart.getShapeById(id);
    if (entity?.setProperties) {
      entity.setProperties(overrides);
    }
    // 文案居中对齐：未使用锚点左偏移时，尝试 TV 内部 centerPosition（双 rAF + setTimeout 兜底）。
    // 已使用左偏移时不再调用，避免水平被重复调整。
    const usedOffset = pointToUse !== shape.point;
    if (
      !usedOffset &&
      (hAlign === 'center' && vAlign === 'middle') &&
      typeof (entity as any).centerPosition === 'function'
    ) {
      const tryCenter = () => {
        try {
          const e = chart.getShapeById(id);
          if (e && typeof (e as any).centerPosition === 'function') {
            (e as any).centerPosition();
          }
        } catch {
          // 忽略
        }
      };
      requestAnimationFrame(() => {
        requestAnimationFrame(tryCenter);
      });
      setTimeout(tryCenter, 80);
    }
  } catch {
    // 忽略
  }
  return [id];
}

async function drawRectangle(chart: any, shape: ShapeRectangle): Promise<string[]> {
  const borderWidth = shape.style.borderWidth ?? 1;
  const rectProps: Record<string, unknown> = {
    fillBackground: true,
    backgroundColor: shape.style.fillColor,
    transparency: shape.style.transparency ?? 0,
    linewidth: borderWidth > 0 && shape.style.borderColor ? borderWidth : 0,
  };
  if (borderWidth > 0 && shape.style.borderColor) {
    rectProps.color = shape.style.borderColor;
  }
  const overrides = withPrefix(PREFIX.rectangle, rectProps);
  const id = await chart.createMultipointShape([shape.p1, shape.p2], {
    shape: 'rectangle',
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

async function drawHorizontalRay(
  chart: any,
  shape: ShapeHorizontalRay
): Promise<string[]> {
  let endPoint: ChartPoint;
  if (shape.end) {
    endPoint = shape.end;
  } else {
    const len = shape.lengthSeconds ?? DEFAULT_RAY_LENGTH_SEC;
    const dir = shape.direction ?? 'right';
    const tEnd = dir === 'right' ? shape.start.time + len : shape.start.time - len;
    endPoint = { time: tEnd, price: shape.start.price };
  }
  const tEnd = endPoint.time;
  const lineStyle = shape.style.dashed ? LINESTYLE_DASHED : LINESTYLE_SOLID;
  const lineOverrides: Record<string, unknown> = {
    ...withPrefix(PREFIX.trendline, {
      linecolor: shape.style.color,
      linewidth: shape.style.width,
      linestyle: lineStyle,
    }),
    linecolor: shape.style.color,
    linewidth: shape.style.width,
    linestyle: lineStyle,
  };
  const id = await chart.createMultipointShape([shape.start, endPoint], {
    shape: 'trend_line',
    ...LOCK_OPTS,
    overrides: lineOverrides,
  });
  const ids = [id];
  if (shape.label) {
    const align = shape.label.align ?? 'right';
    const vertical = shape.label.vertical ?? 'above';
    const offsetPercent = shape.label.offsetPercent ?? 0.01;
    const linePrice = shape.start.price;
    const labelTime =
      align === 'left'
        ? shape.start.time
        : align === 'middle'
          ? Math.floor((shape.start.time + tEnd) / 2)
          : tEnd;
    const sign = vertical === 'above' ? 1 : -1;
    const priceOffset = sign * Math.abs(linePrice * offsetPercent);
    const labelPoint: ChartPoint = { time: labelTime, price: linePrice + priceOffset };
    const textOverrides = buildTextLineToolOverrides({
      color: shape.label.color,
      fontsize: shape.label.fontSize,
      bold: shape.label.bold,
    });
    const idText = await chart.createShape(labelPoint, {
      shape: 'text',
      ...LOCK_OPTS,
      text: shape.label.text,
      overrides: textOverrides,
    });
    ids.push(idText);
  }
  return ids;
}

async function drawPolyline(chart: any, shape: ShapePolyline): Promise<string[]> {
  const ids: string[] = [];
  const overrides = withPrefix(PREFIX.trendline, {
    linecolor: shape.style.color,
    linewidth: shape.style.width,
    linestyle: shape.style.dashed ? LINESTYLE_DASHED : LINESTYLE_SOLID,
  });
  const pts = shape.points;
  for (let i = 0; i < pts.length - 1; i++) {
    const id = await chart.createMultipointShape([pts[i], pts[i + 1]], {
      shape: 'trend_line',
      ...LOCK_OPTS,
      overrides,
    });
    ids.push(id);
  }
  return ids;
}

/** 单点箭头：ArrowmarkupLineToolOverrides / ArrowmarkdownLineToolOverrides 全属性 */
async function drawArrow(chart: any, shape: ShapeArrow): Promise<string[]> {
  const isUp = shape.direction === 'up';
  const tvShape = isUp ? 'arrow_up' : 'arrow_down';
  const prefix = isUp ? PREFIX.arrowmarkup : PREFIX.arrowmarkdown;
  const defaultColor = isUp ? '#089981' : '#CC2F3C';
  const color = toColor(shape.style.color || shape.style.arrowColor, defaultColor);
  const overrides = withPrefix(prefix, {
    arrowColor: toColor(shape.style.arrowColor, color),
    bold: shape.style.bold ?? false,
    color,
    fontsize: shape.style.fontsize ?? 14,
    italic: shape.style.italic ?? false,
    showLabel: shape.style.showLabel ?? true,
  });
  const id = await chart.createShape(shape.point, {
    shape: tvShape,
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

/**
 * 等腰三角形三顶点：轴对称，底边水平、中心在 point。
 * 正三角：顶点在上、底在下；倒三角：顶点在下、底在上。时间半宽约半日。
 */
function getTrianglePoints(shape: ShapeTriangle): ChartPoint[] {
  const t = shape.point.time;
  const price = shape.point.price;
  const sizePercent = (shape.style.sizePercent ?? 0.6) / 100;
  const halfDay = 43200;
  const offset = price * sizePercent;
  if (shape.direction === 'up') {
    return [
      { time: t, price: price + offset },       // 顶点
      { time: t - halfDay, price: price - offset }, // 底左
      { time: t + halfDay, price: price - offset }, // 底右
    ];
  }
  return [
    { time: t, price: price - offset },       // 顶点
    { time: t - halfDay, price: price + offset }, // 底左
    { time: t + halfDay, price: price + offset }, // 底右
  ];
}

/** 三角形：createMultipointShape(shape: 'triangle')，TriangleLineToolOverrides 全属性 */
async function drawTriangle(chart: any, shape: ShapeTriangle): Promise<string[]> {
  const points = getTrianglePoints(shape);
  const overrides = withPrefix(PREFIX.triangle, {
    backgroundColor: shape.style.backgroundColor ?? 'rgba(8, 153, 129, 0.2)',
    color: toColor(shape.style.color, '#089981'),
    fillBackground: shape.style.fillBackground ?? true,
    linewidth: shape.style.linewidth ?? 2,
    transparency: shape.style.transparency ?? 80,
  });
  const id = await chart.createMultipointShape(points, {
    shape: 'triangle',
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

/** 竖线：createShape(shape: 'vertical_line')，VertlineLineToolOverrides 全属性 */
async function drawVerticalLine(chart: any, shape: ShapeVerticalLine): Promise<string[]> {
  const lineColor = toColor(shape.style.color, '#2962FF');
  const overrides = withPrefix(PREFIX.vertline, {
    bold: shape.style.bold ?? false,
    extendLine: shape.style.extendLine ?? true,
    fontsize: shape.style.fontsize ?? 14,
    horzLabelsAlign: shape.style.horzLabelsAlign ?? 'center',
    italic: shape.style.italic ?? false,
    linecolor: lineColor,
    linestyle: shape.style.dashed ? LINESTYLE_DASHED : LINESTYLE_SOLID,
    linewidth: shape.style.width ?? 2,
    showTime: shape.style.showTime ?? true,
    textcolor: toColor(shape.style.textcolor ?? shape.style.color, '#2962FF'),
    textOrientation: shape.style.textOrientation ?? 'vertical',
    vertLabelsAlign: shape.style.vertLabelsAlign ?? 'middle',
  });
  const id = await chart.createShape(shape.point, {
    shape: 'vertical_line',
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

/** 水平线：createShape(shape: 'horizontal_line')，HorzlineLineToolOverrides */
async function drawHorizontalLine(chart: any, shape: ShapeHorizontalLine): Promise<string[]> {
  const linecolor = toColor(shape.style.linecolor, '#2962FF');
  const overrides = withPrefix(PREFIX.horzline, {
    bold: shape.style.bold ?? false,
    fontsize: shape.style.fontsize ?? 12,
    horzLabelsAlign: shape.style.horzLabelsAlign ?? 'center',
    italic: shape.style.italic ?? false,
    linecolor,
    linewidth: shape.style.linewidth ?? 2,
    linestyle: shape.style.linestyle ?? LINESTYLE_SOLID,
    showPrice: shape.style.showPrice ?? true,
    textcolor: toColor(shape.style.textcolor ?? shape.style.linecolor, '#2962FF'),
    vertLabelsAlign: shape.style.vertLabelsAlign ?? 'middle',
  });
  const id = await chart.createShape(shape.point, {
    shape: 'horizontal_line',
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

/** 旗帜：createShape(shape: 'flag')，FlagmarkLineToolOverrides */
async function drawFlag(chart: any, shape: ShapeFlag): Promise<string[]> {
  const overrides = withPrefix(PREFIX.flagmark, {
    flagColor: toColor(shape.style.flagColor, '#2962FF'),
  });
  const id = await chart.createShape(shape.point, {
    shape: 'flag',
    ...LOCK_OPTS,
    text: shape.text,
    overrides,
  });
  return [id];
}

/** 圆：createMultipointShape(shape: 'circle')，仅边框与填充，仅传 color、backgroundColor、fillBackground、linewidth */
async function drawCircle(chart: any, shape: ShapeCircle): Promise<string[]> {
  const bg = shape.style.backgroundColor ?? 'rgba(255, 152, 0, 0.2)';
  const color = toColor(shape.style.color, '#FF9800');
  const linewidth = shape.style.linewidth ?? 2;
  const fillBackground = shape.style.fillBackground ?? true;

  const overrides = withPrefix(PREFIX.circle, {
    backgroundColor: bg,
    color,
    fillBackground,
    linewidth,
  });
  const id = await chart.createMultipointShape([shape.center, shape.onCircle], {
    shape: 'circle',
    ...LOCK_OPTS,
    overrides,
  });
  return [id];
}

/**
 * 在图表上绘制一组图形，返回新建的 entity id 列表。
 */
export async function drawChartShapes(
  chart: any,
  shapes: ChartShape[]
): Promise<string[]> {
  const allIds: string[] = [];
  for (const s of shapes) {
    try {
      let ids: string[];
      switch (s.kind) {
        case 'line':
          ids = await drawLine(chart, s);
          break;
        case 'text':
          ids = await drawText(chart, s);
          break;
        case 'rectangle':
          ids = await drawRectangle(chart, s);
          break;
        case 'horizontal_ray':
          ids = await drawHorizontalRay(chart, s);
          break;
        case 'polyline':
          ids = await drawPolyline(chart, s);
          break;
        case 'arrow':
          ids = await drawArrow(chart, s);
          break;
        case 'triangle':
          ids = await drawTriangle(chart, s);
          break;
        case 'vertical_line':
          ids = await drawVerticalLine(chart, s);
          break;
        case 'circle':
          ids = await drawCircle(chart, s);
          break;
        case 'horizontal_line':
          ids = await drawHorizontalLine(chart, s);
          break;
        case 'flag':
          ids = await drawFlag(chart, s);
          break;
        default:
          continue;
      }
      allIds.push(...ids);
    } catch {
      // 单图元失败不阻断
    }
  }
  return allIds;
}

/**
 * 移除图表上由 drawChartShapes 创建的 entities。
 */
export function clearChartShapes(chart: any, entityIds: string[]): void {
  if (!chart) return;
  for (const id of entityIds) {
    try {
      chart.removeEntity(id);
    } catch {
      // ignore
    }
  }
}
