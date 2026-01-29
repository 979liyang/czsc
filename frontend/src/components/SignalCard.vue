<template>
  <el-card
    class="signal-card"
    shadow="hover"
    :body-style="{ padding: '15px' }"
    @click="$emit('click')"
  >
    <div class="card-header">
      <h3 class="signal-name">{{ signal.name }}</h3>
      <el-tag :type="getCategoryType(signal.category)" size="small">
        {{ signal.category }}
      </el-tag>
    </div>
    <div class="card-body">
      <p class="signal-description">
        {{ truncateDescription(signal.description) }}
      </p>
      <div class="signal-meta">
        <span class="meta-item">
          <el-icon><Document /></el-icon>
          {{ signal.params.length }} 个参数
        </span>
        <span class="meta-item">
          <el-icon><List /></el-icon>
          {{ signal.signals.length }} 个信号
        </span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ElCard, ElTag, ElIcon } from 'element-plus';
import { Document, List } from '@element-plus/icons-vue';
import type { SignalInfo } from '../api/docs';

interface Props {
  signal: SignalInfo;
}

defineProps<Props>();
defineEmits<{
  click: [];
}>();

const truncateDescription = (desc: string, maxLength: number = 100): string => {
  if (!desc) return '暂无说明';
  if (desc.length <= maxLength) return desc;
  return desc.substring(0, maxLength) + '...';
};

const getCategoryType = (category: string): string => {
  const typeMap: Record<string, string> = {
    '缠论类': 'danger',
    '技术指标类': 'success',
    'K线形态类': 'warning',
    '成交量类': 'info',
    '股票特定类': '',
    '持仓状态类': 'success',
    '角度类': 'warning',
    '基础类': 'info',
    '其他类': '',
    '笔相关': 'danger',
    '选股类': 'success',
  };
  return typeMap[category] || '';
};
</script>

<style scoped>
.signal-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.signal-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.signal-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-body {
  margin-top: 10px;
}

.signal-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 10px 0;
  min-height: 48px;
}

.signal-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
