<template>
  <div class="analysis-page">
    <el-card class="search-card">
      <template #header>
        <span>缠论分析</span>
      </template>
      <el-form :model="form" :inline="true" @submit.prevent="handleAnalyze">
        <el-form-item label="股票代码">
          <el-input v-model="form.symbol" placeholder="如：000001.SH" style="width: 200px" />
        </el-form-item>
        <el-form-item label="周期">
          <el-select v-model="form.freq" style="width: 150px">
            <el-option label="日线" value="日线" />
            <el-option label="30分钟" value="30分钟" />
            <el-option label="60分钟" value="60分钟" />
            <el-option label="周线" value="周线" />
            <el-option label="月线" value="月线" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="form.sdt"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            placeholder="选择开始时间"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="form.edt"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            placeholder="选择结束时间"
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAnalyze" :loading="store.loading">
            分析
          </el-button>
          <el-button @click="handleClear">清空</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-if="store.error" class="error-message">
      <el-alert :title="store.error" type="error" :closable="false" />
    </div>

    <div v-if="store.hasResult" class="result-container">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card>
            <template #header>
              <span>K线图</span>
            </template>
            <KlineChart
              :symbol="form.symbol"
              :freq="form.freq"
              :bis="store.bis"
              :fxs="store.fxs"
              :sdt="form.sdt"
              :edt="form.edt"
            />
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>笔列表</span>
            </template>
            <BiList :bis="store.bis" />
          </el-card>
          <el-card style="margin-top: 20px">
            <template #header>
              <span>分型列表</span>
            </template>
            <FxList :fxs="store.fxs" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElCard, ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElButton, ElDatePicker, ElAlert, ElRow, ElCol } from 'element-plus';
import { useAnalysisStore } from '../stores/analysis';
import KlineChart from '../components/KlineChart.vue';
import BiList from '../components/BiList.vue';
import FxList from '../components/FxList.vue';

const store = useAnalysisStore();

const form = ref({
  symbol: '000001.SH',
  freq: '日线',
  sdt: '2023-01-01',
  edt: '2023-12-31',
});

const handleAnalyze = async () => {
  try {
    await store.analyze(form.value.symbol, form.value.freq, form.value.sdt, form.value.edt);
  } catch (error) {
    console.error('分析失败:', error);
  }
};

const handleClear = () => {
  store.clear();
};

onMounted(() => {
  // 可以在这里设置默认值或加载历史数据
});
</script>

<style scoped>
.analysis-page {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.error-message {
  margin-bottom: 20px;
}

.result-container {
  margin-top: 20px;
}
</style>
