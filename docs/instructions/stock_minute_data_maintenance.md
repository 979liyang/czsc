# 本地股票分钟数据维护方案（Python + MySQL）

本文档面向“本地维护上证/深证分钟数据”的场景，目标是让你可以稳定回答三类问题：

1. **数据是否完整**：某股票某天分钟数据是否缺失？缺口在哪些时间段？
2. **股票中文名是什么**：本地数据对应的股票中文名如何维护与更新？
3. **数据起止时间**：每只股票本地分钟数据的开始时间与结束时间是什么？

> 约定：分钟数据以 **MySQL** 为中心（查询与统计更快、更一致），脚本负责“扫描/统计/产出报告/写回结果表”。  
> 你也可以继续使用本地 parquet 作为“归档层”，但完整性判断建议以 MySQL 的“分钟明细表”或“日统计表”为准。

---

## 1. 数据分层与表设计（建议）

### 1.1 核心表（建议 4+1 张）

- `stock_basic`：股票主数据（代码、中文名、市场、上市/退市日期等）
- `stock_minute_bars`：分钟K线明细（你已维护的分钟数据，含 dt 字段）
- `stock_minute_coverage`：每只股票分钟数据覆盖概况（start_dt/end_dt/统计时间等）
- `stock_minute_daily_stats`：按交易日的分钟条数统计（actual_count）
- `stock_minute_gaps`：缺口明细（缺口区间、缺口分钟数、定位信息）

> 表名与字段会由后端配置集中管理：`backend/src/utils/settings.py`（前缀 `CZSC_`）。

---

## 2. 维护流程（每日增量）

### 2.1 建议的日常流程（最小闭环）

1. **入库/更新分钟明细**：把当日新增分钟数据写入 `stock_minute_bars`
2. **扫描起止时间**：更新 `stock_minute_coverage`（每只股票 min/max(dt)）
3. **按日统计分钟条数**：更新 `stock_minute_daily_stats`
4. **完整性检查**：对“当天”或“最近 N 天”计算 expected vs actual，生成 `stock_minute_gaps`
5. **出报告 + 补数**：根据 gaps 报告补齐缺口（重新拉取/重新导入）
6. **复查**：补数后重新跑检查，确保 gaps 收敛为 0

---

## 3. 如何判断“完整”（分钟维度）

### 3.1 期望分钟数（expected_count）

以 A 股常规交易时段为例：

- 上午：09:30-11:30
- 下午：13:00-15:00

期望分钟数的计算依赖：

- 交易时段（含午休切分）：配置在 `CZSC_TRADING_SESSIONS`
- 交易日历：需要知道某天是否交易日（可用现有交易日历文件/或你自己的交易日列表）

### 3.2 实际分钟数（actual_count）

从 `stock_minute_bars` 按 `symbol + trading_date` 聚合得到。

### 3.3 缺口区间定位（gap_ranges）

缺口不是只有“少了多少条”，更重要的是：

- 哪些分钟缺失（连续缺失 → 区间）
- 是否跨越午休、是否在开盘/收盘附近

这些信息用于指导补数策略（例如只补某天某段）。

---

## 4. 股票中文名如何维护

### 4.1 推荐：以 `stock_basic` 为准

- 通过 CSV 导入（一次性全量 + 后续增量更新）
- 也可以从你现有分钟表中反推 symbol 列表，然后用外部数据源补齐 name（如果你有）。

CSV 建议字段：

```text
symbol,name,market,list_date,delist_date
000001.SZ,平安银行,SZ,19910403,
600000.SH,浦发银行,SH,19991110,
```

导入脚本将在 `scripts/stock_basic_import.py` 实现（upsert）。

---

## 5. 输出与使用方式（你最终会得到什么）

当脚本体系跑通后，你会得到：

- **每只股票**：分钟数据 `start_dt / end_dt`（来自 coverage）
- **每只股票每交易日**：实际分钟条数 `actual_count`（来自 daily_stats）
- **每只股票每交易日**：缺口区间列表（来自 gaps）

这三类结果可以：

- 直接在 MySQL 用 SQL 查询
- 通过后端 API 查询（用于前端“数据质量”页面）
- 导出 CSV 做人工审查

### 5.1 API / 页面入口（MVP）

- **覆盖概况 API**：`GET /api/v1/data/coverage?market=SH&offset=0&limit=200`
- **缺口查询 API**：`GET /api/v1/data/gaps?symbol=000001.SZ&trade_date=2024-01-04`
- **前端页面**：`/data-quality`（覆盖概况列表 + 单日缺口查询）

---

## 6. 运行入口（规划）

后续脚本会提供统一入口：

- `python scripts/stock_minute_scan.py ...`：扫描 coverage
- `python scripts/stock_minute_scan_daily.py ...`：生成 daily_stats
- `python scripts/stock_minute_check.py ...`：生成 gaps
- `python scripts/stock_minute_cli.py ...`：统一命令（scan/check/report）

### 6.1 推荐的每日维护命令（MVP）

```bash
# 1) 初始化表（首次/升级时执行）
python scripts/db_init_mysql.py

# 2) 扫描覆盖概况（start/end）
python scripts/stock_minute_cli.py scan --market SH,SZ

# 3) 生成日统计（actual/expected）
python scripts/stock_minute_cli.py daily --sdt 2024-01-01 --edt 2024-01-31 --market SH,SZ

# 4) 生成缺口区间（gaps）
python scripts/stock_minute_cli.py check --sdt 2024-01-01 --edt 2024-01-31 --market SH,SZ
```

---

## 7. 常见问题

### 7.1 我的数据不是 1 分钟，是 5 分钟怎么办？

完整性检查的“期望分钟数”需要适配你的粒度（5 分钟则 expected_count 会更小）。建议先把数据粒度统一到 1 分钟（最通用），否则需要在检查算法里做粒度换算。

### 7.2 有些股票停牌会导致缺口，这是“缺失”吗？

技术上它仍是“分钟缺口”，但业务上可能合理。建议 gaps 表里增加 `reason` 或 `tag`（例如停牌/熔断/临停），后续可引入停牌日历来过滤。

