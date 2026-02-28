# Tasks: 完善 my_singles / factor_def 入库

**Input**: 理解当前项目，完善入库：my_singles（用户收藏）、factor_def（因子定义）。  
**Path Conventions**: 后端 `backend/src/`，脚本 `scripts/`，文档 `docs/`（与 plan.md 一致）。

**现状简述**:
- **my_singles**：已有表（MySingles）、仓储（list_by_user、add、remove）、API（GET 列表、POST 添加、DELETE 取消）。入库路径完整，可补充排序更新与文档。
- **factor_def**：已有表（FactorDef）、仓储（list_all、get_by_name、upsert）、种子脚本（seed_factor_def.py）；API 仅有 GET 列表，缺少通过 API 的「入库」能力（POST/PUT/DELETE）。

---

## Phase 1: 确认与文档（必做）

**Purpose**: 确认表与入库路径一致，文档说明使用方式。

- [X] T001 确认 my_singles、factor_def 表与入库路径：确认 `backend/src/models/mysql_models.py` 中 MySingles、FactorDef 与 `backend/src/utils/settings.py` 中 table_my_singles、table_factor_def 一致；确认 `scripts/db_init_mysql.py` 的 create_all 会创建两表（`backend/src/models/mysql_models.py`、`backend/src/utils/settings.py`、`scripts/db_init_mysql.py`）
- [X] T002 [P] 文档 my_singles 与 factor_def 入库方式：在 `docs/signals_and_factors.md` 或 `docs/` 中增加小节：my_singles 的入库方式（GET/POST/DELETE /api/v1/my_singles，需认证）、factor_def 的入库方式（表结构、GET /api/v1/factor-defs、种子脚本 `scripts/seed_factor_def.py`；若已实现 POST/PUT/DELETE 则一并说明）（`docs/signals_and_factors.md` 或 `docs/my_singles_factor_def.md`）

---

## Phase 2: 完善 factor_def 入库（API 增删改）

**Purpose**: 支持通过 API 对 factor_def 进行新增、更新、删除，完成「入库」闭环。

**Independent Test**: 调用 POST /api/v1/factor-defs 创建因子、PUT 更新、GET 列表可见、DELETE 删除后列表无该项。

- [X] T003 为 factor_def 增加 POST/PUT/DELETE API：在 `backend/src/api/v1/factor_defs.py` 中新增 POST（body: name、expression_or_signal_ref、description、is_active）、PUT /{name}（更新）、DELETE /{name}（删除），复用 `backend/src/storage/factor_def_repo.py` 的 upsert、get_by_name；name 重复时 POST 返回 409（`backend/src/api/v1/factor_defs.py`）
- [X] T004 [P] 文档与校验：在 `docs/signals_and_factors.md` 或 API 文档中补充 factor_def 的 POST/PUT/DELETE 请求体与响应说明；可选在仓储层对 expression_or_signal_ref 做非空校验（`docs/signals_and_factors.md`、`backend/src/storage/factor_def_repo.py`）

---

## Phase 3: 完善 my_singles 入库（闭环与可选增强）

**Purpose**: 确认 my_singles 列表/添加/删除闭环完整，可选支持排序更新。

**Independent Test**: 登录后 GET /my_singles 为空，POST 添加 signal/symbol 后列表可见，DELETE 后消失；可选 PATCH 更新 sort_order 后顺序变化。

- [X] T005 确认 my_singles API 与仓储闭环：核对 `backend/src/api/v1/my_singles.py` 与 `backend/src/storage/my_singles_repo.py` 的 list/add/remove 与认证依赖，确保「列表、添加、删除」无缺漏；必要时补充 404/400 响应（`backend/src/api/v1/my_singles.py`、`backend/src/storage/my_singles_repo.py`）
- [X] T006 [P] 可选 my_singles 排序更新与文档：在 `backend/src/storage/my_singles_repo.py` 中新增 update_sort_order(user_id, item_type, item_id, sort_order)；在 `backend/src/api/v1/my_singles.py` 中新增 PATCH /my_singles/{item_type}/{item_id}（body: sort_order），并在文档中说明收藏与排序（`backend/src/storage/my_singles_repo.py`、`backend/src/api/v1/my_singles.py`、`docs/`）

---

## Dependencies & Execution Order

- **Phase 1**: 无依赖，建议先完成。
- **Phase 2**: 依赖 Phase 1（表与文档认知一致）；T003 与 T004 可 T003 完成后做 T004。
- **Phase 3**: 与 Phase 2 无依赖，可与 Phase 2 并行；T005 先做，T006 可选。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 描述 + 文件路径。
- Phase 2/3 各自具备独立验收标准。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_my_singles_factor_def.md` |
| **总任务数** | 6（Phase 1 共 2，Phase 2 共 2，Phase 3 共 2） |
| **Phase 1** | 确认表与入库路径、文档说明 |
| **Phase 2** | factor_def 增 POST/PUT/DELETE，完善入库 API |
| **Phase 3** | my_singles 闭环确认与可选排序更新 |
| **并行** | T002、T004、T006 标 [P]，可与同 Phase 内其他任务或后续任务并行 |
| **MVP 建议** | 先完成 Phase 1 + Phase 2，即可实现 factor_def 与 my_singles 的完整「入库」能力 |
