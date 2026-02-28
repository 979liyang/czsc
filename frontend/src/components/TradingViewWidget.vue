<template>
  <div class="tv-wrap h-[100vh]">
    <div v-if="error" class="tv-error">{{ error }}</div>
    <div :id="containerId" class="tv-container"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { createUdfDatafeed, fetchBars } from '../tv/udfDatafeed';
import { SmcOverlayManager } from '../tv/smcOverlay';
import { CzscBsOverlayManager, type CzscBsOverlayStyle } from '../tv/czscBsOverlay';
import { calcCzscFull } from '../tv/czscBsCalculator';
import { calcCzscZslxFull } from '../tv/czscZslxCalculator';
import { getCustomIndicators } from '../tv/customIndicators';
import { smartMoneyConcepts } from '../tv/smcCalculator';
import { useRouter } from 'vue-router';

const router = useRouter();

/** 图表内部变更时向外部发出的事件（见文档 4.1 / 4.2） */
export interface TvSymbolChangedPayload {
  symbol: string;
}

export interface TvIntervalChangedPayload {
  interval: string;
}

interface Props {
  symbol: string;
  interval: string;
  /** 图表样式覆盖（K 线颜色等），构造时传入，见文档 4.6 ChartPropertiesOverrides */
  overrides?: Record<string, unknown>;
  /** 指标样式覆盖（如成交量红涨绿跌），构造时传入，见文档 4.6 StudyOverrides */
  studiesOverrides?: Record<string, unknown>;
  smcEnabled?: boolean;
  smcShowFvg?: boolean;
  smcShowZones?: boolean;
  smcShowSwingOb?: boolean;
  smcNoInternalOb?: boolean;
  /** 麒麟买卖点叠加 */
  czscBsEnabled?: boolean;
  /** 麒麟模式：simple=简化版无包含处理，zslx=ZSLX 递归版（含 K 线包含、老/新/分型笔、类二） */
  czscMode?: 'simple' | 'zslx';
  /** ZSLX 每笔最少 K 线数（默认 5） */
  czscMinKlinesPerPen?: number;
  /** ZSLX 笔类型：old=老笔, new=新笔, fractal=分型笔 */
  czscPenType?: 'old' | 'new' | 'fractal';
  /** 麒麟叠加样式（颜色、线宽、分型偏移等），见 CzscBsOverlayStyle */
  czscOverlayStyle?: CzscBsOverlayStyle;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'chart-ready', widget: any): void;
  (e: 'symbol-changed', payload: TvSymbolChangedPayload): void;
  (e: 'interval-changed', payload: TvIntervalChangedPayload): void;
}>();

const containerId = `tv_widget_${Math.random().toString(16).slice(2)}`;
const widgetRef = ref<any>(null);
const error = ref<string>('');
const smcMgr = new SmcOverlayManager();
const czscBsMgr = new CzscBsOverlayManager();
/** 顶部工具栏 TradingView 样式按钮 id，用于销毁时移除 */
let headerButtonId: string | null = null;

/** 用于在 destroy 时取消订阅（需与 subscribe 时传入的 callback 同一引用） */
let chartSymbolCallback: ((symbolInfo: any) => void) | null = null;
let chartIntervalCallback: ((interval: string) => void) | null = null;

function loadScriptOnce(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existed = document.querySelector(`script[data-tv-src="${src}"]`) as HTMLScriptElement | null;
    if (existed) {
      if ((window as any).TradingView) resolve();
      else existed.addEventListener('load', () => resolve());
      return;
    }
    const s = document.createElement('script');
    s.src = src;
    s.async = true;
    s.setAttribute('data-tv-src', src);
    s.onload = () => resolve();
    s.onerror = () => reject(new Error(`加载失败: ${src}`));
    document.head.appendChild(s);
  });
}

function unsubscribeChartEvents() {
  const chart = widgetRef.value?.activeChart?.();
  if (!chart) return;
  try {
    if (chartSymbolCallback && chart.onSymbolChanged) {
      chart.onSymbolChanged().unsubscribe(null, chartSymbolCallback);
    }
    if (chartIntervalCallback && chart.onIntervalChanged) {
      chart.onIntervalChanged().unsubscribe(null, chartIntervalCallback);
    }
  } catch {
    // ignore
  }
  chartSymbolCallback = null;
  chartIntervalCallback = null;
}

