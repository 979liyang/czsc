<template>
  <div ref="chartContainer" class="kline-chart analyze4-style"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { BI, FX, Bar, ZS } from '../types';
import { barsApi } from '../api/bars';

interface Props {
  symbol: string;
  freq: string;
  bis: BI[];
  fxs: FX[];
  zss?: ZS[];
  bars?: Bar[];
  sdt?: string;
  edt?: string;
}

const props = withDefaults(defineProps<Props>(), { zss: () => [] });

const chartContainer = ref<HTMLDivElement>();
let chartInstance: echarts.ECharts | null = null;
const bars = ref<Bar[]>([]);
let resizeHandler: (() => void) | null = null;

const effectiveBars = () => (props.bars && props.bars.length > 0 ? props.bars : bars.value);

function parseDt(dt: string): string {
  const s = String(dt).trim();
  if (s.includes('T')) return s.slice(0, 10);
  return s.length >= 10 ? s.slice(0, 10) : s;
}

function SMA(closes: number[], n: number): number[] {
  const out: number[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (i < n - 1) {
      out.push(NaN);
      continue;
    }
    let sum = 0;
    for (let j = i - n + 1; j <= i; j++) sum += closes[j];
    out.push(sum / n);
  }
  return out;
}

function EMA(src: number[], n: number): number[] {
  const k = 2 / (n + 1);
  const out: number[] = [];
  for (let i = 0; i < src.length; i++) {
    if (i === 0) {
      out.push(src[0]);
      continue;
    }
    out.push(src[i] * k + out[i - 1] * (1 - k));
  }
  return out;
}

function MACD(closes: number[], fast = 12, slow = 26, signal = 9) {
  const emaFast = EMA(closes, fast);
  const emaSlow = EMA(closes, slow);
  const diff = emaFast.map((f, i) => (Number.isNaN(f) || Number.isNaN(emaSlow[i]) ? NaN : f - emaSlow[i]));
  const dea = EMA(diff.map((d) => (Number.isNaN(d) ? 0 : d)), signal);
  const macd = diff.map((d, i) => (Number.isNaN(d) ? 0 : (d - dea[i]) * 2));
  return { diff, dea, macd };
}

const loadBars = async () => {
  if (!props.sdt || !props.edt || (props.bars && props.bars.length > 0)) return;
  try {
    const result = await barsApi.getBars({
      symbol: props.symbol,
      freq: props.freq,
      sdt: props.sdt,
      edt: props.edt,
    });
    bars.value = result.bars;
    updateChart();
  } catch (e) {
    console.error('加载K线数据失败:', e);
  }
};

const initChart = () => {
  if (!chartContainer.value) return;
  chartInstance = echarts.init(chartContainer.value);
  updateChart();
  resizeHandler = () => chartInstance?.resize();
  window.addEventListener('resize', resizeHandler);
};

