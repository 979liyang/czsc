<template>
  <div class="signals-page">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>信号函数文档</span>
          <el-select
            v-model="selectedCategory"
            placeholder="选择分类"
            style="width: 200px"
            clearable
            @change="handleCategoryChange"
          >
            <el-option
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
        </div>
      </template>

      <div v-loading="loading" class="signals-content">
        <el-row :gutter="20">
          <el-col
            v-for="signal in signals"
            :key="signal.name"
            :span="8"
            style="margin-bottom: 20px"
          >
            <SignalCard :signal="signal" @click="handleSignalClick(signal)" />
          </el-col>
        </el-row>

        <el-empty v-if="!loading && signals.length === 0" description="暂无信号函数" />
      </div>
    </el-card>

    <!-- 信号详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedSignal?.name"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedSignal" class="signal-detail">
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="函数名称">
            {{ selectedSignal.name }}
          </el-descriptions-item>
          <el-descriptions-item label="完整名称">
            {{ selectedSignal.full_name }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag>{{ selectedSignal.category }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="信号数量">
            {{ selectedSignal.signals.length }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <div class="description-section">
          <h3>函数说明</h3>
          <pre class="description-text">{{ selectedSignal.description }}</pre>
        </div>

        <el-divider />

        <div class="params-section">
          <h3>参数说明</h3>
          <el-table :data="selectedSignal.params" stripe>
            <el-table-column prop="name" label="参数名" width="150" />
            <el-table-column prop="type" label="类型" width="120" />
            <el-table-column prop="description" label="说明" />
            <el-table-column prop="default" label="默认值" width="120">
              <template #default="{ row }">
                <span v-if="row.default !== null">{{ row.default }}</span>
                <el-tag v-else type="info" size="small">无</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'success'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-divider />

        <div class="signals-section">
          <h3>信号列表</h3>
          <el-tag
            v-for="sig in selectedSignal.signals"
            :key="sig"
            style="margin: 5px"
          >
            {{ sig }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  ElCard,
  ElSelect,
  ElOption,
  ElRow,
  ElCol,
  ElEmpty,
  ElDialog,
  ElDescriptions,
  ElDescriptionsItem,
  ElTag,
  ElDivider,
  ElTable,
  ElTableColumn,
} from 'element-plus';
import { docsApi, type SignalInfo } from '../api/docs';
import SignalCard from '../components/SignalCard.vue';

const loading = ref(false);
const signals = ref<SignalInfo[]>([]);
const categories = ref<string[]>([]);
const selectedCategory = ref<string>('');
const detailDialogVisible = ref(false);
const selectedSignal = ref<SignalInfo | null>(null);

const loadSignals = async () => {
  loading.value = true;
  try {
    const result = await docsApi.getSignalsList(selectedCategory.value || undefined);
    signals.value = result.signals;
    if (categories.value.length === 0) {
      categories.value = result.categories;
    }
  } catch (error) {
    console.error('加载信号函数列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const loadCategories = async () => {
  try {
    const result = await docsApi.getCategories();
    categories.value = result.categories;
  } catch (error) {
    console.error('加载分类列表失败:', error);
  }
};

const handleCategoryChange = () => {
  loadSignals();
};

const handleSignalClick = (signal: SignalInfo) => {
  selectedSignal.value = signal;
  detailDialogVisible.value = true;
};

onMounted(() => {
  loadCategories();
  loadSignals();
});
</script>

<style scoped>
.signals-page {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.signals-content {
  min-height: 400px;
}

.signal-detail {
  padding: 10px;
}

.description-section,
.params-section,
.signals-section {
  margin-bottom: 20px;
}

.description-section h3,
.params-section h3,
.signals-section h3 {
  margin-bottom: 10px;
  color: #303133;
}

.description-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}
</style>
