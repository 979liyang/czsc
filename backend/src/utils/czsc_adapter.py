# -*- coding: utf-8 -*-
"""
CZSC适配器

封装czsc库的常用操作，提供统一的接口供API层调用。
"""
from typing import List, Dict, Optional
from pathlib import Path
from loguru import logger

from czsc.analyze import CZSC
from czsc.objects import RawBar, Freq
from czsc.traders.base import CzscSignals
from czsc.utils.bar_generator import BarGenerator
from czsc.connectors import research

from ..storage import KlineStorage


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
        # 优先从本地存储读取
        if self.kline_storage:
            bars = self.kline_storage.load_bars(symbol, freq, sdt, edt)
            if bars:
                logger.info(f"从本地存储读取K线数据：{symbol} {freq}")
                return bars

        # 从connector获取
        try:
            bars = research.get_raw_bars(symbol, freq, sdt, edt)
            logger.info(f"从connector获取K线数据：{symbol} {freq}，共{len(bars)}条")

            # 保存到本地存储
            if self.kline_storage and bars:
                self.kline_storage.save_bars(symbol, freq, bars)

            return bars
        except Exception as e:
            logger.error(f"获取K线数据失败：{symbol} {freq}，错误：{e}")
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
