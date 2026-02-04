# Tasks: K线数据返回最近3个月，分析数据返回全量

**Input**: 用户需求：每次返回最近3个月的K线数据，分析数据返回的是全量的

**Prerequisites**: 
- 现有实现：`backend/src/services/local_czsc_service.py` 的 `_analyze_one` 函数基于传入的 bars 进行分析
- 分页功能：已实现分页参数支持，但需要调整为基于时间范围的策略
- 前端组件：`frontend/src/components/KlineChartTradingVue.vue`、`BiList.vue`、`FxList.vue` 显示数据

**Tests**: 本次优化不包含测试任务（用户未要求）

**Organization**: 任务按功能模块组织，支持独立实现和测试

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以并行执行（不同文件，无依赖关系）
- **[Story]**: 所属用户故事（US1 = K线数据返回最近3个月，分析数据返回全量）
- 所有任务都包含明确的文件路径

## Path Conventions

- **前端**: `frontend/src/`
- **后端**: `backend/src/`
- **API**: `backend/src/api/v1/`

---

## Phase 1: 后端逻辑优化 - 分离K线数据和分析数据的时间范围

**Purpose**: 修改后端分析逻辑，使用全量数据进行CZSC分析，但只返回最近3个月的K线数据

**Goal**: 
- CZSC分析基于全量历史数据（确保分析准确性）
- 返回的K线数据（bars）只包含最近3个月
- 返回的分析数据（fxs、bis）基于全量数据，返回全量结果

**Independent Test**: 调用 `/stock/600078.SH/local_czsc?freqs=30&sdt=20180101&edt=20241231` 应该返回最近3个月的K线数据，但分型和笔数据应该基于全量历史数据

### Implementation for Backend

- [x] T001 [P] [US1] 修改 `_analyze_one` 函数，分离K线数据和分析数据的处理逻辑在 `backend/src/services/local_czsc_service.py` 中，修改 `_analyze_one` 函数，使用全量 bars 进行 CZSC 分析，但只返回最近3个月的 bars

- [x] T002 [US1] 添加时间范围计算函数，计算最近3个月的日期范围在 `backend/src/services/local_czsc_service.py` 中，添加 `_get_recent_3months_range` 函数，根据 `edt` 计算最近3个月的开始日期

- [x] T003 [US1] 修改 `_analyze_one` 函数，过滤K线数据为最近3个月在 `backend/src/services/local_czsc_service.py` 中，修改 `_analyze_one` 函数，在返回 bars 时只包含最近3个月的数据，但分析仍基于全量数据

- [x] T004 [US1] 添加配置参数，支持自定义"最近N个月"的数值在 `backend/src/services/local_czsc_service.py` 中，添加 `recent_months` 参数（默认3），支持配置返回最近几个月的K线数据

- [x] T005 [US1] 添加日志记录，记录K线数据和分析数据的时间范围在 `backend/src/services/local_czsc_service.py` 中添加日志，记录全量数据范围、返回的K线数据范围、分析数据范围

**Checkpoint**: 后端逻辑支持分离K线数据和分析数据的时间范围，可以通过 API 测试工具验证

---

## Phase 2: 后端接口优化 - 添加时间范围控制参数

**Purpose**: 修改后端接口，支持配置返回最近N个月的K线数据

**Goal**: 后端接口支持 `recent_months` 参数，控制返回的K线数据时间范围

**Independent Test**: 调用 `/stock/600078.SH/local_czsc?freqs=30&recent_months=3` 应该返回最近3个月的K线数据

### Implementation for Backend API

- [x] T006 [P] [US1] 修改后端接口参数，添加 `recent_months` 参数在 `backend/src/api/v1/analysis.py` 的 `get_local_czsc` 函数中，添加 `recent_months` 参数（默认3）

- [x] T007 [US1] 传递 `recent_months` 参数到服务层在 `backend/src/api/v1/analysis.py` 中，将 `recent_months` 参数传递给 `LocalCzscService.analyze_multi` 方法

- [x] T008 [US1] 修改 `analyze_multi` 方法，支持 `recent_months` 参数在 `backend/src/services/local_czsc_service.py` 中，修改 `analyze_multi` 方法签名，添加 `recent_months` 参数

