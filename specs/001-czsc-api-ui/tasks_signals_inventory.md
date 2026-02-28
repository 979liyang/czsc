# Tasks: 学习整理全部信号 czsc.signals 并入库

**Input**: 用户需求「学习整理全部信号 czsc.signals 并入库」  
**Prerequisites**: plan.md（技术栈与目录结构）, 现有 backend 与 czsc 库  
**Path Conventions**: 后端 `backend/src/`，czsc 库 `czsc/signals/`，文档 `czsc_api/czsc.signals/`

**Organization**: 按阶段组织，本需求为单一用户故事（信号学习整理并入库）。

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 可并行（不同文件、无未完成依赖）
- **[Story]**: 本特性仅一个用户故事 [US1]
- 描述中需包含具体文件路径

---

## Phase 1: Setup（准备）

**Purpose**: 确认信号来源与入库目标就绪。

- [X] T001 确认 czsc.signals 可被后端导入：在 `backend/` 或项目根运行 `from czsc.signals import ...` 或通过 `czsc.utils.import_by_name('czsc.signals')` 可加载，且 `backend/src/services/doc_service.py` 中 DocService 使用 signals_module='czsc.signals' 能正常 get_all_signals（`backend/src/services/doc_service.py`、项目环境）
- [X] T002 确认 signal_func 表已存在：运行 `python scripts/db_init_mysql.py` 后 MySQL 中存在 `signal_func` 表（字段含 name、module_path、category、param_template、description、is_active），与 `backend/src/models/mysql_models.py` 中 SignalFunc 一致（`backend/src/models/mysql_models.py`、`scripts/db_init_mysql.py`）

---

## Phase 2: Foundational（阻塞性前置）

**Purpose**: 提供“从 czsc.signals 枚举 → 写入 signal_func 表”的复用能力。

- [X] T003 实现 signal_func 仓储层：在 `backend/src/storage/` 下新增 `signal_func_repo.py`，提供 list_all、get_by_name、upsert（以 name 为唯一键，存在则更新 module_path/category/param_template/description/updated_at，不存在则 insert），供同步脚本调用（`backend/src/storage/signal_func_repo.py`）
- [X] T004 从 DocService 生成 signal_func 行数据：在 `backend/src/services/doc_service.py` 或新建 `backend/src/services/signal_sync_service.py` 中提供方法，调用 DocService.get_all_signals()，将每条 signal 转为 SignalFunc 所需字段（name、module_path 取 full_name 的模块部分、category、param_template 从 params 中取「参数模板」或首条 Signal 模板、description 取 description 字段），返回 List[Dict] 或可 upsert 的实体（`backend/src/services/doc_service.py` 或 `backend/src/services/signal_sync_service.py`）

---

## Phase 3: User Story 1 - 学习整理全部信号并入库 (Priority: P1) 🎯

**Goal**: 一次性或定期将 czsc.signals 下全部信号函数整理为统一元数据并写入 signal_func 表，供 API/筛选任务使用。

**Independent Test**: 执行同步脚本或接口后，`SELECT COUNT(*) FROM signal_func` 与 DocService.get_all_signals() 数量一致；GET /api/v1/docs/signals 或直接查库可见完整列表；每条记录的 name、category、description、param_template 与 DocService 输出一致。

- [X] T005 [US1] 实现全量同步脚本：在 `scripts/` 下新增 `sync_czsc_signals_to_db.py`，逻辑为：获取 DocService.get_all_signals() → 通过 SignalFuncRepo 逐条 upsert 到 signal_func 表；支持可选参数（如 --dry-run 仅打印不写库）；脚本内使用 backend 的 get_db_session、DocService、SignalFuncRepo（`scripts/sync_czsc_signals_to_db.py`）
- [X] T006 [US1] 全量同步执行与校验：运行 `python scripts/sync_czsc_signals_to_db.py`，确认无报错且 signal_func 表行数 ≥ czsc.signals 导出函数数量；抽查若干条 name 在库中与 DocService.get_signal_detail(name) 一致（`scripts/sync_czsc_signals_to_db.py`）
- [ ] T007 [US1] 可选：与 czsc_api/czsc.signals 文档对齐：若存在 `czsc_api/czsc.signals/*.md`，在同步时或单独脚本中，根据 signal_func 表或 DocService 列表校验/生成缺失的 md 文件，使「信号名 ↔ 单文件 md」可追溯（`czsc_api/czsc.signals/`、`scripts/` 或 `backend/src/services/signal_sync_service.py`）

---

## Phase 4: Polish & Cross-Cutting

**Purpose**: 文档与可维护性。

- [X] T008 [P] 文档说明：在 `README.md` 或 `docs/` 中增加「信号函数入库」说明：如何运行 `scripts/sync_czsc_signals_to_db.py`、表结构说明、与 GET /docs/signals 的关系（`README.md` 或 `docs/signals_inventory.md`）
- [ ] T009 可选：提供 API 触发同步或仅文档注明需运维定期执行脚本；若需 API，在 `backend/src/api/v1/` 下增加管理员接口（如 POST /admin/sync-signals）并依赖 get_current_user + role=admin（`backend/src/api/v1/`）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖，可立即执行
- **Phase 2 (Foundational)**: 依赖 Phase 1；**阻塞** Phase 3
- **Phase 3 (US1)**: 依赖 Phase 2
- **Phase 4 (Polish)**: 依赖 Phase 3

### Parallel Opportunities

- T001 与 T002 可并行（环境检查 vs 表结构检查）
- T008 与 T009 可并行（文档 vs 可选 API）

---

## Implementation Strategy

### MVP（最小可行）

1. 完成 Phase 1 + Phase 2（T003 仓储、T004 从 DocService 生成行数据）
2. 完成 T005 + T006（全量同步脚本 + 执行校验）
3. **验收**：signal_func 表条数与 czsc.signals 一致，API /docs/signals 数据来源可切换为库或保留现状

### Incremental

1. Phase 1 + 2 → 具备「枚举 → 入库」能力  
2. Phase 3 → 全量同步一次并校验  
3. Phase 4 → 文档与可选管理接口  

---

## Notes

- 不修改 czsc 核心库代码，仅读取 czsc.signals 的导出与 docstring
- SignalFunc 表已存在且被 screen_service 使用，同步后筛选任务可继续按 is_active=1 读取
- param_template 若 DocService 未直接暴露，可从 description 中正则提取「参数模板：」或从 params 列表中取默认值拼接
