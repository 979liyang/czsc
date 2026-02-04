# CZSC `to_echarts()` 与 TradingVue 数据映射说明

> 目标：让前端用 `trading-vue-js` 画出与 `CZSC.to_echarts()`（内部 `kline_pro`）信息密度一致的图：
> **K线主图 + 分型/笔 + 均线 + 成交量 + MACD**。

## 1. `CZSC.to_echarts()` 做了什么

`czsc/analyze.py` 中：

- `CZSC.to_echarts(width, height, bs=[])` 会从对象里取：
  - **K线**：`self.bars_raw`（RawBar 列表）
  - **分型**：`self.fx_list`
  - **笔**：`self.bi_list`
- 然后组织成字典数组并调用：
  - `czsc/utils/echarts_plot.py:kline_pro(kline, bi=bi, fx=fx, width, height, bs, title=...)`

其中：
- `kline`：`[bar.__dict__ for bar in bars_raw]`
- `fx`：`[{dt, fx}]`
- `bi`：如果有笔，则取每笔的 `fx_a` 以及最后一笔的 `fx_b`，组织成 `[{dt, bi}]`

## 2. `kline_pro` 默认画哪些内容

`czsc/utils/echarts_plot.py:kline_pro` 默认绘制：

- **K线主图**：Candles
- **均线系统**（SMA）：
  - 默认 `t_seq=[5, 13, 21]`
  - 计算 `SMA(close, timeperiod=t)` 并在主图叠加
- **分型（FX）**：
  - 用折线图 + 圆点标记（symbol circle）
- **笔（BI）**：
  - 用折线图 + 菱形标记（symbol diamond）
- **成交量（Volume）副图**
- **MACD 副图**：
  - `MACD(close)` 得到 `diff/dea/macd`
  - macd 画柱（红绿区分正负），diff/dea 画线

## 3. TradingVue 推荐数据结构（与后端对接）

`trading-vue-js` 推荐的数据结构：

- `data.chart`: 主图（Candles）
- `data.onchart`: 叠加在主图上的指标/标记（SMA、分型、笔）
- `data.offchart`: 画在下方的指标（Volume、MACD）

## 4. 本项目的映射策略（当前实现目标）

### 4.1 K线（bars）

后端 `bars`（RawBar 序列化）映射为 TradingVue OHLCV：

- `[timestamp_ms, open, high, low, close, volume]`

### 4.2 均线（SMA）

后端返回：

- `indicators.sma["MA5"] = [[ts, v], ...]`（同理 MA13、MA21）

前端作为 `onchart` 指标，`type: "SMA"`（由 TradingVue 内置 `Spline` overlay 渲染）：

- `{"name":"MA5","type":"SMA","data":[[ts,v],...]}`

### 4.3 分型（FX）

后端 `fxs` 已包含 `dt/fx/mark`，前端用 TradingVue 内置 `Trades` overlay 画圆点标记：

- `type: "Trades"`
- `data: [[ts, side, price, label], ...]`
  - `side`: 顶分型=0（卖点色），底分型=1（买点色）
  - `label`: "顶"/"底"（可关掉）

### 4.4 笔（BI）

为了更贴近 `kline_pro` 的 “bi 点序列”，后端需要补齐 `fx_a/fx_b` 的时间与价格字段，
前端将这些点序列用 `Spline` 画折线：

- `type: "Spline"`
- `data: [[ts, price], ...]`

### 4.5 成交量（Volume）

TradingVue 内置 `Volume` overlay 支持 offchart 渲染，数据可以直接复用 OHLCV：

- `{"name":"Volume","type":"Volume","data": ohlcv}`

### 4.6 MACD

TradingVue 默认不带 MACD overlay，本项目通过自定义 overlay（`MACD`）实现：

- `type: "MACD"`
- `data: [[ts, diff, dea, macd], ...]`

MACD overlay 在 offchart 上绘制：
- macd 柱（正/负不同颜色）
- diff/dea 两条线