function destroyWidget() {
  try {
    unsubscribeChartEvents();
    smcMgr.clear(widgetRef.value);
    czscBsMgr.clear(widgetRef.value);
    if (headerButtonId != null && widgetRef.value?.removeButton) {
      widgetRef.value.removeButton(headerButtonId);
      headerButtonId = null;
    }
    widgetRef.value?.remove?.();
  } catch {
    // ignore
  } finally {
    widgetRef.value = null;
  }
}

function intervalToResolution(interval: string): string {
  const s = (interval || '').trim().toUpperCase();
  if (s === '1D' || s === 'D') return 'D';
  if (s === '1W' || s === 'W') return 'W';
  if (s === '1M' || s === 'M') return 'M';
  return s || 'D';
}

async function refreshSmcOverlay() {
  try {
    if (!widgetRef.value) return;
    smcMgr.clear(widgetRef.value);
    if (!props.smcEnabled) return;
    const chart = widgetRef.value.activeChart?.();
    let fromSec: number;
    let toSec: number;
    if (chart?.getVisibleRange) {
      const range = chart.getVisibleRange();
      const from = Number(range?.from);
      const to = Number(range?.to ?? from + 86400 * 365);
      fromSec = from >= 1e12 ? Math.floor(from / 1000) : Math.floor(from);
      toSec = to >= 1e12 ? Math.floor(to / 1000) : Math.floor(to);
    } else {
      toSec = Math.floor(Date.now() / 1000);
      fromSec = toSec - 2 * 365 * 86400;
    }
    const bars = await fetchBars('/api/v1', props.symbol, props.interval, fromSec, toSec);
    if (bars.length < 60) return;
    const { areas, events } = smartMoneyConcepts(bars, {
      show_fair_value_gaps: props.smcShowFvg ?? false,
      show_premium_discount_zones: props.smcShowZones ?? false,
      show_swing_order_blocks: props.smcShowSwingOb ?? false,
      show_internal_order_blocks: !(props.smcNoInternalOb ?? false),
    });
    await smcMgr.draw(widgetRef.value, { areas, events });
  } catch (e) {
    console.warn('[tv] refreshSmcOverlay failed', e);
  }
}

/** 麒麟买卖点请求时间范围：在可见区间基础上前后各扩展的秒数，使标注覆盖更长区间 */
const CZSC_BS_EXTEND_BACK_SEC = 3 * 365 * 86400;   // 开始时间再往前 3 年
const CZSC_BS_EXTEND_FORWARD_SEC = 180 * 86400;     // 结束时间再往后约 6 个月
const CZSC_BS_DEFAULT_RANGE_SEC = 5 * 365 * 86400; // 无可见区间时默认请求 5 年

async function refreshCzscBsOverlay() {
  try {
    if (!widgetRef.value) return;
    czscBsMgr.clear(widgetRef.value);
    if (!props.czscBsEnabled) return;
    const chart = widgetRef.value.activeChart?.();
    let fromSec: number;
    let toSec: number;
    if (chart?.getVisibleRange) {
      const range = chart.getVisibleRange();
      const from = Number(range?.from);
      const to = Number(range?.to ?? from + 86400 * 365);
      fromSec = (from >= 1e12 ? Math.floor(from / 1000) : Math.floor(from)) - CZSC_BS_EXTEND_BACK_SEC;
      toSec = (to >= 1e12 ? Math.floor(to / 1000) : Math.floor(to)) + CZSC_BS_EXTEND_FORWARD_SEC;
    } else {
      toSec = Math.floor(Date.now() / 1000) + CZSC_BS_EXTEND_FORWARD_SEC;
      fromSec = toSec - CZSC_BS_DEFAULT_RANGE_SEC;
    }
    const resolution = intervalToResolution(props.interval);
    const bars = await fetchBars('/api/v1', props.symbol, resolution, fromSec, toSec);
    const mode = props.czscMode ?? 'zslx';
    const result =
      mode === 'zslx'
        ? calcCzscZslxFull(bars, {
            minKlinesPerPen: props.czscMinKlinesPerPen ?? 5,
            penType: props.czscPenType ?? 'new',
          })
        : calcCzscFull(bars);
    const hasAny =
      result.fxs.length > 0 ||
      result.bis.length > 0 ||
      result.zsList.length > 0 ||
      result.events.length > 0;
    if (hasAny) {
      await czscBsMgr.draw(widgetRef.value, {
        events: result.events,
        count: result.events.length,
        fxs: result.fxs,
        bis: result.bis,
        zsList: result.zsList,
        style: props.czscOverlayStyle,
      });
    }
  } catch (e) {
    console.warn('[tv] refreshCzscBsOverlay failed', e);
  }
}

