# Data Model: 涨停跌停与买卖点时间节点

**Feature**: 002-analyze-points-table

## 事件条目（通用）

所有八类事件在 API 中均表示为「事件条目」列表，每条目至少包含时间节点，可选包含业务属性。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| dt | string | 是 | 时间节点。日/周/月周期为 YYYY-MM-DD；15/30/60 分钟等为 YYYY-MM-DD HH:mm 或 ISO 8601 |
| price | number | 否 | 可选，该时刻价格（如收盘价） |
| pct | number | 否 | 可选，涨跌幅等，单位由业务约定 |

后端序列化时可根据需要增加字段（如涨停/跌停时的 close、涨跌幅）；前端表格至少展示 dt，其余列可选。

---

## 八类事件列表

| 实体 | 说明 | 数据来源 |
|------|------|----------|
| 涨停事件 (limit_up_events) | 当前周期 K 线满足「涨停」条件的时刻 | czsc：bars_raw 扫描，close==high>=prev.close |
| 跌停事件 (limit_down_events) | 当前周期 K 线满足「跌停」条件的时刻 | czsc：bars_raw 扫描，close==low<=prev.close |
| 第一类买点 (buy1_events) | 一买信号触发的时刻 | 信号 zdy_macd_bs1_V230422 v1=看多 → dt |
| 第二类买点 (buy2_events) | 二买信号触发的时刻 | 信号 cxt_second_bs_V230320 v1=二买 → dt |
| 第三类买点 (buy3_events) | 三买信号触发的时刻 | 信号 cxt_third_bs_V230319 v1=三买 → dt |
| 第一类卖点 (sell1_events) | 一卖信号触发的时刻 | 信号 zdy_macd_bs1_V230422 v1=看空 → dt |
| 第二类卖点 (sell2_events) | 二卖信号触发的时刻 | 信号 cxt_second_bs_V230320 v1=二卖 → dt |
| 第三类卖点 (sell3_events) | 三卖信号触发的时刻 | 信号 cxt_third_bs_V230319 v1=三卖 → dt |

---

## 与现有模型的关系

- **CZSC**：不改变现有 `bi_list`、`fx_list`、`bars_raw` 等结构；新增属性或方法返回上述八类事件的 `List[Tuple[dt, ...]]` 或等价的简单结构（如 `List[dict]`），由 backend 序列化。
- **AnalysisResponse**：在现有字段基础上增加 8 个可选字段，类型均为 `List[EventItem]`（EventItem 至少含 `dt`），缺省为空列表 `[]`，保证老客户端兼容。

---

## 校验规则

- 所有事件的 `dt` 必须在本次分析的数据时间范围内（data_start_dt ~ data_end_dt）。
- 同一列表中 `dt` 不重复（同一 K 线或同一信号触发点只记录一次）。
- 时间格式由后端按 `freq` 统一生成，前端仅展示，无需再校验格式。
