<template>
  <div class="demo-billing">
    <el-row :gutter="24">
      <el-col :xs="24" :md="16">
        <el-row :gutter="24">
          <el-col :xs="24" :xl="12" class="mb-24">
            <el-card shadow="hover" header="信用卡">
              <div class="credit-placeholder">**** **** **** 4242</div>
              <div class="credit-meta">有效期 12/25</div>
            </el-card>
          </el-col>
          <el-col :xs="24" :xl="12" class="mb-24">
            <el-card shadow="hover" header="支付方式">
              <el-radio-group v-model="paymentMethod">
                <el-radio value="card">信用卡</el-radio>
                <el-radio value="paypal">PayPal</el-radio>
              </el-radio-group>
            </el-card>
          </el-col>
          <el-col :span="24" class="mb-24">
            <el-card shadow="hover" header="发票信息">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="公司">示例科技有限公司</el-descriptions-item>
                <el-descriptions-item label="税号">91xxxxxxxxxx</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-col>
      <el-col :xs="24" :md="8" class="mb-24">
        <el-card shadow="hover" header="最近发票">
          <el-table :data="invoices" stripe size="small">
            <el-table-column prop="id" label="编号" width="80" />
            <el-table-column prop="date" label="日期" />
            <el-table-column prop="amount" label="金额" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({ name: 'DemoBilling' });

const paymentMethod = ref('card');
const invoices = ref([
  { id: '#INV-001', date: '2024-01-10', amount: '¥1,200' },
  { id: '#INV-002', date: '2024-01-05', amount: '¥800' },
]);
</script>

<style scoped>
.demo-billing .mb-24 { margin-bottom: 24px; }
.credit-placeholder { font-size: 18px; letter-spacing: 2px; margin-bottom: 8px; }
.credit-meta { font-size: 12px; color: var(--el-text-color-secondary); }
</style>
