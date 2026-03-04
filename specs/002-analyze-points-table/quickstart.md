# Quickstart: 002 麒麟分析涨停跌停与买卖点表格

**Feature**: 002-analyze-points-table

## 目标

在麒麟分析流程中增加涨停、跌停、第一/二/三类买点、第一/二/三类卖点的时间节点数据，并在前端麒麟分析页以表格展示。

## 实现顺序建议

1. **czsc 层**：在 `czsc/analyze.py` 的 CZSC 上增加计算八类事件列表的能力（涨停/跌停扫描 bars_raw；买卖点通过回放 K 线并调用现有信号，收集 dt）。
2. **backend 层**：在 `AnalysisService.analyze()` 中调用上述能力，序列化后写入 result；在 `AnalysisResponse` 与序列化逻辑中增加 8 个可选字段（默认 []）。
3. **frontend 层**：在 `Analysis.vue` 中增加 8 个表格区域（或复用通用表格组件），数据来自 `analysisResult` 的新字段；时间列直接展示后端返回的 `dt` 字符串。

## 本地运行与验证

### 后端

```bash
# 项目根目录
cd backend
# 若使用 venv
source .venv/bin/activate  # 或 Windows: .venv\Scripts\activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- 接口文档：http://localhost:8000/docs  
- 调用 `POST /api/v1/analysis/czsc`，检查响应中是否包含 `limit_up_events`、`limit_down_events`、`buy1_events`、`buy2_events`、`buy3_events`、`sell1_events`、`sell2_events`、`sell3_events`（可为空数组）。

### 前端

```bash
cd frontend
npm install
npm run dev
```

- 打开麒麟分析页，选择标的、周期、时间范围并点击分析；确认结果区域除笔列表、分型列表、K 线图外，出现涨停、跌停与六类买卖点表格，且时间列格式与周期一致（日线为日期，分钟为日期+时间）。

### 单元测试（czsc）

```bash
# 项目根目录
pytest test/test_analyze.py -v -k "limit_up_or_buy_sell"  # 若有针对性用例
# 或运行全量 analyze 相关测试
pytest test/test_analyze.py -v
```

### K 线图第一类买卖点绘制验证

打开 K 线图页，开启「分析买卖点」及「一买」「一卖」开关，选取有第一类买卖点数据的标的与区间，核对：

- [ ] **一买**：锚点在该根 K 线的 low（或分析接口返回的 price）；连接线向下、长度为锚点价格的 3%；竖线为虚线；文案「一买」在连接线下方端点；无横向射线。
- [ ] **一卖**：锚点在该根 K 线的 high（或分析接口返回的 price）；连接线向上、长度为 3%；竖线为虚线；文案「一卖」在连接线上方端点；无横向射线。
- [ ] 图表上一买/一卖的时间节点与麒麟分析页表格中「第一类买点」「第一类卖点」的 `dt` 一致。

## 参考文档

- 需求与验收：[spec.md](./spec.md)
- 技术方案与结构：[plan.md](./plan.md)
- 研究结论（涨停/跌停/买卖点定义与时间格式）：[research.md](./research.md)
- 数据与契约：[data-model.md](./data-model.md)、[contracts/analysis-czsc-response-extension.md](./contracts/analysis-czsc-response-extension.md)
