<template>
  <div class="chart-layout h-[100vh]">
    <div class="chart-area">
      <TradingViewWidget
        :symbol="symbol"
        :interval="interval"
        :overrides="chartDefaultConfig.overrides"
        :studies-overrides="chartDefaultConfig.studiesOverrides"
        :smc-enabled="smcEnabled"
        :smc-show-fvg="smcShowFvg"
        :smc-show-zones="smcShowZones"
        :smc-show-swing-ob="smcShowSwingOb"
        :smc-no-internal-ob="smcNoInternalOb"
        :czsc-bs-enabled="czscBsEnabled"
        :czsc-mode="czscMode"
        :czsc-min-klines-per-pen="czscMinKlinesPerPen"
        :czsc-pen-type="czscPenType"
        @chart-ready="onChartReady"
        @symbol-changed="onSymbolChanged"
        @interval-changed="onIntervalChanged"
      />
    </div>
    <ChartRightSidebar
      v-model:symbol="symbol"
      :watchlist-items="watchlistItems"
      v-model:smc-enabled="smcEnabled"
      v-model:smc-show-fvg="smcShowFvg"
      v-model:smc-show-zones="smcShowZones"
      v-model:smc-show-swing-ob="smcShowSwingOb"
      v-model:smc-no-internal-ob="smcNoInternalOb"
      v-model:czsc-bs-enabled="czscBsEnabled"
      v-model:czsc-mode="czscMode"
      v-model:czsc-min-klines-per-pen="czscMinKlinesPerPen"
      v-model:czsc-pen-type="czscPenType"
      :pine-t-s-loading="pineTSLoading"
      :pine-t-s-result="pineTSResult"
      :pine-t-s-error="pineTSError"
      :last-momentum-text="lastMomentumText"
      :spark-bars="sparkBars"
      @remove="onWatchlistRemove"
      @run-pine-ts="runPineTSSqueeze"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import TradingViewWidget from '../components/TradingViewWidget.vue';
import ChartRightSidebar from '../components/ChartRightSidebar.vue';
import { useWatchlistStore } from '../stores/watchlist';
import { fetchBars } from '../tv/udfDatafeed';
import { runSqueezeMomentumWithPineTS } from '../tv/pineTSRunner';
import type { SqueezeMomentumResult } from '../tv/pineTSRunner';

/** 图表默认配置类型，可通过接口下发后传入，便于存服务端 */
export interface TvChartDefaultConfig {
  /** 图表样式覆盖（K 线颜色等），对应 ChartPropertiesOverrides */
  overrides: Record<string, unknown>;
  /** 指标默认样式（如成交量红涨绿跌），对应 StudyOverrides */
  studiesOverrides: Record<string, unknown>;
  /** 默认添加的指标（名称、输入、创建后应用的 overrides） */
  defaultStudies: Array<{
    name: string;
    forceOverlay: boolean;
    lock: boolean;
    inputs?: Record<string, unknown>;
    overrides?: Record<string, unknown>;
  }>;
}

/**
 * 内置默认配置（红涨绿跌 + MACD），与本地存储 config 结构对应：
 * - Volume: palettes.volumePalette.colors["0"]=Falling(跌), ["1"]=Growing(涨) → 红涨绿跌：0=绿 #26a69a, 1=红 #ef5350
 * - MACD: styles.plot_1=MACD线, plot_2=Signal线；同时支持 macd.color/signal.color 与 plot_1.color/plot_2.color
 */
