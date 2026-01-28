# -*- coding: utf-8 -*-
"""
AkShare 基础数据获取函数

提供基于 AkShare 的数据获取功能
"""
import akshare as ak
import pandas as pd
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
from czsc.objects import RawBar, Freq


def get_real_time_data() -> Optional[pd.DataFrame]:
    """获取实时行情数据

    :return: DataFrame，包含所有A股实时行情数据
    """
    try:
        df = ak.stock_zh_a_spot_em()
        logger.info(f"获取到 {len(df)} 只股票实时数据")
        return df
    except Exception as e:
        logger.error(f"获取实时数据失败: {e}")
        return None


def get_minute_data(stock_code: str, period: str = "1", adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """获取分钟级别数据

    :param stock_code: 股票代码，如 "sz000001" 或 "sh600000"
    :param period: 周期，"1": 1分钟, "5": 5分钟, "15": 15分钟, "30": 30分钟, "60": 60分钟
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :return: DataFrame，包含分钟级别K线数据
    """
    try:
        df = ak.stock_zh_a_minute(
            symbol=stock_code,
            period=period,
            adjust=adjust
        )
        logger.info(f"获取 {stock_code} 的 {period}分钟数据，共 {len(df)} 条")
        return df
    except Exception as e:
        logger.error(f"获取分钟数据失败: {e}")
        return None


def get_historical_data(stock_code: str, start_date: str, end_date: str, 
                       adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """获取历史日线数据

    :param stock_code: 股票代码，如 "000001" 或 "600000"
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :return: DataFrame，包含历史日线K线数据
    """
    try:
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        logger.info(f"获取 {stock_code} 的历史数据，共 {len(df)} 条，时间范围：{start_date} - {end_date}")
        return df
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return None


def get_stock_list() -> Optional[pd.DataFrame]:
    """获取A股股票列表

    :return: DataFrame，包含所有A股股票代码和名称
    """
    try:
        df = ak.stock_info_a_code_name()
        logger.info(f"获取到 {len(df)} 只A股股票列表")
        return df
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return None


def format_akshare_to_rawbar(df: pd.DataFrame, symbol: str, freq: Freq) -> List[RawBar]:
    """将 AkShare 获取的 DataFrame 转换为 RawBar 列表

    :param df: AkShare 返回的 DataFrame
    :param symbol: 标的代码，格式如 "000001.SZ" 或 "600000.SH"
    :param freq: K线周期
    :return: RawBar 列表
    """
    try:
        bars = []
        
        # 确定时间列名（AkShare 可能使用不同的列名）
        time_col = None
        for col in ['时间', '日期', 'date', 'time', 'datetime']:
            if col in df.columns:
                time_col = col
                break
        
        if time_col is None:
            raise ValueError("无法找到时间列，请检查 DataFrame 列名")
        
        # 确定其他列名（处理中英文列名）
        col_mapping = {
            'open': ['开盘', 'open', '开盘价'],
            'close': ['收盘', 'close', '收盘价'],
            'high': ['最高', 'high', '最高价'],
            'low': ['最低', 'low', '最低价'],
            'vol': ['成交量', 'volume', 'vol', '成交额'],
            'amount': ['成交额', 'amount', '成交金额', 'amount']
        }
        
        col_names = {}
        for key, possible_names in col_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    col_names[key] = name
                    break
        
        # 检查必需的列是否存在
        required_cols = ['open', 'close', 'high', 'low']
        missing_cols = [col for col in required_cols if col not in col_names]
        if missing_cols:
            raise ValueError(f"缺少必需的列：{missing_cols}，当前列名：{df.columns.tolist()}")
        
        # 转换数据
        df = df.sort_values(time_col, ascending=True).reset_index(drop=True)
        
        for i, row in df.iterrows():
            # 处理时间
            dt = pd.to_datetime(row[time_col])
            
            # 处理价格数据
            open_price = float(row[col_names['open']])
            close_price = float(row[col_names['close']])
            high_price = float(row[col_names['high']])
            low_price = float(row[col_names['low']])
            
            # 处理成交量和成交额
            vol = float(row.get(col_names.get('vol', 'vol'), 0))
            amount = float(row.get(col_names.get('amount', 'amount'), 0))
            
            # 如果成交额为空，尝试计算
            if amount == 0 and vol > 0:
                amount = vol * (high_price + low_price + open_price + close_price) / 4
            
            bar = RawBar(
                symbol=symbol,
                id=i,
                dt=dt,
                freq=freq,
                open=open_price,
                close=close_price,
                high=high_price,
                low=low_price,
                vol=vol,
                amount=amount
            )
            bars.append(bar)
        
        logger.info(f"转换完成，共 {len(bars)} 根K线")
        return bars
    except Exception as e:
        logger.error(f"转换 AkShare 数据失败: {e}")
        raise


def normalize_stock_code(stock_code: str) -> str:
    """标准化股票代码格式

    将各种格式的股票代码转换为标准格式：000001.SZ 或 600000.SH

    :param stock_code: 股票代码，支持格式：
        - "000001" -> "000001.SZ"
        - "600000" -> "600000.SH"
        - "sz000001" -> "000001.SZ"
        - "sh600000" -> "600000.SH"
        - "000001.SZ" -> "000001.SZ" (保持不变)
    :return: 标准化后的股票代码
    """
    stock_code = stock_code.upper().strip()
    
    # 如果已经是标准格式，直接返回
    if '.' in stock_code:
        return stock_code
    
    # 处理 sz/shn 前缀
    if stock_code.startswith('SZ'):
        code = stock_code[2:]
        return f"{code}.SZ"
    elif stock_code.startswith('SH') or stock_code.startswith('SHN'):
        code = stock_code[2:] if stock_code.startswith('SH') else stock_code[3:]
        return f"{code}.SH"
    
    # 根据代码判断市场
    if stock_code.startswith('6'):
        return f"{stock_code}.SH"
    elif stock_code.startswith(('0', '3')):
        return f"{stock_code}.SZ"
    else:
        # 默认深圳
        return f"{stock_code}.SZ"


def get_akshare_code(stock_code: str) -> str:
    """将标准股票代码转换为 AkShare 需要的格式

    :param stock_code: 标准股票代码，如 "000001.SZ" 或 "600000.SH"
    :return: AkShare 格式的股票代码，如 "sz000001" 或 "sh600000"
    """
    if '.' in stock_code:
        code, market = stock_code.split('.')
        if market == 'SZ':
            return f"sz{code}"
        elif market == 'SH':
            return f"sh{code}"
        else:
            return stock_code
    return stock_code


# 使用示例
if __name__ == "__main__":
    # 获取实时数据
    real_time_df = get_real_time_data()
    if real_time_df is not None:
        print(f"获取到 {len(real_time_df)} 只股票数据")
        print(real_time_df[['代码', '名称', '最新价', '涨跌幅', '成交量']].head())
    
    # 获取平安银行(000001)的5分钟数据
    minute_df = get_minute_data("sz000001", "5")
    if minute_df is not None:
        print(f"\n获取到 {len(minute_df)} 条分钟数据")
        print(minute_df.head())
        
        # 转换为 RawBar
        bars = format_akshare_to_rawbar(minute_df, "000001.SZ", Freq.F5)
        print(f"\n转换为 RawBar 完成，共 {len(bars)} 根K线")
    
    # 获取历史数据
    hist_df = get_historical_data("000001", "20230101", "20231231")
    if hist_df is not None:
        print(f"\n获取到 {len(hist_df)} 条历史数据")
        print(hist_df.head())
        
        # 转换为 RawBar
        bars = format_akshare_to_rawbar(hist_df, "000001.SZ", Freq.D)
        print(f"\n转换为 RawBar 完成，共 {len(bars)} 根K线")
