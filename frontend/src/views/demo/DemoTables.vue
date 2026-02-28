<template>
  <div class="demo-tables">
    <el-row :gutter="24">
      <el-col :span="24" class="mb-24">
        <el-card shadow="hover" header="作者列表">
          <el-table :data="authorsData" stripe>
            <el-table-column prop="author" label="作者" />
            <el-table-column prop="func" label="职能" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="employed" label="入职时间" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="24">
        <el-card shadow="hover" header="项目列表">
          <el-table :data="projectsData" stripe>
            <el-table-column prop="project" label="项目" />
            <el-table-column prop="budget" label="预算" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.statusType">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="completion" label="完成度" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({ name: 'DemoTables' });

const authorsData = ref([
  { author: '张三', func: '经理', status: '在线', statusType: 'success', employed: '2022-01-15' },
  { author: '李四', func: '开发', status: '离线', statusType: 'info', employed: '2023-03-20' },
  { author: '王五', func: '设计', status: '忙碌', statusType: 'warning', employed: '2021-06-10' },
]);

const projectsData = ref([
  { project: '项目 Alpha', budget: '¥12,000', status: '进行中', statusType: 'primary', completion: '60%' },
  { project: '项目 Beta', budget: '¥8,500', status: '已完成', statusType: 'success', completion: '100%' },
  { project: '项目 Gamma', budget: '¥20,000', status: '待启动', statusType: 'info', completion: '0%' },
]);
</script>

<style scoped>
.demo-tables .mb-24 { margin-bottom: 24px; }
</style>
