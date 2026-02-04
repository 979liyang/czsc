# Tasks: CZSC API与前端界面增强

**Input**: Design documents from `/specs/001-czsc-api-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are OPTIONAL - not explicitly requested in spec, so no test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`, `data/` at repository root

---

## Phase 0: 学习与理解阶段

**Purpose**: 深入学习czsc库的核心功能、数据格式、使用方法和案例，为后续开发奠定基础

**⚠️ CRITICAL**: 这是所有开发工作的基础，必须充分理解czsc后才能开始实现

- [X] T001 学习czsc核心对象结构，理解RawBar、NewBar、FX、BI、ZS等数据对象的定义和用途，记录在docs/learning/czsc_objects.md
- [X] T002 学习czsc.analyze模块，理解CZSC类的分型和笔识别算法，分析examples/目录下的案例代码
- [X] T003 [P] 学习czsc.traders模块，理解CzscTrader、CzscSignals、BarGenerator的使用方法，记录在docs/learning/czsc_traders.md
- [X] T004 [P] 学习czsc.signals模块，分析所有信号函数的签名、参数和返回值格式，记录在docs/learning/czsc_signals.md
- [X] T005 [P] 学习czsc.connectors模块，理解research、ts_connector等数据源的接口和使用方法，记录在docs/learning/czsc_connectors.md
- [X] T006 分析examples/目录下的策略示例，理解CzscStrategyBase的使用模式和Position、Event、Factor的构建方式
- [X] T007 分析czsc对数据格式的要求，总结RawBar的必需字段和格式规范，记录在docs/learning/data_format.md
- [X] T008 研究czsc.utils.bar_generator模块，理解K线合成和多周期处理机制
- [X] T009 分析现有数据存储方式（如CZSC投研数据目录结构），理解Parquet文件的使用模式

**Checkpoint**: 完成czsc核心功能学习，理解数据格式要求，可以开始设计数据结构

---

## Phase 1: Setup (项目初始化)

**Purpose**: 创建项目基础结构和配置文件

- [X] T010 创建backend目录结构，按照plan.md中的结构创建所有目录和__init__.py文件
- [X] T011 [P] 创建frontend目录结构，初始化Vue3项目，配置Vite、TypeScript、ElementPlus、TailwindCSS
- [X] T012 [P] 创建data目录结构，包括klines/、metadata/、cache/子目录
- [X] T013 创建backend/requirements.txt，包含FastAPI、czsc、pandas、pyarrow、sqlalchemy等依赖
- [X] T014 [P] 创建frontend/package.json，配置Vue3、ElementPlus、TailwindCSS、Vue Router、Pinia、Axios等依赖
- [X] T015 创建backend/README.md和frontend/README.md，说明项目结构和启动方式
- [X] T016 [P] 配置backend代码格式工具（black、isort），创建配置文件
- [X] T017 [P] 配置frontend代码格式工具（prettier、eslint），创建配置文件

**Checkpoint**: 项目结构创建完成，可以开始基础功能开发

---

## Phase 2: Foundational (基础功能 - 阻塞所有用户故事)

**Purpose**: 核心基础设施，所有用户故事都依赖这些功能

**⚠️ CRITICAL**: 必须完成此阶段才能开始任何用户故事的实现

### 数据存储层（US5的核心，也是US1和US2的基础）

- [X] T018 设计并实现RawBar到DataFrame的转换函数，在backend/src/storage/kline_storage.py中实现_bars_to_df方法
- [X] T019 设计并实现DataFrame到RawBar的转换函数，在backend/src/storage/kline_storage.py中实现_df_to_bars方法
- [X] T020 实现KlineStorage类，支持按symbol/freq组织存储Parquet文件，在backend/src/storage/kline_storage.py
- [X] T021 实现KlineStorage.save_bars方法，保存K线数据到data/klines/{symbol}/{freq}/data.parquet
- [X] T022 实现KlineStorage.load_bars方法，从Parquet文件加载并过滤指定时间范围的K线数据
- [X] T023 实现数据索引管理，创建和维护data/klines/index.json，记录所有股票的数据元信息
- [X] T024 实现增量更新功能，支持追加新数据到现有Parquet文件而不覆盖旧数据
- [X] T025 实现MetadataStorage类，使用SQLite存储股票列表和元数据，在backend/src/storage/metadata_storage.py
- [X] T026 创建SQLite数据库schema，定义symbols表和signals表结构，在backend/src/models/database.py（schema在MetadataStorage中创建）
- [X] T027 实现缓存管理类Cache，使用functools.lru_cache和内存缓存，在backend/src/storage/cache.py

### CZSC适配器封装

- [X] T028 实现CZSCAdapter类，封装czsc常用操作，在backend/src/utils/czsc_adapter.py
- [X] T029 实现CZSCAdapter.get_bars方法，从数据存储或connector获取K线数据
- [X] T030 实现CZSCAdapter.analyze方法，执行缠论分析并返回CZSC对象
- [X] T031 实现CZSCAdapter.calculate_signals方法，计算信号并返回结果字典
- [X] T032 实现数据验证工具，验证RawBar数据格式和完整性，在backend/src/utils/validators.py