const updateChart = () => {
  if (!chartInstance) return;
  const sourceBars = effectiveBars();
  if (!sourceBars.length) return;

  const dts = sourceBars.map((b) => parseDt(b.dt));
  const closes = sourceBars.map((b) => b.close);
  const klineData = sourceBars.map((b) => [b.open, b.close, b.low, b.high] as [number, number, number, number]);
  const volData = sourceBars.map((b) => ({
    value: b.vol ?? 0,
    itemStyle: { color: b.close > b.open ? '#F9293E' : '#00aa3b' },
  }));

  const ma5 = SMA(closes, 5);
  const ma13 = SMA(closes, 13);
  const ma21 = SMA(closes, 21);
  const { diff, dea, macd } = MACD(closes);
  const macdBar = macd.map((v) => ({
    value: Math.round(v * 1e4) / 1e4,
    itemStyle: { color: v >= 0 ? '#F9293E' : '#00aa3b' },
  }));

  const fxPoints = props.fxs.map((fx) => [parseDt(fx.dt), Number(fx.fx)] as [string, number]);
  const biPoints: [string, number][] = [];
  if (props.bis.length) {
    props.bis.forEach((bi) => {
      const da = bi.fx_a_dt != null ? parseDt(bi.fx_a_dt) : parseDt(bi.sdt);
      const va = bi.fx_a_fx != null ? Number(bi.fx_a_fx) : (bi.direction === '向上' ? bi.low : bi.high);
      biPoints.push([da, va]);
    });
    const last = props.bis[props.bis.length - 1];
    const db = last.fx_b_dt != null ? parseDt(last.fx_b_dt) : parseDt(last.edt);
    const vb = last.fx_b_fx != null ? Number(last.fx_b_fx) : (last.direction === '向上' ? last.high : last.low);
    biPoints.push([db, vb]);
  }

  const validZss = (props.zss || []).filter((z) => z.is_valid !== false);
  const zsMarkArea: [object, object][] = [];
  if (validZss.length && dts.length) {
    for (const z of validZss) {
      const s = String(z.sdt).slice(0, 10);
      const e = String(z.edt).slice(0, 10);
      let i0 = dts.findIndex((d) => d >= s);
      let i1 = dts.length - 1;
      for (let i = dts.length - 1; i >= 0; i--) {
        if (dts[i] <= e) {
          i1 = i;
          break;
        }
      }
      if (i0 < 0) i0 = 0;
      if (i0 > i1) continue;
      zsMarkArea.push(
        [
          { name: '中枢', xAxis: dts[i0], yAxis: Number(z.zd) },
          { xAxis: dts[i1], yAxis: Number(z.zg) },
        ] as [object, object]
      );
    }
  }

  const upColor = '#F9293E';
  const downColor = '#00aa3b';
  const bgColor = '#1f212d';

  const option: EChartsOption = {
    backgroundColor: bgColor,
    title: {
      text: `${props.symbol} ${props.freq}`,
      left: '0%',
      top: '1%',
      textStyle: { color: upColor, fontSize: 20 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(245,245,245,0.8)',
      borderColor: '#ccc',
      textStyle: { color: '#000' },
    },
    legend: {
      show: true,
      top: '1%',
      left: '30%',
      textStyle: { color: '#0e99e2', fontSize: 12 },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2], rangeStart: 0, rangeEnd: 100 },
      { show: true, type: 'slider', xAxisIndex: [0, 1, 2], bottom: '0%', top: '96%', rangeStart: 0, rangeEnd: 100 },
    ],
    grid: [
      { left: '0%', right: '1%', top: '12%', height: '58%' },
      { left: '0%', right: '1%', top: '74%', height: '8%' },
      { left: '0%', right: '1%', top: '86%', height: '10%' },
    ],
    xAxis: [
      {
        type: 'category',
        data: dts,
        gridIndex: 0,
        boundaryGap: false,
        axisLabel: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category',
        data: dts,
        gridIndex: 1,
        boundaryGap: false,
        axisLabel: { show: true, fontSize: 8, color: '#9b9da9' },
      },
      {
        type: 'category',
        data: dts,
        gridIndex: 2,
        boundaryGap: false,
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        gridIndex: 0,
        splitLine: { show: false },
        axisLabel: { color: '#c7c7c7', fontSize: 8 },
      },
      {
        type: 'value',
        scale: true,
        gridIndex: 1,
        splitLine: { show: false },
        axisLabel: { color: '#c7c7c7', fontSize: 8 },
      },
      {
        type: 'value',
        gridIndex: 2,
        splitLine: { show: false },
        axisLabel: { color: '#c7c7c7' },
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor,
          opacity: 0.8,
        },
        ...(zsMarkArea.length
          ? {
              markArea: {
                silent: true,
                data: zsMarkArea,
                itemStyle: {
                  color: 'rgba(0, 170, 59, 0.15)',
                  borderColor: '#00aa3b',
                  borderWidth: 1,
                },
              },
            }
          : {}),
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        xAxisIndex: 0,
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 1, opacity: 0.8 },
        smooth: true,
      },
      {
        name: 'MA13',
        type: 'line',
        data: ma13,
        xAxisIndex: 0,
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 1, opacity: 0.8 },
        smooth: true,
      },
      {
        name: 'MA21',
        type: 'line',
        data: ma21,
        xAxisIndex: 0,
        yAxisIndex: 0,
        showSymbol: false,
        lineStyle: { width: 1, opacity: 0.8 },
        smooth: true,
      },
      {
        name: 'FX',
        type: 'line',
        data: fxPoints,
        xAxisIndex: 0,
        yAxisIndex: 0,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: true,
        lineStyle: { width: 1 },
        itemStyle: { color: 'rgba(152, 147, 193, 1)' },
      },
      {
        name: 'BI',
        type: 'line',
        data: biPoints,
        xAxisIndex: 0,
        yAxisIndex: 0,
        symbol: 'diamond',
        symbolSize: 10,
        showSymbol: true,
        lineStyle: { width: 1.5, color: 'rgba(184, 117, 225, 1)' },
        itemStyle: { color: 'rgba(184, 117, 225, 1)' },
      },
      {
        name: 'Volume',
        type: 'bar',
        data: volData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        barWidth: '60%',
      },
      {
        name: 'MACD',
        type: 'bar',
        data: macdBar,
        xAxisIndex: 2,
        yAxisIndex: 2,
        barWidth: '60%',
      },
      {
        name: 'DIFF',
        type: 'line',
        data: diff,
        xAxisIndex: 2,
        yAxisIndex: 2,
        showSymbol: false,
        lineStyle: { color: '#da6ee8', width: 1, opacity: 0.8 },
      },
      {
        name: 'DEA',
        type: 'line',
        data: dea,
        xAxisIndex: 2,
        yAxisIndex: 2,
        showSymbol: false,
        lineStyle: { color: '#39afe6', width: 1, opacity: 0.8 },
      },
    ],
  };

  chartInstance.setOption(option, true);
};

onMounted(() => {
  initChart();
  if (props.bars && props.bars.length > 0) updateChart();
  else if (props.sdt && props.edt) loadBars();
});

watch(
  () => [props.bis, props.fxs, props.zss, props.symbol, props.freq, props.bars],
  () => updateChart(),
  { deep: true }
);

watch(
  () => [props.sdt, props.edt],
  () => {
    if (props.sdt && props.edt) loadBars();
  }
);

watch(
  () => [props.symbol, props.freq],
  () => {
    if (props.sdt && props.edt) {
      bars.value = [];
      loadBars();
    }
  }
);

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener('resize', resizeHandler);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style scoped>
.kline-chart.analyze4-style {
  width: 100%;
  height: 700px;
  min-height: 580px;
}
</style>
