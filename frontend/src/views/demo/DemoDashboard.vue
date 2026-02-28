<template>
  <div class="demo-dashboard">
    <el-row :gutter="24" class="mb-24">
      <el-col :xs="24" :sm="12" :lg="6" v-for="(stat, index) in stats" :key="index">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <span class="stat-value">{{ stat.prefix }}{{ stat.value }}{{ stat.suffix }}</span>
            <span class="stat-title">{{ stat.title }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="24">
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" header="图表示例">
          <div class="chart-placeholder">图表区域（可接入 ECharts）</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card shadow="hover" header="概览">
          <div class="chart-placeholder">概览区域</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="24" class="mt-24">
      <el-col :span="24">
        <el-card shadow="hover" header="项目列表">
          <el-table :data="tableData" stripe>
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="status" label="状态" />
            <el-table-column prop="date" label="日期" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({ name: 'DemoDashboard' });

const stats = ref([
  { title: '今日销售', value: 53000, prefix: '¥', suffix: '', icon: '' },
  { title: '今日用户', value: 1200, prefix: '', suffix: '', icon: '' },
  { title: '本月订单', value: 3840, prefix: '', suffix: '', icon: '' },
  { title: '收入', value: 89340, prefix: '¥', suffix: '', icon: '' },
]);

const tableData = ref([
  { name: '项目 A', status: '进行中', date: '2024-01-15' },
  { name: '项目 B', status: '已完成', date: '2024-01-10' },
  { name: '项目 C', status: '待开始', date: '2024-01-20' },
]);
</script>

<style scoped>
.demo-dashboard .mb-24 { margin-bottom: 24px; }
.demo-dashboard .mt-24 { margin-top: 24px; }
.stat-card .stat-content { display: flex; flex-direction: column; gap: 8px; }
.stat-value { font-size: 20px; font-weight: 600; }
.stat-title { font-size: 13px; color: var(--el-text-color-secondary); }
.chart-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  color: var(--el-text-color-secondary);
}
</style>
