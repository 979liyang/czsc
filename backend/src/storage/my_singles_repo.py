# -*- coding: utf-8 -*-
"""
用户收藏 my_singles 仓储：信号或标的的增删查
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import MySingles


class MySinglesRepo:
    """用户收藏 my_singles（信号或标的）"""

    def __init__(self, session: Session):
        self.session = session

    def list_by_user(self, user_id: int, item_type: Optional[str] = None) -> List[MySingles]:
        """查询用户收藏列表，可按类型过滤"""
        q = self.session.query(MySingles).filter(MySingles.user_id == user_id)
        if item_type:
            q = q.filter(MySingles.item_type == item_type)
        return q.order_by(MySingles.sort_order, MySingles.id).all()

    def add(self, user_id: int, item_type: str, item_id: str, sort_order: int = 0) -> MySingles:
        """添加收藏，已存在则返回已有记录"""
        existing = (
            self.session.query(MySingles)
            .filter(
                MySingles.user_id == user_id,
                MySingles.item_type == item_type,
                MySingles.item_id == item_id,
            )
            .first()
        )
        if existing:
            return existing
        row = MySingles(user_id=user_id, item_type=item_type, item_id=item_id, sort_order=sort_order)
        self.session.add(row)
        self.session.flush()
        return row

    def remove(self, user_id: int, item_type: str, item_id: str) -> bool:
        """取消收藏，返回是否删除了记录"""
        deleted = (
            self.session.query(MySingles)
            .filter(
                MySingles.user_id == user_id,
                MySingles.item_type == item_type,
                MySingles.item_id == item_id,
            )
            .delete()
        )
        return deleted > 0

    def update_sort_order(
        self, user_id: int, item_type: str, item_id: str, sort_order: int
    ) -> Optional[MySingles]:
        """更新某条收藏的排序；不存在返回 None"""
        row = (
            self.session.query(MySingles)
            .filter(
                MySingles.user_id == user_id,
                MySingles.item_type == item_type,
                MySingles.item_id == item_id,
            )
            .first()
        )
        if not row:
            return None
        row.sort_order = sort_order
        self.session.flush()
        return row
