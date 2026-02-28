/**
 * 应用入口
 */
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
import router from './router';
import App from './App.vue';
import './style.css';
import DefaultLayout from './layouts/Default.vue';
import DashboardLayout from './layouts/Dashboard.vue';
import EmptyLayout from './layouts/Empty.vue';

const app = createApp(App);
const pinia = createPinia();

// 注册ElementPlus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// 注册布局组件
app.component('layout-default', DefaultLayout);
app.component('layout-dashboard', DashboardLayout);
app.component('layout-empty', EmptyLayout);

app.use(pinia);
app.use(router);
app.use(ElementPlus);

app.mount('#app');
