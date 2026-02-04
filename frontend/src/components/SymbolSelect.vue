<template>
  <el-select
    v-model="innerValue"
    filterable
    clearable
    placeholder="选择股票（代码/中文名）"
    style="width: 240px"
    @change="emitValue"
  >
    <el-option
      v-for="item in items"
      :key="item.symbol"
      :label="formatLabel(item)"
      :value="item.symbol"
    />
  </el-select>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { ElSelect, ElOption } from 'element-plus';
import { symbolsApi, type SymbolItem } from '../api/symbols';

const props = withDefaults(
  defineProps<{
    modelValue?: string | null;
    market?: string | null;
  }>(),
  {
    modelValue: null,
    market: null,
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', v: string | null): void;
}>();

const items = ref<SymbolItem[]>([]);
const innerValue = ref<string | null>(props.modelValue ?? null);

watch(
  () => props.modelValue,
  (v) => {
    innerValue.value = v ?? null;
  }
);

const formatLabel = (item: SymbolItem) => {
  const name = item.name ? ` ${item.name}` : '';
  return `${item.symbol}${name}`;
};

const emitValue = () => {
  emit('update:modelValue', innerValue.value ?? null);
};

const load = async () => {
  const res = await symbolsApi.listSymbols({ with_name: true, market: props.market });
  items.value = res.items || [];
};

onMounted(() => {
  load().catch((e) => {
    console.warn('加载股票列表失败', e);
  });
});
</script>

