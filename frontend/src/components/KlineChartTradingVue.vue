<template>
  <div ref="chartContainer" class="kline-chart-tradingvue" style="width: 100%; height: 600px">
    <div v-if="!chartData || chartData.length === 0" class="empty-state">
      <p>正在加载K线数据...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount, nextTick } from 'vue';
import type { AnalysisResponseData } from '../api/analysis';
import type { TradingVueData } from '../types';
import { barsApi } from '../api/bars';
import type { Bar } from '../types';

interface Props {
  data: AnalysisResponseData;
  symbol: string;
}

const props = defineProps<Props>();

const chartContainer = ref<HTMLDivElement>();
let chartInstance: any = null;
const chartData = ref<TradingVueData[]>([]);
const loading = ref(false);

// 将 Bar 数据转换为 TradingVue 格式
const convertBarsToTradingVue = (bars: Bar[]): TradingVueData[] => {
  if (!bars || bars.length === 0) return [];
  
  return bars.map((bar) => ({
    t: new Date(bar.dt).getTime(), // 时间戳（毫秒）
    o: bar.open, // 开盘价
    h: bar.high, // 最高价
    l: bar.low, // 最低价
    c: bar.close, // 收盘价
    v: bar.vol, // 成交量
  }));
};

// 加载K线数据
const loadBars = async () => {
  if (!props.symbol || !props.data) return;
  
  loading.value = true;
  try {
    // 从分析数据中获取时间范围（如果有的话）
    // 否则使用默认时间范围
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    const sdt = oneYearAgo.toISOString().split('T')[0].replace(/-/g, '');
    const edt = today.toISOString().split('T')[0].replace(/-/g, '');
    
    const result = await barsApi.getBars({
      symbol: props.symbol,
      freq: props.data.freq || '日线',
      sdt,
      edt,
    });
    
    chartData.value = convertBarsToTradingVue(result.bars);
    await nextTick();
    initChart();
  } catch (error) {
    console.error('加载K线数据失败:', error);
  } finally {
    loading.value = false;
  }
};

// 将分型转换为 TradingVue overlay
const convertFxsToOverlay = () => {
  if (!props.data.fxs || props.data.fxs.length === 0) return null;
  
  return {
    name: '分型',
    type: 'FX',
    data: props.data.fxs.map((fx) => ({
      time: new Date(fx.dt).getTime(),
      price: fx.mark === '顶分型' ? fx.high : fx.low,
      mark: fx.mark,
      high: fx.high,
      low: fx.low,
    })),
    settings: {
      color: '#ff6b6b',
    },
  };
};

// 将笔转换为 TradingVue overlay
const convertBisToOverlay = () => {
  if (!props.data.bis || props.data.bis.length === 0) return null;
  
  return {
    name: '笔',
    type: 'BI',
    data: props.data.bis.map((bi) => ({
      time: new Date(bi.sdt).getTime(),
      price: bi.direction === '向上' ? bi.low : bi.high,
      direction: bi.direction,
      power: bi.power,
      high: bi.high,
      low: bi.low,
    })),
    settings: {
      color: '#4ecdc4',
    },
  };
};

// 初始化图表
const initChart = async () => {
  if (!chartContainer.value || chartData.value.length === 0) return;

  try {
    // 动态导入 trading-vue-js
    const TradingVue = (await import('trading-vue-js')).default;
    
    // 准备 overlays
    const overlays: any[] = [];
    const fxOverlay = convertFxsToOverlay();
    const biOverlay = convertBisToOverlay();
    if (fxOverlay) overlays.push(fxOverlay);
    if (biOverlay) overlays.push(biOverlay);
    
    // 准备图表数据
    const tvData = {
      ohlcv: chartData.value,
      overlays,
    };

    // 初始化 TradingVue
    chartInstance = new TradingVue({
      target: chartContainer.value,
      data: tvData,
      width: chartContainer.value.clientWidth,
      height: chartContainer.value.clientHeight,
      // 配置选项
      config: {
        DEFAULT_LEN: 100,
        IB: 50,
        TOOLBAR: true,
      },
    });
  } catch (error) {
    console.error('初始化 TradingVue 图表失败:', error);
  }
};

// 更新图表
const updateChart = () => {
  if (!chartInstance || chartData.value.length === 0) return;

  // 准备 overlays
  const overlays: any[] = [];
  const fxOverlay = convertFxsToOverlay();
  const biOverlay = convertBisToOverlay();
  if (fxOverlay) overlays.push(fxOverlay);
  if (biOverlay) overlays.push(biOverlay);

  const tvData = {
    ohlcv: chartData.value,
    overlays,
  };

  chartInstance.update(tvData);
};

// 调整图表大小
const resizeChart = () => {
  if (chartInstance && chartContainer.value) {
    chartInstance.resize(
      chartContainer.value.clientWidth,
      chartContainer.value.clientHeight
    );
  }
};

onMounted(async () => {
  await loadBars();
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  if (chartInstance) {
    try {
      chartInstance.destroy?.();
    } catch (error) {
      console.error('销毁图表失败:', error);
    }
    chartInstance = null;
  }
  window.removeEventListener('resize', resizeChart);
});

watch(
  () => props.data,
  () => {
    if (props.data) {
      loadBars();
    }
  },
  { deep: true }
);
</script>

<style scoped>
.kline-chart-tradingvue {
  min-height: 600px;
  position: relative;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}
</style>
