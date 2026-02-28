# -*- coding: utf-8 -*-
"""
自选股仓储：按 user_id 列表、添加、删除
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models.mysql_models import Watchlist


class WatchlistRepo:
    def __init__(self, session: Session):
        self.session = session

    def list_by_user(self, user_id: int) -> List[Watchlist]:
        """按用户 ID 返回自选股列表（按 sort_order, id）"""
        return (
            self.session.query(Watchlist)
            .filter(Watchlist.user_id == user_id)
            .order_by(Watchlist.sort_order, Watchlist.id)
            .all()
        )

    def add(self, user_id: int, symbol: str, sort_order: int = 0) -> Watchlist:
        """添加自选，已存在则返回已有记录"""
        row = (
            self.session.query(Watchlist)
            .filter(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
            .first()
        )
        if row:
            return row
        w = Watchlist(user_id=user_id, symbol=symbol.strip(), sort_order=sort_order)
        self.session.add(w)
        self.session.flush()
        return w

    def remove(self, user_id: int, symbol: str) -> bool:
        """删除自选，返回是否删除了记录"""
        row = (
            self.session.query(Watchlist)
            .filter(Watchlist.user_id == user_id, Watchlist.symbol == symbol)
            .first()
        )
        if not row:
            return False
        self.session.delete(row)
        return True
