# CZSC核心对象结构学习文档

## 概述

本文档记录czsc库中核心数据对象的定义、用途和关键属性。

## 核心对象

### 1. RawBar（原始K线）

**定义位置**: `czsc.objects.RawBar`

**用途**: 存储原始K线数据，是缠论分析的基础数据单元

**关键属性**:
- `symbol: str` - 标的代码
- `id: int` - K线ID，必须是升序
- `dt: datetime` - 时间戳
- `freq: Freq` - K线周期（枚举类型）
- `open: float` - 开盘价
- `close: float` - 收盘价
- `high: float` - 最高价
- `low: float` - 最低价
- `vol: float` - 成交量
- `amount: float` - 成交额
- `cache: dict` - 用户缓存，常用于缓存技术指标计算结果

**计算属性**:
- `upper` - 上影线长度
- `lower` - 下影线长度
- `solid` - 实体长度

**数据格式要求**:
- `id`必须升序排列
- 所有价格和成交量字段必须为浮点数
- `cache`字段为可选，默认为空字典

### 2. NewBar（去除包含关系后的K线）

**定义位置**: `czsc.objects.NewBar`

**用途**: 存储去除包含关系后的K线数据，用于分型和笔的识别

**关键属性**:
- 与RawBar相同的价格和成交量字段
- `elements: List` - 存入具有包含关系的原始K线列表
- `cache: dict` - 用户缓存

**计算属性**:
- `raw_bars` - 返回构成该NewBar的所有RawBar列表

### 3. FX（分型）

**定义位置**: `czsc.objects.FX`

**用途**: 表示顶分型或底分型，是笔识别的基础

**关键属性**:
- `symbol: str` - 标的代码
- `dt: datetime` - 分型时间
- `mark: Mark` - 分型标记（Mark.D=底分型, Mark.G=顶分型）
- `high: float` - 最高价
- `low: float` - 最低价
- `fx: float` - 分型价格（顶分型为high，底分型为low）
- `elements: List[NewBar]` - 构成分型的无包含关系K线（通常为3根）
- `cache: dict` - 用户缓存

**计算属性**:
- `new_bars` - 构成分型的无包含关系K线
- `raw_bars` - 构成分型的原始K线
- `power_str` - 分型力度强度描述（"强"、"中"、"弱"）
- `power_volume` - 成交量力度
- `has_zs` - 构成分型的三根K线是否有重叠中枢

**分型识别规则**:
- 顶分型：中间K线的高点最高，且左右K线高点都低于中间K线
- 底分型：中间K线低点最低，且左右K线低点都高于中间K线

### 4. BI（笔）

**定义位置**: `czsc.objects.BI`

**用途**: 表示缠论中的"笔"，由两个相邻的顶底分型构成

**关键属性**:
- `symbol: str` - 标的代码
- `fx_a: FX` - 笔开始的分型
- `fx_b: FX` - 笔结束的分型
- `fxs: List[FX]` - 笔内部的分型列表
- `direction: Direction` - 笔的方向（Direction.Up=向上, Direction.Down=向下）
- `bars: List[NewBar]` - 构成笔的K线列表
- `cache: dict` - 用户缓存

**计算属性**:
- `sdt` - 笔开始时间（fx_a.dt）
- `edt` - 笔结束时间（fx_b.dt）
- `high` - 笔的最高价
- `low` - 笔的最低价
- `power` - 笔的力度（价格变化幅度）

**成笔条件**:
1. 顶底分型之间没有包含关系
2. 笔长度（K线数量）大于等于最小笔长度（min_bi_len）

### 5. ZS（中枢）

**定义位置**: `czsc.objects.ZS`

**用途**: 表示缠论中的"中枢"，由至少3笔构成，且笔之间有重叠

**关键属性**:
- `bis: List[BI]` - 构成中枢的笔列表（至少3笔）
- `cache: dict` - 用户缓存

**计算属性**:
- `symbol` - 标的代码（从第一笔获取）
- `sdt` - 中枢开始时间
- `edt` - 中枢结束时间
- `sdir` - 中枢第一笔方向
- `edir` - 中枢最后一笔方向
- `zg` - 中枢上沿（前3笔的最高价的最小值）
- `zd` - 中枢下沿（前3笔的最低价的最大值）
- `gg` - 中枢最高点（所有笔的最高价）
- `dd` - 中枢最低点（所有笔的最低价）
- `zz` - 中枢中轴（(zg + zd) / 2）
- `is_valid` - 中枢是否有效

