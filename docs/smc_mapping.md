# Smart Money Concepts（SMC）对照说明

## 参考

- TradingView 开源脚本说明页：`https://cn.tradingview.com/v/CnB3fSph/`
- 本项目对照源码：`demo/smartMoney.txt`（Pine v5）

## 本项目实现路径

由于 Charting Library 无法直接执行 Pine v5 源码，本项目优先采用：

- **后端计算**：复用 `czsc/indicators/smart_money.py` 计算 areas/events
- **前端绘制**：在 Charting Library 上通过 Drawings API 叠加矩形与文本标注

## 差异与待对齐项

- **实时结构/Present 模式**：当前仅提供“历史计算后叠加”，未完全复现 Pine 的实时迭代绘制模式
- **Internal Confluence Filter**：后端实现已预留开关，但需要更多对照验证
- **绘制样式**：Drawings 的 overrides key 在不同版本可能差异，若样式未生效需要按 CL 版本微调

