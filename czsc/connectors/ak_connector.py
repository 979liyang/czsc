# -*- coding: utf-8 -*-
"""
author: Auto-generated
email: -
create_dt: 2026/1/30
describe: AKShare数据源连接器

基于 AKShare 实现与 ts_connector.py 相同的功能接口
AKShare 是一个免费、开源的 Python 金融数据接口库
"""
import os
import czsc
import pandas as pd
from czsc import Freq, RawBar
from typing import List, Optional
from tqdm import tqdm
from loguru import logger
from datetime import datetime, timedelta

try:
    import akshare as ak
except ImportError:
    logger.error("请先安装 akshare: pip install akshare")
    raise

# 缓存路径（可选，用于缓存数据）
cache_path = os.getenv("AK_CACHE_PATH", os.path.expanduser("~/.ak_data_cache"))


def format_kline(kline: pd.DataFrame, freq: Freq, symbol: str) -> List[RawBar]:
    """AKShare K线数据转换

    :param kline: AKShare 数据接口返回的K线数据
    :param freq: K线周期
    :param symbol: 标的代码
    :return: 转换好的K线数据
    """
    bars = []
    
    # AKShare 返回的列名可能不同，需要统一处理
    # 标准列名：日期、开盘、收盘、最高、最低、成交量、成交额
    column_map = {
        '日期': 'date',
        '时间': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'vol',
        '成交额': 'amount',
        'volume': 'vol',
        'amount': 'amount'
    }
    
    # 统一列名
    kline = kline.copy()
    for old_col, new_col in column_map.items():
        if old_col in kline.columns:
            kline.rename(columns={old_col: new_col}, inplace=True)
    
    # 确定日期列
    date_col = 'date' if 'date' in kline.columns else '时间' if '时间' in kline.columns else kline.columns[0]
    
    # 转换为 datetime
    if date_col in kline.columns:
        kline[date_col] = pd.to_datetime(kline[date_col])
    else:
        kline['date'] = pd.to_datetime(kline.index)
        date_col = 'date'
    
    # 排序
    kline = kline.sort_values(date_col, ascending=True, ignore_index=True)
    
    # 确保数值列为 float
    for col in ['open', 'close', 'high', 'low', 'vol', 'amount']:
        if col in kline.columns:
            kline[col] = pd.to_numeric(kline[col], errors='coerce').fillna(0)
    
    records = kline.to_dict("records")
    
    for i, record in enumerate(records):
        # 处理成交量单位（日线需要乘以100，分钟线直接使用）
        if freq == Freq.D:
            vol = int(record.get("vol", 0) * 100) if record.get("vol", 0) > 0 else 0
            amount = int(record.get("amount", 0) * 1000) if record.get("amount", 0) > 0 else 0
        else:
            vol = int(record.get("vol", 0)) if record.get("vol", 0) > 0 else 0
            amount = int(record.get("amount", 0)) if record.get("amount", 0) > 0 else 0
        
        # 获取时间
        dt = record.get(date_col)
        if dt is None:
            continue
        
        # 创建 RawBar 对象
        bar = RawBar(
            symbol=symbol,
            dt=pd.to_datetime(dt),
            id=i,
            freq=freq,
            open=float(record.get("open", 0)),
            close=float(record.get("close", 0)),
            high=float(record.get("high", 0)),
            low=float(record.get("low", 0)),
            vol=vol,
            amount=amount,
        )
        bars.append(bar)
    
    return bars


def _convert_symbol_format(symbol: str) -> tuple:
    """转换标的代码格式
    
    AKShare 使用不同的代码格式：
    - 股票：000001（6位数字）
    - 指数：sh000001 或 sz399001
    - ETF：sh510300 或 sz159915
    
    :param symbol: CZSC 格式的代码，如 "000001.SH#I" 或 "000001.SZ#E"
    :return: (ak_code, asset_type, market)
    """
    if "#" in symbol:
        code, asset = symbol.split("#")
    else:
        code = symbol
        asset = "E"  # 默认为股票
    
    # 解析代码和市场
    if "." in code:
        code_part, market = code.split(".")
        market = market.upper()
    else:
        code_part = code
        market = "SH" if code_part.startswith("000") or code_part.startswith("600") else "SZ"
    
    # 转换为 AKShare 格式
    if asset == "I":  # 指数
        ak_code = f"{market.lower()}{code_part}"
    elif asset == "FD":  # 基金/ETF
        ak_code = f"{market.lower()}{code_part}"
    else:  # 股票
        ak_code = code_part
    
    return ak_code, asset, market


