<template>
  <div class="examples-page">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>策略示例</span>
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

      <div v-loading="loading" class="examples-content">
        <el-row :gutter="20">
          <el-col
            v-for="example in examples"
            :key="example.id"
            :span="8"
            style="margin-bottom: 20px"
          >
            <el-card
              class="example-card"
              shadow="hover"
              @click="handleExampleClick(example)"
            >
              <template #header>
                <div class="card-header">
                  <h3>{{ example.name }}</h3>
                  <el-tag :type="getCategoryType(example.category)" size="small">
                    {{ example.category }}
                  </el-tag>
                </div>
              </template>
              <div class="card-body">
                <p class="example-description">
                  {{ truncateDescription(example.description) }}
                </p>
                <div class="example-meta">
                  <span class="meta-item">
                    <el-icon><Location /></el-icon>
                    {{ example.market }}
                  </span>
                  <span class="meta-item">
                    <el-icon><Clock /></el-icon>
                    {{ example.freq }}
                  </span>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <el-empty v-if="!loading && examples.length === 0" description="暂无策略示例" />
      </div>
    </el-card>

    <!-- 示例详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedExample?.name"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedExample" class="example-detail">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="代码" name="code">
            <div class="code-viewer">
              <pre><code class="language-python">{{ selectedExample.code }}</code></pre>
            </div>
          </el-tab-pane>
          <el-tab-pane v-if="selectedExample.readme" label="文档" name="readme">
            <div class="readme-viewer" v-html="renderMarkdown(selectedExample.readme)"></div>
          </el-tab-pane>
        </el-tabs>
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
  ElTabs,
  ElTabPane,
  ElTag,
  ElIcon,
} from 'element-plus';
import { Location, Clock } from '@element-plus/icons-vue';
import { examplesApi, type ExampleInfo, type ExampleDetail } from '../api/examples';

const loading = ref(false);
const examples = ref<ExampleInfo[]>([]);
const categories = ref<string[]>([]);
const selectedCategory = ref<string>('');
const detailDialogVisible = ref(false);
const selectedExample = ref<ExampleDetail | null>(null);
const activeTab = ref('code');

const loadExamples = async () => {
  loading.value = true;
  try {
    const result = await examplesApi.getExamplesList(selectedCategory.value || undefined);
    examples.value = result.examples;
    if (categories.value.length === 0) {
      categories.value = result.categories;
    }
  } catch (error) {
    console.error('加载策略示例列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const loadCategories = async () => {
  try {
    const result = await examplesApi.getExamplesList();
    categories.value = result.categories;
  } catch (error) {
    console.error('加载分类列表失败:', error);
  }
};

const handleCategoryChange = () => {
  loadExamples();
};

const handleExampleClick = async (example: ExampleInfo) => {
  try {
    const detail = await examplesApi.getExampleDetail(example.id);
    selectedExample.value = detail;
    detailDialogVisible.value = true;
    activeTab.value = 'code';
  } catch (error) {
    console.error('加载策略示例详情失败:', error);
  }
};

const truncateDescription = (desc: string, maxLength: number = 100): string => {
  if (!desc) return '暂无说明';
  if (desc.length <= maxLength) return desc;
  return desc.substring(0, maxLength) + '...';
};

const getCategoryType = (category: string): string => {
  const typeMap: Record<string, string> = {
    'stock': 'success',
    'future': 'warning',
    'etf': 'info',
  };
  return typeMap[category] || '';
};

const renderMarkdown = (markdown: string): string => {
  // 简单的markdown渲染（实际项目中可以使用marked等库）
  return markdown
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\n/g, '<br>');
};

onMounted(() => {
  loadCategories();
  loadExamples();
});
</script>

<style scoped>
.examples-page {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.examples-content {
  min-height: 400px;
}

.example-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.example-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.card-body {
  margin-top: 10px;
}

.example-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 10px 0;
  min-height: 48px;
}

.example-meta {
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

.example-detail {
  padding: 10px;
}

.code-viewer {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

.code-viewer pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.readme-viewer {
  padding: 15px;
  line-height: 1.8;
}
</style>

