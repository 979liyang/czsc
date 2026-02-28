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
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="error" :title="error" type="error" closable class="mt-4" />
    <el-alert v-if="runMessage" :title="runMessage" type="success" closable class="mt-4" />

    <el-card v-if="results.length" class="mt-4">
      <template #header>筛选结果（共 {{ results.length }} 条）</template>
      <el-table :data="results" stripe max-height="400">
        <el-table-column prop="symbol" label="股票" width="120" />
        <el-table-column prop="signal_name" label="信号名" width="180" />
        <el-table-column prop="factor_name" label="因子名" width="140" />
        <el-table-column prop="trade_date" label="交易日" width="100" />
        <el-table-column prop="value_result" label="结果" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { ElCard, ElForm, ElFormItem, ElDatePicker, ElSelect, ElOption, ElButton, ElRow, ElCol, ElAlert, ElTable, ElTableColumn, ElInputNumber } from 'element-plus';
import { screenApi } from '../api/screen';
import type { ScreenResultItem } from '../api/screen';

const form = ref({
  tradeDate: '',
  taskType: 'signal' as 'signal' | 'factor',
  market: '',
  maxSymbols: 0,
});

const loadingRun = ref(false);
const loadingResults = ref(false);
const error = ref('');
const runMessage = ref('');
const results = ref<ScreenResultItem[]>([]);

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
