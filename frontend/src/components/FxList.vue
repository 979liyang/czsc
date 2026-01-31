<template>
  <div class="fx-list">
    <el-table :data="sortedFxs" stripe style="width: 100%" max-height="400">
      <el-table-column prop="dt" label="时间" width="150" sortable />
      <el-table-column prop="mark" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.mark === '顶分型' ? 'danger' : 'success'">
            {{ row.mark }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="fx" label="分型价格" width="120" />
      <el-table-column prop="high" label="最高" width="100" />
      <el-table-column prop="low" label="最低" width="100" />
      <el-table-column prop="power_str" label="力度" width="80" />
    </el-table>
    <div v-if="fxs.length === 0" class="empty-tip">
      暂无分型数据
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ElTable, ElTableColumn, ElTag } from 'element-plus';
import type { FX } from '../types';

interface Props {
  fxs: FX[];
}

const props = defineProps<Props>();

// 按时间排序（降序，最新的在前）
const sortedFxs = computed(() => {
  return [...props.fxs].sort((a, b) => {
    return new Date(b.dt).getTime() - new Date(a.dt).getTime();
  });
});
</script>

<style scoped>
.fx-list {
  width: 100%;
}

.empty-tip {
  text-align: center;
  padding: 20px;
  color: #909399;
}
</style>
