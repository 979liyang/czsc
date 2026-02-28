<template>
  <div class="strategy-analyze-page">
    <el-card>
      <template #header>
        <span>策略分析</span>
      </template>
      <el-form :model="form" label-width="120px" class="analyze-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="股票代码">
              <SymbolSelect
                :model-value="form.symbol"
                width="100%"
                @update:model-value="(v) => (form.symbol = v ?? '')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="策略">
              <el-select
                v-model="form.strategyId"
                placeholder="选择策略"
                clearable
                filterable
                style="width: 100%"
                @change="onStrategyChange"
              >
                <el-option
                  v-for="s in strategyList"
                  :key="s.id"
                  :label="s.name"
                  :value="s.id"
                >
                  <span>{{ s.name }}</span>
                  <span class="strategy-type-tag">({{ s.strategy_type }})</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="form.sdt"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="开始日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="form.edt"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <template v-if="paramsSchema.length">
          <el-divider content-position="left">策略参数（可修改）</el-divider>
          <el-row :gutter="20">
            <el-col v-for="p in paramsSchema" :key="p.name" :span="12">
              <el-form-item :label="p.description || p.name">
                <el-select
                  v-if="p.options && p.options.length"
                  v-model="paramsForm[p.name]"
                  placeholder="请选择"
                  style="width: 100%"
                >
                  <el-option v-for="opt in p.options" :key="opt" :label="opt" :value="opt" />
                </el-select>
                <el-input
                  v-else-if="p.type === 'string'"
                  v-model="paramsForm[p.name]"
                  :placeholder="String(p.default)"
                  clearable
                  style="width: 100%"
                />
                <el-input-number
                  v-else-if="p.type === 'number'"
                  v-model="paramsForm[p.name]"
                  :placeholder="String(p.default)"
                  style="width: 100%"
                />
                <el-switch v-else-if="p.type === 'boolean'" v-model="paramsForm[p.name]" />
                <el-input
                  v-else
                  v-model="paramsForm[p.name]"
                  :placeholder="String(p.default)"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRun">运行分析</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-alert v-if="strategiesHint" :title="strategiesHint" type="info" closable class="mt-4" show-icon />
    <el-alert v-if="error" :title="error" type="error" closable class="mt-4" />

    <!-- 当前状态：根据回测最新日期——有持仓则当前持有，否则按笔方向 G买入/S卖出 -->
    <el-card v-if="result && backtestStatusLabel" class="status-card mt-4" :class="backtestStatusClass">
      <span class="status-label">当前状态：</span>
      <span class="status-value">{{ backtestStatusLabel }}</span>
    </el-card>

    <el-card v-if="result" class="mt-4">
      <template #header>回测结果</template>
      <!-- 按持仓分块展示（对齐 strategy_demo） -->
      <template v-if="result.positions_summary && result.positions_summary.length">
        <div
          v-for="item in result.positions_summary"
          :key="item.pos_name"
          class="position-block mt-4"
        >
          <h4 class="position-title">【{{ item.pos_name }}】</h4>
          <p class="operate-count">操作次数: {{ item.operate_count }}</p>
          <h5 class="section-label">全部操作</h5>
          <el-table
            v-if="getOperatesByPosName(item.pos_name).length"
            :data="getOperatesByPosName(item.pos_name)"
            stripe
            size="small"
            class="all-operates-table"
            max-height="320"
          >
            <el-table-column prop="dt" label="时间" width="180" />
            <el-table-column prop="op" label="操作" width="120" :formatter="(row, col, op) => opToLabel(op)" />
            <el-table-column prop="bid" label="bid" width="80" />
            <el-table-column prop="price" label="价格" width="100" />
            <el-table-column prop="amount" label="数量" width="80" />
          </el-table>
          <p v-else class="no-operates">无操作记录</p>
          <h5 class="section-label">评估</h5>
          <div v-if="hasEvaluateContent(item.evaluate)" class="evaluate-block">
            <div v-for="(val, dir) in item.evaluate" :key="dir" class="evaluate-sub">
              <strong>{{ dir }}：</strong>
              <pre v-if="val && typeof val === 'object' && Object.keys(val).length" class="evaluate-pre">{{ JSON.stringify(val, null, 2) }}</pre>
              <span v-else class="evaluate-empty">暂无数据</span>
            </div>
          </div>
          <div v-else class="evaluate-block">
            <span class="evaluate-empty">暂无评估数据</span>
          </div>
        </div>
      </template>
      <!-- 降级：无 positions_summary 时展示绩效 JSON + 全量操作表 -->
      <template v-else>
        <div v-if="Object.keys(result.pairs).length" class="pairs-summary">
          <h4>绩效摘要</h4>
          <pre>{{ JSON.stringify(result.pairs, null, 2) }}</pre>
        </div>
        <el-table :data="result.operates" stripe max-height="400" class="mt-4">
          <el-table-column prop="pos_name" label="持仓名" width="180" />
          <el-table-column prop="dt" label="时间" width="180" />
          <el-table-column prop="op" label="操作" width="120" :formatter="(row, col, op) => opToLabel(op)" />
          <el-table-column prop="bid" label="bid" width="80" />
          <el-table-column prop="price" label="价格" width="100" />
          <el-table-column prop="amount" label="数量" width="80" />
        </el-table>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import {
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElSelect,
  ElOption,
  ElDatePicker,
  ElButton,
  ElRow,
  ElCol,
  ElAlert,
  ElTable,
  ElTableColumn,
  ElInputNumber,
  ElSwitch,
  ElDivider,
} from 'element-plus';
import { strategiesApi } from '../api/strategies';
import type { StrategyItem, ParamsSchemaItem } from '../api/strategies';
import { backtestApi } from '../api/backtest';
import type { BacktestResponse, BacktestOperateItem } from '../api/backtest';
import { analysisApi } from '../api/analysis';
import SymbolSelect from '../components/SymbolSelect.vue';

