# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2023/3/5 20:45
describe: CZSC投研数据共享接口

"""
import os
import czsc
import glob
import pandas as pd
from datetime import datetime
from pathlib import Path


# 投研共享数据的本地缓存路径，需要根据实际情况修改
cache_path = os.environ.get("czsc_research_cache", r"/Users/liyang/Desktop/npc-czsc/.stock_data/raw")
if not os.path.exists(cache_path):
    raise ValueError(
        f"请设置环境变量 czsc_research_cache 为投研共享数据的本地缓存路径，当前路径不存在：{cache_path}。\n\n"
    )


def get_groups():
    """获取投研共享数据的分组信息

    :return: 分组信息
    """
    return ["A股主要指数", "A股场内基金", "中证500成分股", "期货主力"]


def get_symbols(name, **kwargs):
    """获取指定分组下的所有标的代码

    :param name: 分组名称，可选值：'A股主要指数', 'A股场内基金', '中证500成分股', '期货主力'
    :param kwargs:
    :return:
    """
    stock_dir  = Path(cache_path) / 'CZSC投研数据'
    if name.upper() == "ALL":
        files = glob.glob(os.path.join(stock_dir, "*", "*.parquet"))
    else:
        files = glob.glob(os.path.join(stock_dir, name, "*.parquet"))
    return [os.path.basename(x).replace(".parquet", "") for x in files]


# def get_raw_bars(symbol, freq, sdt, edt, fq="前复权", **kwargs):
#     """获取 CZSC 库定义的标准 RawBar 对象列表

#     :param symbol: 标的代码
#     :param freq: 周期，支持 Freq 对象，或者字符串，如
#             '1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线', '季线', '年线'
#     :param sdt: 开始时间
#     :param edt: 结束时间
#     :param fq: 除权类型，投研共享数据默认都是后复权，不需要再处理
#     :param kwargs:
#     :return:
#     """
#     raw_bars = kwargs.get("raw_bars", True)
#     kwargs["fq"] = fq
#     base = Path(cache_path)
#     files = list(base.rglob(f"{symbol}.parquet"))
#     if not files:
#         raise FileNotFoundError(
#             f"在 {base} 下未找到 {symbol}.parquet。"
#             "请确认 cache_path（或环境变量 czsc_research_cache）指向的目录下存在该标的的 parquet 文件。"
#         )
#     file = files[0]
#     freq = czsc.Freq(freq)
#     kline = pd.read_parquet(file)
#     if "dt" not in kline.columns:
#         kline["dt"] = pd.to_datetime(kline["datetime"])
#     kline = kline[(kline["dt"] >= pd.to_datetime(sdt)) & (kline["dt"] <= pd.to_datetime(edt))]
#     if kline.empty:
#         return []

#     df = kline.copy()
#     if symbol in ["SFIC9001", "SFIF9001", "SFIH9001"]:
#         # 股指：仅保留 09:31 - 11:30, 13:01 - 15:00
#         # 历史遗留问题，股指有一段时间，收盘时间是 15:15
#         dt1 = datetime.strptime("09:31:00", "%H:%M:%S")
#         dt2 = datetime.strptime("11:30:00", "%H:%M:%S")
#         c1 = (df["dt"].dt.time >= dt1.time()) & (df["dt"].dt.time <= dt2.time())

#         dt3 = datetime.strptime("13:01:00", "%H:%M:%S")
#         dt4 = datetime.strptime("15:00:00", "%H:%M:%S")
#         c2 = (df["dt"].dt.time >= dt3.time()) & (df["dt"].dt.time <= dt4.time())

#         df = df[c1 | c2].copy().reset_index(drop=True)

#     _bars = czsc.resample_bars(df, freq, raw_bars=raw_bars, base_freq="1分钟")
#     return _bars

# 分钟周期列表，用于判断走分钟数据源还是日线数据源
_MINUTE_FREQS = {"1分钟", "5分钟", "15分钟", "30分钟", "60分钟"}


def get_raw_bars(symbol, freq, sdt, edt, fq="前复权", **kwargs):
    """统一入口：分钟周期从 get_raw_bars_minute 获取，日级及以上从 get_raw_bars_daily 获取。

    :param symbol: 标的代码
    :param freq: 周期，支持 Freq 对象或字符串，如
            '1分钟','5分钟','15分钟','30分钟','60分钟','日线','周线','月线','季线','年线'
    :param sdt: 开始时间
    :param edt: 结束时间
    :param fq: 除权类型
    :param kwargs: 透传 raw_bars 等
    :return: RawBar 列表
    """
    freq_val = getattr(freq, "value", str(freq)).strip()
    if freq_val in _MINUTE_FREQS:
        return get_raw_bars_minute(symbol, freq, sdt, edt, fq=fq, **kwargs)
    return get_raw_bars_daily(symbol, freq, sdt, edt, fq=fq, **kwargs)

