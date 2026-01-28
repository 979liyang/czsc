# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2025/01/XX
describe: stock 作为前缀，代表信号属于股票市场特定信号
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List
from loguru import logger
from collections import OrderedDict
from czsc import CZSC
from czsc.objects import RawBar
from czsc.utils import get_sub_elements, create_single_signal


def stock_price_range_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票价格波动区间信号
    
    参数模板："{freq}_D{di}价格区间N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算最近n根K线的价格波动区间
    2. 判断当前价格在区间中的位置：高位、中位、低位
    
    **信号列表：**
    
    - Signal('日线_D1价格区间N20_股票信号V250101_高位_任意_任意_0')
    - Signal('日线_D1价格区间N20_股票信号V250101_中位_任意_任意_0')
    - Signal('日线_D1价格区间N20_股票信号V250101_低位_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算区间使用的K线数量，默认 20
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 20))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}价格区间N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    current_bar = c.bars_raw[-di]
    current_price = current_bar.close
    
    high_prices = [b.high for b in bars]
    low_prices = [b.low for b in bars]
    
    price_high = max(high_prices)
    price_low = min(low_prices)
    price_range = price_high - price_low
    
    if price_range == 0:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1="其他")
    
    position = (current_price - price_low) / price_range
    
    if position >= 0.7:
        v1 = "高位"
    elif position <= 0.3:
        v1 = "低位"
    else:
        v1 = "中位"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def stock_volume_concentration_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票成交量集中度信号
    
    参数模板："{freq}_D{di}成交量集中度N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算最近n根K线的成交量集中度
    2. 判断成交量是否集中在最近几根K线
    
    **信号列表：**
    
    - Signal('日线_D1成交量集中度N20_股票信号V250101_集中_任意_任意_0')
    - Signal('日线_D1成交量集中度N20_股票信号V250101_分散_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算集中度使用的K线数量，默认 20
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 20))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}成交量集中度N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    volumes = [b.vol for b in bars if b.vol > 0]
    
    if len(volumes) < 5:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    # 计算最近3根K线的成交量占比
    recent_vol = sum(volumes[-3:])
    total_vol = sum(volumes)
    
    if total_vol == 0:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    concentration = recent_vol / total_vol
    
    if concentration >= 0.4:
        v1 = "集中"
    else:
        v1 = "分散"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def stock_momentum_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票价格动量信号
    
    参数模板："{freq}_D{di}价格动量N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算最近n根K线的价格动量
    2. 判断价格动量的强度和方向
    
    **信号列表：**
    
    - Signal('日线_D1价格动量N10_股票信号V250101_强上涨_任意_任意_0')
    - Signal('日线_D1价格动量N10_股票信号V250101_弱上涨_任意_任意_0')
    - Signal('日线_D1价格动量N10_股票信号V250101_弱下跌_任意_任意_0')
    - Signal('日线_D1价格动量N10_股票信号V250101_强下跌_任意_任意_0')
    - Signal('日线_D1价格动量N10_股票信号V250101_震荡_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算动量使用的K线数量，默认 10
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 10))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}价格动量N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    prices = [b.close for b in bars]
    
    # 计算价格变化率
    price_change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
    
    # 计算价格波动率
    returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices)) if prices[i-1] > 0]
    volatility = np.std(returns) if len(returns) > 0 else 0
    
    # 判断动量
    if price_change > 0.05 and volatility < 0.03:
        v1 = "强上涨"
    elif price_change > 0.02:
        v1 = "弱上涨"
    elif price_change < -0.05 and volatility < 0.03:
        v1 = "强下跌"
    elif price_change < -0.02:
        v1 = "弱下跌"
    else:
        v1 = "震荡"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def stock_price_efficiency_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票价格效率信号
    
    参数模板："{freq}_D{di}价格效率N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算价格效率：实际价格变化 / 理论最大价格变化
    2. 判断价格运动的效率
    
    **信号列表：**
    
    - Signal('日线_D1价格效率N10_股票信号V250101_高效_任意_任意_0')
    - Signal('日线_D1价格效率N10_股票信号V250101_低效_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算效率使用的K线数量，默认 10
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 10))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}价格效率N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    
    # 实际价格变化
    actual_change = abs(bars[-1].close - bars[0].close)
    
    # 理论最大价格变化（所有K线的最高价和最低价之差）
    high_prices = [b.high for b in bars]
    low_prices = [b.low for b in bars]
    max_range = max(high_prices) - min(low_prices)
    
    if max_range == 0:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    # 计算效率
    efficiency = actual_change / max_range
    
    if efficiency >= 0.6:
        v1 = "高效"
    else:
        v1 = "低效"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def stock_volatility_regime_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票波动率状态信号
    
    参数模板："{freq}_D{di}波动率状态N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算最近n根K线的波动率
    2. 与历史波动率比较，判断当前波动率状态
    
    **信号列表：**
    
    - Signal('日线_D1波动率状态N20_股票信号V250101_高波动_任意_任意_0')
    - Signal('日线_D1波动率状态N20_股票信号V250101_正常波动_任意_任意_0')
    - Signal('日线_D1波动率状态N20_股票信号V250101_低波动_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算波动率使用的K线数量，默认 20
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 20))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}波动率状态N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n * 2 + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    historical_bars = get_sub_elements(c.bars_raw, di=di + n, n=n)
    
    # 计算当前波动率
    current_returns = [(bars[i].close - bars[i-1].close) / bars[i-1].close 
                      for i in range(1, len(bars)) if bars[i-1].close > 0]
    current_vol = np.std(current_returns) if len(current_returns) > 0 else 0
    
    # 计算历史波动率
    historical_returns = [(historical_bars[i].close - historical_bars[i-1].close) / historical_bars[i-1].close 
                          for i in range(1, len(historical_bars)) if historical_bars[i-1].close > 0]
    historical_vol = np.std(historical_returns) if len(historical_returns) > 0 else 0
    
    if historical_vol == 0:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    # 比较波动率
    vol_ratio = current_vol / historical_vol
    
    if vol_ratio >= 1.5:
        v1 = "高波动"
    elif vol_ratio <= 0.7:
        v1 = "低波动"
    else:
        v1 = "正常波动"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def stock_trend_strength_V250101(c: CZSC, **kwargs) -> OrderedDict:
    """股票趋势强度信号
    
    参数模板："{freq}_D{di}趋势强度N{n}_股票信号V250101"
    
    **信号逻辑：**
    
    1. 计算最近n根K线的趋势强度
    2. 通过价格和成交量的配合判断趋势强度
    
    **信号列表：**
    
    - Signal('日线_D1趋势强度N10_股票信号V250101_强趋势_任意_任意_0')
    - Signal('日线_D1趋势强度N10_股票信号V250101_弱趋势_任意_任意_0')
    - Signal('日线_D1趋势强度N10_股票信号V250101_无趋势_任意_任意_0')
    
    :param c: CZSC对象
    :param kwargs: 参数字典
        - di: 倒数第 di 根 K 线，默认 1
        - n: 计算趋势强度使用的K线数量，默认 10
    :return: 返回信号结果
    """
    di = int(kwargs.get("di", 1))
    n = int(kwargs.get("n", 10))
    freq = c.freq.value
    k1, k2, k3 = f"{freq}_D{di}趋势强度N{n}_股票信号V250101".split("_")
    v1 = "其他"
    
    if len(c.bars_raw) < n + di:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    bars = get_sub_elements(c.bars_raw, di=di, n=n)
    
    # 计算价格趋势
    prices = [b.close for b in bars]
    price_trend = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
    
    # 计算成交量趋势
    volumes = [b.vol for b in bars if b.vol > 0]
    if len(volumes) < 2:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)
    
    avg_vol_first = np.mean(volumes[:len(volumes)//2])
    avg_vol_last = np.mean(volumes[len(volumes)//2:])
    vol_trend = (avg_vol_last - avg_vol_first) / avg_vol_first if avg_vol_first > 0 else 0
    
    # 判断趋势强度
    price_strength = abs(price_trend)
    vol_confirmation = abs(vol_trend) > 0.1 and (price_trend * vol_trend > 0)
    
    if price_strength > 0.05 and vol_confirmation:
        v1 = "强趋势"
    elif price_strength > 0.02:
        v1 = "弱趋势"
    else:
        v1 = "无趋势"
    
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)