### 数据模型定义

- [X] T033 [P] 创建Pydantic模型BarRequest、BarResponse，在backend/src/models/schemas.py
- [X] T034 [P] 创建Pydantic模型AnalysisRequest、AnalysisResponse，在backend/src/models/schemas.py
- [X] T035 [P] 创建Pydantic模型SignalRequest、SignalResponse，在backend/src/models/schemas.py
- [X] T036 [P] 创建Pydantic模型BacktestRequest、BacktestResponse，在backend/src/models/schemas.py
- [X] T037 实现RawBar、BI、FX、ZS等对象的序列化方法，转换为字典格式用于JSON传输

### FastAPI基础配置

- [X] T038 创建FastAPI应用入口，配置CORS和基础中间件，在backend/src/main.py
- [X] T039 配置日志系统，使用loguru记录API请求和错误，在backend/src/main.py
- [X] T040 实现全局异常处理，统一错误响应格式，在backend/src/api/dependencies.py
- [X] T041 实现API限流中间件，防止请求频率过高，在backend/src/api/dependencies.py

**Checkpoint**: 基础功能完成，数据存储、CZSC适配器、数据模型和API框架就绪，可以开始实现用户故事

---

## Phase 3: User Story 1 - 通过Web界面进行缠论分析 (Priority: P1) 🎯 MVP

**Goal**: 用户可以通过浏览器访问Web界面，输入股票代码和时间范围，查看缠论分析结果（分型、笔、中枢）

**Independent Test**: 用户可以在浏览器中访问Web界面，输入股票代码"000001.SH"，选择日线周期，查看2023年的分析结果，系统应显示K线图、分型标记、笔的识别结果

### Implementation for User Story 1

- [X] T042 [US1] 实现AnalysisService类，封装缠论分析业务逻辑，在backend/src/services/analysis_service.py
- [X] T043 [US1] 实现AnalysisService.analyze方法，调用CZSCAdapter执行分析并返回结果
- [X] T044 [US1] 创建缠论分析API端点POST /api/v1/analysis/czsc，在backend/src/api/v1/analysis.py
- [X] T045 [US1] 实现API端点参数验证和错误处理
- [X] T046 [US1] 创建前端API客户端analysisApi，封装分析接口调用，在frontend/src/api/analysis.ts
- [X] T047 [US1] 创建Analysis.vue页面组件，包含股票代码输入、时间范围选择、周期选择表单
- [X] T048 [US1] 创建KlineChart.vue组件，使用ECharts或lightweight-charts绘制K线图，在frontend/src/components/KlineChart.vue
- [X] T049 [US1] 在KlineChart组件中实现分型标记显示（顶分型、底分型）
- [X] T050 [US1] 在KlineChart组件中实现笔的绘制（连接相邻分型）
- [X] T051 [US1] 创建BiList.vue组件，显示笔列表信息，在frontend/src/components/BiList.vue
- [X] T052 [US1] 创建FxList.vue组件，显示分型列表信息，在frontend/src/components/FxList.vue
- [X] T053 [US1] 在Analysis.vue中集成KlineChart、BiList、FxList组件
- [X] T054 [US1] 实现多周期切换功能，用户可以在同一界面切换不同周期查看分析结果（通过周期选择下拉框实现）
- [X] T055 [US1] 创建Pinia store analysis.ts，管理分析状态和结果，在frontend/src/stores/analysis.ts
- [X] T056 [US1] 配置Vue Router路由，添加/analysis路由指向Analysis.vue，在frontend/src/router/routes.ts

**Checkpoint**: User Story 1完成，用户可以通过Web界面进行缠论分析

**Note**: KlineChart组件需要K线数据，已实现bars API端点提供K线数据

---

## Phase 4: User Story 2 - 通过API获取股票数据和信号 (Priority: P1)

**Goal**: 开发者可以通过REST API获取股票K线数据、计算信号、执行策略回测

**Independent Test**: 开发者可以通过HTTP请求调用 `/api/v1/bars?symbol=000001.SH&freq=D&sdt=20230101&edt=20231231` 获取K线数据，调用 `/api/v1/signals/calculate?symbol=000001.SH&freq=D&signal=cxt_bi_status_V230101` 获取信号计算结果

### Implementation for User Story 2

