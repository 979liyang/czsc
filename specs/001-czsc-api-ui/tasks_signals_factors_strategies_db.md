# Tasks: 信号库(signals)、因子库(factors)、策略库(strategies) 表与入库

**Input**: 将 signal_func 改为 signals 信号库；factor_def 改为 factors 因子库（因子存储多个信号配置）；新增 strategies 策略库并入库 czsc.strategies 中的策略。  
**Path Conventions**: 后端 `backend/src/`，与 plan.md 一致。

**现状简述**:
- 当前：`signal_func` 表存信号函数元数据，`factor_def` 表存单条 expression_or_signal_ref。
- 目标：信号表改名为「信号库」signals；因子表改名为 factors 且一条因子对应多条信号配置（如 factor_usage_demo 的 FACTOR_CONFIGS）；新增 strategies 表存策略配置，并把 czsc.strategies 中 create_single_ma_long、create_third_buy_long 等策略入库。

---

## Phase 1: 信号库（signal_func → signals）

**Purpose**: 表名与业务命名统一为「信号库」signals，模型/配置/代码引用同步修改。

- [x] T001 配置与模型：在 `backend/src/utils/settings.py` 中将 `table_signal_func` 改为 `table_signals`（默认值 `"signals"`）；在 `backend/src/models/mysql_models.py` 中将 `SignalFunc` 的 `__tablename__` 改为使用 `get_settings().table_signals`，类注释改为「信号库（与 czsc.signals 对应）」
- [x] T002 仓储与引用：将 `backend/src/storage/signal_func_repo.py` 重命名为 `backend/src/storage/signals_repo.py`，类名 `SignalFuncRepo` 改为 `SignalsRepo`，内部引用 `SignalFunc` 改为通过 `mysql_models` 的 `SignalFunc`（表名已为 signals，模型名可保留或改为 Signal 需全局一致）；所有引用 `SignalFuncRepo`、`signal_func_repo`、`table_signal_func` 的代码改为 `SignalsRepo`、`signals_repo`、`table_signals`（`backend/src/services/doc_service.py`、`backend/src/services/signal_sync_service.py`、`backend/src/main.py` 等）
- [x] T003 数据库迁移：新增 Alembic 迁移，将表 `signal_func` 重命名为 `signals`（或建新表 `signals` 并迁移数据后删旧表，视当前迁移规范而定）；迁移脚本放在 `backend/alembic/versions/`
- [x] T004 API 与路由：若有单独「信号函数」相关 API（如原 factor_defs 同级的 signal_func 列表），将路由/标签中的「信号函数」改为「信号库」；若 API 内部引用 `signal_func` 表名或旧 repo，改为 `signals` 与 `SignalsRepo`（`backend/src/api/v1/` 下相关模块）

---

## Phase 2: 因子库（factor_def → factors，一因子多信号）

**Purpose**: 表改名为 factors；因子可包含多条信号配置（如 factor_usage_demo 中每因子多条 name/freq/params），供筛选与前端按「因子」维度使用。

- [x] T005 模型与表结构：在 `backend/src/utils/settings.py` 中将 `table_factor_def` 改为 `table_factors`（默认值 `"factors"`）；在 `backend/src/models/mysql_models.py` 中将 `FactorDef` 的 `__tablename__` 改为使用 `get_settings().table_factors`；新增字段或替换：用 `signals_config`（Text/JSON）存储「多条信号配置」列表，每项含 name、freq、及该信号参数字段（如 di、ma_type、timeperiod 等），与 demo 中 `FACTOR_CONFIGS` 单因子下多信号结构一致；保留 name、description、is_active、created_at、updated_at；若保留 expression_or_signal_ref 作兼容可标废弃
- [x] T006 仓储：将 `backend/src/storage/factor_def_repo.py` 重命名为 `backend/src/storage/factors_repo.py`，类名 `FactorDefRepo` 改为 `FactorsRepo`，增删改查使用新表与 `signals_config` 字段；所有引用 `FactorDefRepo`、`factor_def_repo`、`FactorDef`、`table_factor_def` 的代码改为 `FactorsRepo`、`factors_repo`、新模型名、`table_factors`（`backend/src/services/screen_service.py`、`backend/src/api/v1/factor_defs.py` 等）
- [x] T007 筛选服务：在 `backend/src/services/screen_service.py` 中，因子筛选逻辑改为按 factors 表的 `signals_config` 解析出多条信号配置，对每只股票按该列表调用 CzscSignals 或既有信号计算流程，合并/汇总为因子结果写入 screen_result（factor_id 关联 factors.id）
- [x] T008 迁移与 API：新增 Alembic 迁移，将表 `factor_def` 重命名为 `factors` 并添加/调整 `signals_config` 列；将 `backend/src/api/v1/factor_defs.py` 重命名为 `factors.py`（或保留路径但路由 prefix 改为 `/factors`），请求/响应体支持 `signals_config` 列表的读写，标签改为「因子库」

