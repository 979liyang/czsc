<template>
  <div class="screen-scan-page">
    <el-card>
      <template #header>
        <span>全盘扫描</span>
      </template>
      <p class="tip">
        扫描由后端任务执行，结果写入后可在「查看结果」中按交易日查询。
      </p>
      <el-form :model="form" label-width="100px" class="scan-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="交易日">
              <el-date-picker
                v-model="form.tradeDate"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="选择交易日"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务类型">
              <el-select v-model="form.taskType" style="width: 100%">
                <el-option label="按信号" value="signal" />
                <el-option label="按因子" value="factor" />
                <el-option label="第一类买卖点" value="bs1" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="市场">
              <el-select v-model="form.market" placeholder="空为全市场" clearable style="width: 100%">
                <el-option label="上海" value="SH" />
                <el-option label="深圳" value="SZ" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最多股票数">
              <el-input-number v-model="form.maxSymbols" :min="0" :max="5000" placeholder="0=不限制" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" :loading="loadingRun" @click="handleRun">执行扫描</el-button>
          <el-button :loading="loadingResults" @click="handleLoadResults">查看结果</el-button>
          <el-button :loading="loadingRuns" @click="handleLoadRuns">扫描历史</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="error" :title="error" type="error" closable class="mt-4" />
    <el-alert v-if="runMessage" :title="runMessage" type="success" closable class="mt-4" />

    <el-card v-if="results.length" class="mt-4">
      <template #header>筛选结果（共 {{ results.length }} 条）</template>
      <el-table
        :data="sortedTableRows"
        stripe
        max-height="400"
        @sort-change="onSortChange"
      >
        <el-table-column prop="symbol" label="股票" width="120" />
        <el-table-column prop="signal_name" label="信号名" width="100" />
        <el-table-column v-if="isBs1Results" prop="buy1_latest_dt" label="第一买点时间" width="120" sortable="custom">
          <template #default="{ row }">
            {{ (row as ScreenResultRow).buy1_latest_dt ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column v-if="isBs1Results" prop="sell1_latest_dt" label="第一卖点时间" width="120" sortable="custom">
          <template #default="{ row }">
            {{ (row as ScreenResultRow).sell1_latest_dt ?? '—' }}
          </template>
        </el-table-column>
        <el-table-column v-if="!isBs1Results" prop="factor_name" label="因子名" width="140" />
        <el-table-column prop="trade_date" label="交易日" width="100" />
        <el-table-column prop="value_result" label="结果" show-overflow-tooltip />
      </el-table>
    </el-card>

    <el-card v-if="runs.length" class="mt-4">
      <template #header>扫描历史（共 {{ runs.length }} 次）</template>
      <el-table :data="runs" stripe max-height="360">
        <el-table-column prop="id" label="任务 ID" width="90" />
        <el-table-column prop="task_type" label="类型" width="110">
          <template #default="{ row }">
            {{ row.task_type === 'bs1' ? '第一类买卖点' : row.task_type === 'signal' ? '按信号' : '按因子' }}
          </template>
        </el-table-column>
        <el-table-column prop="run_at" label="运行时间" width="200" />
        <el-table-column prop="status" label="状态" width="90" />
        <el-table-column prop="result_count" label="写入条数" width="100" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewRunResults(row.id)">查看该次结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElCard, ElForm, ElFormItem, ElDatePicker, ElSelect, ElOption, ElButton, ElRow, ElCol, ElAlert, ElTable, ElTableColumn, ElInputNumber } from 'element-plus';
import { screenApi } from '../api/screen';
import type { ScreenResultItem, ScreenRunItem } from '../api/screen';

/** BS1 结果 value_result 结构 */
interface Bs1ValueResult {
  buy1_events?: Array<{ dt?: string }>;
  sell1_events?: Array<{ dt?: string }>;
}

/** 带解析后一买/一卖时间的展示行（用于 BS1 排序与列展示） */
interface ScreenResultRow extends ScreenResultItem {
  buy1_latest_dt?: string | null;
  sell1_latest_dt?: string | null;
}

function parseBs1Dt(valueResult: string | null): { buy1: string | null; sell1: string | null } {
  if (!valueResult || !valueResult.trim()) return { buy1: null, sell1: null };
  try {
    const v = JSON.parse(valueResult) as Bs1ValueResult;
    const buy1 = v.buy1_events?.length ? (v.buy1_events[v.buy1_events.length - 1]?.dt ?? null) : null;
    const sell1 = v.sell1_events?.length ? (v.sell1_events[v.sell1_events.length - 1]?.dt ?? null) : null;
    return { buy1, sell1 };
  } catch {
    return { buy1: null, sell1: null };
  }
}

const form = ref({
  tradeDate: '',
  taskType: 'signal' as 'signal' | 'factor' | 'bs1',
  market: '',
  maxSymbols: 0,
});

const loadingRun = ref(false);
const loadingResults = ref(false);
const loadingRuns = ref(false);
const error = ref('');
const runMessage = ref('');
const results = ref<ScreenResultItem[]>([]);
const runs = ref<ScreenRunItem[]>([]);

/** 当前结果是否为 BS1 类型（按 signal_name 判断） */
const isBs1Results = computed(() => {
  const r = results.value;
  return r.length > 0 && r[0].signal_name === 'bs1';
});

/** 扩展为一买/一卖时间的展示行，供表格与排序使用 */
const tableRows = computed<ScreenResultRow[]>(() => {
  return results.value.map((row) => {
    const { buy1, sell1 } = parseBs1Dt(row.value_result);
    return {
      ...row,
      buy1_latest_dt: buy1 ?? undefined,
      sell1_latest_dt: sell1 ?? undefined,
    };
  });
});

/** 表格排序：prop 与 order */
const sortProp = ref<string | null>(null);
const sortOrder = ref<'ascending' | 'descending' | null>(null);

/** 排序后的表格数据 */
const sortedTableRows = computed(() => {
  const rows = tableRows.value;
  const prop = sortProp.value;
  const order = sortOrder.value;
  if (!prop || !order) return rows;
  const key = prop === 'buy1_latest_dt' ? 'buy1_latest_dt' : prop === 'sell1_latest_dt' ? 'sell1_latest_dt' : null;
  if (!key) return rows;
  return [...rows].sort((a, b) => {
    const va = (a as ScreenResultRow)[key as keyof ScreenResultRow] ?? '';
    const vb = (b as ScreenResultRow)[key as keyof ScreenResultRow] ?? '';
    const cmp = String(va).localeCompare(String(vb), undefined, { numeric: true });
    return order === 'ascending' ? cmp : -cmp;
  });
});

function onSortChange({ prop, order }: { prop?: string; order?: string | null }) {
  sortProp.value = prop ?? null;
  sortOrder.value = (order === 'ascending' || order === 'descending' ? order : null) as
    | 'ascending'
    | 'descending'
    | null;
}

function tradeDateNorm(): string {
  const d = form.value.tradeDate;
  if (!d) return '';
  return d.replace(/-/g, '');
}

async function handleRun() {
  const td = tradeDateNorm();
  if (!td) {
    error.value = '请选择交易日';
    return;
  }
  error.value = '';
  runMessage.value = '';
  loadingRun.value = true;
  try {
    const res = await screenApi.run({
      trade_date: td,
      task_type: form.value.taskType,
      market: form.value.market || undefined,
      max_symbols: form.value.maxSymbols || 0,
    });
    runMessage.value = `扫描完成：写入 ${res.count} 条，任务 ID ${res.task_run_id}`;
  } catch (e: unknown) {
    error.value = (e as Error).message || '执行扫描失败';
  } finally {
    loadingRun.value = false;
  }
}

async function handleLoadResults() {
  const td = tradeDateNorm();
  error.value = '';
  loadingResults.value = true;
  try {
    const res = await screenApi.getResults({
      trade_date: td || undefined,
      task_type: form.value.taskType,
      limit: 500,
    });
    results.value = res.items ?? [];
  } catch (e: unknown) {
    error.value = (e as Error).message || '加载结果失败';
    results.value = [];
  } finally {
    loadingResults.value = false;
  }
}

async function handleLoadRuns() {
  error.value = '';
  loadingRuns.value = true;
  try {
    const res = await screenApi.getRuns({ limit: 100, offset: 0 });
    runs.value = res.items ?? [];
  } catch (e: unknown) {
    error.value = (e as Error).message || '加载扫描历史失败';
    runs.value = [];
  } finally {
    loadingRuns.value = false;
  }
}

async function handleViewRunResults(taskRunId: number) {
  error.value = '';
  loadingResults.value = true;
  try {
    const res = await screenApi.getResults({ task_run_id: taskRunId, limit: 0 });
    results.value = res.items ?? [];
  } catch (e: unknown) {
    error.value = (e as Error).message || '加载该次结果失败';
    results.value = [];
  } finally {
    loadingResults.value = false;
  }
}
</script>

<style scoped>
.screen-scan-page {
  padding: 20px;
}
.tip {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin-bottom: 16px;
}
.mt-4 {
  margin-top: 16px;
}
</style>
