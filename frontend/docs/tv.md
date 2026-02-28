# TradingView 图表库中文使用文档

## 目录

- [1. 简介](#1-简介)
- [2. 核心概念](#2-核心概念)
- [3. 快速开始](#3-快速开始)
- [4. 核心模块与API详解](#4-核心模块与api详解)
  - [4.1 Widget](#41-widget-chartinglibrarywidgetconstructor-和-ichartinglibrarywidget)
  - [4.2 图表](#42-图表-ichartwidgetapi)
  - [4.3 数据源](#43-数据源-ibasicdatafeed-idatafeedchartapi)
  - [4.4 指标](#44-指标-istudyapi)
  - [4.5 绘图](#45-绘图-ilinedatasourceapi)
  - [4.6 覆盖](#46-覆盖-overrides)
  - [4.7 交易终端特有功能](#47-交易终端特有功能-trading-platform)
- [5. 类型系统](#5-类型系统)
- [6. 常用示例](#6-常用示例)
- [7. 最佳实践与注意事项](#7-最佳实践与注意事项)

---

## 1. 简介

TradingView 图表库是一个功能强大、可高度定制的金融图表库，允许开发者将专业的金融图表集成到自己的网页应用中。它支持丰富的图表类型、技术指标、绘图工具，并提供了一个完整的交易终端解决方案（Trading Platform）。

本文档基于图表库的类型声明文件，旨在为开发者提供一个清晰、全面的参考指南，涵盖核心概念、主要模块和常用API。

## 2. 核心概念

在开始使用之前，了解以下几个核心概念至关重要：

| 概念 | 描述 |
|------|------|
| **Widget (小部件)** | 图表库的入口点。通过 `TradingView.widget()` 构造函数创建一个图表实例，并将其挂载到页面的DOM元素上。 |
| **Datafeed (数据源)** | 一个关键的接口（`IBasicDataFeed`），负责将您的后端数据连接到图表库。您需要实现这个接口来提供历史K线数据、实时更新、搜索交易品种等功能。 |
| **Chart (图表)** | 通过 `widget.chart()` 或 `widget.activeChart()` 获取的 `IChartWidgetApi` 对象。它代表一个具体的图表实例，提供了操作图表（如切换交易品种、修改周期、添加指标）的方法。 |
| **Study (指标)** | 添加到图表上的技术指标，如移动平均线、MACD、RSI等。您可以通过 `createStudy` 方法添加内置或自定义指标。 |
| **Overrides (覆盖)** | 允许您在初始化时或运行时修改图表、指标和绘图的默认样式和行为的机制。这是定制图表外观的核心方式。 |
| **Broker API / Trading Host (经纪商API/交易主机)** | 仅在 Trading Platform 中可用。`Broker API` 是您需要实现的接口，用于将您的交易逻辑（下单、撤单、查询持仓等）连接到图表。`Trading Host` 是库提供给您的API，用于向图表推送交易状态更新。 |

## 3. 快速开始

1.  **引入库**: 在您的HTML页面中引入 TradingView 图表库的脚本。
2.  **创建容器**: 准备一个用于挂载图表的DOM元素，例如 `<div id="tv_chart_container"></div>`。
3.  **实现数据源 (Datafeed)**: 创建一个对象，实现 `IBasicDataFeed` 接口。这是连接您数据的桥梁。您至少需要实现 `onReady`、`resolveSymbol`、`getBars`、`subscribeBars` 和 `unsubscribeBars` 方法。
4.  **实例化 Widget**: 使用 `TradingView.widget()` 构造函数，传入配置选项，如 `container`、`datafeed`、`symbol`、`interval` 等。
5.  **与图表交互**: 在图表就绪后（通过 `onChartReady` 回调），可以使用 `widget.chart()` 或 `widget.activeChart()` 获取 `IChartWidgetApi` 对象，进而操作图表。

```javascript
// 示例：初始化一个简单的图表
const widget = new TradingView.widget({
    container: 'tv_chart_container',
    datafeed: new MyDatafeed(), // 您的数据源实现
    interval: '1D',
    symbol: 'AAPL',
    // ... 其他配置
});

widget.onChartReady(() => {
    const chart = widget.activeChart();
    console.log('图表已就绪，当前交易品种:', chart.symbol());
});
```

## 4. 核心模块与API详解

### 4.1 Widget (`ChartingLibraryWidgetConstructor` 和 `IChartingLibraryWidget`)

这是您与图表库交互的主要入口。通过 `TradingView.widget` 创建。

#### 构造函数选项

| 选项 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `container` | `HTMLElement \| string` | ✓ | 挂载图表的DOM元素或其ID |
| `datafeed` | `IBasicDataFeed` | ✓ | 您的数据源实现 |
| `interval` | `ResolutionString` | ✓ | 默认时间周期，例如 `'1D'` |
| `symbol` | `string` | | 默认交易品种，例如 `'AAPL'` |
| `autosize` / `fullscreen` | `boolean` | | 控制图表尺寸 |
| `theme` | `'light' \| 'dark'` | | 主题 |
| `locale` | `LanguageCode` | | 本地化语言代码，例如 `'zh'` |
| `overrides` | `Partial<ChartPropertiesOverrides>` | | 覆盖默认的图表样式和属性 |
| `studies_overrides` | `Partial<StudyOverrides>` | | 覆盖指标的默认样式和输入值 |
| `disabled_features` / `enabled_features` | `array` | | 启用或禁用特定的功能集 |
| `saved_data` | `object` | | 加载之前保存的图表布局 |
| `timeframe` | `TimeframeOption` | | 设置默认的时间范围 |
| `timezone` | `Timezone \| 'exchange'` | | 设置默认时区 |
| `custom_formatters` | `CustomFormatters` | | 提供自定义的日期、时间、价格格式化器 |
| `favorites` | `Favorites` | | 设置默认的收藏项 |
| `broker_config` / `broker_factory` | - | | (Trading Platform) 交易功能的配置和工厂函数 |

#### 主要方法

| 方法 | 描述 |
|------|------|
| `onChartReady(callback)` | 图表准备就绪后的回调 |
| `chart(index?)` | 获取指定索引的图表API对象 |
| `activeChart()` | 获取当前活动图表的API对象 |
| `setSymbol(symbol, interval, callback)` | 更改当前图表的交易品种和周期 |
| `remove()` | 销毁小部件并清理资源 |
| `subscribe(event, callback)` | 订阅库级事件 |
| `unsubscribe(event, callback)` | 取消订阅库级事件 |
| `onContextMenu(callback)` | 自定义右键菜单 |
| `createButton(options)` | 在顶部工具栏创建自定义按钮 |
| `applyOverrides(overrides)` | 运行时应用样式覆盖 |
| `applyStudiesOverrides(overrides)` | 运行时应用指标覆盖 |
| `takeScreenshot()` | 截取当前图表快照 |
| `changeTheme(themeName)` | 动态切换主题 |
| `undoRedoState()` | 获取撤销/重做状态 |
| `watchList()` | (Trading Platform) 获取Watchlist API |
| `news()` | (Trading Platform) 获取News API |

### 4.2 图表 (`IChartWidgetApi`)

通过 `widget.chart()` 或 `widget.activeChart()` 获取，用于操作单个图表。

#### 事件订阅

| 方法 | 触发时机 |
|------|----------|
| `onDataLoaded()` | 新数据加载完成时 |
| `onSymbolChanged()` | 交易品种更改时 |
| `onIntervalChanged()` | 周期更改时 |
| `onVisibleRangeChanged()` | 图表可见范围改变时 |
| `crossHairMoved()` | 十字光标移动时 |
| `onHoveredSourceChanged()` | 十字光标悬停的指标或序列改变时 |

#### 操作方法

| 方法 | 描述 |
|------|------|
| `setSymbol(symbol, options?)` | 更改图表交易品种 |
| `setResolution(resolution, options?)` | 更改图表周期 |
| `setChartType(type)` | 更改图表类型 |
| `setVisibleRange(range, options?)` | 设置图表的可见时间范围 |
| `executeActionById(actionId)` | 执行一个内置动作 |
| `createStudy(name, forceOverlay?, lock?, inputs?, overrides?, options?)` | 创建一个指标，返回指标ID |
| `getStudyById(id)` | 根据ID获取指标API对象 |
| `getSeries()` | 获取主图序列API对象 |
| `createShape(point, options)` | 创建一个单点绘图，返回绘图ID |
| `createMultipointShape(points, options)` | 创建一个多点绘图，返回绘图ID |
| `getShapeById(id)` | 根据ID获取绘图API对象 |
| `removeEntity(entityId)` | 从图表中移除一个实体（指标或绘图） |
| `selection()` | 获取选择集API |
| `getAllShapes()` / `getAllStudies()` | 获取图表上所有绘图/指标的ID和名称 |
| `exportData(options?)` | 导出图表数据 |
| `getPanes()` | 获取图表中所有窗格的数组 |
| `getTimeScale()` | 获取时间刻度API |
| `createOrderLine()` / `createPositionLine()` / `createExecutionShape()` | (Trading Platform) 创建交易相关的图元 |

### 4.3 数据源 (`IBasicDataFeed`, `IDatafeedChartApi`)

这是您必须实现的核心接口，用于为图表提供数据。

#### 必需方法

| 方法 | 描述 |
|------|------|
| `onReady(callback)` | 向库提供数据源的配置信息 |
| `resolveSymbol(symbolName, onResolve, onError)` | 根据交易品种名称解析出其详细信息 |
| `getBars(symbolInfo, resolution, periodParams, onResult, onError)` | 请求历史K线数据 |
| `subscribeBars(symbolInfo, resolution, onTick, listenerGuid, onResetCacheNeededCallback)` | 订阅实时K线更新 |
| `unsubscribeBars(listenerGuid)` | 取消订阅实时更新 |

#### 可选方法

| 方法 | 描述 |
|------|------|
| `searchSymbols(userInput, exchange, symbolType, onResult)` | 实现交易品种搜索功能 |
| `getMocks` / `getTimescaleMarks` | 提供K线标记和时间轴标记 |
| `getServerTime` | 提供服务器时间 |
| `getQuotes` / `subscribeQuotes` / `unsubscribeQuotes` | (Trading Platform) 提供报价数据 |

### 4.4 指标 (`IStudyApi`)

通过 `getStudyById` 获取。

| 方法 | 描述 |
|------|------|
| `getInputsInfo()` | 获取指标输入参数的定义 |
| `getInputValues()` | 获取当前输入参数的值 |
| `setInputValues(values)` | 设置输入参数的值 |
| `getStyleInfo()` | 获取指标样式定义 |
| `getStyleValues()` | 获取当前样式值 |
| `isVisible()` / `setVisible()` | 获取或设置指标的可见性 |
| `mergeUp()` / `mergeDown()` / `unmergeUp()` / `unmergeDown()` | 将指标移动到其他窗格 |
| `applyOverrides(overrides)` | 动态应用指标样式覆盖 |
| `onDataLoaded()` | 指标数据加载完成时触发 |

### 4.5 绘图 (`ILineDataSourceApi`)

通过 `getShapeById` 获取。

| 方法 | 描述 |
|------|------|
| `getPoints()` | 获取绘图的点坐标 |
| `setPoints(points)` | 设置绘图的点坐标 |
| `getProperties()` | 获取绘图的全部属性 |
| `setProperties(newProperties, saveDefaults?)` | 设置绘图的属性 |
| `bringToFront()` / `sendToBack()` | 调整绘图的Z轴顺序 |
| `setSelectionEnabled()` / `setSavingEnabled()` | 控制绘图的交互和保存行为 |

### 4.6 覆盖 (Overrides)

覆盖是自定义图表外观和行为的核心。

#### 图表覆盖示例

| 覆盖路径 | 描述 |
|----------|------|
| `"mainSeriesProperties.style"` | 设置主图样式 (0: Bar, 1: Candle, 2: Line ...) |
| `"mainSeriesProperties.candleStyle.upColor"` | 设置阳线颜色 |
| `"paneProperties.background"` | 设置窗格背景色 |
| `"scalesProperties.textColor"` | 设置坐标轴文本颜色 |

#### 指标覆盖示例

| 覆盖路径 | 描述 |
|----------|------|
| `"volume.volume.color"` | 修改成交量指标的颜色 |
| `"MACD.macd.color"` | 修改MACD快线颜色 |
| `"RSI.plot.linewidth"` | 修改RSI线宽 |
| `"Bollinger Bands.length"` | 修改布林带周期 |

### 4.7 交易终端特有功能 (Trading Platform)

如果使用 `TradingTerminalWidgetOptions` 初始化，图表将启用交易功能。

| 组件 | 描述 |
|------|------|
| **Broker API (`IBrokerTerminal`)** | 您需要实现的接口，包含下单、撤单、查询订单/持仓等方法 |
| **Trading Host (`IBrokerConnectionAdapterHost`)** | 库提供给您的API，用于向库推送交易状态更新 |
| **账户管理器 (`AccountManagerInfo`)** | 配置底部账户管理器的表格、列、摘要信息等 |
| **Watchlist API (`IWatchListApi`)** | 通过 `widget.watchList()` 获取，用于操作自选列表 |
| **News API (`INewsApi`)** | 通过 `widget.news()` 获取，用于操作新闻面板 |
| **Widgetbar API (`IWidgetbarApi`)** | 通过 `widget.widgetbar()` 获取，用于控制右侧面板的显示隐藏 |

## 5. 类型系统

该库使用TypeScript编写，提供了丰富的类型定义。

| 类型 | 描述 | 示例 |
|------|------|------|
| **枚举 (Enums)** | 限制可选值 | `ChartStyle`, `LineStyle`, `OrderType` |
| **接口 (Interfaces)** | 定义API和配置对象的结构 | `IChartWidgetApi`, `IBrokerTerminal` |
| **工具类型 (Utility Types)** | 名义类型，帮助区分不同的字符串ID | `EntityId`, `ResolutionString` |
| **联合类型 (Union Types)** | 多个类型的组合 | `SeriesType` (数字枚举和字符串枚举的联合) |

## 6. 常用示例

### 示例 1：自定义K线颜色

```javascript
// 在初始化时设置
const widget = new TradingView.widget({
    // ... 其他选项
    overrides: {
        'mainSeriesProperties.candleStyle.upColor': '#4caf50', // 阳线绿色
        'mainSeriesProperties.candleStyle.downColor': '#f44336', // 阴线红色
        'mainSeriesProperties.candleStyle.wickColor': '#cccccc' // 影线灰色
    }
});
```

### 示例 2：动态修改指标

```javascript
widget.onChartReady(() => {
    const chart = widget.activeChart();
    // 创建一个MA指标
    chart.createStudy('Moving Average', false, false, [9]).then((maId) => {
        const maStudy = chart.getStudyById(maId);
        // 修改MA的颜色和线宽
        maStudy.applyOverrides({
            'plot.color': '#ff9900',
            'plot.linewidth': 2
        });
        // 修改MA的周期
        maStudy.setInputValues([{ id: 'length', value: 21 }]);
    });
});
```

### 示例 3：处理十字光标移动

```javascript
widget.activeChart().crossHairMoved().subscribe(null, (params) => {
    console.log('十字光标位置:', {
        time: new Date(params.time * 1000).toISOString(), // 注意时间戳单位
        price: params.price
    });
    // 可以获取其他指标的值
    // console.log(params.entityValues);
});
```

### 示例 4：添加一个趋势线绘图

```javascript
const points = [
    { time: 1672531200, price: 150 }, // 2023-01-01
    { time: 1675209600, price: 180 }  // 2023-02-01
];
widget.activeChart().createMultipointShape(points, {
    shape: 'trend_line',
    overrides: {
        'linetooltrendline.linecolor': '#FF00FF',
        'linetooltrendline.linewidth': 3
    },
    lock: false
});
```

## 7. 最佳实践与注意事项

| 实践 | 描述 |
|------|------|
| **Datafeed 的健壮性** | 确保您的数据源能够稳定、快速地响应 `getBars` 和 `resolveSymbol` 请求。合理处理历史数据为空、网络错误等情况。 |
| **性能优化** | 避免在 `crossHairMoved` 等高频率事件回调中执行复杂计算。如需更新UI，考虑使用节流或防抖。 |
| **内存管理** | 在移除图表 (`widget.remove()`) 或不再需要时，正确取消所有通过 `subscribe` 订阅的回调，以防止内存泄漏。 |
| **善用覆盖 (Overrides)** | 尽量使用 `overrides` 和 `studies_overrides` 进行样式定制，避免在每次创建后手动修改属性。 |
| **类型安全** | 在TypeScript项目中，充分利用提供的类型定义，特别是在实现Datafeed和Broker API时。 |
| **参考官方文档** | 这份文档是类型定义的指南，更详细的功能说明、教程和示例请参考 TradingView 的官方文档网站。 |

---