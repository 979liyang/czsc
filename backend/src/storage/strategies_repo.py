# -*- coding: utf-8 -*-
"""
策略库仓储：list_all、get_by_name、get_by_id、upsert、delete_by_name
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import Strategy


class StrategiesRepo:
    """strategies 表仓储，以 name 为唯一键"""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self, active_only: bool = False) -> List[Strategy]:
        """查询全部，可选仅 is_active=1"""
        q = self.session.query(Strategy)
        if active_only:
            q = q.filter(Strategy.is_active == 1)
        return q.order_by(Strategy.name).all()

    def get_by_name(self, name: str) -> Optional[Strategy]:
        """按 name 查询"""
        return self.session.query(Strategy).filter(Strategy.name == name).first()

    def get_by_id(self, id: int) -> Optional[Strategy]:
        """按 id 查询"""
        return self.session.query(Strategy).filter(Strategy.id == id).first()

    def upsert(
        self,
        name: str,
        description: Optional[str] = None,
        strategy_type: Optional[str] = None,
        config_json: str = "",
        is_active: int = 1,
    ) -> Strategy:
        """
        以 name 为唯一键插入或更新。
        存在则更新 description、strategy_type、config_json、is_active、updated_at；
        不存在则 insert。
        """
        row = self.get_by_name(name)
        if row:
            if description is not None:
                row.description = description
            if strategy_type is not None:
                row.strategy_type = strategy_type
            if config_json is not None:
                row.config_json = config_json
            row.is_active = is_active
            self.session.flush()
            return row
        row = Strategy(
            name=name,
            description=description,
            strategy_type=strategy_type,
            config_json=config_json or "{}",
            is_active=is_active,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def delete_by_name(self, name: str) -> bool:
        """按 name 删除，存在则删并返回 True，否则返回 False"""
        row = self.get_by_name(name)
        if not row:
            return False
        self.session.delete(row)
        self.session.flush()
        return True
