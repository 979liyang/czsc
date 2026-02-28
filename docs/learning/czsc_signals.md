# CZSC信号函数学习文档

## 概述

本文档记录czsc.signals模块中所有信号函数的分类、签名、参数和返回值格式。

**延伸阅读**：因子与策略在 CZSC 及本项目中的对应关系见 [czsc_factors_and_strategies.md](./czsc_factors_and_strategies.md)。

## 信号函数分类

根据czsc.signals.__init__.py，信号函数按功能分为以下类别：

### 1. cxt（缠论类）
- 分型相关：`cxt_fx_power_V221107`
- 笔相关：`cxt_bi_status_V230101`, `cxt_bi_end_V230222`, `cxt_bi_base_V230228`
- 买卖点：`cxt_first_buy_V221126`, `cxt_first_sell_V221126`, `cxt_third_buy_V230228`
- 中枢相关：`cxt_zhong_shu_gong_zhen_V221221`, `cxt_double_zs_V230311`

### 2. tas（技术指标类）
- 均线：`tas_ma_base_V221101`, `tas_double_ma_V221203`
- MACD：`tas_macd_base_V221203`
- 其他技术指标

### 3. bar（K线形态类）
- K线形态识别相关函数

### 4. vol（成交量类）
- 成交量相关分析函数

### 5. stock（股票特定类）
- 股票市场特定信号函数

### 6. pos（持仓状态类）
- 持仓状态相关函数

### 7. ang（角度类）
- 笔的角度分析函数

### 8. jcc（基础类）
- 基础信号函数

### 9. coo（其他类）
- 其他辅助信号函数

### 10. byi（笔相关）
- 笔的特定分析函数

### 11. xls（选股类）
- 选股相关函数

## 信号函数通用格式

### 函数签名

所有信号函数遵循以下格式：

```python
def signal_name(cat: CzscSignals, **kwargs) -> dict:
    """
    信号函数说明
    
    :param cat: CzscSignals对象或CZSC对象
    :param kwargs: 信号函数参数
    :return: 信号字典，格式：{signal_name: signal_value}
    """
```

### 参数说明

1. **cat参数**:
   - 类型：`CzscSignals` 或 `CZSC`
   - 如果指定了`freq`参数，使用`CZSC`对象
   - 否则使用`CzscSignals`对象

2. **kwargs参数**:
   - `freq: str` - K线周期（可选）
   - `di: int` - 信号计算偏移量（可选，默认1）
   - 其他信号函数特定参数

### 返回值格式

信号函数返回字典，格式：

```python
{
    "信号名称": "信号值"
}
```

信号名称格式：`{freq}_{k2}_{k3}_{v1}_{v2}_{v3}_{score}`

示例：
```python
{
    "日线_D1_三买辅助V230228_三买_任意_任意_0": "三买",
    "30分钟_D1B_SELL1_一卖_任意_任意_0": "一卖"
}
```

## 信号函数调用方式

### 方式1：通过signals_config配置

```python
signals_config = [
    {
        'name': 'czsc.signals.cxt_bi_status_V230101',
        'freq': '日线',
        'di': 1
    },
    {
        'name': 'czsc.signals.tas_ma_base_V221101',
        'freq': '30分钟',
        'di': 1,
        'ma_type': 'SMA',
        'timeperiod': 5
    }
]

cs = CzscSignals(bg=bg, signals_config=signals_config)
signals = dict(cs.s)
```

### 方式2：直接调用

```python
from czsc.signals import cxt_bi_status_V230101

# 使用CZSC对象
ka = CZSC(bars)
signals = cxt_bi_status_V230101(ka, di=1)

# 使用CzscSignals对象
cs = CzscSignals(bg=bg)
signals = cxt_bi_status_V230101(cs, freq='日线', di=1)
```

## 信号函数文档生成

可以通过以下方式自动提取信号函数信息：

```python
import inspect
from czsc.signals import *

def get_signal_info(signal_func):
    """提取信号函数信息"""
    doc = inspect.getdoc(signal_func)
    sig = inspect.signature(signal_func)
    params = {}
    for name, param in sig.parameters.items():
        if name != 'cat':
            params[name] = {
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'annotation': str(param.annotation) if param.annotation != inspect.Parameter.empty else None
            }
    return {
        'name': signal_func.__name__,
        'doc': doc,
        'params': params
    }
```

## 常用信号函数示例

### 1. cxt_bi_status_V230101（笔状态）

**功能**: 判断笔的状态（向上、向下、未完成）

**参数**:
- `cat`: CZSC对象或CzscSignals对象
- `di: int = 1` - 信号计算偏移量

**返回值**:
```python
{
    "{freq}_D1_表里关系V230102_向上_顶分_任意_0": "向上"
}
```

### 2. cxt_third_buy_V230228（三买）

**功能**: 识别三买信号

**参数**:
- `cat`: CZSC对象或CzscSignals对象
- `di: int = 1` - 信号计算偏移量

**返回值**:
```python
{
    "{freq}_D1_三买辅助V230228_三买_任意_任意_0": "三买"
}
```

### 3. tas_ma_base_V221101（均线）

**功能**: 计算均线信号

**参数**:
- `cat`: CZSC对象或CzscSignals对象
- `di: int = 1` - 信号计算偏移量
- `ma_type: str = 'SMA'` - 均线类型
- `timeperiod: int = 5` - 均线周期

**返回值**:
```python
{
    "{freq}_D{di}_{ma_type}{timeperiod}_均线_任意_任意_0": "均线值"
}
```

## 信号函数开发规范

1. **命名规范**: `{category}_{function}_{version}`
2. **版本号**: 使用日期格式，如`V230101`表示2023年1月1日
3. **文档字符串**: 必须包含函数说明、参数说明、返回值说明
4. **返回值**: 必须返回字典格式，键为信号名称，值为信号值

## 注意事项

1. **信号名称唯一性**: k3字段必须具有唯一性，推荐使用信号分类和开发日期
2. **信号值格式**: v1_v2_v3_score格式，score取值0~100
3. **参数验证**: 信号函数内部应验证参数有效性
4. **缓存利用**: 充分利用cat.cache缓存计算结果

## 本项目 API 与信号入参/返回

### GET /docs/signals 与 GET /docs/signals/{name}

- **category**：信号分类（cxt、tas、bar、vol 等），用于前端按类型筛选与展示。
- **params**：信号函数参数列表，每项含 name、type、description、default、required，对应 kwargs（如 freq、di、ma_type、timeperiod）。
- **data_requirements**：经验性数据需求，含 **freq**（建议周期，如「日线」「1分钟」）、**needed_bars**（约需 K 线根数），供前端作为该信号的默认周期参考。
- **signals**：从 docstring 中解析出的 Signal('...') 列表，即该函数返回的 signal 键名格式说明。

### POST /signals/batch

- **请求体**：symbol、**freq**（本批次统一周期）、signal_configs、sdt、edt。  
- **signal_configs** 每项：**name**（信号函数名，如 czsc.signals.xxx 或短名）、**freq**（可选，若与顶层 freq 一致可省略）、**di**（可选，默认 1）、以及该信号特有参数（如 ma_type、timeperiod）。  
- **说明**：当前接口一次请求只支持一个 freq；若需「每信号不同周期」，前端可按周期分组后多次调用 batch，再合并返回的 signals 字典。
- **返回**：**signals** 字典，key 为各信号产出的键名（如 `日线_D1_xxx_任意_任意_0`），value 为信号值字符串。