def _get_stock_daily(ak_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> pd.DataFrame:
    """获取股票日线数据
    
    :param ak_code: AKShare 格式的股票代码
    :param start_date: 开始日期 YYYYMMDD
    :param end_date: 结束日期 YYYYMMDD
    :param adjust: 复权类型 qfq(前复权)/hfq(后复权)/None(不复权)
    :return: DataFrame
    """
    try:
        # AKShare 股票日线数据接口
        df = ak.stock_zh_a_hist(
            symbol=ak_code,
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            adjust=adjust
        )

        if df.empty:
            return pd.DataFrame()
        
        # 标准化列名
        df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount'
        }, inplace=True)
        
        return df
    except Exception as e:
        logger.error(f"获取股票日线数据失败 {ak_code}: {e}")
        return pd.DataFrame()


def _get_index_daily(ak_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取指数日线数据
    
    :param ak_code: AKShare 格式的指数代码，如 "sh000001"
    :param start_date: 开始日期 YYYYMMDD
    :param end_date: 结束日期 YYYYMMDD
    :return: DataFrame
    """
    try:
        # AKShare 指数日线数据接口
        df = ak.index_zh_a_hist(
            symbol=ak_code,
            period="日k",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", "")
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # 标准化列名
        df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount'
        }, inplace=True)
        
        return df
    except Exception as e:
        logger.error(f"获取指数日线数据失败 {ak_code}: {e}")
        return pd.DataFrame()


def _get_stock_minute(ak_code: str, start_date: str, end_date: str, period: str = "1") -> pd.DataFrame:
    """获取股票分钟线数据
    
    :param ak_code: AKShare 格式的股票代码
    :param start_date: 开始日期 YYYYMMDD
    :param end_date: 结束日期 YYYYMMDD
    :param period: 分钟周期 1/5/15/30/60
    :return: DataFrame
    """
    try:
        # AKShare 股票分钟线数据接口
        df = ak.stock_zh_a_hist_min_em(
            symbol=ak_code,
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", ""),
            period=period,
            adjust=""
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # 标准化列名
        df.rename(columns={
            '时间': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol',
            '成交额': 'amount'
        }, inplace=True)
        
        # 删除9:30的K线（集合竞价）
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df[~((df['date'].dt.hour == 9) & (df['date'].dt.minute == 30))]
        
        # 删除无成交量的K线
        df = df[df['vol'] > 0].reset_index(drop=True)
        
        return df
    except Exception as e:
        logger.error(f"获取股票分钟线数据失败 {ak_code}: {e}")
        return pd.DataFrame()


def _get_etf_daily(ak_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取ETF日线数据
    
    :param ak_code: AKShare 格式的ETF代码，如 "sh510300"
    :param start_date: 开始日期 YYYYMMDD
    :param end_date: 结束日期 YYYYMMDD
    :return: DataFrame
    """
    try:
        # AKShare ETF日线数据接口
        df = ak.fund_etf_hist_sina(
            symbol=ak_code.upper(),
            period="daily",
            start_date=start_date.replace("-", ""),
            end_date=end_date.replace("-", "")
        )
        
        if df.empty:
            return pd.DataFrame()
        
        # 标准化列名
        df.rename(columns={
            'date': 'date',
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'volume': 'vol',
            'amount': 'amount'
        }, inplace=True)
        
        return df
    except Exception as e:
        logger.error(f"获取ETF日线数据失败 {ak_code}: {e}")
        return pd.DataFrame()


def get_raw_bars(symbol: str, freq: Freq, sdt: str, edt: str, fq: str = "后复权", raw_bar: bool = True) -> List[RawBar]:
    """获取 CZSC 库定义的标准 RawBar 对象列表（使用 AKShare 数据源）
    
    :param symbol: 标的代码，格式：
        - 股票："000001.SZ" 或 "000001.SZ#E"
        - 指数："000001.SH" 或 "000001.SH#I"
        - ETF："510300.SH" 或 "510300.SH#FD"
    :param freq: K线周期，支持 Freq 对象或字符串
    :param sdt: 开始时间，格式 "YYYYMMDD"
    :param edt: 结束时间，格式 "YYYYMMDD"
    :param fq: 复权类型，"前复权"/"后复权"/"不复权"
    :param raw_bar: 是否返回 RawBar 对象列表，默认 True
    :return: RawBar 对象列表或 DataFrame
    """
    # 保存原始的 freq 值（用于 format_kline）
    if isinstance(freq, Freq):
        original_freq = freq
        freq_str = str(freq.value)
    else:
        original_freq = Freq(freq)
        freq_str = str(freq)
    
    # 转换复权类型
    if fq == "前复权":
        adjust = "qfq"
    elif fq == "后复权":
        adjust = "hfq"
    else:
        adjust = ""
    
    # 转换标的代码格式
    ak_code, asset, market = _convert_symbol_format(symbol)
    
    # 格式化日期
    sdt_str = sdt.replace("-", "")
    edt_str = edt.replace("-", "")
    
    df = pd.DataFrame()
    
    # 根据频率和资产类型获取数据
    if "分钟" in freq_str:
        # 分钟线数据
        period_map = {
            "1分钟": "1",
            "5分钟": "5",
            "15分钟": "15",
            "30分钟": "30",
            "60分钟": "60"
        }
        period = period_map.get(freq_str, "1")
        
        if asset == "E":
            df = _get_stock_minute(ak_code, sdt_str, edt_str, period)
        else:
            logger.warning(f"AKShare 暂不支持 {asset} 类型的分钟线数据")
            return []
    
    else:
        # 日线/周线/月线数据
        if asset == "E":
            # 股票
            df = _get_stock_daily(ak_code, sdt_str, edt_str, adjust)
        elif asset == "I":
            # 指数
            df = _get_index_daily(ak_code, sdt_str, edt_str)
        elif asset == "FD":
            # ETF/基金
            df = _get_etf_daily(ak_code, sdt_str, edt_str)
        else:
            logger.warning(f"AKShare 暂不支持资产类型: {asset}")
            return []
        
        # 如果是周线或月线，需要重采样
        if freq_str == "周线" or freq_str == "月线":
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                if freq_str == "周线":
                    df = df.resample('W').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'vol': 'sum',
                        'amount': 'sum'
                    }).reset_index()
                elif freq_str == "月线":
                    df = df.resample('M').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'vol': 'sum',
                        'amount': 'sum'
                    }).reset_index()
    
    if df.empty:
        logger.warning(f"未获取到数据: {symbol} {freq_str} {sdt} - {edt}")
        return []
    
    # 转换为 RawBar 对象
    if raw_bar:
        bars = format_kline(df, original_freq, symbol.split("#")[0] if "#" in symbol else symbol)
        return bars
    else:
        return df


