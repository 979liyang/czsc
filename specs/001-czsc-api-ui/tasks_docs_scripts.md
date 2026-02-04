# Tasks: 脚本与文档使用说明补全（环境变量 / MySQL / 数据采集 / 本地分析）

**Input**: `/specs/001-czsc-api-ui/plan.md` 与 `/specs/001-czsc-api-ui/spec.md`  
**Scope**: 产出“能直接照着跑”的文档与脚本说明，覆盖 `.env`、MySQL 初始化、Tushare 分钟采集、`.stock_data` 本地分析与前后端联调  
**Tests**: spec 未要求 TDD，本清单不强制加入测试任务  
**Path Conventions**: 文档 `docs/`，脚本 `scripts/`，后端 `backend/`，前端 `frontend/`

## 任务格式（严格）

每条任务必须严格符合：`- [ ] T001 [P] [US?] 描述（包含文件路径）`

- **[P]**：可并行（不同文件/无未完成依赖）
- **[US?]**：仅用户故事阶段任务需要（[US1]..[US5]）

---

## Phase 1: Setup（文档骨架与约定）

- [ ] T001 创建脚本文档目录与索引页在 docs/usage/README.md
- [ ] T002 [P] 增加根目录快速开始入口链接到 docs/usage/README.md（更新 README.md）
- [ ] T003 [P] 增加环境变量示例文件（不包含真实密钥）在 .env.example
- [ ] T004 [P] 在 scripts/README.md 增加“脚本分类导航 + 统一约定（--help / loguru / 输出目录）”

---

## Phase 2: Foundational（阻塞所有文档可用性的前置）

**⚠️ CRITICAL**：完成本阶段后，US1/US2/US5 的文档才能互相引用且不冲突。

- [ ] T005 编写“环境与依赖安装”指南（venv/requirements/node）在 docs/usage/setup.md
- [ ] T006 编写“.env 与配置读取规则”说明（CZSC_ 前缀、读取顺序、常见误区）在 docs/usage/env.md
- [ ] T007 编写“MySQL 初始化与连接排错”说明（1045/1049/连不上/权限）在 docs/usage/mysql.md

**Checkpoint**：新用户只看 Phase 1~2 就能完成本地环境准备

---

## Phase 3: User Story 5 - 高效的数据存储和检索（Priority: P2）🎯 文档闭环核心

**Goal**: 用户能理解 `.stock_data` 数据目录结构，知道每个“数据采集/扫描/校验/导出”脚本的作用与使用方式  
**Independent Test**: 用户按文档执行后能得到：目录结构创建成功、分钟数据落盘路径正确、能跑一次扫描/校验命令并看到日志输出

- [ ] T008 [US5] 编写“.stock_data 目录结构与分区规范”文档（minute_by_stock/minute_by_date 等）在 docs/usage/storage_layout.md
- [ ] T009 [P] [US5] 为 scripts/setup_storage_dirs.py 补充 README 使用说明与输出示例（更新 scripts/README.md）
- [ ] T010 [US5] 为分钟数据质量维护 CLI 写使用说明（scan/daily/check）在 docs/usage/minute_data_maintenance.md（对应 scripts/stock_minute_cli.py）
- [ ] T011 [P] [US5] 为 scripts/stock_minute_scan.py / scripts/stock_minute_scan_daily.py / scripts/stock_minute_check.py 增加“各自职责 + 示例命令 + 常见耗时说明”（更新 scripts/README.md）
- [ ] T012 [US5] 为 scripts/stock_basic_import.py / scripts/stock_basic_from_minute_table.py 写“股票主数据维护”说明（中文名/market 推断/用法）在 docs/usage/stock_basic.md
- [ ] T013 [US5] 为 scripts/db_init_mysql.py 写“建库建表流程 + 自动建库行为 + 注意事项”在 docs/usage/mysql.md（补充章节）

---

## Phase 4: User Story 2 - 通过API获取股票数据和信号（Priority: P1）

**Goal**: 开发者能按文档启动后端，并调用关键接口验证数据链路正常（特别是本地 `.stock_data` 的 `local_czsc`）  
**Independent Test**: 按文档在浏览器/命令行能成功调用 `GET /api/v1/stock/{symbol}/local_czsc` 并理解返回的 `meta/items/indicators`

