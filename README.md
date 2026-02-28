## 项目概述

### 什么是 CZSC？

CZSC（缠中说禅）是一个基于缠论技术分析理论的 Python 量化交易工具库。它实现了缠论中的核心概念，包括：

- **分型识别**：自动识别顶分型和底分型
- **笔识别**：基于分型自动识别笔
- **中枢识别**：识别价格震荡区间
- **多级别联立分析**：支持多个时间周期的联合分析
- **信号系统**：基于缠论结构生成交易信号
- **策略回测**：完整的策略回测框架

### 项目特点

- ✅ 完整的缠论技术分析实现
- ✅ 支持多数据源（Tushare、聚宽、米筐、QMT等）
- ✅ 灵活的信号和策略系统
- ✅ 丰富的可视化工具
- ✅ 完善的回测框架
- ✅ 活跃的社区支持

### token账号

13029727256
15114579671Ly

# 后端backend

## 从项目根目录运行
./backend/install.sh

## 1. 激活虚拟环境（从项目根目录）
source venv/bin/activate

## 2. 进入 backend 目录并安装依赖
cd backend
pip install -r requirements.txt

## 3. 运行服务
python run.py

## 4. 环境变量（可选）

- `DATA_PATH`: 数据根目录，默认 `data`；K 线在 `data/klines`，元数据在 `data/metadata`
- `CZSC_MYSQL_*`: MySQL 连接（host/port/user/password/database），见 `backend/src/utils/settings.py`
- `CZSC_JWT_SECRET`: JWT 密钥（生产环境务必修改）
- `LOG_LEVEL`: 日志级别，如 `INFO` / `DEBUG`

## 5. API 使用说明

- 基础 URL：`http://localhost:8000/api/v1`
- 文档：`http://localhost:8000/docs`
- 需登录接口：请求头携带 `Authorization: Bearer <token>`（登录后返回的 access_token）
- 主要接口：GET /bars（K 线）、POST /analysis/czsc（缠论分析）、GET /signals/calculate、POST /backtest/run、GET /symbols、GET /docs/signals、GET /auth/me（当前用户与积分档位）、GET/POST/DELETE /my_singles（收藏）、POST /screen/run、GET /screen/results（全盘扫描）
- **信号分析**：前端「信号分析」页（/signal-analyze）可按类型添加多信号、支持每信号不同周期，对单只股票执行分析（POST /signals/batch）；默认时间半年前至今。
- **全盘扫描**：前端「全盘扫描」页（/screen）可选择交易日与任务类型（按信号/按因子），触发 POST /screen/run 执行扫描，通过 GET /screen/results 查看结果列表。

## 6. 数据质量与清理

- K 线数据质量校验：后端 `KlineStorage.validate_data_quality(symbol, freq)` 可检查单只股票单周期的完整性、价格有效性等
- 旧数据清理：`KlineStorage.cleanup_old_data(before_date, dry_run=True)` 可预览或清理指定日期之前的 parquet 文件
- 用户与积分权限表结构升级：先运行 `python scripts/db_init_mysql.py` 创建新表，再运行 `python scripts/migrate_user_points_permission.py` 为 user 表添加扩展列

## 7. 信号函数入库（czsc.signals → signal_func 表）

- **表结构**：`signal_func` 表存信号函数元数据（name、module_path、category、param_template、description、is_active），与 `backend/src/models/mysql_models.py` 中 SignalFunc 一致；由 `python scripts/db_init_mysql.py` 创建。
- **全量同步**：在项目根目录激活 venv 后执行  
  `python scripts/sync_czsc_signals_to_db.py`  
  会从 `czsc.signals` 枚举全部信号并 upsert 到 `signal_func` 表。可选 `--dry-run` 仅打印不写库，`--signals-module` 可指定模块名（默认 `czsc.signals`）。
- **与 API 关系**：GET /api/v1/docs/signals 当前由 DocService 实时从 czsc.signals 读取；同步后筛选任务等可从库中按 is_active=1 读取 signal_func 列表。

## 8. 学习与文档

- **学习 CZSC / 因子与策略**：[docs/learning/czsc_factors_and_strategies.md](docs/learning/czsc_factors_and_strategies.md)（因子与策略在 CZSC 及本项目中的对应表与接口）
- **信号配置与因子库 / 数据库入库顺序**：[docs/signals_and_factors.md](docs/signals_and_factors.md)（signals_config、factor_def、my_singles 表与入库脚本顺序）

# czsc安装安装运行

## 卸载

```
venv/bin/pip uninstall czsc -y
venv/bin/pip install -e .
```
## 安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# czsc安装
pip install --upgrade pip setuptools wheel
cp setup_fixed.py setup.py && pip install -e .

# rs_czsc 安装

pip install rs_czsc
```

### 2. 安装依赖

主要依赖已包含在 requirements.txt 中，安装时会自动安装。如需手动安装：

```bash
pip install -r requirements.txt
```

### 3. 环境配置

#### 日志配置
CZSC 使用 `loguru` 进行日志记录，默认会输出到控制台。可以通过环境变量配置：

```python
import os
os.environ['CZSC_LOG_LEVEL'] = 'INFO'  # DEBUG, INFO, WARNING, ERROR
```

#### 后端安装方案

```python
# 方案 A（推荐）：安装后端依赖
pip install -r backend/requirements.txt

# 方案 B：如果你用虚拟环境，先激活再装
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

#### 缓存配置
CZSC 使用本地缓存存储数据，默认路径在用户主目录下的 `.czsc` 文件夹：

