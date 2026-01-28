# -*- coding: utf-8 -*-
"""
AkShare 数据源模块

提供基于 AkShare 的数据获取和转换功能，与 CZSC 框架集成
支持：
- 从 AkShare 获取股票数据
- 存储到 MySQL 数据库
- 从 MySQL 读取数据并转换为 CZSC 格式
"""
from czsc.akshare.manager import AkShareDataManager
from czsc.akshare.base import (
    get_real_time_data,
    get_minute_data,
    get_historical_data,
    format_akshare_to_rawbar,
    get_stock_list,
    normalize_stock_code,
    get_akshare_code,
)
from czsc.akshare.database import (
    DatabaseManager,
    StockInfo,
    StockKline,
    get_db_manager,
    init_database,
)
from czsc.akshare.fetch_data import (
    get_stock_list_by_market,
    get_stock_info,
    fetch_historical_data,
    fetch_minute_data,
    batch_fetch_stocks,
)
from czsc.akshare.store_data import (
    store_stock_info,
    store_kline_data,
    batch_store_stocks,
    sync_all_stocks,
)
from czsc.akshare.czsc_adapter import (
    get_symbols,
    get_raw_bars,
    get_latest_bar,
    check_data_availability,
)

__all__ = [
    # 数据管理器
    'AkShareDataManager',
    # 基础数据获取
    'get_real_time_data',
    'get_minute_data',
    'get_historical_data',
    'format_akshare_to_rawbar',
    'get_stock_list',
    'normalize_stock_code',
    'get_akshare_code',
    # 数据库相关
    'DatabaseManager',
    'StockInfo',
    'StockKline',
    'get_db_manager',
    'init_database',
    # 数据获取
    'get_stock_list_by_market',
    'get_stock_info',
    'fetch_historical_data',
    'fetch_minute_data',
    'batch_fetch_stocks',
    # 数据存储
    'store_stock_info',
    'store_kline_data',
    'batch_store_stocks',
    'sync_all_stocks',
    # CZSC 适配器
    'get_symbols',
    'get_raw_bars',
    'get_latest_bar',
    'check_data_availability',
]