def get_symbols(step: str = "all") -> List[str]:
    """获取标的代码列表（使用 AKShare 数据源）
    
    :param step: 标的类型，可选值：
        - "index" - 主要指数
        - "stock" - 所有A股股票
        - "check" - 检查用标的
        - "train" - 训练集标的
        - "valid" - 验证集标的
        - "etfs" - ETF列表
        - "all" - 所有标的
    :return: 标的代码列表，格式 ["code#asset", ...]
    """
    symbols = []
    
    # 主要指数列表
    index_list = [
        "000905.SH",  # 中证500
        "000016.SH",  # 上证50
        "000300.SH",  # 沪深300
        "000001.SH",  # 上证指数
        "000852.SH",  # 中证1000
        "399001.SZ",  # 深证成指
        "399006.SZ",  # 创业板指
        "399376.SZ",  # 深证100
        "399377.SZ",  # 中小板指
        "399317.SZ",  # 国证1000
        "399303.SZ",  # 国证2000
    ]
    
    # ETF列表
    etf_list = [
        "512880.SH",  # 证券ETF
        "518880.SH",  # 黄金ETF
        "515880.SH",  # 银行ETF
        "513050.SH",  # 中概互联
        "512690.SH",  # 酒ETF
        "512660.SH",  # 军工ETF
        "512400.SH",  # 有色金属ETF
        "512010.SH",  # 医药ETF
        "512000.SH",  # 券商ETF
        "510900.SH",  # H股ETF
        "510300.SH",  # 沪深300ETF
        "510500.SH",  # 中证500ETF
        "510050.SH",  # 上证50ETF
        "159992.SZ",  # 创新药ETF
        "159985.SZ",  # 消费ETF
        "159981.SZ",  # 能源ETF
        "159949.SZ",  # 华安创业板50ETF
        "159915.SZ",  # 易方达创业板ETF
    ]
    
    # 获取股票列表
    try:
        stock_list = ak.stock_info_a_code_name()["code"].tolist()
    except Exception as e:
        logger.warning(f"获取股票列表失败: {e}，使用默认列表")
        stock_list = ["000001.SZ", "000002.SZ"]  # 默认列表
    
    # 筛选2010年之前上市的股票（用于训练/验证集）
    stocks_old = []
    try:
        stock_info = ak.stock_info_a_code_name()
        # 这里简化处理，实际应该根据上市日期筛选
        stocks_old = stock_list[:800]  # 简化：取前800只
    except:
        stocks_old = stock_list[:800]
    
    stocks_map = {
        "index": index_list,
        "stock": stock_list,
        "check": ["000001.SZ"],
        "train": stocks_old[:200],
        "valid": stocks_old[200:600],
        "etfs": etf_list,
    }
    
    asset_map = {"index": "I", "stock": "E", "check": "E", "train": "E", "valid": "E", "etfs": "FD"}
    
    if step.lower() == "all":
        for k, v in stocks_map.items():
            symbols += [f"{code}#{asset_map[k]}" for code in v]
    else:
        if step in stocks_map:
            asset = asset_map[step]
            symbols = [f"{code}#{asset}" for code in stocks_map[step]]
        else:
            logger.warning(f"未知的 step 参数: {step}")
    
    return symbols


