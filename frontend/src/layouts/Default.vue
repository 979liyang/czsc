<template>
  <el-container class="layout-default">
    <el-header class="layout-header">
      <div class="header-content">
        <h1>Kylin Trading Pro分析系统</h1>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="header-menu"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/analysis">麒麟分析</el-menu-item>
          <el-menu-item index="/signals">信号函数</el-menu-item>
          <el-menu-item index="/examples">策略示例</el-menu-item>
          <el-menu-item index="/backtest">策略回测</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="layout-main">
      <router-view />
    </el-main>
    <el-footer class="layout-footer" height="48px">
      Kylin Trading Pro分析系统 · 麒麟 K 线分析
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

defineOptions({ name: 'LayoutDefault' });

const route = useRoute();
const activeMenu = computed(() => route.path);
</script>

<style scoped>
.layout-default {
  min-height: 100vh;
}

.layout-header {
  padding: 0 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 18px;
}

.header-menu {
  border-bottom: none;
}

.layout-main {
  flex: 1;
  padding: 16px;
}

.layout-footer {
  text-align: center;
  line-height: 48px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