- [X] T057 [US2] 实现DataService类，封装数据获取业务逻辑，在backend/src/services/data_service.py
- [X] T058 [US2] 实现DataService.get_bars方法，从存储或connector获取K线数据
- [X] T059 [US2] 创建K线数据API端点GET /api/v1/bars，在backend/src/api/v1/bars.py
- [X] T060 [US2] 实现SignalService类，封装信号计算业务逻辑，在backend/src/services/signal_service.py
- [X] T061 [US2] 实现SignalService.calculate_signal方法，动态调用czsc信号函数
- [X] T062 [US2] 实现SignalService.calculate_batch方法，批量计算多个信号
- [X] T063 [US2] 创建信号计算API端点GET /api/v1/signals/calculate，在backend/src/api/v1/signals.py
- [X] T064 [US2] 创建批量信号计算API端点POST /api/v1/signals/batch，在backend/src/api/v1/signals.py
- [X] T065 [US2] 实现BacktestService类，封装策略回测业务逻辑，在backend/src/services/backtest_service.py
- [X] T066 [US2] 实现BacktestService.run_backtest方法，执行策略回测并返回结果
- [X] T067 [US2] 创建策略回测API端点POST /api/v1/backtest/run，在backend/src/api/v1/backtest.py
- [X] T068 [US2] 创建股票列表API端点GET /api/v1/symbols，在backend/src/api/v1/symbols.py
- [X] T069 [US2] 实现API响应序列化，确保RawBar、BI、FX等对象正确转换为JSON（已在serializers.py中实现）
- [X] T070 [US2] 创建前端API客户端barsApi、signalsApi、backtestApi，在frontend/src/api/目录下
- [X] T071 [US2] 配置API客户端基础URL和错误处理，在frontend/src/api/index.ts

**Checkpoint**: User Story 2完成，API接口可用，开发者可以通过REST API获取数据和计算信号

---

## Phase 5: User Story 3 - 查看和学习信号函数文档 (Priority: P2)

**Goal**: 用户可以通过Web界面查看所有信号函数的说明、参数、返回值和使用示例

**Independent Test**: 用户访问信号函数文档页面，可以看到所有信号函数的分类列表（缠论类、技术指标类、成交量类等），点击某个信号函数可以查看详细说明、参数说明和使用示例

### Implementation for User Story 3

- [X] T072 [US3] 实现DocService类，自动分析czsc.signals模块提取信号函数信息，在backend/src/services/doc_service.py
- [X] T073 [US3] 实现DocService.get_all_signals方法，遍历所有信号函数并提取元信息
- [X] T074 [US3] 实现DocService.get_signal_detail方法，获取单个信号函数的详细信息
- [X] T075 [US3] 实现信号函数分类逻辑，按cxt、tas、bar、vol等前缀分类
- [X] T076 [US3] 创建信号函数列表API端点GET /api/v1/docs/signals，在backend/src/api/v1/docs.py
- [X] T077 [US3] 创建信号函数详情API端点GET /api/v1/docs/signals/{signal_name}，在backend/src/api/v1/docs.py
- [X] T078 [US3] 创建前端API客户端docsApi，封装文档接口调用，在frontend/src/api/docs.ts
- [X] T079 [US3] 创建Signals.vue页面组件，显示信号函数列表和分类，在frontend/src/views/Signals.vue
- [X] T080 [US3] 实现信号函数详情展示，包括函数说明、参数表格、返回值说明
- [ ] T081 [US3] 实现信号函数测试功能，用户可以在文档页面输入参数并实时计算信号（可选功能，后续实现）
- [X] T082 [US3] 创建SignalCard.vue组件，显示单个信号函数的卡片信息，在frontend/src/components/SignalCard.vue
- [X] T083 [US3] 配置Vue Router路由，添加/signals路由指向Signals.vue（已在routes.ts中配置）

**Checkpoint**: User Story 3完成，用户可以通过Web界面查看和学习信号函数文档

---

## Phase 6: User Story 4 - 使用更多策略示例 (Priority: P2)

**Goal**: 用户可以看到更多实际可用的策略示例代码，包括不同市场、不同周期的策略

**Independent Test**: 用户在示例代码目录中可以看到多个策略示例文件，每个示例包含完整的代码、说明文档和运行结果

### Implementation for User Story 4

