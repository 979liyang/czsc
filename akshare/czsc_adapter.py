# -*- coding: utf-8 -*-
"""
CZSC 数据适配器

从 MySQL 数据库读取数据并转换为 CZSC 所需的 RawBar 格式
提供与 czsc.connectors 类似的接口
"""
import pandas as pd
from datetime import datetime
from typing import List, Optional
from loguru import logger
from czsc.objects import RawBar, Freq
from czsc.akshare.database import get_db_manager, StockKline
from czsc.akshare.base import normalize_stock_code


def get_symbols(name: str = "all", **kwargs) -> List[str]:
    """获取标的代码列表
    
    :param name: 标的类别
        - "all": 所有股票
        - "sh": 上证股票
        - "sz": 深证股票
        - "cyb": 创业板股票
    :param kwargs: 其他参数
    :return: 标的代码列表，格式：["000001.SZ", "600000.SH", ...]
    """
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
            # 创业板股票代码以3开头，在深圳市场
            stocks = session.query(StockKline.symbol).filter(
                StockKline.symbol.like('3%.SZ')
            ).distinct().all()
        else:
            logger.warning(f"不支持的标的类别: {name}")
            return []
        
        symbols = [stock[0] for stock in stocks]
        logger.info(f"获取 {name} 标的列表完成，共 {len(symbols)} 个")
        return symbols
    except Exception as e:
        logger.error(f"获取标的列表失败: {e}")
        return []
    finally:
        session.close()


def get_raw_bars(symbol: str, freq: Freq, sdt: str, edt: str, 
                fq: str = "前复权", **kwargs) -> List[RawBar]:
    """从数据库获取K线数据并转换为 RawBar 格式
    
    :param symbol: 标的代码，支持格式："000001"、"000001.SZ"
    :param freq: K线周期
    :param sdt: 开始时间，格式：YYYYMMDD 或 YYYY-MM-DD
    :param edt: 结束时间，格式：YYYYMMDD 或 YYYY-MM-DD
    :param fq: 复权类型，"前复权" 或 "后复权"
    :param kwargs: 其他参数
    :return: RawBar 列表
    """
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        # 标准化股票代码
        normalized_symbol = normalize_stock_code(symbol)
        
        # 转换频率字符串
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
                sdt = datetime.strptime(sdt, "%Y%m%d")
            else:  # YYYY-MM-DD
                sdt = datetime.strptime(sdt, "%Y-%m-%d")
        
        if isinstance(edt, str):
            if len(edt) == 8:  # YYYYMMDD
                edt = datetime.strptime(edt, "%Y%m%d")
            else:  # YYYY-MM-DD
                edt = datetime.strptime(edt, "%Y-%m-%d")
        
        # 查询数据
        query = session.query(StockKline).filter(
            StockKline.symbol == normalized_symbol,
            StockKline.freq == db_freq,
            StockKline.adjust == adjust,
            StockKline.dt >= sdt,
            StockKline.dt <= edt
        ).order_by(StockKline.dt.asc())
        
        klines = query.all()
        
        if len(klines) == 0:
            logger.warning(f"未找到 {normalized_symbol} {db_freq} 的数据")
            return []
        
        # 转换为 RawBar
        bars = []
        for i, kline in enumerate(klines):
            bar = RawBar(
                symbol=kline.symbol,
                id=i,
                dt=kline.dt,
                freq=freq,
                open=kline.open,
                close=kline.close,
                high=kline.high,
                low=kline.low,
                vol=kline.vol,
                amount=kline.amount
            )
            bars.append(bar)
        
        logger.info(f"从数据库获取 {normalized_symbol} {db_freq} 数据完成，共 {len(bars)} 根K线")
        return bars
        
    except Exception as e:
        logger.error(f"获取K线数据失败: {symbol}, {e}")
        return []
    finally:
        session.close()


def get_latest_bar(symbol: str, freq: Freq, fq: str = "前复权") -> Optional[RawBar]:
    """获取最新的K线数据
    
    :param symbol: 标的代码
    :param freq: K线周期
    :param fq: 复权类型
    :return: 最新的 RawBar，如果没有则返回 None
    """
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        normalized_symbol = normalize_stock_code(symbol)
        
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
        
        adjust_map = {
            "前复权": "qfq",
            "后复权": "hfq",
            "不复权": "none"
        }
        adjust = adjust_map.get(fq, "qfq")
        
        kline = session.query(StockKline).filter(
            StockKline.symbol == normalized_symbol,
            StockKline.freq == db_freq,
            StockKline.adjust == adjust
        ).order_by(StockKline.dt.desc()).first()
        
        if kline is None:
            return None
        
        bar = RawBar(
            symbol=kline.symbol,
            id=0,
            dt=kline.dt,
            freq=freq,
            open=kline.open,
            close=kline.close,
            high=kline.high,
            low=kline.low,
            vol=kline.vol,
            amount=kline.amount
        )
        
        return bar
        
    except Exception as e:
        logger.error(f"获取最新K线数据失败: {symbol}, {e}")
        return None
    finally:
        session.close()


def check_data_availability(symbol: str, freq: Freq, fq: str = "前复权") -> dict:
    """检查数据可用性
    
    :param symbol: 标的代码
    :param freq: K线周期
    :param fq: 复权类型
    :return: 数据可用性信息字典
    """
    db_manager = get_db_manager()
    session = db_manager.get_session()
    
    try:
        normalized_symbol = normalize_stock_code(symbol)
        
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
        
        adjust_map = {
            "前复权": "qfq",
            "后复权": "hfq",
            "不复权": "none"
        }
        adjust = adjust_map.get(fq, "qfq")
        
        # 查询数据范围
        result = session.query(
            StockKline.dt.min().label('min_dt'),
            StockKline.dt.max().label('max_dt'),
            StockKline.id.count().label('count')
        ).filter(
            StockKline.symbol == normalized_symbol,
            StockKline.freq == db_freq,
            StockKline.adjust == adjust
        ).first()
        
        if result and result.count > 0:
            return {
                'available': True,
                'min_date': result.min_dt,
                'max_date': result.max_dt,
                'count': result.count
            }
        else:
            return {
                'available': False,
                'min_date': None,
                'max_date': None,
                'count': 0
            }
            
    except Exception as e:
        logger.error(f"检查数据可用性失败: {symbol}, {e}")
        return {
            'available': False,
            'min_date': None,
            'max_date': None,
            'count': 0
        }
    finally:
        session.close()


# 为了与 czsc.connectors 接口兼容，提供类似的函数
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