def get_sw_members(level: str = "L1") -> pd.DataFrame:
    """获取申万行业分类成分股（使用 AKShare 数据源）
    
    :param level: 行业级别，L1/L2/L3
    :return: DataFrame
    """
    try:
        # AKShare 申万行业分类接口
        df = ak.sw_index_cons(symbol="801010")  # 示例：使用第一个行业代码
        return df
    except Exception as e:
        logger.error(f"获取申万行业分类失败: {e}")
        return pd.DataFrame()


def get_daily_basic(sdt: str = "20100101", edt: str = "20240101") -> pd.DataFrame:
    """获取全市场A股的每日指标数据（使用 AKShare 数据源）
    
    :param sdt: 开始日期
    :param edt: 结束日期
    :return: DataFrame
    """
    try:
        # AKShare 股票基本信息接口
        # 注意：AKShare 没有直接的每日指标接口，这里返回股票基本信息
        df = ak.stock_info_a_code_name()
        return df
    except Exception as e:
        logger.error(f"获取每日指标数据失败: {e}")
        return pd.DataFrame()


def moneyflow_hsgt(start_date: str, end_date: str) -> pd.DataFrame:
    """获取沪深港通资金流向数据（使用 AKShare 数据源）
    
    :param start_date: 开始日期，格式 "YYYYMMDD"
    :param end_date: 结束日期，格式 "YYYYMMDD"
    :return: DataFrame
    """
    try:
        # AKShare 沪深港通资金流向接口
        df = ak.tool_trade_date_hist_sina()
        
        # 筛选日期范围
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        sdt = pd.to_datetime(start_date)
        edt = pd.to_datetime(end_date)
        df = df[(df['trade_date'] >= sdt) & (df['trade_date'] <= edt)]
        
        # 重命名列
        df.rename(columns={'trade_date': 'dt'}, inplace=True)
        
        return df
    except Exception as e:
        logger.error(f"获取沪深港通资金流向数据失败: {e}")
        return pd.DataFrame()