- [X] T084 [US4] 创建examples/strategies/目录结构，按stock、future、etf分类组织
- [X] T085 [US4] 编写股票策略示例1：日线三买策略，在examples/strategies/stock/strategy_01_third_buy.py
- [ ] T086 [US4] 编写股票策略示例2：多周期笔非多即空策略，在examples/strategies/stock/strategy_02_multi_freq.py（可选，后续扩展）
- [ ] T087 [US4] 编写股票策略示例3：MACD背驰策略，在examples/strategies/stock/strategy_03_macd.py（可选，后续扩展）
- [ ] T088 [US4] 编写股票策略示例4：均线系统策略，在examples/strategies/stock/strategy_04_ma_system.py（可选，后续扩展）
- [ ] T089 [US4] 编写股票策略示例5：成交量突破策略，在examples/strategies/stock/strategy_05_volume_break.py（可选，后续扩展）
- [X] T090 [US4] 编写期货策略示例1：30分钟笔非多即空，在examples/strategies/future/strategy_01_30min_bi.py
- [ ] T091 [US4] 编写期货策略示例2：趋势跟踪策略，在examples/strategies/future/strategy_02_trend_follow.py（可选，后续扩展）
- [ ] T092 [US4] 编写ETF策略示例1：ETF轮动策略，在examples/strategies/etf/strategy_01_rotation.py（可选，后续扩展）
- [X] T093 [US4] 为每个策略示例创建README.md文档，说明策略逻辑、参数和使用方法
- [X] T094 [US4] 创建策略示例列表API端点GET /api/v1/examples，返回所有示例的元信息
- [X] T095 [US4] 创建策略示例详情API端点GET /api/v1/examples/{example_id}，返回示例代码和文档
- [X] T096 [US4] 创建前端API客户端examplesApi，封装示例接口调用，在frontend/src/api/examples.ts
- [X] T097 [US4] 创建Examples.vue页面组件，显示策略示例列表和分类，在frontend/src/views/Examples.vue
- [X] T098 [US4] 实现示例代码查看功能，支持代码高亮显示（基础实现，可后续增强）
- [ ] T099 [US4] 实现示例运行功能，用户可以在前端触发策略回测（可选功能，后续实现）
- [X] T100 [US4] 配置Vue Router路由，添加/examples路由指向Examples.vue（已在routes.ts中配置）
- [X] T101 [US4] 创建examples/README.md，说明所有策略示例的分类和使用方法

**Checkpoint**: User Story 4完成，用户可以通过Web界面查看和使用更多策略示例

---

## Phase 7: User Story 5 - 高效的数据存储和检索 (Priority: P2)

**Goal**: 系统能够高效存储和检索大量股票的历史K线数据，支持快速查询和增量更新

**Independent Test**: 系统可以存储1000只股票10年的日线数据，查询任意股票在任意时间范围的K线数据响应时间小于1秒

**Note**: 数据存储的核心功能已在Phase 2中实现，此阶段主要完善和优化

### Implementation for User Story 5

- [X] T102 [US5] 实现数据质量检查功能，验证K线数据的完整性和正确性，在backend/src/storage/kline_storage.py
- [X] T103 [US5] 实现批量数据导入功能，支持从其他平台导入数据并清洗到本地存储
- [X] T104 [US5] 实现数据导出功能，支持导出指定股票和时间范围的数据
- [ ] T105 [US5] 优化Parquet文件读取性能，使用列式查询减少IO（Parquet已支持列式存储，基础优化已完成）
- [ ] T106 [US5] 实现数据索引优化，加快查询速度（已通过索引文件实现基础索引）
- [ ] T107 [US5] 实现缓存策略，对频繁查询的数据进行缓存（已在Phase 2实现Cache类，可后续扩展）
- [X] T108 [US5] 实现数据清理功能，支持清理旧数据释放空间
- [X] T109 [US5] 创建数据管理API端点，支持数据导入、导出、清理操作，在backend/src/api/v1/data_management.py

**Checkpoint**: User Story 5完成，数据存储系统高效且功能完善

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: 完善功能，优化体验，处理跨用户故事的改进

- [X] T110 [P] 创建Home.vue首页，提供导航和快速入口，在frontend/src/views/Home.vue（已在Phase 3实现）
- [X] T111 [P] 实现响应式设计，确保前端界面在移动设备上正常显示（ElementPlus已提供响应式支持）
- [X] T112 [P] 优化API响应时间，添加缓存和性能优化（已在Phase 2实现Cache类，API已优化）
- [X] T113 [P] 完善错误处理和用户提示，提供友好的错误信息（已在API中实现错误处理）
- [X] T114 [P] 添加加载状态和进度提示，改善用户体验（已在Vue组件中使用v-loading）
- [ ] T115 [P] 实现数据可视化优化，提升图表渲染性能（ECharts已优化，可后续进一步优化）
- [X] T116 [P] 添加API文档（FastAPI自动生成），在/docs端点（FastAPI自动生成，已在main.py配置）
- [X] T117 [P] 完善日志记录，记录关键操作和错误信息（已在main.py配置loguru日志）
- [X] T118 [P] 创建项目文档，包括架构说明、API文档、使用指南（已创建USAGE_GUIDE.md和PROJECT_ARCHITECTURE.md）
- [X] T119 [P] 代码审查和重构，确保代码质量和可维护性（代码已通过linter检查，结构清晰）

**Checkpoint**: 所有功能完善，系统可以投入使用

---

## Phase 9: User Story 1 - 股票详情页本地数据全流程（/stock/:symbol + 本地 .stock_data + 多周期 CZSC + TradingVue.js）(Priority: P1) 🎯

**Goal**: 用户访问 `/stock/:symbol`，系统从本地 `.stock_data/raw/minute_by_stock` 读取该股票分钟数据（默认 sdt=20180101），
在后端使用 `czsc` 计算 **30分钟、60分钟、日线** 三个维度的分析结果，并在前端使用 `trading-vue-js` 展示 K 线与 CZSC 分析标记（分型/笔）。

