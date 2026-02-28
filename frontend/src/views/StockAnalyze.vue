<template>
  <div class="signal-analyze-page">
    <el-card>
      <template #header>
        <span>信号分析</span>
      </template>
      <el-form :model="form" label-width="100px" class="analyze-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="股票代码">
              <SymbolSelect v-model="form.symbol" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间">
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
            <el-form-item label="结束时间">
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
        <el-form-item label="已选信号">
          <div class="selected-signals">
            <template v-for="(items, cat) in selectedByCategory" :key="cat">
              <div v-if="items.length" class="signal-group">
                <span class="category-label">{{ cat }}</span>
                <div class="signal-tags">
                  <el-tag
                    v-for="item in items"
                    :key="item.fullName"
                    closable
                    size="small"
                    @close="removeSelected(item.fullName)"
                  >
                    {{ item.name }} <span class="freq-tag">({{ item.freq }})</span>
                  </el-tag>
                </div>
              </div>
            </template>
            <el-button type="primary" plain circle :icon="Plus" class="add-btn" @click="openAddDialog" />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loadingAnalyze" @click="handleAnalyze">
            分析
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog
      v-model="addDialogVisible"
      title="添加信号"
      width="560px"
      @closed="addDialogClosed"
    >
      <el-form label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="addDialogCategory" placeholder="先选类型" clearable style="width: 100%" @change="onAddCategoryChange">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="信号">
          <el-select
            v-model="addDialogSelected"
            multiple
            collapse-tags
            placeholder="选择要添加的信号"
            style="width: 100%"
            value-key="name"
          >
            <el-option
              v-for="s in addDialogSignalList"
              :key="s.name"
              :label="s.name"
              :value="s"
            >
              <div class="signal-option">
                <span class="signal-option-name">{{ s.name }}</span>
                <span class="signal-option-desc">{{ truncateDesc(s.description) }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        <template v-if="addDialogDetailSignal">
          <el-divider content-position="left">当前信号说明</el-divider>
          <div class="signal-detail-panel">
            <p class="detail-desc">{{ addDialogDetailSignal.description || '无描述' }}</p>
            <p v-if="addDialogDetailSignal.params?.length" class="detail-label">参数</p>
            <ul v-if="addDialogDetailSignal.params?.length" class="detail-list">
              <li v-for="p in addDialogDetailSignal.params" :key="p.name">
                {{ p.name }}: {{ p.type || '—' }}
                <span v-if="p.default !== undefined"> 默认 {{ String(p.default) }}</span>
              </li>
            </ul>
            <p v-if="addDialogDetailSignal.signals?.length" class="detail-label">输出键 (signals)</p>
            <ul v-if="addDialogDetailSignal.signals?.length" class="detail-list">
              <li v-for="k in addDialogDetailSignal.signals" :key="k">{{ k }}</li>
            </ul>
          </div>
        </template>
        <template v-if="addDialogSelected.length">
          <el-divider content-position="left">选择要展示的输出键</el-divider>
          <div v-for="s in addDialogSelected" :key="s.name" class="outputs-row">
            <span class="outputs-label">{{ s.name }}</span>
            <el-select
              :model-value="addDialogOutputs[s.name] ?? s.signals ?? []"
              multiple
              collapse-tags
              placeholder="默认全部"
              style="flex: 1; min-width: 0"
              @update:model-value="(v: string[]) => setDialogOutputs(s.name, v)"
            >
              <el-option v-for="k in (s.signals || [])" :key="k" :label="k" :value="k" />
            </el-select>
          </div>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAdd">确定添加</el-button>
      </template>
    </el-dialog>

    <el-alert v-if="error" :title="error" type="error" closable class="mt-4" />

    <el-card v-if="displayedResult" class="mt-4">
      <template #header>信号结果</template>
      <pre class="result-pre">{{ JSON.stringify(displayedResult, null, 2) }}</pre>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { Plus } from '@element-plus/icons-vue';
import {
  ElCard, ElForm, ElFormItem, ElSelect, ElOption, ElButton, ElRow, ElCol,
  ElAlert, ElTag, ElDialog,
} from 'element-plus';
import SymbolSelect from '../components/SymbolSelect.vue';
import { docsApi } from '../api/docs';
import { signalsApi } from '../api/signals';
import type { SignalInfo } from '../api/docs';

/** 已选信号项：展示用 name，请求用 fullName；可选 selectedOutputs 仅展示这些输出键 */
interface SelectedSignal {
  name: string;
  fullName: string;
  category: string;
  freq: string;
  selectedOutputs?: string[];
}

function defaultSdt(): string {
  const d = new Date();
  d.setMonth(d.getMonth() - 6);
  return d.toISOString().slice(0, 10);
}
function defaultEdt(): string {
  return new Date().toISOString().slice(0, 10);
}

const form = ref({
  symbol: '000001.SZ',
  sdt: defaultSdt(),
  edt: defaultEdt(),
});

const selectedSignals = ref<SelectedSignal[]>([]);
const signalOptions = ref<SignalInfo[]>([]);
const categories = ref<string[]>([]);
const loadingAnalyze = ref(false);
const error = ref('');
const signalResult = ref<Record<string, string> | null>(null);

const selectedByCategory = computed(() => {
  const map: Record<string, SelectedSignal[]> = {};
  for (const item of selectedSignals.value) {
    if (!map[item.category]) map[item.category] = [];
    map[item.category].push(item);
  }
  return map;
});

/** 若已选信号中存在 selectedOutputs，则结果只展示这些 key 的并集 */
const displayedResult = computed(() => {
  const raw = signalResult.value;
  if (!raw) return null;
  const allowed = new Set<string>();
  for (const item of selectedSignals.value) {
    if (item.selectedOutputs?.length) {
      item.selectedOutputs.forEach((k) => allowed.add(k));
    }
  }
  if (allowed.size === 0) return raw;
  const out: Record<string, string> = {};
  for (const k of Object.keys(raw)) {
    if (allowed.has(k)) out[k] = raw[k];
  }
  return out;
});

const addDialogVisible = ref(false);
const addDialogCategory = ref('');
const addDialogSelected = ref<SignalInfo[]>([]);
/** 每个已选信号函数对应的输出键多选（key=signal name） */
const addDialogOutputs = ref<Record<string, string[]>>({});

const addDialogSignalList = computed(() => {
  if (!addDialogCategory.value) return [];
  return signalOptions.value.filter((s) => s.category === addDialogCategory.value);
});

/** 当前选中的第一个信号，用于展示详细说明 */
const addDialogDetailSignal = computed(() => {
  const list = addDialogSelected.value;
  return list.length ? list[0] : null;
});

function sdtEdt(): { sdt: string; edt: string } {
  let sdt = form.value.sdt || defaultSdt();
  let edt = form.value.edt || defaultEdt();
  sdt = sdt.replace(/-/g, '');
  edt = edt.replace(/-/g, '');
  return { sdt, edt };
}

function removeSelected(name: string) {
  selectedSignals.value = selectedSignals.value.filter((s) => s.fullName !== name && s.name !== name);
}

function openAddDialog() {
  addDialogCategory.value = '';
  addDialogSelected.value = [];
  addDialogOutputs.value = {};
  addDialogVisible.value = true;
}

function onAddCategoryChange() {
  addDialogSelected.value = [];
  addDialogOutputs.value = {};
}

/** 选中信号变化时，为新选中的信号初始化输出键为“全选” */
watch(addDialogSelected, (next) => {
  const out = { ...addDialogOutputs.value };
  for (const s of next) {
    if (!(s.name in out)) {
      out[s.name] = s.signals ? [...s.signals] : [];
    }
  }
  addDialogOutputs.value = out;
}, { deep: true });

function setDialogOutputs(signalName: string, keys: string[]) {
  addDialogOutputs.value = { ...addDialogOutputs.value, [signalName]: keys };
}

/** 截断描述为一行，便于在选项内展示 */
function truncateDesc(text: string | undefined, maxLen = 56): string {
  if (!text || !text.trim()) return '';
  const t = text.trim().replace(/\s+/g, ' ');
  return t.length <= maxLen ? t : t.slice(0, maxLen) + '…';
}

function addDialogClosed() {
  addDialogCategory.value = '';
  addDialogSelected.value = [];
}

/** 分钟级周期在无对应 K 线数据时回退为日线，避免「未找到K线数据」 */
function resolveFreq(requiredFreq: string | undefined): string {
  const f = requiredFreq?.trim() || '日线';
  if (f === '1分钟' || f === '5分钟' || f === '15分钟' || f === '30分钟' || f === '60分钟') {
    return '日线';
  }
  return f;
}

function confirmAdd() {
  for (const s of addDialogSelected.value) {
    const fullName = s.full_name || s.name;
    if (!selectedSignals.value.some((x) => x.fullName === fullName)) {
      const chosen = addDialogOutputs.value[s.name];
      const selectedOutputs =
        chosen?.length ? chosen : (s.signals?.length ? s.signals : undefined);
      const freq = resolveFreq(s.data_requirements?.freq);
      selectedSignals.value.push({
        name: s.name,
        fullName,
        category: s.category,
        freq,
        selectedOutputs,
      });
    }
  }
  addDialogVisible.value = false;
}

async function loadOptions() {
  error.value = '';
  try {
    const res = await docsApi.getSignalsList();
    signalOptions.value = res.signals || [];
    categories.value = res.categories || [];
  } catch (e: unknown) {
    error.value = (e as Error).message || '加载信号列表失败';
  }
}

async function handleAnalyze() {
  if (!selectedSignals.value.length) {
    error.value = '请先添加至少一个信号';
    return;
  }
  if (!form.value.symbol) {
    error.value = '请填写股票代码';
    return;
  }
  const { sdt, edt } = sdtEdt();
  error.value = '';
  signalResult.value = null;
  loadingAnalyze.value = true;
  try {
    const byFreq = new Map<string, SelectedSignal[]>();
    for (const item of selectedSignals.value) {
      const list = byFreq.get(item.freq) || [];
      list.push(item);
      byFreq.set(item.freq, list);
    }
    const merged: Record<string, string> = {};
    for (const [freq, list] of byFreq) {
      const configs = list.map((item) => ({ name: item.fullName, freq, di: 1 }));
      const res = await signalsApi.calculateBatch({
        symbol: form.value.symbol,
        freq,
        signal_configs: configs,
        sdt,
        edt,
      });
      if (res.signals) {
        Object.assign(merged, res.signals);
      }
    }
    signalResult.value = merged;
  } catch (e: unknown) {
    error.value = (e as Error).message || '分析失败';
  } finally {
    loadingAnalyze.value = false;
  }
}

onMounted(() => {
  form.value.sdt = defaultSdt();
  form.value.edt = defaultEdt();
  loadOptions();
});
</script>

<style scoped>
.signal-analyze-page {
  padding: 20px;
}
.selected-signals {
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  min-height: 60px;
}
.signal-group {
  margin-bottom: 8px;
}
.signal-group:last-of-type {
  margin-bottom: 0;
}
.category-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-right: 8px;
}
.signal-tags {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.freq-tag {
  font-size: 11px;
  opacity: 0.85;
}
.add-btn {
  margin-left: 8px;
  vertical-align: middle;
}
.mt-4 {
  margin-top: 16px;
}
.result-pre {
  font-size: 12px;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
}

.signal-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.signal-option-name {
  font-weight: 500;
  font-size: 13px;
}
.signal-option-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.3;
}
.signal-detail-panel {
  font-size: 12px;
  color: var(--el-text-color-regular);
  max-height: 200px;
  overflow-y: auto;
}
.detail-desc {
  margin: 0 0 8px;
  line-height: 1.5;
  white-space: pre-wrap;
}
.detail-label {
  font-weight: 600;
  margin: 8px 0 4px;
}
.detail-list {
  margin: 0;
  padding-left: 18px;
}
.outputs-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.outputs-row:last-child {
  margin-bottom: 0;
}
.outputs-label {
  font-size: 12px;
  min-width: 100px;
  flex-shrink: 0;
}
</style>
