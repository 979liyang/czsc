<template>
  <aside class="right-siderbar" :class="{ 'is-watchlist-expanded': watchlistPanelVisible }">
    <!-- 内容区：左侧自选，右侧工具 -->
    <div class="widgetbar-pages">
      <!-- 自选（左侧，可收起） -->
      <div v-show="watchlistPanelVisible" class="widgetbar-page watchlist-page">
        <div class="widgetbar-widget-header">
          <span class="widgetbar-widget-title">自选表</span>
        </div>
        <div class="watchlist-table-wrap">
          <table class="watchlist-table">
            <thead>
              <tr>
                <th>代码</th>
                <th>名称</th>
                <th class="num">最新价</th>
                <th class="num">涨跌</th>
                <th class="num">涨跌%</th>
                <th class="op">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in watchlistItems"
                :key="item.symbol"
                class="watchlist-row"
                :class="{ active: item.symbol === symbol }"
                @click="emit('update:symbol', item.symbol)"
              >
                <td class="code">{{ item.symbol }}</td>
                <td class="name">{{ item.name ?? '—' }}</td>
                <td class="num">{{ formatNum(item.latest_price) }}</td>
                <td class="num" :class="changeClass(item.change)">{{ formatNum(item.change) }}</td>
                <td class="num" :class="changeClass(item.change_pct)">{{ formatPct(item.change_pct) }}</td>
                <td class="op">
                  <button type="button" class="btn-remove" title="删除" @click.stop="emit('remove', item.symbol)">
                    删除
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="watchlistItems.length === 0" class="watchlist-empty">暂无自选</div>
        </div>
      </div>
      <!-- 工具（右侧，常显） -->
      <div class="widgetbar-page tools-page">
        <ChartRightTools
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
          @run-pine-ts="emit('run-pine-ts')"
        />
      </div>
    </div>
    <!-- 标签条：靠右，自选(展开/收起) + 工具 -->
    <div class="widgetbar-tabs" role="toolbar" aria-orientation="vertical">
      <button
        type="button"
        class="widgetbar-tab"
        :class="{ 'is-active': watchlistPanelVisible }"
        title="自选表"
        @click="toggleWatchlist"
      >
        <span class="widgetbar-tab-icon" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="20" height="20">
            <path fill="currentColor" d="M28 16H16v1h12v-1ZM28 20H16v1h12v-1ZM16 24h12v1H16v-1Z" />
            <path fill="currentColor" fill-rule="evenodd" d="m22 30-10 4V12a1 1 0 0 1 1-1h18a1 1 0 0 1 1 1v22l-10-4Zm-9 2.52V12h18v20.52l-9-3.6-9 3.6Z" />
          </svg>
        </span>
      </button>
      <button
        type="button"
        class="widgetbar-tab is-active"
        title="工具"
      >
        <span class="widgetbar-tab-icon" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 44 44" width="20" height="20">
            <path fill="currentColor" d="M7.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM5 14.5a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0zm9.5-1.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM12 14.5a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0zm9.5-1.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM19 14.5a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0z" />
          </svg>
        </span>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ChartRightTools from './ChartRightTools.vue';
import type { SqueezeMomentumResult } from '../tv/pineTSRunner';
import type { WatchlistItem } from '../api/watchlist';

interface SparkBar {
  color: string;
  height: number;
}

defineProps<{
  /** 自选列表（含代码、名称、最新价、涨跌、涨跌%） */
  watchlistItems: WatchlistItem[];
  symbol: string;
  pineTSLoading: boolean;
  pineTSResult: SqueezeMomentumResult | null;
  pineTSError: string;
  lastMomentumText: string;
  sparkBars: SparkBar[];
}>();

const emit = defineEmits<{
  (e: 'update:symbol', v: string): void;
  (e: 'remove', symbol: string): void;
  (e: 'run-pine-ts'): void;
}>();

const smcEnabled = defineModel<boolean>('smcEnabled', { default: false });
const smcShowFvg = defineModel<boolean>('smcShowFvg', { default: false });
const smcShowZones = defineModel<boolean>('smcShowZones', { default: false });
const smcShowSwingOb = defineModel<boolean>('smcShowSwingOb', { default: false });
const smcNoInternalOb = defineModel<boolean>('smcNoInternalOb', { default: false });
const czscBsEnabled = defineModel<boolean>('czscBsEnabled', { default: false });
const czscMode = defineModel<'simple' | 'zslx'>('czscMode', { default: 'zslx' });
const czscMinKlinesPerPen = defineModel<number>('czscMinKlinesPerPen', { default: 5 });
const czscPenType = defineModel<'old' | 'new' | 'fractal'>('czscPenType', { default: 'new' });

