# Tasks: 单周期数据返回验证和修复

**Input**: 用户需求：`http://localhost:5173/stock/SH600078` 选择30分钟只返回30分钟的k线数据和分析数据，选择60分钟返回60分钟的K线和分析数据，选择日线返回日线的K线数据和分析数据。

**Prerequisites**: 
- 已完成性能优化：按需加载功能已实现
- 后端接口：`backend/src/api/v1/analysis.py` 的 `/stock/{symbol}/local_czsc` 支持单周期请求
- Store：`frontend/src/stores/stockDetail.ts` 支持按周期缓存
- 视图：`frontend/src/views/StockDetail.vue` 支持按需加载

**Tests**: 本次任务包含验证测试，确保数据一致性

**Organization**: 任务按验证和修复组织，确保单周期请求只返回对应周期的数据

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可以并行执行（不同文件，无依赖关系）
- **[Story]**: 所属用户故事（US1 = 单周期数据返回验证）
- 所有任务都包含明确的文件路径

## Path Conventions

- **前端**: `frontend/src/`
- **后端**: `backend/src/`
- **API**: `backend/src/api/v1/`

---

## Phase 1: 后端验证 - 确保只返回请求的周期数据

**Purpose**: 验证后端接口在单周期请求时，只返回该周期的数据，不包含其他周期

**Goal**: 后端返回的 `items` 字典只包含请求的周期，`meta.target_freqs` 也只包含请求的周期

**Independent Test**: 调用 `/stock/600078.SH/local_czsc?freqs=30&sdt=20180101` 应该只返回30分钟周期的数据，`items` 字典的 key 应该只有 "30分钟"

### Verification and Fix for Backend

- [x] T001 [P] [US1] 验证后端 `_analyze_items` 函数，确保只处理请求的周期在 `backend/src/services/local_czsc_service.py` 中，检查 `_analyze_items` 函数，确保 `targets` 参数只包含请求的周期，不会添加其他周期

- [x] T002 [US1] 验证后端 `_targets_from` 函数，确保单周期请求时只返回一个周期在 `backend/src/services/local_czsc_service.py` 中，检查 `_targets_from` 函数，当 `freqs` 为单个周期（如 "30"）时，确保只返回一个 `Freq` 对象

- [ ] T003 [US1] 添加后端单元测试，验证单周期请求只返回该周期数据在 `backend/tests/` 中创建测试文件，验证单周期请求时返回的数据结构只包含请求的周期（可选，手动测试已足够）

- [x] T004 [US1] 修复后端返回数据，确保 `items` 只包含请求的周期在 `backend/src/services/local_czsc_service.py` 的 `_analyze_cached` 函数中，确保返回的 `items` 字典只包含 `targets` 中的周期，过滤掉其他周期

**Checkpoint**: 后端接口验证通过，单周期请求只返回该周期的数据

---

## Phase 2: 前端验证 - 确保只显示当前激活周期的数据

**Purpose**: 验证前端只显示当前激活周期的数据，不显示其他周期的数据

**Goal**: 前端视图只显示 `store.activeFreq` 对应的周期数据，图表、统计、列表都只显示该周期

**Independent Test**: 打开股票详情页，选择30分钟周期，应该只看到30分钟的数据；切换到60分钟，应该只看到60分钟的数据

### Verification and Fix for Frontend

- [x] T005 [P] [US1] 验证 `activeItem` 计算属性，确保只从当前周期获取数据在 `frontend/src/views/StockDetail.vue` 中，检查 `activeItem` 计算属性，确保只从 `store.localCzsc.items[store.activeFreq]` 获取数据

- [x] T006 [US1] 验证 `itemsKeys` 计算属性，确保只返回当前周期的 key在 `frontend/src/views/StockDetail.vue` 中，检查 `itemsKeys` 计算属性，确保只返回当前激活周期的 key，不包含其他周期

- [x] T007 [US1] 验证 Store 缓存，确保每个周期独立存储数据在 `frontend/src/stores/stockDetail.ts` 中，检查 `localCzscCache` 的存储逻辑，确保每个周期的数据独立存储，不会混合

- [x] T008 [US1] 添加前端控制台日志，验证数据加载和显示在 `frontend/src/views/StockDetail.vue` 中添加日志，记录当前激活周期、加载的数据周期、显示的数据周期，确保一致性

- [x] T009 [US1] 验证周期切换逻辑，确保切换时只加载对应周期在 `frontend/src/views/StockDetail.vue` 中，检查 `watch` 监听器，确保周期切换时只调用 `fetchSingleFreq` 加载对应周期

**Checkpoint**: 前端验证通过，只显示当前激活周期的数据

---

## Phase 3: 端到端验证 - 完整流程测试

**Purpose**: 端到端验证，确保从请求到显示的数据一致性