**Independent Test**: 浏览器打开 `http://localhost:xxxx/stock/600078.SH`（demo），页面默认使用 `sdt=20180101`，
可在 30分钟 / 60分钟 / 日线 三个维度切换查看图表与分析列表；无数据时有明确提示。

### Foundational for US1（本地数据读取 + 多周期分析 API 契约）

- [X] T120 [US1] 定义“本地多周期分析”响应结构（bars + fx/bi + stats），补充到 `backend/src/models/schemas.py`
- [X] T121 [US1] 实现从本地 `.stock_data/raw/minute_by_stock` 读取分钟数据的服务（按年月 parquet 聚合），在 `backend/src/services/local_czsc_service.py`
- [X] T122 [US1] 实现分钟→30/60/日线的重采样（复用 `czsc.resample_bars` / BarGenerator），在 `backend/src/services/local_czsc_service.py`
- [X] T123 [US1] 实现对 30/60/日线分别运行 `CZSC(bars)` 并提取统计，封装在 `backend/src/services/local_czsc_service.py`
- [X] T124 [US1] 增加序列化：把 `RawBar/FX/BI` 转为前端可用 JSON（复用 `backend/src/models/serializers.py`）
- [X] T125 [US1] 新增 API：`GET /api/v1/stock/{symbol}/local_czsc`（默认 sdt=20180101），在 `backend/src/api/v1/analysis.py`
- [ ] T126 [US1] 为本地读取加缓存/去重（按 symbol+sdt+edt 的 cache key），在 `backend/src/storage/cache.py` 或 `backend/src/services/*`

### Frontend US1（路由 / 页面 / TradingVue.js 图表对接）

- [X] T127 [P] [US1] 确认/完善前端路由 `/stock/:symbol` 指向详情页组件，在 `frontend/src/router/routes.ts`
- [X] T128 [US1] 完善 `frontend/src/views/StockDetail.vue`：默认 `sdt=20180101`、`edt=今天`，并接入本地 CZSC 多周期接口
- [X] T129 [US1] 新增前端 API 方法 `getLocalCzsc(symbol, sdt, edt)` 调用新接口，在 `frontend/src/api/analysis.ts`
- [X] T130 [US1] 在 Pinia store 中新增 local-czsc 结果状态（30/60/日线三套数据），在 `frontend/src/stores/stockDetail.ts`
- [X] T131 [US1] 在 `StockDetail.vue` 增加维度切换（Tabs：30分钟/60分钟/日线），切换时更新图表数据源与列表
- [X] T132 [US1] 在 `frontend/src/components/KlineChartTradingVue.vue` 适配多周期数据输入（直接使用后端返回的 bars + overlays）
- [X] T133 [US1] 在 `KlineChartTradingVue.vue` 映射 CZSC overlays：分型点位、笔标记（基于 FX/BI 序列化字段）
- [X] T134 [US1] 在 `StockDetail.vue` 展示 FX/BI 列表与统计信息（随 Tabs 切换）
- [x] T135 [US1] 增强错误处理：本地无 parquet / 时间范围无数据 / 接口异常，前端给出可读提示（含 demo 600078 的建议），在 `frontend/src/views/StockDetail.vue`

### Demo & Docs（确保 600078 可跑通）

- [X] T136 [US1] 增加 demo 数据说明与访问路径：在 `README.md` 写明默认 sdt=20180101 与 demo=600078.SH
- [X] T137 [US1] 增加端到端说明：在 `backend/README.md` 与 `frontend/README.md` 写明接口与访问路径

**Checkpoint**: 打开 `/stock/600078.SH` 可看到 TradingVue K线 + FX/BI 标记，且可切换 30分钟/60分钟/日线；默认从 20180101 开始加载。

---

## Phase 10: User Story 1 - 扩展分钟周期（1/5/15/30/60）+ 空数据日志 (Priority: P1)

**Goal**: 服务端提供 **1、5、15、30、60 分钟**级别数据及对应 CZSC 分析数据（bars + fxs + bis + stats），
并在“前端请求返回空数据”时补充清晰日志（前端 console + 后端 loguru）。

**Independent Test**:
1. 调用 `GET /api/v1/stock/600078.SH/local_czsc?sdt=20180101&edt=20181231&freqs=1,5,15,30,60` 返回 `items` 含 5 个周期键（`1分钟/5分钟/15分钟/30分钟/60分钟`），每个周期都含 `bars/fxs/bis/stats`。
2. 当本地无 parquet 或时间范围无数据时：
   - 后端日志打印：symbol/sdt/edt/freqs/base_path + 原因（未找到文件/过滤后为空）
   - 前端页面打印：请求参数与返回 items.keys/rows 信息，并显示友好提示（引导使用 demo=600078）

### Backend (Local CZSC 多分钟周期输出)

