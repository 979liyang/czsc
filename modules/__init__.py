# -*- coding: utf-8 -*-
"""
CZSC 模块封装

该模块提供了对 czsc 库功能的封装，使调用更加便捷和统一。

主要模块：
- analyze: 缠论分析相关功能
- trading: 交易相关功能
- strategy: 策略相关功能
- data: 数据处理相关功能
- utils: 工具函数封装
- visualization: 可视化相关功能
"""

from modules.analyze import CZSCAnalyzer
from modules.trading import TradingManager
from modules.strategy import StrategyManager
from modules.data import DataManager
from modules.utils import CZSCUtils

__all__ = [
    'CZSCAnalyzer',
    'TradingManager',
    'StrategyManager',
    'DataManager',
    'CZSCUtils',
]