def get_raw_bars_minute(symbol, freq, sdt, edt, fq="前复权", **kwargs):
    """从 cache_path 下 minute_by_stock 目录读取分钟数据，返回与 get_raw_bars 一致的 RawBar 列表。

    数据源：cache_path/minute_by_stock/stock_code={symbol}/year={year}/{symbol}_{year}-{month:02d}.parquet
    与 get_raw_bars 使用投研共享 parquet 不同，本方法使用本地按股票+年月分区的 1 分钟数据。

    :param symbol: 标的代码（如 600078.SH）
    :param freq: 周期，支持 Freq 对象或字符串，如 '1分钟','5分钟','15分钟','30分钟','60分钟','日线' 等
    :param sdt: 开始时间（字符串或 datetime）
    :param edt: 结束时间（字符串或 datetime）
    :param fq: 除权类型，保留入参一致，本地分钟数据一般不处理复权
    :param kwargs: 含 raw_bars 等，同 get_raw_bars
    :return: RawBar 列表，与 get_raw_bars 返回格式一致
    """
    raw_bars = kwargs.get("raw_bars", True)
    base = Path(cache_path)
    minute_root = base / "minute_by_stock"
    if not minute_root.exists():
        raise ValueError(
            f"minute_by_stock 路径不存在：{minute_root}。请确保 cache_path 下存在 minute_by_stock 目录。"
        )
    stock_dir = minute_root / f"stock_code={symbol}"
    if not stock_dir.exists():
        return []
    files = sorted(stock_dir.glob("year=*/**/*.parquet"))
    if not files:
        return []
    dfs = []
    for fp in files:
        try:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0:
                dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return []
    kline = pd.concat(dfs, ignore_index=True)
    kline["timestamp"] = pd.to_datetime(kline["timestamp"])
    if "period" in kline.columns:
        kline = kline[kline["period"] == 1]
    kline = kline[(kline["timestamp"] >= pd.to_datetime(sdt)) & (kline["timestamp"] <= pd.to_datetime(edt))]
    if kline.empty:
        return []
    df = kline.copy()
    df["symbol"] = df["stock_code"] if "stock_code" in df.columns else symbol
    df["dt"] = df["timestamp"]
    df["vol"] = df["volume"] if "volume" in df.columns else df.get("vol", 0)
    if "amount" not in df.columns:
        df["amount"] = 0
    df = df[["symbol", "dt", "open", "close", "high", "low", "vol", "amount"]]
    freq = czsc.Freq(freq)
    _bars = czsc.resample_bars(df, freq, raw_bars=raw_bars, base_freq="1分钟")
    return _bars

def get_raw_bars_daily(symbol, freq, sdt, edt, fq="前复权", **kwargs):
    """从 cache_path 下 daily/by_stock 目录读取日线数据，返回与 get_raw_bars 一致的 RawBar 列表。

    数据源：cache_path/daily/by_stock/stock_code={symbol}/*.parquet

    :param symbol: 标的代码（如 600078.SH）
    :param freq: 周期，支持 Freq 对象或字符串，通常为 '日线'，也可为 '周线','月线' 等由日线重采样
    :param sdt: 开始时间（字符串或 datetime）
    :param edt: 结束时间（字符串或 datetime）
    :param fq: 除权类型，保留入参一致
    :param kwargs: 含 raw_bars 等，同 get_raw_bars
    :return: RawBar 列表，与 get_raw_bars 返回格式一致
    """
    raw_bars = kwargs.get("raw_bars", True)
    base = Path(cache_path)
    daily_root = base / "daily" / "by_stock"
    stock_dir = daily_root / f"stock_code={symbol}"
    if not daily_root.exists() or not stock_dir.exists():
        return []
    files = sorted(stock_dir.glob("*.parquet"))
    if not files:
        return []
    dfs = []
    for fp in files:
        try:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0:
                dfs.append(df)
        except Exception:
            continue
    if not dfs:
        return []
    kline = pd.concat(dfs, ignore_index=True)
    date_col = "date" if "date" in kline.columns else ("trade_date" if "trade_date" in kline.columns else "dt")
    if date_col not in kline.columns:
        return []
    kline["dt"] = pd.to_datetime(kline[date_col])
    kline = kline[(kline["dt"] >= pd.to_datetime(sdt)) & (kline["dt"] <= pd.to_datetime(edt))]
    if kline.empty:
        return []
    df = kline.copy()
    df["symbol"] = df["stock_code"] if "stock_code" in df.columns else symbol
    df["vol"] = df["volume"] if "volume" in df.columns else df.get("vol", 0)
    if "amount" not in df.columns:
        df["amount"] = 0
    df = df[["symbol", "dt", "open", "close", "high", "low", "vol", "amount"]].sort_values("dt").reset_index(drop=True)
    freq = czsc.Freq(freq)
    _bars = czsc.resample_bars(df, freq, raw_bars=raw_bars, base_freq="日线")
    return _bars