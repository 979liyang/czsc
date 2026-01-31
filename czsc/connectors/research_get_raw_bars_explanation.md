# research.py get_raw_bars 函数逐行解释

## 函数概述

`get_raw_bars` 函数用于从本地 Parquet 文件读取K线数据，并根据指定的周期进行重采样，最终返回 CZSC 标准的 `RawBar` 对象列表。

## 逐行代码解释

### 第 49 行：函数定义
```python
def get_raw_bars(symbol, freq, sdt, edt, fq="前复权", **kwargs):
```

**作用**：定义函数签名
- `symbol`: 标的代码，如 `"000001.SH"`、`"SFIC9001"` 等
- `freq`: K线周期，可以是 `Freq` 枚举对象或字符串（如 `"日线"`、`"5分钟"`）
- `sdt`: 开始时间，格式如 `"20200101"` 或 `"2020-01-01"`
- `edt`: 结束时间，格式同 `sdt`
- `fq`: 复权类型，默认 `"前复权"`（但投研数据已复权，此参数实际不使用）
- `**kwargs`: 其他可选参数，如 `raw_bars=True` 控制返回类型

---

### 第 61 行：获取返回类型参数
```python
raw_bars = kwargs.get("raw_bars", True)
```

**作用**：从 `kwargs` 中获取 `raw_bars` 参数，默认为 `True`
- `True`: 返回 `RawBar` 对象列表
- `False`: 返回 `DataFrame`

**说明**：这个参数控制最终返回的数据格式

---

### 第 62 行：保存复权参数
```python
kwargs["fq"] = fq
```

**作用**：将复权类型参数保存到 `kwargs` 字典中
- 虽然投研数据已经复权处理，但保留此参数以保持接口一致性

---

### 第 63 行：查找 Parquet 文件
```python
file = list(Path(cache_path).rglob(f"{symbol}.parquet"))[0]
```

**作用**：在缓存目录中递归查找匹配标的代码的 Parquet 文件

**详细说明**：
- `Path(cache_path)`: 将缓存路径转换为 `Path` 对象
- `.rglob(f"{symbol}.parquet")`: 递归搜索所有匹配 `{symbol}.parquet` 的文件
  - 例如：`symbol="000001.SH"` 会搜索 `**/000001.SH.parquet`
- `list(...)[0]`: 取第一个匹配的文件
  - **注意**：如果找不到文件，这里会抛出 `IndexError`

**文件路径示例**：
```
.cache/CZSC投研数据/A股主要指数/000001.SH.parquet
.cache/CZSC投研数据/期货主力/SFIC9001.parquet
```

---

### 第 64 行：转换频率为 Freq 枚举
```python
freq = czsc.Freq(freq)
```

**作用**：将频率参数转换为 `Freq` 枚举对象

**说明**：
- 如果 `freq` 已经是 `Freq` 对象，则保持不变
- 如果是字符串（如 `"日线"`、`"5分钟"`），则转换为对应的 `Freq` 枚举
- 例如：`"日线"` → `Freq.D`，`"5分钟"` → `Freq.F5`

---

### 第 65 行：读取 Parquet 文件
```python
kline = pd.read_parquet(file)
```

**作用**：使用 pandas 读取 Parquet 文件，返回 DataFrame

**返回的 DataFrame 列**：
- `symbol`: 标的代码
- `dt` 或 `datetime`: 时间戳
- `open`, `close`, `high`, `low`: OHLC 价格
- `vol`: 成交量
- `amount`: 成交额

---

### 第 66-67 行：处理时间列
```python
if "dt" not in kline.columns:
    kline["dt"] = pd.to_datetime(kline["datetime"])
```

**作用**：确保 DataFrame 中有 `dt` 列（时间列）

**逻辑**：
- 如果存在 `dt` 列，跳过
- 如果不存在 `dt` 但存在 `datetime` 列，将 `datetime` 转换为 `dt`
- `pd.to_datetime()`: 将字符串或时间对象转换为 pandas 的 datetime 类型

**为什么需要**：不同数据源可能使用不同的时间列名，统一为 `dt` 便于后续处理

---

### 第 68 行：时间范围过滤
```python
kline = kline[(kline["dt"] >= pd.to_datetime(sdt)) & (kline["dt"] <= pd.to_datetime(edt))]
```