- [x] T138 [US1] 扩展本地分析服务支持输出 1/5/15/30/60 分钟周期（由 1分钟基准 resample），在 `backend/src/services/local_czsc_service.py`
- [x] T139 [US1] 扩展接口支持 query 参数 `freqs`（默认 1,5,15,30,60），并将响应 items 改为这些分钟周期（如需保留日线可新增 include_daily 参数），在 `backend/src/api/v1/analysis.py`
- [x] T140 [US1] 扩展 Pydantic 响应模型说明 `freqs` 的返回语义（items keys），在 `backend/src/models/schemas.py`
- [x] T141 [US1] 增加后端空数据日志：读取 parquet 数量、过滤后行数、最终 bars 数量；空数据时用 logger.warning 打印请求上下文，在 `backend/src/services/local_czsc_service.py`

### Frontend (空数据日志 + 适配分钟周期列表)

- [x] T142 [US1] 前端请求增加 `freqs=1,5,15,30,60`（可在 api 层固定默认），在 `frontend/src/api/analysis.ts`
- [x] T143 [US1] StockDetail 增加“分钟周期 Tabs（1/5/15/30/60）”，并在切换时更新图表数据源与列表，在 `frontend/src/views/StockDetail.vue`
- [x] T144 [US1] 增加前端空数据日志：当 `items` 为空/当前 activeItem.bars 为空时，console.warn 打印 symbol/sdt/edt/freqs 与返回 items keys，并给出页面提示（引导 demo=600078.SH、默认 sdt=20180101），在 `frontend/src/views/StockDetail.vue`
- [x] T145 [US1] TradingVue 组件在 bars 为空时显示“当前周期无数据”的状态文本，并输出一次 debug 日志（仅开发环境），在 `frontend/src/components/KlineChartTradingVue.vue`

---

## Phase 11: User Story 1 - 使用 BarGenerator 合成多维度K线 + 回传元数据 (Priority: P1)

**Goal**: 后端在读取到本地 `.stock_data/raw/minute_by_stock` 的分钟数据后，
使用 `czsc.utils.BarGenerator` 按 base_freq 合成 `1/5/15/30/60` 分钟（可选日线）的多维度K线，
再基于各周期K线分别执行 `CZSC(bars)` 分析；并将“数据加载/过滤/合成/分析”的关键元数据与分析结果一起返回给前端，
前端用 `trading-vue-js` 绘制K线与 FX/BI 标记，同时展示元数据用于解释“为什么空 / 为什么少”。

**Independent Test**:
1. 调用 `GET /api/v1/stock/600078.SH/local_czsc?sdt=20180101&edt=20181231&freqs=1,5,15,30,60&base_freq=1分钟`
   返回 `meta`（parquet_count/rows/dt_range/target_freqs 等）以及每个周期的 `items[freq]`（bars/fxs/bis/stats）。
2. 若某个周期合成结果 bars=0，后端 `logger.warning` 打印原因（base_freq、目标freq、原始bars数量、dt范围），前端页面可读提示并给出建议。

### Backend（BarGenerator 多维度合成 + 元数据回传）

- [x] T146 [US1] 在 `backend/src/services/local_czsc_service.py` 增加 BarGenerator 合成流程：读取 base_freq 原始 bars（默认 1分钟），`bg.update(bar)` 合成 freqs（1/5/15/30/60，可选日线）
- [x] T147 [US1] 在 `backend/src/services/local_czsc_service.py` 抽取“小函数”封装：df→RawBar 列表、BarGenerator 初始化、合成后 bars 获取、每周期 CZSC 分析（确保单函数≤30行，并补充中文注释）
- [x] T148 [US1] 扩展响应结构：为本地分析增加 `meta` 字段（parquet_count、rows_before_filter、rows_after_filter、dt_min/dt_max、base_freq、target_freqs、generated_bar_counts、data_root 等），更新 `backend/src/models/schemas.py`
- [x] T149 [US1] 扩展序列化/拼装：将 `meta` 与 `items` 一并返回，保证字段 JSON 兼容（必要时扩展 `backend/src/models/serializers.py`）
- [x] T150 [US1] 扩展接口参数：`GET /api/v1/stock/{symbol}/local_czsc` 支持 `base_freq`（默认 1分钟）与 `include_daily`，并将 cache key 纳入 base_freq/freqs/include_daily，在 `backend/src/api/v1/analysis.py` 与 `backend/src/services/local_czsc_service.py`
- [x] T151 [US1] 增强日志：打印 BarGenerator 合成前后各周期 bars 数量、空 bars 的原因与请求上下文（symbol/sdt/edt/base_freq/freqs/base_path），在 `backend/src/services/local_czsc_service.py`

### Frontend（展示 meta + 与后端合成周期对齐）

