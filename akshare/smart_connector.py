# -*- coding: utf-8 -*-
"""
智能数据连接器

优先从数据库获取数据，如果数据库没有数据，则从 akshare 获取并保存到数据库
提供与 czsc.connectors 类似的接口
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
from czsc.objects import RawBar, Freq
from czsc.akshare.database import get_db_manager, StockKline
from czsc.akshare.base import normalize_stock_code, get_akshare_code
from czsc.akshare.fetch_data import fetch_historical_data, fetch_minute_data, get_stock_info
from czsc.akshare.store_data import store_kline_data, store_stock_info
from czsc.akshare.czsc_adapter import get_raw_bars as db_get_raw_bars


def get_symbols(name: str = "all", **kwargs) -> List[str]:
    """获取标的代码列表
    
    优先从数据库获取，如果数据库没有，则从 akshare 获取股票列表
    
    :param name: 标的类别
        - "all": 所有股票
        - "sh": 上证股票
        - "sz": 深证股票
        - "cyb": 创业板股票
    :param kwargs: 其他参数
    :return: 标的代码列表，格式：["000001.SZ", "600000.SH", ...]
    """
    # 先尝试从数据库获取
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        if name.lower() == "all":
            stocks = session.query(StockKline.symbol).distinct().all()
        elif name.lower() == "sh":
            stocks = session.query(StockKline.symbol).filter(
                StockKline.symbol.like('%.SH')
            ).distinct().all()
        elif name.lower() == "sz":
            stocks = session.query(StockKline.symbol).filter(
                StockKline.symbol.like('%.SZ')
            ).distinct().all()
        elif name.lower() == "cyb":
            stocks = session.query(StockKline.symbol).filter(
                StockKline.symbol.like('3%.SZ')
            ).distinct().all()
        else:
            logger.warning(f"不支持的标的类别: {name}")
            return []
        
        symbols = [stock[0] for stock in stocks]
        
        # 如果数据库有数据，直接返回
        if len(symbols) > 0:
            logger.info(f"从数据库获取 {name} 标的列表完成，共 {len(symbols)} 个")
            return symbols
        
        # 如果数据库没有数据，从 akshare 获取
        logger.info(f"数据库中没有 {name} 标的列表，从 akshare 获取...")
        from czsc.akshare.fetch_data import get_stock_list_by_market
        
        stocks_dict = get_stock_list_by_market()
        
        if name.lower() == "all":
            all_codes = stocks_dict.get('sh', []) + stocks_dict.get('sz', []) + stocks_dict.get('cyb', [])
            symbols = [normalize_stock_code(code) for code in all_codes]
        elif name.lower() == "sh":
            symbols = [normalize_stock_code(code) for code in stocks_dict.get('sh', [])]
        elif name.lower() == "sz":
            symbols = [normalize_stock_code(code) for code in stocks_dict.get('sz', [])]
        elif name.lower() == "cyb":
            symbols = [normalize_stock_code(code) for code in stocks_dict.get('cyb', [])]
        
        logger.info(f"从 akshare 获取 {name} 标的列表完成，共 {len(symbols)} 个")
        return symbols
        
    except Exception as e:
        logger.error(f"获取标的列表失败: {e}")
        return []
    finally:
        session.close()


def get_raw_bars(symbol: str, freq: Freq, sdt: str, edt: str, 
                fq: str = "前复权", **kwargs) -> List[RawBar]:
    """获取K线数据并转换为 RawBar 格式
    
    优先从数据库获取，如果数据库没有或数据不完整，则从 akshare 获取并保存到数据库
    
    :param symbol: 标的代码，支持格式："000001"、"000001.SZ"
    :param freq: K线周期
    :param sdt: 开始时间，格式：YYYYMMDD 或 YYYY-MM-DD
    :param edt: 结束时间，格式：YYYYMMDD 或 YYYY-MM-DD
    :param fq: 复权类型，"前复权" 或 "后复权"
    :param kwargs: 其他参数
    :return: RawBar 列表
    """
    # 标准化股票代码
    normalized_symbol = normalize_stock_code(symbol)
    
    # 先尝试从数据库获取
    try:
        bars = db_get_raw_bars(normalized_symbol, freq, sdt, edt, fq, **kwargs)
        
        # 检查数据是否完整
        if len(bars) > 0:
            # 检查时间范围是否完整
            bars_dt = [bar.dt for bar in bars]
            min_dt = min(bars_dt)
            max_dt = max(bars_dt)
            
            # 转换时间格式
            if isinstance(sdt, str):
                if len(sdt) == 8:  # YYYYMMDD
                    sdt_dt = datetime.strptime(sdt, "%Y%m%d")
                else:  # YYYY-MM-DD
                    sdt_dt = datetime.strptime(sdt, "%Y-%m-%d")
            else:
                sdt_dt = sdt
            
            if isinstance(edt, str):
                if len(edt) == 8:  # YYYYMMDD
                    edt_dt = datetime.strptime(edt, "%Y%m%d")
                else:  # YYYY-MM-DD
                    edt_dt = datetime.strptime(edt, "%Y-%m-%d")
            else:
                edt_dt = edt
            
            # 如果数据范围基本满足要求（允许1天的误差），直接返回
            if min_dt <= sdt_dt + timedelta(days=1) and max_dt >= edt_dt - timedelta(days=1):
                logger.info(f"从数据库获取 {normalized_symbol} 数据完成，共 {len(bars)} 根K线")
                return bars
            else:
                logger.info(f"数据库数据不完整（{min_dt} - {max_dt}），需要从 akshare 补充")
        else:
            logger.info(f"数据库中没有 {normalized_symbol} 的数据，从 akshare 获取...")
    except Exception as e:
        logger.warning(f"从数据库获取数据失败: {e}，将从 akshare 获取")
    
    # 从 akshare 获取数据
    try:
        # 转换复权类型
        adjust_map = {
            "前复权": "qfq",
            "后复权": "hfq",
            "不复权": "none"
        }
        adjust = adjust_map.get(fq, "qfq")
        
        # 转换时间格式
        if isinstance(sdt, str):
            if len(sdt) == 8:  # YYYYMMDD
                sdt_str = sdt
            else:  # YYYY-MM-DD
                sdt_str = datetime.strptime(sdt, "%Y-%m-%d").strftime("%Y%m%d")
        else:
            sdt_str = sdt.strftime("%Y%m%d")
        
        if isinstance(edt, str):
            if len(edt) == 8:  # YYYYMMDD
                edt_str = edt
            else:  # YYYY-MM-DD
                edt_str = datetime.strptime(edt, "%Y-%m-%d").strftime("%Y%m%d")
        else:
            edt_str = edt.strftime("%Y%m%d")
        
        # 根据周期选择不同的数据获取方法
        freq_str = str(freq)
        freq_map = {
            "1分钟": "1min",
            "5分钟": "5min",
            "15分钟": "15min",
            "30分钟": "30min",
            "60分钟": "60min",
            "日线": "D",
            "周线": "W",
            "月线": "M"
        }
        db_freq = freq_map.get(freq_str, freq_str)
        
        df = None
        code = normalized_symbol.split('.')[0]  # 获取纯代码，如 "000001"
        
        if freq == Freq.D:
            # 日线数据
            df = fetch_historical_data(code, sdt_str, edt_str, adjust=adjust)
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
            df = fetch_minute_data(code, period=period, adjust=adjust)
        else:
            # 对于其他周期，先获取日线数据，然后重采样
            logger.warning(f"AkShare 不支持 {freq.value} 周期，将获取日线数据后重采样")
            df = fetch_historical_data(code, sdt_str, edt_str, adjust=adjust)
        
        if df is None or len(df) == 0:
            logger.warning(f"从 akshare 获取 {normalized_symbol} 数据失败或为空")
            return []
        
        # 保存到数据库
        logger.info(f"保存 {normalized_symbol} 数据到数据库...")
        stored_count = store_kline_data(normalized_symbol, df, db_freq, adjust)
        logger.info(f"保存完成，共 {stored_count} 条记录")
        
        # 保存股票基本信息
        stock_info = get_stock_info(code)
        if stock_info:
            store_stock_info(stock_info)
        
        # 从数据库重新获取（确保数据格式一致）
        bars = db_get_raw_bars(normalized_symbol, freq, sdt, edt, fq, **kwargs)
        logger.info(f"从数据库获取 {normalized_symbol} 数据完成，共 {len(bars)} 根K线")
        return bars
        
    except Exception as e:
        logger.error(f"从 akshare 获取数据失败: {normalized_symbol}, {e}")
        return []


def get_groups():
    """获取数据分组列表
    
    :return: 分组列表
    """
    return ["A股", "上证", "深证", "创业板"]


# 为了与 czsc.connectors 接口兼容
def format_kline(kline: pd.DataFrame, freq: Freq) -> List[RawBar]:
    """格式化K线数据（兼容接口）
    
    :param kline: DataFrame，包含K线数据
    :param freq: K线周期
    :return: RawBar 列表
    """
    from czsc.akshare.base import format_akshare_to_rawbar
    
    if kline is None or len(kline) == 0:
        return []
    
    # 假设第一行包含symbol信息，或者从参数传入
    symbol = kline.get('symbol', 'UNKNOWN').iloc[0] if 'symbol' in kline.columns else 'UNKNOWN'
    return format_akshare_to_rawbar(kline, symbol, freq)


if __name__ == "__main__":
    # 测试获取标的列表
    symbols = get_symbols("all")
    print(f"获取到 {len(symbols)} 个标的")
    if len(symbols) > 0:
        print(f"前5个标的: {symbols[:5]}")
    
    # 测试获取K线数据
    if len(symbols) > 0:
        test_symbol = symbols[0]
        print(f"\n测试获取 {test_symbol} 的K线数据...")
        bars = get_raw_bars(test_symbol, Freq.D, "20230101", "20231231")
        print(f"获取到 {len(bars)} 根K线")
        if len(bars) > 0:
            print(f"第一根K线: {bars[0]}")
            print(f"最后一根K线: {bars[-1]}")

