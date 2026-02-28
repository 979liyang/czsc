<template>
  <el-container class="layout-dashboard">
    <el-aside :width="sidebarCollapsed ? '64px' : '130px'" class="layout-aside">
      <div class="logo">
        <span v-if="!sidebarCollapsed">KT</span>
        <span v-else>K</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        :collapse="sidebarCollapsed"
        class="sidebar-menu"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/watchlist">
          <el-icon><Star /></el-icon>
          <template #title>自选股</template>
        </el-menu-item>
        <el-menu-item index="/tv">
          <el-icon><Monitor /></el-icon>
          <template #title>TV 分析</template>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><TrendCharts /></el-icon>
          <template #title>麒麟分析</template>
        </el-menu-item>
        <el-menu-item index="/signal-analyze">
          <el-icon><DataLine /></el-icon>
          <template #title>信号分析</template>
        </el-menu-item>
        <el-menu-item index="/strategy-analyze">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>策略分析</template>
        </el-menu-item>
        <el-menu-item index="/screen">
          <el-icon><Search /></el-icon>
          <template #title>全盘扫描</template>
        </el-menu-item>
        <el-menu-item index="/data-fetch">
          <el-icon><Upload /></el-icon>
          <template #title>数据拉取</template>
        </el-menu-item>
        <el-menu-item index="/data-quality">
          <el-icon><DocumentChecked /></el-icon>
          <template #title>数据质量</template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><Setting /></el-icon>
          <template #title>个人资料</template>
        </el-menu-item>
        <!-- <el-menu-item index="/signals">
          <el-icon><Operation /></el-icon>
          <template #title>信号函数</template>
        </el-menu-item>
        <el-menu-item index="/examples">
          <el-icon><Document /></el-icon>
          <template #title>策略示例</template>
        </el-menu-item> -->
        <!-- <el-sub-menu index="/demo" popper-class="demo-submenu">
          <template #title>
            <el-icon><Grid /></el-icon>
            <span>Web Demo</span>
          </template>
          <el-menu-item index="/demo/dashboard">仪表盘</el-menu-item>
          <el-menu-item index="/demo/tables">表格</el-menu-item>
          <el-menu-item index="/demo/billing">账单</el-menu-item>
          <el-menu-item index="/demo/profile">个人资料</el-menu-item>
          <el-menu-item index="/demo/rtl">RTL</el-menu-item>
          <el-menu-item index="/demo/layout">布局</el-menu-item>
        </el-sub-menu> -->
      </el-menu>
    </el-aside>
    <el-container direction="vertical">
      <!-- <el-header class="layout-header" height="56px">
        <el-button
          text
          :icon="sidebarCollapsed ? Expand : Fold"
          @click="sidebarCollapsed = !sidebarCollapsed"
        />
        <div class="header-user">
          <template v-if="authStore.isLoggedIn">
            <span class="username">{{ authStore.user?.username ?? '' }}</span>
            <el-button type="primary" link @click="onLogout">退出</el-button>
          </template>
        </div>
      </el-header> -->
      <AuthLoginDialog
        :visible="loginDialogVisible"
        @close="loginDialogVisible = false"
        @success="onAuthSuccess"
        @switch-to-register="loginDialogVisible = false; registerDialogVisible = true"
      />
      <AuthRegisterDialog
        :visible="registerDialogVisible"
        @close="registerDialogVisible = false"
        @success="onAuthSuccess"
        @switch-to-login="registerDialogVisible = false; loginDialogVisible = true"
      />
      <el-main class="layout-main">
        <router-view />
      </el-main>
      <el-footer class="layout-footer" height="40px">
        Kylin Trading Pro分析系统
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  HomeFilled,
  Fold,
  Expand,
  TrendCharts,
  DataLine,
  DataAnalysis,
  Monitor,
  Star,
  Search,
  Setting,
  Upload,
  DocumentChecked,
} from '@element-plus/icons-vue';
import { useAuthStore } from '../stores/auth';
import AuthLoginDialog from '../components/AuthLoginDialog.vue';
import AuthRegisterDialog from '../components/AuthRegisterDialog.vue';

defineOptions({ name: 'LayoutDashboard' });

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const sidebarCollapsed = ref(true);
const loginDialogVisible = ref(false);
const registerDialogVisible = ref(false);

function onAuthSuccess() {
  loginDialogVisible.value = false;
  registerDialogVisible.value = false;
  authStore.fetchUser();
}

function onLogout() {
  authStore.logout();
  router.push('/sign-in');
}

onMounted(() => {
  if (authStore.isLoggedIn && !authStore.user) {
    authStore.fetchUser();
  }
});

const activeMenu = computed(() => route.path);

const titleMap: Record<string, string> = {
  '/': '首页',
  '/analysis': '麒麟分析',
  '/signals': '信号函数',
  '/examples': '策略示例',
  '/signal-analyze': '信号分析',
  '/screen': '全盘扫描',
  '/data-fetch': '数据拉取',
  '/data-quality': '数据质量',
  '/backtest': '策略回测',
  '/strategy-analyze': '策略分析',
  '/watchlist': '自选股',
  '/profile': '个人资料',
  '/demo/dashboard': 'Demo 仪表盘',
  '/demo/tables': 'Demo 表格',
  '/demo/billing': 'Demo 账单',
  '/demo/profile': 'Demo 个人资料',
  '/demo/rtl': 'Demo RTL',
  '/demo/layout': 'Demo 布局',
};

const currentTitle = computed(() => titleMap[route.path] ?? route.meta?.title ?? 'Kylin Trading Pro分析系统');
</script>

<style scoped>
.layout-dashboard {
  min-height: 100vh;
}

.layout-aside {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  transition: width 0.2s;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.sidebar-menu {
  border-right: none;
}

.layout-header {
  display: flex;
  align-items: center;
  padding: 0 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-title {
  margin-left: 12px;
  font-size: 16px;
  flex: 1;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-user .username {
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.layout-main {
  flex: 1;
  padding: 16px;
  background: var(--el-fill-color-blank);
  overflow: auto;
}

.layout-footer {
  text-align: center;
  line-height: 40px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
