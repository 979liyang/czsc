# Tasks: 每日定时数据拉取与前端手动触发

**Input**: 用户需求「每天定时执行拉取股票日线 daily/fetch.py、分钟数据 minute/fetch.py；前端可手动调用拉取；若今日已手动执行则定时脚本可选择是否拉取；**python scripts/daily/fetch.py 执行时默认拉取当天股票**」。  
**Prerequisites**: 现有 `scripts/daily/fetch.py`、`scripts/minute/fetch.py`、`scripts/scheduled_tasks.py`（含 fetch_daily、fetch_minute 子命令）；后端 FastAPI、MySQL、前端 Vue3 已就绪。

**Organization**: 按用户故事分组，便于独立实现与验收。

## 格式说明：`[ID] [P?] [Story?] 描述`

- **[P]**: 可并行（不同文件、无依赖）
- **[Story]**: 所属用户故事（US1、US2、US3、US4）
- 描述中需包含具体文件路径

## 路径约定

- 后端：`backend/src/`
- 脚本：`scripts/`
- 前端：`frontend/src/`
- 文档：`docs/`

---

## Phase 1: Setup（数据库与配置）

**Purpose**: 新增“数据拉取运行记录”表与配置，供手动/定时统一查询“今日是否已执行”。

- [x] T001 在 `backend/src/models/mysql_models.py` 中新增模型 `DataFetchRun`：表名由 settings 的 `table_data_fetch_run` 指定；字段：id（自增主键）、task_type（String(32)，取值 daily / minute，index）、run_at（DateTime，运行时间，index）、trigger（String(16)，取值 manual / scheduled）、status（String(16)，running / success / failed，默认 running）、summary（Text，可选，如「成功 5000 只」）、params_json（Text，可选）、created_at（DateTime）；注释与现有风格一致
- [x] T002 在 `backend/src/utils/settings.py` 中新增配置项 `table_data_fetch_run: str = "data_fetch_run"`
- [x] T003 在 `backend` 的 MySQL 初始化/迁移流程中增加 `data_fetch_run` 表的创建（若使用 alembic 则新增 migration，若使用 db_init_mysql.py 或等价脚本则在该脚本中增加该表创建逻辑）；表结构需与 T001 模型一致

---

## Phase 2: Foundational（仓储与调度入口）

**Purpose**: 运行记录写入与查询、定时脚本“今日是否已执行”的判定依赖此层。

- [x] T004 [P] 在 `backend/src/storage/` 下新增 `data_fetch_run_repo.py`（或等价命名）：提供 `create(task_type, trigger, status='running', params_json=None) -> DataFetchRun`、`update_status(run_id, status, summary=None)`、`get_today_success(task_type) -> Optional[DataFetchRun]`（按 task_type 与 run_at 的日期为今天且 status=success 查询一条）；使用项目现有 MySQL session 与 ORM
- [x] T005 在 `scripts/scheduled_tasks.py` 中为 `fetch_daily`、`fetch_minute` 子命令增加可选参数 `--skip-if-done-today`：当传入时，在真正执行拉取前通过调用 backend 的 DataFetchRun 查询逻辑（或直接读 MySQL）判断当日是否已有同 task_type 的 success 记录；若有则打印日志“今日已执行过 [daily|minute]，跳过”并 exit(0)，否则照常执行；执行成功后在脚本结束前写入一条 success 记录（需能从脚本侧访问 backend 的 repo 或执行一条 INSERT，可考虑通过 `python -m backend.src.scripts.record_fetch_run` 子进程或等价方式写入）

---

## Phase 3: User Story 1 - 后端“手动触发”API (P1)

**Goal**: 前端或第三方可通过 API 手动触发日线/分钟拉取，并得到运行记录 id 与状态；执行可为异步（后台子进程），避免 HTTP 超时。

**Independent Test**: 调用 POST /api/v1/data-fetch/trigger 且 body 为 { "task_type": "daily" }，返回 202 及 run_id；随后 GET /api/v1/data-fetch/runs/{run_id} 或 list 接口能查到该 run，状态先为 running，脚本结束后变为 success 或 failed；同一天内再次触发可再插入新记录。