- [x] T009 [US1] 传递 `recent_months` 参数到分析函数在 `backend/src/services/local_czsc_service.py` 中，将 `recent_months` 参数传递给 `_analyze_items` 和 `_analyze_one` 函数

**Checkpoint**: 后端接口支持 `recent_months` 参数，可以通过 API 测试工具验证

---

## Phase 3: 前端 API 层优化 - 支持时间范围控制参数

**Purpose**: 修改前端 API 调用层，支持 `recent_months` 参数

**Goal**: API 层提供 `recent_months` 参数，与后端接口配合实现时间范围控制

**Independent Test**: 调用 `analysisApi.getLocalCzscSingleFreq` 时传入 `recent_months=3`，应该只返回最近3个月的K线数据

### Implementation for Frontend API

- [x] T010 [P] [US1] 修改 `getLocalCzscSingleFreq` 方法，添加 `recent_months` 参数在 `frontend/src/api/analysis.ts` 中，为 `getLocalCzscSingleFreq` 方法添加 `recent_months` 参数（默认3）

- [x] T011 [US1] 更新类型定义，支持 `recent_months` 参数在 `frontend/src/api/analysis.ts` 中，更新方法签名和注释，说明 `recent_months` 参数的作用

**Checkpoint**: API 层支持 `recent_months` 参数，可以通过浏览器 Network 面板验证

---

## Phase 4: 前端 Store 优化 - 支持时间范围控制

**Purpose**: 修改前端状态管理，支持 `recent_months` 参数

**Goal**: Store 中支持 `recent_months` 参数，默认使用3个月

**Independent Test**: 调用 `store.fetchSingleFreq` 时应该默认只请求最近3个月的K线数据

### Implementation for Frontend Store

- [x] T012 [P] [US1] 修改 `fetchSingleFreq` 方法，添加 `recent_months` 参数在 `frontend/src/stores/stockDetail.ts` 中，为 `fetchSingleFreq` 方法添加 `recent_months` 参数（默认3）

- [x] T013 [US1] 传递 `recent_months` 参数到 API 调用在 `frontend/src/stores/stockDetail.ts` 中，将 `recent_months` 参数传递给 `analysisApi.getLocalCzscSingleFreq` 方法

- [x] T014 [US1] 添加注释说明，解释K线数据和分析数据的时间范围差异在 `frontend/src/stores/stockDetail.ts` 中添加注释，说明K线数据只返回最近3个月，但分析数据基于全量历史数据

**Checkpoint**: Store 支持 `recent_months` 参数，可以通过 Vue DevTools 验证

---

## Phase 5: 前端视图优化 - 显示时间范围信息

**Purpose**: 修改股票详情页，显示K线数据和分析数据的时间范围信息

**Goal**: 页面显示K线数据的时间范围（最近3个月）和分析数据的时间范围（全量）

**Independent Test**: 打开股票详情页，应该显示"K线数据：最近3个月"和"分析数据：全量历史数据"的提示

### Implementation for Frontend View

- [x] T015 [P] [US1] 修改 `StockDetail.vue`，添加时间范围信息显示在 `frontend/src/views/StockDetail.vue` 中，在数据元信息区域添加K线数据和分析数据的时间范围说明

- [x] T016 [US1] 添加提示信息，说明K线数据和分析数据的时间范围差异在 `frontend/src/views/StockDetail.vue` 中，添加提示信息，说明"K线数据仅显示最近3个月，但分型和笔分析基于全量历史数据"

- [x] T017 [US1] 优化初始请求，使用默认的 `recent_months=3` 参数在 `frontend/src/views/StockDetail.vue` 中，修改初始请求逻辑，传递 `recent_months=3` 参数

**Checkpoint**: 前端视图显示时间范围信息，可以通过浏览器验证

---

## Phase 6: 文档和注释更新

**Purpose**: 更新代码注释和文档，说明时间范围控制机制

**Goal**: 代码注释清晰，便于后续维护

**Independent Test**: 代码注释完整，新开发者可以理解时间范围控制的实现逻辑

### Documentation

- [x] T018 [P] [US1] 在 `local_czsc_service.py` 中添加注释，说明时间范围控制逻辑在 `backend/src/services/local_czsc_service.py` 中，为时间范围控制相关的代码添加详细注释