---

## Phase 3: 策略库（strategies 表与入库）

**Purpose**: 新增 strategies 表，结构可存储 czsc 策略（如 Position 的 opens/exits 等配置）；将 czsc.strategies 中现有策略（如 create_single_ma_long、create_single_ma_short、create_third_buy_long、create_third_sell_short 等）序列化为配置并写入数据库。

- [x] T009 模型与表：在 `backend/src/utils/settings.py` 中新增 `table_strategies = "strategies"`；在 `backend/src/models/mysql_models.py` 中新增 `Strategy` 模型，字段至少包含：id、name（唯一）、description、strategy_type（如 single_ma_long / third_buy_long）、config_json（Text，存 Position 的 opens/exits 等可序列化配置，与 czsc Position.load/dump 兼容）、is_active、created_at、updated_at
- [x] T010 仓储与 API：新增 `backend/src/storage/strategies_repo.py`（StrategiesRepo：list_all、get_by_name、upsert、delete）；新增 `backend/src/api/v1/strategies.py`（GET 列表、GET 单条、POST 新增、PUT 更新、DELETE 删除），挂载到 `backend/src/main.py`，标签「策略库」
- [x] T011 种子数据：编写脚本 `scripts/seed_strategies.py`，从 czsc.strategies 中读取 create_single_ma_long、create_single_ma_short、create_third_buy_long、create_third_sell_short、create_macd_long、create_macd_short 等策略，将每种的 Position 配置 dump 为 JSON（或等价 config_json），写入 strategies 表；脚本可接受 `--dry-run`，默认执行写入

---

## Phase 4: 收尾与一致性

**Purpose**: 文档、前端或其它引用表名/接口处统一为 signals、factors、strategies。

- [x] T012 文档与注释：更新 `backend/README.md` 或项目文档中涉及 signal_func、factor_def 的说明为 signals、factors；补充 strategies 表与 API 说明；检查 `specs/001-czsc-api-ui/plan.md` 中存储相关描述是否需更新
- [x] T013 前端与其它引用：若前端或配置中有硬编码 `signal_func`、`factor_def`、`factor-defs` 等，改为 `signals`、`factors`、`factors` API 路径；若有策略相关页面需拉取策略列表，对接 GET /api/v1/strategies（或实际路由）

---

## Dependencies & Execution Order

- **Phase 1**：T001 → T002；T003 可与 T002 并行准备，但迁移执行建议在 T002 代码就绪后；T004 依赖 T002。
- **Phase 2**：依赖 Phase 1 完成；T005 → T006 → T007；T008 与 T006/T007 可部分并行。
- **Phase 3**：可与 Phase 2 并行；T009 → T010 → T011。
- **Phase 4**：依赖 Phase 1/2/3 完成。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_signals_factors_strategies_db.md` |
| **总任务数** | 13 |
| **Phase 1** | 信号库 signal_func → signals（表、模型、repo、迁移、API） |
| **Phase 2** | 因子库 factor_def → factors，一因子多信号配置 |
| **Phase 3** | 策略库 strategies 表、repo、API、种子入库 |
| **Phase 4** | 文档与前端一致性 |
| **建议顺序** | Phase 1 → Phase 2 与 Phase 3（可并行）→ Phase 4 |
