# 数据维护脚本说明

本目录用于存放“数据拉取/导入/扫描/校验/导出”等脚本。

## 约定

- 所有脚本都应支持 `--help` 输出参数说明
- 脚本执行过程中使用 `loguru` 输出关键日志
- 对可能耗时的扫描/校验任务，建议输出耗时与处理行数

## 规划中的数据质量脚本（分钟级）

以下脚本将用于维护“分钟数据是否完整、每只股票起止时间、缺口在哪”的闭环：

- `scripts/db_init_mysql.py`：初始化/升级 MySQL 表结构（幂等）
- `scripts/stock_basic_import.py`：从 CSV 导入/更新股票主数据（含中文名）
- `scripts/stock_basic_from_minute_table.py`：从分钟明细表反推 symbol 列表并补齐市场字段
- `scripts/stock_minute_scan.py`：扫描每只股票分钟数据起止时间，写入 coverage 表
- `scripts/stock_minute_scan_daily.py`：按交易日统计分钟条数，写入 daily_stats 表
- `scripts/stock_minute_check.py`：按日完整性校验并定位缺口区间，写入 gaps 表
- `scripts/stock_minute_cli.py`：统一入口（scan/check/report）

> 这些脚本的实现任务清单见：`specs/001-czsc-api-ui/tasks.md`

