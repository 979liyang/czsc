# -*- coding: utf-8 -*-
"""
CZSC适配器

封装czsc库的常用操作，提供统一的接口供API层调用。
"""
from typing import List, Dict, Optional, Any
from pathlib import Path

import pandas as pd
from loguru import logger

from czsc.analyze import CZSC
from czsc.objects import RawBar, Freq
from czsc.traders.base import CzscSignals
from czsc.utils.bar_generator import BarGenerator
from czsc.connectors import research

from ..storage import KlineStorage


def _get_daily_bars_from_stock_data_impl(
    symbol: str, sdt: str, edt: str
) -> List[RawBar]:
    """
    从 .stock_data/raw/daily/by_stock 读取日线并转为 RawBar 列表。
    与 TradingView / 本地 CZSC 接口同源，供 get_bars 日线回退使用。
    """
    from ..services.local_czsc_service import (
        _default_stock_data_root,
        _load_daily_df_by_stock,
        _df_to_raw_bars,
        _normalize_symbol,
    )

    base_path = _default_stock_data_root()
    symbol_norm = _normalize_symbol(symbol)
    sdt_ts = pd.to_datetime(sdt)
    edt_ts = pd.to_datetime(edt)
    df = _load_daily_df_by_stock(base_path, symbol_norm, sdt_ts, edt_ts)
    if df is None or df.empty:
        return []
    return _df_to_raw_bars(df, "日线")


def _bar_first_date(bar) -> Optional[pd.Timestamp]:
    """取 bar.dt 的日期用于比较"""
    if bar is None:
        return None
    dt = getattr(bar, "dt", None)
    if dt is None:
        return None
    return pd.to_datetime(dt)


def _requested_sdt_date(sdt: str) -> pd.Timestamp:
    """请求的 sdt 转为日期"""
    return pd.to_datetime(sdt)


def _requested_edt_date(edt: str) -> pd.Timestamp:
    """请求的 edt 转为日期"""
    return pd.to_datetime(edt)


def _merge_bars_by_date(bars_a: List[RawBar], bars_b: List[RawBar]) -> List[RawBar]:
    """按日期合并两段 bars，同日期保留 bars_b 中的（通常更新），按 dt 排序"""
    by_date: Dict[Any, RawBar] = {}
    for b in bars_a:
        by_date[pd.to_datetime(b.dt).date()] = b
    for b in bars_b:
        by_date[pd.to_datetime(b.dt).date()] = b
    return sorted(by_date.values(), key=lambda x: x.dt)


