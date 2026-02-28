# TradingView Charting Library 数据接入（本地 `.stock_data`）

本文档用于说明本项目如何给 TradingView Charting Library 提供数据（UDF 风格接口），以及本地数据的路径约定。

## 数据来源

- **分钟数据**：`.stock_data/raw/minute_by_stock/stock_code={symbol}/year={year}/{symbol}_{year}-{month}.parquet`
- **日线数据**：`.stock_data/raw/daily/by_stock/stock_code={symbol}/{symbol}_{year}.parquet`（如存在）

分钟数据的读取与合成逻辑参考：`backend/src/services/local_czsc_service.py`

## UDF 端点（后端）

后端路由位于：`backend/src/api/v1/tradingview.py`，统一前缀为 `/api/v1/tv`。

- `GET /api/v1/tv/config`：datafeed 配置
- `GET /api/v1/tv/search`：按关键字搜索 symbols（最小实现：从本地 `.stock_data` 推断）
- `GET /api/v1/tv/symbols`：resolveSymbol（返回 session/timezone/pricescale 等）
- `GET /api/v1/tv/history`：历史 K 线（UDF 标准：s/t/o/h/l/c/v）
- `GET /api/v1/tv/time`：服务器时间（秒）

## 分钟级别数据范围

- **resolution 为 1/5/15/30/60（分钟）时**：**只返回最近 3 个月**的数据。不按前端 countback/from 向前扩展，读取窗口固定为 `to` 往前 3 个月，避免单次请求数据量过大。
- 日/周/月（D/W/M）按请求范围返回，countback 时最多向前扩展 1 年。

## 快速验证（curl）

```bash
curl "http://localhost:8000/api/v1/tv/config"
curl "http://localhost:8000/api/v1/tv/search?query=300308&limit=10"
curl "http://localhost:8000/api/v1/tv/symbols?symbol=300308.SZ"
curl "http://localhost:8000/api/v1/tv/history?symbol=300308.SZ&resolution=D&from=1700000000&to=1760000000"
curl "http://localhost:8000/api/v1/tv/time"
```

## 常见问题

- **无数据**：请确认 `.stock_data` 下对应 parquet 文件存在；缺数据可用项目内已有采集脚本补齐。
- **价格精度**：本项目对 A 股默认设置 `pricescale=100`，表示价格最小精度为 0.01。

