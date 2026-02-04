# Tasks: 股票详情页性能优化 - 按需加载周期数据

**Input**: 用户需求：`/stock/:symbol` 因为性能原因，只分析30分钟、60分钟、日的数据，并且在选择30分钟数据的情况下请求对应的后端接口和分析结果。选择60分钟、选择日 同理

**Prerequisites**: 
- 现有实现：`frontend/src/views/StockDetail.vue` 一次性请求所有周期（1,5,15,30,60分钟+日线）
- 后端接口：`backend/src/api/v1/analysis.py` 的 `/stock/{symbol}/local_czsc` 支持多周期请求
- Store：`frontend/src/stores/stockDetail.ts` 管理状态

**Tests**: 本次优化不包含测试任务（用户未要求）

**Organization**: 任务按功能模块组织，支持独立实现和测试

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以并行执行（不同文件，无依赖关系）
- **[Story]**: 所属用户故事（US1 = 股票详情页性能优化）
- 所有任务都包含明确的文件路径

## Path Conventions

- **前端**: `frontend/src/`
- **后端**: `backend/src/`
- **API**: `backend/src/api/v1/`

---

## Phase 1: 后端接口优化 - 支持单周期请求

**Purpose**: 修改后端接口，支持只请求单个周期，而不是一次性返回所有周期

**Goal**: 后端接口支持 `freqs` 参数为单个周期（如 "30" 或 "60" 或 "日线"），只分析并返回该周期的数据

**Independent Test**: 调用 `/stock/600078.SH/local_czsc?freqs=30&sdt=20180101` 应该只返回30分钟周期的数据，不包含其他周期

### Implementation for Backend

- [x] T001 [P] [US1] 修改后端接口参数解析，支持单周期请求在 `backend/src/api/v1/analysis.py` 的 `get_local_czsc` 函数中，确保 `freqs` 参数可以接受单个周期值（如 "30"、"60"、"日线"）

- [x] T002 [US1] 优化 `LocalCzscService.analyze_multi` 方法，当只请求单个周期时跳过其他周期的计算在 `backend/src/services/local_czsc_service.py` 中，修改 `analyze_multi` 方法，根据 `freqs` 参数只计算请求的周期，避免不必要的计算

- [x] T003 [US1] 添加日志记录，记录请求的周期和实际计算的周期在 `backend/src/services/local_czsc_service.py` 中添加日志，记录用户请求的周期列表和实际执行的周期分析

**Checkpoint**: 后端接口支持单周期请求，可以通过 API 测试工具验证只返回请求周期的数据

---

## Phase 2: 前端 Store 优化 - 支持按周期缓存和加载

**Purpose**: 修改前端状态管理，支持按周期缓存数据，实现按需加载

**Goal**: Store 中按周期分别存储数据，切换周期时只请求未缓存的周期

**Independent Test**: 打开股票详情页，选择30分钟周期，应该只请求30分钟数据；切换到60分钟时，如果已缓存则直接显示，未缓存则请求

### Implementation for Frontend Store

- [x] T004 [P] [US1] 修改 `stockDetail.ts` Store，将 `localCzsc` 改为按周期存储的 Map 结构在 `frontend/src/stores/stockDetail.ts` 中，将 `localCzsc` 从单一对象改为 `Map<string, LocalCzscResponseData>`，key 为周期名称（如 "30分钟"、"60分钟"、"日线"）

- [x] T005 [US1] 添加 `fetchSingleFreq` 方法，支持只请求单个周期的数据在 `frontend/src/stores/stockDetail.ts` 中添加新方法 `fetchSingleFreq(symbol, sdt, edt, freq, baseFreq)`，只请求指定周期的数据

- [x] T006 [US1] 添加缓存检查逻辑，已缓存的周期不再重复请求在 `frontend/src/stores/stockDetail.ts` 中，在 `fetchSingleFreq` 方法中添加缓存检查，如果该周期数据已存在且时间范围匹配，则直接返回缓存数据

- [x] T007 [US1] 修改 `fetchLocalCzsc` 方法，保留为兼容性方法但标记为废弃在 `frontend/src/stores/stockDetail.ts` 中，保留原有方法但添加注释说明建议使用 `fetchSingleFreq`