- [x] T006 [US1] 在 `backend/src/api/v1/` 下新增 `data_fetch.py`（或并入现有 jobs 相关路由）：注册路由前缀 `data-fetch`；实现 `POST /trigger`，请求体为 `{ "task_type": "daily" | "minute" }`；校验 task_type 后插入一条 DataFetchRun（trigger=manual, status=running），返回 run_id 与 status；在后台通过 subprocess 或 multiprocessing 调用 `scripts/scheduled_tasks.py fetch_daily` 或 `fetch_minute`（不传 --skip-if-done-today），脚本结束时根据退出码更新该条记录为 success 或 failed，并可选写入 summary（如从脚本日志解析或固定文案）；使用 loguru 记录日志
- [x] T007 [US1] 在同一 `data_fetch.py` 中实现 `GET /runs`：支持 query 参数 `task_type`（可选）、`limit`（默认 20）、`date`（可选，YYYY-MM-DD，只查该日）；返回运行记录列表（id、task_type、run_at、trigger、status、summary、created_at）；实现 `GET /runs/{run_id}`：返回单条记录详情
- [x] T008 [US1] 在 `backend/src/main.py` 中挂载 data_fetch 路由（若为独立 router）；在 `backend/src/models/schemas.py` 中新增 Pydantic 模型 `DataFetchTriggerRequest`（task_type: Literal["daily","minute"]）、`DataFetchRunResponse`（与 DataFetchRun 字段对应），供 API 使用

---

## Phase 4: User Story 2 - 定时脚本“今日已执行则跳过” (P1)

**Goal**: 定时任务（cron/计划任务）调用 fetch_daily/fetch_minute 时，若当天已有成功记录（含手动触发），可通过参数选择跳过执行，避免重复拉取。

**Independent Test**: 先通过 API 或直接写库插入一条今日 task_type=daily、status=success 的记录；再执行 `python scripts/scheduled_tasks.py fetch_daily --skip-if-done-today`，脚本不执行实际拉取即退出 0 并输出“今日已执行过 daily，跳过”；未加该参数时仍正常执行并写库。

- [x] T009 [US2] 完善 T005：确保 `--skip-if-done-today` 的查询使用“当前服务器日期”的“今日”区间（考虑 timezone 与 MySQL 的 run_at 存储方式）；脚本在执行成功后的写库逻辑与 T005 一致；在 `docs/instructions/cron_examples.md` 中增加一段说明：推荐在 cron 中加 `--skip-if-done-today` 的示例（如每日 17:00 执行 fetch_daily，若当天已手动拉取过则跳过）

---

## Phase 5: User Story 3 - 前端“数据拉取”页 (P2)

**Goal**: 前端提供一页“数据拉取/数据维护”，可手动触发日线、分钟拉取，并展示最近运行记录及状态；若今日已有成功记录可给出提示。

**Independent Test**: 打开数据拉取页，点击“拉取日线”后列表中出现一条 running，随后变为 success；今日已有 success 时页面上有“今日日线已执行过”类提示；拉取分钟同理。

- [x] T010 [P] [US3] 在 `frontend/src/router/routes.ts` 中新增路由：path `/data-fetch`（或 `/data-maintain`），name `DataFetch`，meta 含 `layout: 'dashboard'`、`requiresAuth: true`、`title: '数据拉取'`，component 指向 `views/DataFetch.vue`
- [x] T011 [US3] 在 `frontend/src/api/` 下新增 `dataFetch.ts`：封装 `triggerFetch(task_type: 'daily' | 'minute')`（POST /api/v1/data-fetch/trigger）、`getRuns(params?: { task_type?, limit?, date? })`（GET /api/v1/data-fetch/runs）、`getRun(id)`（GET /api/v1/data-fetch/runs/:id）；使用项目现有 axios 实例
- [x] T012 [US3] 在 `frontend/src/views/DataFetch.vue` 中实现页面：顶部说明文案（可简述日线/分钟拉取用途）；两个主按钮“拉取日线”“拉取分钟”，点击调用 triggerFetch，成功后轮询或刷新列表直至该 run 状态非 running；下方表格展示最近运行记录（任务类型、触发方式、运行时间、状态、摘要）；支持仅看今日记录或按 task_type 筛选；若当日已有 task_type=daily 且 status=success 的记录，在“拉取日线”旁显示“今日已执行”；分钟同理
- [x] T013 [US3] 在 `frontend/src/layouts/Dashboard.vue` 的侧栏菜单中增加“数据拉取”入口，链接到 `/data-fetch`；在 titleMap 或 meta 中为 `/data-fetch` 设置标题“数据拉取”

