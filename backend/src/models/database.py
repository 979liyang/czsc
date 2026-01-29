# -*- coding: utf-8 -*-
"""
数据库模型定义

定义SQLite数据库的表结构。实际表结构在MetadataStorage中创建。
这里定义模型类以备将来使用ORM。
"""
from datetime import datetime
from typing import Optional


class Symbol:
    """股票信息模型"""

    def __init__(self, symbol: str, name: Optional[str] = None,
                 market: Optional[str] = None, group_name: Optional[str] = None,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None):
        self.symbol = symbol
        self.name = name
        self.market = market
        self.group_name = group_name
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.updated_at = updated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'market': self.market,
            'group_name': self.group_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class Signal:
    """信号函数信息模型"""

    def __init__(self, name: str, category: str, description: Optional[str] = None,
                 params: Optional[str] = None, examples: Optional[str] = None,
                 created_at: Optional[str] = None, updated_at: Optional[str] = None):
        self.name = name
        self.category = category
        self.description = description
        self.params = params
        self.examples = examples
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.updated_at = updated_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'params': self.params,
            'examples': self.examples,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


# 数据库表结构说明
"""
symbols表结构：
- symbol: TEXT PRIMARY KEY - 标的代码
- name: TEXT - 标的名称
- market: TEXT - 市场（如：SH、SZ）
- group_name: TEXT - 分组名称
- created_at: TEXT - 创建时间
- updated_at: TEXT - 更新时间

signals表结构：
- name: TEXT PRIMARY KEY - 信号函数名称
- category: TEXT - 信号分类（如：cxt、tas、bar等）
- description: TEXT - 函数说明
- params: TEXT - 参数说明（JSON字符串）
- examples: TEXT - 使用示例（JSON字符串）
- created_at: TEXT - 创建时间
- updated_at: TEXT - 更新时间
"""
