<template>
  <div class="profile-page">
    <el-card shadow="hover" class="profile-header mb-24">
      <el-row align="middle" :gutter="24">
        <el-col :span="24" :md="12" class="flex align-center">
          <el-avatar :size="74" shape="square">
            {{ displayName.charAt(0) }}
          </el-avatar>
          <div class="avatar-info ml-16">
            <h4 class="m-0">{{ displayName }}</h4>
            <p class="text-secondary m-0">{{ roleLabel }}{{ tierLabel }}</p>
          </div>
        </el-col>
      </el-row>
    </el-card>
    <el-row :gutter="24">
      <el-col :xs="24" :md="12" class="mb-24">
        <el-card shadow="hover" header="个人信息">
          <el-descriptions v-if="user" :column="1" border size="small">
            <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
            <el-descriptions-item label="昵称">{{ user.nickname || '—' }}</el-descriptions-item>
            <el-descriptions-item label="签名">{{ user.signature || '—' }}</el-descriptions-item>
            <el-descriptions-item label="手机">{{ user.phone || '—' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ user.email || '—' }}</el-descriptions-item>
            <el-descriptions-item label="积分">{{ user.points ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ user.role || 'user' }}</el-descriptions-item>
            <el-descriptions-item label="档位">{{ user.tier_name || '—' }}</el-descriptions-item>
            <el-descriptions-item v-if="featureFlags.length" label="功能">
              {{ featureFlags.join('、') }}
            </el-descriptions-item>
          </el-descriptions>
          <p v-else class="text-muted">加载中…</p>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12" class="mb-24">
        <el-card shadow="hover" header="编辑资料">
          <el-form
            ref="formRef"
            :model="editForm"
            label-position="top"
            @submit.prevent="handleSave"
          >
            <el-form-item label="昵称">
              <el-input v-model="editForm.nickname" placeholder="昵称" maxlength="64" show-word-limit />
            </el-form-item>
            <el-form-item label="签名">
              <el-input
                v-model="editForm.signature"
                type="textarea"
                placeholder="个人签名"
                :rows="2"
                maxlength="255"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="手机">
              <el-input v-model="editForm.phone" placeholder="手机号" maxlength="32" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="editForm.email" placeholder="邮箱" maxlength="128" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
              <el-button class="ml-8" @click="handleLogout">退出登录</el-button>
            </el-form-item>
          </el-form>
          <p v-if="saveError" class="error-msg">{{ saveError }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import * as authApi from '../api/auth';

defineOptions({ name: 'Profile' });

const authStore = useAuthStore();
const router = useRouter();
const formRef = ref();
const saving = ref(false);
const saveError = ref('');

const user = computed(() => authStore.user);

const displayName = computed(() => {
  const u = user.value;
  return u?.nickname?.trim() || u?.username || '用户';
});

const roleLabel = computed(() => {
  const r = user.value?.role;
  return r === 'admin' ? '管理员' : '普通用户';
});

const tierLabel = computed(() => {
  const t = user.value?.tier_name;
  return t ? ` / ${t}` : '';
});

const featureFlags = computed(() => user.value?.feature_flags ?? []);

const editForm = reactive({
  nickname: '',
  signature: '',
  phone: '',
  email: '',
});

function syncEditForm() {
  const u = user.value;
  if (u) {
    editForm.nickname = u.nickname ?? '';
    editForm.signature = u.signature ?? '';
    editForm.phone = u.phone ?? '';
    editForm.email = u.email ?? '';
  }
}

watch(user, syncEditForm, { immediate: true });

onMounted(() => {
  if (authStore.isLoggedIn && !authStore.user) {
    authStore.fetchUser();
  } else {
    syncEditForm();
  }
});

async function handleSave() {
  saveError.value = '';
  saving.value = true;
  try {
    const res = await authApi.updateProfile({
      nickname: editForm.nickname || null,
      signature: editForm.signature || null,
      phone: editForm.phone || null,
      email: editForm.email || null,
    });
    authStore.setUser(res);
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string } } };
    saveError.value = err?.response?.data?.detail ?? '保存失败';
  } finally {
    saving.value = false;
  }
}

function handleLogout() {
  authStore.logout();
  router.push('/sign-in');
}
</script>

<style scoped>
.profile-page .mb-24 {
  margin-bottom: 24px;
}
.profile-page .ml-16 {
  margin-left: 16px;
}
.profile-page .flex {
  display: flex;
}
.profile-page .align-center {
  align-items: center;
}
.profile-page .text-secondary {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.profile-page .m-0 {
  margin: 0;
}
.avatar-info h4 {
  font-size: 16px;
}
.text-muted {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
.error-msg {
  color: var(--el-color-danger);
  font-size: 12px;
  margin-top: 8px;
}
.profile-page .ml-8 {
  margin-left: 8px;
}
</style>
