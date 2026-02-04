# -*- coding: utf-8 -*-
"""
分钟K线仓储（面向既有分钟明细表）

说明：
- 分钟明细表通常由用户已有的数据写入，不强制由本项目创建
- 本仓储尽量只依赖两个列：symbol / dt（dt 为 datetime）
- 其余字段（open/high/low/close/vol...）不参与完整性检查的核心算法
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional, Tuple

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..utils.settings import get_settings


class MinuteBarRepo:
    """分钟K线仓储（只做查询与统计）"""

    def __init__(self, session: Session, table_name: Optional[str] = None, symbol_col: str = "symbol", dt_col: str = "dt"):
        """
        初始化仓储

        :param session: SQLAlchemy Session
        :param table_name: 分钟明细表名；默认取 settings.table_minute_bar
        :param symbol_col: 股票代码字段名，默认 symbol
        :param dt_col: 时间字段名，默认 dt（datetime）
        """

        self.session = session
        self.table_name = table_name or get_settings().table_minute_bar
        self.symbol_col = symbol_col
        self.dt_col = dt_col

    def get_dt_range(self, symbol: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """查询某股票分钟数据起止时间"""

        sql = text(
            f"SELECT MIN({self.dt_col}) AS min_dt, MAX({self.dt_col}) AS max_dt "
            f"FROM {self.table_name} WHERE {self.symbol_col} = :symbol"
        )
        row = self.session.execute(sql, {"symbol": symbol}).mappings().first()
        if not row:
            return None, None
        return row.get("min_dt"), row.get("max_dt")

    def count_by_trade_date(self, symbol: str, trade_date: date) -> int:
        """统计某股票在某交易日的分钟条数"""

        sql = text(
            f"SELECT COUNT(1) AS cnt FROM {self.table_name} "
            f"WHERE {self.symbol_col} = :symbol AND DATE({self.dt_col}) = :d"
        )
        row = self.session.execute(sql, {"symbol": symbol, "d": trade_date}).mappings().first()
        return int(row["cnt"]) if row and row.get("cnt") is not None else 0

    def list_distinct_symbols(self, limit: int = 0) -> List[str]:
        """从分钟明细表中列出 distinct symbol（用于反推主数据）"""

        sql = f"SELECT DISTINCT {self.symbol_col} AS symbol FROM {self.table_name}"
        if limit and limit > 0:
            sql += " LIMIT :limit"
            rows = self.session.execute(text(sql), {"limit": limit}).mappings().all()
        else:
            rows = self.session.execute(text(sql)).mappings().all()

        symbols = [r["symbol"] for r in rows if r.get("symbol")]
        logger.info(f"分钟表 distinct symbols={len(symbols)}（limit={limit}）")
        return symbols

    def list_minutes(self, symbol: str, trade_date: date) -> List[datetime]:
        """获取某股票某交易日的分钟时间点列表（用于缺口计算）"""

        sql = text(
            f"SELECT {self.dt_col} AS dt FROM {self.table_name} "
            f"WHERE {self.symbol_col} = :symbol AND DATE({self.dt_col}) = :d "
            f"ORDER BY {self.dt_col} ASC"
        )
        rows = self.session.execute(sql, {"symbol": symbol, "d": trade_date}).mappings().all()
        return [r["dt"] for r in rows if r.get("dt") is not None]

