# CZSC 前端应用

基于Vue3 + ElementPlus + TailwindCSS的CZSC缠论分析前端界面。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **UI库**: ElementPlus
- **样式**: TailwindCSS
- **语言**: TypeScript
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **图表**: ECharts
- **构建工具**: Vite

## 项目结构

```
frontend/
├── src/
│   ├── api/                    # API调用层
│   ├── router/                 # 路由配置
│   ├── views/                  # 页面组件
│   ├── components/             # 通用组件
│   ├── stores/                 # 状态管理
│   ├── utils/                  # 工具函数
│   ├── App.vue
│   └── main.ts
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

## 安装

```bash
npm install
```

## 开发

```bash
npm run dev
```

访问 http://localhost:5173

## 构建

```bash
npm run build
```

## 代码格式化

```bash
npm run format
npm run lint
```