```python
from czsc.utils import home_path
print(home_path)  # 查看缓存路径

# 清空缓存
from czsc.utils import empty_cache_path
empty_cache_path()
```

#### 数据源配置

**Tushare 配置**：
```python
# 在 tushare_config.json 中配置
{
    "token": "your_tushare_token",
    "pro_api": "https://api.tushare.pro"
}
```

**其他数据源**：根据具体连接器文档配置相应的 API Key 或连接信息。

## 存储的数据格式

```python
      symbol                  dt         open        close         high          low        vol      amount
0  000001.SH 2010-01-04 09:31:00  3292.049072  3293.325928  3295.279053  3292.049072  203927696  2358753536
```

## 前端使用

https://github.com/tvjsx/trading-vue-js?tab=readme-ov-file

### 指数
symbols/SSE-000001/

### 指标 

- 收藏
- 我的脚本

### 技术指标

#### 指标

#### 策略

### 形态

### 从某个股票之后开始跑数据
python scripts/fetch_tushare_minute_data_stk_mins.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-01-31 19:00:00" --resume-after 000615.SZ

### 另外如果你想用自动断点续跑
python scripts/fetch_tushare_minute_data_stk_mins.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-01-31 19:00:00" --checkpoint


sz	深圳证券交易所
000001-004999（主板）
300000-309999（创业板）
002000-002999（中小板）


sh	上海证券交易所	
600000-603999（主板）
605000-605999（主板）
688000-688999（科创板）




后端
Charting Library 静态托管：后端直接挂载 frontend/charting_library/ 到 /charting_library/*，避免前端复制大量文件（backend/src/main.py）。
UDF(Datafeed) 接口：新增 backend/src/api/v1/tradingview.py，并在 backend/src/main.py 注册，提供：
GET /api/v1/tv/config
GET /api/v1/tv/search
GET /api/v1/tv/symbols
GET /api/v1/tv/history（优先日线 parquet，否则分钟合成；带简单 TTL 缓存）
GET /api/v1/tv/time
SMC 指标接口：新增 backend/src/api/v1/indicators.py
GET /api/v1/indicators/smc 返回 areas/events（复用 czsc/indicators/smart_money.py）
前端
新增页面 /tv：frontend/src/views/TradingViewChart.vue
新增组件：frontend/src/components/TradingViewWidget.vue（加载 /charting_library/charting_library.js 并创建 widget）
新增 datafeed：frontend/src/tv/udfDatafeed.ts（对接后端 /api/v1/tv/*）
新增 SMC 覆盖绘制：frontend/src/tv/smcOverlay.ts（用 Drawings API 画 rectangle/text，并支持清理旧图形）
路由：frontend/src/router/routes.ts 添加 /tv
首页入口：frontend/src/views/Home.vue 添加 “TradingView 图表” 卡片
Vite 代理：frontend/vite.config.ts 增加 /charting_library -> http://localhost:8000

docs/tradingview_datafeed.md
docs/tradingview_quickstart.md
docs/smc_mapping.md
docs/charting_library_custom_studies.md（明确：不能直接执行 Pine v5 源码，推荐当前“后端计算+前端叠加”）




1天1分钟数据
5天返回5分钟数据
1个月返回30分钟数据
3个月返回1小时数据
半年返回2小时数据
1年返回日数据
5年返回周数据


1分钟每次返回1天的数据
5分钟每次返回5天的数据
30分钟每次返回1个月的数据
1个小时每次返回三个月的数据
2个小时每次返回6个月数据
日数据每次返回1年数据
周数据每次返回5年数据




后缀说明
后缀	代表含义	适用指数类型	示例
.SH	上海证券交易所	上证系列、中证系列（沪市代码）	000300.SH（沪深300）
.SZ	深圳证券交易所	深证系列、国证系列	399006.SZ（创业板指）
.CSI	中证指数有限公司	中证系列指数（统一代码）	930050.CSI（中证A50）
.HK	香港交易所	恒生系列指数	HSTECH.HK（恒生科技）
.CFETS	中国外汇交易中心	债券指数	-
.NQ	全国股转系统	新三板指数	-


# 表设计

## users
用户表

- 昵称
- 签名
- 手机号
- 邮箱
- 积分
- 特殊权限列表(独立开通)
- 可以收藏my_singles
- 身份（管理员和用户）

## 用户积分权限表

- 2000积分：基础功能
- 5000积分：高级功能
- 10000积分：高级功能+特色服务

# 特殊权限

- 名称
- 描述

## signals 
存储所有基本信号

如下是我的一些描述和要求

- 名称
- 描述
- 创建时间
- 创建人
- 状态（启用、禁用）
- 已发布、未发布
- 版本
- 参数说明
- 脚本内容
- 脚本执行结果结构
- 历史脚本和当前版本
- 权限，根据不同积分权限展示不同信号
- 类型（bar / cxt / coo / byi / vol / jcc / tas / cat / pos / zdy / up_dw / xl / stock / other）
- 参考 czsc.singals.md 把所有demo都入库

## signals_config

配置信号，基本信号的入参

如下：
[
    {
        "name": "czsc.signals.tas_ma_base_V230313",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 40,
        "max_overlap": 5,
    },
    {"name": "czsc.signals.cxt_five_bi_V230619", "freq": "日线", "di": 1},
]

- 参考 czsc.singals.md 把所有demo都入库

# scripts 

脚本

- 名称
- 描述
- 是否是定时任务
- 执行时间
- 执行周期
- 执行结果
- 执行完成后触发其他脚本
- 前端可以看到这些脚本



# signal_func 

表记录所有信号，增加入参和出参说明，及