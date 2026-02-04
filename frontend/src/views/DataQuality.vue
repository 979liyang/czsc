<template>
  <div style="padding: 20px">
    <el-card>
      <template #header>
        <span>数据质量（分钟数据覆盖/缺口）</span>
      </template>

      <el-form :inline="true" @submit.prevent>
        <el-form-item label="市场">
          <el-select v-model="market" clearable placeholder="SH / SZ" style="width: 120px">
            <el-option label="SH" value="SH" />
            <el-option label="SZ" value="SZ" />
          </el-select>
        </el-form-item>

        <el-form-item label="股票">
          <SymbolSelect v-model="symbol" :market="market || null" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="loadCoverage">查询覆盖概况</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>覆盖概况</span>
      </template>

      <el-table :data="items" v-loading="loading" style="width: 100%">
        <el-table-column prop="symbol" label="代码" width="120" />
        <el-table-column prop="name" label="中文名" width="120" />
        <el-table-column prop="market" label="市场" width="80" />
        <el-table-column prop="start_dt" label="开始时间" />
        <el-table-column prop="end_dt" label="结束时间" />
        <el-table-column prop="last_scan_at" label="最近扫描" />
      </el-table>

      <div style="margin-top: 12px; display: flex; justify-content: flex-end">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :total="total"
          :page-size="pageSize"
          :current-page="pageNo"
          @current-change="onPageChange"
        />
      </div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>缺口查询</span>
      </template>

      <el-form :inline="true" @submit.prevent>
        <el-form-item label="股票">
          <el-input v-model="gapSymbol" placeholder="如 000001.SZ" style="width: 200px" />
        </el-form-item>
        <el-form-item label="交易日">
          <el-date-picker v-model="gapDate" type="date" value-format="YYYY-MM-DD" style="width: 180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="gapLoading" @click="loadGaps">查询缺口</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="gaps" v-loading="gapLoading" style="width: 100%; margin-top: 10px">
        <el-table-column prop="start" label="缺口开始" />
        <el-table-column prop="end" label="缺口结束" />
        <el-table-column prop="minutes" label="缺口分钟数" width="120" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import {
  ElCard,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElButton,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElInput,
  ElDatePicker,
} from 'element-plus';
import SymbolSelect from '../components/SymbolSelect.vue';
import { dataQualityApi, type CoverageItem, type GapItem } from '../api/data_quality';

const market = ref<string | null>(null);
const symbol = ref<string | null>(null);

const loading = ref(false);
const items = ref<CoverageItem[]>([]);
const total = ref(0);
const pageNo = ref(1);
const pageSize = ref(200);

const gapLoading = ref(false);
const gapSymbol = ref<string>('');
const gapDate = ref<string>('');
const gaps = ref<GapItem[]>([]);

const loadCoverage = async () => {
  loading.value = true;
  try {
    const offset = (pageNo.value - 1) * pageSize.value;
    const res = await dataQualityApi.getCoverage({
      symbol: symbol.value,
      market: market.value,
      offset,
      limit: pageSize.value,
    });
    items.value = res.items || [];
    total.value = res.count || 0;
  } finally {
    loading.value = false;
  }
};

const onPageChange = (p: number) => {
  pageNo.value = p;
  loadCoverage().catch(() => {});
};

const loadGaps = async () => {
  if (!gapSymbol.value || !gapDate.value) return;
  gapLoading.value = true;
  try {
    const res = await dataQualityApi.getGaps({ symbol: gapSymbol.value, trade_date: gapDate.value });
    gaps.value = res.gaps || [];
  } finally {
    gapLoading.value = false;
  }
};

onMounted(() => {
  loadCoverage().catch(() => {});
});
</script>

