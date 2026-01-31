# Tasks: 股票详情页 - TradingVue.js K线图表

**Feature**: 股票详情页K线图表展示  
**Created**: 2025-01-31  
**Status**: Draft  
**Input**: 前端使用 npm i trading-vue-js 去绘制K线，生成一个/stock/SH600519，会请求获取当前股票的分析数据详情如 python demo/analyze.py 的报告

## Summary

实现股票详情页功能，使用 TradingVue.js 绘制K线图表，展示类似 `demo/analyze.py` 的完整分析报告。包括：
- 动态路由 `/stock/:symbol` 支持不同股票代码
- TradingVue.js K线图表集成
- 完整的CZSC分析数据展示（K线、分型、笔、统计信息）
- 响应式布局设计

## Dependencies

- 后端API已实现：`/api/v1/analysis/czsc` 接口
- 前端基础架构已就绪：Vue 3 + Vue Router + ElementPlus

## Phase 1: 前端依赖安装和基础配置

### Story Goal
安装 TradingVue.js 依赖，配置基础环境

### Independent Test Criteria
- TradingVue.js 已安装到 node_modules
- 可以在 Vue 组件中导入 TradingVue
- 基础配置完成，无编译错误

### Implementation Tasks

- [x] T001 安装 trading-vue-js 依赖到 frontend/package.json
- [x] T002 更新 frontend/package.json 的 dependencies，添加 trading-vue-js
- [x] T003 运行 npm install 安装依赖
- [x] T004 在 frontend/src/types/index.ts 中添加 TradingVue 相关类型定义

---

## Phase 2: 后端API增强 - 完整分析数据

### Story Goal
扩展后端API，返回类似 `demo/analyze.py` 的完整分析数据

### Independent Test Criteria
- API返回包含所有 `demo/analyze.py` 展示的数据字段
- 响应时间 < 3秒
- 数据格式符合前端需求

### Implementation Tasks

- [x] T005 [US1] 扩展 backend/src/models/schemas.py 中的 AnalysisResponse，添加统计字段（bars_raw_count, bars_ubi_count, fx_count, finished_bi_count, bi_count, ubi_count, last_bi_extend, last_bi_direction, last_bi_power）
- [x] T006 [US1] 扩展 backend/src/services/analysis_service.py 的 analyze 方法，计算并返回统计信息
- [x] T007 [US1] 在 backend/src/services/analysis_service.py 中添加 last_bi 信息提取逻辑
- [x] T008 [US1] 更新 backend/src/api/v1/analysis.py，确保返回完整数据
- [x] T009 [US1] 在 backend/src/models/serializers.py 中添加原始K线数据的序列化方法（如果需要）

---

## Phase 3: 前端路由和页面结构

### Story Goal
创建股票详情页路由和基础页面结构

### Independent Test Criteria
- 访问 `/stock/SH600519` 可以正常显示页面
- 路由参数正确解析
- 页面基础布局正常

### Implementation Tasks

- [x] T010 [US1] 在 frontend/src/router/routes.ts 中添加动态路由 `/stock/:symbol`
- [x] T011 [US1] 创建 frontend/src/views/StockDetail.vue 组件
- [x] T012 [US1] 在 StockDetail.vue 中实现路由参数解析（symbol）
- [x] T013 [US1] 在 StockDetail.vue 中实现基础布局（头部、图表区域、统计信息区域）
- [x] T014 [US1] 在 StockDetail.vue 中添加加载状态和错误处理

---

## Phase 4: API客户端和状态管理

### Story Goal
实现API调用和状态管理

### Independent Test Criteria
- 可以成功调用后端API获取分析数据
- 数据正确存储到 Pinia store
- 错误处理正常

### Implementation Tasks

- [x] T015 [US1] 在 frontend/src/api/analysis.ts 中添加 getStockAnalysis 方法，调用 `/api/v1/analysis/czsc`
- [x] T016 [US1] 创建 frontend/src/stores/stockDetail.ts Pinia store
- [x] T017 [US1] 在 stockDetail store 中定义 state（symbol, analysisData, loading, error）
- [x] T018 [US1] 在 stockDetail store 中实现 fetchAnalysis action
- [x] T019 [US1] 在 StockDetail.vue 中集成 store，调用 fetchAnalysis

---

## Phase 5: TradingVue.js K线图表集成

### Story Goal
集成 TradingVue.js 绘制K线图表

### Independent Test Criteria
- K线图表正常显示
- 数据格式正确转换
- 图表响应式布局正常

### Implementation Tasks

- [x] T020 [US1] 在 frontend/src/components/KlineChartTradingVue.vue 中创建 TradingVue 组件
- [x] T021 [US1] 在 KlineChartTradingVue.vue 中实现数据格式转换（RawBar → TradingVue 格式）
- [x] T022 [US1] 在 KlineChartTradingVue.vue 中配置 TradingVue 基础选项（主题、工具栏等）
- [x] T023 [US1] 在 StockDetail.vue 中集成 KlineChartTradingVue 组件
- [x] T024 [US1] 在 KlineChartTradingVue.vue 中实现分型（FX）标记显示
- [x] T025 [US1] 在 KlineChartTradingVue.vue 中实现笔（BI）标记显示

---

## Phase 6: 分析数据展示

### Story Goal
展示完整的分析统计信息

### Independent Test Criteria
- 所有统计信息正确显示
- 数据格式化正确（数字、日期等）
- 布局美观易读

### Implementation Tasks

