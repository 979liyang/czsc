<template>
  <div class="stock-detail-page">
    <!-- 头部信息 -->
    <el-card class="header-card">
      <div class="header-content">
        <h2>{{ symbol }}</h2>
        <div class="header-actions">
          <el-form :inline="true" class="filter-form">
            <el-form-item label="周期">
              <el-select v-model="form.freq" style="width: 120px" @change="handleFreqChange">
                <el-option label="日线" value="日线" />
                <el-option label="30分钟" value="30分钟" />
                <el-option label="60分钟" value="60分钟" />
                <el-option label="周线" value="周线" />
                <el-option label="月线" value="月线" />
              </el-select>
            </el-form-item>
            <el-form-item label="开始时间">
              <el-date-picker
                v-model="form.sdt"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择开始时间"
                style="width: 150px"
                @change="handleDateChange"
              />
            </el-form-item>
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="form.edt"
                type="date"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                placeholder="选择结束时间"
                style="width: 150px"
                @change="handleDateChange"
              />
            </el-form-item>
            <el-form-item>
              <el-button @click="handleRefresh" :loading="store.loading" :icon="Refresh">
                刷新
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-card>

    <!-- 加载状态 -->
    <div v-if="store.loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 错误提示 -->
    <div v-if="store.error" class="error-container">
      <el-alert :title="store.error" type="error" :closable="false" />
    </div>

    <!-- 主要内容 -->
    <div v-if="!store.loading && !store.error && store.analysisData">
      <!-- 图表区域 -->
      <el-card class="chart-card">
        <template #header>
          <span>K线图表</span>
        </template>
        <KlineChartTradingVue
          v-if="store.analysisData"
          :data="store.analysisData"
          :symbol="symbol"
        />
      </el-card>

      <!-- 统计信息区域 -->
      <el-card class="stats-card">
        <template #header>
          <span>分析统计</span>
        </template>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">原始K线数量：</span>
            <span class="stat-value">{{ store.analysisData.bars_raw_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未完成笔的K线数量：</span>
            <span class="stat-value">{{ store.analysisData.bars_ubi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">分型数量：</span>
            <span class="stat-value">{{ store.analysisData.fx_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成笔数量：</span>
            <span class="stat-value">{{ store.analysisData.finished_bi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">所有笔数量：</span>
            <span class="stat-value">{{ store.analysisData.bi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未完成笔数量：</span>
            <span class="stat-value">{{ store.analysisData.ubi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔是否延伸：</span>
            <span class="stat-value">{{ store.analysisData.last_bi_extend ? '是' : '否' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔方向：</span>
            <span class="stat-value">{{ store.analysisData.last_bi_direction || '-' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔幅度：</span>
            <span class="stat-value">
              {{ store.analysisData.last_bi_power ? store.analysisData.last_bi_power.toFixed(2) : '-' }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- 分型和笔列表区域 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="list-card">
            <template #header>
              <span>分型列表</span>
            </template>
            <FxList :fxs="store.analysisData.fxs || []" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="list-card">
            <template #header>
              <span>笔列表</span>
            </template>
            <BiList :bis="store.analysisData.bis || []" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import { useRoute } from 'vue-router';
import { Refresh } from '@element-plus/icons-vue';
import { useStockDetailStore } from '../stores';
import KlineChartTradingVue from '../components/KlineChartTradingVue.vue';
import BiList from '../components/BiList.vue';
import FxList from '../components/FxList.vue';

const route = useRoute();
const store = useStockDetailStore();

// 从路由参数获取股票代码
const symbol = computed(() => {
  return (route.params.symbol as string) || '';
});

// 表单数据
const form = ref({
  freq: '日线',
  sdt: '',
  edt: '',
});

// 获取默认时间范围
const getDefaultDateRange = () => {
  const today = new Date();
  const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
  const sdt = oneYearAgo.toISOString().split('T')[0];
  const edt = today.toISOString().split('T')[0];
  return { sdt, edt };
};

// 初始化表单默认值
const initForm = () => {
  const { sdt, edt } = getDefaultDateRange();
  form.value.sdt = sdt;
  form.value.edt = edt;
};

// 刷新数据
const handleRefresh = () => {
  if (symbol.value && form.value.sdt && form.value.edt) {
    const sdt = form.value.sdt.replace(/-/g, '');
    const edt = form.value.edt.replace(/-/g, '');
    
    store.fetchAnalysis({
      symbol: symbol.value,
      freq: form.value.freq,
      sdt,
      edt,
    });
  }
};

// 周期变更
const handleFreqChange = () => {
  handleRefresh();
};

// 日期变更
const handleDateChange = () => {
  if (form.value.sdt && form.value.edt) {
    handleRefresh();
  }
};

// 组件挂载时获取数据
onMounted(() => {
  if (symbol.value) {
    initForm();
    handleRefresh();
  }
});
</script>

<style scoped>
.stock-detail-page {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-form {
  margin: 0;
}

.header-content h2 {
  margin: 0;
  font-size: 24px;
}

.loading-container,
.error-container {
  margin: 20px 0;
}

.chart-card,
.stats-card,
.list-card {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  font-weight: 500;
  color: #606266;
}

.stat-value {
  font-weight: 600;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-form {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .el-col {
    margin-bottom: 20px;
  }
}
</style>
