# Tasks: 分页按需加载优化

**Input**: 用户需求：为了保证前端和后端性能，改成按需加载，分页获取。

**Prerequisites**: 
- 现有实现：`backend/src/api/v1/analysis.py` 的 `/stock/{symbol}/local_czsc` 一次性返回所有数据（bars、fxs、bis）
- 前端组件：`frontend/src/components/KlineChartTradingVue.vue`、`BiList.vue`、`FxList.vue` 一次性渲染所有数据
- Store：`frontend/src/stores/stockDetail.ts` 管理状态

**Tests**: 本次优化不包含测试任务（用户未要求）

**Organization**: 任务按功能模块组织，支持独立实现和测试

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以并行执行（不同文件，无依赖关系）
- **[Story]**: 所属用户故事（US1 = 分页按需加载优化）
- 所有任务都包含明确的文件路径

## Path Conventions

- **前端**: `frontend/src/`
- **后端**: `backend/src/`
- **API**: `backend/src/api/v1/`

---

## Phase 1: 后端接口优化 - 支持分页参数

**Purpose**: 修改后端接口，支持分页参数，只返回请求页的数据

**Goal**: 后端接口支持 `offset`、`limit` 参数，对 bars、fxs、bis 进行分页返回

**Independent Test**: 调用 `/stock/600078.SH/local_czsc?freqs=30&sdt=20180101&bars_offset=0&bars_limit=100` 应该只返回前100条K线数据

### Implementation for Backend

- [x] T001 [P] [US1] 修改后端接口参数，添加分页参数支持在 `backend/src/api/v1/analysis.py` 的 `get_local_czsc` 函数中，添加 `bars_offset`、`bars_limit`、`fxs_offset`、`fxs_limit`、`bis_offset`、`bis_limit` 参数

- [x] T002 [US1] 修改 `LocalCzscService.analyze_multi` 方法，支持分页参数在 `backend/src/services/local_czsc_service.py` 中，修改 `analyze_multi` 方法签名，添加分页参数

- [x] T003 [US1] 修改 `_analyze_one` 函数，支持分页返回 bars、fxs、bis在 `backend/src/services/local_czsc_service.py` 中，修改 `_analyze_one` 函数，根据分页参数只返回请求范围的数据

- [x] T004 [US1] 添加分页元数据，返回总数和分页信息在 `backend/src/services/local_czsc_service.py` 中，在返回结果中添加 `pagination` 字段，包含总数、当前页、每页数量等信息

- [x] T005 [US1] 添加日志记录，记录分页请求信息在 `backend/src/services/local_czsc_service.py` 中添加日志，记录分页参数和返回的数据量

**Checkpoint**: 后端接口支持分页参数，可以通过 API 测试工具验证分页功能

---

## Phase 2: 前端 API 层优化 - 支持分页请求

**Purpose**: 修改前端 API 调用层，支持分页参数

**Goal**: API 层提供分页请求方法，与后端接口配合实现分页加载

**Independent Test**: 调用 `analysisApi.getLocalCzscSingleFreq` 时传入分页参数，应该只请求对应页的数据

### Implementation for Frontend API

- [x] T006 [P] [US1] 修改 `getLocalCzscSingleFreq` 方法，添加分页参数在 `frontend/src/api/analysis.ts` 中，为 `getLocalCzscSingleFreq` 方法添加分页参数（bars_offset, bars_limit, fxs_offset, fxs_limit, bis_offset, bis_limit）

- [x] T007 [US1] 更新类型定义，支持分页参数和分页响应在 `frontend/src/api/analysis.ts` 中，更新 `LocalCzscResponseData` 接口，添加 `pagination` 字段

**Checkpoint**: API 层支持分页请求，可以通过浏览器 Network 面板验证分页参数

---

## Phase 3: 前端 Store 优化 - 支持分页数据管理

**Purpose**: 修改前端状态管理，支持分页数据的缓存和管理

**Goal**: Store 中支持分页数据的加载、缓存和追加

**Independent Test**: 调用 `store.fetchSingleFreq` 时传入分页参数，应该只加载对应页的数据并追加到缓存

### Implementation for Frontend Store

- [x] T008 [P] [US1] 修改 `fetchSingleFreq` 方法，支持分页参数在 `frontend/src/stores/stockDetail.ts` 中，为 `fetchSingleFreq` 方法添加分页参数

- [x] T009 [US1] 修改缓存结构，支持分页数据的追加和合并在 `frontend/src/stores/stockDetail.ts` 中，修改 `localCzscCache` 的存储逻辑，支持分页数据的追加（而不是替换）

