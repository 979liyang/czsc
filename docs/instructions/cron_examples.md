# 定时任务示例（分钟数据维护）

本页给出两类常见环境的“定时运行入口”示例，帮助你把分钟数据维护变成固定流程。

## 1. Linux / macOS（cron）

### 1.1 每天收盘后扫描 coverage + daily_stats + gaps

编辑 crontab：

```bash
crontab -e
```

添加（示例：每个交易日 16:30 执行，日志重定向到文件）：

```cron
30 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/db_init_mysql.py >> logs/cron_db_init.log 2>&1
35 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/stock_minute_scan.py --market SH,SZ >> logs/cron_scan.log 2>&1
45 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/stock_minute_scan_daily.py --sdt $(date +\\%F) --edt $(date +\\%F) --market SH,SZ >> logs/cron_daily.log 2>&1
55 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/stock_minute_check.py --date $(date +\\%F) --market SH,SZ >> logs/cron_check.log 2>&1
```

> 注意：A股存在节假日与调休，cron 的“周一到周五”并不等于交易日。  
> 如果你希望严格只在交易日执行，建议用脚本内部交易日历判断（后续可增强）。

## 2. Windows（任务计划程序）

### 2.1 每天固定时间运行

- 打开“任务计划程序”
- 创建基本任务 → 触发器选择“每天” → 操作选择“启动程序”
- 程序/脚本：`python`
- 参数：`scripts/stock_minute_cli.py scan --market SH,SZ`
- 起始于：项目根目录

建议拆成 3 个任务（scan / daily / check），便于失败重跑与定位。