**中枢有效性判断**:
1. zg >= zd（上沿必须大于等于下沿）
2. 中枢内的笔必须与中枢的上下沿有交集

### 6. Signal（信号）

**定义位置**: `czsc.objects.Signal`

**用途**: 表示技术分析信号，用于策略构建

**关键属性**:
- `signal: str` - 信号字符串，格式：`{k1}_{k2}_{k3}_{v1}_{v2}_{v3}_{score}`
- `score: int` - 信号得分（0~100），得分越高信号越强
- `k1: str` - 信号名称第一部分（一般指明K线周期）
- `k2: str` - 信号名称第二部分（一般记录信号计算参数）
- `k3: str` - 信号名称第三部分（用于区分信号，必须唯一）
- `v1, v2, v3: str` - 信号取值

**信号匹配规则**:
- 使用`is_match`方法判断信号是否匹配
- 匹配条件：score >= 目标score，且v1/v2/v3匹配或为"任意"

### 7. Factor（因子）

**定义位置**: `czsc.objects.Factor`

**用途**: 组合多个信号形成交易因子

**关键属性**:
- `signals_all: List[Signal]` - 必须全部满足的信号（至少一个）
- `signals_any: List[Signal]` - 满足其中任一信号（可选）
- `signals_not: List[Signal]` - 不能满足其中任一信号（可选）
- `name: str` - 因子名称

### 8. Event（事件）

**定义位置**: `czsc.objects.Event`

**用途**: 表示交易事件（开多、平多、开空、平空等）

**关键属性**:
- `operate: Operate` - 操作类型（开多、平多、开空、平空等）
- `signals_all: List[Signal]` - 必须全部满足的信号
- `signals_any: List[Signal]` - 满足其中任一信号
- `signals_not: List[Signal]` - 不能满足其中任一信号
- `factors: List[Factor]` - 因子列表

### 9. Position（持仓）

**定义位置**: `czsc.objects.Position`

**用途**: 表示策略持仓配置

**关键属性**:
- `name: str` - 持仓名称
- `symbol: str` - 标的代码
- `opens: List[Event]` - 开仓事件列表
- `exits: List[Event]` - 平仓事件列表
- `interval: int` - 操作间隔（秒）
- `timeout: int` - 超时时间（秒）
- `stop_loss: float` - 止损价格
- `T0: bool` - 是否T+0交易

## 枚举类型

### Mark（分型标记）
- `Mark.D` - 底分型
- `Mark.G` - 顶分型

### Direction（方向）
- `Direction.Up` - 向上
- `Direction.Down` - 向下

### Freq（周期）
- `Freq.Tick` - Tick级别
- `Freq.F1` - 1分钟
- `Freq.F5` - 5分钟
- `Freq.F15` - 15分钟
- `Freq.F30` - 30分钟
- `Freq.F60` - 60分钟
- `Freq.D` - 日线
- `Freq.W` - 周线
- `Freq.M` - 月线
- `Freq.S` - 季线
- `Freq.Y` - 年线

### Operate（操作）
- `Operate.LO` - 开多
- `Operate.LE` - 平多
- `Operate.SO` - 开空
- `Operate.SE` - 平空
- `Operate.HL` - 持多
- `Operate.HS` - 持空
- `Operate.HO` - 持币

## 数据流转关系

```
RawBar → NewBar → FX → BI → ZS
         ↓
      Signal → Factor → Event → Position
```

## 关键设计要点

1. **数据不可变性**: 所有对象使用dataclass定义，建议使用不可变对象
2. **缓存机制**: 所有对象都有`cache`字段，用于缓存计算结果
3. **时间序列**: 所有对象都包含时间信息（dt、sdt、edt）
4. **符号一致性**: 所有对象都包含`symbol`字段，确保数据一致性
5. **分层设计**: 从RawBar到ZS，数据逐步抽象和聚合

## 使用建议

1. **数据存储**: 使用Parquet格式存储RawBar数据，按symbol/freq组织
2. **数据转换**: 使用`format_standard_kline`函数将DataFrame转换为RawBar列表
3. **对象序列化**: 需要将对象转换为字典格式用于JSON传输
4. **缓存利用**: 充分利用`cache`字段缓存技术指标计算结果，避免重复计算
