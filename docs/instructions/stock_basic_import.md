# 股票主数据导入（中文名维护）

本项目建议把“股票中文名/市场/上市退市信息”等主数据统一维护在 MySQL 的 `stock_basic` 表中，作为后续 API 与数据质量统计的**唯一真相**。

## 1. CSV 格式约定

建议 CSV 至少包含以下列（表头必须存在）：

```text
symbol,name,market,list_date,delist_date
```

字段说明：

- `symbol`：股票代码，建议统一为 `000001.SZ / 600000.SH`
- `name`：中文名（可为空）
- `market`：`SZ` 或 `SH`（可为空）
- `list_date`：上市日期 `YYYYMMDD`（可为空）
- `delist_date`：退市日期 `YYYYMMDD`（可为空）

示例：

```text
symbol,name,market,list_date,delist_date
000001.SZ,平安银行,SZ,19910403,
600000.SH,浦发银行,SH,19991110,
```

## 2. 导入方式

1. 初始化表结构（幂等）：

```bash
python scripts/db_init_mysql.py
```

2. 导入 CSV（upsert，不会重复插入）：

```bash
python scripts/stock_basic_import.py --csv /path/to/stock_basic.csv
```

## 3. 从 Tushare 获取上证/深证股票基本数据（生成 CSV 并可选入库）

如果你没有现成的 `stock_basic.csv`，可以直接使用项目自带脚本从 Tushare 拉取上证/深证的股票基本信息（含中文名、上市/退市日期）：

1. 只生成 CSV（推荐先检查内容）：

```bash
python scripts/fetch_tushare_stock_basic.py --out-csv .stock_data/metadata/stock_basic.csv
```

2. 生成 CSV 并写入 MySQL（需要已配置 `CZSC_MYSQL_*`，且已执行过 `db_init_mysql.py`）：

```bash
python scripts/fetch_tushare_stock_basic.py --to-mysql
```

说明：

- 默认拉取范围：`exchange=SSE,SZSE`，`list_status=L`（仅在市）
- 你也可以只拉取上证/深证：

```bash
python scripts/fetch_tushare_stock_basic.py --exchange SSE
python scripts/fetch_tushare_stock_basic.py --exchange SZSE
```

## 4. 扩展字段（全量保存到 CSV 与 MySQL）

`fetch_tushare_stock_basic.py` 支持拉取并保存**全量字段**：

- **stock_basic**：symbol, name, market, list_date, delist_date, area, industry, fullname, enname, cnspell, exchange, curr_type, list_status, is_hs, act_name, act_ent_type
- **daily_basic**（默认拉取最近交易日）：trade_date, close, turnover_rate, pe, pe_ttm, pb, ps, total_mv, circ_mv 等

一键拉取并写入本地 CSV + MySQL：

```bash
python scripts/fetch_tushare_stock_basic.py --with-daily-basic --to-mysql
```

若 MySQL 表 `stock_basic` 为旧版（仅 5 列），需先做**表结构升级**（增加扩展列），再执行上述命令或 `stock_basic_import.py`。新部署可直接执行 `db_init_mysql.py` 建表（模型已含全字段）。

## 5. 更新策略建议

- **全量导入**：首次建设时，用一份尽可能完整的股票列表（含历史退市）
- **增量更新**：每周或每月导入一次最新列表（upsert 会覆盖 name/market/list_date 等字段）
- **字段缺失**：如果 `market` 缺失，可先用分钟表反推（见 `scripts/stock_basic_from_minute_table.py`）