const builtinChartDefaultConfig: TvChartDefaultConfig = {
  overrides: {
    'mainSeriesProperties.candleStyle.upColor': '#ef5350',
    'mainSeriesProperties.candleStyle.downColor': '#26a69a',
    'mainSeriesProperties.candleStyle.borderUpColor': '#ef5350',
    'mainSeriesProperties.candleStyle.borderDownColor': '#26a69a',
    'mainSeriesProperties.candleStyle.wickUpColor': '#ef5350',
    'mainSeriesProperties.candleStyle.wickDownColor': '#26a69a',
  },
  studiesOverrides: {
    // 成交量红涨绿跌
    'volume.volume.color.0': '#26a69a',
    'volume.volume.color.1': '#ef5350',
    'volume.color based on previous close': true,
    'volume.vol.color': '#ef5350',
  },
  defaultStudies: [
    {
      name: 'Moving Average',
      forceOverlay: true,
      lock: false,
      inputs: { length: 5 },
      overrides: { 'plot.color': '#2196F3' },
    },
    {
      name: 'Moving Average',
      forceOverlay: true,
      lock: false,
      inputs: { length: 10 },
      overrides: { 'plot.color': '#43A047' },
    },
    {
      name: 'MACD',
      forceOverlay: false,
      lock: false,
      inputs: { fast_length: 12, slow_length: 26, signal_length: 9 },
      overrides: {
        'histogram.color.0': '#ff5252',
        'histogram.color.1': '#ffcbcd',
        'histogram.color.2': '#ace5dc',
        'histogram.color.3': '#22ab94',
      },
    },
  ],
};

/** 当前使用的图表默认配置（可替换为接口返回，用于存服务端场景） */
const chartDefaultConfig = ref<TvChartDefaultConfig>(builtinChartDefaultConfig);

const route = useRoute();
const router = useRouter();

const defaultSymbol = '600078.SH';
const defaultInterval = '1D';
const symbol = ref<string>(
  typeof route.query.symbol === 'string' && route.query.symbol.trim()
    ? route.query.symbol.trim()
    : defaultSymbol
);

const interval = ref<string>(typeof route.query.interval === 'string' && route.query.interval.trim()
    ? route.query.interval.trim()
    : defaultInterval
);

watch(
  symbol,
  (val) => {
    if (!val) return;
    router.replace({ path: route.path, query: { ...route.query, symbol: val } });
  },
  { immediate: false }
);

watch(
  () => route.query.symbol,
  (querySymbol) => {
    const s = typeof querySymbol === 'string' ? querySymbol.trim() : '';
    if (s && s !== symbol.value) symbol.value = s;
  }
);

watch(
  interval,
  (val) => {
    if (!val) return;
    router.replace({ path: route.path, query: { ...route.query, interval: val } });
  },
  { immediate: false }
);

watch(
  () => route.query.interval,
  (queryInterval) => {
    const i = typeof queryInterval === 'string' ? queryInterval.trim() : '';
    if (i && i !== interval.value) interval.value = i;
  }
);

/** 自选列表：优先使用 store（含名称、最新价、涨跌等），未登录时用默认列表 */
const watchlistStore = useWatchlistStore();
const watchlistItems = computed(() => {
  if (watchlistStore.items.length > 0) return watchlistStore.items;
  return [
    { symbol: '600078.SH', sort_order: 0 },
    { symbol: '000001.SZ', sort_order: 1 },
    { symbol: '000858.SZ', sort_order: 2 },
    { symbol: '600519.SH', sort_order: 3 },
    { symbol: '300750.SZ', sort_order: 4 },
  ];
});

function onWatchlistRemove(sym: string) {
  watchlistStore.remove(sym).catch(() => {});
}

const smcEnabled = ref<boolean>(false);
const smcShowFvg = ref<boolean>(false);
const smcShowZones = ref<boolean>(false);
const smcShowSwingOb = ref<boolean>(false);
const smcNoInternalOb = ref<boolean>(false);
const czscBsEnabled = ref<boolean>(false);
const czscMode = ref<'simple' | 'zslx'>('zslx');
const czscMinKlinesPerPen = ref<number>(5);
const czscPenType = ref<'old' | 'new' | 'fractal'>('new');

const pineTSLoading = ref(false);
const pineTSResult = ref<SqueezeMomentumResult | null>(null);
const pineTSError = ref('');

const lastMomentumText = computed(() => {
  const m = pineTSResult.value?.momentum ?? [];
  const last = m.slice(-30);
  return last.map((v) => (typeof v === 'number' && Number.isFinite(v) ? v.toFixed(4) : '—')).join(', ');
});

