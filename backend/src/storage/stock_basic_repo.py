# -*- coding: utf-8 -*-
"""
股票主数据仓储

负责对 MySQL 的 stock_basic 表进行读写（增删改查、批量 upsert）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import StockBasic


class StockBasicRepo:
    """股票主数据仓储"""

    def __init__(self, session: Session):
        """
        初始化仓储

        :param session: SQLAlchemy Session
        """

        self.session = session

    def get(self, symbol: str) -> Optional[StockBasic]:
        """获取单条"""

        return self.session.get(StockBasic, symbol)

    def upsert_one(self, symbol: str, name: Optional[str] = None, market: Optional[str] = None, **kwargs) -> None:
        """单条 upsert"""

        obj = self.get(symbol)
        if obj is None:
            obj = StockBasic(symbol=symbol)
            self.session.add(obj)

        obj.name = name if name is not None else obj.name
        obj.market = market if market is not None else obj.market
        obj.list_date = kwargs.get("list_date", obj.list_date)
        obj.delist_date = kwargs.get("delist_date", obj.delist_date)
        obj.updated_at = datetime.now()

    def bulk_upsert(self, rows: Iterable[Dict[str, Any]]) -> int:
        """
        批量 upsert

        :param rows: 每行至少包含 symbol，可选包含 name/market/list_date/delist_date
        :return: 处理行数
        """

        n = 0
        for r in rows:
            symbol = (r.get("symbol") or "").strip()
            if not symbol:
                continue
            self.upsert_one(
                symbol=symbol,
                name=(r.get("name") or None),
                market=(r.get("market") or None),
                list_date=(r.get("list_date") or None),
                delist_date=(r.get("delist_date") or None),
            )
            n += 1

        logger.info(f"stock_basic 批量 upsert 完成：rows={n}")
        return n

    def list_symbols(self, market: Optional[str] = None) -> List[str]:
        """列出股票代码"""

        q = self.session.query(StockBasic.symbol)
        if market:
            q = q.filter(StockBasic.market == market)
        return [x[0] for x in q.all()]

