# CZSC API 后端

基于FastAPI的CZSC缠论分析API服务。

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

## 环境变量

- `DATA_PATH`: 数据存储路径，默认为 `./data`
- `LOG_LEVEL`: 日志级别，默认为 `INFO`
