# TradingView Chart 前端 SDK 说明

基于 `charting_library` 的 Widget 与 Chart API，本 SDK 提供两类能力：

1. **更换 K 线周期、更换股票**：不销毁 widget，通过 API 切换标的与周期。
2. **通知图表更新**：在 K 线上新增/修改指标、图形、覆盖层等。

---

## 一、SDK 封装用法

### 1.1 创建并注入 Widget

```ts
import { createChartWidgetSdk } from '@/tv/chartWidgetSdk';

const sdk = createChartWidgetSdk();

// 在 new TradingView.widget(...) 且 onChartReady 之后
sdk.setWidget(widgetRef.value);
```

### 1.2 更换标的与周期（不重建图表）

**场景**：用户在下拉框里切换股票或周期，希望图表只刷新数据，不整表重建。

```ts
// 同时更换股票和周期（推荐，一次调用）
sdk.setSymbolAndInterval('600078.SH', '30', () => {
  console.log('切换完成，可在这里刷新 SMC 等覆盖层');
});

// 仅更换股票
await sdk.setSymbol('000001.SZ', () => { /* 可选回调 */ });

// 仅更换周期
await sdk.setResolution('60', () => { /* 可选回调 */ });
```

### 1.3 获取当前图表 API（用于添加数据/监听）

```ts
const chart = sdk.getActiveChart();
if (!chart) return;

// 当前标的与周期
const { symbol, interval } = sdk.getSymbolInterval() ?? {};
```

---

## 二、在 K 线上新增/修改数据（通知 Widget）

以下均通过 `widget.activeChart()` 返回的 **IChartWidgetApi** 完成，即 `sdk.getActiveChart()`。

### 2.1 指标（Study）

| 方法 | 说明 |
|------|------|
| `createStudy(name, forceOverlay?, lock?, inputs?, overrides?, options?)` | 添加指标，返回 `Promise<EntityId \| null>` |
| `getStudyById(entityId)` | 获取指标 API，可 `.setVisible(false)`、`.applyOverrides({})` 等 |
| `getAllStudies()` | 所有指标 `{ id, name }[]` |
| `removeEntity(entityId)` | 删除指定实体（指标/图形） |
| `removeAllStudies()` | 删除全部指标 |

示例：

```ts
const chart = sdk.getActiveChart();
if (!chart) return;

// 添加 MACD
const id = await chart.createStudy(
  'MACD',
  false,  // 不强制主图
  false,  // 不锁定
  { in_0: 14, in_1: 30, in_2: 9, in_3: 'close' }
);

// 隐藏某指标
const study = chart.getStudyById(id);
study?.setVisible(false);
```

### 2.2 图形（Drawing）

| 方法 | 说明 |
|------|------|
| `createShape(point, options)` | 单点图形，如竖线 `{ shape: 'vertical_line' }` |
| `createMultipointShape(points, options)` | 多点图形，如趋势线、矩形、箭头等 |
| `createAnchoredShape(position, options)` | 锚定图形（随比例位置），如文字 |
| `getShapeById(entityId)` | 获取图形 API |
| `getAllShapes()` | 所有图形 `{ id, name }[]` |
| `removeEntity(entityId)` / `removeAllShapes()` | 删除图形 |

示例：

```ts
// 趋势线：两点 (time 为 Unix 秒)
await chart.createMultipointShape(
  [
    { time: 1704067200, price: 10.5 },
    { time: 1704153600, price: 11.2 },
  ],
  {
    shape: 'trend_line',
    lock: true,
    disableSelection: true,
    disableSave: true,
  }
);

// 竖线
await chart.createShape(
  { time: 1704067200, price: 10 },
  { shape: 'vertical_line' }
);
```

### 2.3 图表样式与可见范围

| 方法 | 说明 |
|------|------|
| `widget.applyOverrides(overrides)` | 图表整体样式覆盖（如背景、网格） |
| `widget.applyStudiesOverrides(overrides)` | 指标样式覆盖 |
| `chart.setVisibleRange({ from, to }, options?)` | 设置可见时间范围（from/to 为 Unix 秒） |

### 2.4 事件订阅（在 onChartReady 后调用）

| 方法 | 说明 |
|------|------|
| `onDataLoaded()` | 新数据加载完成 |
| `onSymbolChanged()` | 标的解析完成（含周期/品种变化） |
| `onIntervalChanged()` | 周期变化 |
| `onVisibleRangeChanged()` | 可见范围变化 |
| `crossHairMoved()` | 十字光标移动 |

示例：

```ts
chart.onIntervalChanged().subscribe(null, (interval, timeframeObj) => {
  console.log('周期变为', interval);
});
```

---

## 三、与 Vue 组件配合

- **仅 symbol / interval 变化**：调用 `sdk.setSymbolAndInterval(symbol, interval, () => refreshSmcOverlay())`，无需 `destroyWidget` + `initWidget`。
- **其他功能（如 SMC 开关）**：在回调或 watch 里调用 `refreshSmcOverlay()`，内部用 `chart.removeEntity` / `createMultipointShape` 等更新覆盖层。

类型定义见 `charting_library.d.ts` 中的 `IChartingLibraryWidget`、`IChartWidgetApi`、`IStudyApi`、`ILineDataSourceApi` 等。