- [x] T010 [US1] 添加分页状态管理，记录已加载的页数和总数在 `frontend/src/stores/stockDetail.ts` 中，添加 `pagination` 状态，记录每个周期的分页信息（已加载的 bars/fxs/bis 数量、总数等）

- [x] T011 [US1] 添加 `loadMore` 方法，支持加载更多数据在 `frontend/src/stores/stockDetail.ts` 中，添加 `loadMoreBars`、`loadMoreFxs`、`loadMoreBis` 方法，支持加载下一页数据

**Checkpoint**: Store 支持分页数据管理，可以通过 Vue DevTools 验证分页状态

---

## Phase 4: 前端图表组件优化 - 支持分页显示

**Purpose**: 修改图表组件，支持分页显示K线数据

**Goal**: 图表组件初始只显示部分数据，支持滚动加载更多

**Independent Test**: 打开股票详情页，图表初始只显示最近的100条K线，滚动到底部时自动加载更多

### Implementation for Frontend Chart Component

- [ ] T012 [P] [US1] 修改 `KlineChartTradingVue.vue`，支持分页显示K线在 `frontend/src/components/KlineChartTradingVue.vue` 中，修改 `buildOhlcv` 函数，只使用当前页的 bars 数据

- [ ] T013 [US1] 添加滚动监听，实现滚动加载更多在 `frontend/src/components/KlineChartTradingVue.vue` 中，添加滚动监听器，当滚动到底部时调用 Store 的 `loadMoreBars` 方法

- [ ] T014 [US1] 添加加载状态提示，显示正在加载更多数据在 `frontend/src/components/KlineChartTradingVue.vue` 中，添加加载状态提示，显示 "正在加载更多K线数据..."

- [ ] T015 [US1] 优化图表性能，使用虚拟滚动或数据切片在 `frontend/src/components/KlineChartTradingVue.vue` 中，优化大量数据的渲染性能，考虑使用虚拟滚动或只渲染可见区域的数据

**Checkpoint**: 图表组件支持分页显示，可以通过浏览器验证滚动加载功能

---

## Phase 5: 前端列表组件优化 - 支持分页显示

**Purpose**: 修改列表组件，支持分页显示分型和笔数据

**Goal**: 列表组件初始只显示部分数据，支持分页或滚动加载更多

**Independent Test**: 打开股票详情页，分型列表和笔列表初始只显示最近的50条，点击"加载更多"或滚动到底部时加载更多

### Implementation for Frontend List Components

- [ ] T016 [P] [US1] 修改 `FxList.vue`，支持分页显示分型数据在 `frontend/src/components/FxList.vue` 中，添加分页逻辑，初始只显示部分数据

- [ ] T017 [US1] 修改 `BiList.vue`，支持分页显示笔数据在 `frontend/src/components/BiList.vue` 中，添加分页逻辑，初始只显示部分数据

- [ ] T018 [US1] 添加"加载更多"按钮，支持手动加载更多数据在 `frontend/src/components/FxList.vue` 和 `BiList.vue` 中，添加"加载更多"按钮，点击时调用 Store 的 `loadMoreFxs` 或 `loadMoreBis` 方法

- [ ] T019 [US1] 添加分页信息显示，显示当前页数和总数在 `frontend/src/components/FxList.vue` 和 `BiList.vue` 中，添加分页信息显示，如 "显示 1-50 / 共 200 条"

- [ ] T020 [US1] 添加滚动加载，支持滚动到底部自动加载在 `frontend/src/components/FxList.vue` 和 `BiList.vue` 中，添加滚动监听器，滚动到底部时自动加载更多

**Checkpoint**: 列表组件支持分页显示，可以通过浏览器验证分页和加载更多功能

---

## Phase 6: 前端视图优化 - 集成分页功能

**Purpose**: 修改股票详情页，集成分页功能

**Goal**: 页面初始只加载部分数据，支持按需加载更多

**Independent Test**: 打开股票详情页，初始只加载最近的100条K线、50条分型、50条笔，用户可以通过滚动或点击按钮加载更多

### Implementation for Frontend View

- [ ] T021 [P] [US1] 修改 `StockDetail.vue`，初始请求时使用分页参数在 `frontend/src/views/StockDetail.vue` 中，修改 `handleRefresh` 和初始化逻辑，初始请求时传入分页参数（如 bars_limit=100, fxs_limit=50, bis_limit=50）

- [ ] T022 [US1] 添加分页信息显示，显示数据加载状态在 `frontend/src/views/StockDetail.vue` 中，添加分页信息显示，如 "K线：已加载 100 / 共 500 条"

- [ ] T023 [US1] 优化加载策略，初始只加载必要的数据在 `frontend/src/views/StockDetail.vue` 中，优化初始加载策略，只加载图表显示所需的数据，列表数据可以延迟加载