class CZSCAdapter:
    """CZSC适配器，封装常用操作"""

    def __init__(self, kline_storage: Optional[KlineStorage] = None):
        """
        初始化CZSC适配器

        :param kline_storage: K线存储服务（可选），如果提供则优先从本地存储读取
        """
        self.kline_storage = kline_storage

    def get_bars(self, symbol: str, freq: str, sdt: str, edt: str) -> List[RawBar]:
        """
        获取K线数据

        优先从本地存储读取，如果不存在则从connector获取。

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始时间（YYYYMMDD或YYYY-MM-DD）
        :param edt: 结束时间（YYYYMMDD或YYYY-MM-DD）
        :return: RawBar对象列表
        """
        source = "none"
        # 优先从本地存储读取
        if self.kline_storage:
            bars = self.kline_storage.load_bars(symbol, freq, sdt, edt)
            if bars:
                source = "kline_storage"
                # 日线且 Parquet 覆盖不足（首条晚于请求 sdt）时，尝试 .stock_data 拉取更早数据
                if freq in ("日线", "日"):
                    req_sdt = _requested_sdt_date(sdt)
                    first_dt = _bar_first_date(bars[0])
                    if first_dt is not None and first_dt > req_sdt:
                        fallback = _get_daily_bars_from_stock_data_impl(symbol, sdt, edt)
                        if fallback:
                            fallback_first = _bar_first_date(fallback[0])
                            if fallback_first is not None and fallback_first < first_dt:
                                bars = fallback
                                source = "stock_data_merge"
                                logger.info(
                                    f"日线覆盖不足，已用 .stock_data 回退：{symbol} {sdt}~{edt}，共{len(bars)}条"
                                )
                                if self.kline_storage:
                                    self.kline_storage.save_bars(symbol, freq, bars)
                                logger.info(f"K线数据来源：{source} | {symbol} {freq}，共{len(bars)}条")
                                return bars
                    # 结束日期扩展：Parquet 最晚数据早于请求 edt 时，从 .stock_data 补 [实际结束+1, edt]
                    req_edt = _requested_edt_date(edt)
                    last_dt = _bar_first_date(bars[-1])
                    if last_dt is not None and last_dt.date() < req_edt.date():
                        extend_sdt = (last_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                        extension = _get_daily_bars_from_stock_data_impl(symbol, extend_sdt, edt)
                        if extension:
                            bars = _merge_bars_by_date(bars, extension)
                            source = "stock_data_merge"
                            logger.info(
                                f"日线结束日期已用 .stock_data 扩展：{symbol} {extend_sdt}~{edt}，共{len(bars)}条"
                            )
                            if self.kline_storage:
                                self.kline_storage.save_bars(symbol, freq, bars)
                            logger.info(f"K线数据来源：{source} | {symbol} {freq}，共{len(bars)}条")
                            return bars
                logger.info(f"K线数据来源：{source} | {symbol} {freq}，共{len(bars)}条")
                return bars

        # 从 connector 获取（统一走 research.get_raw_bars）
        try:
            bars = research.get_raw_bars(symbol, freq, sdt, edt)
            if bars:
                source = "connector"
                logger.info(f"K线数据来源：{source} | {symbol} {freq}，共{len(bars)}条")
                if self.kline_storage:
                    self.kline_storage.save_bars(symbol, freq, bars)
                return bars
        except Exception as e:
            logger.error(f"获取K线数据失败：{symbol} {freq}，错误：{e}")

        # 日线回退：从 .stock_data/raw/daily/by_stock 读取（与 TradingView / 本地 CZSC 同源）
        if freq in ("日线", "日"):
            bars = _get_daily_bars_from_stock_data_impl(symbol, sdt, edt)
            if bars:
                source = "stock_data"
                logger.info(f"K线数据来源：{source} | {symbol} 日线，共{len(bars)}条")
                if self.kline_storage:
                    self.kline_storage.save_bars(symbol, freq, bars)
                return bars

        return []

    def analyze(self, bars: List[RawBar]) -> CZSC:
        """
        执行缠论分析

        :param bars: RawBar对象列表
        :return: CZSC分析对象
        """
        if not bars:
            raise ValueError("K线数据为空，无法进行分析")

        czsc = CZSC(bars)
        logger.debug(f"执行缠论分析：{bars[0].symbol} {bars[0].freq.value}，共{len(bars)}条K线")
        return czsc

    def calculate_signals(self, bg: BarGenerator, signals_config: List[Dict]) -> Dict:
        """
        计算信号

        :param bg: BarGenerator对象
        :param signals_config: 信号配置列表
        :return: 信号字典
        """
        cs = CzscSignals(bg=bg, signals_config=signals_config)
        signals = dict(cs.s)
        logger.debug(f"计算信号：{bg.symbol}，共{len(signals)}个信号")
        return signals

    def create_bar_generator(self, base_freq: str, freqs: List[str],
                            bars: Optional[List[RawBar]] = None) -> BarGenerator:
        """
        创建BarGenerator对象

        :param base_freq: 基础周期
        :param freqs: 需要合成的周期列表
        :param bars: 初始K线数据（可选）
        :return: BarGenerator对象
        """
        bg = BarGenerator(base_freq=base_freq, freqs=freqs)

        if bars:
            # 初始化基础周期K线
            bg.init_freq_bars(base_freq, bars)

        return bg

    def resample_bars(self, bars: List[RawBar], target_freq: str) -> List[RawBar]:
        """
        将K线数据重新采样为目标周期

        :param bars: 原始K线数据
        :param target_freq: 目标周期
        :return: 重新采样后的K线数据
        """
        from czsc.utils.bar_generator import resample_bars
        from czsc.utils.bar_generator import format_standard_kline
        import pandas as pd

        if not bars:
            return []

        # 转换为DataFrame
        data = []
        for bar in bars:
            data.append({
                'symbol': bar.symbol,
                'dt': bar.dt,
                'open': bar.open,
                'close': bar.close,
                'high': bar.high,
                'low': bar.low,
                'vol': bar.vol,
                'amount': bar.amount,
            })

        df = pd.DataFrame(data)
        df['dt'] = pd.to_datetime(df['dt'])

        # 重新采样
        resampled_df = resample_bars(df, target_freq, raw_bars=False)

        # 转换为RawBar
        resampled_bars = format_standard_kline(resampled_df, target_freq)

        logger.debug(f"重新采样K线：{bars[0].symbol} {bars[0].freq.value} -> {target_freq}，"
                    f"{len(bars)}条 -> {len(resampled_bars)}条")

        return resampled_bars
