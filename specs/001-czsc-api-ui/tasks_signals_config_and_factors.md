# Tasks: signals_config 与因子库——结论与可选实现

**Input**: 用户问题「学习这个项目，需要创建 signals_config 数据库吗？需要创建因子库吗？」  
**结论摘要**:
- **signals_config 数据库**：当前项目**没有** signals_config 表；信号配置在代码中为 `List[dict]` 传入 `CzscSignals(bg, signals_config=...)`。若需「可复用的、命名的信号配置方案」持久化，则**可选**新增 signals_config 表。
- **因子库**：**因子定义表 factor_def 已存在**（`backend/src/models/mysql_models.py` 中 FactorDef），由 `scripts/db_init_mysql.py` 的 create_all 创建；筛选任务可读 SignalFunc，因子筛选逻辑可后续按 FactorDef 扩展。不需要再「创建因子库表」，只需确认使用方式与可选管理/种子数据。

**Path Conventions**: 后端 `backend/src/`，脚本 `scripts/`

---

## 结论说明

### 1. 是否需要创建 signals_config 数据库？

| 现状 | 说明 |
|------|------|
| 无 signals_config 表 | 项目中仅有 `signal_func`（信号函数元数据）、API 请求体中的 `signal_configs: List[dict]`；signals_config 在 README 中指「基本信号的入参」结构，不是表名。 |
| 可选建表 | 若希望多套「命名信号配置」持久化（如「策略A配置」「日线组合」），可新增表存储 config 名称 + JSON 内容，供 API/回测/筛选按名称加载。 |

**建议**：非必须。若不做「按名称加载预设配置」功能，可不建表；若做，按 Phase 2 任务实现。

### 2. 是否需要创建因子库？

| 现状 | 说明 |
|------|------|
| factor_def 表已存在 | `FactorDef` 在 mysql_models.py 中已定义（name, expression_or_signal_ref, description, is_active），db_init_mysql 会创建。 |
| 筛选任务 | screen_service 当前仅实现按 SignalFunc 的信号筛选；按 FactorDef 的因子筛选可后续扩展。 |

**建议**：不需要再「创建因子库」表结构；需要的是：确认 factor_def 已建、可选种子数据或管理 API、文档说明（见 Phase 1 / Phase 3）。

---

## Phase 1: 确认与文档（必做）

**Purpose**: 明确现有表与用法，避免重复建表。

- [X] T001 确认 factor_def 表已存在：运行 `python scripts/db_init_mysql.py` 后 MySQL 中存在 `factor_def` 表，与 `backend/src/models/mysql_models.py` 中 FactorDef 一致（`backend/src/models/mysql_models.py`、`scripts/db_init_mysql.py`）
- [X] T002 [P] 文档说明「信号配置 vs 因子库」：在 `README.md` 或 `docs/` 中增加小节：说明 (1) 当前无 signals_config 表，信号配置以请求体 List[dict] 或策略内列表存在；(2) factor_def 表已存在，用于因子定义，筛选任务可扩展为按因子计算；(3) signal_func 表存信号函数元数据，与 signals_config（若建表）的区别（`README.md` 或 `docs/signals_and_factors.md`）

---

## Phase 2: 可选——signals_config 表与 API

**Purpose**: 仅当需要「可复用的、命名的信号配置」时执行。

- [X] T003 设计 signals_config 表：在 `backend/src/models/mysql_models.py` 中新增模型（如：id、name、description、config_json、created_at、updated_at），在 `backend/src/utils/settings.py` 中增加 table_signals_config 配置（`backend/src/models/mysql_models.py`、`backend/src/utils/settings.py`）
- [X] T004 迁移与仓储：为 signals_config 表添加 Alembic 迁移或 db_init_mysql 的 create_all 包含新模型；在 `backend/src/storage/` 下新增 `signals_config_repo.py`，提供 list、get_by_name、create、update、delete（`backend/src/storage/signals_config_repo.py`）
- [X] T005 可选 API：在 `backend/src/api/v1/` 下新增或扩展现有路由，提供 GET/POST/PUT/DELETE 命名配置（如 GET /signals-config、POST /signals-config），请求体/响应含 name、config_json（`backend/src/api/v1/`）
- [X] T006 文档：在 README 或 docs 中说明 signals_config 表用途、与 CzscSignals(signals_config=...) 的对应关系及示例（`README.md` 或 `docs/signals_and_factors.md`）

---

## Phase 3: 可选——因子库使用与扩展

**Purpose**: 确认因子表用法，可选种子数据或管理接口。

- [X] T007 [P] 因子定义仓储与列表 API：在 `backend/src/storage/` 下新增 `factor_def_repo.py`（list、get_by_name、upsert）；在 `backend/src/api/v1/` 中提供 GET /factor-defs 或等价，返回 factor_def 列表（`backend/src/storage/factor_def_repo.py`、`backend/src/api/v1/`）
- [X] T008 可选因子筛选扩展：在 `backend/src/services/screen_service.py` 中扩展 run_factor_screen 或类似逻辑，按 FactorDef 记录对股票池计算并写入 ScreenResult（factor_id、value_result）（`backend/src/services/screen_service.py`）
- [X] T009 [P] 因子库文档与种子：在 docs 中说明 factor_def 字段含义、与 signal_func 的区别、筛选任务如何选用信号 vs 因子；可选提供脚本或数据为 factor_def 插入若干条种子数据（`docs/signals_and_factors.md`、`scripts/`）

---

## Dependencies & Execution Order

- **Phase 1**: 无依赖，建议先完成以统一认知。
- **Phase 2**: 依赖 Phase 1；T003→T004→T005，T006 可与 T005 并行。
- **Phase 3**: 依赖 Phase 1；T007 与 T008 可顺序或并行，T009 可与 T007 并行。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 描述 + 文件路径。
- Phase 2/3 为可选，按需勾选执行。
