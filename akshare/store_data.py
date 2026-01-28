# -*- coding: utf-8 -*-
"""
将股票数据存储到 MySQL 数据库

从 AkShare 获取数据后，存储到 MySQL 数据库中
"""
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger
from sqlalchemy.exc import IntegrityError
from czsc.akshare.database import get_db_manager, StockInfo, StockKline
from czsc.akshare.fetch_data import get_stock_list_by_market, get_stock_info, fetch_historical_data, batch_fetch_stocks
from czsc.akshare.base import normalize_stock_code


def store_stock_info(stock_info: Dict, db_manager=None) -> bool:
    """存储股票基本信息
    
    :param stock_info: 股票信息字典，包含 symbol, code, name, market 等字段
    :param db_manager: 数据库管理器，如果不提供则使用默认实例
    :return: 是否成功
    """
    if db_manager is None:
        db_manager = get_db_manager()
    
    session = db_manager.get_session()
    try:
        # 检查是否已存在
        existing = session.query(StockInfo).filter_by(symbol=stock_info['symbol']).first()
        
        if existing:
            # 更新现有记录
            for key, value in stock_info.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.now()
            logger.debug(f"更新股票信息: {stock_info['symbol']}")
        else:
            # 创建新记录
            stock = StockInfo(**stock_info)
            session.add(stock)
            logger.debug(f"添加股票信息: {stock_info['symbol']}")
        
        session.commit()
        return True
    except IntegrityError as e:
        session.rollback()
        logger.warning(f"存储股票信息失败（可能已存在）: {stock_info['symbol']}, {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"存储股票信息失败: {stock_info['symbol']}, {e}")
        return False
    finally:
        session.close()


def store_kline_data(symbol: str, df: pd.DataFrame, freq: str, adjust: str = "qfq", 
                    db_manager=None, replace: bool = False) -> int:
    """存储K线数据到数据库
    
    :param symbol: 股票代码，格式：000001.SZ
    :param df: K线数据DataFrame
    :param freq: K线周期：1min, 5min, 15min, 30min, 60min, D, W, M
    :param adjust: 复权类型：qfq, hfq, none
    :param db_manager: 数据库管理器
    :param replace: 是否替换已存在的数据（删除后重新插入）
    :return: 成功存储的记录数
    """
    if db_manager is None:
        db_manager = get_db_manager()
    
    if df is None or len(df) == 0:
        logger.warning(f"K线数据为空: {symbol}")
        return 0
    
    session = db_manager.get_session()
    stored_count = 0
    
    try:
        # 标准化股票代码
        normalized_symbol = normalize_stock_code(symbol)
        
        # 如果需要替换，先删除已存在的数据
        if replace:
            deleted = session.query(StockKline).filter_by(
                symbol=normalized_symbol,
                freq=freq,
                adjust=adjust
            ).delete()
            if deleted > 0:
                logger.info(f"删除 {normalized_symbol} {freq} 已存在数据 {deleted} 条")
        
        # 确定时间列名
        time_col = None
        for col in ['日期', '时间', 'date', 'time', 'datetime', '交易日期']:
            if col in df.columns:
                time_col = col
                break
        
        if time_col is None:
            raise ValueError(f"无法找到时间列，当前列名：{df.columns.tolist()}")
        
        # 确定价格列名
        col_mapping = {
            'open': ['开盘', 'open', '开盘价'],
            'close': ['收盘', 'close', '收盘价'],
            'high': ['最高', 'high', '最高价'],
            'low': ['最低', 'low', '最低价'],
            'vol': ['成交量', 'volume', 'vol', '成交额'],
            'amount': ['成交额', 'amount', '成交金额']
        }
        
        col_names = {}
        for key, possible_names in col_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    col_names[key] = name
                    break
        
        # 检查必需的列
        required_cols = ['open', 'close', 'high', 'low']
        missing_cols = [col for col in required_cols if col not in col_names]
        if missing_cols:
            raise ValueError(f"缺少必需的列：{missing_cols}")
        
        # 转换并存储数据
        for _, row in df.iterrows():
            try:
                dt = pd.to_datetime(row[time_col])
                
                kline = StockKline(
                    symbol=normalized_symbol,
                    dt=dt,
                    freq=freq,
                    open=float(row[col_names['open']]),
                    close=float(row[col_names['close']]),
                    high=float(row[col_names['high']]),
                    low=float(row[col_names['low']]),
                    vol=float(row.get(col_names.get('vol', 'vol'), 0)),
                    amount=float(row.get(col_names.get('amount', 'amount'), 0)),
                    adjust=adjust
                )
                
                # 检查是否已存在（避免重复插入）
                existing = session.query(StockKline).filter_by(
                    symbol=normalized_symbol,
                    dt=dt,
                    freq=freq,
                    adjust=adjust
                ).first()
                
                if not existing:
                    session.add(kline)
                    stored_count += 1
                    
            except Exception as e:
                logger.warning(f"存储单条K线数据失败: {e}")
                continue
        
        session.commit()
        logger.info(f"存储 {normalized_symbol} {freq} K线数据完成，共 {stored_count} 条")
        return stored_count
        
    except Exception as e:
        session.rollback()
        logger.error(f"存储K线数据失败: {symbol}, {e}")
        return 0
    finally:
        session.close()


def batch_store_stocks(stock_codes: List[str], start_date: str = None, 
                      end_date: str = None, adjust: str = "qfq",
                      freq: str = "D", delay: float = 0.1,
                      db_manager=None) -> Dict[str, int]:
    """批量获取并存储股票数据
    
    :param stock_codes: 股票代码列表
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型
    :param freq: K线周期
    :param delay: 每次请求之间的延迟（秒）
    :param db_manager: 数据库管理器
    :return: 字典，key为股票代码，value为成功存储的记录数
    """
    from czsc.akshare.fetch_data import fetch_historical_data
    import time
    
    if db_manager is None:
        db_manager = get_db_manager()
    
    results = {}
    total = len(stock_codes)
    
    logger.info(f"开始批量获取并存储 {total} 只股票的数据...")
    
    for i, code in enumerate(stock_codes, 1):
        try:
            # 获取股票信息
            stock_info = get_stock_info(code)
            if stock_info:
                store_stock_info(stock_info, db_manager)
            
            # 获取历史数据
            df = fetch_historical_data(code, start_date, end_date, adjust)
            if df is not None and len(df) > 0:
                stored_count = store_kline_data(code, df, freq, adjust, db_manager)
                results[code] = stored_count
                logger.info(f"进度: {i}/{total} - {code} 存储成功，共 {stored_count} 条")
            else:
                logger.warning(f"进度: {i}/{total} - {code} 数据获取失败或为空")
                results[code] = 0
                
        except Exception as e:
            logger.error(f"进度: {i}/{total} - {code} 处理异常: {e}")
            results[code] = 0
        
        # 添加延迟
        if i < total:
            time.sleep(delay)
    
    success_count = sum(1 for v in results.values() if v > 0)
    logger.info(f"批量存储完成，成功存储 {success_count}/{total} 只股票的数据")
    return results


def sync_all_stocks(markets: List[str] = None, start_date: str = None, 
                    end_date: str = None, adjust: str = "qfq",
                    freq: str = "D", delay: float = 0.1) -> Dict[str, int]:
    """同步所有股票数据到数据库
    
    :param markets: 要同步的市场列表，如 ['sh', 'sz', 'cyb']，如果不提供则同步所有市场
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型
    :param freq: K线周期
    :param delay: 每次请求之间的延迟（秒）
    :return: 字典，key为股票代码，value为成功存储的记录数
    """
    # 初始化数据库
    db_manager = get_db_manager()
    db_manager.create_tables()
    
    # 获取股票列表
    stocks = get_stock_list_by_market()
    
    if markets is None:
        markets = ['sh', 'sz', 'cyb']
    
    all_codes = []
    for market in markets:
        if market in stocks:
            all_codes.extend(stocks[market])
    
    logger.info(f"开始同步 {len(all_codes)} 只股票的数据（市场：{markets}）...")
    
    # 批量存储
    results = batch_store_stocks(
        all_codes, 
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
        freq=freq,
        delay=delay,
        db_manager=db_manager
    )
    
    return results


if __name__ == "__main__":
    # 测试存储单只股票数据
    test_code = "000001"
    logger.info(f"测试存储 {test_code} 的数据...")
    
    # 初始化数据库
    db_manager = get_db_manager()
    db_manager.create_tables()
    
    # 获取并存储股票信息
    stock_info = get_stock_info(test_code)
    if stock_info:
        store_stock_info(stock_info, db_manager)
        print(f"股票信息存储成功: {stock_info}")
    
    # 获取并存储K线数据
    df = fetch_historical_data(test_code, "20230101", "20231231")
    if df is not None:
        count = store_kline_data(test_code, df, "D", "qfq", db_manager)
        print(f"K线数据存储成功，共 {count} 条")

