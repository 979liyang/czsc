/**
 * 自选股状态：列表、添加、删除
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useAuthStore } from './auth';
import * as watchlistApi from '../api/watchlist';
import type { WatchlistItem } from '../api/watchlist';

export const useWatchlistStore = defineStore('watchlist', () => {
  const authStore = useAuthStore();
  const items = ref<WatchlistItem[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const symbols = computed(() => items.value.map((i) => i.symbol));

  async function load() {
    if (!authStore.isLoggedIn) {
      items.value = [];
      return;
    }
    loading.value = true;
    error.value = null;
    try {
      const res = await watchlistApi.getWatchlist();
      items.value = res.items;
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? '加载失败';
      items.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function add(symbol: string) {
    if (!authStore.isLoggedIn) return;
    const s = symbol.trim().toUpperCase();
    if (!s) return;
    error.value = null;
    try {
      const item = await watchlistApi.addWatchlist(s);
      if (!items.value.find((i) => i.symbol === item.symbol)) {
        items.value = [...items.value, item];
      }
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? '添加失败';
      throw e;
    }
  }

  async function remove(symbol: string) {
    if (!authStore.isLoggedIn) return;
    error.value = null;
    try {
      await watchlistApi.removeWatchlist(symbol);
      items.value = items.value.filter((i) => i.symbol !== symbol);
    } catch (e: any) {
      error.value = e?.response?.data?.detail ?? '删除失败';
      throw e;
    }
  }

  return {
    items,
    symbols,
    loading,
    error,
    load,
    add,
    remove,
  };
});
