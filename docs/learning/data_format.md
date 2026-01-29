# CZSC数据格式要求学习文档

## 概述

本文档总结czsc库对数据格式的要求，特别是RawBar的必需字段和格式规范，为数据存储方案设计提供依据。

## RawBar数据格式规范

### 必需字段

RawBar对象必须包含以下字段：

1. **symbol: str** - 标的代码
   - 格式：如 "000001.SH", "000001.SZ"
   - 必须唯一标识一个交易标的

2. **id: int** - K线ID
   - 必须是升序排列
   - 从1开始递增
   - 同一symbol、同一freq的K线，id必须连续且递增

3. **dt: datetime** - 时间戳
   - Python datetime对象
   - 必须按时间顺序排列
   - 同一symbol、同一freq的K线，dt必须递增

4. **freq: Freq** - K线周期
   - 枚举类型：Freq.Tick, Freq.F1, F5, F15, F30, F60, D, W, M, S, Y
   - 或字符串："1分钟", "5分钟", "日线"等

5. **open: float** - 开盘价
   - 必须 >= 0
   - 精度建议保留2-4位小数

6. **close: float** - 收盘价
   - 必须 >= 0
   - 精度建议保留2-4位小数

7. **high: float** - 最高价
   - 必须 >= max(open, close)
   - 精度建议保留2-4位小数

8. **low: float** - 最低价
   - 必须 <= min(open, close)
   - 精度建议保留2-4位小数

9. **vol: float** - 成交量
   - 必须 >= 0
   - 单位：股（股票）或手（期货）

10. **amount: float** - 成交额
    - 必须 >= 0
    - 单位：元

11. **cache: dict** - 用户缓存（可选）
    - 默认为空字典 {}
    - 用于缓存技术指标计算结果
    - 序列化时需要特殊处理

### 数据完整性要求

1. **时间序列连续性**
   - 同一symbol、同一freq的K线，dt必须按时间顺序排列
   - 不允许有重复的dt
   - 允许有缺失的K线（非交易日等）

2. **价格逻辑一致性**
   - high >= max(open, close)
   - low <= min(open, close)
   - high >= low

3. **ID连续性**
   - 同一symbol、同一freq的K线，id必须连续递增
   - 不允许有重复的id
   - 不允许有缺失的id

## 数据存储格式

### Parquet文件格式

czsc使用Parquet格式存储K线数据，具有以下优势：

1. **列式存储**：压缩率高，查询速度快
2. **类型支持**：支持datetime、float等复杂类型
3. **兼容性**：可直接用pandas读取

### Parquet文件结构

**列名要求**：
- symbol: str
- dt: datetime (或datetime64[ns])
- open: float64
- close: float64
- high: float64
- low: float64
- vol: float64
- amount: float64
- id: int64 (可选，可以从索引生成)

**时间列处理**：
- 如果Parquet文件中没有dt列，可以使用datetime列
- 读取时需要转换为datetime类型：`kline["dt"] = pd.to_datetime(kline["datetime"])`

### 数据组织方式

根据czsc.connectors.research模块的实现，推荐的数据组织方式：

```
data/
├── klines/
│   ├── {symbol}/
│   │   ├── {freq}/
│   │   │   └── data.parquet
│   │   └── metadata.json
│   └── index.json
```

**说明**：
- 按symbol组织目录
- 按freq组织子目录
- 每个symbol/freq组合对应一个Parquet文件
- metadata.json记录该symbol的数据元信息（时间范围、数据量等）
- index.json记录全局索引（所有symbol列表、数据更新时间等）

## 数据转换

### DataFrame → RawBar

使用`czsc.utils.bar_generator.format_standard_kline`函数：

```python
from czsc.utils.bar_generator import format_standard_kline
from czsc.objects import Freq

# df必须包含列：symbol, dt, open, close, high, low, vol, amount
bars = format_standard_kline(df, freq="日线")
```

### Parquet → RawBar

使用`czsc.connectors.research.get_raw_bars`函数：

```python
from czsc.connectors.research import get_raw_bars
from czsc.objects import Freq

bars = get_raw_bars(
    symbol="000001.SH",
    freq=Freq.D,  # 或 "日线"
    sdt="20230101",
    edt="20231231"
)
```

### RawBar → DataFrame

```python
import pandas as pd

def bars_to_df(bars):
    """将RawBar列表转换为DataFrame"""
    data = []
    for bar in bars:
        data.append({
            'symbol': bar.symbol,
            'id': bar.id,
            'dt': bar.dt,
            'freq': bar.freq.value,
            'open': bar.open,
            'close': bar.close,
            'high': bar.high,
            'low': bar.low,
            'vol': bar.vol,
            'amount': bar.amount,
        })
    return pd.DataFrame(data)
```

## 数据质量检查

### 1. 时间序列检查

```python
def check_time_sequence(bars):
    """检查时间序列是否连续"""
    dts = [bar.dt for bar in bars]
    assert dts == sorted(dts), "时间序列不连续"
    assert len(dts) == len(set(dts)), "存在重复时间"
```

### 2. ID连续性检查

```python
def check_id_continuity(bars):
    """检查ID是否连续"""
    ids = [bar.id for bar in bars]
    assert ids == list(range(1, len(ids) + 1)), "ID不连续"
```

### 3. 价格逻辑检查

```python
def check_price_logic(bar):
    """检查价格逻辑是否正确"""
    assert bar.high >= max(bar.open, bar.close), "最高价逻辑错误"
    assert bar.low <= min(bar.open, bar.close), "最低价逻辑错误"
    assert bar.high >= bar.low, "最高价必须大于等于最低价"
```

## 数据更新策略

### 增量更新

1. **读取现有数据**：从Parquet文件读取现有K线数据
2. **获取新数据**：从数据源获取新的K线数据
3. **合并数据**：按dt去重，保留最新的数据
4. **重新排序**：按dt排序，重新分配id
5. **保存数据**：保存到Parquet文件

### 注意事项

1. **时间范围过滤**：更新时只更新指定时间范围的数据
2. **数据去重**：相同dt的K线，保留最新的
3. **ID重新分配**：合并后需要重新分配id，确保连续性
4. **索引更新**：更新metadata.json和index.json

## 数据存储建议

1. **使用Parquet格式**：压缩率高，查询速度快
2. **按symbol/freq组织**：便于快速定位和查询
3. **维护索引文件**：记录数据元信息，加快查询速度
4. **支持增量更新**：避免全量更新，提高效率
5. **数据验证**：存储前进行数据质量检查

## 与信号函数的兼容性

所有czsc信号函数都基于RawBar数据格式，因此：

1. **数据格式必须严格符合RawBar规范**
2. **时间序列必须连续且有序**
3. **价格字段必须符合逻辑关系**
4. **freq字段必须正确设置**

只有满足以上要求，信号函数才能正确计算。
