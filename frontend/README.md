# CZSC 前端应用

基于Vue3 + ElementPlus + TailwindCSS的Kylin Trading Pro分析前端界面。

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

## 麒麟图表分析 Demo（与参考 HTML 完全一致，数据同源）

页面 `/demo-czsc-analyze` 与 `.results/czsc_chart_analyze_01_000001.SH_20260209_104835.html`（000001.SH 上证指数）**完全一致**：内容、技术栈、样式及**图表数据**均与该参考 HTML 一致。

- **技术栈**: ECharts 5（与 pyecharts 使用的 echarts.min.js v5 一致）、Vue 3、TypeScript；初始化方式与参考一致（canvas、locale ZH）
- **图表**: K 线、MA5/MA13/MA21、分型(FX)、笔(BI)、成交量、MACD/DIFF/DEA；容器 1400×580，背景 #1f212d
- **数据来源**: 从该参考 HTML 内嵌的 ECharts option 解析并导出为 `frontend/public/czsc_chart_000001_SH_option.json`，本页加载该 JSON 后直接 `setOption(option)`，实现数据与参考页同源。若未导出 JSON，页面会提示执行：`python scripts/extract_echarts_option_from_html.py`（详见仓库根目录 `scripts/README.md`）

访问：`http://localhost:5173/demo-czsc-analyze`

## 股票详情页（本地 .stock_data 数据）

后端启动后，你可以直接打开股票详情页查看本地数据的 30/60/日线 CZSC 分析结果（TradingVue.js 展示）：

- Demo（600078）：
  - `http://localhost:5173/stock/600078.SH`

页面默认起始日期为 **2018-01-01**，结束日期为今天，可在页面内调整时间范围。

## 构建

```bash
npm run build
```

## 代码格式化

```bash
npm run format
npm run lint
```