---

## Phase 6: Polish & 一致性

**Purpose**: 脚本与 API 对齐、文档与错误处理一致。

- [x] T014 确保 `scripts/scheduled_tasks.py` 中 `fetch_minute` 实际调用的脚本与需求一致：若当前为 `scripts/minute/scan.py`（仅扫描 coverage），而用户需要“拉取分钟数据”为 `scripts/minute/fetch.py`，则新增子命令 `fetch_minute_data` 调用 `scripts/minute/fetch.py`，并在 tasks 的“分钟拉取”相关描述中统一为“拉取分钟数据”对应 minute/fetch.py；或在 T005/T006/T009 中明确“minute”对应 fetch.py，并保留原 fetch_minute（scan）为另一子命令
- [x] T015 [P] 在 `backend/src/models/schemas.py` 中为 DataFetchRun 的 list 响应补充分页或总数字段（若前端需要）；API 错误时返回 4xx/5xx 与统一 error 格式

---

## Phase 7: User Story 4 - daily fetch 默认拉取当天 (P2)

**Goal**: 执行 `python scripts/daily/fetch.py` 且不传任何日期参数时，默认拉取“当天”全市场日线（即单日全市场模式，日期为当日或当日最近交易日），便于定时/手动一键拉取当日数据。

**Independent Test**: 不传 `--start-date`、`--end-date`、`--trade-date` 时运行 `python scripts/daily/fetch.py`，脚本应使用当日或当日最近交易日作为 trade_date，执行单日全市场拉取（等价于 `--trade-date=YYYYMMDD`），并正常落库；传任意 `--start-date`/`--end-date` 或 `--trade-date` 时保持原有按参数执行的行为不变。

- [x] T016 [US4] 在 `scripts/daily/fetch.py` 的 `main()` 中，当未传入 `--start-date`、`--end-date`、`--trade-date` 时，先计算默认 trade_date：调用 `_get_latest_trade_date_from_cal(pro)` 得到“当日或当日最近交易日”（YYYYMMDD）；若得到有效值则设置 `args.trade_date = 该值`，然后走现有 `if getattr(args, "trade_date", None):` 分支，执行 `fetch_by_trade_date(...)` 单日全市场拉取后 return，不再进入按股票列表循环的增量逻辑；若 trade_cal 未返回有效日期则回退为当前“增量 + end_date=latest”的原有逻辑（保持兼容）
- [x] T017 [US4] 更新 `scripts/daily/fetch.py` 顶部模块 docstring 与用法注释：明确说明“无参数时默认拉取当天（或当日最近交易日）全市场日线”，并补充示例 `python scripts/daily/fetch.py` 表示拉取当天

---

## Phase 8: User Story 5 - 统一退出码，消除「退出码 2」(P2)

**Goal**: 数据拉取相关脚本及调度入口统一使用退出码 0（成功）/ 1（失败），不再向 API/前端返回退出码 2，避免用户看到「拉取日线/分钟数据失败 退出码 2」的困惑。

**Independent Test**: 手动或通过前端触发日线/分钟拉取，故意制造失败（如断网、错误 token）；运行记录中的 summary 或状态为 failed 时，不应出现「退出码 2」，应为「退出码 1」或等价失败描述；成功时退出码为 0。

