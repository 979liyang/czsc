<template>
  <div class="bi-list">
    <el-table :data="sortedBis" stripe style="width: 100%" max-height="400">
      <el-table-column prop="sdt" label="开始时间" width="150" sortable />
      <el-table-column prop="edt" label="结束时间" width="150" />
      <el-table-column prop="direction" label="方向" width="80">
        <template #default="{ row }">
          <el-tag :type="row.direction === '向上' ? 'success' : 'danger'">
            {{ row.direction }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="high" label="最高" width="100" />
      <el-table-column prop="low" label="最低" width="100" />
      <el-table-column prop="power" label="力度" width="100" />
    </el-table>
    <div v-if="bis.length === 0" class="empty-tip">
      暂无笔数据
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElTable, ElTableColumn, ElTag } from 'element-plus';
import type { BI } from '../types';

interface Props {
  bis: BI[];
}

const props = defineProps<Props>();

// 按开始时间排序（降序，最新的在前）
const sortedBis = computed(() => {
  return [...props.bis].sort((a, b) => {
    return new Date(b.sdt).getTime() - new Date(a.sdt).getTime();
  });
});
</script>

<style scoped>
.bi-list {
  width: 100%;
}

.empty-tip {
  text-align: center;
  padding: 20px;
  color: #909399;
}
</style>
