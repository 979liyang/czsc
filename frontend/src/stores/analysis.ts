/**
 * 缠论分析状态管理
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { analysisApi, type AnalysisResponseData } from '../api/analysis';

export const useAnalysisStore = defineStore('analysis', () => {
  // 状态
  const loading = ref(false);
  const analysisResult = ref<AnalysisResponseData | null>(null);
  const error = ref<string | null>(null);

  // 计算属性
  const hasResult = computed(() => analysisResult.value !== null);
  const bis = computed(() => analysisResult.value?.bis || []);
  const fxs = computed(() => analysisResult.value?.fxs || []);
  const zss = computed(() => analysisResult.value?.zss || []);

  // 操作
  async function analyze(symbol: string, freq: string, sdt: string, edt: string) {
    loading.value = true;
    error.value = null;

    try {
      const result = await analysisApi.analyze({ symbol, freq, sdt, edt });
      analysisResult.value = result;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '分析失败';
      analysisResult.value = null;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function clear() {
    analysisResult.value = null;
    error.value = null;
  }

  return {
    // 状态
    loading,
    analysisResult,
    error,
    // 计算属性
    hasResult,
    bis,
    fxs,
    zss,
    // 操作
    analyze,
    clear,
  };
});