**Goal**: 用户选择某个周期时，从后端请求到前端显示，整个过程只涉及该周期的数据

**Independent Test**: 
1. 打开 `http://localhost:5173/stock/SH600078`
2. 选择30分钟周期，Network 面板应该只看到请求 `freqs=30` 的请求
3. 响应数据应该只包含30分钟周期的数据
4. 页面应该只显示30分钟的数据
5. 切换到60分钟，重复验证

### End-to-End Verification

- [ ] T010 [US1] 验证网络请求，确保只请求当前激活周期在浏览器 Network 面板中，验证选择不同周期时，API 请求的 `freqs` 参数只包含当前周期（如 `freqs=30` 或 `freqs=60` 或 `include_daily=true`）

- [ ] T011 [US1] 验证响应数据，确保只返回请求的周期在浏览器 Network 面板中，验证 API 响应的 `items` 字典只包含请求的周期，`meta.target_freqs` 也只包含请求的周期

- [ ] T012 [US1] 验证页面显示，确保只显示当前激活周期的数据在浏览器中，验证页面显示的K线图、统计信息、分型列表、笔列表都只包含当前激活周期的数据

- [ ] T013 [US1] 验证周期切换，确保切换时数据正确更新在浏览器中，验证从30分钟切换到60分钟时，页面数据正确更新为60分钟的数据，不显示30分钟的数据

- [ ] T014 [US1] 验证缓存机制，确保已缓存的周期直接显示在浏览器中，验证切换到已加载的周期时，不发送网络请求，直接显示缓存的数据

**Checkpoint**: 端到端验证通过，完整流程只涉及当前激活周期的数据

---

## Phase 4: 数据一致性修复（如需要）

**Purpose**: 如果验证发现问题，修复数据不一致的问题

**Goal**: 确保后端返回的数据和前端显示的数据完全一致，只包含当前激活周期

### Data Consistency Fixes

- [ ] T015 [US1] 修复后端数据过滤，确保只返回请求的周期（如发现问题）在 `backend/src/services/local_czsc_service.py` 中，如果发现返回了多个周期，添加过滤逻辑，只返回 `targets` 中的周期

- [ ] T016 [US1] 修复前端数据过滤，确保只显示当前激活周期（如发现问题）在 `frontend/src/views/StockDetail.vue` 中，如果发现显示了其他周期的数据，添加过滤逻辑，只显示 `store.activeFreq` 对应的数据

- [ ] T017 [US1] 修复 Store 缓存逻辑，确保周期数据独立存储（如发现问题）在 `frontend/src/stores/stockDetail.ts` 中，如果发现缓存混合了多个周期，修复存储逻辑，确保每个周期独立存储

**Checkpoint**: 数据一致性修复完成，所有问题已解决

---

## Dependencies

**Task Dependency Graph**:

```
Phase 1 (Backend Verification) → Phase 2 (Frontend Verification) → Phase 3 (E2E Verification) → Phase 4 (Fixes if needed)
```

**Parallel Opportunities**:
- Phase 1 内部：T001, T002 可以并行（不同函数）
- Phase 2 内部：T005, T006, T007 可以并行（不同属性/逻辑）
- Phase 3 内部：T010, T011, T012 可以并行（不同验证点）
- Phase 4 内部：T015, T016, T017 可以并行（不同文件）

**Critical Path**: 
- T001 → T002 → T004 → T005 → T006 → T010 → T011 → T012

---

## Implementation Strategy

**MVP Scope**: 
- 完成 Phase 1-3，验证数据一致性
- Phase 4 仅在发现问题时执行

**Incremental Delivery**:
1. **Step 1**: 后端验证（Phase 1）
2. **Step 2**: 前端验证（Phase 2）
3. **Step 3**: 端到端验证（Phase 3）
4. **Step 4**: 修复问题（Phase 4，如需要）

**Testing Strategy**:
- 单元测试：验证后端单周期请求逻辑
- 集成测试：验证前后端数据传递
- 端到端测试：在浏览器中验证完整流程
- 手动测试：验证用户体验和数据一致性

---

## Summary

**Total Tasks**: 17
- Phase 1 (Backend Verification): 4 tasks
- Phase 2 (Frontend Verification): 5 tasks  
- Phase 3 (E2E Verification): 5 tasks
- Phase 4 (Fixes if needed): 3 tasks

**Estimated Complexity**: Low-Medium
- 主要工作：验证现有实现
- 次要工作：修复可能的数据不一致问题
- 新增功能：无（仅验证和修复）

**Risk Areas**:
- 后端可能返回了多个周期的数据（需要过滤）
- 前端可能显示了其他周期的数据（需要过滤）
- 缓存可能混合了多个周期的数据（需要修复）
