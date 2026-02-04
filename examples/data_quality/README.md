# 数据质量示例（分钟缺口）

本目录提供“分钟缺口报告导出”的最小示例，用于把 MySQL 中的 `stock_minute_gaps`（或你自定义表名）导出为 CSV，方便人工审查与补数。

## 前置条件

- 已完成 MySQL 表初始化：`python scripts/db_init_mysql.py`
- 已运行缺口生成脚本（计划中）：`python scripts/stock_minute_check.py ...`
- 已在环境变量中配置 MySQL 连接（可选，默认见 `backend/src/utils/settings.py`）：
  - `CZSC_MYSQL_HOST`
  - `CZSC_MYSQL_PORT`
  - `CZSC_MYSQL_USER`
  - `CZSC_MYSQL_PASSWORD`
  - `CZSC_MYSQL_DATABASE`

## 导出缺口报告

```bash
python examples/data_quality/minute_gap_report.py --sdt 2024-01-01 --edt 2024-01-31 --out gaps.csv
```

导出字段：

- `symbol`：股票代码
- `trade_date`：交易日
- `gap_start/gap_end`：缺口区间（半开区间 [start, end)）
- `gap_minutes`：缺口分钟数
- `details`：缺口定位信息（可选）