/** 操作代码 -> 中文（与 czsc Operate 枚举一致），展示格式：LO-开多 */
const OP_LABELS: Record<string, string> = {
  LO: '开多',
  LE: '平多',
  SO: '开空',
  SE: '平空',
  HL: '持多',
  HS: '持空',
  HO: '持币',
};

function opToLabel(op: string | undefined): string {
  if (op == null || op === '') return op ?? '';
  return OP_LABELS[op] ? `${op}-${OP_LABELS[op]}` : op;
}

function defaultSdt(): string {
  const d = new Date();
  d.setMonth(d.getMonth() - 6);
  return d.toISOString().slice(0, 10);
}
function defaultEdt(): string {
  return new Date().toISOString().slice(0, 10);
}

const form = reactive({
  symbol: '000001.SZ',
  strategyId: null as number | null,
  sdt: defaultSdt(),
  edt: defaultEdt(),
});

const strategyList = ref<StrategyItem[]>([]);
const paramsSchema = ref<ParamsSchemaItem[]>([]);
const paramsForm = reactive<Record<string, unknown>>({});
const loading = ref(false);
const error = ref('');
const result = ref<BacktestResponse | null>(null);

/** 麒麟分析结果（用于当前区间 G/S），回测成功后按日线请求 */
const zoneAnalysisResult = ref<{ last_bi_direction?: string | null } | null>(null);

/** 当前区间文案：向下笔→G买入区间，向上笔→S卖出区间 */
const currentZoneLabel = computed(() => {
  const dir = zoneAnalysisResult.value?.last_bi_direction;
  if (dir === '向下') return 'G买入区间';
  if (dir === '向上') return 'S卖出区间';
  return null;
});

/** 回测结果当前状态：有持仓→当前持有，否则按最新笔方向→G买入/S卖出 */
const backtestStatusLabel = computed(() => {
  if (!result.value) return null;
  const hasHold = (result.value.positions || []).some((p) => p.pos !== 0);
  if (hasHold) return '当前持有';
  const zone = currentZoneLabel.value;
  if (zone === 'G买入区间') return 'G买入';
  if (zone === 'S卖出区间') return 'S卖出';
  return null;
});

const backtestStatusClass = computed(() => {
  const label = backtestStatusLabel.value;
  if (label === '当前持有') return 'status-hold';
  if (label === 'G买入') return 'status-buy';
  if (label === 'S卖出') return 'status-sell';
  return '';
});

/** 按持仓名聚合的全部操作，用于表格数据（倒序：时间新的在前） */
const operatesByPosName = computed(() => {
  const m = new Map<string, BacktestOperateItem[]>();
  if (!result.value?.operates) return m;
  for (const o of result.value.operates) {
    const list = m.get(o.pos_name) || [];
    list.push(o);
    m.set(o.pos_name, list);
  }
  for (const [key, list] of m) {
    m.set(key, [...list].reverse());
  }
  return m;
});

function buildParamsFromSchema(schema: ParamsSchemaItem[]): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const p of schema) {
    out[p.name] = p.default;
  }
  return out;
}

/** 按持仓名从 result.operates 中筛出该持仓的全部操作 */
function getOperatesByPosName(posName: string) {
  return operatesByPosName.value.get(posName) || [];
}

