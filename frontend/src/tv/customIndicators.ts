/**
 * 自定义指标注册
 *
 * - SMC：占位说明，实际由前端 smcCalculator + 叠加绘制执行。
 * - Squeeze Momentum：用 Charting Library 的 PineJS API 直接按 Pine 思路实现（与 studies/squeeze_momentum_indicator.pine 一致）。
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

export type PineJS = any;
export type CustomIndicator = any;

/** 用 PineJS 实现 Squeeze Momentum [LazyBear]，与 squeeze_momentum_indicator.pine 逻辑一致 */
function buildSqueezeMomentumIndicator(PineJS: PineJS): CustomIndicator {
  return {
    name: 'Squeeze_Momentum_LB',
    metainfo: {
      _metainfoVersion: 53,
      id: 'Squeeze_Momentum_LB@tv-basicstudies-1',
      description: 'Squeeze Momentum Indicator [LazyBear]',
      shortDescription: 'BB 与 KC 挤压动量，PineJS 直接执行（同 squeeze_momentum_indicator.pine）',
      name: 'Squeeze Momentum [LazyBear]',
      format: { type: 'price' as const, precision: 4 },
      is_price_study: false,
      isCustomIndicator: true,
      linkedToSeries: true,
      plots: [
        { id: 'plot_val', type: 'line' },
        { id: 'plot_zero', type: 'line' },
      ],
      defaults: {
        styles: {
          plot_val: {
            plottype: 5, // histogram
            linewidth: 4,
            transparency: 0,
            visible: true,
            color: '#26a69a',
          },
          plot_zero: {
            plottype: 2, // cross
            linewidth: 2,
            transparency: 0,
            visible: true,
            color: '#2196F3',
          },
        },
        inputs: {
          length: 20,
          mult: 2.0,
          lengthKC: 20,
          multKC: 1.5,
          useTrueRange: true,
        },
      },
      styles: {
        plot_val: { title: 'Momentum', histogramBase: 0 },
        plot_zero: { title: 'Squeeze', histogramBase: 0 },
      },
      inputs: [
        { id: 'length', name: 'BB Length', defval: 20, type: 'integer', min: 1, max: 500 },
        { id: 'mult', name: 'BB MultFactor', defval: 2.0, type: 'float', min: 0.1, max: 10 },
        { id: 'lengthKC', name: 'KC Length', defval: 20, type: 'integer', min: 1, max: 500 },
        { id: 'multKC', name: 'KC MultFactor', defval: 1.5, type: 'float', min: 0.1, max: 10 },
        { id: 'useTrueRange', name: 'Use TrueRange (KC)', defval: true, type: 'bool' },
      ],
    },
    constructor: function (this: any) {
      this.main = function (ctx: any, inputs: (i: number) => any) {
        const length = inputs(0) || 20;
        const mult = inputs(1) ?? 2.0;
        const lengthKC = inputs(2) || 20;
        const multKC = inputs(3) ?? 1.5;
        const useTrueRange = inputs(4) !== false;
        const Std = PineJS.Std;
        const maxLen = Math.max(length, lengthKC) + 2;
        ctx.setMinimumAdditionalDepth(maxLen);

        const source = Std.close(ctx);
        const closeSeries = ctx.new_var(source);
        const highSeries = ctx.new_var(Std.high(ctx));
        const lowSeries = ctx.new_var(Std.low(ctx));

        const basis = Std.sma(closeSeries, length, ctx);
        const dev = mult * Std.stdev(closeSeries, length, ctx);
        const upperBB = basis + dev;
        const lowerBB = basis - dev;

        const ma = Std.sma(closeSeries, lengthKC, ctx);
        const rangeVal = useTrueRange ? Std.tr(undefined, ctx) : Std.high(ctx) - Std.low(ctx);
        const rangeSeries = ctx.new_var(rangeVal);
        const rangema = Std.sma(rangeSeries, lengthKC, ctx);
        const upperKC = ma + rangema * multKC;
        const lowerKC = ma - rangema * multKC;
        // 挤压状态可用于后续 colorer 着色：sqzOn / sqzOff / noSqz
        void { upperBB, lowerBB, upperKC, lowerKC };

        const highestHigh = Std.highest(highSeries, lengthKC, ctx);
        const lowestLow = Std.lowest(lowSeries, lengthKC, ctx);
        const smaCloseKC = Std.sma(closeSeries, lengthKC, ctx);
        const inner = (highestHigh + lowestLow) / 2;
        const innerAvg = (inner + smaCloseKC) / 2;
        const diffVal = source - innerAvg;
        const diffSeries = ctx.new_var(diffVal);
        const val = Std.linreg(diffSeries, lengthKC, 0);

        this._valSeries = ctx.new_var(val);

        return [
          { value: val, offset: 0 },
          { value: 0, offset: 0 },
        ];
      };
    },
  };
}

export function getCustomIndicators(PineJS: PineJS): Promise<readonly CustomIndicator[]> {
  const squeezeMomentum = buildSqueezeMomentumIndicator(PineJS);

  const smartMoneyConcepts: CustomIndicator = {
    name: 'LuxAlgo_Smart_Money_Concepts',
    metainfo: {
      id: 'LuxAlgo_Smart_Money_Concepts@tv-basicstudies-1',
      description: 'Smart Money Concepts [LuxAlgo]',
      shortDescription: '在本图表执行：打开图表上方「SMC」开关即可叠加前端根据当前 K 线数据计算的 OB/FVG/Zones 等（数据与图表同源）。完整 Pine 版见 studies/smart_money_concepts_luxalgo.pine。',
      name: 'Smart Money Concepts [LuxAlgo]',
      format: { type: 'price' as const },
      is_price_study: true,
      isCustomIndicator: true,
      linkedToSeries: true,
      defaults: {},
      inputs: [],
      plots: [],
    },
    constructor: function (this: any) {
      this.main = function (_ctx: any, _inputs: any) {
        return null;
      };
    },
  };

  return Promise.resolve([squeezeMomentum, smartMoneyConcepts]);
}
