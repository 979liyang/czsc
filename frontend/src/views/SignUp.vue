<template>
  <div class="sign-up-page">
    <el-row type="flex" justify="center" align="middle" class="sign-up-row">
      <el-col :xs="24" :md="12" :lg="10" class="col-form">
        <el-card shadow="hover" class="form-card">
          <template #header>
            <h2 class="form-title">注册</h2>
            <p class="form-desc">创建新账号</p>
          </template>
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            @submit.prevent="handleSubmit"
          >
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="至少 6 位"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" native-type="submit" class="w-full">
                注 册
              </el-button>
            </el-form-item>
          </el-form>
          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
          <p class="text-muted">
            已有账号？
            <router-link to="/sign-in" class="link">登录</router-link>
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import type { FormInstance, FormRules } from 'element-plus';

defineOptions({ name: 'SignUp' });

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const formRef = ref<FormInstance>();
const loading = ref(false);
const errorMsg = ref('');

const form = reactive({ username: '', password: '' });

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
};

function getRedirect(): string {
  const r = route.query.redirect as string;
  return r && r.startsWith('/') ? r : '/sign-in';
}

async function handleSubmit() {
  errorMsg.value = '';
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  try {
    await authStore.register(form.username, form.password);
    router.replace(getRedirect());
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } };
    errorMsg.value = err?.response?.data?.detail ?? '注册失败';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.sign-up-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}
.sign-up-row {
  width: 100%;
}
.col-form {
  max-width: 420px;
}
.form-card {
  padding: 0 24px 24px;
}
.form-title {
  margin: 0 0 8px;
  font-size: 22px;
}
.form-desc {
  margin: 0 0 20px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.w-full {
  width: 100%;
}
.error-msg {
  color: var(--el-color-danger);
  font-size: 12px;
  margin: 8px 0;
}
.text-muted {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.link {
  color: var(--el-color-primary);
  text-decoration: none;
}
</style>
