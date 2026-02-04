# Tasks: 本地股票分钟数据维护与质量检查（Python + MySQL）

**Input**: 设计文档来自 `/specs/001-czsc-api-ui/plan.md` 与 `/specs/001-czsc-api-ui/spec.md`  
**Scope Hint**: 本任务清单聚焦“分钟级数据维护（完整性/中文名/起止时间）”，对应 `spec.md` 的 US2（股票列表与API）与 US5（数据存储与质量）  
**Tests**: spec 未要求 TDD，本清单不强制加入测试任务（如需可在实现阶段补充）  
**Path Conventions**: 后端 `backend/src/`，脚本 `scripts/`，文档 `docs/`  

## 任务格式（严格）

每条任务必须严格符合：`- [ ] T001 [P] [US?] 描述（包含文件路径）`

- **[P]**：可并行（不同文件/无未完成依赖）
- **[US?]**：仅用户故事阶段任务需要（[US1]..[US5]）

---

## Phase 1: Setup（共享基础设施）

- [X] T001 创建数据维护文档入口与约定说明在 docs/instructions/stock_minute_data_maintenance.md
- [X] T002 [P] 补齐后端配置读取（MySQL连接、表名、时区、交易时段）在 backend/src/utils/settings.py
- [X] T003 [P] 补齐后端依赖声明（SQLAlchemy + MySQL Driver）在 backend/requirements.txt
- [X] T004 [P] 增加数据维护脚本入口说明与示例参数在 scripts/README.md

---

## Phase 2: Foundational（阻塞所有用户故事的基础）

**⚠️ CRITICAL**：完成本阶段后，US1~US5 才能并行推进。

- [X] T005 实现 MySQL 数据库连接与会话管理（engine/session/依赖注入）在 backend/src/storage/mysql_db.py
- [X] T006 [P] 定义“股票主数据/分钟数据覆盖率/分钟日统计/缺口明细”表结构（SQLAlchemy ORM）在 backend/src/models/mysql_models.py
- [X] T007 编写初始化/升级表结构的脚本（幂等创建 + 版本标记）在 scripts/db_init_mysql.py
- [X] T008 [P] 实现股票主数据仓储（增删改查、批量 upsert）在 backend/src/storage/stock_basic_repo.py
- [X] T009 [P] 实现分钟K线仓储（查询起止时间、按日统计条数、按分钟补齐检查所需查询）在 backend/src/storage/minute_bar_repo.py
- [X] T010 [P] 实现交易日历与交易时段工具（交易日列表、期望分钟数计算、午休切分）在 backend/src/utils/trading_calendar.py
- [X] T011 实现数据覆盖率/缺口计算的公共数据结构（Pydantic schema）在 backend/src/models/schemas_data_quality.py
- [X] T012 将数据质量 schemas 统一导出并在 backend/src/models/__init__.py 中暴露
- [X] T013 实现“数据质量计算核心算法（按日完整性/缺口区间/汇总指标）”在 backend/src/services/data_quality_core.py
- [X] T014 在 backend/src/main.py 中挂载数据质量相关路由（后续 US2/US5 会实现具体 router 文件）于 backend/src/api/v1/data_quality.py

---

## Phase 3: User Story 1 - 通过Web界面进行缠论分析（Priority: P1）🎯 MVP

**Goal**: Web界面分析能力可用，并能友好提示“本地分钟数据不足/缺失”的原因  
**Independent Test**: 前端分析页面在输入 `000001.SZ` 和时间范围后，若数据不足能展示“可用范围（start/end）+ 缺口摘要”

- [X] T015 [P] [US1] 在后端分析响应中增加可选的“数据可用范围/缺口摘要”字段（不影响原接口）在 backend/src/models/schemas.py
- [X] T016 [US1] 在分析服务中按 symbol/freq 查询本地数据起止时间并回填摘要在 backend/src/services/analysis_service.py
- [X] T017 [P] [US1] 前端分析页面增加“数据可用范围与缺口提示”展示在 frontend/src/views/Analysis.vue

---

## Phase 4: User Story 2 - 通过API获取股票数据和信号（Priority: P1）

**Goal**: 能通过 API 获取股票中文名、市场、以及本地分钟数据起止时间/覆盖概况  
**Independent Test**:
- 调用 `GET /api/v1/symbols?with_name=true` 返回 symbol + 中文名  
- 调用 `GET /api/v1/symbols/coverage` 返回每只股票分钟数据的 start_dt/end_dt/coverage_ratio

