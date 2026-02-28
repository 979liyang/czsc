/**
 * 使用 PineTS 在浏览器中直接执行 Pine Script 源码，得到指标结果。
 * 与 Charting Library 的 PineJS 不同：PineTS 跑完整 Pine 源码，返回数值数组。
 */

import { PineTS } from 'pinets';
import type { Bar } from './udfDatafeed';

/** PineTS 接受的 K 线格式（openTime 毫秒） */
interface PineTSCandle {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  openTime: number;
}

/** 将前端 Bar 转为 PineTS 蜡烛数组 */
function barsToCandles(bars: Bar[]): PineTSCandle[] {
  return bars.map((b) => ({
    open: b.open,
    high: b.high,
    low: b.low,
    close: b.close,
    volume: b.volume,
    openTime: b.time,
  }));
}

/**
 * Squeeze Momentum 的 Pine v5 源码（与 studies/squeeze_momentum_indicator.pine 逻辑一致）。
 * PineTS 支持原生 Pine v5，故使用 ta.* 等。
 */
const SQUEEZE_MOMENTUM_PINE_V5 = `
//@version=5
indicator("Squeeze Momentum [LazyBear]", overlay=false)
length = input.int(20, "BB Length")
mult = input.float(2.0, "BB MultFactor")
lengthKC = input.int(20, "KC Length")
multKC = input.float(1.5, "KC MultFactor")
useTrueRange = input.bool(true, "Use TrueRange (KC)")
source = close
basis = ta.sma(source, length)
dev = mult * ta.stdev(source, length)
upperBB = basis + dev
lowerBB = basis - dev
ma = ta.sma(source, lengthKC)
range = useTrueRange ? ta.tr : (high - low)
rangema = ta.sma(range, lengthKC)
upperKC = ma + rangema * multKC
lowerKC = ma - rangema * multKC
highestHigh = ta.highest(high, lengthKC)
lowestLow = ta.lowest(low, lengthKC)
smaCloseKC = ta.sma(close, lengthKC)
inner = (highestHigh + lowestLow) / 2
innerAvg = (inner + smaCloseKC) / 2
val = ta.linreg(source - innerAvg, lengthKC, 0)
plot(val, "Momentum", style=plot.style_histogram, linewidth=4)
plot(0, "Zero", linewidth=2)
`;

export interface SqueezeMomentumResult {
  /** 动量值序列（与 bars 一一对应） */
  momentum: number[];
  /** 零线（恒为 0，长度与 momentum 一致） */
  zero: number[];
  /** 原始 plot 标题到数据（若 PineTS 返回格式有变可备用） */
  plots: Record<string, { data: number[] }>;
}

/**
 * 用 PineTS 执行 Squeeze Momentum 的 Pine 源码，返回计算结果。
 * @param bars 与图表同源的 K 线
 */
export async function runSqueezeMomentumWithPineTS(
  bars: Bar[]
): Promise<SqueezeMomentumResult> {
  if (bars.length < 60) {
    return { momentum: [], zero: [], plots: {} };
  }
  const candles = barsToCandles(bars);
  const pineTS = new PineTS(candles);
  await pineTS.ready();
  const ctx = await pineTS.run(SQUEEZE_MOMENTUM_PINE_V5);
  const plots = ctx.plots || {};
  const momentum = Array.isArray(plots['Momentum']?.data) ? plots['Momentum'].data : [];
  const zero = Array.isArray(plots['Zero']?.data) ? plots['Zero'].data : momentum.map(() => 0);
  return {
    momentum,
    zero: zero.length ? zero : momentum.map(() => 0),
    plots,
  };
}