**作用**：根据开始时间和结束时间过滤数据

**详细说明**：
- `pd.to_datetime(sdt)`: 将开始时间字符串转换为 datetime 对象
- `pd.to_datetime(edt)`: 将结束时间字符串转换为 datetime 对象
- `(kline["dt"] >= ...) & (kline["dt"] <= ...)`: 布尔索引，筛选在时间范围内的数据
- 结果：只保留 `sdt <= dt <= edt` 的K线数据

**示例**：
```python
# 如果 sdt="20200101", edt="20201231"
# 只保留 2020-01-01 到 2020-12-31 之间的数据
```

---

### 第 69-70 行：检查数据是否为空
```python
if kline.empty:
    return []
```

**作用**：如果过滤后数据为空，直接返回空列表

**说明**：
- `kline.empty`: pandas DataFrame 的属性，判断是否为空
- 如果为空，说明指定时间范围内没有数据，返回空列表避免后续处理出错

---

### 第 72 行：复制 DataFrame
```python
df = kline.copy()
```

**作用**：创建 DataFrame 的副本，避免修改原始数据

**为什么需要**：后续可能对 `df` 进行修改（如过滤股指数据），使用副本可以保护原始数据

---

### 第 73 行：检查是否为股指期货
```python
if symbol in ["SFIC9001", "SFIF9001", "SFIH9001"]:
```

**作用**：判断是否为特定的股指期货标的

**说明**：
- `SFIC9001`: 中证500股指期货
- `SFIF9001`: 沪深300股指期货
- `SFIH9001`: 上证50股指期货

**为什么特殊处理**：股指期货的交易时间与股票不同，需要过滤掉非交易时段的数据

---

### 第 76-77 行：定义上午交易时段
```python
dt1 = datetime.strptime("09:31:00", "%H:%M:%S")
dt2 = datetime.strptime("11:30:00", "%H:%M:%S")
```

**作用**：定义上午交易时段的开始和结束时间

**说明**：
- `datetime.strptime()`: 将时间字符串解析为 datetime 对象
- `"09:31:00"`: 上午开盘时间（9:30 是集合竞价，9:31 开始连续竞价）
- `"11:30:00"`: 上午收盘时间

---

### 第 78 行：创建上午时段过滤条件
```python
c1 = (df["dt"].dt.time >= dt1.time()) & (df["dt"].dt.time <= dt2.time())
```

**作用**：创建布尔条件，筛选出上午交易时段的数据

**详细说明**：
- `df["dt"].dt.time`: 提取时间列中的时间部分（去掉日期）
- `dt1.time()`: 获取 datetime 对象的时间部分
- `>= dt1.time()`: 时间大于等于 09:31:00
- `<= dt2.time()`: 时间小于等于 11:30:00
- `c1`: 布尔 Series，True 表示该行在上午交易时段

**示例**：
```python
# 如果 dt = "2020-01-01 10:30:00"
# df["dt"].dt.time = "10:30:00"
# "10:30:00" >= "09:31:00" and "10:30:00" <= "11:30:00" → True
```

---

### 第 80-81 行：定义下午交易时段
```python
dt3 = datetime.strptime("13:01:00", "%H:%M:%S")
dt4 = datetime.strptime("15:00:00", "%H:%M:%S")
```

**作用**：定义下午交易时段的开始和结束时间

**说明**：
- `"13:01:00"`: 下午开盘时间（13:00 是集合竞价，13:01 开始连续竞价）
- `"15:00:00"`: 下午收盘时间

---

### 第 82 行：创建下午时段过滤条件
```python
c2 = (df["dt"].dt.time >= dt3.time()) & (df["dt"].dt.time <= dt4.time())
```

**作用**：创建布尔条件，筛选出下午交易时段的数据

**逻辑同第 78 行**，只是时间范围不同

---

### 第 84 行：合并两个时段并过滤
```python
df = df[c1 | c2].copy().reset_index(drop=True)
```

**作用**：保留上午或下午交易时段的数据，过滤掉其他时间的数据

