# -*- coding: utf-8 -*-
"""
AkShare数据客户端

封装AkShare API调用，提供统一的股票数据获取接口
"""
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
import pandas as pd
import akshare as ak
import time
from loguru import logger


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码格式
    
    :param code: 股票代码，如 "000001" 或 "000001.SZ"
    :return: 标准化后的代码，如 "000001.SZ"
    """
    code = code.upper().strip()
    if '.' in code:
        return code
    if code.startswith('6'):
        return f"{code}.SH"
    elif code.startswith(('0', '3')):
        return f"{code}.SZ"
    return f"{code}.SZ"


def get_akshare_code(code: str) -> str:
    """
    获取AkShare格式的股票代码
    
    :param code: 股票代码，如 "000001.SZ"
    :return: AkShare格式代码，如 "sz000001"
    """
    if '.' in code:
        code, market = code.split('.')
        return f"{market.lower()}{code}"
    return code


def get_stock_list_by_market() -> Dict[str, List[str]]:
    """
    获取按市场分类的股票列表
    
    :return: 字典，包含 'sh'（上证）、'sz'（深证）、'cyb'（创业板）三个市场的股票代码列表
    """
    df = ak.stock_info_a_code_name()
    stocks = {'sh': [], 'sz': [], 'cyb': []}
    for _, row in df.iterrows():
        code = str(row['code']).strip()
        if code.startswith('6'):
            stocks['sh'].append(code)
        elif code.startswith('3'):
            stocks['cyb'].append(code)
        elif code.startswith('0'):
            stocks['sz'].append(code)
    return stocks


def fetch_historical_data(code: str, start_date: str, end_date: str, adjust: str = "qfq") -> Optional[pd.DataFrame]:
    """
    获取股票历史日线数据
    
    :param code: 股票代码，如 "000001"
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :return: DataFrame，包含历史K线数据
    """
    return ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust
    )


def get_stock_info(code: str) -> Optional[Dict]:
    """
    获取股票基本信息
    
    :param code: 股票代码，如 "000001"
    :return: 股票信息字典
    """
    df = ak.stock_info_a_code_name()
    stock_info = df[df['code'] == code]
    if len(stock_info) == 0:
        return None
    row = stock_info.iloc[0]
    market = 'SH' if code.startswith('6') else ('CYB' if code.startswith('3') else 'SZ')
    return {
        'symbol': normalize_stock_code(code),
        'code': code,
        'name': row.get('name', ''),
        'market': market
    }


def fetch_minute_data(code: str, period: str = "1", adjust: str = "qfq", max_retry: int = 3, 
                     start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """
    获取股票分钟级别K线数据
    
    :param code: 股票代码，如 "000001"
    :param period: 周期，"1": 1分钟, "5": 5分钟, "15": 15分钟, "30": 30分钟, "60": 60分钟
    :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
    :param max_retry: 最大重试次数
    :param start_date: 开始日期，格式：YYYYMMDD，如果不提供则使用30天前
    :param end_date: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
    :return: DataFrame，包含分钟K线数据
    """
    # 重要：ak.stock_zh_a_hist_min_em 的 symbol 参数需要传“纯数字代码”（如 600078）
    # 该函数内部会自行根据首位数字判断市场并拼接 secid=市场代码.股票代码
    # 如果传入 sh600078 这类带市场前缀的代码，会导致 secid 无效，从而返回 data=None 并触发 akshare 内部 TypeError
    akshare_symbol = str(code).split(".")[0].replace("sh", "").replace("sz", "").upper()
    
    start_date, end_date = _normalize_minute_date_range(start_date=start_date, end_date=end_date)
    if start_date is None or end_date is None:
        return None
    
    for attempt in range(max_retry):
        try:
            logger.info(f"获取 {code} {period}分钟数据 (尝试 {attempt + 1}/{max_retry})")
            logger.debug(
                f"  参数: symbol={akshare_symbol}, start_date={start_date}, end_date={end_date}, period={period}, adjust={adjust}"
            )
            
            # 调用 AKShare API
            df = ak.stock_zh_a_hist_min_em(
                symbol=akshare_symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                adjust=adjust
            )
            
            # 检查返回值：可能是 None、空 DataFrame 或有效 DataFrame
            if df is None:
                logger.warning(f"获取 {code} {period}分钟数据返回 None（可能是该股票在指定日期范围内没有分钟数据）")
                if attempt < max_retry - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"获取 {code} {period}分钟数据失败：API返回None，可能原因：")
                    logger.error(f"  1. 该股票在 {start_date} 至 {end_date} 期间没有交易数据")
                    logger.error(f"  2. 该股票可能已退市或停牌")
                    logger.error(f"  3. AKShare API 数据源暂时不可用")
                    return None
            elif not isinstance(df, pd.DataFrame):
                logger.error(f"获取 {code} {period}分钟数据返回了非DataFrame类型: {type(df)}")
                if attempt < max_retry - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    return None
            elif len(df) == 0:
                logger.warning(f"获取 {code} {period}分钟数据为空DataFrame（该股票在指定日期范围内可能没有分钟数据）")
                return None
            else:
                logger.info(f"获取 {code} {period}分钟数据成功，共 {len(df)} 条记录")
                return df
                
        except (TypeError, KeyError, AttributeError) as e:
            # 捕获 AKShare 库内部的错误（通常是 API 返回数据格式异常）
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"获取 {code} {period}分钟数据时发生 {error_type} 错误: {error_msg}")
            logger.error(f"  这通常表示：")
            logger.error(f"  1. AKShare API 返回的数据格式异常（data_json['data'] 为 None）")
            logger.error(f"  2. 该股票在 {start_date} 至 {end_date} 期间可能没有分钟数据")
            logger.error(f"  3. 股票代码格式可能不正确（当前使用: {akshare_symbol}）")
            
            if attempt < max_retry - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"{wait_time}秒后重试...")
                time.sleep(wait_time)
            else:
                logger.error(f"获取 {code} {period}分钟数据失败（已重试{max_retry}次）")
                logger.error(f"  建议：")
                logger.error(f"  - 检查股票代码是否正确（当前: {code} -> {akshare_symbol}）")
                logger.error(f"  - 尝试使用更近的日期范围（分钟数据通常只能获取最近的数据）")
                logger.error(f"  - 检查该股票是否在指定日期范围内有交易")
                # 只在调试模式下记录详细 traceback
                import traceback
                logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
                return None
        except Exception as e:
            # 捕获其他所有异常
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"获取 {code} {period}分钟数据时发生 {error_type} 错误: {error_msg}")
            
            if attempt < max_retry - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"获取 {code} 分钟数据失败，{wait_time}秒后重试: {error_msg}")
                time.sleep(wait_time)
            else:
                logger.error(f"获取 {code} 分钟数据失败（已重试{max_retry}次）: {error_msg}")
                # 只在调试模式下记录详细 traceback
                import traceback
                logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
                return None
    
    return None


def _normalize_minute_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """标准化分钟数据日期范围（尽量对齐到交易日）

    - end_date 默认取今天；若今天为非交易日（如周末），自动回退到最近交易日
    - start_date 默认取 end_date 往前 5 个交易日（AKShare 分钟数据常见限制）

    :param start_date: 开始日期 YYYYMMDD 或 YYYY-MM-DD
    :param end_date: 结束日期 YYYYMMDD 或 YYYY-MM-DD
    :return: (start_date, end_date) 统一为 YYYYMMDD；若解析失败返回 (None, None)
    """
    from czsc.utils.calendar import get_trading_dates

    def _clean(x: Optional[str]) -> Optional[str]:
        return x.replace("-", "") if x else None

    def _safe_find_nearest_trading_date(target_dt: datetime, lookback_days: int = 60) -> datetime:
        """安全地查找最近的交易日（如果日期不在日历范围内，使用自然日回退）"""
        try:
            # 尝试在日历范围内查找交易日（扩大查找范围）
            sdt0 = target_dt - timedelta(days=lookback_days)
            trade_dates = get_trading_dates(sdt=sdt0, edt=target_dt)
            if trade_dates:
                # 找到最近的交易日（小于等于目标日期）
                valid_dates = [d for d in trade_dates if pd.to_datetime(d) <= target_dt]
                if valid_dates:
                    nearest = pd.to_datetime(valid_dates[-1])
                    # 如果找到的日期太早（超过30天），说明日历数据可能不包含目标日期
                    if (target_dt - nearest).days <= 30:
                        return nearest
                    else:
                        logger.warning(f"日期 {target_dt.strftime('%Y%m%d')} 不在交易日历范围内（最近交易日为 {nearest.strftime('%Y%m%d')}），使用自然日回退")
                else:
                    # 如果所有交易日都晚于目标日期，取最早的交易日
                    if trade_dates:
                        earliest = pd.to_datetime(trade_dates[0])
                        logger.warning(f"日期 {target_dt.strftime('%Y%m%d')} 早于交易日历范围（最早交易日为 {earliest.strftime('%Y%m%d')}），使用自然日回退")
                    else:
                        logger.warning(f"日期 {target_dt.strftime('%Y%m%d')} 不在交易日历范围内，使用自然日回退")
            else:
                logger.warning(f"日期 {target_dt.strftime('%Y%m%d')} 不在交易日历范围内，使用自然日回退")
            
            # 如果找不到，回退到自然日（往前推，直到找到工作日，但最多回退7天）
            # 注意：这里只回退到最近的工作日，不会回退太多天
            for i in range(0, 8):  # 从0开始，先检查今天
                candidate = target_dt - timedelta(days=i)
                if candidate.weekday() < 5:  # 周一到周五
                    if i > 0:
                        logger.info(f"使用自然日回退：{target_dt.strftime('%Y%m%d')} -> {candidate.strftime('%Y%m%d')} (回退{i}天)")
                    return candidate
            # 如果7天内都不是工作日，回退到最近的周一
            return target_dt - timedelta(days=target_dt.weekday())
        except Exception as e:
            logger.warning(f"查找交易日失败: {e}，使用自然日回退（最多7天）")
            # 回退到最近的工作日
            for i in range(0, 8):
                candidate = target_dt - timedelta(days=i)
                if candidate.weekday() < 5:
                    return candidate
            return target_dt - timedelta(days=target_dt.weekday())

    end_date = _clean(end_date)
    start_date = _clean(start_date)

    # 结束日期：默认今天，且不能为未来日期
    if end_date is None:
        end_dt = datetime.now()
    else:
        try:
            end_dt = datetime.strptime(end_date, "%Y%m%d")
        except ValueError:
            logger.error(f"无效的结束日期格式: {end_date}")
            return None, None

    today = datetime.now().date()
    if end_dt.date() > today:
        logger.warning(f"结束日期 {end_dt.strftime('%Y%m%d')} 是未来日期，调整为当前日期 {today.strftime('%Y%m%d')}")
        end_dt = datetime.combine(today, datetime.min.time())

    # 安全地回退到最近交易日（周末 / 节假日）
    end_dt = _safe_find_nearest_trading_date(end_dt)
    end_date = end_dt.strftime("%Y%m%d")

    # 开始日期：默认取最近 5 个交易日
    if start_date is None:
        sdt0 = end_dt - timedelta(days=40)
        try:
            trade_dates = get_trading_dates(sdt=sdt0, edt=end_dt)
            if trade_dates and len(trade_dates) >= 5:
                start_dt = pd.to_datetime(trade_dates[-5])
                start_date = start_dt.strftime("%Y%m%d")
                # 验证日期范围合理（不超过30天）
                if (end_dt - start_dt).days > 30:
                    logger.warning(f"交易日范围过大（{start_date} 至 {end_date}），使用自然日回退5天")
                    start_date = (end_dt - timedelta(days=5)).strftime("%Y%m%d")
            elif trade_dates:
                start_dt = pd.to_datetime(trade_dates[0])
                start_date = start_dt.strftime("%Y%m%d")
            else:
                # 如果找不到交易日，使用自然日回退5天（最多7天）
                logger.warning(f"无法从交易日历获取开始日期，使用自然日回退5天")
                start_date = (end_dt - timedelta(days=5)).strftime("%Y%m%d")
        except Exception as e:
            logger.warning(f"获取交易日列表失败: {e}，使用自然日回退5天")
            start_date = (end_dt - timedelta(days=5)).strftime("%Y%m%d")
        logger.info(f"未指定开始日期，使用默认值：最近5个交易日（{start_date} 至 {end_date}）")
    else:
        try:
            start_dt = datetime.strptime(start_date, "%Y%m%d")
        except ValueError:
            logger.error(f"无效的开始日期格式: {start_date}")
            return None, None
        if start_dt > end_dt:
            logger.warning(f"开始日期 {start_date} 晚于结束日期 {end_date}，交换日期")
            start_date, end_date = end_date, start_date

    return start_date, end_date


class AkShareClient:
    """AkShare数据客户端"""
    
    def __init__(self, max_retry: int = 3, delay: float = 0.1):
        """
        初始化客户端
        
        :param max_retry: 最大重试次数
        :param delay: 请求间隔（秒）
        """
        self.max_retry = max_retry
        self.delay = delay
        logger.info(f"AkShare客户端初始化完成，最大重试次数: {max_retry}, 请求间隔: {delay}秒")
    
    def get_stock_list_by_market(self) -> Dict[str, List[str]]:
        """
        获取按市场分类的股票列表
        
        :return: 字典，包含 'sh'（上证）、'sz'（深证）、'cyb'（创业板）三个市场的股票代码列表
        """
        try:
            logger.info("开始获取A股股票列表...")
            result = get_stock_list_by_market()
            logger.info(
                f"获取股票列表完成：上证 {len(result.get('sh', []))} 只，"
                f"深证 {len(result.get('sz', []))} 只，"
                f"创业板 {len(result.get('cyb', []))} 只"
            )
            return result
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            raise
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """
        获取股票基本信息
        
        :param code: 股票代码，如 "000001"
        :return: 股票信息字典
        """
        try:
            result = get_stock_info(code)
            if result:
                logger.debug(f"获取股票 {code} 信息成功: {result.get('name', '')}")
            return result
        except Exception as e:
            logger.error(f"获取股票 {code} 信息失败: {e}")
            return None
    
    def fetch_historical_data(
        self,
        code: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史日线数据
        
        :param code: 股票代码，如 "000001"
        :param start_date: 开始日期，格式：YYYYMMDD，如果不提供则获取最近1年数据
        :param end_date: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
        :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
        :return: DataFrame，包含历史K线数据
        """
        # 获取当前日期
        today = datetime.now()
        today_str = today.strftime("%Y%m%d")
        
        if end_date is None:
            end_date = today_str
        else:
            # 验证结束日期不能是未来日期
            try:
                end_dt = datetime.strptime(end_date, "%Y%m%d")
                if end_dt.date() > today.date():
                    logger.warning(f"结束日期 {end_date} 是未来日期，使用当前日期 {today_str}")
                    end_date = today_str
            except ValueError:
                logger.error(f"无效的结束日期格式: {end_date}")
                end_date = today_str
        
        if start_date is None:
            start_date = (today - timedelta(days=365)).strftime("%Y%m%d")
        else:
            # 验证开始日期不能是未来日期
            try:
                start_dt = datetime.strptime(start_date, "%Y%m%d")
                if start_dt.date() > today.date():
                    logger.warning(f"开始日期 {start_date} 是未来日期，使用默认值")
                    start_date = (today - timedelta(days=365)).strftime("%Y%m%d")
            except ValueError:
                logger.error(f"无效的开始日期格式: {start_date}")
                start_date = (today - timedelta(days=365)).strftime("%Y%m%d")
        
        # 验证日期范围
        try:
            start_dt = datetime.strptime(start_date, "%Y%m%d")
            end_dt = datetime.strptime(end_date, "%Y%m%d")
            if start_dt > end_dt:
                logger.error(f"开始日期 {start_date} 晚于结束日期 {end_date}，交换日期")
                start_date, end_date = end_date, start_date
        except ValueError:
            logger.error(f"日期格式验证失败: start_date={start_date}, end_date={end_date}")
            return None
        
        for attempt in range(self.max_retry):
            try:
                logger.info(f"获取 {code} 历史数据：{start_date} - {end_date} (尝试 {attempt + 1}/{self.max_retry})")
                
                df = fetch_historical_data(code, start_date, end_date, adjust)
                
                if df is not None and len(df) > 0:
                    logger.info(f"获取 {code} 历史数据成功，共 {len(df)} 条记录")
                    time.sleep(self.delay)  # 请求间隔
                    return df
                else:
                    logger.warning(f"获取 {code} 历史数据为空")
                    return None
                    
            except Exception as e:
                error_msg = str(e)
                # 检查是否是网络连接错误
                if 'Connection' in error_msg or 'Remote' in error_msg or 'timeout' in error_msg.lower():
                    if attempt < self.max_retry - 1:
                        wait_time = (attempt + 1) * 3  # 网络错误时增加等待时间
                        logger.warning(f"网络连接错误，{wait_time}秒后重试: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"获取 {code} 历史数据失败（网络错误，已重试{self.max_retry}次）: {e}")
                        return None
                else:
                    if attempt < self.max_retry - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"获取 {code} 数据失败，{wait_time}秒后重试: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"获取 {code} 历史数据失败（已重试{self.max_retry}次）: {e}")
                        return None
        
        return None
    
    def collect_historical_data_by_market(
        self,
        market: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        按市场批量获取历史K线数据
        
        注意：此方法在 fetch_stock_data.py 中未使用，保留用于其他场景
        
        :param market: 市场代码（SH/SZ/CY/ALL）
        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :param adjust: 复权类型
        :return: 字典，key为股票代码，value为DataFrame
        """
        # 延迟导入，避免不必要的依赖
        from backend.utils.market_utils import normalize_market_code
        
        # 标准化市场代码
        markets = normalize_market_code(market)
        if not markets:
            logger.warning(f"无效的市场代码: {market}")
            return {}
        
        # 获取股票列表
        stocks_by_market = self.get_stock_list_by_market()
        
        results = {}
        total_stocks = 0
        
        for market_code in markets:
            stock_codes = stocks_by_market.get(market_code, [])
            total_stocks += len(stock_codes)
            
            logger.info(f"开始获取 {market_code.upper()} 市场 {len(stock_codes)} 只股票的历史数据...")
            
            for i, code in enumerate(stock_codes, 1):
                try:
                    df = self.fetch_historical_data(code, start_date, end_date, adjust)
                    if df is not None and len(df) > 0:
                        results[code] = df
                        if i % 50 == 0:
                            logger.info(f"进度: {i}/{len(stock_codes)} - {market_code.upper()} 市场")
                    else:
                        logger.debug(f"股票 {code} 数据为空")
                except Exception as e:
                    logger.error(f"获取股票 {code} 历史数据失败: {e}")
                    results[code] = None
        
        logger.info(f"按市场获取历史数据完成，共处理 {total_stocks} 只股票，成功 {len([v for v in results.values() if v is not None])} 只")
        return results
    
    def clean_and_format_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        数据清洗和格式转换
        
        :param df: 原始DataFrame
        :return: 清洗后的DataFrame
        """
        if df is None or len(df) == 0:
            return None
        
        try:
            # 标准化列名
            df.columns = df.columns.str.strip()
            
            # 确保时间列存在
            time_col = None
            for col in ['时间', '日期', 'date', 'time', 'datetime', '日期时间']:
                if col in df.columns:
                    time_col = col
                    break
            
            if time_col is None:
                logger.error("无法找到时间列")
                return None
            
            # 转换时间列为datetime类型
            df[time_col] = pd.to_datetime(df[time_col])
            
            # 按时间排序
            df = df.sort_values(time_col, ascending=True).reset_index(drop=True)
            
            # 数据验证和清洗
            # 移除无效数据（价格为0或负数）
            price_cols = ['开盘', '收盘', '最高', '最低', 'open', 'close', 'high', 'low']
            for col in price_cols:
                if col in df.columns:
                    df = df[df[col] > 0]
            
            # 移除重复数据
            df = df.drop_duplicates(subset=[time_col], keep='first')
            
            logger.debug(f"数据清洗完成，剩余 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            return None
    
    def batch_fetch_stocks(
        self,
        stock_codes: List[str],
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取股票历史数据
        
        :param stock_codes: 股票代码列表
        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :param adjust: 复权类型
        :return: 字典，key为股票代码，value为DataFrame
        """
        results = {}
        total = len(stock_codes)
        
        logger.info(f"开始批量获取 {total} 只股票的历史数据...")
        
        for i, code in enumerate(stock_codes, 1):
            try:
                df = self.fetch_historical_data(code, start_date, end_date, adjust)
                if df is not None and len(df) > 0:
                    # 数据清洗
                    df = self.clean_and_format_data(df)
                    if df is not None:
                        results[code] = df
                        logger.info(f"进度: {i}/{total} - {code} 数据获取成功")
                else:
                    logger.warning(f"进度: {i}/{total} - {code} 数据获取失败或为空")
            except Exception as e:
                logger.error(f"进度: {i}/{total} - {code} 数据获取异常: {e}")
        
        logger.info(f"批量获取完成，成功获取 {len(results)}/{total} 只股票的数据")
        return results
    
    def fetch_minute_data(
        self,
        code: str,
        period: str = "1",
        adjust: str = "qfq",
        start_date: str = None,
        end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        获取股票分钟级别K线数据
        
        :param code: 股票代码，如 "000001"
        :param period: 周期，"1": 1分钟, "5": 5分钟, "15": 15分钟, "30": 30分钟, "60": 60分钟
        :param adjust: 复权类型，"qfq": 前复权, "hfq": 后复权, "": 不复权
        :param start_date: 开始日期，格式：YYYYMMDD，如果不提供则使用30天前
        :param end_date: 结束日期，格式：YYYYMMDD，如果不提供则使用当前日期
        :return: DataFrame，包含分钟K线数据
        """
        for attempt in range(self.max_retry):
            try:
                logger.info(f"获取 {code} {period}分钟数据：尝试 {attempt + 1}/{self.max_retry}")
                
                df = fetch_minute_data(code, period, adjust, max_retry=1, start_date=start_date, end_date=end_date)
                
                # 检查返回值：可能是 None、空 DataFrame 或有效 DataFrame
                if df is None:
                    logger.warning(f"获取 {code} {period}分钟数据返回 None")
                    if attempt < self.max_retry - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None
                elif not isinstance(df, pd.DataFrame):
                    logger.error(f"获取 {code} {period}分钟数据返回了非DataFrame类型: {type(df)}")
                    if attempt < self.max_retry - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return None
                elif len(df) == 0:
                    logger.warning(f"获取 {code} {period}分钟数据为空DataFrame")
                    return None
                else:
                    logger.info(f"获取 {code} {period}分钟数据成功，共 {len(df)} 条记录")
                    time.sleep(self.delay)  # 请求间隔
                    return df
                    
            except Exception as e:
                error_msg = str(e)
                if attempt < self.max_retry - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"获取 {code} 分钟数据失败，{wait_time}秒后重试: {error_msg}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"获取 {code} 分钟数据失败（已重试{self.max_retry}次）: {error_msg}")
                    # 只在调试模式下记录详细 traceback
                    import traceback
                    logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
                    return None
        
        return None
    
    def clean_and_format_minute_data(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> Optional[pd.DataFrame]:
        """
        清洗和格式化分钟K线数据，转换为标准格式（symbol, dt, open, close, high, low, vol, amount）
        
        :param df: 原始DataFrame（从AkShare获取的分钟数据）
        :param symbol: 股票代码（如：000008.SZ）
        :return: 清洗后的DataFrame
        """
        # 先检查是否为 None，避免对 None 调用 len()
        if df is None:
            logger.warning(f"clean_and_format_minute_data: 输入数据为 None")
            return None
        
        # 检查是否为空 DataFrame
        if not isinstance(df, pd.DataFrame):
            logger.error(f"clean_and_format_minute_data: 输入不是 DataFrame，而是 {type(df)}")
            return None
        
        if len(df) == 0:
            logger.warning(f"clean_and_format_minute_data: 输入数据为空")
            return None
        
        try:
            # 标准化列名
            df.columns = df.columns.str.strip()
            
            # 确保时间列存在（AkShare分钟数据使用'day'列）
            time_col = None
            for col in ['day', '时间', '日期', 'date', 'time', 'datetime', '日期时间', 'trade_time', 'dt']:
                if col in df.columns:
                    time_col = col
                    break
            
            if time_col is None:
                logger.error(f"无法找到时间列，可用列: {list(df.columns)}")
                return None
            
            # 转换时间列为datetime类型
            df[time_col] = pd.to_datetime(df[time_col])
            
            # 列名映射（从AkShare格式转换为标准格式）
            # 注意：AkShare分钟数据可能没有'amount'列，只有'volume'
            col_mapping = {
                'open': ['开盘', 'open', '开盘价'],
                'close': ['收盘', 'close', '收盘价'],
                'high': ['最高', 'high', '最高价'],
                'low': ['最低', 'low', '最低价'],
                'vol': ['成交量', 'volume', 'vol', '成交量（股）'],
                'amount': ['成交额', 'amount', '成交金额', 'turnover', '成交额（元）']
            }
            
            # 构建标准格式的DataFrame
            result_data = {
                'symbol': symbol,
                'dt': df[time_col]
            }
            
            # 映射价格和成交量列
            for target_col, possible_names in col_mapping.items():
                found = False
                for name in possible_names:
                    if name in df.columns:
                        result_data[target_col] = df[name]
                        found = True
                        break
                if not found:
                    # amount列可能不存在（AkShare分钟数据可能只有volume）
                    if target_col == 'amount':
                        logger.debug(f"未找到amount列，将通过 vol * close 估算成交额")
                        # 如果存在close和vol，通过 vol * close 估算成交额
                        if 'close' in result_data and 'vol' in df.columns:
                            vol_col = None
                            for vol_name in col_mapping['vol']:
                                if vol_name in df.columns:
                                    vol_col = vol_name
                                    break
                            if vol_col:
                                result_data[target_col] = df[vol_col] * result_data['close']
                            else:
                                result_data[target_col] = 0
                        else:
                            result_data[target_col] = 0
                    else:
                        logger.warning(f"未找到列: {target_col}，将设为None")
                        result_data[target_col] = None
            
            # 创建新的DataFrame
            result_df = pd.DataFrame(result_data)
            
            # 数据验证和清洗
            original_count = len(result_df)
            validation_issues = []
            
            # 1. 移除无效数据（价格为0或负数）
            price_cols = ['open', 'close', 'high', 'low']
            for col in price_cols:
                if col in result_df.columns:
                    invalid_count = len(result_df[result_df[col] <= 0])
                    if invalid_count > 0:
                        validation_issues.append(f"{col}列有{invalid_count}条无效数据（<=0）")
                        result_df = result_df[result_df[col] > 0]
            
            # 2. 价格范围检查（价格应该在合理范围内，如0.01到10000）
            MIN_PRICE = 0.01
            MAX_PRICE = 10000.0
            for col in price_cols:
                if col in result_df.columns:
                    invalid_range = result_df[(result_df[col] < MIN_PRICE) | (result_df[col] > MAX_PRICE)]
                    if len(invalid_range) > 0:
                        validation_issues.append(f"{col}列有{len(invalid_range)}条数据超出合理范围（{MIN_PRICE}-{MAX_PRICE}）")
                        result_df = result_df[(result_df[col] >= MIN_PRICE) & (result_df[col] <= MAX_PRICE)]
            
            # 3. 验证价格合理性（high >= low, high >= open, high >= close, low <= open, low <= close）
            if 'high' in result_df.columns and 'low' in result_df.columns:
                invalid_high_low = len(result_df[result_df['high'] < result_df['low']])
                if invalid_high_low > 0:
                    validation_issues.append(f"有{invalid_high_low}条数据high < low")
                    result_df = result_df[result_df['high'] >= result_df['low']]
            if 'high' in result_df.columns and 'open' in result_df.columns:
                invalid_high_open = len(result_df[result_df['high'] < result_df['open']])
                if invalid_high_open > 0:
                    validation_issues.append(f"有{invalid_high_open}条数据high < open")
                    result_df = result_df[result_df['high'] >= result_df['open']]
            if 'high' in result_df.columns and 'close' in result_df.columns:
                invalid_high_close = len(result_df[result_df['high'] < result_df['close']])
                if invalid_high_close > 0:
                    validation_issues.append(f"有{invalid_high_close}条数据high < close")
                    result_df = result_df[result_df['high'] >= result_df['close']]
            if 'low' in result_df.columns and 'open' in result_df.columns:
                invalid_low_open = len(result_df[result_df['low'] > result_df['open']])
                if invalid_low_open > 0:
                    validation_issues.append(f"有{invalid_low_open}条数据low > open")
                    result_df = result_df[result_df['low'] <= result_df['open']]
            if 'low' in result_df.columns and 'close' in result_df.columns:
                invalid_low_close = len(result_df[result_df['low'] > result_df['close']])
                if invalid_low_close > 0:
                    validation_issues.append(f"有{invalid_low_close}条数据low > close")
                    result_df = result_df[result_df['low'] <= result_df['close']]
            
            # 4. 数据一致性检查（同一时间点的数据是否一致）
            # 检查open/close/high/low之间的关系是否合理
            if all(col in result_df.columns for col in ['open', 'close', 'high', 'low']):
                # high应该是open、close、high中的最大值
                invalid_high = result_df[
                    (result_df['high'] < result_df['open']) | 
                    (result_df['high'] < result_df['close'])
                ]
                if len(invalid_high) > 0:
                    validation_issues.append(f"有{len(invalid_high)}条数据high不是最高价")
                    result_df = result_df[
                        (result_df['high'] >= result_df['open']) & 
                        (result_df['high'] >= result_df['close'])
                    ]
                # low应该是open、close、low中的最小值
                invalid_low = result_df[
                    (result_df['low'] > result_df['open']) | 
                    (result_df['low'] > result_df['close'])
                ]
                if len(invalid_low) > 0:
                    validation_issues.append(f"有{len(invalid_low)}条数据low不是最低价")
                    result_df = result_df[
                        (result_df['low'] <= result_df['open']) & 
                        (result_df['low'] <= result_df['close'])
                    ]
            
            # 5. 价格变化幅度检查（相邻K线的价格变化不应超过合理范围，如涨跌停限制）
            if len(result_df) > 1 and all(col in result_df.columns for col in ['close', 'dt']):
                result_df = result_df.sort_values('dt', ascending=True).reset_index(drop=True)
                # 计算相邻K线的价格变化百分比
                result_df['price_change_pct'] = result_df['close'].pct_change(fill_method=None) * 100
                # 涨跌停限制通常是±10%（ST股票是±5%）
                MAX_CHANGE_PCT = 12.0  # 允许稍微超过10%以处理特殊情况
                invalid_change = result_df[result_df['price_change_pct'].abs() > MAX_CHANGE_PCT]
                if len(invalid_change) > 0:
                    validation_issues.append(f"有{len(invalid_change)}条数据价格变化幅度异常（超过{MAX_CHANGE_PCT}%）")
                    # 不直接过滤，而是记录警告
                    logger.warning(f"发现{len(invalid_change)}条数据价格变化幅度异常，最大变化: {invalid_change['price_change_pct'].abs().max():.2f}%")
                result_df = result_df.drop(columns=['price_change_pct'], errors='ignore')
            
            # 6. 验证成交量（vol >= 0）
            if 'vol' in result_df.columns:
                # 如果volume是字符串类型，需要转换
                if result_df['vol'].dtype == 'object':
                    result_df['vol'] = pd.to_numeric(result_df['vol'], errors='coerce')
                invalid_vol = len(result_df[result_df['vol'] < 0])
                if invalid_vol > 0:
                    validation_issues.append(f"有{invalid_vol}条数据成交量<0")
                    result_df = result_df[result_df['vol'] >= 0]
            
            # 7. 验证成交额（amount >= 0，如果存在）
            if 'amount' in result_df.columns:
                invalid_amount = len(result_df[result_df['amount'] < 0])
                if invalid_amount > 0:
                    validation_issues.append(f"有{invalid_amount}条数据成交额<0")
                    result_df = result_df[result_df['amount'] >= 0]
            
            # 8. 数据完整性检查（时间序列连续性、是否有缺失的时间点）
            if 'dt' in result_df.columns and len(result_df) > 1:
                result_df = result_df.sort_values('dt', ascending=True).reset_index(drop=True)
                # 计算时间间隔（分钟）
                time_diffs = result_df['dt'].diff().dt.total_seconds() / 60
                # 对于1分钟数据，时间间隔应该是1分钟（允许一些容差）
                expected_interval = 1.0  # 1分钟
                tolerance = 0.5  # 允许0.5分钟的容差
                missing_intervals = time_diffs[(time_diffs > expected_interval + tolerance) & (time_diffs.notna())]
                if len(missing_intervals) > 0:
                    missing_count = len(missing_intervals)
                    max_gap = missing_intervals.max()
                    validation_issues.append(f"时间序列不连续：发现{missing_count}个时间间隔异常，最大间隔{max_gap:.1f}分钟")
                    logger.warning(f"时间序列不连续：发现{missing_count}个时间间隔异常，最大间隔{max_gap:.1f}分钟")
            
            # 9. 异常值检测（价格突变、成交量异常等，使用统计方法）
            if len(result_df) > 10:  # 需要足够的数据点进行统计
                import numpy as np
                # 价格异常值检测（使用Z-score方法）
                if 'close' in result_df.columns:
                    close_prices = result_df['close'].values
                    mean_price = np.mean(close_prices)
                    std_price = np.std(close_prices)
                    if std_price > 0:
                        z_scores = np.abs((close_prices - mean_price) / std_price)
                        # Z-score > 3 通常被认为是异常值
                        outliers = result_df[z_scores > 3]
                        if len(outliers) > 0:
                            validation_issues.append(f"价格异常值检测：发现{len(outliers)}个异常价格点（Z-score > 3）")
                            logger.warning(f"价格异常值检测：发现{len(outliers)}个异常价格点，价格范围: {outliers['close'].min():.2f} - {outliers['close'].max():.2f}")
                
                # 成交量异常值检测
                if 'vol' in result_df.columns:
                    volumes = result_df['vol'].values
                    # 过滤掉0值
                    non_zero_volumes = volumes[volumes > 0]
                    if len(non_zero_volumes) > 0:
                        mean_vol = np.mean(non_zero_volumes)
                        std_vol = np.std(non_zero_volumes)
                        if std_vol > 0:
                            z_scores_vol = np.abs((volumes - mean_vol) / std_vol)
                            outliers_vol = result_df[z_scores_vol > 3]
                            if len(outliers_vol) > 0:
                                validation_issues.append(f"成交量异常值检测：发现{len(outliers_vol)}个异常成交量点（Z-score > 3）")
                                logger.warning(f"成交量异常值检测：发现{len(outliers_vol)}个异常成交量点")
            
            # 10. 移除重复数据
            before_dedup = len(result_df)
            result_df = result_df.drop_duplicates(subset=['dt'], keep='first')
            after_dedup = len(result_df)
            if before_dedup > after_dedup:
                validation_issues.append(f"移除{before_dedup - after_dedup}条重复数据")
            
            # 11. 按时间排序
            result_df = result_df.sort_values('dt', ascending=True).reset_index(drop=True)
            
            # 12. 确保数据类型正确
            if 'vol' in result_df.columns:
                result_df['vol'] = result_df['vol'].astype('Int64')  # 使用可空整数类型
            
            # 数据修复策略（对于可修复的数据问题）
            repair_count = 0
            repair_actions = []
            
            # 修复策略1: 如果high/low/open/close之间的关系不合理，尝试修复
            if all(col in result_df.columns for col in ['open', 'close', 'high', 'low']) and len(result_df) > 0:
                # 确保high是open、close、high中的最大值
                result_df['high'] = result_df[['open', 'close', 'high']].max(axis=1)
                # 确保low是open、close、low中的最小值
                result_df['low'] = result_df[['open', 'close', 'low']].min(axis=1)
                repair_actions.append("修复high/low与open/close的关系")
                repair_count += 1
            
            # 修复策略2: 如果amount缺失或为0，但vol和close存在，重新计算amount
            if 'amount' in result_df.columns and 'vol' in result_df.columns and 'close' in result_df.columns:
                missing_amount = result_df[(result_df['amount'] == 0) | (result_df['amount'].isna())]
                if len(missing_amount) > 0:
                    # 先计算新的amount值
                    mask = result_df['amount'].isna() | (result_df['amount'] == 0)
                    new_amount = result_df.loc[mask, 'vol'].astype(float) * result_df.loc[mask, 'close'].astype(float)
                    # 确保amount列是float类型
                    if result_df['amount'].dtype != 'float64':
                        result_df['amount'] = result_df['amount'].astype('float64')
                    result_df.loc[mask, 'amount'] = new_amount
                    repair_actions.append(f"修复{len(missing_amount)}条数据的amount字段（通过vol*close计算）")
                    repair_count += 1
            
            # 计算最终数据量和移除数量（在质量评分之前）
            final_count = len(result_df)
            removed_count = original_count - final_count
            
            # 数据质量评分机制
            quality_score = 100.0
            quality_details = {}
            
            if original_count > 0:
                # 数据完整性评分（基于移除的数据比例）
                removal_rate = removed_count / original_count
                completeness_score = (1 - removal_rate) * 100
                quality_details['completeness'] = completeness_score
                quality_score = min(quality_score, completeness_score)
                
                # 数据一致性评分（基于验证问题的数量）
                issue_rate = len(validation_issues) / original_count
                consistency_score = max(0, 100 - issue_rate * 100)
                quality_details['consistency'] = consistency_score
                quality_score = min(quality_score, consistency_score)
                
                # 数据修复评分（基于修复的数据比例）
                if repair_count > 0:
                    repair_score = 100 - (repair_count / original_count) * 10  # 每次修复扣10分
                    quality_details['repair'] = repair_score
                    quality_score = min(quality_score, repair_score)
                else:
                    quality_details['repair'] = 100
            
            # 生成数据质量报告
            quality_report = self._generate_data_quality_report(
                original_count=original_count,
                final_count=final_count,
                validation_issues=validation_issues,
                repair_actions=repair_actions,
                quality_score=quality_score,
                quality_details=quality_details
            )
            
            # 输出验证结果和数据质量报告（final_count和removed_count已在上面计算）
            
            if validation_issues:
                logger.warning(f"数据验证发现问题（共{len(validation_issues)}个）:")
                for issue in validation_issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("✅ 数据验证通过，未发现问题")
            
            if repair_actions:
                logger.info(f"数据修复完成（共{len(repair_actions)}项修复）:")
                for action in repair_actions:
                    logger.info(f"  - {action}")
            
            # 输出数据质量评分
            logger.info(f"数据质量评分: {quality_score:.1f}/100")
            logger.debug(f"  详细评分: {quality_details}")
            
            # 输出数据质量报告摘要
            self._log_quality_report_summary(quality_report)
            
            logger.info(f"数据清洗完成: 原始{original_count}条 -> 清洗后{final_count}条（移除{removed_count}条，{removed_count/original_count*100:.1f}%）")
            
            return result_df
            
        except Exception as e:
            logger.error(f"分钟数据清洗失败: {e}")
            logger.error(f"建议：检查数据源是否正常，数据格式是否正确")
            logger.error(f"如果问题持续，请检查网络连接或联系技术支持")
            # 只在调试模式下记录详细 traceback
            import traceback
            logger.debug(f"详细错误信息:\n{traceback.format_exc()}")
            return None
    
    def _generate_data_quality_report(
        self,
        original_count: int,
        final_count: int,
        validation_issues: list,
        repair_actions: list,
        quality_score: float,
        quality_details: dict
    ) -> dict:
        """
        生成数据质量报告
        
        :param original_count: 原始数据量
        :param final_count: 清洗后数据量
        :param validation_issues: 验证问题列表
        :param repair_actions: 修复操作列表
        :param quality_score: 质量评分
        :param quality_details: 详细评分
        :return: 数据质量报告字典
        """
        # 分类统计问题
        issue_categories = {
            'price': [],
            'volume': [],
            'time': [],
            'consistency': [],
            'outlier': [],
            'other': []
        }
        
        for issue in validation_issues:
            issue_lower = issue.lower()
            if any(keyword in issue_lower for keyword in ['价格', 'price', 'open', 'close', 'high', 'low']):
                issue_categories['price'].append(issue)
            elif any(keyword in issue_lower for keyword in ['成交量', 'volume', 'vol', '成交额', 'amount']):
                issue_categories['volume'].append(issue)
            elif any(keyword in issue_lower for keyword in ['时间', 'time', '间隔', '连续']):
                issue_categories['time'].append(issue)
            elif any(keyword in issue_lower for keyword in ['一致', 'consistency', '关系']):
                issue_categories['consistency'].append(issue)
            elif any(keyword in issue_lower for keyword in ['异常', 'outlier', 'z-score']):
                issue_categories['outlier'].append(issue)
            else:
                issue_categories['other'].append(issue)
        
        report = {
            'summary': {
                'original_count': original_count,
                'final_count': final_count,
                'removed_count': original_count - final_count,
                'removal_rate': (original_count - final_count) / original_count * 100 if original_count > 0 else 0,
                'quality_score': quality_score,
                'quality_details': quality_details,
                'total_issues': len(validation_issues),
                'total_repairs': len(repair_actions)
            },
            'issues': {
                'by_category': {
                    category: {
                        'count': len(issues),
                        'details': issues
                    }
                    for category, issues in issue_categories.items()
                    if len(issues) > 0
                },
                'all': validation_issues
            },
            'repairs': {
                'count': len(repair_actions),
                'details': repair_actions
            }
        }
        
        return report
    
    def _log_quality_report_summary(self, report: dict):
        """
        输出数据质量报告摘要到日志
        
        :param report: 数据质量报告字典
        """
        summary = report['summary']
        issues = report['issues']
        
        logger.info("=" * 60)
        logger.info("数据质量报告摘要")
        logger.info("=" * 60)
        logger.info(f"原始数据量: {summary['original_count']}")
        logger.info(f"清洗后数据量: {summary['final_count']}")
        logger.info(f"移除数据量: {summary['removed_count']} ({summary['removal_rate']:.1f}%)")
        logger.info(f"数据质量评分: {summary['quality_score']:.1f}/100")
        logger.info(f"发现问题数: {summary['total_issues']}")
        logger.info(f"修复操作数: {summary['total_repairs']}")
        
        if summary['total_issues'] > 0:
            logger.info("\n问题分类统计:")
            for category, category_data in issues['by_category'].items():
                logger.info(f"  {category}: {category_data['count']}个问题")
        
        if summary['total_repairs'] > 0:
            logger.info(f"\n修复操作: {summary['total_repairs']}项")
        
        logger.info("=" * 60)