- [ ] T024 [US1] 添加错误处理，处理分页加载失败的情况在 `frontend/src/views/StockDetail.vue` 中，添加分页加载失败的错误处理和提示

**Checkpoint**: 前端视图支持分页功能，可以通过浏览器验证完整的分页流程

---

## Phase 7: 性能优化和缓存策略

**Purpose**: 优化分页加载的性能和缓存策略

**Goal**: 确保分页加载的性能最优，避免重复请求

**Independent Test**: 切换周期后再切换回来，应该使用缓存数据，不重复请求

### Performance Optimization

- [ ] T025 [P] [US1] 优化后端分页查询性能，使用索引和缓存在 `backend/src/services/local_czsc_service.py` 中，优化分页查询的性能，考虑使用缓存避免重复计算

- [ ] T026 [US1] 优化前端缓存策略，支持分页数据的增量更新在 `frontend/src/stores/stockDetail.ts` 中，优化缓存策略，支持分页数据的增量更新和合并

- [ ] T027 [US1] 添加防抖和节流，避免频繁请求在 `frontend/src/views/StockDetail.vue` 和组件中，添加防抖和节流逻辑，避免滚动时频繁触发加载请求

- [ ] T028 [US1] 优化大数据渲染性能，使用虚拟列表在 `frontend/src/components/FxList.vue` 和 `BiList.vue` 中，考虑使用虚拟列表（如 `vue-virtual-scroller`）优化大量数据的渲染性能

**Checkpoint**: 性能优化完成，可以通过浏览器性能面板验证优化效果

---

## Dependencies

**Task Dependency Graph**:

```
Phase 1 (Backend) → Phase 2 (API) → Phase 3 (Store) → Phase 4 (Chart) → Phase 5 (Lists) → Phase 6 (View) → Phase 7 (Performance)
```

**Parallel Opportunities**:
- Phase 1 内部：T001, T002 可以并行（不同函数）
- Phase 2 内部：T006, T007 可以并行（不同方法）
- Phase 3 内部：T008, T009 可以并行（不同方法）
- Phase 4 内部：T012, T013 可以并行（不同功能）
- Phase 5 内部：T016, T017 可以并行（不同组件）
- Phase 6 内部：T021, T022 可以并行（不同功能）
- Phase 7 内部：T025, T026, T027, T028 可以并行（不同优化点）

**Critical Path**: 
- T001 → T002 → T003 → T006 → T008 → T012 → T016 → T021

---

## Implementation Strategy

**MVP Scope**: 
- 完成 Phase 1-6，实现基本的分页功能
- Phase 7 可以在 MVP 后完善

**Incremental Delivery**:
1. **Step 1**: 后端支持分页参数（Phase 1）
2. **Step 2**: API 层支持分页请求（Phase 2）
3. **Step 3**: Store 支持分页数据管理（Phase 3）
4. **Step 4**: 图表组件支持分页显示（Phase 4）
5. **Step 5**: 列表组件支持分页显示（Phase 5）
6. **Step 6**: 视图集成分页功能（Phase 6）
7. **Step 7**: 性能优化（Phase 7）

**Testing Strategy**:
- 手动测试：打开股票详情页，验证分页加载功能
- 性能测试：对比优化前后的加载时间和内存占用
- 用户体验测试：验证滚动加载和"加载更多"按钮的交互体验

**Default Pagination Settings**:
- K线数据（bars）：初始加载 100 条，每页 100 条
- 分型数据（fxs）：初始加载 50 条，每页 50 条
- 笔数据（bis）：初始加载 50 条，每页 50 条

---

## Summary

**Total Tasks**: 28
- Phase 1 (Backend): 5 tasks
- Phase 2 (API): 2 tasks  
- Phase 3 (Store): 4 tasks
- Phase 4 (Chart): 4 tasks
- Phase 5 (Lists): 5 tasks
- Phase 6 (View): 4 tasks
- Phase 7 (Performance): 4 tasks

**Estimated Complexity**: Medium-High
- 主要修改：后端接口、前端 Store、图表和列表组件
- 新增功能：分页参数、分页状态管理、滚动加载
- 性能优化：虚拟滚动、缓存策略、防抖节流

**Risk Areas**:
- 分页数据的缓存和合并逻辑可能复杂
- 滚动加载的触发时机需要精确控制
- 大量数据的渲染性能需要优化
- 分页状态管理需要仔细设计

**Performance Benefits**:
- 后端：减少数据传输量，提升响应速度
- 前端：减少初始加载时间，降低内存占用
- 用户体验：页面加载更快，交互更流畅
