# 信号配置与因子库说明

本文说明项目中**信号配置**与**因子库**的现状与用法，便于避免重复建表与统一认知。

**延伸阅读**：CZSC 中「因子」与「策略」的概念及在本项目中的落位见 [learning/czsc_factors_and_strategies.md](learning/czsc_factors_and_strategies.md)。

## 1. 信号配置（signals_config）

### 概念与可选表

- 在 README 与 czsc 代码里，「signals_config」指**基本信号的入参结构**（如 `name`、`freq`、`di`、`ma_type`、`timeperiod` 等），即传给 `CzscSignals(bg, signals_config=...)` 的 `List[dict]`。
- 信号配置除可写在请求体或策略代码内外，本项目也提供可选的 **signals_config 表** 做持久化（见下）。

本项目已实现可选的 **signals_config 表**与 API，用于持久化命名配置：

- **表**：`signals_config`（见 `backend/src/models/mysql_models.py` 中 `SignalsConfig`），字段：id、name、description、config_json、created_at、updated_at。
- **API**：`GET/POST/PUT/DELETE /api/v1/signals-config`，请求体/响应含 name、config_json（与 `CzscSignals(signals_config=...)` 入参一致的 JSON 数组字符串）。按名称加载后解析 `config_json` 为 `List[dict]` 即可传入 CZSC。
- **仓储**：`backend/src/storage/signals_config_repo.py` 提供 list、get_by_name、create、update、delete、get_config_as_list（解析为 List[dict] 供计算使用）。

## 2. 因子库（factor_def）

### factor_def 表已存在

- **因子定义表**已在 `backend/src/models/mysql_models.py` 中定义为 `FactorDef`，表名由配置 `table_factor_def`（默认 `factor_def`）指定。
- 运行 `python scripts/db_init_mysql.py` 时，会通过 SQLAlchemy `Base.metadata.create_all()` 创建该表，无需再「创建因子库」表结构。
- 表字段含义：
  - `name`：因子名称，唯一，便于在筛选结果与报表中识别。
  - `expression_or_signal_ref`：表达式或关联的信号函数全名（如 `czsc.signals.tas_ma_base_V230313`）；在 `run_factor_screen` 中会作为信号名参与计算。
  - `description`：说明。
  - `is_active`：是否启用（1 启用，0 禁用）；仅启用的因子参与因子筛选。
- 与 **signal_func** 的区别：`signal_func` 存「有哪些信号函数」的元数据（名、模块、分类等）；`factor_def` 存「业务侧命名的因子」，可引用信号函数或未来扩展为自定义表达式，用于筛选任务中的「因子维度」统计与展示。

### 筛选任务中的用法：信号 vs 因子

- **run_signal_screen**：按 `signal_func` 表中启用的信号函数，对股票池逐只、逐信号计算，结果写入 `screen_result`（`signal_name` 有值，`factor_id` 为空）。适合「全量信号函数扫描」。
- **run_factor_screen**：按 `factor_def` 表中启用的因子，对股票池逐只、逐因子计算；因子的 `expression_or_signal_ref` 填信号函数全名（如 `czsc.signals.tas_ma_base_V230313`），计算逻辑与信号一致，结果写入 `screen_result`（`factor_id` 有值，`signal_name` 为空）。适合「只关心部分因子/组合」的场景。
- 选用建议：若需对所有已入库信号做全市场扫描用 `run_signal_screen`；若只对少数命名的因子做筛选用 `run_factor_screen` 并在 `factor_def` 中维护因子列表。

## 3. signal_func 与 signals_config（若建表）的区别

| 概念 | 含义 |
|------|------|
| **signal_func** | 信号**函数**的元数据：函数名、模块路径、分类、参数模板、说明、是否启用。表示「有哪些信号函数可用」，不存具体某次调用的参数。 |
| **signals_config（若建表）** | 某套**命名配置**：保存多组「信号名 + 入参」的 JSON（如策略 A 的日线组合）。用于按名称加载预设，供 API/回测/筛选复用。 |

简而言之：`signal_func` 描述「有哪些信号」，`signals_config`（若实现）描述「某套配置里选了哪些信号以及各自参数」。

## 4. signals_config 表与 CzscSignals 的对应关系

- 表中 `config_json` 存储的即 `CzscSignals(bg, signals_config=...)` 的第二个参数序列化结果。
- 示例：若代码中为 `signals_config = [{"name": "czsc.signals.tas_ma_base_V230313", "freq": "日线", "di": 1}]`，则入库时 `config_json` 为 `'[{"name":"czsc.signals.tas_ma_base_V230313","freq":"日线","di":1}]'`。读取后 `json.loads(row.config_json)` 得到 list，再传给 CZSC 即可。

## 5. my_singles 与 factor_def 入库方式

### my_singles（用户收藏）

- **表**：`my_singles`（`backend/src/models/mysql_models.py` 中 `MySingles`），字段：user_id、item_type（signal/symbol）、item_id、sort_order。
- **入库方式**：**无服务端批量种子**；仅通过以下认证接口由用户自行入库（GET/POST/DELETE/PATCH /api/v1/my_singles，需 `Authorization: Bearer <token>`）。
  - **GET /api/v1/my_singles**：获取当前用户收藏列表，可选查询参数 `item_type=signal|symbol`。
  - **POST /api/v1/my_singles**：添加收藏，请求体 `{ "item_type": "signal"|"symbol", "item_id": "信号名或标的代码", "sort_order": 0 }`。
  - **DELETE /api/v1/my_singles/{item_type}/{item_id}**：取消收藏。
