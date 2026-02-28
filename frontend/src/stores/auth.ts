/**
 * 认证状态：登录、退出、当前用户
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import * as authApi from '../api/auth';
import type { UserResponse } from '../api/auth';

const TOKEN_KEY = 'czsc_token';

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(sessionStorage.getItem(TOKEN_KEY));
  const user = ref<UserResponse | null>(null);

  const isLoggedIn = computed(() => !!token.value);

  const canAccessAdvanced = computed(() => {
    const u = user.value;
    return !!u?.feature_flags?.includes('advanced') || u?.role === 'admin';
  });

  const canAccessPremium = computed(() => {
    const u = user.value;
    return !!u?.feature_flags?.includes('premium') || u?.role === 'admin';
  });

  function setToken(t: string | null) {
    token.value = t;
    if (t) sessionStorage.setItem(TOKEN_KEY, t);
    else sessionStorage.removeItem(TOKEN_KEY);
  }

  function setUser(u: UserResponse | null) {
    user.value = u;
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password });
    setToken(res.access_token);
    setUser(res.user);
    return res;
  }

  async function register(username: string, password: string) {
    const res = await authApi.register({ username, password });
    setToken(res.access_token);
    setUser(res.user);
    return res;
  }

  function logout() {
    setToken(null);
    setUser(null);
    authApi.logout().catch(() => {});
  }

  async function fetchUser() {
    if (!token.value) return null;
    const u = await authApi.getCurrentUser();
    setUser(u ?? null);
    return u;
  }

  return {
    token,
    user,
    isLoggedIn,
    canAccessAdvanced,
    canAccessPremium,
    login,
    register,
    logout,
    fetchUser,
    setToken,
    setUser,
  };
});