**详细说明**：
- `c1 | c2`: 逻辑或运算，True 表示在上午或下午交易时段
- `df[c1 | c2]`: 布尔索引，只保留交易时段的数据
- `.copy()`: 创建副本（虽然已经复制过，但这里再次确保）
- `.reset_index(drop=True)`: 重置索引，从 0 开始连续编号

**过滤效果**：
- ✅ 保留：09:31-11:30 和 13:01-15:00 的数据
- ❌ 过滤：09:30（集合竞价）、11:30-13:01（午休）、15:00 之后的数据

**为什么需要**：
- 注释说明：历史遗留问题，股指期货有一段时间收盘时间是 15:15
- 为了数据一致性，统一过滤到 15:00

---

### 第 86 行：重采样K线数据
```python
_bars = czsc.resample_bars(df, freq, raw_bars=raw_bars, base_freq="1分钟")
```

**作用**：将 DataFrame 重采样为目标周期，并转换为 RawBar 对象列表

**参数说明**：
- `df`: 输入 DataFrame（包含 symbol, dt, open, close, high, low, vol, amount 列）
- `freq`: 目标周期（Freq 枚举对象，如 `Freq.D` 表示日线）
- `raw_bars`: 是否返回 RawBar 对象（True）还是 DataFrame（False）
- `base_freq="1分钟"`: 基础周期，表示原始数据是 1 分钟K线

**重采样逻辑**（`resample_bars` 函数内部）：
1. 根据目标周期计算每个数据点所属的周期结束时间
2. 按周期结束时间分组
3. 每组内聚合：
   - `open`: 取第一个（周期开始时的开盘价）
   - `close`: 取最后一个（周期结束时的收盘价）
   - `high`: 取最大值（周期内的最高价）
   - `low`: 取最小值（周期内的最低价）
   - `vol`: 求和（周期内的总成交量）
   - `amount`: 求和（周期内的总成交额）
4. 如果 `raw_bars=True`，转换为 `RawBar` 对象列表

**示例**：
```python
# 输入：1分钟K线数据（240 根，4小时交易时间）
# 目标：日线
# 输出：1 根日线K线
# - open: 第一根1分钟K线的开盘价
# - close: 最后一根1分钟K线的收盘价
# - high: 240根1分钟K线中的最高价
# - low: 240根1分钟K线中的最低价
# - vol: 240根1分钟K线的成交量之和
# - amount: 240根1分钟K线的成交额之和
```

---

### 第 87 行：返回结果
```python
return _bars
```

**作用**：返回处理后的 RawBar 对象列表或 DataFrame

**返回类型**：
- 如果 `raw_bars=True`：`List[RawBar]`
- 如果 `raw_bars=False`：`pd.DataFrame`

---

## 完整数据流程

```
本地 Parquet 文件
    ↓ (第 65 行：读取)
DataFrame (原始1分钟K线)
    ↓ (第 66-67 行：统一时间列)
DataFrame (有 dt 列)
    ↓ (第 68 行：时间范围过滤)
DataFrame (指定时间范围内的数据)
    ↓ (第 73-84 行：股指期货特殊处理)
DataFrame (过滤非交易时段，仅股指期货)
    ↓ (第 86 行：重采样)
List[RawBar] (目标周期的K线数据)
    ↓ (第 87 行：返回)
返回给调用者
```

## 关键要点总结

1. **数据源**：从本地 Parquet 文件读取，路径由环境变量 `czsc_research_cache` 指定
2. **基础数据**：假设所有 Parquet 文件存储的是 1 分钟K线数据
3. **重采样**：通过 `resample_bars` 函数将 1 分钟K线转换为目标周期
4. **特殊处理**：股指期货需要过滤非交易时段的数据
5. **时间过滤**：支持按时间范围筛选数据
6. **返回格式**：默认返回 `RawBar` 对象列表，可通过参数返回 DataFrame

## 使用示例

```python
from czsc.connectors.research import get_raw_bars
from czsc.objects import Freq

# 获取上证指数日线数据
bars = get_raw_bars(
    symbol="000001.SH",
    freq=Freq.D,  # 或 "日线"
    sdt="20200101",
    edt="20201231"
)

# 获取股指期货5分钟K线
bars = get_raw_bars(
    symbol="SFIC9001",
    freq="5分钟",
    sdt="20200101",
    edt="20201231"
)
```
