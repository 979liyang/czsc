<template>
  <div class="demo-sign-up">
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
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" class="w-full">注 册</el-button>
            </el-form-item>
          </el-form>
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
import { useRouter } from 'vue-router';
import type { FormInstance, FormRules } from 'element-plus';

defineOptions({ name: 'DemoSignUp' });

const router = useRouter();
const formRef = ref<FormInstance>();
const form = reactive({
  name: '',
  email: '',
  password: '',
});

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
};

function handleSubmit() {
  formRef.value?.validate((valid) => {
    if (valid) {
      console.log('Sign up:', form);
      router.push('/sign-in');
    }
  });
}
</script>

<style scoped>
.demo-sign-up {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}
.sign-up-row { width: 100%; }
.col-form { max-width: 420px; }
.form-card { padding: 0 24px 24px; }
.form-title { margin: 0 0 8px; font-size: 22px; }
.form-desc { margin: 0 0 20px; font-size: 13px; color: var(--el-text-color-secondary); }
.w-full { width: 100%; }
.text-muted { font-size: 13px; color: var(--el-text-color-secondary); }
.link { color: var(--el-color-primary); text-decoration: none; }
</style>
