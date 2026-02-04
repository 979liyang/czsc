# -*- coding: utf-8 -*-
"""
市场工具函数

提供市场代码映射和转换功能
"""
from typing import Dict, List, Optional


# 市场代码映射
MARKET_CODE_MAP = {
    'SH': 'sh',      # 上证
    'SZ': 'sz',      # 深证
    'CY': 'cyb',     # 创业板
    'CYB': 'cyb',    # 创业板（别名）
    'ALL': ['sh', 'sz', 'cyb']  # 所有市场
}

# 反向映射：从小写代码到大写代码
MARKET_CODE_REVERSE_MAP = {
    'sh': 'SH',
    'sz': 'SZ',
    'cyb': 'CY',
    'cy': 'CY'
}


def normalize_market_code(market: str) -> List[str]:
    """
    标准化市场代码，将大写代码转换为小写代码列表
    
    :param market: 市场代码（SH/SZ/CY/CYB/ALL）
    :return: 小写市场代码列表
    """
    market = market.upper().strip()
    
    if market == 'ALL':
        return MARKET_CODE_MAP['ALL']
    
    if market in MARKET_CODE_MAP:
        code = MARKET_CODE_MAP[market]
        if isinstance(code, list):
            return code
        return [code]
    
    # 如果已经是小写，直接返回
    if market.lower() in MARKET_CODE_REVERSE_MAP:
        return [market.lower()]
    
    # 默认返回空列表
    return []


def market_code_to_name(market_code: str) -> str:
    """
    将市场代码转换为市场名称
    
    :param market_code: 市场代码（sh/sz/cyb 或 SH/SZ/CY）
    :return: 市场名称
    """
    market_code = market_code.lower()
    name_map = {
        'sh': '上证',
        'sz': '深证',
        'cyb': '创业板',
        'cy': '创业板'
    }
    return name_map.get(market_code, market_code)


def market_name_to_code(market_name: str) -> Optional[str]:
    """
    将市场名称转换为市场代码
    
    :param market_name: 市场名称（上证/深证/创业板）
    :return: 市场代码（SH/SZ/CY）
    """
    name_map = {
        '上证': 'SH',
        '深证': 'SZ',
        '创业板': 'CY',
        'cyb': 'CY'
    }
    return name_map.get(market_name, None)


def get_market_from_symbol(symbol: str) -> Optional[str]:
    """
    从股票代码中提取市场代码
    
    :param symbol: 股票代码（如：000001.SH 或 600000.SH）
    :return: 市场代码（SH/SZ/CY）
    """
    if '.' in symbol:
        _, market = symbol.split('.', 1)
        return market.upper()
    
    # 根据代码前缀判断
    code = symbol.strip()
    if code.startswith('6'):
        return 'SH'
    elif code.startswith('3'):
        return 'CY'
    elif code.startswith('0'):
        return 'SZ'
    
    return None


def is_valid_market(market: str) -> bool:
    """
    验证市场代码是否有效
    
    :param market: 市场代码
    :return: 是否有效
    """
    market = market.upper().strip()
    return market in ['SH', 'SZ', 'CY', 'CYB', 'ALL']