const sparkBars = computed(() => {
  const m = pineTSResult.value?.momentum ?? [];
  const arr = m.slice(-50).filter((v) => typeof v === 'number' && Number.isFinite(v)) as number[];
  if (arr.length === 0) return [];
  const max = Math.max(...arr.map(Math.abs), 1e-9);
  return arr.map((v) => ({
    color: v > 0 ? '#26a69a' : v < 0 ? '#ef5350' : '#878b94',
    height: Math.min(100, Math.round((Math.abs(v) / max) * 100)),
  }));
});

async function runPineTSSqueeze() {
  pineTSResult.value = null;
  pineTSError.value = '';
  pineTSLoading.value = true;
  try {
    const toSec = Math.floor(Date.now() / 1000);
    const fromSec = toSec - 2 * 365 * 86400;
    const bars = await fetchBars('/api/v1', symbol.value, interval.value, fromSec, toSec);
    if (bars.length < 60) {
      pineTSError.value = 'K 线不足 60 根，请切换标的或周期';
      return;
    }
    const result = await runSqueezeMomentumWithPineTS(bars);
    pineTSResult.value = result;
  } catch (e: unknown) {
    pineTSError.value = e instanceof Error ? e.message : String(e);
  } finally {
    pineTSLoading.value = false;
  }
}

onMounted(() => {
  watchlistStore.load();
  console.log('[TradingView] 默认配置（可存服务端）:', JSON.stringify(chartDefaultConfig.value, null, 2));
  printLocalStorageChartKeys();
});

/** 打印 localStorage 里与图表相关的 key，便于核对本地已存配置 */
function printLocalStorageChartKeys() {
  try {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && /tradingview|tv\.|chart\.|tvchart/i.test(k)) keys.push(k);
    }
    if (keys.length) {
      console.log('[TradingView] localStorage 中与图表相关的 key:', keys);
      keys.forEach((k) => {
        const raw = localStorage.getItem(k);
        const len = raw?.length ?? 0;
        console.log(`  ${k} (长度 ${len})`, len > 500 ? raw?.slice(0, 500) + '...' : raw);
      });
    } else {
      console.log('[TradingView] localStorage 中未发现图表相关 key');
    }
  } catch (e) {
    console.warn('[TradingView] 读取 localStorage 失败', e);
  }
}

function onChartReady(_widget: any) {
  const widget = _widget;
  const config = chartDefaultConfig.value;
  if (!widget) return;
  if (widget.applyStudiesOverrides && Object.keys(config.studiesOverrides).length) {
    widget.applyStudiesOverrides(config.studiesOverrides);
    setTimeout(() => {
      widget.applyStudiesOverrides?.(config.studiesOverrides);
    }, 300);
  }
  const chart = widget.activeChart?.();
  if (!chart?.createStudy) return;
  config.defaultStudies.forEach((s) => {
    chart
      .createStudy(s.name, s.forceOverlay, s.lock, s.inputs ?? {})
      .then((id: any) => {
        const study = chart.getStudyById?.(id);
        if (!study?.applyOverrides || !s.overrides || !Object.keys(s.overrides).length) return;
        study.applyOverrides(s.overrides);
        setTimeout(() => {
          study.applyOverrides(s.overrides);
        }, 150);
      })
      .catch(() => {});
  });

  setTimeout(() => {
    if (widget.save) {
      widget.save((state: object) => {
        console.log('[TradingView] 当前图表状态（save 回调，含成交量/MACD 等）:', JSON.stringify(state, null, 2));
        const s = state as Record<string, unknown>;
        if (s.charts) {
          const first = (s.charts as unknown[])?.[0] as Record<string, unknown> | undefined;
          if (first?.panes) {
            console.log(
              '[TradingView] 第一个图表的 panes（含 studies 与 overrides）:',
              JSON.stringify(first.panes, null, 2)
            );
          }
        }
      });
    }
  }, 800);
}

function onSymbolChanged(payload: { symbol: string }) {
  if (payload?.symbol && payload.symbol !== symbol.value) symbol.value = payload.symbol;
}

function onIntervalChanged(payload: { interval: string }) {
  if (payload?.interval && payload.interval !== interval.value) interval.value = payload.interval;
}
</script>

<style scoped>
.chart-layout {
  display: flex;
  flex-direction: row;
  min-height: 0;
}
.chart-area {
  flex: 1;
  min-width: 0;
  min-height: 0;
}
</style>

