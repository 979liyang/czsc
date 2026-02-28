# CZSC 图表分析 Demo 技术文档

## 1. 概述

本项目提供与 **czsc_chart_analyze_01_000001.SZ_20260207_170420.html** 页面一致的前端 Demo，用于在 Vue 3 应用中复现 CZSC 缠论分析单图效果。K 线图使用与参考 HTML 相同的图表库 **ECharts**（参考页由 pyecharts 生成，底层同样使用 ECharts）。

## 2. 参考页面说明

- **参考文件**：`.results/czsc_chart_analyze_01_000001.SZ_20260207_170420.html`
- **来源**：由 CZSC 分析脚本（如 `czsc.utils.echarts_plot` / pyecharts）导出的单图 HTML。
- **图表库**：页面通过 `<script src="https://assets.pyecharts.org/assets/v5/echarts.min.js"></script>` 引入 ECharts 5。
- **容器尺寸**：`width: 1400px; height: 580px`。

## 3. 前端 Demo 与路由

| 说明       | 路径                  | 组件                     |
|------------|-----------------------|--------------------------|
| 与 HTML 一致 | `/demo-czsc-analyze`   | `CzscChartAnalyzeDemo.vue` |
| 原功能 Demo | `/demo-czsc-chart`     | `CzscChartDemo.vue`        |

**与参考 HTML 严格对齐的页面**：`/demo-czsc-analyze`，对应组件 `frontend/src/views/CzscChartAnalyzeDemo.vue`。

## 4. 使用的图表库

- **库名**：Apache ECharts 5
- **引入方式**：项目依赖 `echarts`（`package.json`），在组件中 `import * as echarts from 'echarts'`。
- **与参考 HTML 的关系**：参考页使用 pyecharts 导出的 ECharts 配置；本 Demo 使用同一套 ECharts API，配置（grid、series、dataZoom、axisPointer 等）按参考 HTML 的 option 对齐，保证布局与交互一致。

## 5. 页面布局与配置对齐

Demo 与参考 HTML 在以下方面保持一致：

| 配置项       | 参考 HTML 取值           | Demo 实现说明 |
|--------------|---------------------------|----------------|
| 背景色       | `#1f212d`                 | `backgroundColor: '#1f212d'` |
| 主图区域     | 上 12%，高 58%，左 0%，右 1% | `grid[0]: top 12%, height 58%, left 0%, right 1%` |
| 成交量区域   | 上 74%，高 8%             | `grid[1]: top 74%, height 8%` |
| MACD 区域    | 上 86%，高 10%            | `grid[2]: top 86%, height 10%` |
| 图例         | 顶部居中                  | `legend: top 1%, left center` |
| 缩略轴       | 底部，start 80, end 100   | `dataZoom slider: top 96%, bottom 0%, start 80, end 100` |
| 坐标轴联动   | 三块区域 x 轴联动         | `axisPointer.link: xAxisIndex all`、`dataZoom.xAxisIndex: [0,1,2]` |
| 容器尺寸     | 1400×580                  | 容器 `max-width: 1400px; height: 580px`（宽度可响应） |

## 6. 图表内容与数据

- **K 线**：candlestick，数据格式与参考一致（按类目轴索引的 [open, close, low, high]）。
- **均线**：MA5 / MA13 / MA21，line 系列，与 K 线共用类目轴，`connectNulls: true`。
- **分型**：顶/底分型为 scatter（三角），并有一条按时间顺序连接分型点的折线。
- **笔**：由 bis 数据画线段，连接分型端点。
- **成交量**：bar，第二块 grid，红绿与 K 线一致。
- **MACD**：DIF、DEA 线 + MACD 柱，第三块 grid。

数据来源：`frontend/src/views/mock.ts` 的日线 mock（bars、fxs、bis、indicators.sma、indicators.macd）。类目轴按 bars 顺序生成，保证**数据连续、无缺口**。

## 7. 如何运行与访问

```bash
# 安装依赖（若未安装）
cd frontend && npm install

# 启动开发服务
npm run dev
```

浏览器访问：**http://localhost:5173/demo-czsc-analyze** 即可看到与参考 HTML 一致的 K 线分析图。

## 8. 文件与依赖清单

- **页面**：`frontend/src/views/CzscChartAnalyzeDemo.vue`
- **路由**：`frontend/src/router/routes.ts` 中 path `'/demo-czsc-analyze'`
- **数据**：`frontend/src/views/mock.ts`（mockData）
- **依赖**：`echarts`（见 `frontend/package.json`）

## 9. 与参考 HTML 的差异说明

- **数据**：参考 HTML 为静态导出的单次分析结果；Demo 使用前端 mock，后续可替换为接口返回的同一结构数据。
- **brush**：参考中可选 brush 组件未在 Demo 中实现，不影响主图、成交量、MACD 及联动效果。
- **容器宽度**：Demo 使用 `max-width: 1400px`、`width: 100%`，小屏下会等比缩放，参考为固定 1400px。

以上为 CZSC 图表分析 Demo 的完整技术说明，便于与 `czsc_chart_analyze_01_*.html` 对照与二次开发。