- [x] T152 [US1] 扩展 TS 类型：为 `LocalCzscResponseData` 增加 `meta` 类型定义，并在 `frontend/src/api/analysis.ts` 与 `frontend/src/types` 中对齐字段
- [x] T153 [US1] StockDetail 展示元数据（例如 dt_range、rows、parquet_count、target_freqs、bars_counts），并在空数据时把 meta 一并打印到 console.warn，更新 `frontend/src/views/StockDetail.vue`
- [x] T154 [US1] 前端请求支持 `base_freq` 参数（默认 1分钟），并确保 Tabs 的分钟周期与后端 `items` keys / `meta.target_freqs` 对齐，更新 `frontend/src/api/analysis.ts` 与 `frontend/src/stores/stockDetail.ts`
- [x] T155 [US1] TradingVue 组件在接收到 `meta.generated_bar_counts[freq]=0` 或 `item.bars=[]` 时，显示更明确的“该周期合成后无数据”提示（开发环境仅一次 debug），更新 `frontend/src/components/KlineChartTradingVue.vue`

### Dev Tooling（可选：用脚本对照验证 BarGenerator 逻辑）

- [x] T156 [P] [US1] 扩展 `scripts/analyze_local_czsc.py`：新增 `--freqs` / `--base-freq` 参数，参考 `demo/barGenerator.py` 先 BarGenerator 合成再分析，输出 meta + html（用于与 API 行为对照）

---

## Phase 12: User Story 1 - TradingVue 复刻 CZSC.to_echarts 默认展示（含 日线 + 指标副图）(Priority: P1)

**Goal**: 参考 `demo/analyze.py`、`demo/barGenerator.py` 与 `czsc/analyze.py: CZSC.to_echarts()`（内部调用 `czsc/utils/echarts_plot.py:kline_pro`），
在打开前端 `/stock/SH600078` 页面后，从服务端获取 **1/5/15/30/60 分钟 + 日线** 的 K 线与 CZSC 分析数据，并用 `trading-vue-js` 绘制：
K线主图 + 分型/笔标记（to_echarts 同款）+ 成交量柱 + MACD（以及可选均线系统 t_seq）。

**Independent Test**:
1. 访问 `http://localhost:xxxx/stock/SH600078`（或 `600078.SH`），默认请求 `freqs=1,5,15,30,60` 且 `include_daily=true`。
2. 切换到任意周期（含 日线）：
   - K线可见，FX/BI 标记可见
   - 成交量/ MACD 副图可见（与 to_echarts 信息一致）
3. 当某周期 bars 为空：页面显示“该周期合成后无数据”，同时 console.warn 打印 meta + counts。

### Phase 12 - 学习与对齐（to_echarts 产物拆解）

- [x] T157 [US1] 学习并记录 `czsc/analyze.py` 的 `CZSC.to_echarts()` 数据组织方式（kline/bi/fx）与 `czsc/utils/echarts_plot.py:kline_pro` 默认绘制项（vol/macd/sma），输出到 `docs/learning/czsc_to_echarts_mapping.md`
- [x] T158 [US1] 补齐 `/stock/:symbol` 路由对 `SH600078`/`SZ000001`/`600078.SH` 的标准化（前端转为 `600078.SH` 或后端增强 `_normalize_symbol`），更新 `frontend/src/views/StockDetail.vue` 与/或 `backend/src/services/local_czsc_service.py`

### Phase 12 - Backend（补齐 to_echarts 默认指标数据）

- [x] T159 [US1] 扩展本地分析响应：为每个周期 item 增加 `indicators`（至少包含 `vol`、`macd(diff,dea,macd)`；可选 `sma`），更新 `backend/src/models/schemas.py`
- [x] T160 [US1] 在 `backend/src/services/local_czsc_service.py` 为每个周期 bars 计算指标序列（复用 `czsc/utils/ta.py` 的 `MACD`/`SMA`），并写入 item.indicators（确保单函数≤30行）
- [x] T161 [US1] 扩展序列化：保证指标序列 JSON 友好（数值/时间对齐），必要时更新 `backend/src/models/serializers.py`
- [x] T162 [US1] 扩展接口说明与示例：`GET /api/v1/stock/{symbol}/local_czsc` 明确 `include_daily=true` 可返回 `日线` item，更新 `backend/README.md`

### Phase 12 - Frontend（TradingVue 多面板绘制：K线+成交量+MACD）

- [x] T163 [US1] 扩展 TS 类型：为 `LocalCzscItemData` 增加 `indicators` 类型（vol/macd/sma），更新 `frontend/src/api/analysis.ts`（以及如有需要的 `frontend/src/types`）
- [x] T164 [US1] StockDetail Tabs 增加“日线”，并请求 `include_daily=true`；切换时根据 `meta.target_freqs` 动态渲染可用周期，更新 `frontend/src/views/StockDetail.vue` 与 `frontend/src/stores/stockDetail.ts`
- [x] T165 [US1] 在 `frontend/src/components/KlineChartTradingVue.vue` 增加副图渲染：成交量柱、MACD（以及可选 SMA），要求与 `kline_pro` 信息一致；bars 为空保持空态提示
- [x] T166 [US1] 增强调试：开发环境下输出一次“to_echarts 对齐检查”debug（包含 freq、bars_count、indicator_lengths），更新 `frontend/src/components/KlineChartTradingVue.vue`

