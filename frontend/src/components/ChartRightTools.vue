<template>
  <div class="chart-right-tools">
    <div class="chart-toolbar">
      <el-switch v-model="smcEnabled" size="small" active-text="SMC" inactive-text="SMC" />
      <el-switch v-model="czscBsEnabled" size="small" active-text="麒麟买卖点" inactive-text="麒麟买卖点" />
      <div v-if="czscBsEnabled" class="czsc-toolbar">
        <el-select v-model="czscMode" size="small" style="width: 100px" title="麒麟模式">
          <el-option label="ZSLX 递归" value="zslx" />
          <el-option label="简化版" value="simple" />
        </el-select>
        <template v-if="czscMode === 'zslx'">
          <el-select v-model="czscPenType" size="small" style="width: 88px" title="笔类型">
            <el-option label="老笔" value="old" />
            <el-option label="新笔" value="new" />
            <el-option label="分型笔" value="fractal" />
          </el-select>
          <el-input-number v-model="czscMinKlinesPerPen" size="small" :min="1" :max="20" controls-position="right" style="width: 96px" title="每笔最少K线数" />
        </template>
      </div>
      <div v-if="smcEnabled" class="smc-toolbar">
        <el-switch v-model="smcShowFvg" size="small" active-text="FVG" inactive-text="FVG" />
        <el-switch v-model="smcShowZones" size="small" active-text="Zones" inactive-text="Zones" />
        <el-switch v-model="smcShowSwingOb" size="small" active-text="Swing OB" inactive-text="Swing OB" />
        <el-switch v-model="smcNoInternalOb" size="small" active-text="No Internal OB" inactive-text="No Internal OB" />
      </div>
      <el-button size="small" :loading="pineTSLoading" @click="$emit('run-pine-ts')">
        Squeeze (PineTS)
      </el-button>
    </div>
    <div v-if="pineTSResult || pineTSError" class="pinets-result-panel">
      <div v-if="pineTSError" class="pinets-error">{{ pineTSError }}</div>
      <template v-else-if="pineTSResult">
        <div class="pinets-title">PineTS 执行结果（Squeeze Momentum 源码）</div>
        <div class="pinets-meta">共 {{ pineTSResult.momentum.length }} 根 · 最近 30 个动量值：</div>
        <div class="pinets-values">{{ lastMomentumText }}</div>
        <div class="pinets-sparkline" :title="lastMomentumText">
          <span
            v-for="(bar, i) in sparkBars"
            :key="i"
            class="spark-dot"
            :style="{ backgroundColor: bar.color, height: bar.height + '%' }"
          />
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElSwitch, ElButton } from 'element-plus';
import type { SqueezeMomentumResult } from '../tv/pineTSRunner';

interface SparkBar {
  color: string;
  height: number;
}

defineProps<{
  pineTSLoading: boolean;
  pineTSResult: SqueezeMomentumResult | null;
  pineTSError: string;
  lastMomentumText: string;
  sparkBars: SparkBar[];
}>();

const emit = defineEmits<{
  (e: 'update:smcEnabled', v: boolean): void;
  (e: 'update:smcShowFvg', v: boolean): void;
  (e: 'update:smcShowZones', v: boolean): void;
  (e: 'update:smcShowSwingOb', v: boolean): void;
  (e: 'update:smcNoInternalOb', v: boolean): void;
  (e: 'update:czscBsEnabled', v: boolean): void;
  (e: 'update:czscMode', v: 'simple' | 'zslx'): void;
  (e: 'update:czscMinKlinesPerPen', v: number): void;
  (e: 'update:czscPenType', v: 'old' | 'new' | 'fractal'): void;
  (e: 'run-pine-ts'): void;
}>();

const smcEnabled = defineModel<boolean>('smcEnabled', { default: false });
const czscBsEnabled = defineModel<boolean>('czscBsEnabled', { default: false });
const czscMode = defineModel<'simple' | 'zslx'>('czscMode', { default: 'zslx' });
const czscMinKlinesPerPen = defineModel<number>('czscMinKlinesPerPen', { default: 5 });
const czscPenType = defineModel<'old' | 'new' | 'fractal'>('czscPenType', { default: 'new' });
const smcShowFvg = defineModel<boolean>('smcShowFvg', { default: false });
const smcShowZones = defineModel<boolean>('smcShowZones', { default: false });
const smcShowSwingOb = defineModel<boolean>('smcShowSwingOb', { default: false });
const smcNoInternalOb = defineModel<boolean>('smcNoInternalOb', { default: false });
</script>

<style scoped>
.chart-right-tools {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chart-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.czsc-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.smc-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.pinets-result-panel {
  padding: 10px 12px;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  font-size: 12px;
}
.pinets-error {
  color: var(--el-color-danger);
}
.pinets-title {
  font-weight: 600;
  margin-bottom: 6px;
}
.pinets-meta {
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}
.pinets-values {
  word-break: break-all;
  max-height: 3em;
  overflow: auto;
  margin-bottom: 8px;
}
.pinets-sparkline {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 24px;
}
.pinets-sparkline .spark-dot {
  flex: 1;
  min-width: 2px;
  border-radius: 1px;
  opacity: 0.85;
}
</style>