async function initWidget() {
  error.value = '';
  destroyWidget();
  try {
    await loadScriptOnce('/charting_library/charting_library.js');
    const TradingView = (window as any).TradingView;
    if (!TradingView?.widget) {
      error.value = 'TradingView.widget 不存在，请检查 charting_library 静态资源是否可访问';
      return;
    }
    const datafeed = createUdfDatafeed('/api/v1');
    widgetRef.value = new TradingView.widget({
      symbol: props.symbol,
      interval: props.interval,
      container: containerId,
      datafeed,
      library_path: '/charting_library/',
      locale: 'zh',
      timezone: 'Asia/Shanghai',
      // theme: 'dark',
      autosize: true,
      enabled_features: ['charting_library_debug_mode'],
      overrides:
        props.overrides && Object.keys(props.overrides).length ? props.overrides : undefined,
      studies_overrides:
        props.studiesOverrides && Object.keys(props.studiesOverrides).length
          ? props.studiesOverrides
          : undefined,
      custom_indicators_getter: getCustomIndicators,
    });
    widgetRef.value.onChartReady(() => {
      const chart = widgetRef.value?.activeChart?.();
      if (chart) {
        chartSymbolCallback = (symbolInfo: any) => {
          const s = symbolInfo?.ticker ?? symbolInfo?.name ?? '';
          if (s) emit('symbol-changed', { symbol: String(s) });
        };
        chartIntervalCallback = (interval: string) => {
          if (interval) emit('interval-changed', { interval: String(interval) });
        };
        chart.onSymbolChanged?.().subscribe(null, chartSymbolCallback);
        chart.onIntervalChanged?.().subscribe(null, chartIntervalCallback);
      }
      emit('chart-ready', widgetRef.value);
      refreshSmcOverlay();
      refreshCzscBsOverlay();
    });
    if (typeof widgetRef.value.headerReady === 'function') {
      widgetRef.value.headerReady().then(() => {
        if (!widgetRef.value?.createButton) return;
        headerButtonId = widgetRef.value.createButton({
          align: 'right',
          useTradingViewStyle: true,
          text: '返回主页',
          title: '返回主页',
          onClick: () => {
            router.push('/');
          },
        });
      });
    }
  } catch (e: any) {
    error.value = e?.message || '初始化 TradingView 失败';
  }
}

onMounted(() => {
  initWidget();
});

watch(
  () => [props.symbol, props.interval],
  ([newSymbol, newInterval]) => {
    const w = widgetRef.value;
    if (w?.setSymbol && newSymbol && newInterval) {
      w.setSymbol(String(newSymbol), String(newInterval), () => {});
    } else if (!w) {
      initWidget();
    }
  }
);

watch(
  () => [props.smcEnabled, props.smcShowFvg, props.smcShowZones, props.smcShowSwingOb, props.smcNoInternalOb],
  () => {
    refreshSmcOverlay();
  }
);

watch(
  () => [
    props.czscBsEnabled,
    props.symbol,
    props.interval,
    props.czscMode,
    props.czscMinKlinesPerPen,
    props.czscPenType,
    props.czscOverlayStyle,
  ],
  () => {
    refreshCzscBsOverlay();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  destroyWidget();
});
</script>

<style scoped>
.tv-wrap {
  width: 100%;
  background: #1f212d;
  position: relative;
  border-radius: 4px;
  overflow: hidden;
}
.tv-container {
  width: 100%;
  height: 100%;
}
.tv-error {
  position: absolute;
  z-index: 10;
  left: 12px;
  top: 12px;
  padding: 8px 10px;
  border-radius: 4px;
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
  font-size: 13px;
}
</style>

