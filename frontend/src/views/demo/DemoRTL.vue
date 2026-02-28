<template>
  <div class="demo-rtl" dir="rtl">
    <el-card shadow="hover" header="RTL 布局示例">
      <p>此页面为从 web-demo 迁移的 RTL 示例，使用 <code>dir="rtl"</code> 实现从右到左布局。</p>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-card shadow="hover" body-style="padding: 16px">区块 1</el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" body-style="padding: 16px">区块 2</el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" body-style="padding: 16px">区块 3</el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'DemoRTL' });
</script>

<style scoped>
.demo-rtl code { padding: 2px 6px; background: var(--el-fill-color-light); border-radius: 4px; }
</style>
