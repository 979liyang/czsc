<template>
  <el-dialog
    v-model="dialogVisible"
    title="注册"
    width="420px"
    class="auth-register-dialog"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <p class="form-desc">创建新账号</p>
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
      <a href="#" class="link" @click.prevent="onSwitchLogin">登录</a>
    </p>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { useAuthStore } from '../stores/auth';
import type { FormInstance, FormRules } from 'element-plus';

defineOptions({ name: 'AuthRegisterDialog' });

const props = defineProps<{
  visible: boolean;
}>();

const emit = defineEmits<{
  close: [];
  success: [];
  'switch-to-login': [];
}>();

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

const dialogVisible = ref(props.visible);

watch(
  () => props.visible,
  (v) => {
    dialogVisible.value = v;
    if (!v) {
      errorMsg.value = '';
      form.username = '';
      form.password = '';
    }
  }
);

watch(dialogVisible, (v) => {
  if (!v) emit('close');
});

function handleClose() {
  dialogVisible.value = false;
  emit('close');
}

function onSwitchLogin() {
  handleClose();
  emit('switch-to-login');
}

async function handleSubmit() {
  errorMsg.value = '';
  const valid = await formRef.value?.validate().catch(() => false);
  if (!valid) return;
  loading.value = true;
  try {
    await authStore.register(form.username, form.password);
    dialogVisible.value = false;
    emit('success');
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } };
    errorMsg.value = err?.response?.data?.detail ?? '注册失败';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.form-desc {
  margin: 0 0 16px;
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
