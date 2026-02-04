#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从本地存储读取股票K线数据（兼容 czsc.connectors.research.get_raw_bars 返回结构）

说明：
- 本项目采集脚本 `scripts/fetch_stock_data.py` 会把数据写入 `/.stock_data` 分区目录
- 本脚本提供一个与 `czsc.connectors.research.get_raw_bars` 同签名的方法 `get_raw_bars`
  用于从本地分区存储读取数据，并返回 `czsc.objects.RawBar` 列表（或 DataFrame）

使用示例：
  python scripts/get_stock_data.py --symbol 600078.SH --freq 日线 --sdt 20240101 --edt 20241231
  python scripts/get_stock_data.py --symbol 600078.SH --freq 30分钟 --sdt 20250101 --edt 20250131
"""

import sys
import argparse
from pathlib import Path
from typing import Iterator, List, Tuple

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from loguru import logger

import czsc
from czsc.objects import Freq, RawBar

from backend.data.raw_data_storage import RawDataStorage


def _parse_dt(x: str) -> pd.Timestamp:
    """解析日期字符串，支持 YYYYMMDD / YYYY-MM-DD / datetime 字符串"""
    return pd.to_datetime(x)


def _iter_years(sdt: pd.Timestamp, edt: pd.Timestamp) -> Iterator[int]:
    """生成包含 sdt~edt 的年份序列（闭区间）"""
    for y in range(int(sdt.year), int(edt.year) + 1):
        yield y


def _iter_year_months(sdt: pd.Timestamp, edt: pd.Timestamp) -> Iterator[Tuple[int, int]]:
    """生成包含 sdt~edt 的 (year, month) 序列（闭区间）"""
    cur = pd.Timestamp(year=int(sdt.year), month=int(sdt.month), day=1)
    end = pd.Timestamp(year=int(edt.year), month=int(edt.month), day=1)
    while cur <= end:
        yield int(cur.year), int(cur.month)
        cur = (cur + pd.offsets.MonthBegin(1)).normalize()


def _minute_freq_to_period(freq: Freq) -> int:
    """将分钟频率转换为 period 数字"""
    value = freq.value
    if not value.endswith("分钟"):
        raise ValueError(f"freq 不是分钟周期：{value}")
    return int(value.replace("分钟", ""))


def _standardize_minute_df(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """将分钟分区数据标准化为 czsc.resample_bars 需要的列"""
    required = {"timestamp", "open", "close", "high", "low"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"分钟数据缺少必需列: {missing}; 当前列: {list(df.columns)}")

    x = df.copy()
    x["symbol"] = symbol
    x["dt"] = pd.to_datetime(x["timestamp"])
    x["vol"] = x["volume"] if "volume" in x.columns else x.get("vol", 0)
    x["amount"] = x["amount"] if "amount" in x.columns else 0
    return x[["symbol", "dt", "open", "close", "high", "low", "vol", "amount"]]


def _standardize_daily_df(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """将日线分区数据标准化为 czsc.resample_bars 需要的列"""
    required = {"date", "open", "close", "high", "low"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"日线数据缺少必需列: {missing}; 当前列: {list(df.columns)}")

    x = df.copy()
    x["symbol"] = symbol
    x["dt"] = pd.to_datetime(x["date"])
    x["vol"] = x["volume"] if "volume" in x.columns else x.get("vol", 0)
    x["amount"] = x["amount"] if "amount" in x.columns else 0
    return x[["symbol", "dt", "open", "close", "high", "low", "vol", "amount"]]


def _filter_dt_range(df: pd.DataFrame, sdt: pd.Timestamp, edt: pd.Timestamp) -> pd.DataFrame:
    """按时间范围过滤"""
    x = df[(df["dt"] >= sdt) & (df["dt"] <= edt)].copy()
    return x.reset_index(drop=True)


def _load_daily_from_storage(storage: RawDataStorage, symbol: str, sdt: pd.Timestamp, edt: pd.Timestamp) -> pd.DataFrame:
    """从按股票分区的日线存储加载数据（按年份文件合并）"""
    dfs: List[pd.DataFrame] = []
    for y in _iter_years(sdt, edt):
        df_y = storage.read_partitioned_data("daily", "by_stock", stock_code=symbol, year=y)
        if df_y is not None and len(df_y) > 0:
            dfs.append(df_y)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def _load_minute_from_storage(
    storage: RawDataStorage,
    symbol: str,
    sdt: pd.Timestamp,
    edt: pd.Timestamp,
    period: int,
) -> pd.DataFrame:
    """从按股票分区的分钟存储加载数据（按年月文件合并）"""
    dfs: List[pd.DataFrame] = []
    for y, m in _iter_year_months(sdt, edt):
        df_ym = storage.read_partitioned_data("minute", "by_stock", stock_code=symbol, year=y, month=m)
        if df_ym is not None and len(df_ym) > 0:
            dfs.append(df_ym)
    if not dfs:
        return pd.DataFrame()
    df = pd.concat(dfs, ignore_index=True)
    if "period" in df.columns:
        df = df[df["period"].astype(int) == int(period)].copy()
    return df.reset_index(drop=True)


def get_raw_bars(symbol, freq, sdt, edt, fq="前复权", **kwargs):
    """获取 CZSC 库定义的标准 RawBar 对象列表（从本地分区存储读取）

    设计目标：返回结构与 `czsc.connectors.research.get_raw_bars` 保持一致

    :param symbol: 标的代码，如 "600078.SH"
    :param freq: 周期，支持 Freq 对象，或者字符串，如
            '1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线', '季线', '年线'
    :param sdt: 开始时间
    :param edt: 结束时间
    :param fq: 除权类型（本地存储默认采集时已处理；此参数仅为接口一致性保留）
    :param kwargs:
        - raw_bars: bool，是否返回 RawBar 列表；False 则返回 DataFrame
        - base_path: Path|str，本地存储根目录（默认使用 StorageManager 的默认值：项目根目录/.stock_data）
    :return: List[RawBar] 或 DataFrame
    """
    raw_bars = kwargs.get("raw_bars", True)
    base_path = kwargs.get("base_path", None)
    _ = fq  # fq 保留占位，保证与 research.get_raw_bars 参数一致

    target_freq = czsc.Freq(freq)
    sdt_dt = _parse_dt(sdt)
    edt_dt = _parse_dt(edt)

    storage = RawDataStorage(base_path=base_path)
    if target_freq.value.endswith("分钟"):
        period = _minute_freq_to_period(target_freq)
        df0 = _load_minute_from_storage(storage, symbol, sdt_dt, edt_dt, period=period)
        if df0.empty:
            return []
        df1 = _standardize_minute_df(df0, symbol=symbol)
        df1 = _filter_dt_range(df1, sdt_dt, edt_dt)
        if df1.empty:
            return []
        return czsc.resample_bars(df1, target_freq=target_freq, raw_bars=raw_bars, base_freq=target_freq.value)

    df0 = _load_daily_from_storage(storage, symbol, sdt_dt, edt_dt)
    if df0.empty:
        return []
    df1 = _standardize_daily_df(df0, symbol=symbol)
    df1 = _filter_dt_range(df1, sdt_dt, edt_dt)
    if df1.empty:
        return []
    return czsc.resample_bars(df1, target_freq=target_freq, raw_bars=raw_bars, base_freq="日线")


def main() -> None:
    """命令行入口"""
    parser = argparse.ArgumentParser(description="从本地分区存储读取K线（返回结构兼容 czsc.get_raw_bars）")
    parser.add_argument("--symbol", required=True, type=str, help="标的代码，如 600078.SH")
    parser.add_argument("--freq", required=True, type=str, help="周期，如 日线 / 30分钟 / 周线")
    parser.add_argument("--sdt", required=True, type=str, help="开始时间，如 20240101")
    parser.add_argument("--edt", required=True, type=str, help="结束时间，如 20241231")
    parser.add_argument("--raw-bars", action="store_true", default=True, help="返回 RawBar 列表（默认）")
    parser.add_argument("--df", dest="raw_bars", action="store_false", help="返回 DataFrame")
    parser.add_argument("--base-path", type=str, default=None, help="本地存储根目录（默认：项目根目录/.stock_data）")
    args = parser.parse_args()

    bars_or_df = get_raw_bars(
        symbol=args.symbol,
        freq=args.freq,
        sdt=args.sdt,
        edt=args.edt,
        raw_bars=args.raw_bars,
        base_path=args.base_path,
    )

    if isinstance(bars_or_df, list):
        logger.info(f"返回 RawBar 数量：{len(bars_or_df)}")
        if bars_or_df:
            last = bars_or_df[-1]
            logger.info(f"最后一根：dt={last.dt} open={last.open} close={last.close} high={last.high} low={last.low} vol={last.vol}")
    else:
        logger.info(f"返回 DataFrame 行数：{len(bars_or_df)}；列：{list(bars_or_df.columns)}")
        logger.info(f"时间范围：{bars_or_df['dt'].min()} ~ {bars_or_df['dt'].max()}" if len(bars_or_df) else "空数据")


if __name__ == "__main__":
    main()