- [x] T018 [US5] 在 `scripts/scheduled_tasks.py` 的 `_run_script` 中，当子进程返回码 `returncode == 2` 时改为返回 `1` 并打 log 说明“子进程返回 2，已规范为 1”，确保调用方（API/前端）仅看到 0 或 1
- [x] T019 [US5] 在 `scripts/minute/scan.py` 中将异常分支的 `return 2` 改为 `return 1`，与项目“失败即 1”的约定一致；在 `scripts/minute/fetch.py` 的 `if __name__ == "__main__"` 中增加与 `scripts/daily/fetch.py` 一致的退出码规范化（捕获 SystemExit(2)→sys.exit(1)，异常→sys.exit(1)，成功→sys.exit(0)），文件路径：`scripts/minute/scan.py`、`scripts/minute/fetch.py`

---

## Phase 9: User Story 6 - 极简日线测试脚本（验证退出码）(P2)

**Goal**: 日线脚本仍出现退出码 2 时，可先通过“极简脚本”验证：子进程调用链与调度入口是否正常返回 0/1，排除 Tushare/DB/业务逻辑干扰。

**Independent Test**: 使用极简脚本作为日线拉取入口时，前端触发“拉取日线”或执行 `python scripts/scheduled_tasks.py fetch_daily --test-simple`，运行记录应为 success、summary 无“退出码 2”；恢复正式脚本后可按需再测。

- [x] T020 [US6] 在 `scripts/daily/` 下新增极简测试脚本 `fetch_daily_simple.py`：内容仅包含 `if __name__ == "__main__": print("daily_fetch_simple_ok"); import sys; sys.exit(0)`，无 Tushare/DB/网络依赖，用于验证“被 scheduled_tasks 或 API 子进程调用时是否返回 0”，文件路径：`scripts/daily/fetch_daily_simple.py`
- [x] T021 [US6] 在 `scripts/scheduled_tasks.py` 的 `cmd_fetch_daily` 中增加可选参数 `--test-simple`：当传入时执行 `scripts/daily/fetch_daily_simple.py` 而非 `scripts/daily/fetch.py`，成功时仍按现有逻辑写入 data_fetch_run 的 success 记录，便于单独验证退出码与写入流程，文件路径：`scripts/scheduled_tasks.py`

---

## Phase 10: User Story 7 - 日线失败时可见错误原因（测试脚本成功但正式日线不成功）(P2)

**Goal**: 当“极简测试脚本成功、正式日线脚本仍不成功”时，能在运行记录或前端看到子进程的真实错误（如 ImportError、Tushare/DB 报错），便于定位是环境、依赖还是业务逻辑问题。

**Independent Test**: 触发拉取日线（正式脚本）并令其失败（如断网、错误 token、缺包）；GET /api/v1/data-fetch/runs/{run_id} 或列表中该条记录的 summary 应包含子进程 stderr 或 stdout 的截断内容（如“ModuleNotFoundError: No module named 'tushare'”），便于排查。

- [x] T022 [US7] 在 `backend/src/api/v1/data_fetch.py` 的 `_run_fetch_task` 中，当 subprocess 返回非 0 时，将 `result.stderr` 与 `result.stdout` 的文本（截断至例如 500 字符）拼入 `summary` 写入 DataFetchRun，便于前端/运维看到“执行日线不成功”时的真实错误，文件路径：`backend/src/api/v1/data_fetch.py`
- [x] T023 [US7] 在 `scripts/daily/fetch.py` 的 `if __name__ == "__main__"` 入口处，在调用 `main()` 前用 `traceback.print_exc()` 或等效方式确保任何未捕获异常在退出前将完整 traceback 打印到 stderr，以便 API 端 capture_output 能捕获并写入运行记录，文件路径：`scripts/daily/fetch.py`

---

## Phase 11: User Story 8 - 数据拉取增加指数拉取 (P2)

**Goal**: 在数据拉取功能中增加“指数日线”拉取入口，对应 `scripts/index/fetch.py`，支持前端手动触发、定时脚本及“今日已执行则跳过”，与日线/分钟拉取一致。

