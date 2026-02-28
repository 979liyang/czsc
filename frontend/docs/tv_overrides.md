# TradingView Advanced Charts 参数详细说明

## 图形 API 来源说明

- **数据源标记**（K 线标记、时间轴标记）：见 `frontend/charting_library/datafeed-api.d.ts` 中的 `Mark`、`TimescaleMark`、`getMarks`、`getTimescaleMarks`；需配置 `supports_marks` / `supports_timescale_marks`。
- **绘图 API**（单点/多点图形）：见 `frontend/charting_library/charting_library.d.ts` 中的 `CreateShapeOptions`、`CreateMultipointShapeOptions`、`SupportedLineTools`、`DrawingOverrides` 及各 `*LineToolOverrides` 接口。Demo 与 Overrides 键名对照见 `frontend/src/tv/README-shapes.md`。

---

## 目录

- [常量](#常量)
- [枚举类型](#枚举类型)
- [接口定义](#接口定义)
- [类型别名](#类型别名)
- [函数](#函数)

---

## 常量

### `LINESTYLE_DASHED = 2`
虚线样式常量

### `LINESTYLE_DOTTED = 1`
点线样式常量

### `LINESTYLE_SOLID = 0`
实线样式常量

### `dateFormatFunctions`
日期格式化函数集合，支持多种日期格式：
- `"qq 'yy"` - 季度和年份缩写
- `"qq yyyy"` - 季度和完整年份
- `"dd MMM 'yy"` - 日、月份缩写、年份缩写
- `"MMM 'yy"` - 月份缩写、年份缩写
- `"MMM dd, yyyy"` - 月份缩写、日、完整年份
- `"MMM yyyy"` - 月份缩写、完整年份
- `"MMM dd"` - 月份缩写、日
- `"dd MMM"` - 日、月份缩写
- `"yyyy-MM-dd"` - ISO格式日期
- `"yy-MM-dd"` - 短年份-月-日
- `"yy/MM/dd"` - 短年/月/日
- `"yyyy/MM/dd"` - 完整年/月/日
- `"dd-MM-yyyy"` - 日-月-完整年
- `"dd-MM-yy"` - 日-月-短年
- `"dd/MM/yy"` - 日/月/短年
- `"dd/MM/yyyy"` - 日/月/完整年
- `"MM/dd/yy"` - 月/日/短年
- `"MM/dd/yyyy"` - 月/日/完整年

---

## 枚举类型

### `ColorType`
颜色类型
- `Solid` - 纯色
- `Gradient` - 渐变

### `DisconnectType`
断开连接类型
- `LogOut = 0` - 登出
- `FailedRestoring = 1` - 恢复失败
- `Offline = 2` - 离线
- `APIError = 3` - API错误
- `TwoFactorRequired = 4` - 需要双因素认证
- `CancelAuthorization = 5` - 取消授权
- `TimeOutForAuthorization = 6` - 授权超时
- `OauthError = 7` - OAuth错误
- `BrokenConnection = 8` - 连接中断
- `Reconnect = 9` - 重新连接
- `FailedSignIn = 10` - 登录失败

### `PlotSymbolSize`
图表符号大小
- `Auto = "auto"` - 自动
- `Tiny = "tiny"` - 极小
- `Small = "small"` - 小
- `Normal = "normal"` - 正常
- `Large = "large"` - 大
- `Huge = "huge"` - 巨大

### `StopType`
止损类型
- `StopLoss = 0` - 止损
- `TrailingStop = 1` - 移动止损
- `GuaranteedStop = 2` - 保证止损

### `BottomWidgetBarMode`
底部工具栏模式
- `Minimized = "minimized"` - 最小化
- `Normal = "normal"` - 正常
- `Maximized = "maximized"` - 最大化

### `PaneSize`
面板大小
- `Tiny = "tiny"` - 极小
- `Small = "small"` - 小
- `Medium = "medium"` - 中
- `Large = "large"` - 大

### `PropertyKeyType`
属性键类型
- `DefaultsKey = 1` - 默认值键
- `StateKey = 2` - 状态键
- `TemplateKey = 4` - 模板键

### `SearchInitiationPoint`
搜索起始点
- `SymbolSearch = "symbolSearch"` - 符号搜索
- `Watchlist = "watchlist"` - 观察列表
- `Compare = "compare"` - 比较
- `IndicatorInputs = "indicatorInputs"` - 指标输入

### `ActionId`
操作ID枚举（部分重要示例）
- `ChartAddIndicatorToAllCharts` - 添加指标到所有图表
- `ChartAddSymbolToWatchList` - 添加符号到观察列表
- `ChartChangeTimeZone` - 更改时区
- `ChartClipboardCopyPrice` - 复制价格
- `ChartRedo` - 重做
- `ChartUndo` - 撤销
- `TradingAddOrder` - 添加订单
- `TradingCancelOrder` - 取消订单
- `TradingClosePosition` - 平仓
- `WatchlistAddSymbol` - 添加符号到观察列表

### `ChartStyle`
图表样式
- `Bar = 0` - 条形图
- `Candle = 1` - 蜡烛图
- `Line = 2` - 线图
- `Area = 3` - 面积图
- `Renko = 4` - 砖形图
- `Kagi = 5` - 卡吉图
- `PnF = 6` - 点数图
- `LineBreak = 7` - 新线图
- `HeikinAshi = 8` - 平均K线
- `HollowCandle = 9` - 空心蜡烛
- `Baseline = 10` - 基线
- `HiLo = 12` - 高低图
- `Column = 13` - 柱状图
- `LineWithMarkers = 14` - 带标记线图
- `Stepline = 15` - 阶梯线图
- `HLCArea = 16` - HLC面积图
- `VolCandle = 19` - 成交量蜡烛
- `HLCBars = 21` - HLC条形图

### `ClearMarksMode`
清除标记模式
- `All = 0` - 清除所有标记
- `BarMarks = 1` - 仅清除K线标记
- `TimeScaleMarks = 2` - 仅清除时间轴标记

### `ConnectionStatus`
连接状态
- `Connected = 1` - 已连接
- `Connecting = 2` - 连接中
- `Disconnected = 3` - 已断开
- `Error = 4` - 错误

### `FilledAreaType`
填充区域类型
- `TypePlots = "plot_plot"` - 绘图填充
- `TypeHlines = "hline_hline"` - 水平线填充

### `HHistDirection`
直方图方向
- `LeftToRight = "left_to_right"` - 从左到右
- `RightToLeft = "right_to_left"` - 从右到左

### `LineStudyPlotStyle`
线研究图样式
- `Line = 0` - 线
- `Histogram = 1` - 直方图
- `Cross = 3` - 交叉
- `Area = 4` - 面积
- `Columns = 5` - 列
- `Circles = 6` - 圆
- `LineWithBreaks = 7` - 带断点线
- `AreaWithBreaks = 8` - 带断点面积
- `StepLine = 9` - 阶梯线
- `StepLineWithDiamonds = 10` - 带菱形阶梯线
- `StepLineWithBreaks = 11` - 带断点阶梯线

### `LineStyle`
线样式
- `Solid = 0` - 实线
- `Dotted = 1` - 点线
- `Dashed = 2` - 虚线

### `MarkLocation`
标记位置
- `AboveBar` - K线上方
- `BelowBar` - K线下方
- `Top` - 顶部
- `Bottom` - 底部
- `Right` - 右侧
- `Left` - 左侧
- `Absolute` - 绝对位置
- `AbsoluteUp` - 绝对位置向上
- `AbsoluteDown` - 绝对位置向下

### `MarketStatus`
市场状态
- `Open = "market"` - 开盘
- `Pre = "pre_market"` - 盘前
- `Post = "post_market"` - 盘后
- `Close = "out_of_session"` - 收盘
- `Holiday = "holiday"` - 假期

### `MenuItemType`
菜单项类型
- `Separator = "separator"` - 分隔符
- `Action = "action"` - 操作

### `NotificationType`
通知类型
- `Error = 0` - 错误
- `Success = 1` - 成功

### `OhlcStudyPlotStyle`
OHLC研究图样式
- `OhlcBars = "ohlc_bars"` - OHLC条形
- `OhlcCandles = "ohlc_candles"` - OHLC蜡烛

### `OrderOrPositionMessageType`
订单/持仓消息类型
- `Information = "information"` - 信息
- `Warning = "warning"` - 警告
- `Error = "error"` - 错误

### `OrderStatus`
订单状态
- `Canceled = 1` - 已取消
- `Filled = 2` - 已成交
- `Inactive = 3` - 未激活
- `Placing = 4` - 下单中
- `Rejected = 5` - 已拒绝
- `Working = 6` - 工作中

### `OrderStatusFilter`
订单状态筛选
- `All = 0` - 全部
- `Canceled = 1` - 已取消
- `Filled = 2` - 已成交
- `Inactive = 3` - 未激活
- `Rejected = 5` - 已拒绝
- `Working = 6` - 工作中

### `OrderTicketFocusControl`
订单对话框焦点控制
- `LimitPrice = 1` - 限价
- `StopPrice = 2` - 止损价
- `TakeProfit = 3` - 止盈
- `StopLoss = 4` - 止损
- `Quantity = 5` - 数量

### `OrderType`
订单类型
- `Limit = 1` - 限价单
- `Market = 2` - 市价单
- `Stop = 3` - 止损单
- `StopLimit = 4` - 止损限价单

### `OverrideLineStyle`
覆盖线样式
- `Solid = 0` - 实线
- `Dotted = 1` - 点线
- `Dashed = 2` - 虚线

### `OverridePriceAxisLastValueMode`
价格轴最后值显示模式
- `LastPriceAndPercentageValue = 0` - 最后价格和百分比
- `LastValueAccordingToScale = 1` - 根据刻度的最后值

### `ParentType`
父类型
- `Order = 1` - 订单
- `Position = 2` - 持仓
- `IndividualPosition = 3` - 单个持仓

### `PlDisplay`
盈亏显示方式
- `Money = 0` - 金额
- `Pips = 1` - 点值
- `Percentage = 2` - 百分比

### `PriceScaleMode`
价格刻度模式
- `Normal = 0` - 正常模式
- `Log = 1` - 对数模式
- `Percentage = 2` - 百分比模式
- `IndexedTo100 = 3` - 归一化到100

### `SeriesType`
序列类型（同ChartStyle）

### `Side`
交易方向
- `Buy = 1` - 买入
- `Sell = -1` - 卖出

### `StandardFormatterName`
标准格式化器名称
- `Date` - 日期
- `DateOrDateTime` - 日期或日期时间
- `Default` - 默认
- `Fixed` - 固定小数位
- `FixedInCurrency` - 固定货币格式
- `VariablePrecision` - 可变精度
- `FormatQuantity` - 格式化数量
- `FormatPrice` - 格式化价格
- `Percentage` - 百分比
- `Pips` - 点值
- `Profit` - 利润
- `Side` - 方向
- `Status` - 状态
- `Symbol` - 符号
- `Text` - 文本
- `Type` - 类型

### `StudyInputType`
研究输入类型
- `Integer` - 整数
- `Float` - 浮点数
- `Price` - 价格
- `Bool` - 布尔值
- `Text` - 文本
- `Symbol` - 符号
- `Session` - 交易时段
- `Source` - 数据源
- `Resolution` - 分辨率
- `Time` - 时间
- `BarTime` - K线时间
- `Color` - 颜色
- `Textarea` - 多行文本

### `StudyPlotDisplayTarget`
研究图显示目标
- `None = 0` - 不显示
- `Pane = 1` - 在面板显示
- `DataWindow = 2` - 在数据窗口显示
- `PriceScale = 4` - 在价格刻度显示
- `StatusLine = 8` - 在状态行显示
- `All = 15` - 所有位置

### `StudyPlotType`
研究图类型
- `Line` - 线
- `Colorer` - 着色器
- `BarColorer` - K线着色器
- `BgColorer` - 背景着色器
- `TextColorer` - 文本着色器
- `OhlcColorer` - OHLC着色器
- `CandleWickColorer` - 蜡烛芯着色器
- `CandleBorderColorer` - 蜡烛边框着色器
- `UpColorer` - 上涨着色器
- `DownColorer` - 下跌着色器
- `Shapes` - 形状
- `Chars` - 字符
- `Arrows` - 箭头
- `Data` - 数据
- `DataOffset` - 数据偏移
- `OhlcOpen` - OHLC开盘
- `OhlcHigh` - OHLC最高
- `OhlcLow` - OHLC最低
- `OhlcClose` - OHLC收盘

### `StudyTargetPriceScale`
研究目标价格刻度
- `Right = 0` - 右侧
- `Left = 1` - 左侧
- `NoScale = 2` - 无刻度

### `TimeFrameType`
时间框架类型
- `PeriodBack = "period-back"` - 回溯周期
- `TimeRange = "time-range"` - 时间范围

### `TimeHoursFormat`
时间小时格式
- `TwentyFourHours = "24-hours"` - 24小时制
- `TwelveHours = "12-hours"` - 12小时制

### `TradedGroupHorizontalAlignment`
交易组水平对齐
- `Left = 0` - 左对齐
- `Center = 1` - 居中对齐
- `Right = 2` - 右对齐

### `VisibilityType`
可见性类型
- `AlwaysOn = "alwaysOn"` - 始终显示
- `VisibleOnMouseOver = "visibleOnMouseOver"` - 鼠标悬停显示
- `AlwaysOff = "alwaysOff"` - 始终隐藏

---

## 接口定义

### `AbcdLineToolOverrides`
ABCD绘图工具覆盖属性
- `"linetoolabcd.bold"` - 是否粗体，默认值：`false`
- `"linetoolabcd.color"` - 颜色，默认值：`#089981`
- `"linetoolabcd.fontsize"` - 字体大小，默认值：`12`
- `"linetoolabcd.italic"` - 是否斜体，默认值：`false`
- `"linetoolabcd.linewidth"` - 线宽，默认值：`2`
- `"linetoolabcd.textcolor"` - 文本颜色，默认值：`#ffffff`

### `AcceleratorOscillatorIndicatorOverrides`
加速器震荡器指标覆盖
- `"plot.display"` - 显示设置，默认值：`15`
- `"plot.linestyle"` - 线样式，默认值：`0`
- `"plot.linewidth"` - 线宽，默认值：`1`
- `"plot.plottype"` - 绘图类型，默认值：`histogram`
- `"plot.trackprice"` - 跟踪价格，默认值：`false`
- `"plot.transparency"` - 透明度，默认值：`0`
- `"plot.color"` - 颜色，默认值：`#000080`

### `AccessList`
访问控制列表
- `type` - 列表类型：`"black"`（黑名单）或 `"white"`（白名单）
- `tools` - 工具列表

### `AccessListItem`
访问列表项
- `name` - 工具名称
- `grayed` - 是否显示为禁用状态

### `AccountManagerColumnBase`
账户管理器列基础
- `label` - 列标题
- `alignment` - 对齐方式：`"left"` 或 `"right"`
- `id` - 唯一标识符
- `formatter` - 格式化器
- `dataFields` - 数据字段数组
- `sortProp` - 排序属性
- `notSortable` - 是否可排序
- `help` - 帮助文本
- `highlightDiff` - 是否高亮差异
- `notHideable` - 是否可隐藏
- `hideByDefault` - 默认是否隐藏
- `tooltipProperty` - 工具提示属性
- `isCapitalize` - 是否首字母大写
- `showZeroValues` - 是否显示零值

### `AccountManagerInfo`
账户管理器信息
- `accountTitle` - 账户标题
- `summary` - 摘要字段
- `customFormatters` - 自定义格式化器
- `orderColumns` - 订单列
- `orderColumnsSorting` - 订单列排序
- `historyColumns` - 历史列
- `historyColumnsSorting` - 历史列排序
- `positionColumns` - 持仓列
- `individualPositionColumns` - 单个持仓列
- `pages` - 自定义页面
- `possibleOrderStatuses` - 可能的订单状态
- `marginUsed` - 已用保证金
- `contextMenuActions` - 上下文菜单操作

### `AccountManagerPage`
账户管理器页面
- `id` - 唯一标识符
- `title` - 页面标题
- `tables` - 表格数组
- `displayCounterInTab` - 是否显示计数

### `AccountManagerSummaryField`
账户管理器摘要字段
- `text` - 显示文本
- `wValue` - 可观察值
- `formatter` - 格式化器
- `isDefault` - 是否默认显示
- `informerMessage` - 提示信息

### `AccountManagerTable`
账户管理器表格
- `id` - 唯一标识符
- `title` - 表格标题
- `columns` - 列定义
- `initialSorting` - 初始排序
- `changeDelegate` - 数据变更委托
- `deleteDelegate` - 数据删除委托
- `flags` - 表格标志
- `getData` - 获取数据函数

### `AccountManagerTableFlags`
账户管理器表格标志
- `supportPagination` - 是否支持分页

### `AccountMetainfo`
账户元信息
- `id` - 账户ID
- `name` - 账户名称
- `type` - 账户类型：`"live"` 或 `"demo"`
- `currency` - 货币
- `currencySign` - 货币符号

### `AccumulationDistributionIndicatorOverrides`
累积/分配指标覆盖
- `"plot.display"` - 显示设置，默认值：`15`
- `"plot.linestyle"` - 线样式，默认值：`0`
- `"plot.linewidth"` - 线宽，默认值：`1`
- `"plot.plottype"` - 绘图类型，默认值：`line`
- `"plot.trackprice"` - 跟踪价格，默认值：`false`
- `"plot.transparency"` - 透明度，默认值：`0`
- `"plot.color"` - 颜色，默认值：`#2196F3`

### `ActionDescription`
操作描述
- `text` - 显示文本
- `separator` - 是否分隔符
- `shortcut` - 快捷键
- `tooltip` - 工具提示
- `checked` - 是否选中
- `checkedStateSource` - 选中状态获取函数
- `checkable` - 是否可勾选
- `enabled` - 是否启用
- `externalLink` - 外部链接
- `icon` - SVG图标

### `ActionDescriptionWithCallback`
带回调的操作描述（继承ActionDescription）
- `action` - 执行的回调函数

### `ActionOptions`
操作选项
- `actionId` - 操作ID
- `onExecute` - 执行处理器

### `ActionState`
操作状态
- `actionId` - 操作ID
- `active` - 是否激活
- `label` - 标签文本
- `styledLabel` - 带样式的标签
- `disabled` - 是否禁用
- `subItems` - 子项
- `checkable` - 是否可勾选
- `checked` - 是否已勾选
- `hint` - 提示
- `icon` - 图标
- `iconChecked` - 选中时图标
- `loading` - 加载中
- `shortcutHint` - 快捷键提示
- `doNotCloseOnClick` - 点击后是否关闭菜单
- `noInteractive` - 是否非交互

### `ActionsFactory`
操作工厂
- `createAction` - 创建操作
- `createAsyncAction` - 创建异步操作
- `createSeparator` - 创建分隔符

### `AdditionalSymbolInfoField`
附加符号信息字段
- `title` - 标题
- `propertyName` - 属性名

### `AdvanceDeclineIndicatorOverrides`
涨跌比指标覆盖
- `"plot.display"` - 显示设置，默认值：`15`
- `"plot.linestyle"` - 线样式，默认值：`0`
- `"plot.linewidth"` - 线宽，默认值：`1`
- `"plot.plottype"` - 绘图类型，默认值：`line`
- `"plot.trackprice"` - 跟踪价格，默认值：`false`
- `"plot.transparency"` - 透明度，默认值：`0`
- `"plot.color"` - 颜色，默认值：`#2196F3`

### `AnchoredVWAPIndicatorOverrides`
锚定VWAP指标覆盖
- `"background #1.color"` - 背景色，默认值：`#4caf50`
- `"background #1.transparency"` - 背景透明度，默认值：`95`
- `"background #1.visible"` - 背景可见性，默认值：`true`
- `"vwap.display"` - VWAP显示，默认值：`15`
- `"vwap.color"` - VWAP颜色，默认值：`#1e88e5`
- `"vwap.linestyle"` - VWAP线样式，默认值：`0`
- `"vwap.linewidth"` - VWAP线宽，默认值：`1`
- `"vwap.plottype"` - VWAP绘图类型，默认值：`line`
- `"vwap.trackprice"` - VWAP跟踪价格，默认值：`false`
- `"vwap.transparency"` - VWAP透明度，默认值：`0`

### `AreaStylePreferences`
面积图样式偏好
- `color1` - 渐变顶部颜色
- `color2` - 渐变底部颜色
- `linecolor` - 线颜色
- `linestyle` - 线样式
- `linewidth` - 线宽
- `transparency` - 透明度

### `ArnaudLegouxMovingAverageIndicatorOverrides`
Arnaud Legoux移动平均线指标覆盖
- `"plot.display"` - 显示设置，默认值：`15`
- `"plot.linestyle"` - 线样式，默认值：`0`
- `"plot.linewidth"` - 线宽，默认值：`1`
- `"plot.plottype"` - 绘图类型，默认值：`line`
- `"plot.trackprice"` - 跟踪价格，默认值：`false`
- `"plot.transparency"` - 透明度，默认值：`0`
- `"plot.color"` - 颜色，默认值：`#2196F3`

### `AroonIndicatorOverrides`
阿隆指标覆盖
- `"upper.display"` - 上线显示，默认值：`15`
- `"upper.color"` - 上线颜色，默认值：`#FB8C00`
- `"lower.display"` - 下线显示，默认值：`15`
- `"lower.color"` - 下线颜色，默认值：`#2196F3`

### `AvailableZOrderOperations`
可用Z轴顺序操作
- `bringForwardEnabled` - 是否可前移
- `bringToFrontEnabled` - 是否可置顶
- `sendBackwardEnabled` - 是否可后移
- `sendToBackEnabled` - 是否可置底

### `AverageDirectionalIndexIndicatorOverrides`
平均趋向指数指标覆盖
- `"adx.display"` - ADX显示，默认值：`15`
- `"adx.color"` - ADX颜色，默认值：`#FF5252`

### `Bar`
K线数据
- `time` - 时间戳（毫秒）
- `open` - 开盘价
- `high` - 最高价
- `low` - 最低价
- `close` - 收盘价
- `volume` - 成交量

### `BarState`
K线状态接口
- `isLast()` - 是否为最后一根K线

### `BarStylePreferences`
K线样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `barColorsOnPrevClose` - 是否根据前收盘着色
- `dontDrawOpen` - 是否不画开盘价
- `thinBars` - 是否细线

### `BaselineStylePreferences`
基线样式偏好
- `topFillColor1` - 正区域顶部填充色1
- `topFillColor2` - 正区域顶部填充色2
- `bottomFillColor1` - 负区域底部填充色1
- `bottomFillColor2` - 负区域底部填充色2
- `topLineColor` - 正区域线颜色
- `bottomLineColor` - 负区域线颜色
- `baselineColor` - 基线颜色
- `topLineWidth` - 正区域线宽
- `bottomLineWidth` - 负区域线宽
- `topLineStyle` - 正区域线样式
- `bottomLineStyle` - 负区域线样式
- `transparency` - 透明度
- `baseLevelPercentage` - 基线水平百分比

### `BollingerBandsIndicatorOverrides`
布林带指标覆盖
- `"median.color"` - 中线颜色，默认值：`#FF6D00`
- `"upper.color"` - 上线颜色，默认值：`#2196F3`
- `"lower.color"` - 下线颜色，默认值：`#2196F3`
- `"plots background.color"` - 背景色，默认值：`#2196F3`

### `BoolInputOptions`
布尔输入选项
- 继承自 `CommonInputOptions`

### `BracketOrder`
括号订单（带止损止盈的订单）
- 继承自 `BracketOrderBase` 和 `CustomFields`

### `BracketOrderBase`
括号订单基础
- `parentId` - 父订单ID
- `parentType` - 父类型

### `Brackets`
括号设置（止损止盈）
- `stopLoss` - 止损
- `guaranteedStop` - 保证止损
- `takeProfit` - 止盈
- `trailingStopPips` - 移动止损点值

### `BrokerConfigFlags`
经纪商配置标志
- `showQuantityInsteadOfAmount` - 显示数量而非金额
- `supportOrderBrackets` - 支持订单括号（止损止盈）
- `supportStopLoss` - 支持止损
- `supportTrailingStop` - 支持移动止损
- `supportGuaranteedStop` - 支持保证止损
- `supportPositions` - 支持持仓
- `supportPositionBrackets` - 支持持仓括号
- `supportIndividualPositionBrackets` - 支持单个持仓括号
- `supportPositionNetting` - 支持持仓净额
- `supportClosePosition` - 支持平仓
- `supportCloseIndividualPosition` - 支持平单个持仓
- `supportModifyOrderPrice` - 支持修改订单价格
- `supportEditAmount` - 支持编辑数量
- `supportModifyBrackets` - 支持修改括号
- `supportLevel2Data` - 支持Level2数据
- `supportMultiposition` - 支持多持仓
- `supportPLUpdate` - 支持盈亏更新
- `supportReversePosition` - 支持反向持仓
- `supportNativeReversePosition` - 支持原生反向持仓
- `supportMarketOrders` - 支持市价单
- `supportLimitOrders` - 支持限价单
- `supportStopOrders` - 支持止损单
- `supportStopLimitOrders` - 支持止损限价单
- `supportDemoLiveSwitcher` - 支持模拟/实盘切换
- `supportMarketBrackets` - 支持市价单括号
- `supportSymbolSearch` - 支持符号搜索
- `supportModifyDuration` - 支持修改有效期
- `supportModifyTrailingStop` - 支持修改移动止损
- `supportMargin` - 支持保证金
- `supportPlaceOrderPreview` - 支持下单预览
- `supportModifyOrderPreview` - 支持修改订单预览
- `supportLeverage` - 支持杠杆
- `supportLeverageButton` - 支持杠杆按钮
- `supportOrdersHistory` - 支持订单历史
- `supportAddBracketsToExistingOrder` - 支持为现有订单添加括号
- `supportBalances` - 支持余额
- `closePositionCancelsOrders` - 平仓是否取消订单
- `supportOnlyPairPositionBrackets` - 是否只支持成对持仓括号
- `supportOnlyPairOrderBrackets` - 是否只支持成对订单括号
- `supportCryptoExchangeOrderTicket` - 支持加密货币交易所订单
- `positionPLInInstrumentCurrency` - 持仓盈亏是否以工具货币显示
- `showRiskInInstrumentCurrency` - 风险是否以工具货币显示
- `supportPartialClosePosition` - 支持部分平仓
- `supportPartialCloseIndividualPosition` - 支持部分平单个持仓
- `supportCancellingBothBracketsOnly` - 是否只支持同时取消两个括号
- `supportCryptoBrackets` - 支持加密货币括号
- `showNotificationsLog` - 显示通知日志
- `supportStopOrdersInBothDirections` - 支持双向止损单
- `supportStopLimitOrdersInBothDirections` - 支持双向止损限价单
- `supportStrictCheckingLimitOrderPrice` - 支持严格检查限价单价格
- `supportExecutions` - 支持执行记录
- `supportModifyOrderType` - 支持修改订单类型
- `requiresFIFOCloseIndividualPositions` - 是否需要FIFO平仓
- `supportCustomOrderInfo` - 支持自定义订单信息
- `supportPreviewClosePosition` - 支持平仓预览

### `BrokerCustomUI`
经纪商自定义UI
- `showOrderDialog` - 显示订单对话框
- `showPositionDialog` - 显示持仓对话框
- `showCancelOrderDialog` - 显示取消订单对话框
- `showClosePositionDialog` - 显示平仓对话框
- `showReversePositionDialog` - 显示反向持仓对话框

### `CandleStylePreferences`
蜡烛图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `drawWick` - 是否画影线
- `drawBorder` - 是否画边框
- `drawBody` - 是否画实体
- `borderColor` - 边框颜色
- `borderUpColor` - 上涨边框颜色
- `borderDownColor` - 下跌边框颜色
- `wickColor` - 影线颜色
- `wickUpColor` - 上涨影线颜色
- `wickDownColor` - 下跌影线颜色
- `barColorsOnPrevClose` - 是否根据前收盘着色

### `ChaikinMoneyFlowIndicatorOverrides`
柴金资金流指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#43A047`

### `ChartData`
保存的图表数据
- `id` - 图表ID
- `name` - 图表名称
- `symbol` - 符号
- `resolution` - 分辨率
- `content` - 图表内容
- `timestamp` - 最后修改时间

### `ChartDescriptionContext`
图表描述上下文
- `chartType` - 图表类型
- `chartTypeName` - 图表类型名称
- `description` - 描述
- `symbol` - 符号
- `exchange` - 交易所
- `ticker` - 代码
- `visibleRange` - 可见范围
- `visibleData` - 可见数据
- `symbolInfo` - 符号信息
- `chartIndex` - 图表索引
- `chartCount` - 图表数量
- `priceFormatter` - 价格格式化器
- `interval` - 间隔
- `isIntraday` - 是否为日内

### `ChartMetaInfo`
图表元信息
- `id` - 图表ID
- `name` - 图表名称
- `symbol` - 符号
- `resolution` - 分辨率
- `timestamp` - 时间戳

### `ChartPropertiesOverrides`
图表属性覆盖
- `"timezone"` - 时区
- `"priceScaleSelectionStrategyName"` - 价格刻度选择策略：`"left"` | `"right"` | `"auto"`
- `"paneProperties.backgroundType"` - 面板背景类型
- `"paneProperties.background"` - 面板背景色
- `"paneProperties.backgroundGradientStartColor"` - 渐变起始色
- `"paneProperties.backgroundGradientEndColor"` - 渐变结束色
- `"paneProperties.vertGridProperties.color"` - 垂直网格颜色
- `"paneProperties.vertGridProperties.style"` - 垂直网格样式
- `"paneProperties.horzGridProperties.color"` - 水平网格颜色
- `"paneProperties.horzGridProperties.style"` - 水平网格样式
- `"paneProperties.gridLinesMode"` - 网格线模式
- `"paneProperties.crossHairProperties.color"` - 十字线颜色
- `"paneProperties.crossHairProperties.style"` - 十字线样式
- `"paneProperties.crossHairProperties.transparency"` - 十字线透明度
- `"paneProperties.crossHairProperties.width"` - 十字线宽度
- `"paneProperties.topMargin"` - 上边距
- `"paneProperties.bottomMargin"` - 下边距
- `"paneProperties.separatorColor"` - 分隔符颜色
- `"paneProperties.legendProperties.showStudyArguments"` - 显示研究参数
- `"paneProperties.legendProperties.showStudyTitles"` - 显示研究标题
- `"paneProperties.legendProperties.showStudyValues"` - 显示研究值
- `"paneProperties.legendProperties.showSeriesTitle"` - 显示序列标题
- `"paneProperties.legendProperties.showSeriesOHLC"` - 显示OHLC值
- `"paneProperties.legendProperties.showLastDayChange"` - 显示最后一天变化
- `"paneProperties.legendProperties.showBarChange"` - 显示K线变化
- `"paneProperties.legendProperties.showSeriesLegendCloseOnMobile"` - 移动端显示收盘价
- `"paneProperties.legendProperties.showVolume"` - 显示成交量
- `"paneProperties.legendProperties.showBackground"` - 显示背景
- `"paneProperties.legendProperties.backgroundTransparency"` - 背景透明度
- `"scalesProperties.lineColor"` - 轴线颜色
- `"scalesProperties.textColor"` - 文本颜色
- `"scalesProperties.fontSize"` - 字体大小
- `"scalesProperties.showSeriesLastValue"` - 显示序列最后值
- `"scalesProperties.seriesLastValueMode"` - 最后值显示模式
- `"scalesProperties.showStudyLastValue"` - 显示研究最后值
- `"scalesProperties.showSymbolLabels"` - 显示符号标签
- `"scalesProperties.showStudyPlotLabels"` - 显示研究绘图标签
- `"scalesProperties.showBidAskLabels"` - 显示买卖价标签
- `"scalesProperties.showPrePostMarketPriceLabel"` - 显示盘前盘后价格标签
- `"scalesProperties.axisHighlightColor"` - 轴线高亮颜色
- `"scalesProperties.axisLineToolLabelBackgroundColorCommon"` - 轴线工具标签背景色
- `"scalesProperties.axisLineToolLabelBackgroundColorActive"` - 激活时标签背景色
- `"scalesProperties.showPriceScaleCrosshairLabel"` - 显示价格刻度十字线标签
- `"scalesProperties.showTimeScaleCrosshairLabel"` - 显示时间刻度十字线标签
- `"scalesProperties.crosshairLabelBgColorLight"` - 十字线标签亮色背景
- `"scalesProperties.crosshairLabelBgColorDark"` - 十字线标签暗色背景
- `"scalesProperties.scaleSeriesOnly"` - 仅缩放序列
- `"mainSeriesProperties.style"` - 主序列样式
- `"mainSeriesProperties.showCountdown"` - 显示倒计时
- `"mainSeriesProperties.bidAsk.visible"` - 显示买卖价
- `"mainSeriesProperties.bidAsk.lineStyle"` - 买卖价线样式
- `"mainSeriesProperties.bidAsk.lineWidth"` - 买卖价线宽
- `"mainSeriesProperties.bidAsk.bidLineColor"` - 买价线颜色
- `"mainSeriesProperties.bidAsk.askLineColor"` - 卖价线颜色
- `"mainSeriesProperties.highLowAvgPrice.highLowPriceLinesVisible"` - 显示高低价线
- `"mainSeriesProperties.highLowAvgPrice.highLowPriceLabelsVisible"` - 显示高低价标签
- `"mainSeriesProperties.highLowAvgPrice.averageClosePriceLineVisible"` - 显示平均收盘价线
- `"mainSeriesProperties.highLowAvgPrice.averageClosePriceLabelVisible"` - 显示平均收盘价标签
- `"mainSeriesProperties.visible"` - 主序列可见性
- `"mainSeriesProperties.sessionId"` - 交易时段ID
- `"mainSeriesProperties.showPriceLine"` - 显示价格线
- `"mainSeriesProperties.priceLineWidth"` - 价格线宽
- `"mainSeriesProperties.priceLineColor"` - 价格线颜色
- `"mainSeriesProperties.showPrevClosePriceLine"` - 显示前收盘价线
- `"mainSeriesProperties.prevClosePriceLineWidth"` - 前收盘价线宽
- `"mainSeriesProperties.prevClosePriceLineColor"` - 前收盘价线颜色
- `"mainSeriesProperties.minTick"` - 最小跳动点
- `"mainSeriesProperties.statusViewStyle.showExchange"` - 显示交易所
- `"mainSeriesProperties.statusViewStyle.showInterval"` - 显示间隔
- `"mainSeriesProperties.statusViewStyle.symbolTextSource"` - 符号文本来源

### `ChartTemplate`
图表模板
- `content` - 模板内容

### `ChartTemplateContent`
图表模板内容
- `chartProperties` - 图表属性
- `mainSourceProperties` - 主源属性
- `version` - 版本

### `ChartingLibraryWidgetConstructor`
图表库构件构造函数
- `new (options: ChartingLibraryWidgetOptions | TradingTerminalWidgetOptions)` - 创建新实例

### `ChartingLibraryWidgetOptions`
图表库构件选项
- `container` - 容器元素
- `datafeed` - 数据源
- `interval` - 默认间隔
- `symbol` - 默认符号
- `auto_save_delay` - 自动保存延迟
- `autosize` - 是否自动调整大小
- `debug` - 调试模式
- `disabled_features` - 禁用的功能
- `drawings_access` - 绘图访问控制
- `enabled_features` - 启用的功能
- `fullscreen` - 全屏模式
- `library_path` - 库路径
- `locale` - 语言环境
- `numeric_formatting` - 数字格式化
- `saved_data` - 保存的数据
- `saved_data_meta_info` - 保存数据的元信息
- `studies_access` - 研究访问控制
- `study_count_limit` - 研究数量限制
- `symbol_search_request_delay` - 符号搜索请求延迟
- `timeframe` - 时间框架
- `timezone` - 时区
- `toolbar_bg` - 工具栏背景色
- `width` - 宽度
- `height` - 高度
- `charts_storage_url` - 图表存储URL
- `charts_storage_api_version` - 图表存储API版本
- `client_id` - 客户端ID
- `user_id` - 用户ID
- `load_last_chart` - 是否加载最后图表
- `studies_overrides` - 研究覆盖
- `custom_formatters` - 自定义格式化器
- `overrides` - 覆盖属性
- `snapshot_url` - 快照URL
- `time_frames` - 时间框架
- `custom_css_url` - 自定义CSS URL
- `custom_font_family` - 自定义字体
- `favorites` - 收藏夹
- `save_load_adapter` - 保存加载适配器
- `loading_screen` - 加载屏幕选项
- `settings_adapter` - 设置适配器
- `theme` - 主题
- `compare_symbols` - 比较符号
- `custom_indicators_getter` - 自定义指标获取器
- `additional_symbol_info_fields` - 附加符号信息字段
- `header_widget_buttons_mode` - 头部按钮模式
- `context_menu` - 上下文菜单选项
- `time_scale` - 时间刻度选项
- `custom_translate_function` - 自定义翻译函数
- `symbol_search_complete` - 符号搜索完成函数
- `settings_overrides` - 设置覆盖
- `custom_timezones` - 自定义时区
- `custom_chart_description_function` - 自定义图表描述函数
- `custom_themes` - 自定义主题
- `image_storage_adapter` - 图像存储适配器

### `CheckboxFieldMetaInfo`
复选框字段元信息
- `inputType` - 输入类型：`"Checkbox"`
- `value` - 值
- `supportModify` - 是否支持修改
- `help` - 帮助信息

### `ClientSnapshotOptions`
客户端快照选项
- `backgroundColor` - 背景色
- `borderColor` - 边框色
- `font` - 字体
- `fontSize` - 字体大小
- `legendMode` - 图例模式
- `hideResolution` - 隐藏分辨率
- `hideStudiesFromLegend` - 从图例隐藏研究

### `Colors`
颜色工具
- `blue` - 蓝色：`"#2962ff"`
- `gray` - 灰色：`"#787B86"`
- `green` - 绿色：`"#4CAF50"`
- `olive` - 橄榄色：`"#808000"`
- `teal` - 青色：`"#00897B"`
- `new` - 创建新颜色函数

### `ColumnStylePreferences`
柱状图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `barColorsOnPrevClose` - 是否根据前收盘着色
- `baselinePosition` - 基线位置

### `CommonFillOptions`
公共填充选项
- `display` - 显示设置
- `title` - 标题

### `CommonInputOptions`
公共输入选项
- `confirm` - 是否需要确认
- `display` - 显示设置
- `group` - 分组
- `inline` - 内联
- `tooltip` - 工具提示

### `CompareIndicatorOverrides`
比较指标覆盖
- `"plot.color"` - 颜色，默认值：`#9C27B0`

### `CompareSymbol`
比较符号
- `symbol` - 符号标识
- `title` - 标题

### `ContextMenuItem`
上下文菜单项
- `position` - 位置：`"top"` 或 `"bottom"`
- `text` - 文本
- `click` - 点击回调

### `ContextMenuOptions`
上下文菜单选项
- `items_processor` - 项处理器
- `renderer_factory` - 渲染器工厂

### `ContextMenuPosition`
上下文菜单位置
- `clientX` - X坐标
- `clientY` - Y坐标
- `touches` - 触摸点数组
- `attachToXBy` - X轴附着方式
- `attachToYBy` - Y轴附着方式
- `box` - 位置盒子
- `marginX` - X轴边距
- `marginY` - Y轴边距

### `CreateAnchoredShapeOptions`
创建锚定形状选项
- `shape` - 形状类型：`"anchored_text"` 或 `"anchored_note"`

### `CreateContextMenuParams`
创建上下文菜单参数
- `menuName` - 菜单名称
- `detail` - 详细信息

### `CreateHTMLButtonOptions`
创建HTML按钮选项
- `align` - 对齐方式
- `useTradingViewStyle` - 是否使用TradingView样式

### `CreateMultipointShapeOptions`
创建多点形状选项
- `shape` - 形状类型

### `CreateShapeOptions`
创建形状选项
- `shape` - 形状类型
- `ownerStudyId` - 所属研究ID

### `CreateShapeOptionsBase`
创建形状选项基础
- `text` - 文本
- `lock` - 是否锁定
- `disableSelection` - 禁用选择
- `disableSave` - 禁用保存
- `disableUndo` - 禁用撤销
- `overrides` - 覆盖属性
- `zOrder` - Z轴顺序
- `showInObjectsTree` - 是否显示在对象树
- `ownerStudyId` - 所属研究ID
- `filled` - 是否填充
- `icon` - 图标

### `CreateStudyOptions`
创建研究选项
- `checkLimit` - 是否检查限制
- `priceScale` - 价格刻度
- `allowChangeCurrency` - 允许更改货币
- `allowChangeUnit` - 允许更改单位
- `disableUndo` - 禁用撤销

### `CreateStudyTemplateOptions`
创建研究模板选项
- `saveSymbol` - 保存符号
- `saveInterval` - 保存间隔

### `CreateTradingViewStyledButtonOptions`
创建TradingView样式按钮选项
- `align` - 对齐方式
- `useTradingViewStyle` - 使用TradingView样式
- `text` - 文本
- `title` - 标题
- `onClick` - 点击回调

### `CrossHairMovedEventParams`
十字线移动事件参数
- `time` - 时间戳
- `price` - 价格
- `userTime` - 用户时区时间
- `entityValues` - 实体值
- `offsetX` - X偏移
- `offsetY` - Y偏移

### `CrossHairMovedEventSource`
十字线移动事件源
- `isHovered` - 是否悬停
- `title` - 标题
- `values` - 值数组

### `CryptoBalance`
加密货币余额
- `symbol` - 符号
- `total` - 总额
- `available` - 可用额
- `reserved` - 保留额
- `value` - 价值
- `valueCurrency` - 价值货币
- `longName` - 长名称
- `btcValue` - 比特币价值

### `CurrencyInfo`
货币信息
- `selectedCurrency` - 选中的货币
- `originalCurrencies` - 原始货币
- `currencies` - 可用货币
- `symbols` - 符号列表

### `CurrencyItem`
货币项
- `id` - 唯一ID
- `code` - 货币代码
- `logoUrl` - 图标URL
- `description` - 描述

### `CustomAliasedTimezone`
自定义时区别名
- `alias` - 时区别名
- `title` - 标题

### `CustomComboBoxItem`
自定义组合框项
- `text` - 文本
- `value` - 值

### `CustomComboBoxMetaInfo`
自定义组合框元信息
- `inputType` - 输入类型：`"ComboBox"`
- `items` - 项列表

### `CustomFieldMetaInfoBase`
自定义字段元信息基础
- `inputType` - 输入类型
- `id` - ID
- `title` - 标题
- `value` - 值
- `saveToSettings` - 是否保存到设置

### `CustomFields`
自定义字段
- `[key: string]` - 任意自定义字段

### `CustomFormatter`
自定义格式化器
- `format` - 格式化日期时间
- `formatLocal` - 格式化为本地时间
- `parse` - 解析字符串

### `CustomFormatters`
自定义格式化器集合
- `timeFormatter` - 时间格式化器
- `dateFormatter` - 日期格式化器
- `tickMarkFormatter` - 刻度标记格式化器
- `priceFormatterFactory` - 价格格式化器工厂
- `studyFormatterFactory` - 研究格式化器工厂

### `CustomIndicator`
自定义指标
- `name` - 指标名称
- `metainfo` - 元信息
- `constructor` - 构造函数

### `CustomInputFieldMetaInfo`
自定义输入字段元信息
- `preventModify` - 禁止修改
- `placeHolder` - 占位符
- `validator` - 验证器
- `customInfo` - 自定义信息

### `CustomInputFieldsValues`
自定义输入字段值
- `[fieldId: string]` - 字段值

### `CustomStatusDropDownAction`
自定义状态下拉操作
- `text` - 文本
- `tooltip` - 工具提示
- `onClick` - 点击回调

### `CustomStatusDropDownContent`
自定义状态下拉内容
- `title` - 标题
- `color` - 颜色
- `icon` - 图标
- `content` - 内容数组
- `action` - 操作

### `CustomStudyFormatterFormat`
自定义研究格式化器格式
- `type` - 类型：`"price"` | `"volume"` | `"percent"` | `"inherit"`
- `precision` - 精度

### `CustomTableElementFormatter`
自定义表格元素格式化器
- `name` - 名称
- `formatElement` - 格式化元素函数
- `formatText` - 格式化文本函数
- `isPriceFormatterNeeded` - 是否需要价格格式化器

### `CustomThemeColors`
自定义主题颜色
- `color1` - 颜色1（TradingView蓝）
- `color2` - 颜色2（TradingView灰）
- `color3` - 颜色3（TradingView红）
- `color4` - 颜色4（TradingView绿）
- `color5` - 颜色5（TradingView橙）
- `color6` - 颜色6（TradingView紫）
- `color7` - 颜色7（TradingView黄）
- `white` - 白色
- `black` - 黑色

### `CustomThemes`
自定义主题
- `light` - 亮色主题
- `dark` - 暗色主题

### `CustomTimezoneInfo`
自定义时区信息
- `alias` - 时区别名
- `title` - 标题

### `DOMData`
深度市场数据（订单簿）
- `snapshot` - 是否为快照
- `asks` - 卖单层级
- `bids` - 买单层级

### `DOMLevel`
深度市场层级
- `price` - 价格
- `volume` - 成交量

### `DatafeedConfiguration`
数据源配置
- `exchanges` - 交易所列表
- `supported_resolutions` - 支持的分辨率
- `units` - 支持的单位组
- `currency_codes` - 货币代码
- `supports_marks` - 是否支持标记
- `supports_time` - 是否支持时间
- `supports_timescale_marks` - 是否支持时间刻度标记
- `symbols_types` - 符号类型
- `symbols_grouping` - 符号分组

### `DatafeedQuoteValues`
数据源报价值
- `ch` - 价格变化
- `chp` - 价格变化百分比
- `short_name` - 短名称
- `exchange` - 交易所
- `description` - 描述
- `lp` - 最后价格
- `ask` - 卖价
- `bid` - 买价
- `spread` - 价差
- `open_price` - 开盘价
- `high_price` - 最高价
- `low_price` - 最低价
- `prev_close_price` - 前收盘价
- `volume` - 成交量
- `original_name` - 原始名称
- `rtc` - 盘前/盘后价格
- `rtc_time` - 盘前/盘后价格更新时间
- `rch` - 盘前/盘后价格变化
- `rchp` - 盘前/盘后价格变化百分比

### `DatafeedSymbolType`
数据源符号类型
- `name` - 类型名称
- `value` - 类型值

### `DefaultContextMenuActionsParams`
默认上下文菜单操作参数

### `DefaultDropdownActionsParams`
默认下拉菜单操作参数
- `tradingProperties` - 显示交易属性
- `restoreConfirmations` - 恢复确认

### `DialogParams`
对话框参数
- `title` - 标题
- `body` - 内容
- `callback` - 回调

### `DisconnectionInfo`
断开连接信息
- `message` - 消息
- `heading` - 标题
- `additionalInfo` - 附加信息
- `disconnectType` - 断开类型

### `DragStartParams`
拖拽开始参数
- `preventDefault` - 阻止默认事件
- `hoveredSourceId` - 悬停源ID
- `exportData` - 导出数据函数
- `setData` - 设置数据函数
- `setDragImage` - 设置拖拽图像
- `keys` - 按键状态

### `DropdownItem`
下拉菜单项
- `title` - 标题
- `icon` - 图标
- `onSelect` - 选择回调

### `DropdownParams`
下拉菜单参数
- `title` - 标题
- `items` - 菜单项
- `tooltip` - 工具提示
- `icon` - 图标
- `align` - 对齐方式

### `EMACrossIndicatorOverrides`
EMA交叉指标覆盖
- `"short:plot.color"` - 短期EMA颜色，默认值：`#FF6D00`
- `"long:plot.color"` - 长期EMA颜色，默认值：`#43A047`
- `"crosses.color"` - 交叉点颜色，默认值：`#2196F3`

### `EditObjectDialogEventParams`
编辑对象对话框事件参数
- `objectType` - 对象类型
- `scriptTitle` - 脚本标题

### `EntityInfo`
实体信息
- `id` - 实体ID
- `name` - 实体名称

### `Execution`
执行记录
- `symbol` - 符号
- `price` - 价格
- `qty` - 数量
- `side` - 方向
- `time` - 时间
- `commission` - 佣金
- `netAmount` - 净额

### `ExportDataOptions`
导出数据选项
- `from` - 开始时间
- `to` - 结束时间
- `includeTime` - 包含时间
- `includeUserTime` - 包含用户时间
- `includeSeries` - 包含序列
- `includeDisplayedValues` - 包含显示值
- `includedStudies` - 包含的研究
- `includeOffsetStudyValues` - 包含偏移研究值
- `includeOHLCValuesForSingleValuePlots` - 包含单值图的OHLC值
- `includeHiddenStudies` - 包含隐藏研究

### `ExportedData`
导出的数据
- `schema` - 字段描述符数组
- `data` - 数据数组
- `displayedData` - 显示数据数组

### `Favorites`
收藏夹
- `intervals` - 间隔列表
- `indicators` - 指标列表
- `chartTypes` - 图表类型列表
- `drawingTools` - 绘图工具列表

### `GradientFillOptions`
渐变填充选项
- `bottomColor` - 底部颜色
- `topColor` - 顶部颜色

### `GrayedObject`
灰色对象
- `type` - 类型：`"drawing"` 或 `"study"`
- `name` - 名称

### `HHistPreferences`
直方图偏好
- `colors` - 颜色数组
- `transparencies` - 透明度数组
- `visible` - 可见性
- `percentWidth` - 宽度百分比
- `showValues` - 显示值
- `valuesColor` - 值颜色
- `direction` - 方向

### `HLCAreaStylePreferences`
HLC面积图样式偏好
- `highLineVisible` - 最高线可见
- `highLineColor` - 最高线颜色
- `highLineStyle` - 最高线样式
- `highLineWidth` - 最高线宽度
- `lowLineVisible` - 最低线可见
- `lowLineColor` - 最低线颜色
- `lowLineStyle` - 最低线样式
- `lowLineWidth` - 最低线宽度
- `closeLineColor` - 收盘线颜色
- `closeLineStyle` - 收盘线样式
- `closeLineWidth` - 收盘线宽度
- `highCloseFillColor` - 高-收盘填充色
- `closeLowFillColor` - 收盘-低填充色

### `HLCBarsStylePreferences`
HLC条形图样式偏好
- `color` - 颜色
- `thinBars` - 细线

### `HLine`
水平线
- `id` - ID

### `HeikinAshiStylePreferences`
平均K线样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `drawWick` - 画影线
- `drawBorder` - 画边框
- `drawBody` - 画实体
- `borderColor` - 边框颜色
- `borderUpColor` - 上涨边框颜色
- `borderDownColor` - 下跌边框颜色
- `wickColor` - 影线颜色
- `wickUpColor` - 上涨影线颜色
- `wickDownColor` - 下跌影线颜色
- `showRealLastPrice` - 显示真实最后价格
- `barColorsOnPrevClose` - 根据前收盘着色

### `HiLoStylePreferences`
高低图样式偏好
- `color` - 颜色
- `showBorders` - 显示边框
- `borderColor` - 边框颜色
- `showLabels` - 显示标签
- `labelColor` - 标签颜色
- `drawBody` - 画实体

### `HistoryMetadata`
历史元数据
- `noData` - 无数据
- `nextTime` - 下一个可用时间

### `HlineOptions`
水平线选项
- `color` - 颜色
- `display` - 显示设置
- `linestyle` - 线样式
- `linewidth` - 线宽
- `title` - 标题

### `HollowCandleStylePreferences`
空心蜡烛样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `drawWick` - 画影线
- `drawBorder` - 画边框
- `drawBody` - 画实体
- `borderColor` - 边框颜色
- `borderUpColor` - 上涨边框颜色
- `borderDownColor` - 下跌边框颜色
- `wickColor` - 影线颜色
- `wickUpColor` - 上涨影线颜色
- `wickDownColor` - 下跌影线颜色

### `HorizLinePreferences`
水平线偏好
- `visible` - 可见性
- `width` - 宽度
- `color` - 颜色
- `style` - 样式
- `showPrice` - 显示价格

### `HyperlinkInfo`
超链接信息
- `text` - 文本
- `url` - URL

### `IAction`
操作接口
- `type` - 类型
- `execute()` - 执行方法
- `getState()` - 获取状态
- `onUpdate()` - 更新订阅

### `IBoxedValue<T>`
盒装值接口
- `setValue(value: T)` - 设置值

### `IBoxedValueReadOnly<T>`
只读盒装值接口
- `value()` - 获取值

### `IBrokerAccountInfo`
经纪商账户信息接口
- `accountsMetainfo()` - 获取账户元信息
- `currentAccount()` - 获取当前账户
- `setCurrentAccount?(id: AccountId)` - 设置当前账户

### `IBrokerCommon`
经纪商公共接口
- `chartContextMenuActions(context: TradeContext, options?: DefaultContextMenuActionsParams)` - 图表上下文菜单操作
- `isTradable(symbol: string)` - 是否可交易
- `connectionStatus()` - 连接状态
- `orders()` - 获取订单
- `ordersHistory?()` - 获取订单历史
- `positions?()` - 获取持仓
- `individualPositions?()` - 获取单个持仓
- `executions(symbol: string)` - 获取执行记录
- `symbolInfo(symbol: string)` - 获取符号信息
- `accountManagerInfo()` - 获取账户管理器信息
- `formatter?(symbol: string, alignToMinMove: boolean)` - 格式化器
- `spreadFormatter?(symbol: string)` - 价差格式化器
- `quantityFormatter?(symbol: string)` - 数量格式化器
- `getOrderDialogOptions?(symbol: string)` - 获取订单对话框选项
- `getPositionDialogOptions?(symbol: string)` - 获取持仓对话框选项
- `getSymbolSpecificTradingOptions?(symbol: string)` - 获取符号特定交易选项

### `IBrokerConnectionAdapterFactory`
经纪商连接适配器工厂
- `createDelegate<T extends Function>()` - 创建委托
- `createWatchedValue<T>(value?: T)` - 创建可观察值
- `createPriceFormatter(priceScale?: number, minMove?: number, fractional?: boolean, minMove2?: number, variableMinTick?: string)` - 创建价格格式化器

### `IBrokerConnectionAdapterHost`
经纪商连接适配器主机
- `factory` - 工厂
- `connectionStatusUpdate(status: ConnectionStatus, info?: DisconnectionInfo)` - 连接状态更新
- `defaultFormatter(symbol: string, alignToMinMove: boolean)` - 默认格式化器
- `numericFormatter(decimalPlaces: number)` - 数字格式化器
- `quantityFormatter(decimalPlaces?: number)` - 数量格式化器
- `defaultContextMenuActions(context: TradeContext, params?: DefaultContextMenuActionsParams)` - 默认上下文菜单操作
- `defaultDropdownMenuActions(options?: Partial<DefaultDropdownActionsParams>)` - 默认下拉菜单操作
- `sellBuyButtonsVisibility()` - 买卖按钮可见性
- `domPanelVisibility()` - DOM面板可见性
- `orderPanelVisibility()` - 订单面板可见性
- `silentOrdersPlacement()` - 静默下单
- `patchConfig(config: Partial<BrokerConfigFlags>)` - 修补配置
- `setDurations(durations: OrderDurationMetaInfo[])` - 设置有效期
- `orderUpdate(order: Order)` - 订单更新
- `ordersFullUpdate()` - 订单完全更新
- `orderPartialUpdate(id: string, orderChanges: Partial<Order>)` - 订单部分更新
- `positionUpdate(position: Position, isHistoryUpdate?: boolean)` - 持仓更新
- `positionsFullUpdate()` - 持仓完全更新
- `positionPartialUpdate(id: string, positionChanges: Partial<Position>)` - 持仓部分更新
- `individualPositionUpdate(individualPosition: IndividualPosition, isHistoryUpdate?: boolean)` - 单个持仓更新
- `individualPositionsFullUpdate()` - 单个持仓完全更新
- `individualPositionPartialUpdate(id: string, changes: Partial<IndividualPosition>)` - 单个持仓部分更新
- `executionUpdate(execution: Execution)` - 执行更新
- `currentAccountUpdate()` - 当前账户更新
- `realtimeUpdate(symbol: string, data: TradingQuotes)` - 实时报价更新
- `plUpdate(positionId: string, pl: number)` - 盈亏更新
- `pipValueUpdate(symbol: string, pipValues: PipValues)` - 点值更新
- `individualPositionPLUpdate(individualPositionId: string, pl: number)` - 单个持仓盈亏更新
- `equityUpdate(equity: number)` - 权益更新
- `marginAvailableUpdate(marginAvailable: number)` - 可用保证金更新
- `cryptoBalanceUpdate(symbol: string, balance: CryptoBalance)` - 加密货币余额更新
- `domUpdate(symbol: string, equity: DOMData)` - DOM更新
- `setQty(symbol: string, quantity: number)` - 设置数量
- `getQty(symbol: string)` - 获取数量
- `subscribeSuggestedQtyChange(symbol: string, listener: SuggestedQtyChangedListener)` - 订阅建议数量变化
- `unsubscribeSuggestedQtyChange(symbol: string, listener: SuggestedQtyChangedListener)` - 取消订阅建议数量变化
- `showOrderDialog?<T extends PreOrder>(order: T, focus?: OrderTicketFocusControl)` - 显示订单对话框
- `showNotification(title: string, text: string, notificationType?: NotificationType)` - 显示通知
- `showCancelOrderDialog(orderId: string, handler: () => Promise<void>)` - 显示取消订单对话框
- `showCancelMultipleOrdersDialog(symbol: string, side: Side, qty: number, handler: () => Promise<void>)` - 显示取消多个订单对话框
- `showCancelBracketsDialog(orderId: string, handler: () => Promise<void>)` - 显示取消括号对话框
- `showCancelMultipleBracketsDialog(orderId: string, handler: () => Promise<void>)` - 显示取消多个括号对话框
- `showReversePositionDialog(position: string, handler: () => Promise<boolean>)` - 显示反向持仓对话框
- `showPositionBracketsDialog(position: Position | IndividualPosition, brackets: Brackets, focus: OrderTicketFocusControl)` - 显示持仓括号对话框
- `activateBottomWidget()` - 激活底部构件
- `getAccountManagerVisibilityMode()` - 获取账户管理器可见模式
- `setAccountManagerVisibilityMode(mode: BottomWidgetBarMode)` - 设置账户管理器可见模式
- `showTradingProperties()` - 显示交易属性
- `getSymbolMinTick(symbol: string)` - 获取符号最小跳动
- `showMessageDialog(title: string, text: string, textHasHTML?: boolean)` - 显示消息对话框
- `showConfirmDialog(title: string, content: string | string[], mainButtonText?: string, cancelButtonText?: string, showDisableConfirmationsCheckbox?: boolean)` - 显示确认对话框
- `showSimpleConfirmDialog(title: string, content: string | string[], mainButtonText?: string, cancelButtonText?: string, showDisableConfirmationsCheckbox?: boolean)` - 显示简单确认对话框
- `getOrderTicketSetting<K extends keyof OrderTicketSettings>(settingName: K)` - 获取订单工单设置
- `setOrderTicketSetting<K extends keyof OrderTicketSettings>(settingName: K, value: OrderTicketSettings[K])` - 设置订单工单设置

### `IBrokerTerminal`
经纪商终端接口
- `placeOrder(order: PreOrder, confirmId?: string)` - 下单
- `previewOrder?(order: PreOrder)` - 预览订单
- `modifyOrder(order: Order, confirmId?: string)` - 修改订单
- `cancelOrder(orderId: string)` - 取消订单
- `cancelOrders?(symbol: string, side: Side | undefined, ordersIds: string[])` - 取消多个订单
- `reversePosition?(positionId: string)` - 反向持仓
- `closePosition?(positionId: string, amount?: number, confirmId?: string)` - 平仓
- `closeIndividualPosition?(individualPositionId: string, amount?: number, confirmId?: string)` - 平单个持仓
- `editPositionBrackets?(positionId: string, brackets: Brackets, customFields?: CustomInputFieldsValues)` - 编辑持仓括号
- `editIndividualPositionBrackets?(individualPositionId: string, brackets: Brackets)` - 编辑单个持仓括号
- `leverageInfo?(leverageInfoParams: LeverageInfoParams)` - 获取杠杆信息
- `setLeverage?(leverageSetParams: LeverageSetParams)` - 设置杠杆
- `previewLeverage?(leverageSetParams: LeverageSetParams)` - 预览杠杆
- `subscribeEquity?()` - 订阅权益
- `subscribeMarginAvailable?(symbol: string)` - 订阅可用保证金
- `subscribePipValue?(symbol: string)` - 订阅点值
- `unsubscribePipValue?(symbol: string)` - 取消订阅点值
- `unsubscribeMarginAvailable?(symbol: string)` - 取消订阅可用保证金
- `unsubscribeEquity?()` - 取消订阅权益

### `IChartWidgetApi`
图表构件API
- `onDataLoaded()` - 数据加载完成订阅
- `onSymbolChanged()` - 符号变更订阅
- `onIntervalChanged()` - 间隔变更订阅
- `onVisibleRangeChanged()` - 可见范围变更订阅
- `onChartTypeChanged()` - 图表类型变更订阅
- `dataReady(callback?: () => void)` - 数据就绪检查
- `crossHairMoved()` - 十字线移动订阅
- `onHoveredSourceChanged()` - 悬停源变更订阅
- `setVisibleRange(range: SetVisibleTimeRange, options?: SetVisibleRangeOptions)` - 设置可见范围
- `setSymbol(symbol: string, options?: SetSymbolOptions | (() => void))` - 设置符号
- `setResolution(resolution: ResolutionString, options?: SetResolutionOptions | (() => void))` - 设置分辨率
- `setChartType(type: SeriesType, callback?: () => void)` - 设置图表类型
- `resetData()` - 重置数据
- `executeActionById(actionId: ChartActionId)` - 执行操作
- `getCheckableActionState(actionId: ChartActionId)` - 获取可勾选操作状态
- `refreshMarks()` - 刷新标记
- `clearMarks(marksToClear?: ClearMarksMode)` - 清除标记
- `getAllShapes()` - 获取所有形状
- `getAllStudies()` - 获取所有研究
- `getPriceToBarRatio()` - 获取价格与K线比例
- `setPriceToBarRatio(ratio: number, options?: UndoOptions)` - 设置价格与K线比例
- `isPriceToBarRatioLocked()` - 价格与K线比例是否锁定
- `setPriceToBarRatioLocked(value: boolean, options?: UndoOptions)` - 锁定/解锁价格与K线比例
- `getAllPanesHeight()` - 获取所有面板高度
- `setAllPanesHeight(heights: readonly number[])` - 设置所有面板高度
- `maximizeChart()` - 最大化图表
- `isMaximized()` - 是否最大化
- `restoreChart()` - 恢复图表
- `availableZOrderOperations(sources: readonly EntityId[])` - 可用Z轴顺序操作
- `sendToBack(entities: readonly EntityId[])` - 置底
- `bringToFront(sources: readonly EntityId[])` - 置顶
- `bringForward(sources: readonly EntityId[])` - 前移
- `sendBackward(sources: readonly EntityId[])` - 后移
- `createStudy<TOverrides extends Partial<SingleIndicatorOverrides>>(name: string, forceOverlay?: boolean, lock?: boolean, inputs?: Record<string, StudyInputValue>, overrides?: TOverrides, options?: CreateStudyOptions)` - 创建研究
- `getStudyById(entityId: EntityId)` - 获取研究
- `getSeries()` - 获取序列
- `createShape<TOverrides extends object>(point: ShapePoint, options: CreateShapeOptions<TOverrides>)` - 创建形状
- `createMultipointShape<TOverrides extends object>(points: ShapePoint[], options: CreateMultipointShapeOptions<TOverrides>)` - 创建多点形状
- `createAnchoredShape<TOverrides extends object>(position: PositionPercents, options: CreateAnchoredShapeOptions<TOverrides>)` - 创建锚定形状
- `getShapeById(entityId: EntityId)` - 获取形状
- `removeEntity(entityId: EntityId, options?: UndoOptions)` - 移除实体
- `removeAllShapes()` - 移除所有形状
- `removeAllStudies()` - 移除所有研究
- `selection()` - 获取选择API
- `showPropertiesDialog(studyId: EntityId)` - 显示属性对话框
- `createStudyTemplate(options: CreateStudyTemplateOptions)` - 创建研究模板
- `applyStudyTemplate(template: object)` - 应用研究模板
- `createOrderLine()` - 创建订单线
- `createPositionLine()` - 创建持仓线
- `createExecutionShape()` - 创建执行形状
- `symbol()` - 获取当前符号
- `symbolExt()` - 获取扩展符号信息
- `resolution()` - 获取当前分辨率
- `getVisibleRange()` - 获取可见范围
- `getVisibleBarsRange()` - 获取可见K线范围
- `priceFormatter()` - 获取价格格式化器
- `chartType()` - 获取图表类型
- `getTimezoneApi()` - 获取时区API
- `getPanes()` - 获取面板数组
- `exportData(options?: Partial<ExportDataOptions>)` - 导出数据
- `setDragExportEnabled(enabled: boolean)` - 设置拖拽导出
- `canZoomOut()` - 能否缩小
- `canZoomOutWV()` - 可观察的能否缩小
- `zoomOut()` - 缩小
- `setZoomEnabled(enabled: boolean)` - 设置缩放启用
- `setScrollEnabled(enabled: boolean)` - 设置滚动启用
- `shapesGroupController()` - 获取形状组控制器
- `barTimeToEndOfPeriod(unixTime: number)` - K线时间转换为周期结束时间
- `endOfPeriodToBarTime(unixTime: number)` - 周期结束时间转换为K线时间
- `getTimeScale()` - 获取时间刻度API
- `isSelectBarRequested()` - 是否请求选择K线
- `requestSelectBar()` - 请求选择K线
- `cancelSelectBar()` - 取消选择K线
- `loadChartTemplate(templateName: string)` - 加载图表模板
- `marketStatus()` - 获取市场状态
- `setTimeFrame(timeFrame: RangeOptions)` - 设置时间框架
- `getLineToolsState()` - 获取线工具状态
- `applyLineToolsState(state: LineToolsAndGroupsState)` - 应用线工具状态
- `reloadLineToolsFromServer()` - 从服务器重新加载线工具
- `inactivityGaps()` - 获取不活跃缺口设置

### `IChartingLibraryWidget`
图表库构件接口
- `headerReady()` - 头部就绪
- `onChartReady(callback: EmptyCallback)` - 图表就绪回调
- `onGrayedObjectClicked(callback: (obj: GrayedObject) => void)` - 灰色对象点击回调
- `onShortcut(shortCut: string | number | (string | number)[], callback: EmptyCallback)` - 快捷键回调
- `subscribe<EventName extends keyof SubscribeEventsMap>(event: EventName, callback: SubscribeEventsMap[EventName])` - 订阅事件
- `unsubscribe<EventName extends keyof SubscribeEventsMap>(event: EventName, callback: SubscribeEventsMap[EventName])` - 取消订阅事件
- `chart(index?: number)` - 获取图表API
- `getLanguage()` - 获取语言
- `setSymbol(symbol: string, interval: ResolutionString, callback: EmptyCallback)` - 设置符号
- `remove()` - 移除构件
- `closePopupsAndDialogs()` - 关闭弹出窗口和对话框
- `selectLineTool(linetool: "icon", options?: IconOptions)` - 选择线工具
- `selectLineTool(linetool: Omit<"icon", SupportedLineTools>)` - 选择线工具
- `selectLineTool(linetool: SupportedLineTools, options?: IconOptions | EmojiOptions)` - 选择线工具
- `selectedLineTool()` - 获取选中的线工具
- `save(callback: (state: object) => void, options?: SaveChartOptions)` - 保存图表状态
- `load(state: object, extendedData?: SavedStateMetaInfo)` - 加载图表状态
- `getSavedCharts(callback: (chartRecords: SaveLoadChartRecord[]) => void)` - 获取保存的图表
- `loadChartFromServer(chartRecord: SaveLoadChartRecord)` - 从服务器加载图表
- `saveChartToServer(onComplete?: EmptyCallback, onFail?: (error: SaveChartErrorInfo) => void, options?: SaveChartToServerOptions)` - 保存图表到服务器
- `removeChartFromServer(chartId: string | number, onCompleteCallback: EmptyCallback)` - 从服务器移除图表
- `onContextMenu(callback: (unixTime: number, price: number) => ContextMenuItem[])` - 上下文菜单回调
- `createButton(options?: CreateHTMLButtonOptions)` - 创建按钮
- `createButton(options: CreateTradingViewStyledButtonOptions)` - 创建按钮
- `createButton(options?: CreateButtonOptions)` - 创建按钮
- `removeButton(buttonIdOrHtmlElement: HTMLElement | string)` - 移除按钮
- `createDropdown(params: DropdownParams)` - 创建下拉菜单
- `showNoticeDialog(params: DialogParams<() => void>)` - 显示通知对话框
- `showConfirmDialog(params: DialogParams<(confirmed: boolean) => void>)` - 显示确认对话框
- `showLoadChartDialog()` - 显示加载图表对话框
- `showSaveAsChartDialog()` - 显示另存为图表对话框
- `symbolInterval()` - 获取符号和间隔
- `mainSeriesPriceFormatter()` - 获取主序列价格格式化器
- `getIntervals()` - 获取支持的间隔
- `getStudiesList()` - 获取研究列表
- `getStudyInputs(studyName: string)` - 获取研究输入
- `getStudyStyles(studyName: string)` - 获取研究样式
- `addCustomCSSFile(url: string)` - 添加自定义CSS文件
- `applyOverrides<TOverrides extends Partial<ChartPropertiesOverrides>>(overrides: TOverrides)` - 应用覆盖
- `applyStudiesOverrides(overrides: object)` - 应用研究覆盖
- `applyTradingCustomization(tradingCustomization: TradingCustomization)` - 应用交易自定义
- `watchList()` - 获取观察列表API
- `news()` - 获取新闻API
- `widgetbar()` - 获取构件栏API
- `activeChart()` - 获取活动图表API
- `activeChartIndex()` - 获取活动图表索引
- `setActiveChart(index: number)` - 设置活动图表
- `chartsCount()` - 获取图表数量
- `unloadUnusedCharts()` - 卸载未使用的图表
- `layout()` - 获取布局类型
- `setLayout(layout: LayoutType)` - 设置布局类型
- `layoutName()` - 获取布局名称
- `resetLayoutSizes(disableUndo?: boolean)` - 重置布局大小
- `setLayoutSizes(sizes: Partial<LayoutSizes>, disableUndo?: boolean)` - 设置布局大小
- `changeTheme(themeName: ThemeName, options?: ChangeThemeOptions)` - 更改主题
- `getTheme()` - 获取主题
- `takeScreenshot()` - 截屏
- `takeClientScreenshot(options?: Partial<ClientSnapshotOptions>)` - 客户端截屏
- `lockAllDrawingTools()` - 锁定所有绘图工具
- `hideAllDrawingTools()` - 隐藏所有绘图工具
- `magnetEnabled()` - 磁力启用
- `magnetMode()` - 磁力模式
- `symbolSync()` - 符号同步
- `intervalSync()` - 间隔同步
- `crosshairSync()` - 十字线同步
- `timeSync()` - 时间同步
- `dateRangeSync()` - 日期范围同步
- `startFullscreen()` - 开始全屏
- `exitFullscreen()` - 退出全屏
- `undoRedoState()` - 撤销/重做状态
- `navigationButtonsVisibility()` - 导航按钮可见性
- `paneButtonsVisibility()` - 面板按钮可见性
- `dateFormat()` - 日期格式
- `timeHoursFormat()` - 小时格式
- `currencyAndUnitVisibility()` - 货币和单位可见性
- `setDebugMode(enabled: boolean)` - 设置调试模式
- `drawOnAllChartsEnabled()` - 在所有图表上绘图启用
- `clearUndoHistory()` - 清除撤销历史
- `supportedChartTypes()` - 支持的图表类型
- `watermark()` - 获取水印API
- `customSymbolStatus()` - 获取自定义符号状态API
- `setCSSCustomProperty(customPropertyName: string, value: string)` - 设置CSS自定义属性
- `getCSSCustomPropertyValue(customPropertyName: string)` - 获取CSS自定义属性值
- `customThemes()` - 获取自定义主题API
- `resetCache()` - 重置缓存

### `IContext`
PineJS执行上下文
- `symbol` - 符号工具
- `new_sym(tickerid: string, period: string, currencyCode?: string, unitId?: string, subsessionId?: string)` - 新建符号
- `select_sym(i: number)` - 选择符号
- `new_var(value?: number)` - 新建变量
- `new_unlimited_var(value?: number)` - 新建无限变量
- `new_ctx()` - 新建上下文
- `is_main_symbol(symbol: ISymbolInstrument | undefined)` - 是否主符号
- `setMinimumAdditionalDepth(value: number)` - 设置最小附加深度

### `IContextMenuRenderer`
上下文菜单渲染器
- `show(pos: ContextMenuPosition)` - 显示
- `hide()` - 隐藏
- `isShown()` - 是否显示

### `ICustomSymbolStatusAdapter`
自定义符号状态适配器
- `getVisible()` - 获取可见性
- `setVisible(visible: boolean)` - 设置可见性
- `getIcon()` - 获取图标
- `setIcon(icon: string | null)` - 设置图标
- `getColor()` - 获取颜色
- `setColor(color: string)` - 设置颜色
- `getTooltip()` - 获取工具提示
- `setTooltip(tooltip: string | null)` - 设置工具提示
- `getDropDownContent()` - 获取下拉内容
- `setDropDownContent(content: CustomStatusDropDownContent[] | null)` - 设置下拉内容

### `ICustomSymbolStatusApi`
自定义符号状态API
- `symbol(symbolId: string)` - 获取符号适配器
- `hideAll()` - 隐藏所有

### `ICustomThemesApi`
自定义主题API
- `applyCustomThemes(customThemes: CustomThemes)` - 应用自定义主题
- `resetCustomThemes()` - 重置自定义主题

### `IDatafeedChartApi`
数据源图表API
- `getMarks?(symbolInfo: LibrarySymbolInfo, from: number, to: number, onDataCallback: GetMarksCallback<Mark>, resolution: ResolutionString)` - 获取标记
- `getTimescaleMarks?(symbolInfo: LibrarySymbolInfo, from: number, to: number, onDataCallback: GetMarksCallback<TimescaleMark>, resolution: ResolutionString)` - 获取时间刻度标记
- `getServerTime?(callback: ServerTimeCallback)` - 获取服务器时间
- `searchSymbols(userInput: string, exchange: string, symbolType: string, onResult: SearchSymbolsCallback, searchSource?: SearchInitiationPoint)` - 搜索符号
- `resolveSymbol(symbolName: string, onResolve: ResolveCallback, onError: DatafeedErrorCallback, extension?: SymbolResolveExtension)` - 解析符号
- `getBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, periodParams: PeriodParams, onResult: HistoryCallback, onError: DatafeedErrorCallback)` - 获取K线
- `subscribeBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, onTick: SubscribeBarsCallback, listenerGuid: string, onResetCacheNeededCallback: () => void)` - 订阅K线
- `unsubscribeBars(listenerGuid: string)` - 取消订阅K线
- `subscribeDepth?(symbol: string, callback: DOMCallback)` - 订阅深度市场
- `unsubscribeDepth?(subscriberUID: string)` - 取消订阅深度市场
- `getVolumeProfileResolutionForPeriod?(currentResolution: ResolutionString, from: number, to: number, symbolInfo: LibrarySymbolInfo)` - 获取成交量分布分辨率

### `IDatafeedQuotesApi`
数据源报价API
- `getQuotes(symbols: string[], onDataCallback: QuotesCallback, onErrorCallback: QuotesErrorCallback)` - 获取报价
- `subscribeQuotes(symbols: string[], fastSymbols: string[], onRealtimeCallback: QuotesCallback, listenerGUID: string)` - 订阅报价
- `unsubscribeQuotes(listenerGUID: string)` - 取消订阅报价

### `IDelegate<TFunc extends Function>`
委托接口
- `fire` - 触发函数

### `IDestroyable`
可销毁接口
- `destroy()` - 销毁

### `IDropdownApi`
下拉菜单API
- `applyOptions(options: DropdownUpdateParams)` - 应用选项
- `remove()` - 移除

### `IExecutionLineAdapter`
执行线适配器
- `remove()` - 移除
- `getPrice()` - 获取价格
- `setPrice(value: number)` - 设置价格
- `getTime()` - 获取时间
- `setTime(value: number)` - 设置时间
- `getDirection()` - 获取方向
- `setDirection(value: Direction)` - 设置方向
- `getText()` - 获取文本
- `setText(value: string)` - 设置文本
- `getTooltip()` - 获取工具提示
- `setTooltip(value: string)` - 设置工具提示
- `getArrowHeight()` - 获取箭头高度
- `setArrowHeight(value: number)` - 设置箭头高度
- `getArrowSpacing()` - 获取箭头间距
- `setArrowSpacing(value: number)` - 设置箭头间距
- `getFont()` - 获取字体
- `setFont(value: string)` - 设置字体
- `getTextColor()` - 获取文本颜色
- `setTextColor(value: string)` - 设置文本颜色
- `getArrowColor()` - 获取箭头颜色
- `setArrowColor(value: string)` - 设置箭头颜色

### `IExternalDatafeed`
外部数据源
- `onReady(callback: OnReadyCallback)` - 就绪回调

### `IExternalSaveLoadAdapter`
外部保存加载适配器
- `getAllCharts()` - 获取所有图表
- `removeChart(id: string | number)` - 移除图表
- `saveChart(chartData: ChartData)` - 保存图表
- `getChartContent(chartId: number | string)` - 获取图表内容
- `getAllStudyTemplates()` - 获取所有研究模板
- `removeStudyTemplate(studyTemplateInfo: StudyTemplateMetaInfo)` - 移除研究模板
- `saveStudyTemplate(studyTemplateData: StudyTemplateData)` - 保存研究模板
- `getStudyTemplateContent(studyTemplateInfo: StudyTemplateMetaInfo)` - 获取研究模板内容
- `getDrawingTemplates(toolName: string)` - 获取绘图模板名称
- `loadDrawingTemplate(toolName: string, templateName: string)` - 加载绘图模板
- `removeDrawingTemplate(toolName: string, templateName: string)` - 移除绘图模板
- `saveDrawingTemplate(toolName: string, templateName: string, content: string)` - 保存绘图模板
- `getChartTemplateContent(templateName: string)` - 获取图表模板内容
- `getAllChartTemplates()` - 获取所有图表模板名称
- `saveChartTemplate(newName: string, theme: ChartTemplateContent)` - 保存图表模板
- `removeChartTemplate(templateName: string)` - 移除图表模板
- `saveLineToolsAndGroups(layoutId: string | undefined, chartId: string | number, state: LineToolsAndGroupsState)` - 保存线工具和组
- `loadLineToolsAndGroups(layoutId: string | undefined, chartId: string | number, requestType: LineToolsAndGroupsLoadRequestType, requestContext: LineToolsAndGroupsLoadRequestContext)` - 加载线工具和组

### `IFormatter<T>`
格式化器接口
- `format(value?: T, options?: FormatterFormatOptions)` - 格式化
- `parse?(value: string, options?: FormatterParseOptions)` - 解析

### `IImageStorageAdapter`
图像存储适配器
- `getMaxImageSizeInBytes()` - 获取最大图像大小

### `ILineDataSourceApi`
线数据源API
- `isSelectionEnabled()` - 选择是否启用
- `setSelectionEnabled(enable: boolean)` - 设置选择启用
- `isSavingEnabled()` - 保存是否启用
- `setSavingEnabled(enable: boolean)` - 设置保存启用
- `isShowInObjectsTreeEnabled()` - 是否显示在对象树
- `setShowInObjectsTreeEnabled(enabled: boolean)` - 设置显示在对象树
- `isUserEditEnabled()` - 用户编辑是否启用
- `setUserEditEnabled(enabled: boolean)` - 设置用户编辑启用
- `bringToFront()` - 置顶
- `sendToBack()` - 置底
- `getProperties<P extends Record<string, any> = Record<string, any>>(target?: PropertyKeyType, nopack?: boolean)` - 获取属性
- `setProperties<P extends Record<string, any> = Record<string, any>>(newProperties: P, saveDefaults?: boolean)` - 设置属性
- `getPoints()` - 获取点
- `setPoints(points: ShapePoint[])` - 设置点
- `getAnchoredPosition()` - 获取锚定位置
- `setAnchoredPosition(positionPercents: PositionPercents)` - 设置锚定位置

### `IMenuItem`
菜单项接口
- `type` - 类型
- `id` - ID

### `INewsApi`
新闻API
- `refresh()` - 刷新

### `INumberFormatter`
数字格式化器
- `format(value?: number, options?: NumberFormatterFormatOptions)` - 格式化
- `formatChange?(currentPrice: number, prevPrice: number, options?: NumberFormatterFormatOptions)` - 格式化变化

### `IObservable<T>`
可观察接口
- `subscribe(callback: ObservableCallback<T>)` - 订阅
- `unsubscribe(callback: ObservableCallback<T>)` - 取消订阅

### `IObservableValue<T>`
可观察值接口
- 继承 `IBoxedValue<T>` 和 `IObservable<T>`

### `IObservableValueReadOnly<T>`
只读可观察值接口
- 继承 `IBoxedValueReadOnly<T>` 和 `IObservable<T>`

### `IOrderLineAdapter`
订单线适配器
- `remove()` - 移除
- `onModify(callback: () => void)` - 修改回调
- `onModify<T>(data: T, callback: (data: T) => void)` - 修改回调（带数据）
- `onMove(callback: () => void)` - 移动回调
- `onMove<T>(data: T, callback: (data: T) => void)` - 移动回调（带数据）
- `onMoving(callback: () => void)` - 移动中回调
- `onMoving<T>(data: T, callback: (data: T) => void)` - 移动中回调（带数据）
- `onCancel(callback: () => void)` - 取消回调
- `onCancel<T>(data: T, callback: (data: T) => void)` - 取消回调（带数据）
- `getPrice()` - 获取价格
- `setPrice(value: number)` - 设置价格
- `getText()` - 获取文本
- `setText(value: string)` - 设置文本
- `getTooltip()` - 获取工具提示
- `setTooltip(value: string)` - 设置工具提示
- `getModifyTooltip()` - 获取修改工具提示
- `setModifyTooltip(value: string)` - 设置修改工具提示
- `getCancelTooltip()` - 获取取消工具提示
- `setCancelTooltip(value: string)` - 设置取消工具提示
- `getQuantity()` - 获取数量
- `setQuantity(value: string)` - 设置数量
- `getEditable()` - 获取可编辑
- `setEditable(value: boolean)` - 设置可编辑
- `getCancellable()` - 获取可取消
- `setCancellable(value: boolean)` - 设置可取消
- `getExtendLeft()` - 获取向左延伸
- `setExtendLeft(value: boolean)` - 设置向左延伸
- `getLineLength()` - 获取线长度
- `getLineLengthUnit()` - 获取线长度单位
- `setLineLength(value: number, unit?: OrderLineLengthUnit)` - 设置线长度
- `getLineStyle()` - 获取线样式
- `setLineStyle(value: number)` - 设置线样式
- `getLineWidth()` - 获取线宽
- `setLineWidth(value: number)` - 设置线宽
- `getBodyFont()` - 获取主体字体
- `setBodyFont(value: string)` - 设置主体字体
- `getQuantityFont()` - 获取数量字体
- `setQuantityFont(value: string)` - 设置数量字体
- `getLineColor()` - 获取线颜色
- `setLineColor(value: string)` - 设置线颜色
- `getBodyBorderColor()` - 获取主体边框颜色
- `setBodyBorderColor(value: string)` - 设置主体边框颜色
- `getBodyBackgroundColor()` - 获取主体背景色
- `setBodyBackgroundColor(value: string)` - 设置主体背景色
- `getBodyTextColor()` - 获取主体文本颜色
- `setBodyTextColor(value: string)` - 设置主体文本颜色
- `getQuantityBorderColor()` - 获取数量边框颜色
- `setQuantityBorderColor(value: string)` - 设置数量边框颜色
- `getQuantityBackgroundColor()` - 获取数量背景色
- `setQuantityBackgroundColor(value: string)` - 设置数量背景色
- `getQuantityTextColor()` - 获取数量文本颜色
- `setQuantityTextColor(value: string)` - 设置数量文本颜色
- `getCancelButtonBorderColor()` - 获取取消按钮边框颜色
- `setCancelButtonBorderColor(value: string)` - 设置取消按钮边框颜色
- `getCancelButtonBackgroundColor()` - 获取取消按钮背景色
- `setCancelButtonBackgroundColor(value: string)` - 设置取消按钮背景色
- `getCancelButtonIconColor()` - 获取取消按钮图标颜色
- `setCancelButtonIconColor(value: string)` - 设置取消按钮图标颜色

### `IPaneApi`
面板API
- `hasMainSeries()` - 是否有主序列
- `getLeftPriceScales()` - 获取左侧价格刻度
- `getRightPriceScales()` - 获取右侧价格刻度
- `getMainSourcePriceScale()` - 获取主源价格刻度
- `getPriceScaleById(priceScaleId: string)` - 根据ID获取价格刻度
- `getHeight()` - 获取高度
- `setHeight(height: number)` - 设置高度
- `moveTo(paneIndex: number)` - 移动到指定索引
- `paneIndex()` - 获取面板索引
- `collapse()` - 折叠
- `restore()` - 恢复
- `isCollapsed()` - 是否折叠
- `setMaximized(value: boolean)` - 设置最大化
- `isMaximized()` - 是否最大化

### `IPineSeries`
Pine序列接口
- `get(n?: number)` - 获取值
- `set(value: number)` - 设置值
- `indexOf(time: number)` - 获取指定时间戳的索引
- `adopt(source: IPineSeries, destination: IPineSeries, mode: 0 | 1)` - 适应时间尺度

### `IPositionLineAdapter`
持仓线适配器
- `remove()` - 移除
- `onClose(callback: () => void)` - 平仓回调
- `onClose<T>(data: T, callback: (data: T) => void)` - 平仓回调（带数据）
- `onModify(callback: () => void)` - 修改回调
- `onModify<T>(data: T, callback: (data: T) => void)` - 修改回调（带数据）
- `onReverse(callback: () => void)` - 反向回调
- `onReverse<T>(data: T, callback: (data: T) => void)` - 反向回调（带数据）
- `getPrice()` - 获取价格
- `setPrice(value: number)` - 设置价格
- `getText()` - 获取文本
- `setText(value: string)` - 设置文本
- `getTooltip()` - 获取工具提示
- `setTooltip(value: string)` - 设置工具提示
- `getProtectTooltip()` - 获取保护工具提示
- `setProtectTooltip(value: string)` - 设置保护工具提示
- `getCloseTooltip()` - 获取平仓工具提示
- `setCloseTooltip(value: string)` - 设置平仓工具提示
- `getReverseTooltip()` - 获取反向工具提示
- `setReverseTooltip(value: string)` - 设置反向工具提示
- `getQuantity()` - 获取数量
- `setQuantity(value: string)` - 设置数量
- `getExtendLeft()` - 获取向左延伸
- `setExtendLeft(value: boolean)` - 设置向左延伸
- `getLineLengthUnit()` - 获取线长度单位
- `getLineLength()` - 获取线长度
- `setLineLength(value: number, unit?: PositionLineLengthUnit)` - 设置线长度
- `getLineStyle()` - 获取线样式
- `setLineStyle(value: number)` - 设置线样式
- `getLineWidth()` - 获取线宽
- `setLineWidth(value: number)` - 设置线宽
- `getBodyFont()` - 获取主体字体
- `setBodyFont(value: string)` - 设置主体字体
- `getQuantityFont()` - 获取数量字体
- `setQuantityFont(value: string)` - 设置数量字体
- `getLineColor()` - 获取线颜色
- `setLineColor(value: string)` - 设置线颜色
- `getBodyBorderColor()` - 获取主体边框颜色
- `setBodyBorderColor(value: string)` - 设置主体边框颜色
- `getBodyBackgroundColor()` - 获取主体背景色
- `setBodyBackgroundColor(value: string)` - 设置主体背景色
- `getBodyTextColor()` - 获取主体文本颜色
- `setBodyTextColor(value: string)` - 设置主体文本颜色
- `getQuantityBorderColor()` - 获取数量边框颜色
- `setQuantityBorderColor(value: string)` - 设置数量边框颜色
- `getQuantityBackgroundColor()` - 获取数量背景色
- `setQuantityBackgroundColor(value: string)` - 设置数量背景色
- `getQuantityTextColor()` - 获取数量文本颜色
- `setQuantityTextColor(value: string)` - 设置数量文本颜色
- `getReverseButtonBorderColor()` - 获取反向按钮边框颜色
- `setReverseButtonBorderColor(value: string)` - 设置反向按钮边框颜色
- `getReverseButtonBackgroundColor()` - 获取反向按钮背景色
- `setReverseButtonBackgroundColor(value: string)` - 设置反向按钮背景色
- `getReverseButtonIconColor()` - 获取反向按钮图标颜色
- `setReverseButtonIconColor(value: string)` - 设置反向按钮图标颜色
- `getCloseButtonBorderColor()` - 获取平仓按钮边框颜色
- `setCloseButtonBorderColor(value: string)` - 设置平仓按钮边框颜色
- `getCloseButtonBackgroundColor()` - 获取平仓按钮背景色
- `setCloseButtonBackgroundColor(value: string)` - 设置平仓按钮背景色
- `getCloseButtonIconColor()` - 获取平仓按钮图标颜色
- `setCloseButtonIconColor(value: string)` - 设置平仓按钮图标颜色

### `IPriceFormatter`
价格格式化器
- `format(price: number, options?: PriceFormatterFormatOptions)` - 格式化价格
- `formatChange?(price: number, prevPrice: number, options?: PriceFormatterFormatOptions)` - 格式化价格变化

### `IPriceScaleApi`
价格刻度API
- `getMode()` - 获取模式
- `setMode(newMode: PriceScaleMode)` - 设置模式
- `isInverted()` - 是否反转
- `setInverted(isInverted: boolean)` - 设置反转
- `isLocked()` - 是否锁定
- `setLocked(isLocked: boolean)` - 设置锁定
- `isAutoScale()` - 是否自动缩放
- `setAutoScale(isAutoScale: boolean)` - 设置自动缩放
- `getVisiblePriceRange()` - 获取可见价格范围
- `setVisiblePriceRange(range: VisiblePriceRange)` - 设置可见价格范围
- `hasMainSeries()` - 是否有主序列
- `getStudies()` - 获取研究
- `currency()` - 获取货币
- `setCurrency(currency: string | null)` - 设置货币
- `unit()` - 获取单位
- `setUnit(unit: string | null)` - 设置单位

### `ISelectionApi`
选择API
- `add(entities: EntityId[] | EntityId)` - 添加实体
- `set(entities: EntityId[] | EntityId)` - 设置实体
- `remove(entities: EntityId[])` - 移除实体
- `contains(entity: EntityId)` - 是否包含实体
- `allSources()` - 获取所有源
- `isEmpty()` - 是否为空
- `clear()` - 清除
- `onChanged()` - 变更订阅
- `canBeAddedToSelection(entity: EntityId)` - 是否可以添加到选择

### `ISeparator`
分隔符接口
- 继承 `IMenuItem`

### `ISeriesApi`
序列API
- `isUserEditEnabled()` - 用户编辑是否启用
- `setUserEditEnabled(enabled: boolean)` - 设置用户编辑启用
- `mergeUp()` - 向上合并
- `mergeDown()` - 向下合并
- `unmergeUp()` - 向上取消合并
- `unmergeDown()` - 向下取消合并
- `detachToRight()` - 分离到右侧
- `detachToLeft()` - 分离到左侧
- `detachNoScale()` - 分离到无刻度
- `changePriceScale(newPriceScale: SeriesPriceScale)` - 更改价格刻度
- `isVisible()` - 是否可见
- `setVisible(visible: boolean)` - 设置可见性
- `bringToFront()` - 置顶
- `sendToBack()` - 置底
- `entityId()` - 获取实体ID
- `chartStyleProperties<T extends ChartStyle>(chartStyle: T)` - 获取图表样式属性
- `setChartStyleProperties<T extends ChartStyle>(chartStyle: T, newPrefs: DeepPartial<SeriesPreferencesMap[T])>` - 设置图表样式属性

### `ISettingsAdapter`
设置适配器
- `initialSettings` - 初始设置
- `setValue(key: string, value: string)` - 设置值
- `removeValue(key: string)` - 移除值

### `IShapesGroupControllerApi`
形状组控制器API
- `createGroupFromSelection()` - 从选择创建组
- `removeGroup(groupId: ShapesGroupId)` - 移除组
- `groups()` - 获取所有组
- `shapesInGroup(groupId: ShapesGroupId)` - 获取组内形状
- `excludeShapeFromGroup(groupId: ShapesGroupId, shapeId: EntityId)` - 从组中排除形状
- `addShapeToGroup(groupId: ShapesGroupId, shapeId: EntityId)` - 添加形状到组
- `availableZOrderOperations(groupId: ShapesGroupId)` - 获取可用Z轴顺序操作
- `bringToFront(groupId: ShapesGroupId)` - 置顶组
- `sendToBack(groupId: ShapesGroupId)` - 置底组
- `bringForward(groupId: ShapesGroupId)` - 前移组
- `sendBackward(groupId: ShapesGroupId)` - 后移组
- `insertAfter(groupId: ShapesGroupId, target: ShapesGroupId | EntityId)` - 插入到目标之后
- `insertBefore(groupId: ShapesGroupId, target: ShapesGroupId | EntityId)` - 插入到目标之前
- `setGroupVisibility(groupId: ShapesGroupId, value: boolean)` - 设置组可见性
- `groupVisibility(groupId: ShapesGroupId)` - 获取组可见性
- `setGroupLock(groupId: ShapesGroupId, value: boolean)` - 设置组锁定
- `groupLock(groupId: ShapesGroupId)` - 获取组锁定状态
- `getGroupName(groupId: ShapesGroupId)` - 获取组名称
- `setGroupName(groupId: ShapesGroupId, name: string)` - 设置组名称
- `canBeGroupped(shapes: readonly EntityId[])` - 是否可以分组

### `IStudyApi`
研究API
- `isUserEditEnabled()` - 用户编辑是否启用
- `setUserEditEnabled(enabled: boolean)` - 设置用户编辑启用
- `getInputsInfo()` - 获取输入信息
- `getInputValues()` - 获取输入值
- `setInputValues(values: StudyInputValueItem[])` - 设置输入值
- `getStyleInfo()` - 获取样式信息
- `getStyleValues()` - 获取样式值
- `mergeUp()` - 向上合并
- `mergeDown()` - 向下合并
- `unmergeUp()` - 向上取消合并
- `unmergeDown()` - 向下取消合并
- `paneIndex()` - 获取面板索引
- `changePriceScale(newPriceScale: StudyPriceScale | EntityId)` - 更改价格刻度
- `isVisible()` - 是否可见
- `setVisible(visible: boolean)` - 设置可见性
- `bringToFront()` - 置顶
- `sendToBack()` - 置底
- `applyOverrides<TOverrides extends Partial<SingleIndicatorOverrides>>(overrides: TOverrides)` - 应用覆盖
- `applyToEntireLayout()` - 应用到整个布局
- `onDataLoaded()` - 数据加载完成订阅
- `onStudyError()` - 研究错误订阅

### `ISubscription<TFunc extends Function>`
订阅接口
- `subscribe(obj: object | null, member: TFunc, singleshot?: boolean)` - 订阅
- `unsubscribe(obj: object | null, member: TFunc)` - 取消订阅
- `unsubscribeAll(obj: object | null)` - 取消所有订阅

### `ISymbolInstrument`
符号工具接口
- `periodBase` - 周期基础
- `tickerid` - 代码ID
- `currencyCode` - 货币代码
- `unitId` - 单位ID
- `period` - 周期
- `index` - 索引
- `time` - 时间
- `open` - 开盘
- `high` - 最高
- `low` - 最低
- `close` - 收盘
- `volume` - 成交量
- `updatetime` - 更新时间
- `ticker` - 代码
- `resolution` - 分辨率
- `interval` - 间隔
- `minTick` - 最小跳动
- `isFirstBar` - 是否第一根K线
- `isLastBar` - 是否最后一根K线
- `isNewBar` - 是否新K线
- `isBarClosed` - K线是否关闭
- `info` - 符号信息
- `bartime()` - 获取K线时间
- `isdwm()` - 是否日/周/月

### `ISymbolValueFormatter`
符号值格式化器
- `format(price: number, options?: SymbolValueFormatterFormatOptions)` - 格式化
- `formatChange?(currentPrice: number, prevPrice: number, options?: SymbolValueFormatterFormatOptions)` - 格式化变化

### `ITimeScaleApi`
时间刻度API
- `coordinateToTime(x: number)` - 坐标转时间
- `barSpacingChanged()` - 柱间距变更订阅
- `rightOffsetChanged()` - 右偏移变更订阅
- `setRightOffset(offset: number)` - 设置右偏移
- `setBarSpacing(newBarSpacing: number)` - 设置柱间距
- `barSpacing()` - 获取柱间距
- `rightOffset()` - 获取右偏移
- `width()` - 获取宽度
- `defaultRightOffset()` - 获取默认右偏移
- `defaultRightOffsetPercentage()` - 获取默认右偏移百分比
- `usePercentageRightOffset()` - 是否使用百分比右偏移

### `ITimezoneApi`
时区API
- `availableTimezones()` - 可用时区
- `getTimezone()` - 获取当前时区
- `setTimezone(timezone: TimezoneId | CustomTimezoneId, options?: UndoOptions)` - 设置时区
- `onTimezoneChanged()` - 时区变更订阅

### `IWatchListApi`
观察列表API
- `defaultList()` - 获取默认列表
- `getList(id?: string)` - 获取列表
- `getAllLists()` - 获取所有列表
- `setActiveList(id: string)` - 设置活动列表
- `getActiveListId()` - 获取活动列表ID
- `setList(symbols: string[])` - 设置列表
- `updateList(listId: string, symbols: string[])` - 更新列表
- `renameList(listId: string, newName: string)` - 重命名列表
- `createList(listName?: string, symbols?: string[])` - 创建列表
- `saveList(list: WatchListSymbolList)` - 保存列表
- `deleteList(listId: string)` - 删除列表
- `onListChanged()` - 列表变更订阅
- `onActiveListChanged()` - 活动列表变更订阅
- `onListAdded()` - 列表添加订阅
- `onListRemoved()` - 列表移除订阅
- `onListRenamed()` - 列表重命名订阅

### `IWatchedValue<T>`
可观察值接口
- `setValue(value: T, forceUpdate?: boolean)` - 设置值
- `subscribe(callback: WatchedValueCallback<T>, options?: WatchedValueSubscribeOptions)` - 订阅
- `unsubscribe(callback?: WatchedValueCallback<T> | null)` - 取消订阅

### `IWatchedValueReadonly<T>`
只读可观察值接口
- `subscribe(callback: (value: T) => void, options?: WatchedValueSubscribeOptions)` - 订阅
- `unsubscribe(callback?: ((value: T) => void) | null)` - 取消订阅
- `when(callback: WatchedValueCallback<T>)` - 当值变化时

### `IWatermarkApi`
水印API
- `color()` - 颜色
- `visibility()` - 可见性
- `tickerVisibility()` - 代码可见性
- `intervalVisibility()` - 间隔可见性
- `descriptionVisibility()` - 描述可见性
- `customVisibility()` - 自定义可见性
- `setContentProvider(provider: WatermarkContentProvider | null)` - 设置内容提供者
- `provider()` - 获取提供者

### `IWidgetbarApi`
构件栏API
- `showPage(pageName: PageName)` - 显示页面
- `hidePage(pageName: PageName)` - 隐藏页面
- `isPageVisible(pageName: PageName)` - 页面是否可见
- `openOrderPanel()` - 打开订单面板
- `closeOrderPanel()` - 关闭订单面板
- `changeWidgetBarVisibility(visible: boolean)` - 更改构件栏可见性

### `IchimokuCloudIndicatorOverrides`
一目均衡表指标覆盖
- `"plots background.color"` - 背景色，默认值：`#000080`
- `"conversion line.color"` - 转换线颜色，默认值：`#2196F3`
- `"base line.color"` - 基准线颜色，默认值：`#801922`
- `"lagging span.color"` - 迟行线颜色，默认值：`#43A047`
- `"leading span a.color"` - 先行线A颜色，默认值：`#A5D6A7`
- `"leading span b.color"` - 先行线B颜色，默认值：`#FAA1A4`

### `IndicatorOptions`
指标选项
- `title` - 标题
- `shortTitle` - 短标题
- `overlay` - 是否覆盖
- `format` - 格式
- `precision` - 精度

### `IndividualPosition`
单个持仓
- 继承 `IndividualPositionBase` 和 `CustomFields`

### `IndividualPositionBase`
单个持仓基础
- `id` - ID
- `date` - 日期
- `symbol` - 符号
- `qty` - 数量
- `side` - 方向
- `price` - 价格
- `canBeClosed` - 是否可以平仓

### `InitialSettingsMap`
初始设置映射
- `[key: string]` - 键值对

### `InputFunctions`
输入函数
- `bool(defaultValue: boolean, title: string, options?: Partial<BoolInputOptions>)` - 布尔输入
- `int(defaultValue: number, title: string, options?: Partial<IntInputOptions>)` - 整数输入
- `source(defaultValue: StudyPriceSource, title: string, options?: Partial<SourceInputOptions>)` - 源输入
- `string<TOptions extends readonly string[]>(defaultValue: string, title: string, options?: Partial<StringInputOptions<TOptions>>)` - 字符串输入
- `symbol(defaultValue: string, title: string, options?: Partial<SymbolInputOptions>)` - 符号输入

### `InstrumentInfo`
工具信息
- `qty` - 数量元信息
- `pipValue` - 点值
- `pipSize` - 点大小
- `minTick` - 最小跳动
- `lotSize` - 手数大小
- `type` - 类型
- `units` - 单位
- `brokerSymbol` - 经纪商符号
- `description` - 描述
- `leverage` - 杠杆
- `marginRate` - 保证金率
- `limitPriceStep` - 限价步长
- `stopPriceStep` - 止损步长
- `allowedDurations` - 允许的有效期
- `variableMinTick` - 可变最小跳动
- `currency` - 货币
- `baseCurrency` - 基础货币
- `quoteCurrency` - 报价货币
- `bigPointValue` - 大点值
- `priceMagnifier` - 价格放大系数
- `allowedOrderTypes` - 允许的订单类型

### `IntInputOptions`
整数输入选项
- `minVal` - 最小值
- `maxVal` - 最大值
- `step` - 步长

### `IsTradableResult`
是否可交易结果
- `tradable` - 是否可交易
- `reason` - 原因
- `reasonHeading` - 原因标题
- `solutions` - 解决方案
- `shortReason` - 短原因

### `KagiStylePreferences`
卡吉图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `upColorProjection` - 上涨投影颜色
- `downColorProjection` - 下跌投影颜色

### `KeltnerChannelsIndicatorOverrides`
肯特纳通道指标覆盖
- `"upper.color"` - 上线颜色，默认值：`#2196F3`
- `"middle.color"` - 中线颜色，默认值：`#2196F3`
- `"lower.color"` - 下线颜色，默认值：`#2196F3`

### `KlingerOscillatorIndicatorOverrides`
Klinger震荡器指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`
- `"signal.color"` - 信号线颜色，默认值：`#43A047`

### `KnowSureThingIndicatorOverrides`
确知指标覆盖
- `"kst.color"` - KST颜色，默认值：`#089981`
- `"signal.color"` - 信号线颜色，默认值：`#F23645`

### `LeverageInfo`
杠杆信息
- `title` - 标题
- `leverage` - 杠杆
- `min` - 最小值
- `max` - 最大值
- `step` - 步长

### `LeverageInfoParams`
杠杆信息参数
- `symbol` - 符号
- `orderType` - 订单类型
- `side` - 方向
- `customFields` - 自定义字段

### `LeveragePreviewResult`
杠杆预览结果
- `infos` - 信息
- `warnings` - 警告
- `errors` - 错误

### `LeverageSetParams`
杠杆设置参数
- 继承 `LeverageInfoParams`
- `leverage` - 杠杆

### `LeverageSetResult`
杠杆设置结果
- `leverage` - 杠杆

### `LibraryPineStudy<TPineStudyResult>`
Pine研究库
- `init?(ctx: IContext, inputs: <T extends StudyInputValue>(index: number) => T)` - 初始化
- `main(ctx: IContext, inputs: <T extends StudyInputValue>(index: number) => T)` - 主函数

### `LibraryPineStudyConstructor<TPineStudyResult>`
Pine研究库构造函数
- `new (): LibraryPineStudy<TPineStudyResult>`

### `LibrarySubsessionInfo`
库子会话信息
- `description` - 描述
- `id` - ID
- `session` - 会话
- `"session-correction"` - 会话修正
- `"session-display"` - 显示会话

### `LibrarySymbolInfo`
库符号信息
- `name` - 名称
- `base_name` - 基础名称数组
- `ticker` - 代码
- `description` - 描述
- `long_description` - 长描述
- `type` - 类型
- `session` - 会话
- `session_display` - 显示会话
- `session_holidays` - 会话假期
- `corrections` - 修正
- `exchange` - 交易所
- `listed_exchange` - 上市交易所
- `timezone` - 时区
- `format` - 格式
- `pricescale` - 价格刻度
- `minmov` - 最小移动
- `fractional` - 是否分数
- `minmove2` - 第二最小移动
- `variable_tick_size` - 可变跳动大小
- `has_intraday` - 是否有日内数据
- `supported_resolutions` - 支持的分辨率
- `intraday_multipliers` - 日内乘数
- `has_seconds` - 是否有秒数据
- `has_ticks` - 是否有跳动数据
- `seconds_multipliers` - 秒乘数
- `build_seconds_from_ticks` - 是否从跳动构建秒数据
- `has_daily` - 是否有日数据
- `daily_multipliers` - 日乘数
- `has_weekly_and_monthly` - 是否有周/月数据
- `weekly_multipliers` - 周乘数
- `monthly_multipliers` - 月乘数
- `has_empty_bars` - 是否有空K线
- `visible_plots_set` - 可见绘图集
- `volume_precision` - 成交量精度
- `data_status` - 数据状态
- `delay` - 延迟
- `expired` - 是否过期
- `expiration_date` - 过期日期
- `sector` - 板块
- `industry` - 行业
- `currency_code` - 货币代码
- `original_currency_code` - 原始货币代码
- `unit_id` - 单位ID
- `original_unit_id` - 原始单位ID
- `unit_conversion_types` - 单位转换类型
- `subsession_id` - 子会话ID
- `subsessions` - 子会话数组
- `price_source_id` - 价格源ID
- `price_sources` - 价格源数组
- `logo_urls` - 图标URL数组
- `exchange_logo` - 交易所图标
- `library_custom_fields` - 库自定义字段

### `LineBreakStylePreferences`
新线图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `borderUpColor` - 上涨边框颜色
- `borderDownColor` - 下跌边框颜色
- `upColorProjection` - 上涨投影颜色
- `downColorProjection` - 下跌投影颜色
- `borderUpColorProjection` - 上涨投影边框颜色
- `borderDownColorProjection` - 下跌投影边框颜色

### `LineStylePreferences`
线图样式偏好
- `colorType` - 颜色类型
- `gradientStartColor` - 渐变起始色
- `gradientEndColor` - 渐变结束色
- `color` - 颜色
- `linestyle` - 线样式
- `linewidth` - 线宽

### `LineStyles`
线样式集合
- `hline` - 水平线样式

### `LineToolState`
线工具状态
- `id` - ID
- `symbol` - 符号
- `ownerSource` - 所有者源
- `groupId` - 组ID
- `currencyId` - 货币ID
- `unitId` - 单位ID
- `state` - 状态

### `LineToolsAndGroupsLoadRequestContext`
线工具和组加载请求上下文
- `symbol` - 符号

### `LineToolsAndGroupsState`
线工具和组状态
- `sources` - 源映射
- `groups` - 组映射
- `symbol` - 符号

### `LineToolsGroupState`
线工具组状态
- `id` - ID
- `name` - 名称
- `symbol` - 符号
- `currencyId` - 货币ID
- `unitId` - 单位ID

### `LoadingScreenOptions`
加载屏幕选项
- `foregroundColor` - 前景色
- `backgroundColor` - 背景色

### `MACDIndicatorOverrides`
MACD指标覆盖
- `"histogram.color"` - 柱状图颜色，默认值：`#FF5252`
- `"macd.color"` - MACD线颜色，默认值：`#2196F3`
- `"signal.color"` - 信号线颜色，默认值：`#FF6D00`

### `MACrossIndicatorOverrides`
移动平均交叉指标覆盖
- `"short:plot.color"` - 短期均线颜色，默认值：`#43A047`
- `"long:plot.color"` - 长期均线颜色，默认值：`#FF6D00`
- `"crosses.color"` - 交叉点颜色，默认值：`#2196F3`

### `MAwithEMACrossIndicatorOverrides`
MA与EMA交叉指标覆盖
- `"ma.color"` - MA颜色，默认值：`#FF6D00`
- `"ema.color"` - EMA颜色，默认值：`#43A047`
- `"crosses.color"` - 交叉点颜色，默认值：`#2196F3`

### `Mark`
标记
- `id` - ID
- `time` - 时间
- `color` - 颜色
- `text` - 文本
- `label` - 标签
- `labelFontColor` - 标签字体颜色
- `minSize` - 最小尺寸
- `borderWidth` - 边框宽度
- `hoveredBorderWidth` - 悬停边框宽度
- `imageUrl` - 图片URL
- `showLabelWhenImageLoaded` - 图片加载后是否显示标签

### `MarkCustomColor`
标记自定义颜色
- `border` - 边框颜色
- `background` - 背景色

### `MathFunctions`
数学函数
- `max(value: number, ...args: (IPineSeries | number)[] | number[])` - 最大值
- `max(value: IPineSeries, ...args: (IPineSeries | number)[] | number[])` - 最大值（序列）
- `min(value: number, ...args: (IPineSeries | number)[] | number[])` - 最小值
- `min(value: IPineSeries, ...args: (IPineSeries | number)[] | number[])` - 最小值（序列）
- `negative(value: IPineSeries)` - 负数（序列）
- `negative(value: number)` - 负数

### `MenuSeparator`
菜单分隔符
- 继承 `ActionDescription`
- `separator` - 分隔符标志

### `MoneyFlowIndexIndicatorOverrides`
资金流量指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#7E57C2`

### `MouseEventParams`
鼠标事件参数
- `clientX` - 客户端X坐标
- `clientY` - 客户端Y坐标
- `pageX` - 页面X坐标
- `pageY` - 页面Y坐标
- `screenX` - 屏幕X坐标
- `screenY` - 屏幕Y坐标

### `MovingAverageIndicatorOverrides`
移动平均线指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `NewsItem`
新闻项
- `title` - 标题
- `provider` - 提供者
- `published` - 发布时间
- `link` - 链接
- `shortDescription` - 短描述
- `fullDescription` - 完整描述

### `NewsProvider`
新闻提供者
- `id` - ID
- `name` - 名称
- `logo_id` - 图标ID
- `url` - URL

### `NumberFormatterFormatOptions`
数字格式化器格式选项
- `noExponentialForm` - 禁用指数形式

### `NumericFormattingParams`
数字格式化参数
- `decimal_sign` - 小数点符号
- `grouping_separator` - 千位分隔符

### `OnBalanceVolumeIndicatorOverrides`
能量潮指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `OpenUrlSolution`
打开URL解决方案
- `openUrl` - 打开URL

### `OrderDialogOptions`
订单对话框选项
- `showTotal` - 显示总额

### `OrderDuration`
订单有效期
- `type` - 类型
- `datetime` - 日期时间

### `OrderDurationMetaInfo`
订单有效期元信息
- `hasDatePicker` - 有日期选择器
- `hasTimePicker` - 有时间选择器
- `default` - 是否默认
- `name` - 名称
- `value` - 值
- `supportedOrderTypes` - 支持的订单类型

### `OrderOrPositionMessage`
订单或持仓消息
- `type` - 类型
- `text` - 文本

### `OrderPreviewResult`
订单预览结果
- `sections` - 部分
- `confirmId` - 确认ID
- `warnings` - 警告
- `errors` - 错误

### `OrderPreviewSection`
订单预览部分
- `rows` - 行
- `header` - 标题

### `OrderPreviewSectionRow`
订单预览部分行
- `title` - 标题
- `value` - 值

### `OrderRule`
订单规则
- `id` - ID
- `severity` - 严重性

### `OrderTemplate`
订单模板
- 继承 `OrderTemplateBase`

### `OrderTemplateBase`
订单模板基础
- `symbol` - 符号
- `type` - 类型
- `side` - 方向
- `qty` - 数量
- `stopType` - 止损类型
- `currentQuotes` - 当前报价
- `stopPrice` - 止损价
- `limitPrice` - 限价
- `takeProfit` - 止盈
- `stopLoss` - 止损
- `guaranteedStop` - 保证止损
- `trailingStopPips` - 移动止损点
- `duration` - 有效期
- `customFields` - 自定义字段

### `OrderTicketSettings`
订单工单设置
- `showRelativePriceControl` - 显示相对价格控制
- `showOrderPreview` - 显示订单预览

### `OverlayIndicatorOverrides`
覆盖指标覆盖
- `style` - 样式
- `showPriceLine` - 显示价格线
- `allowExtendTimeScale` - 允许扩展时间刻度
- `minTick` - 最小跳动

### `Overrides`
覆盖
- `[key: string]` - 键值对

### `ParabolicSARIndicatorOverrides`
抛物线SAR指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `PeriodParams`
周期参数
- `from` - 开始时间
- `to` - 结束时间
- `countBack` - 返回数量
- `firstDataRequest` - 是否首次请求

### `PineJS`
PineJS接口
- `Std` - 标准库

### `PineJSStd`
PineJS标准库
- `max_series_default_size` - 最大序列默认大小
- `eps()` - 机器精度
- `high(context: IContext)` - 最高价
- `low(context: IContext)` - 最低价
- `open(context: IContext)` - 开盘价
- `close(context: IContext)` - 收盘价
- `ohlc4(context: IContext)` - OHLC4平均值
- `volume(context: IContext)` - 成交量
- `time(context: IContext)` - 时间
- `time(context: IContext, period: string)` - 时间（带周期）
- `hl2(context: IContext)` - HL2平均值
- `hlc3(context: IContext)` - HLC3平均值
- `period(context: IContext)` - 周期
- `tickerid(context: IContext)` - 代码ID
- `year(context: IContext, time?: number)` - 年
- `month(context: IContext, time?: number)` - 月
- `weekofyear(context: IContext, time?: number)` - 周
- `dayofmonth(context: IContext, time?: number)` - 日
- `dayofweek(context: IContext, time?: number)` - 星期
- `hour(context: IContext, time?: number)` - 小时
- `minute(context: IContext, time?: number)` - 分钟
- `second(context: IContext, time?: number)` - 秒
- `greaterOrEqual(n1: number, n2: number, eps?: number)` - 大于等于
- `lessOrEqual(n1: number, n2: number, eps?: number)` - 小于等于
- `equal(n1: number, n2: number, eps?: number)` - 等于
- `greater(n1: number, n2: number, eps?: number)` - 大于
- `less(n1: number, n2: number, eps?: number)` - 小于
- `compare(n1: number, n2: number, eps?: number)` - 比较
- `ge(n1: number, n2: number)` - 大于等于（返回1/0）
- `le(n1: number, n2: number)` - 小于等于（返回1/0）
- `eq(n1: number, n2: number)` - 等于（返回1/0）
- `neq(n1: number, n2: number)` - 不等于（返回1/0）
- `gt(n1: number, n2: number)` - 大于（返回1/0）
- `lt(n1: number, n2: number)` - 小于（返回1/0）
- `iff(condition: number, thenValue: number, elseValue: number)` - 条件判断
- `tr(n_handleNaN: number | undefined, ctx: IContext)` - 真实范围
- `atr(length: number, context: IContext)` - 平均真实范围
- `isdwm(context: IContext)` - 是否日/周/月
- `isintraday(context: IContext)` - 是否日内
- `isdaily(context: IContext)` - 是否日线
- `isweekly(context: IContext)` - 是否周线
- `ismonthly(context: IContext)` - 是否月线
- `selectSessionBreaks(context: IContext, times: number[])` - 选择会话间隔
- `createNewSessionCheck(context: IContext)` - 创建新会话检查
- `error(message: string, title?: string)` - 错误
- `zigzag(n_deviation: number, n_depth: number, context: IContext)` - 锯齿波
- `zigzagbars(n_deviation: number, n_depth: number, context: IContext)` - K线锯齿波
- `updatetime(context: IContext)` - 更新时间
- `ticker(context: IContext)` - 代码
- `percentrank(source: IPineSeries, length: number)` - 百分等级
- `rising(series: IPineSeries, length: number)` - 是否上升
- `falling(series: IPineSeries, length: number)` - 是否下降
- `rsi(upper: number, lower: number)` - RSI
- `sum(source: IPineSeries, length: number, context: IContext)` - 求和
- `sma(source: IPineSeries, length: number, context: IContext)` - 简单移动平均
- `smma(n_value: number, n_length: number, ctx: IContext)` - 平滑移动平均
- `rma(source: IPineSeries, length: number, context: IContext)` - RMA
- `ema(source: IPineSeries, length: number, context: IContext)` - 指数移动平均
- `wma(source: IPineSeries, length: number, context: IContext)` - 加权移动平均
- `vwma(source: IPineSeries, length: number, context: IContext)` - 成交量加权移动平均
- `swma(source: IPineSeries, context: IContext)` - 对称加权移动平均
- `fixnan(n_current: number, context: IContext)` - 修复NaN
- `lowestbars(source: IPineSeries, length: number, context: IContext)` - 最低值偏移
- `lowest(source: IPineSeries, length: number, context: IContext)` - 最低值
- `highestbars(source: IPineSeries, length: number, context: IContext)` - 最高值偏移
- `highest(source: IPineSeries, length: number, context: IContext)` - 最高值
- `cum(n_value: number, context: IContext)` - 累积和
- `accdist(context: IContext)` - 累积/分配
- `correlation(sourceA: IPineSeries, sourceB: IPineSeries, length: number, context: IContext)` - 相关系数
- `stoch(source: IPineSeries, high: IPineSeries, low: IPineSeries, length: number, context: IContext)` - 随机指标
- `tsi(source: IPineSeries, shortLength: number, longLength: number, context: IContext)` - 真实强度指标
- `cross(n_0: number, n_1: number, context: IContext)` - 交叉
- `linreg(source: IPineSeries, length: number, offset: number)` - 线性回归
- `sar(start: number, inc: number, max: number, context: IContext)` - SAR
- `alma(series: IPineSeries, length: number, offset: number, sigma: number)` - ALMA
- `change(source: IPineSeries)` - 变化
- `roc(source: IPineSeries, length: number)` - 变化率
- `dev(source: IPineSeries, length: number, context: IContext)` - 偏差
- `stdev(source: IPineSeries, length: number, context: IContext)` - 标准差
- `variance(source: IPineSeries, length: number, context: IContext)` - 方差
- `add_days_considering_dst(timezone: string, utcTime: Date, daysCount: number)` - 考虑夏令时的天数添加
- `add_years_considering_dst(timezone: string, utcTime: Date, yearsCount: number)` - 考虑夏令时的年数添加
- `dmi(diLength: number, adxSmoothingLength: number, context: IContext)` - DMI
- `na(n?: number)` - 检查NaN
- `nz(x: number, y?: number)` - 替换NaN
- `and(n_0: number, n_1: number)` - 逻辑与
- `or(n_0: number, n_1: number)` - 逻辑或
- `not(n_0: number)` - 逻辑非
- `max(...values: number[])` - 最大值
- `min(...values: number[])` - 最小值
- `pow(base: number, exponent: number)` - 幂
- `abs(x: number)` - 绝对值
- `log(x: number)` - 自然对数
- `log10(x: number)` - 常用对数
- `sqrt(x: number)` - 平方根
- `sign(x: number)` - 符号
- `exp(x: number)` - 指数
- `sin(x: number)` - 正弦
- `cos(x: number)` - 余弦
- `tan(x: number)` - 正切
- `asin(x: number)` - 反正弦
- `acos(x: number)` - 反余弦
- `atan(x: number)` - 反正切
- `floor(x: number)` - 向下取整
- `ceil(x: number)` - 向上取整
- `round(x: number)` - 四舍五入
- `avg(...values: number[])` - 平均
- `n(context: IContext)` - 当前K线索引
- `isZero: (v: number) => number` - 检查零
- `toBool(v: number): boolean` - 转布尔
- `currencyCode(ctx: IContext)` - 货币代码
- `unitId(ctx: IContext)` - 单位ID
- `interval(ctx: IContext)` - 间隔

### `PipValues`
点值
- `buyPipValue` - 买入点值
- `sellPipValue` - 卖出点值

### `PitchforkLineToolOverrides`
音叉线工具覆盖
- `"median.color"` - 中线颜色，默认值：`#F23645`

### `PlaceOrderResult`
下单结果
- `orderId` - 订单ID

### `PlacedOrder`
已下单
- 继承 `PlacedOrderBase` 和 `CustomFields`

### `PlacedOrderBase`
已下单基础
- `id` - ID
- `symbol` - 符号
- `type` - 类型
- `side` - 方向
- `qty` - 数量
- `status` - 状态
- `stopLoss` - 止损
- `guaranteedStop` - 保证止损
- `trailingStopPips` - 移动止损点
- `stopType` - 止损类型
- `takeProfit` - 止盈
- `duration` - 有效期
- `customFields` - 自定义字段
- `filledQty` - 已成交数量
- `avgPrice` - 平均价格
- `updateTime` - 更新时间
- `limitPrice` - 限价
- `stopPrice` - 止损价
- `message` - 消息

### `Plot`
绘图
- `id` - ID

### `PlotOptions`
绘图选项
- `color` - 颜色
- `display` - 显示
- `linewidth` - 线宽
- `offset` - 偏移
- `style` - 样式
- `title` - 标题

### `PlotStyles`
绘图样式
- `line` - 线

### `PlusClickParams`
加号点击参数
- `symbol` - 符号
- `price` - 价格

### `PnFStylePreferences`
点数图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `upColorProjection` - 上涨投影颜色
- `downColorProjection` - 下跌投影颜色

### `PolygonPreferences`
多边形偏好
- `transparency` - 透明度
- `color` - 颜色

### `Position`
持仓
- 继承 `PositionBase` 和 `CustomFields`

### `PositionBase`
持仓基础
- `id` - ID
- `symbol` - 符号
- `qty` - 数量
- `shortQty` - 空头数量
- `longQty` - 多头数量
- `side` - 方向
- `avgPrice` - 平均价格
- `updateTime` - 更新时间
- `message` - 消息

### `PositionDialogOptions`
持仓对话框选项
- 继承 `TradingDialogOptions`

### `PositiveBaseInputFieldValidatorResult`
正向输入字段验证结果
- `valid` - 有效标志

### `PreOrder`
预订单
- 继承 `OrderTemplateBase`
- `isClose` - 是否平仓

### `PriceChannelIndicatorOverrides`
价格通道指标覆盖
- `"highprice line.color"` - 高价线颜色，默认值：`#F50057`
- `"lowprice line.color"` - 低价线颜色，默认值：`#F50057`
- `"centerprice line.color"` - 中线颜色，默认值：`#2196F3`

### `PriceFormatterFormatOptions`
价格格式化器格式选项
- `tailSize` - 尾部大小
- `signNegative` - 负号
- `useRtlFormat` - 从右到左格式
- `cutFractionalByPrecision` - 按精度截断小数
- `removeAllEndingZeros` - 移除所有尾随零

### `PricedPoint`
带价格的点
- 继承 `TimePoint`
- `price` - 价格

### `QuantityMetainfo`
数量元信息
- `min` - 最小值
- `max` - 最大值
- `step` - 步长
- `uiStep` - UI步长
- `default` - 默认值

### `QuoteDataResponse`
报价数据响应
- `s` - 状态
- `n` - 名称
- `v` - 值

### `RangeOptions`
范围选项
- `val` - 值
- `res` - 分辨率

### `RawStudyMetaInfo`
原始研究元信息
- 继承 `RawStudyMetaInfoBase`
- `id` - ID

### `RawStudyMetaInfoBase`
原始研究元信息基础
- `description` - 描述
- `shortDescription` - 短描述
- `name` - 名称
- `_metainfoVersion` - 元信息版本
- `precision` - 精度
- `format` - 格式
- `is_price_study` - 是否价格研究
- `isCustomIndicator` - 是否自定义指标
- `linkedToSeries` - 是否链接到序列
- `priceScale` - 价格刻度
- `is_hidden_study` - 是否隐藏研究
- `defaults` - 默认值
- `bands` - 带
- `filledAreas` - 填充区域
- `inputs` - 输入
- `symbolSource` - 符号源
- `palettes` - 调色板
- `plots` - 绘图
- `styles` - 样式
- `ohlcPlots` - OHLC绘图
- `financialPeriod` - 财务周期
- `groupingKey` - 分组键
- `behind_chart` - 是否在图表后面

### `RegressionTrendIndicatorOverrides`
回归趋势指标覆盖

### `RelativeStrengthIndexIndicatorOverrides`
相对强弱指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#7E57C2`

### `RenkoStylePreferences`
砖形图样式偏好
- `upColor` - 上涨颜色
- `downColor` - 下跌颜色
- `borderUpColor` - 上涨边框颜色
- `borderDownColor` - 下跌边框颜色
- `upColorProjection` - 上涨投影颜色
- `downColorProjection` - 下跌投影颜色
- `borderUpColorProjection` - 上涨投影边框颜色
- `borderDownColorProjection` - 下跌投影边框颜色
- `wickUpColor` - 上涨影线颜色
- `wickDownColor` - 下跌影线颜色

### `RequestFunctions`
请求函数
- `security(tickerId: TickerId, options?: RequestSecurityOptions)` - 安全请求

### `RequestSecurityOptions`
请求安全选项
- `expression` - 表达式

### `RestBrokerConnectionInfo`
REST经纪商连接信息
- `url` - URL
- `access_token` - 访问令牌

### `RuntimeFunctions`
运行时函数
- `error(message: string)` - 错误

### `SMIErgodicIndicatorOscillatorIndicatorOverrides`
SMI遍历指标/震荡器指标覆盖
- `"indicator.color"` - 指标颜色，默认值：`#2196F3`
- `"signal.color"` - 信号线颜色，默认值：`#FF6D00`
- `"oscillator.color"` - 震荡器颜色，默认值：`#FF5252`

### `SaveChartErrorInfo`
保存图表错误信息
- `message` - 消息

### `SaveChartOptions`
保存图表选项
- `includeDrawings` - 包含绘图

### `SaveChartToServerOptions`
保存图表到服务器选项
- `chartName` - 图表名称
- `defaultChartName` - 默认图表名称

### `SaveLoadChartRecord`
保存加载图表记录
- `id` - ID
- `name` - 名称
- `image_url` - 图片URL
- `modified_iso` - 修改时间
- `short_symbol` - 短符号
- `interval` - 间隔

### `SavedStateMetaInfo`
保存状态元信息
- `uid` - UID
- `name` - 名称
- `description` - 描述

### `ScriptContext`
脚本上下文
- `barstate` - K线状态
- `color` - 颜色
- `input` - 输入
- `linestyle` - 线样式
- `math` - 数学
- `plotstyle` - 绘图样式
- `request` - 请求
- `runtime` - 运行时
- `ta` - 技术分析
- `ticker` - 代码
- `timeframe` - 时间框架
- `open()` - 开盘
- `high()` - 最高
- `low()` - 最低
- `close()` - 收盘
- `volume()` - 成交量
- `year()` - 年
- `na(value: number)` - 检查NaN
- `series(value: number)` - 创建序列
- `fill(plot1: HLine, plot2: HLine, options?: Partial<FillOptions>)` - 填充（水平线）
- `fill(plot1: Plot, plot2: Plot, options?: Partial<FillOptions>)` - 填充（绘图）
- `hline(price: number, options?: Partial<HlineOptions>)` - 水平线
- `indicator(options: Partial<IndicatorOptions>)` - 指标
- `plot(source: IPineSeries | number, options?: Partial<PlotOptions>)` - 绘图

### `SearchSymbolResultItem`
搜索符号结果项
- `symbol` - 符号
- `description` - 描述
- `exchange` - 交易所
- `ticker` - 代码
- `type` - 类型
- `logo_urls` - 图标URL数组
- `exchange_logo` - 交易所图标

### `SeriesFieldDescriptor`
序列字段描述符
- `type` - 类型
- `sourceType` - 源类型
- `plotTitle` - 绘图标题
- `sourceTitle` - 源标题

### `SeriesPreferencesMap`
序列偏好映射
- `[ChartStyle.Bar]` - 条形图偏好
- `[ChartStyle.Candle]` - 蜡烛图偏好
- `[ChartStyle.Line]` - 线图偏好
- `[ChartStyle.LineWithMarkers]` - 带标记线图偏好
- `[ChartStyle.Stepline]` - 阶梯线图偏好
- `[ChartStyle.Area]` - 面积图偏好
- `[ChartStyle.HLCArea]` - HLC面积图偏好
- `[ChartStyle.Renko]` - 砖形图偏好
- `[ChartStyle.Kagi]` - 卡吉图偏好
- `[ChartStyle.PnF]` - 点数图偏好
- `[ChartStyle.LineBreak]` - 新线图偏好
- `[ChartStyle.HeikinAshi]` - 平均K线偏好
- `[ChartStyle.HollowCandle]` - 空心蜡烛偏好
- `[ChartStyle.Baseline]` - 基线偏好
- `[ChartStyle.HiLo]` - 高低图偏好
- `[ChartStyle.Column]` - 柱状图偏好
- `[ChartStyle.HLCBars]` - HLC条形图偏好
- `[ChartStyle.VolCandle]` - 成交量蜡烛偏好

### `SetResolutionOptions`
设置分辨率选项
- `dataReady` - 数据就绪回调
- `doNotActivateChart` - 不激活图表

### `SetSymbolOptions`
设置符号选项
- `dataReady` - 数据就绪回调
- `doNotActivateChart` - 不激活图表

### `SetVisibleRangeOptions`
设置可见范围选项
- `applyDefaultRightMargin` - 应用默认右边距
- `percentRightMargin` - 百分比右边距
- `rejectByTimeout` - 超时拒绝

### `SingleBrokerMetaInfo`
单个经纪商元信息
- `configFlags` - 配置标志
- `customNotificationFields` - 自定义通知字段
- `durations` - 有效期
- `orderRules` - 订单规则
- `customUI` - 自定义UI

### `SolidFillOptions`
纯色填充选项
- `color` - 颜色

### `SortingParameters`
排序参数
- `property` - 属性
- `asc` - 升序

### `SourceInputOptions`
源输入选项
- 继承 `CommonInputOptions`

### `StandardFormattersDependenciesMapping`
标准格式化器依赖映射
- `[StandardFormatterName.Default]` - 默认
- `[StandardFormatterName.Symbol]` - 符号
- `[StandardFormatterName.Side]` - 方向
- `[StandardFormatterName.PositionSide]` - 持仓方向
- `[StandardFormatterName.Text]` - 文本
- `[StandardFormatterName.Type]` - 类型
- `[StandardFormatterName.FormatPrice]` - 格式化价格
- `[StandardFormatterName.FormatPriceForexSup]` - 格式化外汇价格
- `[StandardFormatterName.FormatPriceInCurrency]` - 格式化货币价格
- `[StandardFormatterName.Status]` - 状态
- `[StandardFormatterName.Date]` - 日期
- `[StandardFormatterName.LocalDate]` - 本地日期
- `[StandardFormatterName.DateOrDateTime]` - 日期或日期时间
- `[StandardFormatterName.LocalDateOrDateTime]` - 本地日期或日期时间
- `[StandardFormatterName.Fixed]` - 固定
- `[StandardFormatterName.FixedInCurrency]` - 固定货币
- `[StandardFormatterName.VariablePrecision]` - 可变精度
- `[StandardFormatterName.Pips]` - 点值
- `[StandardFormatterName.IntegerSeparated]` - 整数分隔
- `[StandardFormatterName.FormatQuantity]` - 格式化数量
- `[StandardFormatterName.Profit]` - 利润
- `[StandardFormatterName.ProfitInInstrumentCurrency]` - 工具货币利润
- `[StandardFormatterName.ProfitInPercent]` - 利润百分比
- `[StandardFormatterName.Percentage]` - 百分比
- `[StandardFormatterName.MarginPercent]` - 保证金百分比
- `[StandardFormatterName.Empty]` - 空

### `StickedPoint`
固定点
- 继承 `TimePoint`
- `channel` - 通道

### `StochasticIndicatorOverrides`
随机指标覆盖
- `"%k.color"` - %K线颜色，默认值：`#2196F3`
- `"%d.color"` - %D线颜色，默认值：`#FF6D00`

### `StochasticRSIIndicatorOverrides`
随机RSI指标覆盖
- `"%k.color"` - %K线颜色，默认值：`#2196F3`
- `"%d.color"` - %D线颜色，默认值：`#FF6D00`

### `StringInputOptions`
字符串输入选项
- `options` - 选项数组

### `StudyArrowsPlotInfo`
研究箭头绘图信息
- 继承 `StudyPlotBaseInfo`
- `type` - 类型

### `StudyArrowsPlotPreferences`
研究箭头绘图偏好
- `colorup` - 上涨箭头颜色
- `colordown` - 下跌箭头颜色
- `minHeight` - 最小高度
- `maxHeight` - 最大高度

### `StudyBandBackgroundPreferences`
研究带背景偏好
- `backgroundColor` - 背景色
- `transparency` - 透明度
- `fillBackground` - 填充背景

### `StudyBandInfo`
研究带信息
- `id` - ID
- `name` - 名称
- `isHidden` - 是否隐藏
- `zorder` - Z轴顺序

### `StudyBandPreferences`
研究带偏好
- 继承 `StudyBandStyle` 和 `StudyBandInfo`

### `StudyBandStyle`
研究带样式
- `color` - 颜色
- `linestyle` - 线样式
- `linewidth` - 线宽
- `value` - 值
- `visible` - 可见性

### `StudyBarColorerPlotInfo`
研究K线着色器绘图信息
- 继承 `StudyPalettedPlotInfo`
- `type` - 类型

### `StudyBarTimeInputInfo`
研究K线时间输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `max` - 最大值
- `min` - 最小值

### `StudyBgColorerPlotInfo`
研究背景着色器绘图信息
- 继承 `StudyPalettedPlotInfo`
- `type` - 类型

### `StudyBooleanInputInfo`
研究布尔输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值

### `StudyCandleBorderColorerPlotInfo`
研究蜡烛边框着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyCandleWickColorerPlotInfo`
研究蜡烛芯着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyCharsPlotInfo`
研究字符绘图信息
- 继承 `StudyPlotBaseInfo`
- `type` - 类型

### `StudyCharsPlotPreferences`
研究字符绘图偏好
- `char` - 字符
- `location` - 位置
- `color` - 颜色
- `textColor` - 文本颜色

### `StudyColorInputInfo`
研究颜色输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值

### `StudyColorerPlotInfo`
研究着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyDataOffsetPlotInfo`
研究数据偏移绘图信息
- 继承 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyDataPlotInfo`
研究数据绘图信息
- 继承 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyDefaults`
研究默认值
- `areaBackground` - 区域背景
- `bandsBackground` - 带背景
- `bands` - 带
- `filledAreasStyle` - 填充区域样式
- `inputs` - 输入
- `palettes` - 调色板
- `precision` - 精度
- `styles` - 样式
- `ohlcPlots` - OHLC绘图
- `graphics` - 图形

### `StudyDownColorerPlotInfo`
研究下跌着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyFieldDescriptor`
研究字段描述符
- `type` - 类型
- `sourceType` - 源类型
- `sourceId` - 源ID
- `sourceTitle` - 源标题
- `plotTitle` - 绘图标题

### `StudyFilledAreaGradientColorStyle`
研究填充区域渐变颜色样式
- `fillType` - 填充类型
- `topColor` - 顶部颜色
- `bottomColor` - 底部颜色
- `topValue` - 顶部值
- `bottomValue` - 底部值

### `StudyFilledAreaInfo`
研究填充区域信息
- `id` - ID
- `objAId` - 对象A ID
- `objBId` - 对象B ID
- `title` - 标题
- `type` - 类型
- `fillgaps` - 填充间隙
- `zorder` - Z轴顺序
- `isHidden` - 是否隐藏
- `palette` - 调色板
- `topValue` - 顶部值
- `bottomValue` - 底部值
- `topColor` - 顶部颜色
- `bottomColor` - 底部颜色
- `fillToIntersection` - 填充到交叉点

### `StudyFilledAreaSolidColorStyle`
研究填充区域纯色颜色样式
- `fillType` - 填充类型
- `color` - 颜色

### `StudyFilledAreaStyleBase`
研究填充区域样式基础
- `visible` - 可见性
- `transparency` - 透明度

### `StudyGraphicsDefaults`
研究图形默认值
- `horizlines` - 水平线
- `polygons` - 多边形
- `hhists` - 水平直方图
- `vertlines` - 垂直线

### `StudyInputBaseInfo`
研究输入基础信息
- `id` - ID
- `name` - 名称
- `defval` - 默认值
- `type` - 类型
- `confirm` - 确认
- `isHidden` - 是否隐藏
- `visible` - 可见性
- `hideWhenPlotsHidden` - 当绘图隐藏时隐藏
- `active` - 是否激活

### `StudyInputInformation`
研究输入信息
- `id` - ID
- `name` - 名称
- `type` - 类型
- `localizedName` - 本地化名称

### `StudyInputOptionsTitles`
研究输入选项标题
- `[option: string]` - 选项标题

### `StudyInputValueItem`
研究输入值项
- `id` - ID
- `value` - 值

### `StudyInputsSimple`
研究输入简单映射
- `[inputId: string]` - 输入值

### `StudyLinePlotInfo`
研究线绘图信息
- 继承 `StudyPlotBaseInfo`
- `type` - 类型

### `StudyLinePlotPreferences`
研究线绘图偏好
- `plottype` - 绘图类型
- `color` - 颜色
- `linestyle` - 线样式
- `linewidth` - 线宽
- `trackPrice` - 跟踪价格
- `showLast` - 显示最后数量

### `StudyNumericInputInfo`
研究数字输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `max` - 最大值
- `min` - 最小值
- `step` - 步长

### `StudyOhlcColorerPlotInfo`
研究OHLC着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyOhlcPlotBarsStylePreferences`
研究OHLC绘图条形样式偏好
- `plottype` - 绘图类型
- `color` - 颜色

### `StudyOhlcPlotBaseStylePreferences`
研究OHLC绘图基础样式偏好
- `color` - 颜色
- `display` - 显示
- `visible` - 可见性

### `StudyOhlcPlotCandlesStylePreferences`
研究OHLC绘图蜡烛样式偏好
- `plottype` - 绘图类型
- `color` - 颜色
- `drawWick` - 画影线
- `drawBorder` - 画边框
- `wickColor` - 影线颜色
- `borderColor` - 边框颜色

### `StudyOhlcPlotInfo`
研究OHLC绘图信息
- 继承 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyOhlcStylesInfo`
研究OHLC样式信息
- `title` - 标题
- `isHidden` - 是否隐藏
- `drawBorder` - 画边框
- `showLast` - 显示最后数量
- `forceOverlay` - 强制覆盖
- `format` - 格式

### `StudyOrDrawingAddedToChartEventParams`
研究或绘图添加到图表事件参数
- `label` - 标签
- `value` - 值

### `StudyOverrides`
研究覆盖

### `StudyPaletteColor`
研究调色板颜色
- `color` - 颜色
- `style` - 样式
- `width` - 宽度

### `StudyPaletteColorPreferences`
研究调色板颜色偏好
- 继承 `StudyPaletteColor` 和 `StudyPaletteInfo`

### `StudyPaletteInfo`
研究调色板信息
- `name` - 名称

### `StudyPalettePreferences`
研究调色板偏好
- `colors` - 颜色

### `StudyPaletteStyle`
研究调色板样式
- `colors` - 颜色

### `StudyPalettedPlotInfo`
研究调色板绘图信息
- 继承 `StudyPlotBaseInfo`
- `palette` - 调色板

### `StudyPalettesInfo`
研究调色板集合信息
- `colors` - 颜色
- `valToIndex` - 值到索引映射
- `addDefaultColor` - 添加默认颜色

### `StudyPlotBaseInfo`
研究绘图基础信息
- `id` - ID
- `type` - 类型

### `StudyPlotBasePreferences`
研究绘图基础偏好
- `transparency` - 透明度
- `display` - 显示
- `visible` - 可见性

### `StudyPlotValueInheritFormat`
研究绘图值继承格式
- `type` - 类型

### `StudyPlotValuePrecisionFormat`
研究绘图值精度格式
- `type` - 类型
- `precision` - 精度

### `StudyPriceInputInfo`
研究价格输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `max` - 最大值
- `min` - 最小值
- `step` - 步长

### `StudyResolutionInputInfo`
研究分辨率输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `options` - 选项
- `optionsTitles` - 选项标题
- `isMTFResolution` - 是否多时间框架分辨率

### `StudyResultValueWithOffset`
研究结果值带偏移
- `value` - 值
- `offset` - 偏移

### `StudyRgbaColorerPlotInfo`
研究RGBA着色器绘图信息
- 继承 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudySessionInputInfo`
研究会话输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `options` - 选项
- `optionsTitles` - 选项标题

### `StudyShapesPlotInfo`
研究形状绘图信息
- 继承 `StudyPlotBaseInfo`
- `type` - 类型

### `StudyShapesPlotPreferences`
研究形状绘图偏好
- `plottype` - 绘图类型
- `location` - 位置
- `color` - 颜色
- `textColor` - 文本颜色

### `StudySourceInputInfo`
研究源输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `options` - 选项
- `optionsTitles` - 选项标题

### `StudyStyleInfo`
研究样式信息
- `defaults` - 默认值
- `plots` - 绘图
- `styles` - 样式
- `bands` - 带
- `filledAreas` - 填充区域
- `palettes` - 调色板

### `StudyStyleInfoDefaults`
研究样式信息默认值
- `bands` - 带
- `filledAreasStyle` - 填充区域样式
- `palettes` - 调色板
- `styles` - 样式
- `ohlcPlots` - OHLC绘图
- `graphics` - 图形

### `StudyStyleValues`
研究样式值
- `ohlcPlots` - OHLC绘图
- `bands` - 带
- `palettes` - 调色板
- `styles` - 样式
- `filledAreas` - 填充区域
- `filledAreasStyle` - 填充区域样式
- `graphics` - 图形

### `StudyStylesInfo`
研究样式信息
- `histogramBase` - 直方图基础
- `joinPoints` - 连接点
- `title` - 标题
- `isHidden` - 是否隐藏
- `minHeight` - 最小高度
- `maxHeight` - 最大高度
- `size` - 大小
- `char` - 字符
- `text` - 文本
- `showLast` - 显示最后数量
- `zorder` - Z轴顺序
- `format` - 格式
- `forceOverlay` - 强制覆盖

### `StudySymbolInputInfo`
研究符号输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `optional` - 是否可选

### `StudyTargetedPlotInfo`
研究目标绘图信息
- 继承 `StudyPlotBaseInfo`
- `target` - 目标
- `targetField` - 目标字段

### `StudyTemplateData`
研究模板数据
- `name` - 名称
- `content` - 内容

### `StudyTemplateMetaInfo`
研究模板元信息
- `name` - 名称

### `StudyTextColorerPlotInfo`
研究文本着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StudyTextInputInfo`
研究文本输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `options` - 选项
- `optionsTitles` - 选项标题

### `StudyTextareaInputInfo`
研究多行文本输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值

### `StudyTimeInputInfo`
研究时间输入信息
- 继承 `StudyInputBaseInfo`
- `type` - 类型
- `defval` - 默认值
- `max` - 最大值
- `min` - 最小值

### `StudyUpColorerPlotInfo`
研究上涨着色器绘图信息
- 继承 `StudyPalettedPlotInfo` 和 `StudyTargetedPlotInfo`
- `type` - 类型

### `StyledText`
带样式文本
- `text` - 文本
- `font` - 字体
- `fontFamily` - 字体系列
- `fontFeatureSettings` - 字体特性设置
- `fontKerning` - 字体字距
- `fontOpticalSizing` - 字体光学大小
- `fontPalette` - 字体调色板
- `fontSize` - 字体大小
- `fontSizeAdjust` - 字体大小调整
- `fontStretch` - 字体拉伸
- `fontStyle` - 字体样式
- `fontSynthesis` - 字体合成
- `fontVariant` - 字体变体
- `fontVariantAlternates` - 字体变体替代
- `fontVariantCaps` - 字体变体大写
- `fontVariantEastAsian` - 字体变体东亚
- `fontVariantLigatures` - 字体变体连字
- `fontVariantNumeric` - 字体变体数字
- `fontVariantPosition` - 字体变体位置
- `fontVariationSettings` - 字体变化设置
- `fontWeight` - 字体粗细
- `color` - 颜色
- `lineHeight` - 行高
- `letterSpacing` - 字母间距

### `SubLayoutSizesState`
子布局大小状态
- `percent` - 百分比
- `substate` - 子状态

### `SubscribeEventsMap`
订阅事件映射
- `toggle_sidebar` - 切换侧边栏
- `indicators_dialog` - 指标对话框
- `toggle_header` - 切换头部
- `edit_object_dialog` - 编辑对象对话框
- `chart_load_requested` - 图表加载请求
- `chart_loaded` - 图表加载完成
- `mouse_down` - 鼠标按下
- `mouse_up` - 鼠标释放
- `drawing` - 绘图
- `study` - 研究
- `undo` - 撤销
- `redo` - 重做
- `undo_redo_state_changed` - 撤销/重做状态变更
- `reset_scales` - 重置刻度
- `compare_add` - 比较添加
- `add_compare` - 添加比较
- `load_study_template` - 加载研究模板
- `onTick` - 实时数据更新
- `onAutoSaveNeeded` - 自动保存需要
- `onScreenshotReady` - 截图就绪
- `onMarkClick` - 标记点击
- `onPlusClick` - 加号点击
- `onTimescaleMarkClick` - 时间刻度标记点击
- `onSelectedLineToolChanged` - 选中线工具变更
- `layout_about_to_be_changed` - 布局即将变更
- `layout_changed` - 布局变更
- `activeChartChanged` - 活动图表变更
- `series_event` - 序列事件
- `study_event` - 研究事件
- `drawing_event` - 绘图事件
- `study_properties_changed` - 研究属性变更
- `series_properties_changed` - 序列属性变更
- `panes_height_changed` - 面板高度变更
- `panes_order_changed` - 面板顺序变更
- `widgetbar_visibility_changed` - 构件栏可见性变更
- `study_dialog_save_defaults` - 研究对话框保存默认值
- `timeframe_interval` - 时间框架间隔
- `dragstart` - 拖拽开始
- `dragend` - 拖拽结束
- `chart_theme_changed` - 图表主题变更

### `SuperTrendIndicatorOverrides`
超级趋势指标覆盖
- `"supertrend.color"` - 超级趋势颜色，默认值：`#000080`
- `"up arrow.color"` - 上涨箭头颜色，默认值：`#00FF00`
- `"down arrow.color"` - 下跌箭头颜色，默认值：`#FF0000`

### `SymbolExt`
扩展符号信息
- 继承 `LibrarySymbolInfo`

### `SymbolFormatterProperties`
符号格式化器属性
- `base` - 基础
- `withMessage` - 带消息

### `SymbolInfoPriceSource`
符号信息价格源
- `id` - ID
- `name` - 名称

### `SymbolInputOptions`
符号输入选项
- 继承 `CommonInputOptions`

### `SymbolInputSymbolSource`
符号输入符号源
- `type` - 类型
- `inputId` - 输入ID

### `SymbolIntervalResult`
符号间隔结果
- `symbol` - 符号
- `interval` - 间隔

### `SymbolResolveExtension`
符号解析扩展
- `currencyCode` - 货币代码
- `unitId` - 单位ID
- `session` - 会话

### `SymbolSearchCompleteData`
符号搜索完成数据
- `symbol` - 符号
- `name` - 名称

### `SymbolSpecificTradingOptions`
符号特定交易选项
- `allowedDurations` - 允许的有效期
- `allowedOrderTypes` - 允许的订单类型
- `supportOrderBrackets` - 支持订单括号
- `supportBracketsInPips` - 支持点值括号
- `supportAddBracketsToExistingOrder` - 支持为现有订单添加括号
- `supportModifyBrackets` - 支持修改括号
- `supportPositionBrackets` - 支持持仓括号
- `supportIndividualPositionBrackets` - 支持单个持仓括号
- `supportReversePosition` - 支持反向持仓
- `warningMessage` - 警告消息
- `supportModifyPositionBrackets` - 支持修改持仓括号
- `supportModifyOrderBrackets` - 支持修改订单括号
- `supportRiskControlsAndInfo` - 支持风险控制和信息

### `SymbolValueFormatterFormatOptions`
符号值格式化器格式选项
- `signPositive` - 正号

### `TAFunctions`
技术分析函数
- `change(source: IPineSeries)` - 变化
- `correlation(source1: IPineSeries, source2: IPineSeries, length: number)` - 相关系数
- `cum(source: IPineSeries)` - 累积和
- `ema(source: IPineSeries, length: number)` - 指数移动平均
- `rma(source: IPineSeries, length: number)` - RMA
- `sma(source: IPineSeries, length: number)` - 简单移动平均
- `vwap(source: IPineSeries, anchor: boolean, stdDevMult: number)` - 成交量加权平均价格
- `wma(source: IPineSeries, length: number)` - 加权移动平均

### `TRIXIndicatorOverrides`
TRIX指标覆盖
- `"trix.color"` - TRIX颜色，默认值：`#F23645`

### `TableFormatterInputs`
表格格式化器输入
- `values` - 值数组
- `prevValues` - 前值数组

### `TextFieldMetaInfo`
文本字段元信息
- `inputType` - 输入类型
- `value` - 值
- `validator` - 验证器
- `maskWithAsterisk` - 星号掩码

### `TextWithCheckboxFieldCustomInfo`
带复选框文本字段自定义信息
- `checkboxTitle` - 复选框标题
- `asterix` - 星号

### `TextWithCheckboxFieldMetaInfo`
带复选框文本字段元信息
- `inputType` - 输入类型
- `value` - 值
- `customInfo` - 自定义信息
- `validator` - 验证器

### `TextWithCheckboxValue`
带复选框文本值
- `text` - 文本
- `checked` - 是否选中

### `TickerFunctions`
代码函数
- `modify(symbol: string, session?: SessionId)` - 修改

### `TimeFieldDescriptor`
时间字段描述符
- `type` - 类型

### `TimeFrameItem`
时间框架项
- `text` - 文本
- `resolution` - 分辨率
- `description` - 描述
- `title` - 标题

### `TimeFramePeriodBack`
时间框架回溯周期
- `type` - 类型
- `value` - 值

### `TimeFrameTimeRange`
时间框架时间范围
- `type` - 类型
- `from` - 开始
- `to` - 结束

### `TimePoint`
时间点
- `time` - 时间

### `TimeScaleOptions`
时间刻度选项
- `min_bar_spacing` - 最小柱间距

### `TimescaleMark`
时间刻度标记
- `id` - ID
- `time` - 时间
- `color` - 颜色
- `labelFontColor` - 标签字体颜色
- `label` - 标签
- `tooltip` - 工具提示
- `shape` - 形状
- `imageUrl` - 图片URL
- `showLabelWhenImageLoaded` - 图片加载后是否显示标签

### `TimezoneInfo`
时区信息
- `id` - ID
- `title` - 标题
- `offset` - 偏移
- `alias` - 别名

### `TradableSolutionsTypes`
可交易解决方案类型
- `changeAccountSolution` - 更改账户
- `changeSymbolSolution` - 更改符号
- `openUrlSolution` - 打开URL

### `TradeContext`
交易上下文
- `symbol` - 符号
- `displaySymbol` - 显示符号
- `value` - 值
- `formattedValue` - 格式化值
- `last` - 最后值

### `TradingCustomization`
交易自定义
- `position` - 持仓线覆盖
- `order` - 订单线覆盖
- `brokerOrder` - 经纪商订单覆盖
- `brokerPosition` - 经纪商持仓覆盖

### `TradingDialogOptions`
交易对话框选项
- `customFields` - 自定义字段

### `TradingQuotes`
交易报价
- `trade` - 交易
- `size` - 大小
- `bid` - 买价
- `bid_size` - 买量
- `ask` - 卖价
- `ask_size` - 卖量
- `spread` - 价差
- `isDelayed` - 是否延迟
- `isHalted` - 是否停牌
- `isHardToBorrow` - 是否难借
- `isNotShortable` - 是否不可做空

### `TradingTerminalWidgetOptions`
交易终端构件选项
- 继承 `Omit<ChartingLibraryWidgetOptions, "enabled_features" | "disabled_features" | "favorites">`
- `disabled_features` - 禁用功能
- `enabled_features` - 启用功能
- `favorites` - 收藏夹
- `brokerConfig` - 经纪商配置
- `broker_config` - 经纪商配置
- `restConfig` - REST配置
- `widgetbar` - 构件栏参数
- `rss_news_feed` - RSS新闻源
- `rss_news_title` - RSS新闻标题
- `news_provider` - 新闻提供者
- `trading_customization` - 交易自定义
- `broker_factory` - 经纪商工厂
- `debug_broker` - 调试经纪商

### `TrendStrengthIndexIndicatorOverrides`
趋势强度指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#FF5252`

### `TrueStrengthIndexIndicatorOverrides`
真实强度指标覆盖
- `"true strength index.color"` - TSI颜色，默认值：`#2196F3`
- `"signal.color"` - 信号线颜色，默认值：`#E91E63`

### `TypicalPriceIndicatorOverrides`
典型价格指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#FF6D00`

### `UltimateOscillatorIndicatorOverrides`
终极震荡器指标覆盖
- `"uo.color"` - UO颜色，默认值：`#F23645`

### `UndoOptions`
撤销选项
- `disableUndo` - 禁用撤销

### `UndoRedoState`
撤销/重做状态
- `enableUndo` - 启用撤销
- `undoText` - 撤销文本
- `enableRedo` - 启用重做
- `redoText` - 重做文本
- `originalUndoText` - 原始撤销文本
- `originalRedoText` - 原始重做文本

### `Unit`
单位
- `id` - ID
- `name` - 名称
- `description` - 描述

### `UnitInfo`
单位信息
- `selectedUnit` - 选中的单位
- `originalUnits` - 原始单位
- `availableGroups` - 可用组
- `symbols` - 符号

### `UserTimeFieldDescriptor`
用户时间字段描述符
- `type` - 类型

### `VWAPIndicatorOverrides`
VWAP指标覆盖
- `"vwap.color"` - VWAP颜色，默认值：`#2196F3`

### `VWMAIndicatorOverrides`
VWMA指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `ValueByStyleId`
按样式ID的值
- `[styleId: string]` - 值

### `VertLinePreferences`
垂直线偏好
- `visible` - 可见性
- `width` - 宽度
- `color` - 颜色
- `style` - 样式

### `VisibleBarsTimeRange`
可见K线时间范围
- `from` - 开始
- `to` - 结束

### `VisiblePriceRange`
可见价格范围
- `from` - 开始
- `to` - 结束

### `VisibleTimeRange`
可见时间范围
- `from` - 开始
- `to` - 结束

### `VolatilityClosetoCloseIndicatorOverrides`
波动率（收盘价）指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `VolatilityIndexIndicatorOverrides`
波动率指数指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#FF5252`

### `VolatilityOHLCIndicatorOverrides`
波动率OHLC指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#FF5252`

### `VolatilityZeroTrendClosetoCloseIndicatorOverrides`
波动率零趋势（收盘价）指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `VolumeIndicatorOverrides`
成交量指标覆盖
- `"volume.color"` - 成交量颜色，默认值：`#000080`

### `VolumeOscillatorIndicatorOverrides`
成交量震荡器指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

### `VolumeProfileFixedRangeIndicatorOverrides`
固定范围成交量分布指标覆盖

### `VolumeProfileVisibleRangeIndicatorOverrides`
可见范围成交量分布指标覆盖

### `VortexIndicatorIndicatorOverrides`
涡旋指标覆盖
- `"vi +.color"` - VI+颜色，默认值：`#2196F3`
- `"vi -.color"` - VI-颜色，默认值：`#E91E63`

### `WatchListSymbolList`
观察列表符号列表
- `id` - ID
- `symbols` - 符号数组
- `title` - 标题

### `WatchListSymbolListData`
观察列表符号列表数据
- `symbols` - 符号数组
- `title` - 标题

### `WatchListSymbolListMap`
观察列表符号列表映射
- `[listId: string]` - 列表

### `WatchedValueSubscribeOptions`
可观察值订阅选项
- `once` - 仅一次
- `callWithLast` - 使用最后一个值调用

### `WatchlistSettings`
观察列表设置
- `default_symbols` - 默认符号
- `readonly` - 只读

### `WatermarkContentData`
水印内容数据
- `symbolInfo` - 符号信息
- `interval` - 间隔

### `WatermarkLine`
水印行
- `text` - 文本
- `fontSize` - 字体大小
- `lineHeight` - 行高
- `vertOffset` - 垂直偏移

### `WidgetBarParams`
构件栏参数
- `details` - 详情
- `watchlist` - 观察列表
- `news` - 新闻
- `datawindow` - 数据窗口
- `watchlist_settings` - 观察列表设置

### `WilliamsAlligatorIndicatorOverrides`
威廉鳄鱼指标覆盖
- `"jaw.color"` - 颚线颜色，默认值：`#2196F3`
- `"teeth.color"` - 齿线颜色，默认值：`#E91E63`
- `"lips.color"` - 唇线颜色，默认值：`#66BB6A`

### `WilliamsFractalIndicatorOverrides`
威廉分形指标覆盖
- `"down fractals.color"` - 下跌分形颜色，默认值：`#F23645`
- `"up fractals.color"` - 上涨分形颜色，默认值：`#089981`

### `WilliamsRIndicatorOverrides`
威廉指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#7E57C2`

### `ZigZagIndicatorOverrides`
ZigZag指标覆盖
- `"plot.color"` - 绘图颜色，默认值：`#2196F3`

---

## 类型别名

### `AccountId`
账户ID类型别名

### `AccountManagerColumn`
账户管理器列类型别名

### `ActionMetaInfo`
操作元信息类型别名

### `AskBid`
买卖报价类型别名

### `AvailableSaveloadVersions`
可用保存加载版本类型别名

### `BrokerDebugMode`
经纪商调试模式类型别名

### `CellAlignment`
单元格对齐类型别名

### `ChartActionId`
图表操作ID类型别名

### `ChartDescriptorFunction`
图表描述函数类型别名

### `ChartTypeFavorites`
图表类型收藏夹类型别名

### `ChartingLibraryFeatureset`
图表库功能集类型别名

### `ColorGradient`
颜色渐变类型别名

### `ColorTypes`
颜色类型类型别名

### `ColumnStyleBaselinePosition`
柱状图样式基线位置类型别名

### `ContextMenuItemsProcessor`
上下文菜单项处理器类型别名

### `ContextMenuRendererFactory`
上下文菜单渲染器工厂类型别名

### `CreateButtonOptions`
创建按钮选项类型别名

### `CustomStudyFormatter`
自定义研究格式化器类型别名

### `CustomStudyFormatterFactory`
自定义研究格式化器工厂类型别名

### `CustomTableFormatElementFunction`
自定义表格格式化元素函数类型别名

### `CustomTimezoneId`
自定义时区ID类型别名

### `CustomTimezones`
自定义时区类型别名

### `CustomTranslateFunction`
自定义翻译函数类型别名

### `DOMCallback`
深度市场回调类型别名

### `DatafeedErrorCallback`
数据源错误回调类型别名

### `DateFormat`
日期格式类型别名

### `DeepWriteable<T>`
深度可写类型别名

### `Direction`
方向类型别名

### `DisplayOption`
显示选项类型别名

### `DrawingEventType`
绘图事件类型类型别名

### `DrawingOverrides`
绘图覆盖类型别名

### `DrawingToolIdentifier`
绘图工具标识符类型别名

### `DropdownUpdateParams`
下拉菜单更新参数类型别名

### `EditObjectDialogObjectType`
编辑对象对话框对象类型类型别名

### `EmptyCallback`
空回调类型别名

### `EntityId`
实体ID类型别名

### `FieldDescriptor`
字段描述符类型别名

### `FillOptions`
填充选项类型别名

### `FinancialPeriod`
财务周期类型别名

### `FormatterName`
格式化器名称类型别名

### `GetMarksCallback<T>`
获取标记回调类型别名

### `GetNewsFunction`
获取新闻函数类型别名

### `GmtTimezoneId`
GMT时区ID类型别名

### `GridLinesMode`
网格线模式类型别名

### `GroupLockState`
组锁定状态类型别名

### `GroupVisibilityState`
组可见性状态类型别名

### `HeaderWidgetButtonsMode`
头部构件按钮模式类型别名

### `HistoryCallback`
历史回调类型别名

### `IActionVariant`
操作变体类型别名

### `IBarArray`
K线数组类型别名

### `IBasicDataFeed`
基础数据源类型别名

### `IPineStudyResult`
Pine研究结果类型别名

### `IPineStudyResultSimple`
简单Pine研究结果类型别名

### `IPineStudyResultTypes<TPineStudyResultSimple>`
Pine研究结果类型类型别名

### `IProjectionBar`
投影K线类型别名

### `ISeriesStudyResult`
序列研究结果类型别名

### `InputFieldValidator`
输入字段验证器类型别名

### `InputFieldValidatorResult`
输入字段验证器结果类型别名

### `LanguageCode`
语言代码类型别名

### `LayoutSizes`
布局大小类型别名

### `LayoutSizesState`
布局大小状态类型别名

### `LayoutType`
布局类型类型别名

### `LegendMode`
图例模式类型别名

### `LibrarySessionId`
库会话ID类型别名

### `LineStudyPlotStyleName`
线研究图样式名称类型别名

### `LineToolsAndGroupsLoadRequestType`
线工具和组加载请求类型类型别名

### `MarkConstColors`
标记常量颜色类型别名

### `MarkupText`
标记文本类型别名

### `MultipleChartsLayoutType`
多图表布局类型类型别名

### `ObservableCallback<T>`
可观察回调类型别名

### `OmitActionId<T extends { actionId: ActionId; }>`
省略操作ID类型别名

### `OnActionExecuteHandler`
操作执行处理器类型别名

### `OnActionUpdateHandler`
操作更新处理器类型别名

### `OnReadyCallback`
就绪回调类型别名

### `Order`
订单类型别名

### `OrderLineLengthUnit`
订单线长度单位类型别名

### `OrderPreviewMessage`
订单预览消息类型别名

### `OrderTableColumn`
订单表列类型别名

### `OverlayIndicatorOverridesAll`
覆盖指标覆盖所有类型别名

### `OverlayIndicatorStyleExclusions`
覆盖指标样式排除类型别名

### `PageName`
页面名称类型别名

### `PlotShapeId`
绘图形状ID类型别名

### `PositionLineLengthUnit`
持仓线长度单位类型别名

### `PriceSource`
价格源类型别名

### `QuoteData`
报价数据类型别名

### `QuotesCallback`
报价回调类型别名

### `QuotesErrorCallback`
报价错误回调类型别名

### `RawStudyMetaInfoId`
原始研究元信息ID类型别名

### `RawStudyMetaInformation`
原始研究元信息类型别名

### `ResolutionString`
分辨率字符串类型别名

### `ResolveCallback`
解析回调类型别名

### `RssNewsFeedItem`
RSS新闻源项类型别名

### `SearchSymbolsCallback`
搜索符号回调类型别名

### `SeriesEventType`
序列事件类型类型别名

### `SeriesFormat`
序列格式类型别名

### `SeriesFormatterFactory`
序列格式化器工厂类型别名

### `SeriesPriceScale`
序列价格刻度类型别名

### `SeriesStatusViewSymbolTextSource`
序列状态视图符号文本源类型别名

### `ServerTimeCallback`
服务器时间回调类型别名

### `SessionId`
会话ID类型别名

### `SetVisibleTimeRange`
设置可见时间范围类型别名

### `ShapePoint`
形状点类型别名

### `ShapesGroupId`
形状组ID类型别名

### `SingleChartLayoutType`
单图表布局类型类型别名

### `SingleIndicatorOverrides`
单指标覆盖类型别名

### `StudyEventType`
研究事件类型类型别名

### `StudyFilledAreaStyle`
研究填充区域样式类型别名

### `StudyInputId`
研究输入ID类型别名

### `StudyInputInfo`
研究输入信息类型别名

### `StudyInputInfoList`
研究输入信息列表类型别名

### `StudyInputValue`
研究输入值类型别名

### `StudyMetaInfo`
研究元信息类型别名

### `StudyOhlcPlotPreferences`
研究OHLC绘图偏好类型别名

### `StudyOverrideValueType`
研究覆盖值类型别名

### `StudyPlotDisplayMode`
研究绘图显示模式类型别名

### `StudyPlotInfo`
研究绘图信息类型别名

### `StudyPlotInformation`
研究绘图信息类型别名

### `StudyPlotPreferences`
研究绘图偏好类型别名

### `StudyPlotValueFormat`
研究绘图值格式类型别名

### `StudyPriceScale`
研究价格刻度类型别名

### `StudyPriceSource`
研究价格源类型别名

### `StudyPrimitiveResult`
研究原始结果类型别名

### `StudyScript`
研究脚本类型别名

### `SubscribeBarsCallback`
订阅K线回调类型别名

### `SuggestedQtyChangedListener`
建议数量变更监听器类型别名

### `SupportedLineTools`
支持的线工具类型别名

### `SymbolSearchCompleteOverrideFunction`
符号搜索完成覆盖函数类型别名

### `SymbolSource`
符号源类型别名

### `SymbolType`
符号类型类型别名

### `TableFormatTextFunction`
表格格式化文本函数类型别名

### `TableFormatterInputValue`
表格格式化器输入值类型别名

### `TableFormatterInputValues`
表格格式化器输入值数组类型别名

### `TextInputFieldValidator`
文本输入字段验证器类型别名

### `ThemeName`
主题名称类型别名

### `TickMarkType`
刻度标记类型类型别名

### `TickerId`
代码ID类型别名

### `TimeFrameValue`
时间框架值类型别名

### `TimeScaleMarkShape`
时间刻度标记形状类型别名

### `TimeframeOption`
时间框架选项类型别名

### `Timezone`
时区类型别名

### `TimezoneId`
时区ID类型别名

### `TradableSolutions`
可交易解决方案类型别名

### `TradingDialogCustomField`
交易对话框自定义字段类型别名

### `TradingTerminalChartTypeFavorites`
交易终端图表类型收藏夹类型别名

### `TradingTerminalFeatureset`
交易终端功能集类型别名

### `VisiblePlotsSet`
可见绘图集类型别名

### `WatchListSymbolListAddedCallback`
观察列表符号列表添加回调类型别名

### `WatchListSymbolListChangedCallback`
观察列表符号列表变更回调类型别名

### `WatchListSymbolListRemovedCallback`
观察列表符号列表移除回调类型别名

### `WatchListSymbolListRenamedCallback`
观察列表符号列表重命名回调类型别名

### `WatchedValueCallback<T>`
可观察值回调类型别名

### `WatermarkContentProvider`
水印内容提供者类型别名

### `WidgetOverrides`
构件覆盖类型别名

---

## 函数

### `version()`
返回构建版本字符串

**返回值:** `string` - 构建版本信息，例如 `"CL v23.012 (internal id e0d59dc3 @ 2022-08-23T06:07:00.808Z)"`