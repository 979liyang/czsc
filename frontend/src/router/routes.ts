/**
 * 路由配置
 */
import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('../views/Analysis.vue'),
  },
  {
    path: '/signals',
    name: 'Signals',
    component: () => import('../views/Signals.vue'),
  },
  {
    path: '/examples',
    name: 'Examples',
    component: () => import('../views/Examples.vue'),
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('../views/Backtest.vue'),
  },
  {
    path: '/stock/:symbol',
    name: 'StockDetail',
    component: () => import('../views/StockDetail.vue'),
  },
];