/** 评估对象是否有任意有效内容（多空合并/多头/空头任一为非空对象） */
function hasEvaluateContent(evaluate: Record<string, unknown> | undefined): boolean {
  if (!evaluate || typeof evaluate !== 'object') return false;
  return Object.values(evaluate).some(
    (v) => v && typeof v === 'object' && Object.keys(v as object).length > 0
  );
}

function onStrategyChange() {
  const id = form.strategyId;
  const s = strategyList.value.find((x) => x.id === id);
  if (!s) {
    paramsSchema.value = [];
    Object.keys(paramsForm).forEach((k) => delete paramsForm[k]);
    return;
  }
  paramsSchema.value = s.params_schema || [];
  const defaults = buildParamsFromSchema(paramsSchema.value);
  Object.keys(paramsForm).forEach((k) => delete paramsForm[k]);
  Object.assign(paramsForm, defaults);
}

const strategiesHint = ref('');

async function loadStrategies() {
  strategiesHint.value = '';
  try {
    const res = await strategiesApi.getStrategies(true);
    strategyList.value = res.items || [];
    if (res.count === 0 && res.hint) {
      strategiesHint.value = res.hint;
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '加载策略列表失败';
  }
}

async function handleRun() {
  if (!form.symbol?.trim()) {
    error.value = '请输入股票代码';
    return;
  }
  if (!form.strategyId) {
    error.value = '请选择策略';
    return;
  }
  error.value = '';
  result.value = null;
  zoneAnalysisResult.value = null;
  loading.value = true;
  try {
    const sdt = form.sdt?.replace(/-/g, '') || defaultSdt().replace(/-/g, '');
    const edt = form.edt?.replace(/-/g, '') || defaultEdt().replace(/-/g, '');
    const res = await backtestApi.runBacktestByStrategy({
      strategy_id: form.strategyId,
      symbol: form.symbol.trim(),
      sdt,
      edt,
      params: { ...paramsForm },
    });
    result.value = res;
    try {
      const sdtStr = form.sdt || new Date().toISOString().slice(0, 10);
      const edtStr = form.edt || new Date().toISOString().slice(0, 10);
      const zoneRes = await analysisApi.analyze({
        symbol: form.symbol.trim(),
        freq: '日线',
        sdt: sdtStr,
        edt: edtStr,
      });
      zoneAnalysisResult.value = { last_bi_direction: zoneRes.last_bi_direction ?? undefined };
    } catch {
      zoneAnalysisResult.value = null;
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '回测请求失败';
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadStrategies();
});
</script>

<style scoped>
.strategy-analyze-page {
  padding: 20px;
}
.strategy-type-tag {
  color: #909399;
  font-size: 12px;
  margin-left: 6px;
}
.pairs-summary {
  margin-bottom: 16px;
}
.pairs-summary pre {
  font-size: 12px;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  overflow: auto;
}
.mt-4 {
  margin-top: 16px;
}
.position-block {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}
.position-title {
  margin: 0 0 8px 0;
  font-size: 14px;
}
.operate-count {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
}
.section-label {
  margin: 12px 0 6px 0;
  font-size: 13px;
  color: #303133;
}
.all-operates-table {
  margin-bottom: 8px;
}
.last-operates-table {
  margin-bottom: 8px;
}
.no-operates {
  margin: 0 0 8px 0;
  color: #909399;
  font-size: 12px;
}
.operates-tip {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}
.evaluate-block {
  margin-top: 8px;
}
.evaluate-sub {
  margin-bottom: 8px;
}
.evaluate-sub:last-child {
  margin-bottom: 0;
}
.evaluate-empty {
  color: #909399;
  font-size: 12px;
}
.evaluate-pre {
  font-size: 12px;
  background: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  overflow: auto;
  margin: 4px 0 0 0;
}
.zone-card {
  padding: 12px 16px;
}
.zone-card .zone-label {
  font-weight: 500;
  margin-right: 6px;
}
.zone-card .zone-value {
  font-weight: 600;
  font-size: 1.05em;
}
.zone-card.zone-buy .zone-value {
  color: #67c23a;
}
.zone-card.zone-sell .zone-value {
  color: #f56c6c;
}
.status-card {
  padding: 12px 16px;
}
.status-card .status-label {
  font-weight: 500;
  margin-right: 6px;
}
.status-card .status-value {
  font-weight: 600;
  font-size: 1.05em;
}
.status-card.status-hold .status-value {
  color: #409eff;
}
.status-card.status-buy .status-value {
  color: #67c23a;
}
.status-card.status-sell .status-value {
  color: #f56c6c;
}
</style>
