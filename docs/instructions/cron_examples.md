# 定时任务示例（数据维护与筛选）

本页给出两类常见环境的“定时运行入口”示例，包括：MySQL 表结构初始化、日线/分钟数据拉取、分钟覆盖扫描、以及信号/因子筛选任务。

## 1. Linux / macOS（cron）

### 1.1 统一入口：scheduled_tasks.py（推荐）

项目提供统一入口 `scripts/scheduled_tasks.py`，子命令如下：

| 子命令 | 说明 |
|--------|------|
| `init` | 初始化/升级 MySQL 表结构（等价于 db_init_mysql.py） |
| `fetch_daily` | 拉取日线数据（调用 scripts/daily/fetch.py） |
| `fetch_minute` | 扫描分钟数据覆盖并更新 coverage 表（调用 scripts/minute/scan.py） |
| `fetch_minute_data` | 拉取分钟 K 线数据（调用 scripts/minute/fetch.py） |
| `run_screen` | 执行信号/因子筛选，结果写入 screen_result 表 |

**推荐：使用 `--skip-if-done-today` 避免重复拉取**  
若当天已通过前端手动触发或此前 cron 已成功执行过同类型任务，可加 `--skip-if-done-today`，脚本会先查 `data_fetch_run` 表，若当日已有同类型 success 记录则直接退出 0 并输出“今日已执行过 xxx，跳过”，不执行实际拉取。

推荐 cron 示例（每日 17:00，若当日已拉取过则跳过；请将 `/path/to/npc-czsc` 改为实际项目根目录）：

```cron
0 17 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py fetch_daily --skip-if-done-today >> logs/cron_daily.log 2>&1
0 17 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py fetch_minute_data --skip-if-done-today >> logs/cron_minute.log 2>&1
```

不带跳过时（每次均执行，适用于强制补数）示例（16:30 起）：

```cron
30 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py init >> logs/cron_init.log 2>&1
35 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py fetch_daily >> logs/cron_daily.log 2>&1
45 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py fetch_minute --market SH,SZ >> logs/cron_minute.log 2>&1
55 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/scheduled_tasks.py run_screen --trade-date $(date +\\%Y\\%m\\%d) --market SH,SZ >> logs/cron_screen.log 2>&1
```

环境变量（可选）：在项目根目录或 `backend/.env` 中配置 `CZSC_MYSQL_*`、`DATA_PATH` 等，参见 `backend/src/utils/settings.py`。

### 1.2 单独脚本方式（分钟数据维护）

若希望沿用原有脚本路径，可参考：

```cron
30 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/db_init_mysql.py >> logs/cron_db_init.log 2>&1
35 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/minute/scan.py --market SH,SZ >> logs/cron_scan.log 2>&1
55 16 * * 1-5 cd /path/to/npc-czsc && /usr/bin/python scripts/minute/check.py --date $(date +\\%F) --market SH,SZ >> logs/cron_check.log 2>&1
```

> 注意：A股存在节假日与调休，cron 的“周一到周五”并不等于交易日。  
> 若需严格只在交易日执行，建议在脚本内用交易日历判断（后续可增强）。

## 2. Windows（任务计划程序）

### 2.1 每天固定时间运行

- 打开“任务计划程序”
- 创建基本任务 → 触发器选择“每天” → 操作选择“启动程序”
- 程序/脚本：`python`
- 参数：`scripts/scheduled_tasks.py fetch_minute --market SH,SZ`（或 `init` / `fetch_daily` / `run_screen`）
- 起始于：项目根目录

建议拆成多个任务（init、fetch_daily、fetch_minute、run_screen），便于失败重跑与定位。

