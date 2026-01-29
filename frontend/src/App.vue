<template>
  <el-container>
    <el-header>
      <div class="header-content">
        <h1>CZSC缠论分析系统</h1>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="header-menu"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/analysis">缠论分析</el-menu-item>
          <el-menu-item index="/signals">信号函数</el-menu-item>
          <el-menu-item index="/examples">策略示例</el-menu-item>
          <el-menu-item index="/backtest">策略回测</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { ElContainer, ElHeader, ElMain, ElMenu, ElMenuItem } from 'element-plus';

const route = useRoute();
const activeMenu = computed(() => route.path);
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 20px;
}

.header-menu {
  border-bottom: none;
}
</style>
