# Tasks: 学习 CZSC、了解因子与 strategies、完善数据库和代码

**Input**: 学习 czsc，了解因子和 strategies，完善数据库和代码。  
**Path Conventions**: 后端 `backend/src/`，脚本 `scripts/`，文档 `docs/`，示例 `examples/`（与 plan.md 一致）。

**目标**：在现有实现基础上，厘清 CZSC 中「因子」与「策略」的概念与对应表/代码，补全文档与必要的数据与代码完善。

---

## Phase 1: 学习 CZSC 与「因子、策略」概念（文档）

**Purpose**: 在项目内固化对 czsc 因子与策略的理解，便于后续完善数据库与代码。

**Independent Test**: 阅读文档后能说清：因子在本项目中对应哪些表与接口、策略对应哪些表/目录与接口。

- [X] T001 [P] 编写「CZSC 中的因子与策略」文档：在 `docs/learning/` 下新增 `czsc_factors_and_strategies.md`，说明 (1) 因子：在 czsc 中多指「可计算的指标/信号」，在本项目中对应 `factor_def` 表与 `run_factor_screen`，与 `signal_func` 的关系（因子可引用信号）；(2) 策略：在 czsc 中为「标的+positions+signals_config+回测」的完整逻辑，在本项目中对应 `examples/strategies/` 目录、`BacktestService`、`strategy_config`（含 strategy_class、signals_config 等）；(3) 二者关系：策略使用 signals_config，因子用于筛选维度（`docs/learning/czsc_factors_and_strategies.md`）
- [X] T002 [P] 文档与现有 learning 串联：在 `docs/learning/czsc_signals.md` 或 `docs/signals_and_factors.md` 中增加指向 `docs/learning/czsc_factors_and_strategies.md` 的链接；在 `docs/README.md` 或项目 README 的文档索引中列入该篇（`docs/learning/`、`docs/README.md` 或 `README.md`）

---

## Phase 2: 完善数据库（因子与策略相关表）

**Purpose**: 确认因子相关表及入库链路完整；按需增加或明确策略元数据在库中的落位。

**Independent Test**: 执行入库脚本后 factor_def、signal_func、signals_config 数据完整；若引入策略表则能通过 API 或脚本读写。

- [X] T003 确认因子与信号相关表及脚本：核对 `factor_def`、`signal_func`、`signals_config` 在 `backend/src/models/mysql_models.py` 与 `scripts/db_init_mysql.py` 中已建表；确认 `scripts/sync_czsc_signals_to_db.py`、`scripts/sync_factor_def_from_signal_func.py`、`scripts/seed_signals_config.py` 可正常执行并写入（`backend/src/models/mysql_models.py`、`scripts/`）
- [X] T004 可选策略元数据表与仓储：若需将策略元数据入库（名称、描述、适用市场、配置 JSON 等），在 `backend/src/models/mysql_models.py` 中新增 `StrategyMeta` 或等价模型及 `backend/src/utils/settings.py` 表名配置，在 `backend/src/storage/` 下新增 `strategy_meta_repo.py` 提供 list/get_by_id/upsert；否则在文档中明确「策略示例仅来自 examples/strategies 目录扫描」不建表（`backend/src/models/mysql_models.py`、`backend/src/storage/`、`docs/`）
- [X] T005 [P] 文档入库顺序与因子/策略说明：在 `docs/signals_and_factors.md` 中补充「因子与策略在数据库中的落位」：factor_def/signal_func 用于因子与信号，signals_config 用于命名配置，策略示例当前来自文件；若有 StrategyMeta 表则说明用途（`docs/signals_and_factors.md`）

---

## Phase 3: 完善代码（因子、策略与回测衔接）

**Purpose**: 确保回测与 signals_config/factor 衔接顺畅，示例服务与目录一致，代码可维护。

**Independent Test**: 回测 API 可使用 signals_config 按名称加载配置；策略示例列表与 examples/strategies 一致；无阻塞错误。

- [X] T006 回测与 signals_config 衔接：在 `backend/src/services/backtest_service.py` 或调用层支持从 `signals_config` 表按名称加载配置（如 strategy_config 中支持 `signals_config_name`，内部解析为 signals_config 的 config_json 注入 strategy_config），并在 API 或文档中说明用法（`backend/src/services/backtest_service.py`、`backend/src/api/v1/backtest.py`、`docs/`）
- [X] T007 策略示例服务与目录一致性：核对 `backend/src/services/example_service.py` 与 `examples/strategies/` 目录约定（如 strategy_*.py 或 *.py）一致；若目录为空或路径可配置，在 `backend/src/utils/settings.py` 或环境变量中统一 EXAMPLES_PATH，并在文档中说明（`backend/src/services/example_service.py`、`backend/src/utils/settings.py`、`docs/`）
- [X] T008 [P] 代码注释与类型：在 `backend/src/services/screen_service.py`（run_signal_screen、run_factor_screen）、`backend/src/services/backtest_service.py` 的关键入参处增加中文注释，说明与 czsc 因子/策略的对应关系；必要时补充类型注解（`backend/src/services/screen_service.py`、`backend/src/services/backtest_service.py`）

---

## Phase 4: Polish（文档索引与自检）

**Purpose**: 文档可发现、自检清单可执行。

- [X] T009 [P] 文档索引更新：在 `README.md` 或 `docs/README.md` 中增加「学习 CZSC」「因子与策略」「数据库入库顺序」等入口，指向 `docs/learning/czsc_factors_and_strategies.md`、`docs/signals_and_factors.md`（`README.md`、`docs/README.md`）
- [X] T010 自检清单：在 `docs/` 或 `specs/001-czsc-api-ui/` 下增加简短自检项（如：db_init_mysql → sync_czsc_signals_to_db → sync_factor_def_from_signal_func → seed_signals_config；GET /factor-defs、GET /signals-config、GET /examples 可用），便于后续回归（`docs/` 或 `specs/001-czsc-api-ui/`）

---

## Dependencies & Execution Order

- **Phase 1**: 无依赖，建议先完成以统一概念。
- **Phase 2**: 依赖 Phase 1；T003 先做，T004 可选，T005 可与 T004 并行或其后。
- **Phase 3**: 依赖 Phase 1；T006、T007、T008 可部分并行（不同文件）。
- **Phase 4**: 依赖 Phase 1–3 主体完成；T009 与 T010 可并行。

---

## 格式校验

- 所有任务均满足：`- [ ]` + TaskID + 可选 `[P]` + 描述 + 文件路径。
- 本清单按「学习→数据库→代码→收尾」分 Phase，未使用 [USx] 标签。

---

## Report 摘要

| 项目 | 内容 |
|------|------|
| **生成路径** | `specs/001-czsc-api-ui/tasks_czsc_factors_strategies_db.md` |
| **总任务数** | 10 |
| **Phase 1** | 学习与文档：因子与策略概念文档、与现有 learning 串联 |
| **Phase 2** | 完善数据库：因子/信号表与脚本确认、可选策略元数据表、文档 |
| **Phase 3** | 完善代码：回测与 signals_config 衔接、示例服务与目录一致、注释与类型 |
| **Phase 4** | 文档索引与自检清单 |
| **并行** | T001、T002、T005、T008、T009 标 [P] |
| **建议 MVP** | 先完成 Phase 1 + T003，再按需做 T004、T006–T010 |
