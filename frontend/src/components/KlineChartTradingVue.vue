<!--
  trading-vue-js 数据结构见: https://github.com/tvjsx/trading-vue-js/tree/master/docs/api#api-book
  要求: chart (必填), onchart, offchart；chart.data 为 [ [timestamp, o, h, l, c, vol], ... ]
-->
<template>
  <div ref="wrapRef" class="kline-chart-tradingvue" style="width: 100%; height: 600px">
    <div v-if="!tvDataRef" class="empty-state">
      <p>{{ emptyText }}</p>
    </div>
    <TradingVue
      v-else
      :data="tvDataRef"
      :overlays="customOverlays"
      :width="width"
      :height="height"
      :toolbar="true"
      :chart-config="{ DEFAULT_LEN: 100, IB: 0, TOOLBAR: true }"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import TradingVue from 'trading-vue-js';
import type { LocalCzscItemData, LocalCzscMetaData } from '../api/analysis';

/** 与 mock / 接口返回兼容：含 freq、bars、fxs、bis、indicators 等 */
interface Props {
  item: LocalCzscItemData | null | undefined;
  meta?: LocalCzscMetaData;
}

const props = defineProps<Props>();

let lastEmptyDebugKey = '';
const emptyText = ref('当前周期无数据');
const wrapRef = ref<HTMLDivElement>();
const width = ref(800);
const height = ref(600);
let ro: ResizeObserver | null = null;

const debugEmptyOnce = () => {
  if (!import.meta.env.DEV) return;
  const key = `${props.item?.freq || 'unknown'}`;
  if (key && key !== lastEmptyDebugKey) {
    lastEmptyDebugKey = key;
    // 仅开发环境输出一次，避免刷屏
    const genCount = props.meta?.generated_bar_counts?.[props.item?.freq || ''] ?? null;
    console.debug('[KlineChartTradingVue] bars 为空，当前周期无数据', { freq: props.item?.freq, generated: genCount });
  }
};

const updateEmptyText = () => {
  const f = props.item?.freq || '';
  const gen = props.meta?.generated_bar_counts?.[f];
  if (gen === 0) {
    emptyText.value = '该周期合成后无数据';
    return;
  }
  emptyText.value = '当前周期无数据';
};

const buildOhlcv = () => {
  const bars = props.item?.bars || [];
  return bars.map((b) => [
    new Date(b.dt).getTime(),
    b.open,
    b.high,
    b.low,
    b.close,
    b.vol,
  ]);
};

const buildFxTrades = () => {
  const fxs = props.item?.fxs || [];
  if (!fxs.length) return [];
  return fxs.map((fx) => {
    const ts = new Date(fx.dt).getTime();
    const isBottom = fx.mark === '底分型';
    const side = isBottom ? 1 : 0;
    const price = fx.fx;
    const label = isBottom ? '底' : '顶';
    return [ts, side, price, label];
  });
};

const buildBiSpline = () => {
  const bis: any[] = props.item?.bis || [];
  const pts: Array<[number, number]> = [];
  for (const bi of bis) {
    if (bi.fx_a_dt && bi.fx_a_fx != null) {
      pts.push([new Date(bi.fx_a_dt).getTime(), Number(bi.fx_a_fx)]);
    }
  }
  const last = bis[bis.length - 1];
  if (last && last.fx_b_dt && last.fx_b_fx != null) {
    pts.push([new Date(last.fx_b_dt).getTime(), Number(last.fx_b_fx)]);
  }
  // 去重 + 排序
  const map = new Map<number, number>();
  for (const [t, v] of pts) map.set(t, v);
  return Array.from(map.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([t, v]) => [t, v] as [number, number]);
};

const buildSmaIndicators = () => {
  const sma = props.item?.indicators?.sma || {};
  const colors: Record<string, string> = { MA5: '#42b28a', MA13: '#5691ce', MA21: '#612ff9' };
  return Object.keys(sma)
    .filter((k) => sma[k] && Array.isArray(sma[k]) && sma[k].length > 0)
    .map((k) => ({
      name: k,
      type: 'SMA',
      data: sma[k],
      settings: { color: colors[k] || '#42b28a', lineWidth: 1.0, skipNaN: true },
    }));
};

/** 构建符合 trading-vue-js API 的 data 对象，避免每次渲染新引用导致库内部报错 */
function buildTvData(): Record<string, unknown> | null {
  updateEmptyText();
  const ohlcv = buildOhlcv();
  if (!ohlcv.length) {
    debugEmptyOnce();
    return null;
  }

  const onchart: any[] = [];
  const smaIndicators = buildSmaIndicators();
  if (smaIndicators.length > 0) onchart.push(...smaIndicators);

  const biPts = buildBiSpline();
  if (biPts.length) {
    onchart.push({
      name: 'BI',
      type: 'Spline',
      data: biPts,
      settings: { color: 'rgba(184, 117, 225, 1.0)', lineWidth: 1.5, skipNaN: true },
    });
  }

  const fxTrades = buildFxTrades();
  if (fxTrades.length) {
    onchart.push({
      name: 'FX',
      type: 'Trades',
      data: fxTrades,
      settings: { showLabel: false },
    });
  }

  const offchart: any[] = [];
  offchart.push({ name: 'Volume', type: 'Volume', data: ohlcv, settings: {} });

  if (import.meta.env.DEV) {
    const key = `tv_dbg_${props.item?.freq || 'unknown'}`;
    if (key !== lastEmptyDebugKey) {
      lastEmptyDebugKey = key;
      console.debug('[KlineChartTradingVue] tvData', {
        freq: props.item?.freq,
        bars_count: ohlcv.length,
        onchartCount: onchart.length,
        offchartCount: offchart.length,
      });
    }
  }

  return {
    chart: { type: 'Candles', data: ohlcv, settings: { showVolume: false } },
    onchart,
    offchart,
  };
}

const tvDataRef = ref<Record<string, unknown> | null>(null);

watch(
  () => props.item,
  () => {
    tvDataRef.value = buildTvData();
  },
  { immediate: true, deep: true }
);

const customOverlays: any[] = [];

onMounted(() => {
  if (!wrapRef.value) return;
  const updateSize = () => {
    if (!wrapRef.value) return;
    width.value = wrapRef.value.clientWidth || 800;
    height.value = 600;
  };
  updateSize();
  ro = new ResizeObserver(() => updateSize());
  ro.observe(wrapRef.value);
});

onBeforeUnmount(() => {
  if (ro && wrapRef.value) ro.unobserve(wrapRef.value);
  ro = null;
});

watch(
  () => props.meta,
  () => updateEmptyText(),
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
