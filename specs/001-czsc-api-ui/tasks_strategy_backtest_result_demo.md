# Tasks: 策略增加回测结果（对齐 strategy_demo 展示）

**Input**: 策略分析页回测结果与 `demo/step4-strategies/strategy_demo.py`（56-78 行）一致：按持仓展示操作次数、最近操作（dt、op、bid、price）、评估（pos.evaluate()）。

**Path Conventions**: 后端 `backend/src/`，前端 `frontend/src/`。

**现状简述**:
- 已有 POST /backtest/run-by-strategy 返回 pairs、operates、positions；operates 为扁平日志，未含 bid，op 为枚举字符串。
- 前端策略分析页统一展示「绩效摘要 JSON + 操作表格」，未按持仓分块、未展示操作次数与评估结构。
- Demo 展示：`【持仓名】`、`操作次数: N`、最近 5 条 `dt  op.value  bid  price`、`评估: pos.evaluate()`。

---

## Phase 1: 后端回测结果对齐 demo（operates 含 bid、op 可读）

**Purpose**: 序列化 operates 时增加 bid；op 输出为可读枚举值（如 LO/LE/SO/SE）；可选在响应中按持仓汇总（每持仓：操作次数、最近 N 条、evaluate）。

**Independent Test**: 调用 POST /backtest/run-by-strategy 后，响应中每条 operate 含 dt、op（如 "LO"/"LE"）、bid、price；或新增按持仓汇总结构（pos_name、operate_count、last_operates、evaluate）可供前端直接渲染。

- [x] T001 在 `backend/src/services/backtest_service.py` 的 `_serialize_operates` 中，对 dict 型 op 增加 `bid` 字段（op.get('bid')），并统一 `op` 为可读枚举值：若为 czsc Operate 枚举则取 `.name` 或 `.value` 的短名（如 LO/LE/SO/SE），否则保持 str（`backend/src/services/backtest_service.py`）
- [x] T002 在 `backend/src/services/backtest_service.py` 中新增按持仓汇总结构：在 `run_backtest_by_strategy` 返回中增加 `positions_summary`（或复用/扩展 pairs），每项含 `pos_name`、`operate_count`、`last_operates`（最近 5 条，含 dt、op、bid、price）、`evaluate`（即当前 pairs[pos_name] 的 多空合并/多头/空头），便于前端按 demo 分块展示（`backend/src/services/backtest_service.py`）

---

## Phase 2: 前端策略分析页按持仓展示回测结果（对齐 demo）

**Purpose**: 回测结果区按「持仓」分块展示：持仓名、操作次数、最近几条操作（表格式：时间、操作、bid、价格）、评估（多空合并/多头/空头 结构化展示）。

**Independent Test**: 在策略分析页运行分析后，结果区展示每个持仓的【持仓名】、操作次数、最近 5 条操作（时间、op、bid、price）、评估内容，与 strategy_demo.py 控制台输出一致。

- [x] T003 在 `frontend/src/api/backtest.ts` 的 `BacktestResponse` 类型中增加 `positions_summary`（可选）：每项含 `pos_name`、`operate_count`、`last_operates`、`evaluate`；operates 表单项类型增加 `bid`（`frontend/src/api/backtest.ts`）
- [x] T004 在 `frontend/src/views/StrategyAnalyze.vue` 回测结果区：若有 `positions_summary` 则按持仓分块展示（标题【持仓名】、操作次数、最近 N 条操作表格含 dt/op/bid/price、评估折叠或表格）；否则降级为当前「绩效 JSON + 全量 operates 表」（`frontend/src/views/StrategyAnalyze.vue`）

---

## Phase 3: 收尾

**Purpose**: 文档与一致性。

- [x] T005 在 `backend/README.md` 或策略分析相关文档中注明回测结果结构：operates 含 dt/op/bid/price、positions_summary 含 operate_count/last_operates/evaluate（`backend/README.md` 或 `docs/`）

---

## Dependencies & Execution Order

- **Phase 1**：T001 → T002（T002 依赖 T001 的 operates 结构）。
- **Phase 2**：T003 → T004，依赖 Phase 1 的 API 结构。
- **Phase 3**：T005 在 Phase 1/2 完成后执行。

---

## 格式校验

- 所有任务满足：`- [ ]` + TaskID + 描述 + 文件路径。
