# -*- coding: utf-8 -*-
"""
使用 AkShare 获取股票历史数据

支持获取：
- 上证股票（代码以6开头）
- 深证股票（代码以0开头）
- 创业板股票（代码以3开头）
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from loguru import logger
import time
from czsc.akshare.base import normalize_stock_code, get_akshare_code


def get_stock_list_by_market() -> Dict[str, List[str]]:
    """获取按市场分类的股票列表
    
    :return: 字典，包含 'sh'（上证）、'sz'（深证）、'cyb'（创业板）三个市场的股票代码列表
    """
    try:
        logger.info("开始获取A股股票列表...")
        df = ak.stock_info_a_code_name()
        
        if df is None or len(df) == 0:
            logger.warning("未获取到股票列表")
            return {'sh': [], 'sz': [], 'cyb': []}
        
        stocks = {
            'sh': [],  # 上证股票（6开头）
            'sz': [],  # 深证股票（0开头，非3开头）
            'cyb': []  # 创业板股票（3开头）
        }
        
        for _, row in df.iterrows():
            code = str(row['code']).strip()
            if code.startswith('6'):
                stocks['sh'].append(code)
            elif code.startswith('3'):
                stocks['cyb'].append(code)
            elif code.startswith('0'):
                stocks['sz'].append(code)
        
        logger.info(f"获取股票列表完成：上证 {len(stocks['sh'])} 只，深证 {len(stocks['sz'])} 只，创业板 {len(stocks['cyb'])} 只")
        return stocks
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise


def get_stock_info(code: str) -> Optional[Dict]:
    """获取股票基本信息
    
    :param code: 股票代码，如 "000001"
    :return: 股票信息字典
    """
    try:
        # 获取股票基本信息
        df = ak.stock_info_a_code_name()
        if df is None or len(df) == 0:
            return None
        
        stock_info = df[df['code'] == code]
        if len(stock_info) == 0:
            return None
        
        row = stock_info.iloc[0]
        normalized_code = normalize_stock_code(code)
        
        # 判断市场
        if code.startswith('6'):
            market = 'SH'
        elif code.startswith('3'):
            market = 'CYB'
        else:
            market = 'SZ'
        
        return {
            'symbol': normalized_code,
            'code': code,
            'name': row.get('name', ''),
            'market': market
        }
    except Exception as e:
        logger.error(f"获取股票 {code} 信息失败: {e}")
        return None


def fetch_historical_data(code: str, start_date: str = None, end_date: str = None, 
                         adjust: str = "qfq", max_retry: int = 3) -> Optional[pd.DataFrame]:
    """获取股票历史日线数据
    
    :param code: 股票代码，如 "000001"
    :param start_date: 开始日期，格式：YYYYMMDD，如果不提供则获取最近1年数据
    :param end_date: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :param max_retry: 最大重试次数
    :return: DataFrame，包含历史K线数据
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    if start_date is None:
        # 默认获取最近1年数据
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    akshare_code = get_akshare_code(normalize_stock_code(code))
    
    for attempt in range(max_retry):
        try:
            logger.info(f"获取 {code} 历史数据：{start_date} - {end_date} (尝试 {attempt + 1}/{max_retry})")
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df is not None and len(df) > 0:
                # 标准化列名
                df.columns = df.columns.str.strip()
                logger.info(f"获取 {code} 历史数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning(f"获取 {code} 历史数据为空")
                return None
                
        except Exception as e:
            if attempt < max_retry - 1:
                wait_time = (attempt + 1) * 2  # 递增等待时间
                logger.warning(f"获取 {code} 数据失败，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"获取 {code} 历史数据失败（已重试{max_retry}次）: {e}")
                return None
    
    return None


def fetch_minute_data(code: str, period: str = "1", adjust: str = "qfq", 
                     max_retry: int = 3) -> Optional[pd.DataFrame]:
    """获取股票分钟数据
    
    :param code: 股票代码，如 "000001"
    :param period: 周期，"1": 1分钟, "5": 5分钟, "15": 15分钟, "30": 30分钟, "60": 60分钟
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :param max_retry: 最大重试次数
    :return: DataFrame，包含分钟K线数据
    """
    akshare_code = get_akshare_code(normalize_stock_code(code))
    
    for attempt in range(max_retry):
        try:
            logger.info(f"获取 {code} {period}分钟数据 (尝试 {attempt + 1}/{max_retry})")
            df = ak.stock_zh_a_minute(
                symbol=akshare_code,
                period=period,
                adjust=adjust
            )
            
            if df is not None and len(df) > 0:
                logger.info(f"获取 {code} {period}分钟数据成功，共 {len(df)} 条记录")
                return df
            else:
                logger.warning(f"获取 {code} {period}分钟数据为空")
                return None
                
        except Exception as e:
            if attempt < max_retry - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"获取 {code} 分钟数据失败，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                logger.error(f"获取 {code} 分钟数据失败（已重试{max_retry}次）: {e}")
                return None
    
    return None


def batch_fetch_stocks(stock_codes: List[str], start_date: str = None, 
                      end_date: str = None, adjust: str = "qfq",
                      delay: float = 0.1) -> Dict[str, pd.DataFrame]:
    """批量获取股票历史数据
    
    :param stock_codes: 股票代码列表
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型
    :param delay: 每次请求之间的延迟（秒），避免请求过快
    :return: 字典，key为股票代码，value为DataFrame
    """
    results = {}
    total = len(stock_codes)
    
    logger.info(f"开始批量获取 {total} 只股票的历史数据...")
    
    for i, code in enumerate(stock_codes, 1):
        try:
            df = fetch_historical_data(code, start_date, end_date, adjust)
            if df is not None and len(df) > 0:
                results[code] = df
                logger.info(f"进度: {i}/{total} - {code} 数据获取成功")
            else:
                logger.warning(f"进度: {i}/{total} - {code} 数据获取失败或为空")
        except Exception as e:
            logger.error(f"进度: {i}/{total} - {code} 数据获取异常: {e}")
        
        # 添加延迟，避免请求过快
        if i < total:
            time.sleep(delay)
    
    logger.info(f"批量获取完成，成功获取 {len(results)}/{total} 只股票的数据")
    return results


if __name__ == "__main__":
    # 测试获取股票列表
    stocks = get_stock_list_by_market()
    print(f"上证股票数量: {len(stocks['sh'])}")
    print(f"深证股票数量: {len(stocks['sz'])}")
    print(f"创业板股票数量: {len(stocks['cyb'])}")
    
    # 测试获取单只股票数据
    if len(stocks['sh']) > 0:
        test_code = stocks['sh'][0]
        print(f"\n测试获取 {test_code} 的历史数据...")
        df = fetch_historical_data(test_code, "20230101", "20231231")
        if df is not None:
            print(f"获取成功，共 {len(df)} 条记录")
            print(df.head())

