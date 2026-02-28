<template>
  <div class="demo-profile">
    <el-card shadow="hover" class="profile-header mb-24">
      <el-row align="middle" :gutter="24">
        <el-col :span="24" :md="12" class="flex align-center">
          <el-avatar :size="74" shape="square" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
          <div class="avatar-info ml-16">
            <h4 class="m-0">示例用户</h4>
            <p class="text-secondary m-0">角色 / 部门</p>
          </div>
        </el-col>
        <el-col :span="24" :md="12" class="flex align-center justify-end">
          <el-radio-group v-model="profileTab" size="small">
            <el-radio-button value="overview">概览</el-radio-button>
            <el-radio-button value="teams">团队</el-radio-button>
            <el-radio-button value="projects">项目</el-radio-button>
          </el-radio-group>
        </el-col>
      </el-row>
    </el-card>
    <el-row :gutter="24">
      <el-col :xs="24" :md="8" class="mb-24">
        <el-card shadow="hover" header="平台设置">
          <el-form label-position="top">
            <el-form-item label="邮件通知">
              <el-switch v-model="settings.email" />
            </el-form-item>
            <el-form-item label="短信通知">
              <el-switch v-model="settings.sms" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8" class="mb-24">
        <el-card shadow="hover" header="个人信息">
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="姓名">示例用户</el-descriptions-item>
            <el-descriptions-item label="邮箱">user@example.com</el-descriptions-item>
            <el-descriptions-item label="手机">138****0000</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8" class="mb-24">
        <el-card shadow="hover" header="最近会话">
          <div class="conversation-placeholder">暂无会话</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

defineOptions({ name: 'DemoProfile' });

const profileTab = ref('overview');
const settings = ref({ email: true, sms: false });
</script>

<style scoped>
.demo-profile .mb-24 { margin-bottom: 24px; }
.demo-profile .ml-16 { margin-left: 16px; }
.demo-profile .flex { display: flex; }
.demo-profile .align-center { align-items: center; }
.demo-profile .justify-end { justify-content: flex-end; }
.demo-profile .text-secondary { color: var(--el-text-color-secondary); font-size: 13px; }
.demo-profile .m-0 { margin: 0; }
.avatar-info h4 { font-size: 16px; }
.conversation-placeholder {
  padding: 24px;
  text-align: center;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border-radius: 4px;
}
</style>
