/**
 * 股票详情页状态管理
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { analysisApi, type AnalysisResponseData } from '../api/analysis';
import type { AnalysisRequestParams } from '../api/analysis';

export const useStockDetailStore = defineStore('stockDetail', () => {
  // 状态
  const symbol = ref<string>('');
  const analysisData = ref<AnalysisResponseData | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 操作
  async function fetchAnalysis(params: AnalysisRequestParams) {
    loading.value = true;
    error.value = null;
    symbol.value = params.symbol;

    try {
      const result = await analysisApi.getStockAnalysis(params);
      analysisData.value = result;
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '获取分析数据失败';
      analysisData.value = null;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function clear() {
    symbol.value = '';
    analysisData.value = null;
    error.value = null;
  }

  return {
    // 状态
    symbol,
    analysisData,
    loading,
    error,
    // 操作
    fetchAnalysis,
    clear,
  };
});