- **PATCH /api/v1/my_singles/{item_type}/{item_id}**：更新某条收藏的排序，请求体 `{ "sort_order": 0 }`；记录不存在返回 404。

### factor_def（因子定义）

- **表**：`factor_def`（见上文「因子库」），由 `scripts/db_init_mysql.py` 的 `create_all` 创建。
- **入库方式**：
  - **GET /api/v1/factor-defs**：查询因子列表，可选 `active_only=true` 仅返回启用的因子。
  - **POST /api/v1/factor-defs**：新增因子（body：name、expression_or_signal_ref、description、is_active）；name 重复返回 409。
  - **PUT /api/v1/factor-defs/{name}**：按 name 更新因子（body：expression_or_signal_ref、description、is_active 可选）。
  - **DELETE /api/v1/factor-defs/{name}**：按 name 删除因子。
  - **脚本**：`python scripts/seed_factor_def.py` 可写入示例因子数据。
- **POST 请求体**：`{ "name": "因子名", "expression_or_signal_ref": "czsc.signals.xxx", "description": "说明", "is_active": 1 }`；响应为单条因子 JSON（id、name、expression_or_signal_ref、description、is_active、created_at、updated_at）。
- **PUT 请求体**：`{ "expression_or_signal_ref": "可选", "description": "可选", "is_active": "可选" }`；响应为更新后的单条因子 JSON。建议填写 expression_or_signal_ref 以便 run_factor_screen 使用。

## 6. 因子与策略在数据库中的落位

- **因子与信号**：`factor_def` 表存因子定义（可引用信号函数全名）；`signal_func` 表存信号函数元数据。二者用于筛选任务（run_signal_screen / run_factor_screen）及因子维度统计。
- **命名信号配置**：`signals_config` 表存多套「信号名+入参」的 JSON，供 API、回测按名称加载，与 czsc 策略中的 signals_config 对应。
- **策略示例**：当前**仅来自 examples/strategies 目录扫描**，不建策略元数据表；策略列表与详情由 `ExampleService` 解析 `strategy_*.py` 文件得到，GET /api/v1/examples 即据此返回。若后续需策略入库可扩展 StrategyMeta 表。
- **回测按名称加载 signals_config**：POST /api/v1/backtest/run 的请求体 `strategy_config` 中可带 **signals_config_name**（字符串），后端会从 `signals_config` 表按该名称查出 `config_json`，解析为 list 后注入 `strategy_config["strategy_kwargs"]["signals_config"]` 再调用回测；名称不存在时返回 400。

## 7. 三表入库顺序与脚本

按当前项目思想，建议按以下顺序完成 **signals_config、factor_def、my_singles** 的数据入库：

1. **`python scripts/db_init_mysql.py`**：创建/校验所有表（含 signal_func、signals_config、factor_def、my_singles）。
2. **`python scripts/sync_czsc_signals_to_db.py`**（可选）：将 czsc.signals 全量同步到 **signal_func** 表。
3. **`python scripts/sync_factor_def_from_signal_func.py`**：从 signal_func 全量同步到 **factor_def**，使每个已入库信号都有对应因子（建议在 sync_czsc_signals_to_db 之后执行）。支持 `--dry-run`（仅打印不写库）、`--active-only`（仅同步 is_active=1 的信号）。
4. **`python scripts/seed_signals_config.py`**：向 **signals_config** 表写入若干条预设命名配置（如 README 示例组合）。支持 `--dry-run`。当前预设包括：「README示例日线组合」（日线均线+五笔）、「日线单信号笔状态」等，见脚本内 `_presets()`。
5. **my_singles**：无服务端批量种子；仅通过 **GET/POST/DELETE/PATCH /api/v1/my_singles**（需认证）由用户在前端或 API 按需入库。

脚本用法详见各脚本文件头注释或下文「相关文件」。

## 8. 相关文件

- 表模型与配置：`backend/src/models/mysql_models.py`、`backend/src/utils/settings.py`
- 表初始化：`scripts/db_init_mysql.py`
- 信号配置仓储与 API：`backend/src/storage/signals_config_repo.py`、`backend/src/api/v1/signals_config.py`
- 因子定义仓储与 API：`backend/src/storage/factor_def_repo.py`、`backend/src/api/v1/factor_defs.py`
- 信号/因子筛选服务：`backend/src/services/screen_service.py`（`run_signal_screen`、`run_factor_screen`）
- 因子种子数据（可选）：`scripts/seed_factor_def.py`，用于向 `factor_def` 插入示例数据
- 全量同步：`scripts/sync_factor_def_from_signal_func.py`（从 signal_func 同步到 factor_def）、`scripts/seed_signals_config.py`（signals_config 预设）
- 可选测试数据：`scripts/seed_my_singles.py`（**仅限测试/演示环境**，为指定 user_id 批量导入收藏；生产环境请勿使用，用户收藏应通过 API 由用户自行入库）
- 任务与可选实现：`specs/001-czsc-api-ui/tasks_signals_config_and_factors.md`、`specs/001-czsc-api-ui/tasks_my_singles_factor_def.md`、`specs/001-czsc-api-ui/tasks_seed_signals_config_my_singles_factor_def.md`
