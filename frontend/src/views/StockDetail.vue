<!--
  股票详情页：K 线 + 麒麟分析，支持 30/60 分钟、日线 tab，切换时请求对应周期数据。
-->
<template>
  <div class="stock-detail-page">
    <header class="page-header">
      <h1 class="symbol-title">{{ symbol }}</h1>
      <div class="toolbar">
        <el-date-picker
          v-model="form.sdt"
          type="date"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          placeholder="开始"
          size="small"
          style="width: 120px"
          @change="handleDateChange"
        />
        <el-date-picker
          v-model="form.edt"
          type="date"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          placeholder="结束"
          size="small"
          style="width: 120px"
          @change="handleDateChange"
        />
        <el-button size="small" :loading="store.loading" @click="handleRefresh">刷新</el-button>
      </div>
    </header>

    <el-tabs v-model="store.activeFreq" type="card" class="freq-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="30分钟" name="30分钟" />
      <el-tab-pane label="60分钟" name="60分钟" />
      <el-tab-pane label="日线" name="日线" />
    </el-tabs>

    <div v-if="store.loading" class="loading-state">加载中...</div>
    <div v-else-if="store.error" class="error-state">{{ store.error }}</div>
    <div v-else-if="chartItem" class="chart-wrap">
      <KlineChart
        :symbol="symbol"
        :freq="chartItem.freq"
        :bars="chartItem.bars"
        :fxs="chartItem.fxs || []"
        :bis="chartItem.bis || []"
      />
    </div>
    <div v-else class="empty-state">
      暂无数据，请选择时间范围后点击刷新，或确认本地有该股票的分钟数据。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useStockDetailStore } from '../stores';
import KlineChart from '../components/KlineChart.vue';

const route = useRoute();
const store = useStockDetailStore();

const symbol = computed(() => (route.params.symbol as string) || '');

const form = ref({ sdt: '2018-01-01', edt: '' });

function getDefaultEdt() {
  return new Date().toISOString().split('T')[0];
}

function initForm() {
  if (!form.value.edt) form.value.edt = getDefaultEdt();
}

async function doFetch() {
  if (!symbol.value) return;
  initForm();
  const sdt = form.value.sdt.replace(/-/g, '');
  const edt = form.value.edt.replace(/-/g, '');
  await store.fetchSingleFreq(
    symbol.value,
    sdt,
    edt,
    store.activeFreq,
    '1分钟',
    0, 0, 0, 0, 0, 0,
    false,
    3
  );
}

function handleRefresh() {
  doFetch();
}

function handleDateChange() {
  if (form.value.sdt && form.value.edt) doFetch();
}

function handleTabChange(name: string) {
  store.activeFreq = name;
  if (form.value.sdt && form.value.edt) doFetch();
}

const chartItem = computed(() => {
  const data = store.localCzsc;
  if (!data?.items) return null;
  return data.items[store.activeFreq] || null;
});

watch(symbol, () => {
  if (symbol.value && form.value.sdt && form.value.edt) doFetch();
});

onMounted(() => {
  initForm();
  if (symbol.value) doFetch();
});
</script>

<style scoped>
.stock-detail-page {
  padding: 12px;
  background: #1f212d;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
}

.symbol-title {
  margin: 0;
  font-size: 20px;
  color: #e0e0e0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.freq-tabs {
  margin-bottom: 12px;
}
.freq-tabs :deep(.el-tabs__header) {
  margin: 0;
}
.freq-tabs :deep(.el-tabs__item),
.freq-tabs :deep(.el-tabs__nav) {
  color: #e0e0e0;
  border-color: #4a4d5c;
}
.freq-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
}
.freq-tabs :deep(.el-tabs__item:hover) {
  color: #409eff;
}
.freq-tabs :deep(.el-tabs__content) {
  display: none;
}
.freq-tabs :deep(.el-tabs__nav-wrap::after) {
  background: #4a4d5c;
}
.freq-tabs :deep(.el-tabs__active-bar) {
  background: #409eff;
}
.freq-tabs :deep(.el-tabs__ink-bar) {
  background: #409eff;
}

.chart-wrap {
  background: #1f212d;
  border-radius: 4px;
  overflow: hidden;
  min-height: 580px;
}

.loading-state,
.error-state,
.empty-state {
  padding: 40px;
  text-align: center;
  color: #909399;
  background: #1f212d;
}
.error-state {
  color: #f56c6c;
}
</style>
