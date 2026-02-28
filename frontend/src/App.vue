<template>
  <div id="app" class="font-sans antialiased">
    <component :is="layoutComponent">
      <router-view />
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

/** 根据当前路由 meta.layout 动态选择布局组件名，对应 main.ts 中注册的 layout-default / layout-dashboard */
const layoutComponent = computed(() => {
  const layout = (route.meta?.layout as string) || 'default';
  const name = String(layout).toLowerCase();
  return `layout-${name}`;
});
</script>
