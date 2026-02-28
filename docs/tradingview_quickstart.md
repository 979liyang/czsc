# TradingView Charting Library 快速启动

## 启动后端

在项目根目录执行：

```bash
python -m backend.src.main
```

服务默认监听：`http://localhost:8000`

Charting Library 静态资源由后端托管在：

- `http://localhost:8000/charting_library/`

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认监听：`http://localhost:5173`

## 打开页面

- 访问 `/tv`（TradingView Charting Library 页面）
- 默认展示 `300308.SZ` 的 K 线（若本地 `.stock_data` 有数据）

## 排查

- **图表空白**：打开浏览器 Network，确认 `/api/v1/tv/*` 返回正常 JSON
- **404 charting_library**：确认后端启动成功，并能访问 `http://localhost:8000/charting_library/charting_library.js`
- **无数据**：确认 `.stock_data/raw/minute_by_stock` / `.stock_data/raw/daily/by_stock` 下存在目标标的 parquet
- **价格显示不对（小数位/整数）**：检查 `/api/v1/tv/symbols` 返回的 `pricescale`，A股两位小数一般用 100
- **SMC 不显示**：先打开 `/tv` 页面右上角 SMC 开关，再确认后端 `/api/v1/indicators/smc` 可返回 areas/events
- **“The state with a data type: unknown does not match a schema”**：由库在恢复/校验 state 时触发。前端已对 resolveSymbol 返回的 SymbolInfo 做字段与类型规范化；若仍出现，可清除本站点 localStorage 后刷新（F12 → Application → Local Storage → 删除对应 origin）

---

## 验收（T020）：K 线正常显示

- 启动后端与前端后，访问 `/tv`，默认应显示 `300308.SZ` 的 K 线。
- 验收标准：图表有 K 线、可切换周期（D/60/30/15/5/1）、Network 中可见 `/api/v1/tv/history` 等请求。
- **截图**：（请在本机完成上述步骤后，将截图粘贴于此或附链接）

---

## 验收（T041）：日线/分钟行为一致

- **日线**：选择日线周期，首次加载应只请求一次 history 接口；向左滑动查看更早数据时，再请求更早区间，无重复短窗请求。
- **分钟**：选择 1/5/15/30/60 任一周期，每次应请求 3 个月时间窗（`from = to - 90 天`），一次返回该段内全部 K 线；向左滑再请求更早 3 个月。Network 中不应出现“一直请求”同一或相近时间窗的现象。
- 验收通过标准：日线“每次只请求一次、向左滑继续请求”；分钟“每次 3 个月窗、一次返回全部 K 线、向左滑再请求更早 3 个月”，无“一直请求”。

