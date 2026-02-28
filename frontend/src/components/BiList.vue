<template>
  <div class="bi-list">
    <el-table :data="sortedBis" stripe style="width: 100%" max-height="400">
      <el-table-column label="开始时间" width="170" sortable>
        <template #default="{ row }">{{ formatDt(row.sdt) }}</template>
      </el-table-column>
      <el-table-column label="结束时间" width="170">
        <template #default="{ row }">{{ formatDt(row.edt) }}</template>
      </el-table-column>
      <el-table-column prop="direction" label="方向" width="70">
        <template #default="{ row }">
          <el-tag :type="row.direction === '向上' ? 'danger' : 'success'">
            {{ row.direction }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="high" label="最高" width="70" />
      <el-table-column prop="low" label="最低" width="70" />
      <el-table-column prop="power" label="力度" width="70" />
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

/** 将接口返回的 ISO 或日期时间字符串格式化为完整显示：YYYY-MM-DD HH:mm:ss */
function formatDt(dt: string | undefined): string {
  if (!dt) return '—';
  const s = String(dt).trim();
  if (s.includes('T')) {
    const [datePart, timePart] = s.split('T');
    const time = timePart ? timePart.replace(/\.\d+Z?$/i, '').slice(0, 8) : '00:00:00';
    return `${datePart} ${time}`;
  }
  if (s.length >= 19) return s.slice(0, 19);
  if (s.length >= 10) return `${s.slice(0, 10)} 00:00:00`;
  return s;
}

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
