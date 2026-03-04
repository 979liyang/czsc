# API 契约：麒麟分析响应扩展（涨停跌停与买卖点）

**Feature**: 002-analyze-points-table  
**Endpoint**: `POST /api/v1/analysis/czsc`（沿用现有，仅扩展响应体）

## 请求

不变。沿用现有 `AnalysisRequest`：

- `symbol`: string
- `freq`: string（如 日线、15分钟、30分钟、60分钟、周线、月线）
- `sdt`: string（YYYY-MM-DD 或 YYYYMMDD）
- `edt`: string（YYYY-MM-DD 或 YYYYMMDD）

## 响应扩展

在现有 `AnalysisResponse` 字段基础上，**新增**以下可选字段；未实现时可为空数组 `[]`，以实现向后兼容。

### 事件条目结构（每条记录）

```json
{
  "dt": "2024-01-15 10:30",
  "price": 12.34,
  "pct": 5.2
}
```

- `dt`（必填）：string，时间节点；日/周/月为 `YYYY-MM-DD`，分钟周期为 `YYYY-MM-DD HH:mm` 或 ISO 8601。
- `price`（可选）：number，该时刻价格。
- `pct`（可选）：number，涨跌幅等（单位由业务约定）。

### 新增响应字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit_up_events | array of EventItem | 否（默认 []） | 涨停事件列表 |
| limit_down_events | array of EventItem | 否（默认 []） | 跌停事件列表 |
| buy1_events | array of EventItem | 否（默认 []） | 第一类买点时间节点列表 |
| buy2_events | array of EventItem | 否（默认 []） | 第二类买点时间节点列表 |
| buy3_events | array of EventItem | 否（默认 []） | 第三类买点时间节点列表 |
| sell1_events | array of EventItem | 否（默认 []） | 第一类卖点时间节点列表 |
| sell2_events | array of EventItem | 否（默认 []） | 第二类卖点时间节点列表 |
| sell3_events | array of EventItem | 否（默认 []） | 第三类卖点时间节点列表 |

### 响应示例（片段）

```json
{
  "symbol": "000001.SH",
  "freq": "日线",
  "bis": [...],
  "fxs": [...],
  "zss": [],
  "limit_up_events": [
    { "dt": "2024-06-12", "price": 10.05, "pct": 10.0 }
  ],
  "limit_down_events": [],
  "buy1_events": [
    { "dt": "2024-05-08" }
  ],
  "buy2_events": [
    { "dt": "2024-05-20" }
  ],
  "buy3_events": [],
  "sell1_events": [],
  "sell2_events": [
    { "dt": "2024-06-05" }
  ],
  "sell3_events": [],
  "data_start_dt": "2024-01-02T00:00:00",
  "data_end_dt": "2024-06-14T00:00:00",
  ...
}
```

## 错误与边界

- 当某类事件在分析区间内不存在时，对应字段为空数组 `[]`，不返回错误。
- 请求参数、鉴权、其余响应字段与现有 `POST /analysis/czsc` 一致；仅在此契约中描述新增字段。
