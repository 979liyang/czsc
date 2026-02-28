<template>
  <div class="watchlist-page">
    <h2>自选股</h2>
    <div class="add-row">
      <SymbolSelect
        v-model="selectedSymbol"
        placeholder="搜索或选择股票（代码/名称）"
        width="320px"
      />
      <el-button type="primary" :loading="adding" :disabled="!selectedSymbol" @click="onAdd">添加</el-button>
    </div>
    <div v-if="watchlistStore.error" class="error-msg">{{ watchlistStore.error }}</div>
    <el-table :data="watchlistStore.items" stripe style="width: 100%; max-width: 720px">
      <el-table-column prop="symbol" label="代码" width="120" />
      <el-table-column prop="name" label="名称" width="100" show-overflow-tooltip />
      <el-table-column label="最新价" width="90" align="right">
        <template #default="{ row }">
          {{ formatPrice(row.latest_price) }}
        </template>
      </el-table-column>
      <el-table-column label="涨跌" width="90" align="right">
        <template #default="{ row }">
          <span :class="changeClass(row.change)">{{ formatChange(row.change) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="涨跌%" width="90" align="right">
        <template #default="{ row }">
          <span :class="changeClass(row.change_pct)">{{ formatChangePct(row.change_pct) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" link @click="onRemove(row.symbol)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="!watchlistStore.loading && watchlistStore.items.length === 0" class="empty-tip">
      暂无自选股，请输入代码添加
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useWatchlistStore } from '../stores/watchlist';

defineOptions({ name: 'WatchlistPage' });
import SymbolSelect from '../components/SymbolSelect.vue';

const watchlistStore = useWatchlistStore();
const selectedSymbol = ref<string | null>(null);
const adding = ref(false);

async function doAdd(symbol: string) {
  if (!symbol?.trim()) return;
  adding.value = true;
  try {
    await watchlistStore.add(symbol.trim());
    selectedSymbol.value = null;
  } catch {
    // error 已在 store 中
  } finally {
    adding.value = false;
  }
}

function onAdd() {
  if (selectedSymbol.value) doAdd(selectedSymbol.value);
}

function onRemove(symbol: string) {
  watchlistStore.remove(symbol);
}

function formatPrice(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '—';
  return Number(v).toFixed(2);
}

function formatChange(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '—';
  const n = Number(v);
  const prefix = n >= 0 ? '+' : '';
  return prefix + n.toFixed(2);
}

function formatChangePct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '—';
  const n = Number(v);
  const prefix = n >= 0 ? '+' : '';
  return prefix + n.toFixed(2) + '%';
}

function changeClass(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '';
  return Number(v) >= 0 ? 'text-up' : 'text-down';
}

onMounted(() => {
  watchlistStore.load();
});
</script>

<style scoped>
.watchlist-page {
  padding: 16px;
}
.add-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.error-msg {
  color: var(--el-color-danger);
  font-size: 12px;
  margin-bottom: 8px;
}
.empty-tip {
  margin-top: 16px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.text-up {
  color: var(--el-color-danger);
}
.text-down {
  color: var(--el-color-success);
}
</style>
