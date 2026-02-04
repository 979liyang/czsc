/**
 * 股票详情页状态管理
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { analysisApi, type LocalCzscResponseData } from '../api/analysis';

export const useStockDetailStore = defineStore('stockDetail', () => {
  // 状态
  const symbol = ref<string>('');
  const localCzsc = ref<LocalCzscResponseData | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const activeFreq = ref<string>('30分钟');
  const baseFreq = ref<string>('1分钟');
  const freqs = ref<string>('1,5,15,30,60');

  // 操作
  async function fetchLocalCzsc(
    symbolInput: string,
    sdt: string,
    edt?: string,
    freqsInput: string = '1,5,15,30,60',
    baseFreqInput: string = '1分钟',
    includeDaily: boolean = true
  ) {
    loading.value = true;
    error.value = null;
    symbol.value = symbolInput;
    freqs.value = freqsInput;
    baseFreq.value = baseFreqInput;

    try {
      const result = await analysisApi.getLocalCzsc(symbolInput, sdt, edt, freqsInput, includeDaily, baseFreqInput);
      localCzsc.value = result;
      const keys = Object.keys(result.items || {});
      if (keys.length > 0 && !keys.includes(activeFreq.value)) {
        activeFreq.value = keys.includes('30分钟') ? '30分钟' : keys[0];
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '获取分析数据失败';
      localCzsc.value = null;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  function clear() {
    symbol.value = '';
    localCzsc.value = null;
    error.value = null;
  }

  return {
    // 状态
    symbol,
    localCzsc,
    loading,
    error,
    activeFreq,
    baseFreq,
    freqs,
    // 操作
    fetchLocalCzsc,
    clear,
  };
});