- [X] T018 [P] [US2] 新增 symbols 扩展响应模型（含 name/market/list_date 等）在 backend/src/models/schemas.py
- [X] T019 [US2] 实现“股票列表 + 中文名”查询服务（从 MySQL stock_basic 表）在 backend/src/services/symbol_service.py
- [X] T020 [US2] 实现“股票分钟覆盖概况列表”服务（从 coverage 表/或实时汇总）在 backend/src/services/data_quality_service.py
- [X] T021 [US2] 实现 API：`GET /api/v1/symbols`（支持 with_name/group/market）在 backend/src/api/v1/symbols.py
- [X] T022 [US2] 实现 API：`GET /api/v1/symbols/coverage`（分页/排序）在 backend/src/api/v1/data_quality.py
- [X] T023 [P] [US2] 前端 symbols 下拉选择器支持展示“代码 + 中文名”在 frontend/src/components/SymbolSelect.vue
- [X] T024 [P] [US2] 前端 API 客户端补齐 symbols 与 coverage 调用在 frontend/src/api/symbols.ts

---

## Phase 5: User Story 3 - 查看和学习信号函数文档（Priority: P2）

**Goal**: 文档页提供“信号函数需要的最小数据粒度建议”，指导用户维护分钟数据  
**Independent Test**: 文档页中对常用信号展示“建议数据频率/回看长度（bars 数）”

- [X] T025 [P] [US3] 为信号文档响应增加可选字段 data_requirements（freq/needed_bars）在 backend/src/models/schemas.py
- [X] T026 [US3] 在文档服务中为信号函数标注经验性数据需求（不精确但可用）在 backend/src/services/doc_service.py
- [X] T027 [P] [US3] 前端信号文档卡片展示 data_requirements 在 frontend/src/components/SignalCard.vue

---

## Phase 6: User Story 4 - 使用更多策略示例（Priority: P2）

**Goal**: 提供“分钟数据质量检查与修复建议”的示例脚本  
**Independent Test**: 用户运行示例脚本可生成缺口报告 CSV（按 symbol/day）

- [X] T028 [P] [US4] 新增示例：生成分钟缺口报告并导出 CSV 在 examples/data_quality/minute_gap_report.py
- [X] T029 [P] [US4] 新增示例文档：如何用报告指导补数与回填在 examples/data_quality/README.md

---

## Phase 7: User Story 5 - 高效的数据存储和检索（Priority: P2）🎯 数据维护核心

**Goal**: 你能清晰知道“本地分钟数据是否完整、每只股票中文名、每只股票分钟数据开始/结束时间”，并可持续维护（增量更新+质量检查）  
**Independent Test**:
- 运行 `python scripts/stock_minute_scan.py --market SH,SZ --freq 1m` 后，MySQL 中 coverage 表能看到每只股票 start_dt/end_dt/coverage_ratio
- 运行 `python scripts/stock_minute_check.py --symbol 000001.SZ --date 2024-01-04` 后能输出缺口分钟区间

### 7.1 股票中文名与主数据维护（建议：以 MySQL 为准）

- [X] T030 [P] [US5] 定义股票主数据导入格式（CSV列：symbol,name,market,list_date,delist_date）并写入说明在 docs/instructions/stock_basic_import.md
- [X] T031 [US5] 实现 CSV 导入/更新股票主数据（upsert）脚本在 scripts/stock_basic_import.py
- [X] T032 [US5] 实现“从现有分钟表中反推 symbol 列表并补齐 market”脚本在 scripts/stock_basic_from_minute_table.py

### 7.2 起止时间与覆盖率（全市场扫描）

- [X] T033 [US5] 实现“扫描所有股票分钟数据起止时间（min(dt)/max(dt)）”并写入 coverage 表在 scripts/stock_minute_scan.py
- [X] T034 [US5] 实现“按交易日聚合分钟条数（actual_count）”并写入 daily_stats 表在 scripts/stock_minute_scan_daily.py
- [X] T035 [US5] 实现“按日完整性校验（expected_count vs actual_count）+ 缺口区间定位”并写入 gaps 表在 scripts/stock_minute_check.py
- [X] T036 [P] [US5] 在服务层封装 coverage/daily/gaps 查询（供 API 调用）在 backend/src/services/data_quality_service.py

