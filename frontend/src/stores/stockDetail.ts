/**
 * 股票详情页状态管理
 * 
 * 性能优化说明：
 * - 按周期缓存数据：使用 Map 结构按周期分别存储数据，避免重复请求
 * - 按需加载：只请求用户选择的周期，提升性能
 * - 缓存检查：已缓存的周期且时间范围匹配时，直接返回缓存数据
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { analysisApi, type LocalCzscResponseData } from '../api/analysis';

// 周期缓存项：存储每个周期的数据和对应的日期范围
interface FreqCacheItem {
  data: LocalCzscResponseData;
  sdt: string;
  edt: string;
  // 分页状态：记录已加载的数据量
  pagination?: {
    bars: { loaded: number; total: number };
    fxs: { loaded: number; total: number };
    bis: { loaded: number; total: number };
  };
}

export const useStockDetailStore = defineStore('stockDetail', () => {
  // 状态
  const symbol = ref<string>('');
  // 按周期存储的数据缓存：key 为周期名称（如 "30分钟"、"60分钟"、"日线"）
  const localCzscCache = ref<Map<string, FreqCacheItem>>(new Map());
  const loading = ref(false);
  const error = ref<string | null>(null);
  const activeFreq = ref<string>('30分钟');
  const baseFreq = ref<string>('1分钟');
  const freqs = ref<string>('30,60'); // 默认只支持 30分钟和60分钟，日线通过 include_daily 参数

  /**
   * 获取当前激活周期的数据（从缓存中）
   */
  const localCzsc = computed(() => {
    const cacheItem = localCzscCache.value.get(activeFreq.value);
    return cacheItem?.data || null;
  });

  /**
   * 检查缓存是否有效（时间范围匹配）
   */
  function isCacheValid(freq: string, sdt: string, edt: string): boolean {
    const cacheItem = localCzscCache.value.get(freq);
    if (!cacheItem) return false;
    return cacheItem.sdt === sdt && cacheItem.edt === edt;
  }

  /**
   * 获取单个周期的数据（按需加载，带缓存检查和分页支持）
   * 
   * 时间范围控制说明：
   * - recentMonths: 返回的K线数据只包含最近N个月（默认3，表示返回最近3个月）
   * - 分析数据（fxs、bis）基于全量历史数据计算，返回全量结果（不受 recentMonths 限制）
   * - 这确保了分析准确性（基于全量数据），同时减少了K线数据传输量（只传输最近N个月）
   * 
   * @param symbolInput 股票代码
   * @param sdt 开始日期（YYYYMMDD）
   * @param edt 结束日期（YYYYMMDD，可选）
   * @param freq 周期名称（如 "30分钟"、"60分钟"、"日线"）
   * @param baseFreqInput 基础周期（默认 "1分钟"）
   * @param barsOffset K线数据偏移量（默认 0）
   * @param barsLimit K线数据数量限制（默认 0，表示返回全部；>0 时只返回指定数量）
   * @param fxsOffset 分型数据偏移量（默认 0）
   * @param fxsLimit 分型数据数量限制（默认 0，表示返回全部）
   * @param bisOffset 笔数据偏移量（默认 0）
   * @param bisLimit 笔数据数量限制（默认 0，表示返回全部）
   * @param append 是否追加到现有数据（默认 false，表示替换）
   * @param recentMonths 返回最近N个月的K线数据（默认3，表示返回最近3个月；0表示返回全部）
   */
  async function fetchSingleFreq(
    symbolInput: string,
    sdt: string,
    edt?: string,
    freq: string = '30分钟',
    baseFreqInput: string = '1分钟',
    barsOffset: number = 0,
    barsLimit: number = 0,
    fxsOffset: number = 0,
    fxsLimit: number = 0,
    bisOffset: number = 0,
    bisLimit: number = 0,
    append: boolean = false,
    recentMonths: number = 3
  ) {
    const edtStr = edt || new Date().toISOString().split('T')[0].replace(/-/g, '');
    
    // 如果是追加模式且缓存有效，检查是否需要加载更多
    if (append && isCacheValid(freq, sdt, edtStr)) {
      const cacheItem = localCzscCache.value.get(freq)!;
      const pagination = cacheItem.pagination;
      // 如果已经加载了所有数据，直接返回缓存
      if (pagination) {
        const barsComplete = barsLimit === 0 || (pagination.bars.loaded >= pagination.bars.total);
        const fxsComplete = fxsLimit === 0 || (pagination.fxs.loaded >= pagination.fxs.total);
        const bisComplete = bisLimit === 0 || (pagination.bis.loaded >= pagination.bis.total);
        if (barsComplete && fxsComplete && bisComplete) {
          console.log(`[StockDetail] 所有数据已加载，使用缓存: ${symbolInput} ${freq}`);
          return cacheItem.data;
        }
      }
    } else if (!append && isCacheValid(freq, sdt, edtStr)) {
      // 非追加模式且缓存有效，直接返回
      console.log(`[StockDetail] 使用缓存数据: ${symbolInput} ${freq} ${sdt}~${edtStr}`);
      return localCzscCache.value.get(freq)!.data;
    }

    loading.value = true;
    error.value = null;
    symbol.value = symbolInput;
    baseFreq.value = baseFreqInput;

    try {
      // 将周期名称转换为 freqs 参数
      let freqsParam = '';
      let includeDaily = false;
      if (freq === '日线') {
        freqsParam = ''; // 空字符串表示不请求分钟周期
        includeDaily = true;
      } else {
        // 提取分钟数：如 "30分钟" -> "30"
        const match = freq.match(/(\d+)分钟/);
        if (match) {
          freqsParam = match[1];
        } else {
          throw new Error(`无效的周期名称: ${freq}`);
        }
      }

      const result = await analysisApi.getLocalCzscSingleFreq(
        symbolInput,
        sdt,
        edt,
        freqsParam,
        includeDaily,
        baseFreqInput,
        barsOffset,
        barsLimit,
        fxsOffset,
        fxsLimit,
        bisOffset,
        bisLimit,
        recentMonths
      );

      // 验证返回的数据只包含请求的周期
      const returnedFreqs = Object.keys(result.items || {});
      if (returnedFreqs.length > 1) {
        console.warn(
          `[StockDetail] 后端返回了多个周期: ${returnedFreqs.join(', ')} 请求周期: ${freq}`,
          { result, requestedFreq: freq }
        );
      } else if (returnedFreqs.length === 1 && returnedFreqs[0] !== freq) {
        console.warn(
          `[StockDetail] 后端返回的周期与请求不一致: 请求=${freq} 返回=${returnedFreqs[0]}`,
          { result, requestedFreq: freq }
        );
      }

      // 处理分页数据的追加或替换
      const cacheItem = localCzscCache.value.get(freq);
      if (append && cacheItem && cacheItem.sdt === sdt && cacheItem.edt === edtStr) {
        // 追加模式：合并数据
        const existingItem = cacheItem.data.items[freq];
        const newItem = result.items[freq];
        if (existingItem && newItem) {
          // 合并 bars（追加到前面，因为新数据是更早的）
          existingItem.bars = [...newItem.bars, ...existingItem.bars];
          // 合并 fxs
          existingItem.fxs = [...newItem.fxs, ...existingItem.fxs];
          // 合并 bis
          existingItem.bis = [...newItem.bis, ...existingItem.bis];
        }
        // 更新分页信息
        const pagination = result.pagination?.[freq];
        if (pagination) {
          cacheItem.pagination = {
            bars: {
              loaded: pagination.bars?.returned || 0,
              total: pagination.bars?.total || 0,
            },
            fxs: {
              loaded: pagination.fxs?.returned || 0,
              total: pagination.fxs?.total || 0,
            },
            bis: {
              loaded: pagination.bis?.returned || 0,
              total: pagination.bis?.total || 0,
            },
          };
        }
        console.log(
          `[StockDetail] 分页数据已追加: ${symbolInput} ${freq} bars=${existingItem?.bars.length} fxs=${existingItem?.fxs.length} bis=${existingItem?.bis.length}`
        );
        return cacheItem.data;
      } else {
        // 替换模式：直接存储新数据
        const pagination = result.pagination?.[freq];
        localCzscCache.value.set(freq, {
          data: result,
          sdt,
          edt: edtStr,
          pagination: pagination
            ? {
                bars: {
                  loaded: pagination.bars?.returned || 0,
                  total: pagination.bars?.total || 0,
                },
                fxs: {
                  loaded: pagination.fxs?.returned || 0,
                  total: pagination.fxs?.total || 0,
                },
                bis: {
                  loaded: pagination.bis?.returned || 0,
                  total: pagination.bis?.total || 0,
                },
              }
            : undefined,
        });

        console.log(
          `[StockDetail] 周期数据已缓存: ${symbolInput} ${freq} ${sdt}~${edtStr} 返回周期=${returnedFreqs.join(', ')} 分页=${JSON.stringify(pagination)}`
        );

        return result;
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '获取分析数据失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * @deprecated 使用 fetchSingleFreq 替代，支持按需加载和缓存
   * 获取多个周期的数据（一次性加载所有周期，性能较差）
   */
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
      // 将多周期结果拆分为单周期缓存
      if (result.items) {
        const edtStr = edt || new Date().toISOString().split('T')[0].replace(/-/g, '');
        Object.keys(result.items).forEach((freq) => {
          const singleResult: LocalCzscResponseData = {
            ...result,
            items: { [freq]: result.items[freq] },
          };
          localCzscCache.value.set(freq, {
            data: singleResult,
            sdt,
            edt: edtStr,
          });
        });
      }
      const keys = Object.keys(result.items || {});
      if (keys.length > 0 && !keys.includes(activeFreq.value)) {
        activeFreq.value = keys.includes('30分钟') ? '30分钟' : keys[0];
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || '获取分析数据失败';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  /**
   * 加载更多K线数据
   */
  async function loadMoreBars(
    symbolInput: string,
    sdt: string,
    edt: string,
    freq: string,
    baseFreqInput: string,
    recentMonths: number = 3
  ) {
    const cacheItem = localCzscCache.value.get(freq);
    if (!cacheItem) {
      throw new Error(`周期 ${freq} 的缓存不存在，请先调用 fetchSingleFreq`);
    }

    const pagination = cacheItem.pagination;
    if (!pagination || pagination.bars.loaded >= pagination.bars.total) {
      console.log(`[StockDetail] 所有K线数据已加载: ${freq}`);
      return cacheItem.data;
    }

    const barsOffset = pagination.bars.loaded;
    const barsLimit = 100; // 默认每页100条

    return await fetchSingleFreq(
      symbolInput,
      sdt,
      edt,
      freq,
      baseFreqInput,
      barsOffset,
      barsLimit,
      0,
      0,
      0,
      0,
      true, // append = true
      recentMonths
    );
  }

  /**
   * 加载更多分型数据
   */
  async function loadMoreFxs(
    symbolInput: string,
    sdt: string,
    edt: string,
    freq: string,
    baseFreqInput: string,
    recentMonths: number = 3
  ) {
    const cacheItem = localCzscCache.value.get(freq);
    if (!cacheItem) {
      throw new Error(`周期 ${freq} 的缓存不存在，请先调用 fetchSingleFreq`);
    }

    const pagination = cacheItem.pagination;
    if (!pagination || pagination.fxs.loaded >= pagination.fxs.total) {
      console.log(`[StockDetail] 所有分型数据已加载: ${freq}`);
      return cacheItem.data;
    }

    const fxsOffset = pagination.fxs.loaded;
    const fxsLimit = 50; // 默认每页50条

    return await fetchSingleFreq(
      symbolInput,
      sdt,
      edt,
      freq,
      baseFreqInput,
      0,
      0,
      fxsOffset,
      fxsLimit,
      0,
      0,
      true, // append = true
      recentMonths
    );
  }

  /**
   * 加载更多笔数据
   */
  async function loadMoreBis(
    symbolInput: string,
    sdt: string,
    edt: string,
    freq: string,
    baseFreqInput: string,
    recentMonths: number = 3
  ) {
    const cacheItem = localCzscCache.value.get(freq);
    if (!cacheItem) {
      throw new Error(`周期 ${freq} 的缓存不存在，请先调用 fetchSingleFreq`);
    }

    const pagination = cacheItem.pagination;
    if (!pagination || pagination.bis.loaded >= pagination.bis.total) {
      console.log(`[StockDetail] 所有笔数据已加载: ${freq}`);
      return cacheItem.data;
    }

    const bisOffset = pagination.bis.loaded;
    const bisLimit = 50; // 默认每页50条

    return await fetchSingleFreq(
      symbolInput,
      sdt,
      edt,
      freq,
      baseFreqInput,
      0,
      0,
      0,
      0,
      bisOffset,
      bisLimit,
      true, // append = true
      recentMonths
    );
  }

  function clear() {
    symbol.value = '';
    localCzscCache.value.clear();
    error.value = null;
  }

  return {
    // 状态
    symbol,
    localCzsc, // computed 属性
    localCzscCache, // 原始缓存 Map（用于调试）
    loading,
    error,
    activeFreq,
    baseFreq,
    freqs,
    // 操作
    fetchSingleFreq,
    loadMoreBars,
    loadMoreFxs,
    loadMoreBis,
    fetchLocalCzsc, // 保留为兼容性方法
    clear,
  };
});
