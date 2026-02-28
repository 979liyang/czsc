<template>
  <div class="data-fetch-page">
    <el-card>
      <template #header>
        <span>数据拉取</span>
      </template>
      <p class="desc">
        日线拉取用于更新股票日 K 数据，分钟拉取用于更新 1 分钟 K 线数据，指数拉取用于更新指数日线。任务在后台执行，可在下方查看运行记录与状态。
      </p>

      <div class="actions">
        <div class="action-group">
          <el-button type="primary" :loading="dailyLoading" @click="onTrigger('daily')">
            拉取日线
          </el-button>
          <el-tag v-if="todayDailySuccess" type="success" size="small">今日已执行</el-tag>
        </div>
        <div class="action-group">
          <el-button type="primary" :loading="minuteLoading" @click="onTrigger('minute')">
            拉取分钟
          </el-button>
          <el-tag v-if="todayMinuteSuccess" type="success" size="small">今日已执行</el-tag>
        </div>
        <div class="action-group">
          <el-button type="primary" :loading="indexLoading" @click="onTrigger('index')">
            拉取指数
          </el-button>
          <el-tag v-if="todayIndexSuccess" type="success" size="small">今日已执行</el-tag>
        </div>
      </div>
    </el-card>

    <el-card class="table-card">
      <template #header>
        <span>运行记录</span>
      </template>
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="类型">
          <el-select v-model="filterTaskType" clearable placeholder="全部" style="width: 120px">
            <el-option label="日线" value="daily" />
            <el-option label="分钟" value="minute" />
            <el-option label="指数" value="index" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="filterDate"
            type="date"
            value-format="YYYY-MM-DD"
            clearable
            placeholder="全部"
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRuns">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="runs" v-loading="runsLoading" style="width: 100%">
        <el-table-column prop="task_type" label="任务类型" width="100">
          <template #default="{ row }">
            {{ taskTypeLabel(row.task_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="trigger" label="触发方式" width="100">
          <template #default="{ row }">
            {{ row.trigger === 'manual' ? '手动' : '定时' }}
          </template>
        </el-table-column>
        <el-table-column prop="run_at" label="运行时间" width="180" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="summary" label="摘要" min-width="120" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { ElCard, ElButton, ElTag, ElForm, ElFormItem, ElSelect, ElOption, ElTable, ElTableColumn, ElDatePicker } from 'element-plus';
import { triggerFetch, getRuns, type DataFetchRunResponse } from '../api/dataFetch';

defineOptions({ name: 'DataFetch' });

const dailyLoading = ref(false);
const minuteLoading = ref(false);
const indexLoading = ref(false);
const runsLoading = ref(false);
const runs = ref<DataFetchRunResponse[]>([]);
const filterTaskType = ref<string | null>(null);
const filterDate = ref<string | null>(null);

const today = computed(() => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
});

const todayDailySuccess = ref(false);
const todayMinuteSuccess = ref(false);
const todayIndexSuccess = ref(false);

function taskTypeLabel(t: string) {
  const map: Record<string, string> = { daily: '日线', minute: '分钟', index: '指数' };
  return map[t] ?? t;
}

async function loadTodaySuccess() {
  try {
    const list = await getRuns({ limit: 10, date: today.value });
    todayDailySuccess.value = list.some((r) => r.task_type === 'daily' && r.status === 'success');
    todayMinuteSuccess.value = list.some((r) => r.task_type === 'minute' && r.status === 'success');
    todayIndexSuccess.value = list.some((r) => r.task_type === 'index' && r.status === 'success');
  } catch {
    // ignore
  }
}

function statusText(s: string) {
  const map: Record<string, string> = { running: '运行中', success: '成功', failed: '失败' };
  return map[s] ?? s;
}
function statusTagType(s: string) {
  const map: Record<string, string> = { running: 'warning', success: 'success', failed: 'danger' };
  return map[s] ?? 'info';
}

async function loadRuns() {
  runsLoading.value = true;
  try {
    const params: { task_type?: string; limit: number; date?: string } = { limit: 20 };
    if (filterTaskType.value) params.task_type = filterTaskType.value;
    if (filterDate.value) params.date = filterDate.value;
    runs.value = await getRuns(params);
    await loadTodaySuccess();
  } finally {
    runsLoading.value = false;
  }
}

async function onTrigger(taskType: 'daily' | 'minute' | 'index') {
  const loadingRef =
    taskType === 'daily' ? dailyLoading : taskType === 'minute' ? minuteLoading : indexLoading;
  loadingRef.value = true;
  try {
    const res = await triggerFetch(taskType);
    await loadRuns();
    const runId = res.run_id;
    const timer = setInterval(async () => {
      const list = await getRuns({ limit: 50 });
      const row = list.find((r) => r.id === runId);
      if (row && row.status !== 'running') {
        clearInterval(timer);
        await loadRuns();
        return;
      }
      if (!row) {
        clearInterval(timer);
        await loadRuns();
        return;
      }
    }, 3000);
    setTimeout(() => clearInterval(timer), 600000);
  } finally {
    loadingRef.value = false;
  }
}

onMounted(() => {
  loadRuns();
});
</script>

<style scoped>
.data-fetch-page {
  padding: 0;
}
.desc {
  color: var(--el-text-color-regular);
  margin-bottom: 16px;
}
.actions {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.action-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.table-card {
  margin-top: 20px;
}
</style>
