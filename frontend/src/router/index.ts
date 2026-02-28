/**
 * Vue Router配置
 */
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { routes } from './routes';

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth === true && !authStore.isLoggedIn) {
    next({ path: '/sign-in', query: { redirect: to.fullPath } });
  } else {
    next();
  }
});

export default router;
