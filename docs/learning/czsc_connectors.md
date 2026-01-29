# CZSC数据连接器学习文档

## 概述

本文档记录czsc.connectors模块中各种数据源的接口和使用方法。

## 数据连接器分类

### 1. research（投研数据）

**定义位置**: `czsc.connectors.research`

**用途**: 从本地Parquet文件读取投研共享数据

**关键函数**:
- `get_symbols(name)` - 获取指定分组下的所有标的代码
- `get_raw_bars(symbol, freq, sdt, edt, fq, **kwargs)` - 获取RawBar对象列表

**数据路径**:
- 通过环境变量`czsc_research_cache`设置
- 默认路径：`D:\CZSC投研数据`

**数据组织方式**:
```
{cache_path}/
├── {group}/
│   └── {symbol}.parquet
```

**使用示例**:
```python
from czsc.connectors.research import get_raw_bars, get_symbols

# 获取标的列表
symbols = get_symbols("A股主要指数")

# 获取K线数据
bars = get_raw_bars(
    symbol="000001.SH",
    freq="日线",
    sdt="20230101",
    edt="20231231"
)
```

### 2. ts_connector（Tushare数据）

**定义位置**: `czsc.connectors.ts_connector`

**用途**: 从Tushare API获取数据

**关键函数**:
- `get_raw_bars(symbol, freq, sdt, edt, **kwargs)` - 获取RawBar对象列表

**使用示例**:
```python
from czsc.connectors.ts_connector import get_raw_bars

bars = get_raw_bars(
    symbol="000001.SH",
    freq="日线",
    sdt="20230101",
    edt="20231231"
)
```

### 3. gm_connector（掘金数据）

**定义位置**: `czsc.connectors.gm_connector`

**用途**: 从掘金量化平台获取数据

### 4. jq_connector（聚宽数据）

**定义位置**: `czsc.connectors.jq_connector`

**用途**: 从聚宽平台获取数据

### 5. qmt_connector（QMT数据）

**定义位置**: `czsc.connectors.qmt_connector`

**用途**: 从QMT平台获取数据

### 6. tq_connector（天勤数据）

**定义位置**: `czsc.connectors.tq_connector`

**用途**: 从天勤平台获取数据

## 通用接口规范

所有数据连接器都遵循以下接口规范：

### get_raw_bars函数

```python
def get_raw_bars(
    symbol: str,
    freq: Union[Freq, str],
    sdt: Union[str, datetime],
    edt: Union[str, datetime],
    fq: str = "前复权",
    **kwargs
) -> List[RawBar]:
    """
    获取RawBar对象列表
    
    :param symbol: 标的代码
    :param freq: K线周期
    :param sdt: 开始时间
    :param edt: 结束时间
    :param fq: 除权类型
    :param kwargs: 其他参数
    :return: RawBar对象列表
    """
```

### get_symbols函数

```python
def get_symbols(name: str, **kwargs) -> List[str]:
    """
    获取标的代码列表
    
    :param name: 分组名称或"ALL"
    :param kwargs: 其他参数
    :return: 标的代码列表
    """
```

## 数据格式要求

### Parquet文件格式

所有连接器读取的Parquet文件应包含以下列：

- `symbol: str` - 标的代码
- `dt: datetime` - 时间戳（或`datetime`列）
- `open: float` - 开盘价
- `close: float` - 收盘价
- `high: float` - 最高价
- `low: float` - 最低价
- `vol: float` - 成交量
- `amount: float` - 成交额

### 数据转换

连接器内部使用`czsc.resample_bars`函数进行周期转换：

```python
from czsc.utils.bar_generator import resample_bars

# 读取Parquet文件
kline = pd.read_parquet(file)

# 转换为目标周期
_bars = resample_bars(kline, freq, raw_bars=True, base_freq="1分钟")
```

## 数据存储建议

### 本地数据存储

推荐使用research连接器的数据组织方式：

```
data/
├── klines/
│   ├── {symbol}/
│   │   ├── {freq}/
│   │   │   └── data.parquet
│   │   └── metadata.json
│   └── index.json
```

### 数据更新策略

1. **增量更新**: 只更新新增的K线数据
2. **时间范围过滤**: 更新时只更新指定时间范围
3. **数据去重**: 相同dt的K线，保留最新的
4. **索引维护**: 更新metadata.json和index.json

## 使用建议

1. **优先使用research连接器**: 本地数据读取速度快
2. **数据缓存**: 从外部API获取的数据应缓存到本地
3. **数据验证**: 读取数据后应验证数据完整性
4. **错误处理**: 处理数据源不可用的情况
