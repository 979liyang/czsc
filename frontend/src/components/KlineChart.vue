<template>
  <div ref="chartContainer" class="kline-chart" style="width: 100%; height: 500px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import type { BI, FX, Bar } from '../types';
import { barsApi } from '../api/bars';

interface Props {
  symbol: string;
  freq: string;
  bis: BI[];
  fxs: FX[];
  sdt?: string;
  edt?: string;
}

const props = defineProps<Props>();

const chartContainer = ref<HTMLDivElement>();
let chartInstance: echarts.ECharts | null = null;
const bars = ref<Bar[]>([]);
const loading = ref(false);

const loadBars = async () => {
  if (!props.sdt || !props.edt) return;

  loading.value = true;
  try {
    const result = await barsApi.getBars({
      symbol: props.symbol,
      freq: props.freq,
      sdt: props.sdt,
      edt: props.edt,
    });
    bars.value = result.bars;
    updateChart();
  } catch (error) {
    console.error('加载K线数据失败:', error);
  } finally {
    loading.value = false;
  }
};

const initChart = () => {
  if (!chartContainer.value) return;

  chartInstance = echarts.init(chartContainer.value);
  updateChart();

  // 响应式调整
  window.addEventListener('resize', () => {
    chartInstance?.resize();
  });
};

const updateChart = () => {
  if (!chartInstance) return;

  // 准备K线数据
  const klineData: number[][] = bars.value.map((bar) => [
    new Date(bar.dt).getTime(),
    bar.open,
    bar.close,
    bar.low,
    bar.high,
  ]);

  // 处理分型数据
  const fxMarks: any[] = props.fxs.map((fx) => ({
    value: [new Date(fx.dt).getTime(), fx.fx],
    itemStyle: {
      color: fx.mark === '顶分型' ? '#ff0000' : '#00ff00',
    },
    symbol: fx.mark === '顶分型' ? 'triangle' : 'triangle',
    symbolSize: 12,
    symbolRotate: fx.mark === '顶分型' ? 180 : 0,
  }));

  // 处理笔数据（作为线段）
  const biLines: any[] = props.bis.map((bi) => ({
    type: 'line',
    data: [
      [new Date(bi.sdt).getTime(), bi.direction === '向上' ? bi.low : bi.high],
      [new Date(bi.edt).getTime(), bi.direction === '向上' ? bi.high : bi.low],
    ],
    lineStyle: {
      color: bi.direction === '向上' ? '#00ff00' : '#ff0000',
      width: 2,
    },
  }));

  const option: EChartsOption = {
    title: {
      text: `${props.symbol} ${props.freq} 缠论分析`,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    xAxis: {
      type: 'time',
      scale: true,
      boundaryGap: false,
    },
    yAxis: {
      scale: true,
      splitArea: {
        show: true,
      },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        show: true,
        type: 'slider',
        top: '90%',
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a',
        },
      },
      {
        name: '分型',
        type: 'scatter',
        data: fxMarks,
        symbolSize: 12,
      },
    ],
  };

  chartInstance.setOption(option);
};

onMounted(() => {
  initChart();
  if (props.sdt && props.edt) {
    loadBars();
  }
});

watch(() => [props.bis, props.fxs, props.symbol, props.freq], () => {
  updateChart();
});

watch(() => [props.sdt, props.edt], () => {
  if (props.sdt && props.edt) {
    loadBars();
  }
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose();
  }
  window.removeEventListener('resize', () => {
    chartInstance?.resize();
  });
});
</script>

<style scoped>
.kline-chart {
  min-height: 500px;
}
</style>