**Checkpoint**: Store 支持按周期缓存和按需加载，可以通过 Vue DevTools 验证状态管理

---

## Phase 3: 前端 API 层优化 - 支持单周期请求

**Purpose**: 修改前端 API 调用层，支持只请求单个周期

**Goal**: API 层提供单周期请求方法，与 Store 配合实现按需加载

**Independent Test**: 调用 `analysisApi.getLocalCzscSingleFreq` 应该只请求指定周期的数据

### Implementation for Frontend API

- [x] T008 [P] [US1] 在 `analysis.ts` 中添加 `getLocalCzscSingleFreq` 方法在 `frontend/src/api/analysis.ts` 中，添加新方法 `getLocalCzscSingleFreq(symbol, sdt, edt, freq, baseFreq)`，只请求单个周期的数据

- [x] T009 [US1] 修改 `getLocalCzsc` 方法，添加注释说明多周期请求的性能影响在 `frontend/src/api/analysis.ts` 中，为 `getLocalCzsc` 方法添加注释，说明一次性请求多个周期可能影响性能，建议使用单周期请求

**Checkpoint**: API 层支持单周期请求，可以通过浏览器 Network 面板验证只发送单个周期的请求

---

## Phase 4: 前端视图优化 - 修改周期选项和按需加载逻辑

**Purpose**: 修改股票详情页，只显示30分钟、60分钟、日线三个选项，并实现按需加载

**Goal**: 用户界面只显示三个周期选项，选择周期时才请求对应数据

**Independent Test**: 打开股票详情页，应该只看到30分钟、60分钟、日线三个标签页；点击某个标签页时，Network 面板应该只看到该周期的请求

### Implementation for Frontend View

- [x] T010 [P] [US1] 修改 `StockDetail.vue`，将可用周期列表改为只包含30分钟、60分钟、日线在 `frontend/src/views/StockDetail.vue` 中，修改 `availableFreqs` 计算属性，只返回 `['30分钟', '60分钟', '日线']`

- [x] T011 [US1] 修改默认周期为 "30分钟"在 `frontend/src/views/StockDetail.vue` 中，将 `store.activeFreq` 的默认值改为 "30分钟"

- [x] T012 [US1] 移除一次性加载所有周期的逻辑，改为按需加载在 `frontend/src/views/StockDetail.vue` 中，修改 `handleRefresh` 方法，不再调用 `fetchLocalCzsc` 一次性加载所有周期

- [x] T013 [US1] 添加周期切换监听，切换周期时按需加载数据在 `frontend/src/views/StockDetail.vue` 中，添加 `watch` 监听 `store.activeFreq`，当周期切换时调用 `store.fetchSingleFreq` 加载对应周期数据

- [x] T014 [US1] 修改初始化逻辑，页面加载时只请求默认周期（30分钟）的数据在 `frontend/src/views/StockDetail.vue` 的 `onMounted` 中，只请求30分钟周期的数据

- [x] T015 [US1] 修改 `itemsKeys` 计算属性，从当前周期的缓存中获取数据在 `frontend/src/views/StockDetail.vue` 中，修改 `itemsKeys` 和 `activeItem` 计算属性，从 Store 的周期缓存中获取当前激活周期的数据

- [x] T016 [US1] 添加加载状态提示，显示当前正在加载的周期在 `frontend/src/views/StockDetail.vue` 中，为每个周期添加独立的加载状态，显示 "正在加载30分钟数据..." 等提示

- [x] T017 [US1] 修改日期范围变更逻辑，只刷新当前激活周期的数据在 `frontend/src/views/StockDetail.vue` 的 `handleDateChange` 方法中，只刷新当前激活周期的数据，不清空其他周期的缓存

**Checkpoint**: 前端视图支持按需加载，用户切换周期时只请求对应数据，可以通过浏览器 Network 面板和 Vue DevTools 验证

---

## Phase 5: 类型定义优化 - 更新 TypeScript 类型

**Purpose**: 更新 TypeScript 类型定义，支持按周期存储的数据结构