- [x] T019 [P] [US1] 在 `analysis.py` 后端接口中添加注释，说明 `recent_months` 参数在 `backend/src/api/v1/analysis.py` 的 `get_local_czsc` 函数中添加注释，说明 `recent_months` 参数的作用和默认值

- [x] T020 [P] [US1] 在 `analysis.ts` API 方法中添加注释，说明时间范围控制在 `frontend/src/api/analysis.ts` 中，为 `getLocalCzscSingleFreq` 方法添加注释，说明 `recent_months` 参数

**Checkpoint**: 代码注释完整，文档清晰

---

## Dependencies

**Task Dependency Graph**:

```
Phase 1 (Backend Logic) → Phase 2 (Backend API) → Phase 3 (Frontend API) → Phase 4 (Store) → Phase 5 (View) → Phase 6 (Docs)
```

**Parallel Opportunities**:
- Phase 1 内部：T001, T002 可以并行（不同函数）
- Phase 2 内部：T006, T007 可以并行（不同函数）
- Phase 3 内部：T010, T011 可以并行（不同方法）
- Phase 4 内部：T012, T013 可以并行（不同方法）
- Phase 5 内部：T015, T016 可以并行（不同功能）
- Phase 6 内部：T018, T019, T020 可以并行（不同文件）

**Critical Path**: 
- T001 → T003 → T006 → T008 → T010 → T012 → T015

---

## Implementation Strategy

**MVP Scope**: 
- 完成 Phase 1-5，实现基本的时间范围控制功能
- Phase 6 可以在 MVP 后完善

**Incremental Delivery**:
1. **Step 1**: 后端逻辑支持分离K线数据和分析数据的时间范围（Phase 1）
2. **Step 2**: 后端接口支持 `recent_months` 参数（Phase 2）
3. **Step 3**: API 层支持 `recent_months` 参数（Phase 3）
4. **Step 4**: Store 支持 `recent_months` 参数（Phase 4）
5. **Step 5**: 视图显示时间范围信息（Phase 5）
6. **Step 6**: 完善文档和注释（Phase 6）

**Testing Strategy**:
- 手动测试：调用 API 验证返回的K线数据只包含最近3个月
- 数据验证：验证分析数据（fxs、bis）基于全量数据计算
- 用户体验测试：验证前端显示的时间范围信息

**Default Settings**:
- `recent_months`: 默认值为 3（返回最近3个月的K线数据）
- 分析数据：始终基于全量历史数据，返回全量结果

**Implementation Details**:
- K线数据过滤：在 `_analyze_one` 函数中，使用全量 bars 进行 CZSC 分析，但在返回时只包含最近3个月的 bars
- 分析数据：fxs 和 bis 基于全量 bars 计算，返回全量结果（不受 `recent_months` 限制）
- 时间范围计算：根据 `edt`（结束日期）向前推3个月，作为K线数据的开始日期

---

## Summary

**Total Tasks**: 20
- Phase 1 (Backend Logic): 5 tasks
- Phase 2 (Backend API): 4 tasks  
- Phase 3 (Frontend API): 2 tasks
- Phase 4 (Store): 3 tasks
- Phase 5 (View): 3 tasks
- Phase 6 (Docs): 3 tasks

**Estimated Complexity**: Medium
- 主要修改：后端分析逻辑，分离K线数据和分析数据的时间范围
- 新增功能：`recent_months` 参数，时间范围计算
- 性能优化：减少K线数据传输量，但保持分析准确性

**Risk Areas**:
- 时间范围计算需要考虑不同月份的天数差异
- 确保分析数据基于全量数据，不受K线数据过滤影响
- 前端需要清楚显示时间范围差异，避免用户混淆

**Performance Benefits**:
- 后端：减少K线数据传输量（只传输最近3个月）
- 前端：减少K线数据渲染负担，提升页面性能
- 分析准确性：保持基于全量历史数据的分析准确性

**Key Design Decisions**:
- K线数据：只返回最近3个月（减少数据传输和渲染负担）
- 分析数据：基于全量历史数据计算，返回全量结果（确保分析准确性）
- 可配置性：支持 `recent_months` 参数，可以调整返回的月份数
