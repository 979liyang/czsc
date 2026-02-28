<!--
  与 .results/czsc_chart_analyze_01_000001.SH_20260209_104835.html 完全一致：内容、技术栈、样式及数据均来自该参考 HTML；
  图表数据从该 HTML 内嵌 option 导出为 frontend/public/czsc_chart_000001_SH_option.json，本页加载后 setOption(option)。
-->
<template>
  <div class="czsc-analyze-demo">
    <div v-if="error" class="czsc-analyze-error">{{ error }}</div>
    <div v-else ref="chartRef" class="chart-wrap" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';

const chartRef = ref<HTMLDivElement>();
const error = ref<string>('');
let chartInstance: echarts.ECharts | null = null;

const OPTION_JSON_URL = '/czsc_chart_000001_SH_option.json';

function initChart() {
  if (!chartRef.value) return;
  chartInstance = echarts.init(chartRef.value, 'white', { renderer: 'canvas', locale: 'ZH' });

  fetch(OPTION_JSON_URL)
    .then((res) => {
      if (!res.ok) throw new Error(res.statusText);
      return res.json();
    })
    .then((option: EChartsOption) => {
      if (!option || typeof option !== 'object') throw new Error('option 格式无效');
      chartInstance?.setOption(option);
      error.value = '';
    })
    .catch((e) => {
      error.value =
        '请先从参考 HTML 导出 option 数据：在项目根目录执行 python scripts/extract_echarts_option_from_html.py，' +
        `将生成 frontend/public/czsc_chart_000001_SH_option.json。加载失败: ${e instanceof Error ? e.message : String(e)}`;
    });
}

onMounted(() => {
  initChart();
  window.addEventListener('resize', () => chartInstance?.resize());
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', () => chartInstance?.resize());
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style scoped>
.czsc-analyze-demo {
  width: 1400px;
  height: 580px;
  margin: 0;
  padding: 0;
  background: #1f212d;
}

.chart-wrap {
  width: 1400px;
  height: 580px;
}

.czsc-analyze-error {
  padding: 1rem;
  color: #f0f0f0;
  background: #1f212d;
  width: 1400px;
  height: 580px;
  box-sizing: border-box;
}
</style>