- [x] T026 [US1] 在 StockDetail.vue 中创建统计信息展示区域
- [x] T027 [US1] 在 StockDetail.vue 中显示原始K线数量（bars_raw_count）
- [x] T028 [US1] 在 StockDetail.vue 中显示未完成笔的K线数量（bars_ubi_count）
- [x] T029 [US1] 在 StockDetail.vue 中显示分型数量（fx_count）
- [x] T030 [US1] 在 StockDetail.vue 中显示已完成笔数量（finished_bi_count）
- [x] T031 [US1] 在 StockDetail.vue 中显示所有笔数量（bi_count）
- [x] T032 [US1] 在 StockDetail.vue 中显示未完成笔数量（ubi_count）
- [x] T033 [US1] 在 StockDetail.vue 中显示最后一笔是否延伸（last_bi_extend）
- [x] T034 [US1] 在 StockDetail.vue 中显示最后一笔方向（last_bi_direction）
- [x] T035 [US1] 在 StockDetail.vue 中显示最后一笔幅度（last_bi_power）

---

## Phase 7: 分型和笔列表展示

### Story Goal
展示分型和笔的详细列表

### Independent Test Criteria
- 分型列表正确显示
- 笔列表正确显示
- 支持排序和筛选

### Implementation Tasks

- [x] T036 [US1] 在 StockDetail.vue 中创建分型列表展示区域
- [x] T037 [US1] 在 StockDetail.vue 中使用 ElementPlus Table 组件展示分型列表
- [x] T038 [US1] 在 StockDetail.vue 中创建笔列表展示区域
- [x] T039 [US1] 在 StockDetail.vue 中使用 ElementPlus Table 组件展示笔列表
- [x] T040 [US1] 在分型列表中实现时间排序功能
- [x] T041 [US1] 在笔列表中实现时间排序功能

---

## Phase 8: 交互功能增强

### Story Goal
添加用户交互功能（时间范围选择、周期切换等）

### Independent Test Criteria
- 可以切换时间范围
- 可以切换K线周期
- 交互响应流畅

### Implementation Tasks

- [x] T042 [US1] 在 StockDetail.vue 中添加时间范围选择器（DatePicker）
- [x] T043 [US1] 在 StockDetail.vue 中实现时间范围变更时重新获取数据
- [x] T044 [US1] 在 StockDetail.vue 中添加K线周期选择器（Select）
- [x] T045 [US1] 在 StockDetail.vue 中实现周期变更时重新获取数据
- [x] T046 [US1] 在 StockDetail.vue 中添加刷新按钮

---

## Phase 9: 样式优化和响应式设计

### Story Goal
优化页面样式，实现响应式布局

### Independent Test Criteria
- 页面在不同屏幕尺寸下正常显示
- 样式美观统一
- 移动端体验良好

### Implementation Tasks

- [x] T047 [US1] 在 StockDetail.vue 中使用 TailwindCSS 优化布局样式
- [x] T048 [US1] 在 StockDetail.vue 中实现响应式布局（桌面端和移动端）
- [x] T049 [US1] 在 KlineChartTradingVue.vue 中优化图表样式
- [x] T050 [US1] 在 StockDetail.vue 中添加加载动画
- [x] T051 [US1] 在 StockDetail.vue 中优化错误提示样式

---

## Phase 10: 测试和优化

### Story Goal
测试功能完整性，优化性能

### Independent Test Criteria
- 所有功能正常工作
- 性能满足要求（加载时间 < 3秒）
- 无明显的bug

### Implementation Tasks

- [ ] T052 测试不同股票代码的路由访问（如 SH600519, SZ000001）
- [ ] T053 测试时间范围选择功能
- [ ] T054 测试周期切换功能
- [ ] T055 测试数据加载错误处理
- [ ] T056 优化API请求性能（添加缓存、防抖等）
- [ ] T057 优化图表渲染性能
- [ ] T058 添加单元测试（可选）

---

## Dependencies

### Story Completion Order

1. **Phase 1** (Setup) → 必须最先完成
2. **Phase 2** (Backend API) → 必须在 Phase 3 之前完成
3. **Phase 3** (Frontend Route) → 可以并行 Phase 4
4. **Phase 4** (API Client) → 必须在 Phase 5 之前完成
5. **Phase 5** (TradingVue Chart) → 必须在 Phase 6 之前完成
6. **Phase 6** (Statistics Display) → 可以并行 Phase 7
7. **Phase 7** (Lists Display) → 可以并行 Phase 8
8. **Phase 8** (Interactions) → 可以并行 Phase 9
9. **Phase 9** (Styling) → 可以并行 Phase 10
10. **Phase 10** (Testing) → 最后完成

### Parallel Execution Examples

**Phase 3-4 可以并行**：
- T010-T014 (路由和页面结构) 可以与 T015-T019 (API客户端) 并行开发

**Phase 6-7 可以并行**：
- T026-T035 (统计信息展示) 可以与 T036-T041 (列表展示) 并行开发

**Phase 8-9 可以并行**：
- T042-T046 (交互功能) 可以与 T047-T051 (样式优化) 并行开发

## Implementation Strategy

### MVP Scope
最小可用版本包括：
- Phase 1: 依赖安装
- Phase 2: 后端API增强（返回完整数据）
- Phase 3: 基础路由和页面
- Phase 4: API调用
- Phase 5: TradingVue.js 基础K线图表
- Phase 6: 基础统计信息展示

### Incremental Delivery
1. **Week 1**: Phase 1-5（基础功能）
2. **Week 2**: Phase 6-7（数据展示）
3. **Week 3**: Phase 8-9（交互和样式）
4. **Week 4**: Phase 10（测试和优化）

## Notes

- TradingVue.js 需要特定的数据格式，需要实现数据转换函数
- 分型和笔的标记需要自定义 TradingVue 的 overlay 功能
- 响应式设计需要考虑移动端的图表显示
- API响应时间可能需要优化，考虑添加缓存机制
