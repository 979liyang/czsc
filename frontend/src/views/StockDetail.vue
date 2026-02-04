<!--
  股票详情页 - 性能优化版本
  
  性能优化说明：
  - 只支持 30分钟、60分钟、日线 三个周期（移除 1,5,15 分钟以提升性能）
  - 按需加载：用户选择哪个周期才请求哪个周期的数据
  - 周期缓存：已加载的周期数据会缓存，切换周期时如果已缓存则直接显示
  - 单周期请求：每次只请求一个周期的数据，减少服务器计算负担
-->
<template>
  <div class="stock-detail-page">
    <!-- 头部信息 -->
    <el-card class="header-card">
      <div class="header-content">
        <h2>{{ symbol }}</h2>
        <div class="header-actions">
          <el-form :inline="true" class="filter-form">
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
      <el-alert
        v-if="store.loading"
        type="info"
        :closable="false"
        :title="`正在加载${store.activeFreq}数据...`"
        class="mt-4"
      />
    </div>

    <!-- 错误提示 -->
    <div v-if="store.error" class="error-container">
      <el-alert :title="store.error" type="error" :closable="false" />
    </div>

    <!-- 主要内容 -->
    <div v-if="!store.loading && !store.error && store.localCzsc">
      <el-alert
        v-if="itemsKeys.length === 0"
        class="mb-4"
        type="warning"
        :closable="false"
        title="当前时间范围内没有读取到本地数据"
        description="请确认本地存在 .stock_data/raw/minute_by_stock 的 parquet；或尝试 demo：600078.SH；或将开始时间设为 20180101。"
      />

      <!-- 统计信息区域（含周期切换） -->
      <el-card class="stats-card">
        <template #header>
          <span>分析统计</span>
        </template>
        <el-tabs v-model="store.activeFreq" class="mb-4">
          <el-tab-pane
            v-for="f in availableFreqs"
            :key="f"
            :label="f"
            :name="f"
          />
        </el-tabs>

        <el-card v-if="store.localCzsc?.meta" class="mb-4" shadow="never">
          <template #header>
            <span>数据元信息</span>
          </template>
          <el-alert
            type="info"
            :closable="false"
            class="mb-4"
            title="时间范围说明"
            description="K线数据仅显示最近3个月，但分型和笔分析基于全量历史数据，确保分析准确性。"
          />
          <div class="meta-grid">
            <div class="meta-item">
              <span class="meta-label">parquet 命中：</span>
              <span class="meta-value">{{ store.localCzsc.meta.parquet_count }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">行数（过滤前/后）：</span>
              <span class="meta-value">
                {{ store.localCzsc.meta.rows_before_filter }} / {{ store.localCzsc.meta.rows_after_filter }}
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">period 过滤：</span>
              <span class="meta-value">{{ store.localCzsc.meta.period_filtered ? '是(仅1分钟)' : '否' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">dt 范围：</span>
              <span class="meta-value">{{ store.localCzsc.meta.dt_min || '-' }} ~ {{ store.localCzsc.meta.dt_max || '-' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">base_freq：</span>
              <span class="meta-value">{{ store.localCzsc.meta.base_freq }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">输出周期：</span>
              <span class="meta-value">{{ (store.localCzsc.meta.target_freqs || []).join(', ') || '-' }}</span>
            </div>
            <div class="meta-item meta-item-full">
              <span class="meta-label">bars 数量：</span>
              <span class="meta-value">{{ formatBarCounts(store.localCzsc.meta.generated_bar_counts) }}</span>
            </div>
            <div v-if="activeItem" class="meta-item meta-item-full">
              <span class="meta-label">K线数据时间范围：</span>
              <span class="meta-value">最近3个月（{{ activeItem.bars?.length || 0 }}条）</span>
            </div>
            <div v-if="activeItem" class="meta-item meta-item-full">
              <span class="meta-label">分析数据时间范围：</span>
              <span class="meta-value">全量历史数据（分型{{ activeItem.fxs?.length || 0 }}条，笔{{ activeItem.bis?.length || 0 }}条）</span>
            </div>
            <div v-if="(store.localCzsc.meta.warnings || []).length" class="meta-item meta-item-full">
              <span class="meta-label">warnings：</span>
              <span class="meta-value">{{ (store.localCzsc.meta.warnings || []).join('；') }}</span>
            </div>
          </div>
        </el-card>

        <el-alert
          v-if="itemsKeys.length > 0 && !activeItem"
          type="warning"
          :closable="false"
          title="当前周期没有返回数据"
          description="可尝试切换到其他分钟周期，或扩大时间范围（建议 sdt=20180101）。"
          class="mb-4"
        />

        <div v-if="activeItem" class="stats-grid">
          <div class="stat-item">
            <span class="stat-label">原始K线数量：</span>
            <span class="stat-value">{{ activeItem.stats?.bars_raw_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未完成笔的K线数量：</span>
            <span class="stat-value">{{ activeItem.stats?.bars_ubi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">分型数量：</span>
            <span class="stat-value">{{ activeItem.stats?.fx_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成笔数量：</span>
            <span class="stat-value">{{ activeItem.stats?.finished_bi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">所有笔数量：</span>
            <span class="stat-value">{{ activeItem.stats?.bi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未完成笔数量：</span>
            <span class="stat-value">{{ activeItem.stats?.ubi_count || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔是否延伸：</span>
            <span class="stat-value">{{ activeItem.stats?.last_bi_extend ? '是' : '否' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔方向：</span>
            <span class="stat-value">{{ activeItem.stats?.last_bi_direction || '-' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最后一笔幅度：</span>
            <span class="stat-value">
              {{ activeItem.stats?.last_bi_power ? activeItem.stats.last_bi_power.toFixed(2) : '-' }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- 图表区域 -->
      <el-card v-if="activeItem" class="chart-card">
        <template #header>
          <span>K线图表（{{ store.activeFreq }}）</span>
        </template>
        <KlineChartTradingVue :item="activeItem" :meta="store.localCzsc?.meta" />
      </el-card>

      <!-- 分型和笔列表区域 -->
      <el-row v-if="activeItem" :gutter="20">
        <el-col :span="12">
          <el-card class="list-card">
            <template #header>
              <span>分型列表</span>
            </template>
            <FxList :fxs="activeItem.fxs || []" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="list-card">
            <template #header>
              <span>笔列表</span>
            </template>
            <BiList :bis="activeItem.bis || []" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Refresh } from '@element-plus/icons-vue';
import { useStockDetailStore } from '../stores';
import KlineChartTradingVue from '../components/KlineChartTradingVue.vue';
import BiList from '../components/BiList.vue';
import FxList from '../components/FxList.vue';
// 导入 mock 数据
import { data as mockData } from '../mockdata/index';

const route = useRoute();
const store = useStockDetailStore();

// 从路由参数获取股票代码
const symbol = computed(() => {
  return (route.params.symbol as string) || '';
});

// 表单数据
const form = ref({
  sdt: '',
  edt: '',
});

// 可用周期列表：只支持 30分钟、60分钟、日线（性能优化）
const availableFreqs = ['30分钟', '60分钟', '日线'];
// const defaultBaseFreq = '1分钟'; // 暂时不使用，因为使用 mock 数据

// 获取默认时间范围
const getDefaultDateRange = () => {
  const today = new Date();
  const edt = today.toISOString().split('T')[0];
  const sdt = '2018-01-01';
  return { sdt, edt };
};

// 初始化表单默认值
const initForm = () => {
  const { sdt, edt } = getDefaultDateRange();
  form.value.sdt = sdt;
  form.value.edt = edt;
};

// 刷新当前激活周期的数据（使用默认的 recent_months=3）
// 暂时使用 mock 数据，不请求接口
const handleRefresh = async () => {
  // 使用 mock 数据
  loadMockData();
  
  // 如果需要请求接口，取消下面的注释
  // if (symbol.value && form.value.sdt && form.value.edt) {
  //   const sdt = form.value.sdt.replace(/-/g, '');
  //   const edt = form.value.edt.replace(/-/g, '');
  //   await store.fetchSingleFreq(symbol.value, sdt, edt, store.activeFreq, defaultBaseFreq, 0, 0, 0, 0, 0, 0, false, 3);
  // }
};

// 日期变更：只刷新当前激活周期的数据
const handleDateChange = async () => {
  if (form.value.sdt && form.value.edt) {
    await handleRefresh();
  }
};

// 从当前周期的缓存中获取数据（确保只显示当前激活周期的数据）
const activeItem = computed(() => {
  const data = store.localCzsc;
  if (!data) return null;
  const item = data.items?.[store.activeFreq] || null;
  // 验证数据一致性：确保返回的是当前激活周期的数据
  if (item && item.freq !== store.activeFreq) {
    console.warn(
      `[StockDetail] 数据不一致: activeFreq=${store.activeFreq} item.freq=${item.freq}`,
      { data, activeFreq: store.activeFreq }
    );
  }
  return item;
});

// itemsKeys 只返回当前激活周期的 key（用于调试和验证）
const itemsKeys = computed(() => {
  const data = store.localCzsc;
  if (!data) return [];
  const keys = Object.keys(data?.items || {});
  // 验证：如果 items 包含多个周期，记录警告
  if (keys.length > 1) {
    console.warn(
      `[StockDetail] items 包含多个周期: ${keys.join(', ')} 当前激活周期: ${store.activeFreq}`,
      { items: data.items, activeFreq: store.activeFreq }
    );
  }
  // 只返回当前激活周期的 key（确保一致性）
  return keys.filter((k) => k === store.activeFreq);
});

// 加载 mock 数据到 store
const loadMockData = () => {
  // 将 mock 数据设置到 store 的缓存中
  const freq = '30分钟'; // mock 数据中的周期
  const cacheItem = {
    data: mockData as any,
    sdt: mockData.sdt,
    edt: mockData.edt,
    pagination: mockData.pagination?.[freq] ? {
      bars: {
        loaded: mockData.pagination[freq].bars.returned,
        total: mockData.pagination[freq].bars.total
      },
      fxs: {
        loaded: mockData.pagination[freq].fxs.returned,
        total: mockData.pagination[freq].fxs.total
      },
      bis: {
        loaded: mockData.pagination[freq].bis.returned,
        total: mockData.pagination[freq].bis.total
      }
    } : undefined
  };
  
  // 设置到 store 的缓存中
  // Pinia store 会自动解包 ref，但 localCzscCache 是 Map，需要访问 .value
  store.localCzscCache.set(freq, cacheItem);
  
  // 设置当前激活周期
  store.activeFreq = freq;
  
  // 设置 symbol
  store.symbol = mockData.symbol;
  
  console.log('[StockDetail] Mock 数据已加载', { 
    freq, 
    symbol: mockData.symbol,
    items: Object.keys(mockData.items || {}),
    barsCount: mockData.items?.[freq]?.bars?.length || 0
  });
};

// 监听周期切换，按需加载数据（确保只加载对应周期，使用默认的 recent_months=3）
// 暂时使用 mock 数据，不请求接口
watch(
  () => store.activeFreq,
  async (newFreq, oldFreq) => {
    console.log(`[StockDetail] 周期切换: ${oldFreq} -> ${newFreq}`);
    
    // 使用 mock 数据
    loadMockData();
    
    // 如果需要请求接口，取消下面的注释
    // if (!symbol.value || !form.value.sdt || !form.value.edt) return;
    // 
    // // 检查缓存
    // const sdt = form.value.sdt.replace(/-/g, '');
    // const edt = form.value.edt.replace(/-/g, '');
    // const cacheItem = store.localCzscCache.get(newFreq);
    // 
    // if (cacheItem && cacheItem.sdt === sdt && cacheItem.edt === edt) {
    //   // 缓存有效，直接使用
    //   console.log(`[StockDetail] 使用缓存: ${newFreq} 缓存周期=${Object.keys(cacheItem.data.items || {}).join(', ')}`);
    //   return;
    // }
    // 
    // // 缓存无效或不存在，请求数据（只请求当前激活周期，K线数据只返回最近3个月）
    // console.log(`[StockDetail] 加载周期数据: ${newFreq} sdt=${sdt} edt=${edt} recent_months=3`);
    // try {
    //   const result = await store.fetchSingleFreq(symbol.value, sdt, edt, newFreq, defaultBaseFreq, 0, 0, 0, 0, 0, 0, false, 3);
    //   console.log(
    //     `[StockDetail] 周期数据加载完成: ${newFreq} 返回周期=${Object.keys(result.items || {}).join(', ')}`
    //   );
    // } catch (err) {
    //   console.error(`[StockDetail] 加载周期数据失败: ${newFreq}`, err);
    // }
  }
);

// 监听数据变化，记录日志
watch(
  () => store.localCzsc,
  () => {
    const data = store.localCzsc;
    if (!data) return;
    if (itemsKeys.value.length === 0) {
      console.warn('[StockDetail] local_czsc 返回 items 为空', {
        symbol: symbol.value,
        sdt: form.value.sdt,
        edt: form.value.edt,
        activeFreq: store.activeFreq,
        meta: data.meta,
      });
      return;
    }
    if (!activeItem.value || (activeItem.value.bars || []).length === 0) {
      console.warn('[StockDetail] 当前周期 bars 为空', {
        symbol: symbol.value,
        sdt: form.value.sdt,
        edt: form.value.edt,
        activeFreq: store.activeFreq,
        itemsKeys: itemsKeys.value,
        meta: data.meta,
      });
    }
  },
  { deep: true }
);

const formatBarCounts = (counts: Record<string, number> | undefined) => {
  if (!counts) return '-';
  const keys = Object.keys(counts);
  if (keys.length === 0) return '-';
  return keys
    .sort()
    .map((k) => `${k}:${counts[k]}`)
    .join(', ');
};

// 组件挂载时加载 mock 数据
onMounted(async () => {
  if (symbol.value) {
    initForm();
    // 使用 mock 数据，不请求接口
    loadMockData();
    
    // 如果需要请求接口，取消下面的注释
    // const sdt = form.value.sdt.replace(/-/g, '');
    // const edt = form.value.edt.replace(/-/g, '');
    // await store.fetchSingleFreq(symbol.value, sdt, edt, '30分钟', defaultBaseFreq, 0, 0, 0, 0, 0, 0, false, 3);
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
