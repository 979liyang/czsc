<template>
  <div class="demo-layout">
    <el-card shadow="hover" header="布局示例">
      <p>从 web-demo 迁移的布局展示页，当前使用 dashboard 布局（侧栏 + 顶栏）。</p>
      <el-row :gutter="24">
        <el-col :span="12">
          <el-card shadow="hover" body-style="padding: 24px">左侧内容</el-card>
        </el-col>
        <el-col :span="12">
          <el-card shadow="hover" body-style="padding: 24px">右侧内容</el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'DemoLayout' });
</script>
