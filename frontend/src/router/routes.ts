/**
 * 路由配置
 */
import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    meta: { layout: 'dashboard', requiresAuth: true },
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/analysis',
    name: 'Analysis',
    meta: { layout: 'dashboard', requiresAuth: true, title: '麒麟分析' },
    component: () => import('../views/Analysis.vue'),
  },
  {
    path: '/signal-analyze',
    name: 'SignalAnalyze',
    meta: { layout: 'dashboard', requiresAuth: true, title: '信号分析' },
    component: () => import('../views/StockAnalyze.vue'),
  },
  {
    path: '/strategy-analyze',
    name: 'StrategyAnalyze',
    meta: { layout: 'dashboard', requiresAuth: true, title: '策略分析' },
    component: () => import('../views/StrategyAnalyze.vue'),
  },
  {
    path: '/screen',
    name: 'ScreenScan',
    meta: { layout: 'dashboard', requiresAuth: true, title: '全盘扫描' },
    component: () => import('../views/ScreenScan.vue'),
  },
  {
    path: '/watchlist',
    name: 'Watchlist',
    meta: { layout: 'dashboard', requiresAuth: true, title: '自选股' },
    component: () => import('../views/Watchlist.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    meta: { layout: 'dashboard', requiresAuth: true, title: '个人资料' },
    component: () => import('../views/Profile.vue'),
  },
  {
    path: '/data-quality',
    name: 'DataQuality',
    meta: { layout: 'dashboard', requiresAuth: true, title: '数据质量' },
    component: () => import('../views/DataQuality.vue'),
  },
  {
    path: '/data-fetch',
    name: 'DataFetch',
    meta: { layout: 'dashboard', requiresAuth: true, title: '数据拉取' },
    component: () => import('../views/DataFetch.vue'),
  },
  {
    path: '/tv',
    name: 'TradingViewChart',
    meta: { layout: 'empty', requiresAuth: true, title: 'TradingView 图表' },
    component: () => import('../views/TradingViewChart.vue'),
  },
  {
    path: '/sign-in',
    name: 'SignIn',
    meta: { layout: 'empty', requiresAuth: false, title: '登录' },
    component: () => import('../views/SignIn.vue'),
  },
  {
    path: '/sign-up',
    name: 'SignUp',
    meta: { layout: 'empty', requiresAuth: false, title: '注册' },
    component: () => import('../views/SignUp.vue'),
  },
  {
    path: '/signals',
    name: 'Signals',
    meta: { layout: 'dashboard', requiresAuth: true, title: '信号文档' },
    component: () => import('../views/Signals.vue'),
  },
  {
    path: '/examples',
    name: 'Examples',
    meta: { layout: 'dashboard', requiresAuth: true, title: '策略示例' },
    component: () => import('../views/Examples.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    meta: { layout: 'empty' },
    component: () => import('../views/demo/NotFound.vue'),
  },
  // ------------------------------------demo ----------------------------------
  {
    path: '/demo-czsc-chart',
    name: 'CzscChartDemo',
    meta: { layout: 'dashboard', requiresAuth: true },
    component: () => import('../views/CzscChartDemo.vue'),
  },
  {
    path: '/demo-czsc-analyze',
    name: 'CzscChartAnalyzeDemo',
    meta: { layout: 'dashboard', requiresAuth: true },
    component: () => import('../views/CzscChartAnalyzeDemo.vue'),
  },
  {
    path: '/demo',
    redirect: '/demo/dashboard',
  },
  {
    path: '/stock/:symbol',
    name: 'StockDetail',
    meta: { layout: 'dashboard', requiresAuth: true, title: '股票详情' },
    component: () => import('../views/StockDetail.vue'),
  },
  {
    path: '/demo/shapes',
    name: 'ChartShapesDemo',
    meta: { layout: 'empty', title: '图形参数调试', requiresAuth: true },
    component: () => import('../views/ChartShapesDemo.vue'),
  },
  {
    path: '/demo/dashboard',
    name: 'DemoDashboard',
    meta: { layout: 'dashboard', title: 'Demo 仪表盘', requiresAuth: true },
    component: () => import('../views/demo/DemoDashboard.vue'),
  },
  {
    path: '/demo/tables',
    name: 'DemoTables',
    meta: { layout: 'dashboard', title: 'Demo 表格', requiresAuth: true },
    component: () => import('../views/demo/DemoTables.vue'),
  },
  {
    path: '/demo/billing',
    name: 'DemoBilling',
    meta: { layout: 'dashboard', title: 'Demo 账单', requiresAuth: true },
    component: () => import('../views/demo/DemoBilling.vue'),
  },
  {
    path: '/demo/profile',
    name: 'DemoProfile',
    meta: { layout: 'dashboard', title: 'Demo 个人资料', requiresAuth: true },
    component: () => import('../views/demo/DemoProfile.vue'),
  },
  {
    path: '/demo/rtl',
    name: 'DemoRTL',
    meta: { layout: 'dashboard', title: 'Demo RTL', requiresAuth: true },
    component: () => import('../views/demo/DemoRTL.vue'),
  },
  {
    path: '/demo/layout',
    name: 'DemoLayout',
    meta: { layout: 'dashboard', title: 'Demo 布局', requiresAuth: true },
    component: () => import('../views/demo/DemoLayout.vue'),
  },
];
