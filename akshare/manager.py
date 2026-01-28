# -*- coding: utf-8 -*-
"""
AkShare 数据管理器

提供与 modules/data.py 类似的接口，使用 AkShare 作为数据源
"""
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
from loguru import logger
from czsc.objects import RawBar, Freq
from czsc.utils import format_standard_kline, resample_bars
from czsc.akshare.base import (
    get_real_time_data,
    get_minute_data,
    get_historical_data,
    get_stock_list,
    format_akshare_to_rawbar,
    normalize_stock_code,
    get_akshare_code,
)


class AkShareDataManager:
    """AkShare 数据管理器

    提供基于 AkShare 的数据获取和处理功能，与 CZSC 框架集成
    """

    def __init__(self):
        """初始化数据管理器"""
        pass

    def get_raw_bars(self, symbol: str, freq: Freq, sdt: str = "20150101", 
                    edt: str = None, adjust: str = "qfq") -> List[RawBar]:
        """获取K线数据并转换为 RawBar 格式

        :param symbol: 标的代码，支持格式："000001"、"000001.SZ"、"sz000001"
        :param freq: K线周期
        :param sdt: 开始日期，格式：YYYYMMDD
        :param edt: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
        :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
        :return: RawBar 列表
        """
        try:
            # 标准化股票代码
            normalized_code = normalize_stock_code(symbol)
            akshare_code = get_akshare_code(normalized_code)
            
            if edt is None:
                edt = datetime.now().strftime("%Y%m%d")
            
            # 根据周期选择不同的数据获取方法
            if freq == Freq.D:
                # 日线数据
                df = get_historical_data(akshare_code, sdt, edt, adjust=adjust)
            elif freq in [Freq.F1, Freq.F5, Freq.F15, Freq.F30, Freq.F60]:
                # 分钟数据
                period_map = {
                    Freq.F1: "1",
                    Freq.F5: "5",
                    Freq.F15: "15",
                    Freq.F30: "30",
                    Freq.F60: "60"
                }
                period = period_map.get(freq, "1")
                df = get_minute_data(akshare_code, period=period, adjust=adjust)
            else:
                # 对于其他周期，先获取日线数据，然后重采样
                logger.warning(f"AkShare 不支持 {freq.value} 周期，将获取日线数据后重采样")
                df = get_historical_data(akshare_code, sdt, edt, adjust=adjust)
                if df is not None and len(df) > 0:
                    # 先转换为日线 RawBar
                    daily_bars = format_akshare_to_rawbar(df, normalized_code, Freq.D)
                    # 转换为DataFrame用于重采样（需要包含symbol列）
                    df_daily = pd.DataFrame([{
                        'symbol': normalized_code,
                        'dt': bar.dt,
                        'open': bar.open,
                        'close': bar.close,
                        'high': bar.high,
                        'low': bar.low,
                        'vol': bar.vol,
                        'amount': bar.amount
                    } for bar in daily_bars])
                    # 重采样到目标周期
                    bars = resample_bars(df_daily, freq, base_freq=Freq.D)
                    logger.info(f"获取 {symbol} 的K线数据完成，共 {len(bars)} 根K线")
                    return bars
                else:
                    return []
            
            if df is None or len(df) == 0:
                logger.warning(f"未获取到 {symbol} 的数据")
                return []
            
            # 转换为 RawBar
            bars = format_akshare_to_rawbar(df, normalized_code, freq)
            logger.info(f"获取 {symbol} 的K线数据完成，共 {len(bars)} 根K线")
            return bars
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise

    def get_symbols(self, category: str = "A股") -> List[str]:
        """获取标的列表

        :param category: 标的类别，目前支持 "A股"
        :return: 标的代码列表，格式：["000001.SZ", "600000.SH", ...]
        """
        try:
            if category == "A股":
                df = get_stock_list()
                if df is None:
                    return []
                
                # 转换代码格式
                symbols = []
                for _, row in df.iterrows():
                    code = str(row['code'])
                    normalized = normalize_stock_code(code)
                    symbols.append(normalized)
                
                logger.info(f"获取 {category} 标的列表完成，共 {len(symbols)} 个标的")
                return symbols
            else:
                logger.warning(f"不支持的标的类别：{category}")
                return []
        except Exception as e:
            logger.error(f"获取标的列表失败: {e}")
            raise

    def get_real_time_quotes(self) -> Optional[pd.DataFrame]:
        """获取实时行情数据

        :return: DataFrame，包含所有A股实时行情数据
        """
        return get_real_time_data()

    def format_kline(self, df: pd.DataFrame, symbol: str, freq: Freq) -> List[RawBar]:
        """格式化标准K线数据

        :param df: DataFrame，必须包含时间列和价格列
        :param symbol: 标的代码
        :param freq: K线周期
        :return: RawBar 列表
        """
        try:
            normalized_code = normalize_stock_code(symbol)
            bars = format_akshare_to_rawbar(df, normalized_code, freq)
            logger.info(f"格式化K线数据完成，共 {len(bars)} 根K线")
            return bars
        except Exception as e:
            logger.error(f"格式化K线数据失败: {e}")
            raise

    def resample_bars(self, bars: List[RawBar], target_freq: Freq, 
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
                'symbol': bars[0].symbol,
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

    def df_to_bars(self, df: pd.DataFrame, symbol: str, freq: Freq) -> List[RawBar]:
        """将DataFrame转换为RawBar列表

        :param df: DataFrame，必须包含时间列和价格列
        :param symbol: 标的代码
        :param freq: K线周期
        :return: RawBar 列表
        """
        return self.format_kline(df, symbol, freq)

    def bars_to_df(self, bars: List[RawBar]) -> pd.DataFrame:
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

