# -*- coding: utf-8 -*-
"""
股票信息服务（MySQL）

用于提供股票列表、中文名等主数据能力。
"""

from __future__ import annotations

from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import StockBasic


class SymbolService:
    """股票信息服务"""

    def __init__(self, session: Session):
        """
        初始化服务

        :param session: SQLAlchemy Session
        """

        self.session = session

    def list_symbols(self, market: Optional[str] = None) -> List[StockBasic]:
        """列出股票主数据"""

        q = self.session.query(StockBasic)
        if market:
            q = q.filter(StockBasic.market == market)
        items = q.order_by(StockBasic.symbol.asc()).all()
        logger.info(f"MySQL stock_basic symbols={len(items)} market={market}")
        return items