**Independent Test**: 前端点击“拉取指数”后出现 running 记录并最终变为 success/failed；执行 `python scripts/scheduled_tasks.py fetch_index --skip-if-done-today` 时若当日已有 index 成功记录则跳过；GET /runs 可按 task_type=index 筛选。

- [x] T024 [US8] 在 `scripts/scheduled_tasks.py` 中新增子命令 `fetch_index`：执行 `scripts/index/fetch.py`，支持可选参数 `--skip-if-done-today`（检查 data_fetch_run 当日是否已有 task_type=index 的 success 记录），成功时写入一条 task_type=index、trigger=scheduled、status=success 的记录，文件路径：`scripts/scheduled_tasks.py`
- [x] T025 [US8] 在 `backend/src/models/schemas.py` 中将 `DataFetchTriggerRequest` 的 `task_type` 扩展为 `Literal["daily", "minute", "index"]`；在 `backend/src/api/v1/data_fetch.py` 的 `_run_fetch_task` 中当 `task_type == "index"` 时调用 `scripts/scheduled_tasks.py fetch_index`，trigger 接口已支持任意 task_type 传入，文件路径：`backend/src/models/schemas.py`、`backend/src/api/v1/data_fetch.py`
- [x] T026 [US8] 在 `frontend/src/api/dataFetch.ts` 中将 `triggerFetch` 的 `task_type` 类型扩展为 `'daily' | 'minute' | 'index'`；在 `frontend/src/views/DataFetch.vue` 中增加“拉取指数”按钮与 `todayIndexSuccess` 提示，筛选下拉增加“指数”选项，表格中 task_type 显示支持 index→指数，文件路径：`frontend/src/api/dataFetch.ts`、`frontend/src/views/DataFetch.vue`

---

## Phase 12: User Story 9 - 麒麟分析结束时间/最晚数据与缓存修复 (P2)

**Goal**: 修复 POST /api/v1/analysis/czsc 返回的「数据源中最晚数据」滞后于真实数据源的问题。当 K 线来自 KlineStorage（Parquet）且 Parquet 结束日期早于请求 edt 时，从 .stock_data 日线补充缺失区间并合并，使 data_end_dt / effective_edt 与数据源最新一致，避免“请求结束时间为 2026-02-28，但数据源中最晚数据为 2026-02-26”的缓存滞后提示。

**Independent Test**: 在 .stock_data 中已有某标的 2026-02-27 日线、而 data/klines 中该标的 Parquet 仅到 2026-02-26 时，请求 analysis/czsc 的 edt=2026-02-28，返回的 data_end_dt / effective_edt 应为 2026-02-27，data_range_note 不应再出现“数据源中最晚数据为 2026-02-26”。

- [x] T027 [US9] 在 `backend/src/utils/czsc_adapter.py` 的 `get_bars` 中，当日线数据来自 kline_storage 且实际结束日期早于请求 edt 时，尝试从 .stock_data（_get_daily_bars_from_stock_data_impl）拉取 [实际结束日期+1, edt] 区间数据，与现有 bars 按 dt 合并去重排序；若合并后得到更晚的结束日期则使用合并结果，并在 kline_storage 存在时写回 save_bars，确保麒麟分析返回的 data_end_dt / effective_edt 与数据源最新一致，文件路径：`backend/src/utils/czsc_adapter.py`

---

## Dependencies & Execution Order