### 7.3 API：查询覆盖率、缺口与建议

- [X] T037 [US5] 实现 API：`GET /api/v1/data/coverage`（symbol 可选；返回 start/end/ratio）在 backend/src/api/v1/data_quality.py
- [X] T038 [US5] 实现 API：`GET /api/v1/data/gaps`（symbol+date；返回缺口区间）在 backend/src/api/v1/data_quality.py
- [X] T039 [P] [US5] 前端新增“数据质量”页面（列表 + 详情缺口）在 frontend/src/views/DataQuality.vue
- [X] T040 [P] [US5] 前端增加 API 客户端 data_quality.ts（coverage/gaps）在 frontend/src/api/data_quality.ts
- [X] T041 [P] [US5] 前端路由加入 `/data-quality` 在 frontend/src/router/routes.ts

### 7.4 维护策略：增量更新与定时任务（不强绑定外部数据源）

- [X] T042 [US5] 定义增量维护流程（每日：扫描新增数据→计算覆盖→输出缺口→人工/外部补数→复查）在 docs/instructions/stock_minute_data_maintenance.md
- [X] T043 [P] [US5] 提供一个“定时运行入口”示例（cron/Windows任务计划）文档在 docs/instructions/cron_examples.md
- [X] T044 [US5] 增加一个统一的 CLI 入口（scan/check/report）并输出到 logs（loguru）在 scripts/stock_minute_cli.py

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T045 [P] 补齐错误码与统一异常返回（DB连接失败/表不存在/参数非法）在 backend/src/utils/errors.py
- [X] T046 [P] 在数据质量服务中增加关键日志与耗时统计（按 symbol/日期）在 backend/src/services/data_quality_service.py
- [X] T047 [P] 补齐用户指南：如何通过 API/页面查看 start/end 与缺口在 docs/instructions/stock_minute_data_maintenance.md

---

## 附：脚本使用文档补全任务清单

如果你想把“脚本怎么用 / 每个脚本干什么 / 常见报错怎么排查”完整整理成可运行的文档，请按以下任务清单推进：

- 任务清单：`specs/001-czsc-api-ui/tasks_docs_scripts.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**：无依赖，可立即开始  
- **Phase 2 (Foundational)**：依赖 Phase 1 完成，**阻塞所有 US**  
- **US1~US5**：均依赖 Phase 2 完成；其中 **US2 与 US5** 可并行推进  
- **Polish (Phase 8)**：依赖核心 US 完成后再做  

### User Story Dependencies（建议）

- **US5（数据维护）**：与 US2 强相关；建议优先把“stock_basic + coverage”做成可用 MVP  
- **US2（API）**：依赖 US5 的数据表与服务，但可先实现空实现/占位返回  
- **US1（分析页）**：可独立推进；若要给出“可用范围/缺口提示”，需要 US5 的 coverage 查询能力  

---

## Parallel Opportunities（示例）

- Setup 中 `T002/T003/T004` 可并行  
- Foundational 中 `T006/T008/T009/T010/T011` 可并行（不同文件）  
- US2 前端与后端可并行（`T021/T022` 与 `T023/T024`）  
- US5 脚本与 API/前端可并行（脚本先跑通，再接 API/页面展示）  

---

## Parallel Example: US5（数据维护核心）

```bash
# 并行 1：先把数据落库（脚本）与查询接口（API）分开推进
Task: "实现起止时间扫描并写入 coverage 表在 scripts/stock_minute_scan.py"
Task: "实现 API：GET /api/v1/data/coverage 在 backend/src/api/v1/data_quality.py"

# 并行 2：主数据导入与覆盖率算法可并行
Task: "实现 CSV 导入股票中文名脚本在 scripts/stock_basic_import.py"
Task: "实现按日完整性校验核心算法在 backend/src/services/data_quality_core.py"
```

---

## Implementation Strategy（建议 MVP）

- **MVP**：先完成 `Phase 1~2 + US5(7.1~7.3 的 coverage/gaps)`，你就能拿到“中文名 + 起止时间 + 缺口”三件事  
- **增量**：再补 US2 的 symbols/coverage API 与前端页面，最后把提示嵌入 US1 分析页  
