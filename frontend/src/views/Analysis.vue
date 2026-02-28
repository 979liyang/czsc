<template>
  <div class="analysis-page">
    <el-card class="search-card">
      <el-form :model="form" :inline="true" @submit.prevent="handleAnalyze">
        <el-form-item label="股票代码">
          <SymbolSelect
            :model-value="form.symbol"
            width="200px"
            @update:model-value="(v) => (form.symbol = v ?? '')"
          />
        </el-form-item>
        <el-form-item label="周期">
          <el-select v-model="form.freq" style="width: 150px">
            <el-option label="日线" value="日线" />
            <el-option label="15分钟" value="15分钟" />
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
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="form.edt"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            placeholder="选择结束时间"
            style="width: 180px"
            :disabled-date="disableFutureDate"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="store.loading">
            分析
          </el-button>
          <el-button @click="handleClear">清空</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="store.error" class="error-message">
      <el-alert :title="store.error" type="error" :closable="false" />
    </div>

    <div v-if="store.hasResult" class="result-container">
      <!-- signals3 风格：标题块 -->
      <div class="report-header">
        <div class="report-title">麒麟分析（笔 + 分型）</div>
        <div class="report-meta mb-[6px]">
          <span>标的：{{ store.analysisResult?.symbol }}</span>
          <span>周期：{{ form.freq }}</span>
          <span v-if="store.analysisResult?.data_end_dt">结束时间：{{ formatDataDt(store.analysisResult.data_end_dt) }}</span>
        </div>
        <div
          v-if="
            currentZoneLabel ||
            conclusionLabel ||
            store.analysisResult?.requested_sdt ||
            store.analysisResult?.data_start_dt ||
            store.analysisResult?.data_end_dt ||
            store.analysisResult?.data_range_note ||
            store.analysisResult?.gaps_summary
          "
          class="section-card summary-card text-[#606266]"
        >
          <div class="summary-body">
            <div class="summary-row" v-if="currentZoneLabel || conclusionLabel">
              <span v-if="currentZoneLabel" class="summary-item">
                <span class="summary-label">当前区间</span>
                <span class="zone-value" :class="currentZoneClass">{{ currentZoneLabel }}</span>
              </span>
              <span v-if="conclusionLabel" class="summary-item">
                <span class="summary-label">结论</span>
                <span class="conclusion-value">{{ conclusionLabel }}</span>
              </span>
            </div>
            <div class="summary-row report-text" v-if="store.analysisResult?.requested_sdt || store.analysisResult?.data_start_dt">
              <span v-if="store.analysisResult?.requested_sdt || store.analysisResult?.requested_edt" class="summary-item">
                <span class="summary-label">请求范围</span>
                {{ store.analysisResult?.requested_sdt || '—' }} ~ {{ store.analysisResult?.requested_edt || '—' }}
              </span>
              <span v-if="store.analysisResult?.data_start_dt || store.analysisResult?.data_end_dt" class="summary-item" :class="{ 'actual-range-highlight': store.analysisResult?.data_range_note }">
                <span class="summary-label">实际范围</span>
                {{ effectiveRangeText }}
                <el-button
                  v-if="store.analysisResult?.data_range_note && (store.analysisResult?.effective_sdt && store.analysisResult?.effective_edt)"
                  type="primary"
                  link
                  size="small"
                  @click="syncFormToEffectiveRange"
                >
                  同步到查询条件
                </el-button>
              </span>
            </div>
            <el-alert
              v-if="store.analysisResult?.data_range_note"
              type="warning"
              :title="store.analysisResult.data_range_note"
              show-icon
              class="summary-alert"
            />
            <div v-if="store.analysisResult?.gaps_summary" class="report-text mt-2">缺口摘要：{{ store.analysisResult.gaps_summary }}</div>
          </div>
        </div>
      </div>

      <div class="flex gap-[16px]">
      <!-- 笔列表（独立表格） -->
      <el-card class="section-card">
        <template #header><span class="section-title">【笔列表】</span></template>
        <BiList :bis="store.bis" />
      </el-card>

      <!-- 分型列表（独立表格） -->
      <el-card class="section-card">
        <template #header><span class="section-title">【分型列表】</span></template>
        <FxList :fxs="store.fxs" />
      </el-card>
      </div>
      <!-- K线图（analyze4 风格 100% 还原） -->
      <el-card class="section-card">
        <template #header><span class="section-title">【K线图】</span></template>
        <div class="kline-wrapper">
          <KlineChart
            :symbol="form.symbol"
            :freq="form.freq"
            :bis="store.bis"
            :fxs="store.fxs"
            :zss="store.zss"
            :sdt="form.sdt"
            :edt="form.edt"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import {
  ElCard,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElButton,
  ElDatePicker,
  ElAlert,
} from 'element-plus';
import { useAnalysisStore } from '../stores/analysis';
import SymbolSelect from '../components/SymbolSelect.vue';
import KlineChart from '../components/KlineChart.vue';
import BiList from '../components/BiList.vue';
import FxList from '../components/FxList.vue';

const store = useAnalysisStore();

/** 根据最后一笔方向：向下→G买入区间，向上→S卖出区间 */
const currentZoneLabel = computed(() => {
  const dir = store.analysisResult?.last_bi_direction;
  if (dir === '向下') return 'G买入区间';
  if (dir === '向上') return 'S卖出区间';
  return null;
});

const currentZoneClass = computed(() => {
  const label = currentZoneLabel.value;
  if (label === 'G买入区间') return 'zone-buy';
  if (label === 'S卖出区间') return 'zone-sell';
  return '';
});

