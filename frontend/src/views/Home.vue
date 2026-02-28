<template>
  <div class="home-page">
    <el-card v-if="false">
      <template #header>
        <h2>Kylin Trading Pro分析系统</h2>
      </template>
      <div class="welcome-content">
        <p>欢迎使用Kylin Trading Pro分析系统！</p>
        <div v-if="watchlistStore.symbols.length" class="watchlist-quick">
          <span class="label">自选股：</span>
          <router-link
            v-for="s in watchlistStore.symbols"
            :key="s"
            :to="`/stock/${s}`"
            class="symbol-link"
          >{{ s }}</router-link>
          <router-link to="/watchlist" class="manage-link">管理</router-link>
        </div>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/analysis')">
              <h3>麒麟分析</h3>
              <p>通过Web界面进行麒麟分析，查看分型、笔、中枢</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/signals')">
              <h3>信号函数</h3>
              <p>查看和学习所有信号函数的说明和使用方法</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/examples')">
              <h3>策略示例</h3>
              <p>查看和学习更多策略示例代码</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/signal-analyze')">
              <h3>信号分析</h3>
              <p>按类型添加信号，对单只股票计算多信号（支持每信号不同周期）</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/screen')">
              <h3>全盘扫描</h3>
              <p>按信号或因子条件扫描全市场，查看满足条件的股票</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/strategy-analyze')">
              <h3>策略分析</h3>
              <p>选择策略与参数，对单只股票运行回测并查看绩效与操作记录</p>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" @click="$router.push('/tv')">
              <h3>TradingView 图表</h3>
              <p>使用 Charting Library 展示本地 `.stock_data` K线，并可叠加 SMC</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { ElCard, ElRow, ElCol } from 'element-plus';
import { useRouter } from 'vue-router';
import { useWatchlistStore } from '../stores/watchlist';

const router = useRouter();
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
