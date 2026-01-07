# -*- coding: utf-8 -*-
"""
数据管理模块

提供数据获取、处理、转换等功能
"""
from typing import List, Optional, Dict, Callable
from datetime import datetime
import pandas as pd
from loguru import logger
from czsc.objects import RawBar, Freq
from czsc.utils import format_standard_kline, resample_bars, BarGenerator
from czsc.utils.bar_generator import BarGenerator as BaseBarGenerator
from czsc.connectors import research


class DataManager:
    """数据管理器

    提供数据获取、处理、转换等功能的封装
    """

    def __init__(self):
        """初始化数据管理器"""
        pass

    @staticmethod
    def format_kline(df: pd.DataFrame, freq: Freq = None) -> List[RawBar]:
        """格式化标准K线数据

        :param df: DataFrame，必须包含 dt, open, close, high, low, vol, amount 列
        :param freq: K线周期，如果不提供则从DataFrame中推断
        :return: RawBar列表
        """
        try:
            bars = format_standard_kline(df, freq=freq)
            logger.info(f"格式化K线数据完成，共 {len(bars)} 根K线")
            return bars
        except Exception as e:
            logger.error(f"格式化K线数据失败: {e}")
            raise

    @staticmethod
    def resample_bars(bars: List[RawBar], target_freq: Freq, 
                     base_freq: Freq = None) -> List[RawBar]:
        """重采样K线数据

        :param bars: 原始K线数据
        :param target_freq: 目标K线周期
        :param base_freq: 基础K线周期，如果不提供则从bars中推断
        :return: 重采样后的K线数据
        """
        try:
            if base_freq is None:
                base_freq = bars[0].freq

            df = pd.DataFrame([{
                'dt': bar.dt,
                'open': bar.open,
                'close': bar.close,
                'high': bar.high,
                'low': bar.low,
                'vol': bar.vol,
                'amount': bar.amount
            } for bar in bars])

            resampled = resample_bars(df, target_freq, base_freq=base_freq)
            logger.info(f"K线重采样完成：{base_freq.value} -> {target_freq.value}")
            return resampled
        except Exception as e:
            logger.error(f"K线重采样失败: {e}")
            raise

    @staticmethod
    def get_raw_bars(symbol: str, freq: Freq, sdt: str = "20150101", 
                    edt: str = None) -> List[RawBar]:
        """从研究数据源获取K线数据

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始日期，格式：YYYYMMDD
        :param edt: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
        :return: RawBar列表
        """
        try:
            if edt is None:
                edt = datetime.now().strftime("%Y%m%d")

            bars = research.get_raw_bars(symbol, freq=freq, sdt=sdt, edt=edt)
            logger.info(f"获取 {symbol} 的K线数据完成，共 {len(bars)} 根K线")
            return bars
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise

    @staticmethod
    def get_symbols(category: str = "A股主要指数") -> List[str]:
        """获取标的列表

        :param category: 标的类别，如"A股主要指数"、"中证500成分股"等
        :return: 标的代码列表
        """
        try:
            symbols = research.get_symbols(category)
            logger.info(f"获取 {category} 标的列表完成，共 {len(symbols)} 个标的")
            return symbols
        except Exception as e:
            logger.error(f"获取标的列表失败: {e}")
            raise

    @staticmethod
    def create_bar_generator(base_freq: Freq, freqs: List[str] = None, 
                            market: str = "A") -> BarGenerator:
        """创建K线合成器

        :param base_freq: 基础K线周期
        :param freqs: 需要合成的K线周期列表
        :param market: 市场类型，默认为"A"（A股）
        :return: BarGenerator实例
        """
        try:
            bg = BarGenerator(
                base_freq=str(base_freq.value),
                freqs=freqs or [],
                market=market
            )
            logger.info(f"K线合成器创建成功，基础周期：{base_freq.value}")
            return bg
        except Exception as e:
            logger.error(f"创建K线合成器失败: {e}")
            raise

    @staticmethod
    def df_to_bars(df: pd.DataFrame, symbol: str, freq: Freq) -> List[RawBar]:
        """将DataFrame转换为RawBar列表

        :param df: DataFrame，必须包含 dt, open, close, high, low, vol, amount 列
        :param symbol: 标的代码
        :param freq: K线周期
        :return: RawBar列表
        """
        try:
            bars = []
            for idx, row in df.iterrows():
                bar = RawBar(
                    symbol=symbol,
                    id=idx,
                    dt=pd.to_datetime(row['dt']),
                    freq=freq,
                    open=float(row['open']),
                    close=float(row['close']),
                    high=float(row['high']),
                    low=float(row['low']),
                    vol=float(row['vol']),
                    amount=float(row.get('amount', 0))
                )
                bars.append(bar)
            logger.info(f"DataFrame转换为RawBar完成，共 {len(bars)} 根K线")
            return bars
        except Exception as e:
            logger.error(f"DataFrame转换失败: {e}")
            raise

    @staticmethod
    def bars_to_df(bars: List[RawBar]) -> pd.DataFrame:
        """将RawBar列表转换为DataFrame

        :param bars: RawBar列表
        :return: DataFrame
        """
        try:
            data = []
            for bar in bars:
                data.append({
                    'dt': bar.dt,
                    'symbol': bar.symbol,
                    'open': bar.open,
                    'close': bar.close,
                    'high': bar.high,
                    'low': bar.low,
                    'vol': bar.vol,
                    'amount': bar.amount
                })
            df = pd.DataFrame(data)
            logger.info(f"RawBar转换为DataFrame完成，共 {len(bars)} 根K线")
            return df
        except Exception as e:
            logger.error(f"RawBar转换失败: {e}")
            raise