/** 结论：看多/看空/震荡（与 signals3 一致） */
const conclusionLabel = computed(() => {
  const dir = store.analysisResult?.last_bi_direction;
  if (dir === '向下') return '看多';
  if (dir === '向上') return '看空';
  return '震荡';
});

/** 实际范围展示文案（优先 effective_sdt/effective_edt，否则用 data_start_dt/data_end_dt 格式化） */
const effectiveRangeText = computed(() => {
  const r = store.analysisResult;
  if (!r) return '—';
  if (r.effective_sdt && r.effective_edt) return `${r.effective_sdt} ~ ${r.effective_edt}`;
  return `${formatDataDt(r.data_start_dt)} ~ ${formatDataDt(r.data_end_dt)}`;
});

/** 根据周期与结束日期计算默认开始日期：日线1年、周线5年、月线10年、60分3个月、30/15分1个月 */
function getDefaultSdt(edt: string, freq: string): string {
  const end = new Date(edt);
  const d = new Date(end.getTime());
  if (freq === '日线') {
    d.setFullYear(d.getFullYear() - 1);
  } else if (freq === '周线') {
    d.setFullYear(d.getFullYear() - 5);
  } else if (freq === '月线') {
    d.setFullYear(d.getFullYear() - 10);
  } else if (freq === '60分钟') {
    d.setMonth(d.getMonth() - 3);
  } else if (freq === '30分钟' || freq === '15分钟') {
    d.setMonth(d.getMonth() - 1);
  } else {
    d.setFullYear(d.getFullYear() - 1);
  }
  return d.toISOString().slice(0, 10);
}

function getDefaultEdt(): string {
  return new Date().toISOString().slice(0, 10);
}

/** 结束日期不能选未来：禁用今天之后的日期 */
function disableFutureDate(date: Date): boolean {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d.getTime() > today.getTime();
}

const form = ref({
  symbol: '000001.SH',
  freq: '日线',
  sdt: '',
  edt: getDefaultEdt(),
});

// 初始化 sdt（依赖 edt 与 freq）
form.value.sdt = getDefaultSdt(form.value.edt, form.value.freq);

// 切换周期时，按新周期重算默认开始时间（保持结束时间不变）
watch(
  () => form.value.freq,
  (freq) => {
    if (form.value.edt) {
      form.value.sdt = getDefaultSdt(form.value.edt, freq);
    }
  }
);

const handleAnalyze = async () => {
  const { symbol, freq, sdt, edt } = form.value;
  if (!symbol || !sdt || !edt) return;
  try {
    await store.analyze(symbol, freq, sdt, edt);
  } catch (error) {
    console.error('分析失败:', error);
  }
};

const handleClear = () => {
  store.clear();
};

/** 将表单 sdt/edt 同步为本次分析的实际使用范围（便于再次请求一致） */
function syncFormToEffectiveRange() {
  const r = store.analysisResult;
  if (r?.effective_sdt && r?.effective_edt) {
    form.value.sdt = r.effective_sdt;
    form.value.edt = r.effective_edt;
  } else if (r?.data_start_dt != null && r?.data_end_dt != null) {
    form.value.sdt = formatDataDt(r.data_start_dt).slice(0, 10);
    form.value.edt = formatDataDt(r.data_end_dt).slice(0, 10);
  }
}

/** 将接口返回的 ISO 时间格式化为可读：YYYY-MM-DD HH:mm:ss */
function formatDataDt(dt: string | null | undefined): string {
  if (!dt) return '—';
  const s = String(dt).trim();
  if (s.includes('T')) {
    const [datePart, timePart] = s.split('T');
    const time = timePart ? timePart.replace(/\.\d+Z?$/i, '').slice(0, 8) : ''; // HH:mm:ss
    return time ? `${datePart} ${time}` : datePart;
  }
  return s.length >= 10 ? s.slice(0, 10) : s;
}

onMounted(() => {
  // 可以在这里设置默认值或加载历史数据
});
</script>

<style scoped>
.analysis-page {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.error-message {
  margin-bottom: 20px;
}

.result-container {
  margin-top: 20px;
}

/* signals3 / take_snapshot 风格：报告头 */
.report-header {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}
.report-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}
.report-meta {
  font-size: 13px;
  color: #606266;
}
.report-meta span {
  margin-right: 16px;
}

/* 【摘要】合并卡：当前区间 + 结论 + 数据范围 */
.summary-card .summary-body {
  font-size: 13px;
  color: #606266;
}
.summary-card .summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 24px 32px;
  margin-bottom: 8px;
}
.summary-card .summary-row:last-of-type {
  margin-bottom: 0;
}
.summary-card .summary-item {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
}
.summary-card .summary-label {
  color: #606266;
  flex-shrink: 0;
}
.summary-card .zone-value {
  font-weight: 600;
}
.summary-card .zone-value.zone-buy {
  color: #f56c6c;
}
.summary-card .zone-value.zone-sell {
  color: #67c23a;
}
.summary-card .conclusion-value {
  font-weight: 600;
  color: #303133;
}
.summary-card .summary-alert {
  margin-top: 10px;
}
.summary-card .actual-range-highlight .summary-label {
  font-weight: 600;
  color: #e6a23c;
}

/* 【区块】标题 */
.section-title {
  font-weight: 600;
  color: #303133;
}
.section-card {
  margin-bottom: 16px;
}
.section-card :deep(.el-card__header) {
  padding: 10px 16px;
  background: #fafafa;
}
.report-text {
  font-size: 13px;
  color: #606266;
}
.mt-2 {
  margin-top: 8px;
}

.kline-wrapper {
  width: 100%;
  min-height: 500px;
}
</style>
