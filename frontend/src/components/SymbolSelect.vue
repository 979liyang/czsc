<!--
  公共股票代码选择器
  - 下拉可搜索（代码/名称）
  - sessionStorage 记录搜索/选择过的股票，默认排在前面
-->
<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    filterable
    clearable
    :loading="loading"
    :disabled="disabled"
    :style="inputStyle"
    class="symbol-select"
    @update:model-value="onChange"
  >
    <el-option
      v-for="opt in displayOptions"
      :key="opt.value"
      :label="opt.label"
      :value="opt.value"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { ElSelect, ElOption } from 'element-plus';
import { symbolsApi } from '../api/symbols';
import type { SymbolItem } from '../api/symbols';

const SESSION_KEY = 'czsc_symbol_recent';
const MAX_RECENT = 50;

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    placeholder?: string;
    /** 输入框宽度，如 '100%' | '320px' */
    width?: string;
    disabled?: boolean;
    /** 市场过滤：SH / SZ，不传则全部 */
    market?: string | null;
  }>(),
  {
    modelValue: null,
    placeholder: '搜索股票代码或名称',
    width: '100%',
    disabled: false,
    market: null,
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', v: string | null): void;
}>();

const inputStyle = computed(() => ({ width: props.width }));

const loading = ref(false);
const allOptions = ref<{ value: string; label: string }[]>([]);
const recentSymbols = ref<{ symbol: string; label: string }[]>([]);

function loadRecentFromSession(): { symbol: string; label: string }[] {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw) as { symbol: string; label?: string }[];
    return (arr || []).slice(0, MAX_RECENT).map((x) => ({
      symbol: x.symbol,
      label: x.label || x.symbol,
    }));
  } catch {
    return [];
  }
}

function saveRecentToSession(list: { symbol: string; label: string }[]) {
  try {
    sessionStorage.setItem(
      SESSION_KEY,
      JSON.stringify(list.slice(0, MAX_RECENT))
    );
  } catch {
    // ignore
  }
}

function addToRecent(symbol: string, label: string) {
  const next = [
    { symbol, label },
    ...recentSymbols.value.filter((x) => x.symbol !== symbol),
  ].slice(0, MAX_RECENT);
  recentSymbols.value = next;
  saveRecentToSession(next);
}

/** 展示选项：最近使用的在前，其余在后（去重） */
const displayOptions = computed(() => {
  const recentSet = new Set(recentSymbols.value.map((x) => x.symbol));
  const recentOpts = recentSymbols.value.map((x) => ({ value: x.symbol, label: x.label }));
  const restOpts = allOptions.value.filter((o) => !recentSet.has(o.value));
  return [...recentOpts, ...restOpts];
});

async function loadAllOptions() {
  loading.value = true;
  try {
    const res = await symbolsApi.listSymbols({
      with_name: true,
      market: props.market || undefined,
    });
    allOptions.value = (res.items || []).map((x: SymbolItem) => ({
      value: x.symbol,
      label: x.name ? `${x.symbol} ${x.name}` : x.symbol,
    }));
  } catch {
    allOptions.value = [];
  } finally {
    loading.value = false;
  }
}

function onChange(val: string | null) {
  emit('update:modelValue', val);
  // 先提交选中值；最近使用延后到空闲时更新，避免选中瞬间重算/重绘大量 option 导致卡顿
  if (val) {
    const opt = allOptions.value.find((o) => o.value === val) || { value: val, label: val };
    const runAddRecent = () => addToRecent(opt.value, opt.label);
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(runAddRecent, { timeout: 200 });
    } else {
      nextTick(() => setTimeout(runAddRecent, 0));
    }
  }
}

onMounted(() => {
  recentSymbols.value = loadRecentFromSession();
  loadAllOptions();
});

watch(
  () => props.market,
  () => {
    loadAllOptions();
  }
);
</script>

<style scoped>
.symbol-select {
  display: inline-block;
}
</style>