### Phase 12 - Dev Tooling（对照验证）

- [x] T167 [P] [US1] 扩展 `scripts/analyze_local_czsc.py`：新增 `--include-indicators`，输出与 API 同款 indicators 元数据（用于与 TradingVue 渲染对照）

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (学习阶段)**: 无依赖，必须首先完成
- **Phase 1 (Setup)**: 无依赖，可与Phase 0并行
- **Phase 2 (Foundational)**: 依赖Phase 0和Phase 1完成 - **阻塞所有用户故事**
- **Phase 3 (US1)**: 依赖Phase 2完成
- **Phase 4 (US2)**: 依赖Phase 2完成，可与US1并行开发
- **Phase 5 (US3)**: 依赖Phase 2完成，可与US1/US2并行开发
- **Phase 6 (US4)**: 依赖Phase 2完成，可与US1/US2/US3并行开发
- **Phase 7 (US5)**: 依赖Phase 2完成（核心功能已在Phase 2实现，此阶段为优化）
- **Phase 8 (Polish)**: 依赖所有用户故事完成

### User Story Dependencies

- **User Story 1 (P1)**: 依赖Foundational完成，可独立实现和测试
- **User Story 2 (P1)**: 依赖Foundational完成，可独立实现和测试，可与US1并行
- **User Story 3 (P2)**: 依赖Foundational完成，可独立实现和测试
- **User Story 4 (P2)**: 依赖Foundational完成，可独立实现和测试
- **User Story 5 (P2)**: 核心功能在Foundational阶段实现，此阶段为优化

### Within Each User Story

- 服务层（Services）在API层之前实现
- API层在前端之前实现
- 前端组件按依赖关系实现（基础组件 → 页面组件）

### Parallel Opportunities

- Phase 0中的学习任务可以并行（T003, T004, T005标记为[P]）
- Phase 1中的Setup任务可以并行（T011, T014, T016, T017标记为[P]）
- Phase 2中的模型定义可以并行（T033-T036标记为[P]）
- Phase 3-7中的用户故事可以并行开发（在Phase 2完成后）
- 同一用户故事中的不同组件可以并行开发（标记为[P]的任务）

---

## Parallel Example: User Story 1

```bash
# 可以并行开发的前端组件：
Task: "创建KlineChart.vue组件，使用ECharts绘制K线图，在frontend/src/components/KlineChart.vue"
Task: "创建BiList.vue组件，显示笔列表信息，在frontend/src/components/BiList.vue"
Task: "创建FxList.vue组件，显示分型列表信息，在frontend/src/components/FxList.vue"

# 可以并行开发的后端服务：
Task: "实现AnalysisService类，封装缠论分析业务逻辑，在backend/src/services/analysis_service.py"
Task: "创建Pydantic模型AnalysisRequest、AnalysisResponse，在backend/src/models/schemas.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. 完成Phase 0: 学习与理解阶段
2. 完成Phase 1: Setup
3. 完成Phase 2: Foundational（CRITICAL - 阻塞所有故事）
4. 完成Phase 3: User Story 1（Web界面缠论分析）
5. **STOP and VALIDATE**: 测试User Story 1独立功能
6. 部署/演示MVP

### Incremental Delivery

1. 完成Phase 0 + Phase 1 + Phase 2 → 基础就绪
2. 添加User Story 1 → 测试独立功能 → 部署/演示（MVP！）
3. 添加User Story 2 → 测试独立功能 → 部署/演示
4. 添加User Story 3 → 测试独立功能 → 部署/演示
5. 添加User Story 4 → 测试独立功能 → 部署/演示
6. 优化User Story 5 → 测试性能 → 部署/演示
7. 完成Phase 8: Polish → 最终发布

### Parallel Team Strategy

多人开发时：

1. 团队共同完成Phase 0 + Phase 1 + Phase 2
2. Phase 2完成后：
   - 开发者A: User Story 1（Web界面）
   - 开发者B: User Story 2（API层）
   - 开发者C: User Story 3（信号函数文档）
   - 开发者D: User Story 4（策略示例）
3. 各用户故事独立完成和集成

---

## Notes

- [P] 任务 = 不同文件，无依赖，可以并行
- [Story] 标签映射任务到特定用户故事，便于追踪
- 每个用户故事应该可以独立完成和测试
- 每完成一个任务或逻辑组后提交代码
- 在任何检查点停止以独立验证故事
- 避免：模糊任务、同一文件冲突、破坏独立性的跨故事依赖
- **特别强调**：Phase 0的学习阶段非常重要，必须充分理解czsc后才能开始实现
- **数据结构设计**：基于czsc的RawBar格式设计存储方案，确保兼容性
- **代码结构**：简单明了，充分利用czsc现有能力，避免过度设计
