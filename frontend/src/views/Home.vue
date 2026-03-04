<template>
  <div class="h-[100vh] flex flex-col bg-[#1f212d]">
    <div class="flex items-center justify-between px-3 py-2 bg-[#262a35] border-b border-[#363a45] shrink-0">
    </div>
    <div class="flex flex-1 min-h-0">
      <div class="chart-area flex-1 min-w-0 min-h-0">
        <TradingViewChart />
      </div>
      <aside class="panel w-[320px] shrink-0 overflow-y-auto bg-[#262a35] border-l border-[#363a45] p-4">
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useWatchlistStore } from '../stores/watchlist';
import TradingViewChart from './TradingViewChart.vue';

const watchlistStore = useWatchlistStore();

onMounted(() => {
  watchlistStore.load();
});
</script>

<style scoped>
.home-page {
  padding: 20px;
}

.welcome-content {
  text-align: center;
}

.welcome-content h3 {
  margin-top: 0;
}

.welcome-content p {
  color: #606266;
  margin-top: 10px;
}

.watchlist-quick {
  margin-bottom: 16px;
  font-size: 14px;
}
.watchlist-quick .label {
  color: var(--el-text-color-secondary);
  margin-right: 8px;
}
.symbol-link {
  margin-right: 12px;
  color: var(--el-color-primary);
}
.manage-link {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
