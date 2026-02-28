# Tasks: 根据当前项目思想把 signals_config、my_singles、factor_def 全部入库

**Input**: 根据当前项目思想，把所有的 signals_config、my_singles、factor_def 入库。  
**Path Conventions**: 后端 `backend/src/`，脚本 `scripts/`，文档 `docs/`（与 plan.md 一致）。

**前提**: 三表及 API 已存在（见 tasks_signals_config_and_factors.md、tasks_my_singles_factor_def.md）。本清单聚焦**批量/全量入库**：通过脚本或文档使三表在「项目思想」下完成数据落地。

---

## Phase 1: 确认三表与入库能力（必做）

**Purpose**: 确认 signals_config、my_singles、factor_def 表与入库路径已就绪，明确各表「全量入库」方式。

- [X] T001 确认三表与入库路径：确认 `backend/src/models/mysql_models.py` 中 SignalsConfig、MySingles、FactorDef 及 `backend/src/utils/settings.py` 对应表名；确认 `scripts/db_init_mysql.py` 会创建三表；确认 signals_config 有 repo+API、factor_def 有 repo+API+seed 脚本、my_singles 有 repo+API（`backend/src/models/mysql_models.py`、`scripts/db_init_mysql.py`、`docs/signals_and_factors.md`）
- [X] T002 [P] 文档「三表入库」顺序与方式：在 `docs/signals_and_factors.md` 或 `docs/inventory_seed.md` 中增加「入库顺序与脚本」小节：先执行 `db_init_mysql.py` → 可选 `sync_czsc_signals_to_db.py`（signal_func 全量）→ `sync_factor_def_from_signal_func.py`（factor_def 全量）→ `seed_signals_config.py`（signals_config 预设）；my_singles 由用户通过 API 按需入库（`docs/`）

---

## Phase 2: factor_def 全量入库（与 signal_func 一致）

**Purpose**: 使「所有」已入库信号在 factor_def 中有对应因子，与当前项目「信号→因子」思想一致。

**Independent Test**: 运行 `sync_czsc_signals_to_db.py` 后运行 factor_def 同步脚本，GET /api/v1/factor-defs 条数与 signal_func 表一致（或可配置过滤）。

- [X] T003 实现 factor_def 全量同步脚本：在 `scripts/sync_factor_def_from_signal_func.py` 中从 `signal_func` 表读取所有记录（或 is_active=1），逐条 upsert 到 factor_def（name 取信号名、expression_or_signal_ref 取 module_path+name 或等价全名、description 可取自 signal_func），支持 --dry-run（`scripts/sync_factor_def_from_signal_func.py`）
- [X] T004 [P] 文档与用法：在 `docs/signals_and_factors.md` 或 README 中说明 factor_def 全量入库执行顺序（先 sync_czsc_signals_to_db 再 sync_factor_def_from_signal_func）及脚本用法（`docs/`、`scripts/sync_factor_def_from_signal_func.py`）

---

## Phase 3: signals_config 预设入库

**Purpose**: 将项目内常用或示例的命名信号配置写入 signals_config 表，便于 API/回测按名称加载。

**Independent Test**: 运行 seed 脚本后 GET /api/v1/signals-config 返回至少若干条预设配置。

- [X] T005 实现 signals_config 预设入库脚本：在 `scripts/seed_signals_config.py` 中定义若干条预设（如 README 示例、或从 signal_func 取前 N 条生成默认 config_json），调用 SignalsConfigRepo 或 API 写入；支持 --dry-run（`scripts/seed_signals_config.py`、`backend/src/storage/signals_config_repo.py`）
- [X] T006 [P] 文档：在 `docs/signals_and_factors.md` 中补充 signals_config 预设入库脚本用法及预设列表说明（`docs/signals_and_factors.md`）

---

## Phase 4: my_singles 入库说明与可选种子

**Purpose**: my_singles 按项目思想由用户通过 API 入库；可选为测试/默认用户批量导入。

**Independent Test**: 文档明确 my_singles 仅能通过认证 API 入库；可选脚本对指定 user_id 批量导入后 GET /my_singles 可见。

- [X] T007 [P] 文档 my_singles 入库方式：在 `docs/signals_and_factors.md` 或 `docs/inventory_seed.md` 中明确 my_singles 无服务端批量种子、仅通过 GET/POST/DELETE/PATCH /api/v1/my_singles（需认证）由用户自行入库（`docs/`）
- [X] T008 可选 my_singles 测试数据脚本：在 `scripts/seed_my_singles.py` 中支持从 JSON/配置文件或固定列表为指定 user_id 批量插入 my_singles（仅用于测试/演示），需在脚本或文档中注明仅限测试环境（`scripts/seed_my_singles.py`、`backend/src/storage/my_singles_repo.py`）

---

## Dependencies & Execution Order

- **Phase 1**: 无依赖，建议先完成。
- **Phase 2**: 依赖 Phase 1；依赖 `signal_func` 表已有数据（建议先运行 `sync_czsc_signals_to_db.py`）。
- **Phase 3**: 依赖 Phase 1；可与 Phase 2 并行。
- **Phase 4**: 依赖 Phase 1；T007 与 T008 可独立，T008 可选。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 描述 + 文件路径。
- 无 [Story] 标签（本清单按「入库」目标分 Phase，非 spec 用户故事）。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_seed_signals_config_my_singles_factor_def.md` |
| **总任务数** | 8（Phase 1 共 2，Phase 2 共 2，Phase 3 共 2，Phase 4 共 2） |
| **Phase 1** | 确认三表与入库能力、文档入库顺序与方式 |
| **Phase 2** | factor_def 全量同步脚本（自 signal_func）+ 文档 |
| **Phase 3** | signals_config 预设入库脚本 + 文档 |
| **Phase 4** | my_singles 入库说明 + 可选测试数据脚本 |
| **并行** | T002、T004、T006、T007 标 [P] |
| **建议执行顺序** | db_init_mysql → sync_czsc_signals_to_db → sync_factor_def_from_signal_func → seed_signals_config；my_singles 通过 API 由用户入库 |
