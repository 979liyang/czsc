# CZSC API 后端

基于FastAPI的CZSC缠论分析API服务。支持用户登录与自选股，业务接口需认证后访问。

**认证与自选股**：详见项目根目录 `docs/auth_and_watchlist.md`。需先创建 `user`、`watchlist` 表（见该文档），并可选配置 `CZSC_JWT_SECRET` 等环境变量。

## 项目结构

```
backend/
├── src/
│   ├── api/                    # API路由层
│   │   ├── v1/                 # API v1版本
│   │   └── dependencies.py     # API依赖
│   ├── services/               # 业务逻辑层
│   ├── storage/                # 数据存储层
│   ├── models/                 # 数据模型
│   ├── utils/                  # 工具函数
│   └── main.py                 # FastAPI应用入口
├── tests/                      # 测试代码
├── requirements.txt            # 依赖列表
└── README.md                   # 本文档
```

## 安装

### 方式1：使用安装脚本（推荐，最简单）

```bash
# 从项目根目录运行
./backend/install.sh
```

### 方式2：手动安装

项目根目录已有 `venv` 虚拟环境，需要先激活：

```bash
# 从项目根目录激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 然后进入 backend 目录安装依赖
cd backend
pip install -r requirements.txt
```

### 方式3：如果没有虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
cd backend
pip install -r requirements.txt
```

## 运行

**重要：运行前请确保已激活虚拟环境！**

```bash
# 激活虚拟环境（从项目根目录）
source venv/bin/activate

# 方式1：使用启动脚本（推荐，从任何目录都可以运行）
cd backend
python run.py

# 方式2：直接运行 main.py（需要在 backend 目录下）
cd backend
python src/main.py

# 方式3：使用 uvicorn 命令（需要在 backend 目录下）
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 麒麟分析接口（POST /api/v1/analysis/czsc）数据来源

`POST /api/v1/analysis/czsc` 使用的 K 线数据按以下优先级获取（每次请求均按当前 sdt/edt 拉取，无按 symbol+freq 的响应缓存）：

1. **data/klines（Parquet）**：若配置了 KlineStorage，优先从 `data/klines/{symbol}/{freq}` 的 Parquet 按 sdt/edt 过滤加载。
2. **connector**：Parquet 无数据时，通过 `research.get_raw_bars(symbol, freq, sdt, edt)` 拉取，拉取成功后会回写 Parquet。
3. **日线回退 .stock_data**：仅当周期为日线时：
   - 若 Parquet 无数据，会从 `.stock_data/raw/daily/by_stock` 读取（与本地 CZSC / TradingView 同源），有数据则回写 Parquet。
   - **日线覆盖不足时**：若 Parquet 有数据但首条 K 线日期晚于请求 sdt（例如上次只拉过较晚区间），会再尝试从 `.stock_data/raw/daily/by_stock` 拉取 [sdt, edt]；若 .stock_data 能提供更早的起始日期，则以其为准并回写 Parquet，保证「下次搜索更早时间」能用到本地更早数据。

后端日志中会标明本次使用的数据来源：`kline_storage` / `connector` / `stock_data` / `stock_data_merge`，便于排障。

## 本地数据（.stock_data）多周期缠论分析接口

当你已用采集脚本把分钟数据保存到项目根目录的 `.stock_data/raw/minute_by_stock/` 后，可以通过以下接口直接做本地多周期分析（支持 1/5/15/30/60 分钟，可选日线）：

- `GET /api/v1/stock/{symbol}/local_czsc`
  - Query:
    - `sdt`: 开始日期，默认 `20180101`
    - `edt`: 结束日期，默认今天
    - `freqs`: 分钟周期列表（逗号分隔），默认 `1,5,15,30,60`
    - `include_daily`: 是否额外输出 `日线`，默认 `false`
    - `base_freq`: BarGenerator 合成与分析基础周期，默认 `1分钟`
  - 说明：
    - 数据来源：`.stock_data/raw/minute_by_stock/stock_code={symbol}/year=.../*.parquet`
    - 输出：
      - `items`：key 为周期（如 `1分钟/5分钟/.../日线`），每项包含：
        - `bars` / `fxs` / `bis` / `stats`
        - `indicators`：用于 TradingVue 复刻 `to_echarts` 的指标序列：`vol` / `macd(diff,dea,macd)` / `sma(MA5/MA13/MA21)`
      - `meta`：parquet 命中数、过滤行数、dt 范围、各周期 bars 数量等（排障用）

