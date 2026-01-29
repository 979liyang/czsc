<template>
  <div class="home-page">
    <el-card>
      <template #header>
        <h2>CZSC缠论分析系统</h2>
      </template>
      <div class="welcome-content">
        <p>欢迎使用CZSC缠论分析系统！</p>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card shadow="hover" @click="$router.push('/analysis')">
              <h3>缠论分析</h3>
              <p>通过Web界面进行缠论分析，查看分型、笔、中枢</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" @click="$router.push('/signals')">
              <h3>信号函数</h3>
              <p>查看和学习所有信号函数的说明和使用方法</p>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card shadow="hover" @click="$router.push('/examples')">
              <h3>策略示例</h3>
              <p>查看和学习更多策略示例代码</p>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ElCard, ElRow, ElCol } from 'element-plus';
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<style scoped>
.home-page {
  padding: 20px;
}

.welcome-content {
  text-align: center;
}

.welcome-content h3 {
  margin-top: 0;
}

.welcome-content p {
  color: #606266;
  margin-top: 10px;
}
</style>