**Goal**: 类型定义与新的 Store 结构保持一致

**Independent Test**: TypeScript 编译无错误，类型检查通过

### Implementation for Type Definitions

- [ ] T018 [P] [US1] 更新 `stockDetail.ts` Store 的返回类型，支持按周期存储在 `frontend/src/stores/stockDetail.ts` 中，更新 Store 的返回类型，`localCzsc` 改为 `Map<string, LocalCzscResponseData>`

- [ ] T019 [US1] 更新 `analysis.ts` API 方法的类型定义在 `frontend/src/api/analysis.ts` 中，为 `getLocalCzscSingleFreq` 方法添加完整的类型定义

**Checkpoint**: TypeScript 类型定义完整，编译无错误

---

## Phase 6: 文档和注释更新

**Purpose**: 更新代码注释和文档，说明性能优化和按需加载机制

**Goal**: 代码注释清晰，便于后续维护

**Independent Test**: 代码注释完整，新开发者可以理解按需加载的实现逻辑

### Documentation

- [ ] T020 [P] [US1] 在 `StockDetail.vue` 中添加注释，说明按需加载的性能优化在 `frontend/src/views/StockDetail.vue` 文件顶部添加注释，说明为什么只支持30/60分钟和日线，以及按需加载的实现方式

- [ ] T021 [P] [US1] 在 `stockDetail.ts` Store 中添加注释，说明周期缓存机制在 `frontend/src/stores/stockDetail.ts` 中，为周期缓存相关的代码添加详细注释

- [ ] T022 [P] [US1] 在 `analysis.py` 后端接口中添加注释，说明单周期请求的优化在 `backend/src/api/v1/analysis.py` 的 `get_local_czsc` 函数中添加注释，说明支持单周期请求的性能优势

**Checkpoint**: 代码注释完整，文档清晰

---

## Dependencies

**Task Dependency Graph**:

```
Phase 1 (Backend) → Phase 2 (Store) → Phase 3 (API) → Phase 4 (View) → Phase 5 (Types) → Phase 6 (Docs)
```

**Parallel Opportunities**:
- Phase 1 内部：T001, T002 可以并行（不同函数）
- Phase 2 内部：T004, T005 可以并行（不同方法）
- Phase 3 内部：T008, T009 可以并行（不同方法）
- Phase 4 内部：T010, T011 可以并行（不同属性）
- Phase 5 内部：T018, T019 可以并行（不同文件）
- Phase 6 内部：T020, T021, T022 可以并行（不同文件）

**Critical Path**: 
- T001 → T002 → T004 → T005 → T008 → T010 → T012 → T013 → T014

---

## Implementation Strategy

**MVP Scope**: 
- 完成 Phase 1-4，实现基本的按需加载功能
- Phase 5-6 可以在 MVP 后完善

**Incremental Delivery**:
1. **Step 1**: 后端支持单周期请求（Phase 1）
2. **Step 2**: Store 支持周期缓存（Phase 2）
3. **Step 3**: API 层支持单周期请求（Phase 3）
4. **Step 4**: 前端视图实现按需加载（Phase 4）
5. **Step 5**: 完善类型定义和文档（Phase 5-6）

**Testing Strategy**:
- 手动测试：打开股票详情页，切换周期，观察 Network 请求
- 性能测试：对比优化前后的请求数量和响应时间
- 用户体验测试：验证切换周期时的加载状态和错误处理

---

## Summary

**Total Tasks**: 22
- Phase 1 (Backend): 3 tasks
- Phase 2 (Store): 4 tasks  
- Phase 3 (API): 2 tasks
- Phase 4 (View): 8 tasks
- Phase 5 (Types): 2 tasks
- Phase 6 (Docs): 3 tasks

**Estimated Complexity**: Medium
- 主要修改：前端 Store 和 View 组件
- 次要修改：后端接口和 API 层
- 新增功能：按周期缓存和按需加载

**Risk Areas**:
- Store 数据结构变更可能影响现有代码
- 周期切换时的状态管理需要仔细处理
- 缓存失效策略需要合理设计