## 元数据表（signals / factors / strategies）

- **signals**：信号库，与 czsc.signals 对应，供筛选与 API 查询；同步脚本 `scripts/sync_czsc_signals_to_db.py`，表迁移 `scripts/migrate_rename_signal_func_to_signals.py`。
- **factors**：因子库，支持单条 expression_or_signal_ref 或多条信号配置 signals_config（JSON）；API `GET/POST/PUT/DELETE /api/v1/factors`；表迁移 `scripts/migrate_rename_factor_def_to_factors.py`。
- **strategies**：策略库，存 czsc Position 配置（config_json）；API `GET/POST/PUT/DELETE /api/v1/strategies`；种子脚本 `scripts/seed_strategies.py`。

## 策略库与个股策略分析

策略库用于存储 czsc 各类 Position 模板（单均线、MACD、CCI、EMV、三买/三卖等），前端可基于策略库选择策略并传入参数，对单只股票执行回测。

### 初始化策略库（种子数据）

从项目根目录执行：

```bash
source venv/bin/activate
python scripts/seed_strategies.py
```

- 会向 `strategies` 表写入约 22 条策略（单均线多种 ma_name、MACD、CCI、EMV、三买、三卖等）。
- 按策略 `name` 幂等写入，重复执行不会重复插入。
- 可选：`--dry-run` 仅打印将要写入的策略，不落库；`--force` 强制覆盖已存在记录。

### 各 strategy_type 与参数默认值

参数定义与默认值来自 `czsc.strategies` 中各 `create_*` 的 kwargs，由 `backend/src/services/strategy_params_schema.py` 统一维护：

| strategy_type     | 说明       | 主要参数与默认值（freq/base_freq=15分钟、interval=7200、T0=False 等通用项略） |
|-------------------|------------|-----------------------------------------------------------------------------|
| single_ma_long/short | 单均线多/空 | ma_name（SMA#5/10/20/40）、max_overlap=5、timeout=480                       |
| macd_long/short   | MACD 多/空 | max_overlap=5、timeout=480                                                  |
| cci_long/short    | CCI 多/空  | cci_timeperiod=14、timeout=480                                              |
| emv_long/short    | EMV 多/空  | di=1、timeout=100                                                           |
| third_buy_long    | 三买多头   | timeout=100                                                                |
| third_sell_short  | 三卖空头   | timeout=100                                                                |

前端提交的 `params` 会与上述默认值合并，再传给 czsc 对应 `create_*`。

### API 用法

- **GET /api/v1/strategies**：列表，每项含 `params_schema`（参数名、类型、默认值、说明、options）。
- **GET /api/v1/strategies/{name}**：按名称查单条，同样含 `params_schema`。
- **POST /api/v1/backtest/run-by-strategy**（需认证）：按策略库执行个股回测。请求体示例：

  ```json
  {
    "strategy_id": 1,
    "symbol": "000001.SZ",
    "sdt": "20240101",
    "edt": "20241231",
    "params": { "freq": "15分钟", "ma_name": "SMA#10" }
  }
  ```

  也可用 `strategy_name` 替代 `strategy_id`。返回与普通回测一致：`pairs`、`operates`、`positions`；此外 **run-by-strategy** 会多返回 **`positions_summary`**（按持仓汇总，对齐 demo 展示）。

- **回测结果结构**（run-by-strategy）：
  - `operates`：每条含 `pos_name`、`dt`、`op`（可读枚举如 LO/LE/SO/SE）、`bid`、`price`、`amount`。
  - `positions_summary`：每项含 `pos_name`、`operate_count`、`last_operates`（最近 5 条，含 dt/op/bid/price）、`evaluate`（多空合并/多头/空头）。前端策略分析页按持仓分块展示，与 `demo/step4-strategies/strategy_demo.py` 一致。

## 环境变量

- `DATA_PATH`: 数据存储路径，默认为 `./data`
- `LOG_LEVEL`: 日志级别，默认为 `INFO`