- [ ] T014 [US2] 更新 backend/README.md 增加“本地分析接口 local_czsc 完整示例（含 freqs/include_daily/base_freq）”
- [ ] T015 [US2] 编写“后端启动与接口自测（curl/httpie）”文档在 docs/usage/backend_api.md
- [ ] T016 [US2] 编写“local_czsc 返回字段说明”文档（bars/fxs/bis/indicators/meta）在 docs/usage/local_czsc_response.md
- [ ] T017 [P] [US2] 为 scripts/analyze_local_czsc.py 写“用脚本对照 API 输出”的说明（作为排障手段）在 docs/usage/analyze_local_czsc.md

---

## Phase 5: User Story 1 - 通过Web界面进行缠论分析（Priority: P1）🎯 MVP 文档

**Goal**: 用户能按文档启动前后端，打开 `/stock/:symbol` 页面查看 TradingVue 图表与多周期结果  
**Independent Test**: 用户能打开 `http://localhost:5173/stock/600078.SH` 并看到页面不报错；若无数据，能看到“无数据原因/元信息”说明

- [ ] T018 [US1] 编写“前端启动与路由使用（/stock/:symbol）”文档在 docs/usage/frontend_ui.md
- [ ] T019 [US1] 在 docs/usage/frontend_ui.md 中加入“空数据排障”章节（结合后端 meta、前端控制台提示）
- [ ] T020 [US1] 更新根目录 README.md 增加“一键跑通 Demo：600078.SH（默认 sdt=20180101）”步骤

---

## Phase 6: 数据采集（支撑 US5/US1/US2 的前置材料）

**Goal**: 用户能从 Tushare 采集分钟数据到 `.stock_data/raw/minute_by_stock`，支持断点续跑  
**Independent Test**: 用户能用 `--limit 10` 拉一小批数据，且能用 `--resume-after` / `--checkpoint` 续跑

- [ ] T021 编写“Tushare token 设置与安全建议（不要提交到 git）”文档在 docs/usage/tushare.md（覆盖 scripts/set_token.py 的做法）
- [ ] T022 编写“分钟采集脚本（stk_mins）使用说明”文档在 docs/usage/fetch_stk_mins.md（覆盖 scripts/fetch_tushare_minute_data_stk_mins.py）
- [ ] T023 [P] 更新 scripts/README.md 增加采集脚本对照表（fetch_tushare_minute_data_stk_mins*.py / fetch_stock_data.py / fetch_tushare_minute_data.py）与适用场景

---

## Phase 7: Polish & Cross-Cutting Concerns（收口）

- [ ] T024 [P] 为所有新增文档加上“常见错误速查表”（参数拼写、日期格式、路径不存在、无权限、数据库错误）在 docs/usage/README.md
- [ ] T025 [P] 在 docs/usage/README.md 增加“我该先看哪篇文档？”的决策树（按目标：采集/分析/跑页面/排障）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**：无依赖，可立即开始  
- **Phase 2 (Foundational)**：依赖 Phase 1 完成，**阻塞后续所有文档**  
- **US5/US2/US1**：均依赖 Phase 2；建议优先 US5（数据与存储），再 US2（API），最后 US1（UI）  
- **Phase 6（采集）**：可在 Phase 2 后并行推进；但建议在 US5 文档完成后再补齐采集与目录规范的交叉引用  
- **Polish**：最后做

### Parallel Opportunities

- Phase 1 的 `T002/T003/T004` 可并行  
- Phase 2 的 `T005/T006/T007` 可并行（不同文件）  
- US5 中 `T009/T011` 可并行（同在 scripts/README.md 时避免冲突，建议分段再合并）  
- US2 中 `T015/T016/T017` 可并行（不同文档文件）  
- Phase 6 中 `T021/T022/T023` 可并行（不同文件）

---

## Parallel Example: Phase 2（Foundational）

```bash
Task: "编写环境与依赖安装指南在 docs/usage/setup.md"
Task: "编写 .env 与配置读取规则说明在 docs/usage/env.md"
Task: "编写 MySQL 初始化与连接排错说明在 docs/usage/mysql.md"
```