/** 自选面板是否展开；点击自选 tab 展开，再次点击收起 */
const watchlistPanelVisible = ref(false);

function toggleWatchlist() {
  watchlistPanelVisible.value = !watchlistPanelVisible.value;
}

function formatNum(v: number | null | undefined): string {
  if (v == null || (typeof v === 'number' && !Number.isFinite(v))) return '—';
  return String(v);
}

function formatPct(v: number | null | undefined): string {
  if (v == null || (typeof v === 'number' && !Number.isFinite(v))) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

function changeClass(v: number | null | undefined): string {
  if (v == null || (typeof v !== 'number') || !Number.isFinite(v)) return '';
  return v > 0 ? 'up' : v < 0 ? 'down' : '';
}
</script>

<style scoped>
.right-siderbar {
  flex-shrink: 0;
  display: flex;
  flex-direction: row;
  border-left: 1px solid var(--tv-border, #ebebeb);
  background: var(--tv-widget-pages-bg, #fff);
  overflow: hidden;
}
.right-siderbar.is-watchlist-expanded {
  min-width: 320px;
}
/* 内容区：左侧自选 + 右侧工具，横向排列 */
.widgetbar-pages {
  display: flex;
  flex-direction: row;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
.widgetbar-tabs {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  gap: 4px;
  width: 46px;
  flex-shrink: 0;
  background: var(--tv-toolbar-bg, #f9f9f9);
  border-left: 1px solid var(--tv-border, #ebebeb);
}
.widgetbar-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--tv-toolbar-icon, #707070);
  cursor: pointer;
}
.widgetbar-tab:hover {
  background: var(--tv-toolbar-hover, #ebebeb);
  color: var(--tv-toolbar-icon-hover, #2e2e2e);
}
.widgetbar-tab.is-active {
  background: var(--tv-toolbar-active-bg, #e3effd);
  color: var(--tv-toolbar-active, #2962ff);
}
.widgetbar-tab-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}
.widgetbar-pages {
  width: 280px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: var(--tv-widget-pages-bg, #fff);
}
.widgetbar-page {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 8px 10px;
  overflow: hidden;
}
/* 自选面板固定宽度，工具面板占满剩余 */
.watchlist-page {
  width: 280px;
  min-width: 280px;
  flex: 0 0 auto;
  border-right: 1px solid var(--tv-border, #ebebeb);
}
.tools-page {
  flex: 1;
  min-width: 0;
}
.widgetbar-widget-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--tv-text-primary, #0f0f0f);
  margin-bottom: 8px;
  padding: 0 2px;
}
.watchlist-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}
.watchlist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.watchlist-table th,
.watchlist-table td {
  padding: 4px 6px;
  text-align: left;
  border-bottom: 1px solid var(--tv-border, #eee);
}
.watchlist-table th {
  font-weight: 600;
  color: var(--tv-text-secondary, #666);
  white-space: nowrap;
}
.watchlist-table th.num,
.watchlist-table td.num {
  text-align: right;
}
.watchlist-table th.op,
.watchlist-table td.op {
  text-align: center;
}
.watchlist-row {
  cursor: pointer;
  color: var(--tv-text-regular, #4a4a4a);
}
.watchlist-row:hover {
  background: var(--tv-list-item-hover, #e3effd);
}
.watchlist-row.active {
  background: var(--tv-list-item-active-bg, #e3effd);
  color: var(--tv-list-item-active, #2962ff);
}
.watchlist-table .code {
  font-family: ui-monospace, monospace;
}
.watchlist-table .num.up {
  color: #ef5350;
}
.watchlist-table .num.down {
  color: #26a69a;
}
.btn-remove {
  padding: 2px 6px;
  font-size: 11px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--tv-text-secondary, #909399);
  cursor: pointer;
}
.btn-remove:hover {
  background: #ffebee;
  color: #c62828;
}
.watchlist-empty {
  padding: 16px;
  font-size: 12px;
  color: var(--tv-text-secondary, #909399);
  text-align: center;
}
</style>
