# Tushare数据连接器分析文档

## 概述

`ts_connector.py` 是 CZSC 框架中用于从 Tushare 数据源获取K线数据的连接器模块。Tushare 是一个专业的金融数据服务，提供股票、指数、基金、期货等多种资产类型的数据。

## 核心功能

### 1. format_kline - K线数据格式化

**功能**：将 Tushare 返回的 DataFrame 格式K线数据转换为 CZSC 的 RawBar 对象列表

**关键逻辑**：
- 根据频率类型选择时间字段：分钟线使用 `trade_time`，日线/周线/月线使用 `trade_date`
- 日线数据需要特殊处理：成交量乘以100（单位转换），成交额乘以1000
- 分钟线数据直接使用原始值

**输入**：
- `kline: pd.DataFrame` - Tushare 返回的K线数据
- `freq: Freq` - K线周期枚举对象

**输出**：
- `List[RawBar]` - CZSC 标准格式的K线对象列表

### 2. pro_bar_minutes - 分钟线数据获取

**功能**：从 Tushare 获取分钟级K线数据

**关键逻辑**：
- 分批次请求数据（每次40倍周期天数）
- 处理复权因子（前复权/后复权）
- 删除9:30的K线（开盘集合竞价）
- 删除无成交量的K线
- 标准化数据格式

**支持的资产类型**：
- `E` - 股票（Equity）
- `FD` - 基金（Fund）
- 其他资产类型不支持复权

### 3. get_raw_bars - 主要数据获取接口

**功能**：获取指定标的、周期、时间范围的K线数据

**关键特性**：
- 支持分钟线和日线/周线/月线
- 支持前复权、后复权、不复权
- 自动处理频率转换（Freq枚举 ↔ Tushare格式）
- 返回 RawBar 对象列表或 DataFrame

**参数格式**：
- `symbol`: `"ts_code#asset"` 格式，如 `"000001.SH#I"`（指数）
- `freq`: `Freq` 枚举对象或字符串
- `sdt/edt`: 开始/结束时间，格式 `"YYYYMMDD"`
- `fq`: 复权类型，`"前复权"` / `"后复权"` / `"不复权"`

### 4. get_symbols - 获取标的列表

**功能**：根据投研阶段获取标的代码列表

**支持的阶段**：
- `index` - 指数列表
- `stock` - 股票列表
- `check` - 检查用标的
- `train` - 训练集标的
- `valid` - 验证集标的
- `etfs` - ETF列表
- `all` - 所有标的

**返回格式**：`["ts_code#asset", ...]` 格式的列表

### 5. get_sw_members - 申万行业分类

**功能**：获取申万行业分类成分股

**数据来源**：Tushare 申万行业分类接口

### 6. get_daily_basic - 每日指标数据

**功能**：获取全市场A股的每日指标数据

**特点**：按交易日逐日获取，支持错误重试

### 7. moneyflow_hsgt - 沪深港通资金流向

**功能**：获取沪深港通资金流向数据

**数据字段**：`ggt_ss`, `ggt_sz`, `hgt`, `sgt`, `north_money`, `south_money`

## 数据流程

```
Tushare API
    ↓
pro_bar / pro_bar_minutes
    ↓
DataFrame (标准化格式)
    ↓
format_kline
    ↓
List[RawBar]
```

## 频率映射关系

| CZSC Freq | Tushare 格式 | 说明 |
|-----------|-------------|------|
| F1, F5, F15, F30, F60 | 1min, 5min, 15min, 30min, 60min | 分钟线 |
| D | D | 日线 |
| W | W | 周线 |
| M | M | 月线 |

## 资产类型映射

| Asset | 说明 | 示例 |
|-------|------|------|
| E | 股票 | 000001.SZ#E |
| I | 指数 | 000001.SH#I |
| FD | 基金 | 510300.SH#FD |
| O | 期权 | - |
| C | 期货 | - |

## 使用示例

```python
from czsc.connectors.ts_connector import get_raw_bars
from czsc.objects import Freq

# 获取指数日线数据
bars = get_raw_bars(
    symbol="000001.SH#I",
    freq=Freq.D,
    sdt="20200101",
    edt="20231231",
    fq="前复权"
)
```

## 注意事项

1. **Token配置**：首次使用需要设置 Tushare token
2. **数据缓存**：使用 `DataClient` 进行数据缓存，路径通过环境变量 `TS_CACHE_PATH` 配置
3. **频率转换**：需要正确处理 Freq 枚举和 Tushare 格式之间的转换
4. **复权处理**：分钟线支持股票和基金的复权，其他资产类型不支持
5. **数据质量**：自动过滤无效数据（无成交量、9:30集合竞价等）

---

## AKShare 替代方案

### 概述

`ak_connector.py` 是基于 AKShare 实现的相同功能接口，可以作为 Tushare 的免费替代方案。

### 主要区别

| 特性 | Tushare | AKShare |
|------|---------|---------|
| 费用 | 需要 Token（部分功能付费） | 完全免费 |
| 数据源 | 专业数据服务 | 多个公开数据源 |
| 数据延迟 | 实时/准实时 | 有一定延迟 |
| 接口稳定性 | 高 | 中等 |
| 支持资产 | 股票、指数、基金、期货、期权等 | 主要支持股票、指数、ETF |

### 使用示例

```python
from czsc.connectors.ak_connector import get_raw_bars
from czsc.objects import Freq

# 获取股票日线数据（与 ts_connector 接口完全一致）
bars = get_raw_bars(
    symbol="000001.SZ#E",  # 或 "000001.SZ"
    freq=Freq.D,
    sdt="20200101",
    edt="20231231",
    fq="前复权"
)
```

### 功能对比

| 功能 | ts_connector | ak_connector | 说明 |
|------|--------------|--------------|------|
| `get_raw_bars` | ✅ | ✅ | 完全兼容 |
| `get_symbols` | ✅ | ✅ | 完全兼容 |
| `format_kline` | ✅ | ✅ | 完全兼容 |
| `get_sw_members` | ✅ | ⚠️ | 部分支持 |
| `get_daily_basic` | ✅ | ⚠️ | 简化实现 |
| `moneyflow_hsgt` | ✅ | ⚠️ | 简化实现 |
| `pro_bar_minutes` | ✅ | ✅ | 通过 `get_raw_bars` 支持 |

### 代码格式转换

AKShare 使用不同的代码格式，`ak_connector.py` 会自动处理转换：

- **输入格式**（与 ts_connector 一致）：
  - 股票：`"000001.SZ"` 或 `"000001.SZ#E"`
  - 指数：`"000001.SH#I"`
  - ETF：`"510300.SH#FD"`

- **内部转换**：
  - 股票：`"000001"`（6位数字）
  - 指数：`"sh000001"` 或 `"sz399001"`
  - ETF：`"sh510300"` 或 `"sz159915"`

### 注意事项

1. **安装依赖**：`pip install akshare`
2. **数据延迟**：AKShare 数据可能有几分钟到几小时的延迟
3. **接口变化**：AKShare 接口可能随版本更新而变化，需要及时更新代码
4. **频率支持**：周线/月线通过日线重采样实现
5. **复权支持**：股票支持前复权/后复权，指数和ETF不支持复权

### 迁移建议

如果需要从 `ts_connector` 迁移到 `ak_connector`：

1. **安装 AKShare**：`pip install akshare`
2. **替换导入**：将 `from czsc.connectors.ts_connector import get_raw_bars` 改为 `from czsc.connectors.ak_connector import get_raw_bars`
3. **代码格式**：保持相同的调用方式，无需修改业务代码
4. **测试验证**：对比两种数据源的结果，确保数据一致性
