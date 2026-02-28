# Charting Library 自定义指标（Custom Studies）与 Pine 执行可行性

## 结论（针对 `demo/smartMoney.txt`）

- **无法直接“执行 Pine v5 源码”**：Charting Library 并不提供一个可直接加载/运行 TradingView 网站 Pine 编辑器脚本（`.txt`）的完整编译与运行环境。
- **可行替代**：
  1. **后端计算 + 前端覆盖绘制（推荐）**：本项目已实现（`/api/v1/indicators/smc` + Drawings API 叠加），见 `docs/smc_mapping.md`。
  2. **自定义 Study（JS/PineJS 风格）改写**：需要将 Pine 逻辑重写为 Charting Library 允许的自定义指标脚本形态；SMC 脚本体量大（结构/OB/FVG/MTF/大量绘制），改写成本高，建议先做子集验证（例如仅 FVG）。

## 本项目当前选择

优先保证“能跑起来 + 与参考逻辑可对照”，因此采用 **后端计算 + 前端叠加** 路线：

- 后端：`backend/src/api/v1/indicators.py` → `GET /api/v1/indicators/smc`
- 前端：`frontend/src/tv/smcOverlay.ts`（rectangle/text drawings）