- **Phase 1**：无依赖，先执行（T001→T002→T003）。
- **Phase 2**：依赖 Phase 1（表已存在）；T004 与 T005 可部分并行，但 T005 依赖“写记录”能力，需在 T004 或等价写库逻辑就绪后联调。
- **Phase 3 (US1)**：依赖 Phase 2（repo 与脚本行为已定）；T006、T007、T008 同属 API，顺序执行。
- **Phase 4 (US2)**：依赖 Phase 2 的 --skip-if-done-today 与写库，可与 Phase 3 并行开发，验收依赖 T005 完善。
- **Phase 5 (US3)**：依赖 Phase 3 的 API；T010、T011 可先做，T012 依赖 T011。
- **Phase 6**：依赖 Phase 3、4、5 完成。
- **Phase 7 (US4)**：仅依赖现有 `scripts/daily/fetch.py` 与 `_get_latest_trade_date_from_cal`、`fetch_by_trade_date`，可与其它 Phase 独立实现，无前置 Phase 强依赖。
- **Phase 8 (US5)**：依赖 Phase 2/3（scheduled_tasks、data_fetch 已存在）；可与 Phase 7 独立实现，仅改脚本退出码与 scheduled_tasks 的 _run_script。
- **Phase 9 (US6)**：依赖 Phase 2/3；T020 与 T021 可顺序执行（先有极简脚本，再在 scheduled_tasks 中接 --test-simple）。
- **Phase 10 (US7)**：依赖 Phase 3（data_fetch API 与 fetch.py）；T022 与 T023 可并行（不同文件）。
- **Phase 11 (US8)**：依赖 Phase 2/3/5；T024 与 T025、T026 可并行（T025 与 T026 依赖 T024 的 scheduled 命令存在后可联调 API 与前端）。
- **Phase 12 (US9)**：依赖现有 analysis/czsc 与 czsc_adapter.get_bars、KlineStorage、.stock_data 日线读取；无前置 Phase 强依赖，可与其它 Phase 独立实现。

### Parallel Opportunities

- T001 与 T002 可并行；T004 与 T005 中“写记录”以外的逻辑可并行；T010 与 T011 可并行；T016 与 T017 同文件需顺序执行。

---

## Implementation Strategy

### MVP

1. Phase 1 + Phase 2：表、repo、脚本 --skip-if-done-today 与成功写库。
2. Phase 3：POST trigger + GET runs，后台子进程执行脚本并更新状态。
3. Phase 5（T010+T011+T012+T013）：前端一页完成手动触发与列表展示；“今日已执行”提示依赖 GET runs 的 date 筛选。

### 验收要点

- **数据库**：data_fetch_run 表可记录每次拉取任务类型、触发方式、时间、状态、摘要。
- **手动触发**：前端点击“拉取日线/分钟”后，后端创建 running 记录并启动脚本，脚本结束后更新为 success/failed；前端可查看列表与状态。
- **定时跳过**：cron 使用 `--skip-if-done-today` 时，若当日已有同类型 success 记录则不再执行拉取并 exit(0)。
- **脚本对应**：daily 对应 `scripts/daily/fetch.py`；minute 对应 `scripts/minute/fetch.py`（若 T014 中确认为 fetch.py 而非 scan.py）。
- **默认当天**：无参数执行 `python scripts/daily/fetch.py` 时，默认拉取当天（或当日最近交易日）全市场日线。
- **退出码统一**：拉取脚本及 scheduled_tasks 仅返回 0/1，不向 API 暴露退出码 2。
- **极简测试**：可通过 `--test-simple` 或极简脚本单独验证日线调用链与退出码，再排查正式脚本。
- **失败可观测**：日线/分钟拉取失败时，运行记录 summary 中可看到子进程 stderr/stdout 截断，便于排查“测试脚本成功但正式日线不成功”。
- **指数拉取**：数据拉取支持 task_type=index，对应 `scripts/index/fetch.py`，前端可触发“拉取指数”，定时可配置 fetch_index 及 --skip-if-done-today。
- **麒麟分析结束时间**：analysis/czsc 在日线来自 KlineStorage 且结束日期早于请求 edt 时，从 .stock_data 补充并合并，使返回的 data_end_dt / 最晚数据 与数据源一致，避免缓存滞后。

---

## 格式自检

- 所有任务均为 `- [ ] [TaskID] [P?] [Story?] 描述（含文件路径）`。
- US1: T006、T007、T008；US2: T009；US3: T010、T011、T012、T013；US4: T016、T017；US5: T018、T019；US6: T020、T021；US7: T022、T023；US8: T024、T025、T026；US9: T027；Setup/Foundational/Polish 无 Story 标签。
