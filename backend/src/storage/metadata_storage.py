# -*- coding: utf-8 -*-
"""
元数据存储服务

使用SQLite存储股票列表、信号函数信息等元数据。
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger


class MetadataStorage:
    """元数据存储服务"""

    def __init__(self, db_path: Path):
        """
        初始化元数据存储服务

        :param db_path: SQLite数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建symbols表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbols (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                group_name TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        # 创建signals表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                name TEXT PRIMARY KEY,
                category TEXT,
                description TEXT,
                params TEXT,
                examples TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info(f"元数据数据库初始化完成：{self.db_path}")

    def add_symbol(self, symbol: str, name: Optional[str] = None,
                   market: Optional[str] = None, group_name: Optional[str] = None) -> None:
        """
        添加股票信息

        :param symbol: 标的代码
        :param name: 标的名称
        :param market: 市场（如：SH、SZ）
        :param group_name: 分组名称
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR REPLACE INTO symbols (symbol, name, market, group_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, 
                COALESCE((SELECT created_at FROM symbols WHERE symbol = ?), ?),
                ?)
        ''', (symbol, name, market, group_name, symbol, now, now))

        conn.commit()
        conn.close()
        logger.debug(f"添加股票信息：{symbol}")

    def get_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票信息

        :param symbol: 标的代码
        :return: 股票信息字典，如果不存在返回None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM symbols WHERE symbol = ?', (symbol,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def list_symbols(self, group_name: Optional[str] = None) -> List[str]:
        """
        列出所有股票代码

        :param group_name: 分组名称（可选）
        :return: 股票代码列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if group_name:
            cursor.execute('SELECT symbol FROM symbols WHERE group_name = ?', (group_name,))
        else:
            cursor.execute('SELECT symbol FROM symbols')

        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()

        return symbols

    def add_signal(self, name: str, category: str, description: Optional[str] = None,
                   params: Optional[str] = None, examples: Optional[str] = None) -> None:
        """
        添加信号函数信息

        :param name: 信号函数名称
        :param category: 信号分类（如：cxt、tas、bar等）
        :param description: 函数说明
        :param params: 参数说明（JSON字符串）
        :param examples: 使用示例（JSON字符串）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR REPLACE INTO signals (name, category, description, params, examples, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?,
                COALESCE((SELECT created_at FROM signals WHERE name = ?), ?),
                ?)
        ''', (name, category, description, params, examples, name, now, now))

        conn.commit()
        conn.close()
        logger.debug(f"添加信号函数信息：{name}")

    def get_signal(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取信号函数信息

        :param name: 信号函数名称
        :return: 信号函数信息字典，如果不存在返回None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM signals WHERE name = ?', (name,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return dict(row)
        return None

    def list_signals(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有信号函数

        :param category: 信号分类（可选）
        :return: 信号函数信息列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if category:
            cursor.execute('SELECT * FROM signals WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM signals')

        signals = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return signals
