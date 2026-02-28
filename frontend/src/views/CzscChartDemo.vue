<!--
  Demo：用当前 mock 数据（顶层 bars/fxs/bis）按 czsc_chart_analyze 单图风格绘制 K 线图
-->
<template>
  <div class="czsc-chart-demo">
    <p class="demo-title">{{ mockData.symbol }} {{ mockData.freq }} · czsc_chart_analyze 风格</p>
    <div ref="chartRef" class="chart-container" style="width: 100%; height: 580px" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { mockData } from './mock';

const chartRef = ref<HTMLDivElement>();
let chartInstance: echarts.ECharts | null = null;

function buildOption(): EChartsOption {
  const bars = mockData.bars || [];
  if (!bars.length) {
    return { backgroundColor: '#1f212d', title: { text: '暂无数据', left: 'center', textStyle: { color: '#e0e0e0' } } };
  }

  // 类目轴：按 bars 顺序 0,1,2,... 保证无缺口、数据连续
  const categoryData = bars.map((b) => b.dt.slice(0, 10));
  const barTimeToIndex = new Map(bars.map((b, i) => [new Date(b.dt).getTime(), i]));

  // K 线：每根对应 [open, close, low, high]
  const klineData = bars.map((b) => [b.open, b.close, b.low, b.high]);

  const series: any[] = [
    {
      type: 'candlestick',
      name: 'K线',
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: klineData,
      itemStyle: {
        color: '#ef5350',
        color0: '#26a69a',
        borderColor: '#ef5350',
        borderColor0: '#26a69a',
      },
    },
  ];

  // 均线：按 bar 索引对齐，与 K 线等长
  const sma = (mockData as any).indicators?.sma || {};
  const maColors: Record<string, string> = { MA5: '#42b28a', MA13: '#5691ce', MA21: '#612ff9' };
  ['MA5', 'MA13', 'MA21'].forEach((key) => {
    const arr = sma[key] as [number, number | null][] | undefined;
    if (!arr?.length) return;
    const timeToVal = new Map(arr.map((p) => [p[0], p[1]]));
    const lineData = bars.map((b) => timeToVal.get(new Date(b.dt).getTime()) ?? null);
    series.push({
      type: 'line',
      name: key,
      xAxisIndex: 0,
      yAxisIndex: 0,
      data: lineData,
      showSymbol: false,
      connectNulls: true,
      lineStyle: { width: 1.5, color: maColors[key] || '#42b28a' },
    });
  });

  // 分型点：用 bar 索引作为 x；先画连线（按时间顺序连接），再画三角标记
  const fxs = mockData.fxs || [];
  if (fxs.length) {
    const withIndex = fxs
      .map((fx) => {
        const i = barTimeToIndex.get(new Date(fx.dt).getTime());
        if (i == null) return null;
        return { i, fx };
      })
      .filter((x): x is { i: number; fx: any } => x != null);
    if (withIndex.length) {
      withIndex.sort((a, b) => a.i - b.i);
      const fxLineData = withIndex.map(({ i, fx }) => [i, fx.fx]);
      series.push({
        type: 'line',
        name: '分型连线',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: fxLineData,
        showSymbol: false,
        connectNulls: false,
        lineStyle: { width: 1.5, color: 'rgba(184, 117, 225, 0.9)' },
      });
      series.push({
        type: 'scatter',
        name: '分型',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: withIndex.map(({ i, fx }) => ({
          value: [i, fx.fx],
          itemStyle: { color: fx.mark === '顶分型' ? '#ef5350' : '#26a69a' },
          symbolRotate: fx.mark === '顶分型' ? 180 : 0,
        })),
        symbol: 'triangle',
        symbolSize: 10,
      });
    }
  }

  // 笔：用 bar 索引作为 x
  const bis = mockData.bis || [];
  if (bis.length) {
    bis.forEach((bi) => {
      const i1 = barTimeToIndex.get(new Date(bi.fx_a_dt || bi.sdt).getTime());
      const i2 = barTimeToIndex.get(new Date(bi.fx_b_dt || bi.edt).getTime());
      if (i1 == null || i2 == null) return;
      const y1 = Number(bi.fx_a_fx ?? (bi.direction === '向上' ? bi.low : bi.high));
      const y2 = Number(bi.fx_b_fx ?? (bi.direction === '向上' ? bi.high : bi.low));
      series.push({
        type: 'line',
        name: '笔',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: [
          [i1, y1],
          [i2, y2],
        ],
        showSymbol: false,
        lineStyle: {
          color: bi.direction === '向上' ? '#26a69a' : '#ef5350',
          width: 2,
        },
      });
    });
  }

  // 成交量：与 bars 等长
  const volData = bars.map((b) => b.vol);
  const volColors = bars.map((b) => (b.close >= b.open ? '#26a69a' : '#ef5350'));
  series.push({
    type: 'bar',
    name: '成交量',
    xAxisIndex: 1,
    yAxisIndex: 1,
    data: volData.map((v, i) => ({ value: v, itemStyle: { color: volColors[i] } })),
  });

  // MACD：按 bar 索引对齐，与 bars 等长
  const macdRaw = (mockData as any).indicators?.macd as [number, number | null, number | null, number | null][] | undefined;
  if (macdRaw?.length) {
    const macdByTime = new Map(macdRaw.map((p) => [p[0], [p[1], p[2], p[3]]]));
    const difData = bars.map((b) => macdByTime.get(new Date(b.dt).getTime())?.[0] ?? null);
    const deaData = bars.map((b) => macdByTime.get(new Date(b.dt).getTime())?.[1] ?? null);
    const macdBarData = bars.map((b) => {
      const v = macdByTime.get(new Date(b.dt).getTime())?.[2];
      return {
        value: v,
        itemStyle: { color: v != null && v >= 0 ? '#26a69a' : '#ef5350' },
      };
    });
    series.push(
      {
        type: 'line',
        name: 'DIF',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: difData,
        showSymbol: false,
        connectNulls: true,
        lineStyle: { width: 1.5, color: '#5691ce' },
      },
      {
        type: 'line',
        name: 'DEA',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: deaData,
        showSymbol: false,
        connectNulls: true,
        lineStyle: { width: 1.5, color: '#fac858' },
      },
      {
        type: 'bar',
        name: 'MACD',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: macdBarData,
      }
    );
  }

  const option: EChartsOption = {
    backgroundColor: '#1f212d',
    animation: true,
    animationDuration: 300,
    color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de'],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(31,33,45,0.9)',
      borderColor: '#4a4d5c',
      textStyle: { color: '#e0e0e0' },
    },
    legend: {
      show: true,
      top: 0,
      left: 'center',
      textStyle: { color: '#e0e0e0' },
    },
    grid: [
      { left: '4%', right: '1%', top: '10%', height: '48%', containLabel: true },
      { left: '4%', right: '1%', top: '60%', height: '14%', containLabel: true },
      { left: '4%', right: '1%', top: '76%', height: '16%', containLabel: true },
    ],
    xAxis: [
      {
        type: 'category',
        gridIndex: 0,
        data: categoryData,
        axisLine: { lineStyle: { color: '#4a4d5c' } },
        axisLabel: { color: '#909399', show: true },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categoryData,
        axisLine: { lineStyle: { color: '#4a4d5c' } },
        axisLabel: { color: '#909399', show: false },
        splitLine: { show: false },
      },
      {
        type: 'category',
        gridIndex: 2,
        data: categoryData,
        axisLine: { lineStyle: { color: '#4a4d5c' } },
        axisLabel: { color: '#909399', show: true },
        splitLine: { show: false },
      },
    ],
    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitArea: { show: false },
        axisLine: { show: false },
        axisLabel: { color: '#909399' },
        splitLine: { lineStyle: { color: '#2f3240', type: 'dashed' } },
      },
      {
        type: 'value',
        gridIndex: 1,
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: '#909399' },
        splitLine: { show: false },
      },
      {
        type: 'value',
        gridIndex: 2,
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: '#909399' },
        splitLine: { lineStyle: { color: '#2f3240' } },
      },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2], start: 0, end: 100 },
      {
        type: 'slider',
        xAxisIndex: [0, 1, 2],
        bottom: '2%',
        start: 0,
        end: 100,
        borderColor: '#4a4d5c',
        fillerColor: 'rgba(64, 158, 255, 0.15)',
        handleStyle: { color: '#409eff' },
        textStyle: { color: '#909399' },
      },
    ],
    axisPointer: {
      link: [{ xAxisIndex: [0, 1, 2] }],
    },
    series,
  };

  return option;
}

function initChart() {
  if (!chartRef.value) return;
  chartInstance = echarts.init(chartRef.value, undefined, { renderer: 'canvas', locale: 'ZH' });
  chartInstance.setOption(buildOption());
}

function onResize() {
  chartInstance?.resize();
}

onMounted(() => {
  initChart();
  window.addEventListener('resize', onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize);
  chartInstance?.dispose();
  chartInstance = null;
});

watch(chartRef, () => {
  if (chartRef.value && chartInstance) chartInstance.setOption(buildOption());
});
</script>

<style scoped>
.czsc-chart-demo {
  padding: 12px;
  background: #1f212d;
  min-height: 100vh;
}

.demo-title {
  margin: 0 0 8px 0;
  color: #e0e0e0;
  font-size: 14px;
}

.chart-container {
  border-radius: 4px;
  overflow: hidden;
}
</style>
