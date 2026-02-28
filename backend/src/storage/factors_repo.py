# -*- coding: utf-8 -*-
"""
因子库仓储：list_all、get_by_name、get_by_id、upsert、update、delete_by_name
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import FactorDef


class FactorsRepo:
    """factors 表仓储，以 name 为唯一键"""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self, active_only: bool = False) -> List[FactorDef]:
        """查询全部，可选仅 is_active=1"""
        q = self.session.query(FactorDef)
        if active_only:
            q = q.filter(FactorDef.is_active == 1)
        return q.order_by(FactorDef.name).all()

    def get_by_name(self, name: str) -> Optional[FactorDef]:
        """按 name 查询"""
        return self.session.query(FactorDef).filter(FactorDef.name == name).first()

    def get_by_id(self, id: int) -> Optional[FactorDef]:
        """按 id 查询"""
        return self.session.query(FactorDef).filter(FactorDef.id == id).first()

    def upsert(
        self,
        name: str,
        expression_or_signal_ref: Optional[str] = None,
        signals_config: Optional[str] = None,
        description: Optional[str] = None,
        is_active: int = 1,
    ) -> FactorDef:
        """
        以 name 为唯一键插入或更新。
        存在则更新 expression_or_signal_ref、signals_config、description、is_active、updated_at；
        不存在则 insert。
        """
        row = self.get_by_name(name)
        if row:
            if expression_or_signal_ref is not None:
                row.expression_or_signal_ref = expression_or_signal_ref
            if signals_config is not None:
                row.signals_config = signals_config
            if description is not None:
                row.description = description
            row.is_active = is_active
            self.session.flush()
            return row
        row = FactorDef(
            name=name,
            expression_or_signal_ref=expression_or_signal_ref,
            signals_config=signals_config,
            description=description,
            is_active=is_active,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def update(
        self,
        name: str,
        expression_or_signal_ref: Optional[str] = None,
        signals_config: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[int] = None,
    ) -> Optional[FactorDef]:
        """按 name 更新，不存在返回 None"""
        row = self.get_by_name(name)
        if not row:
            return None
        if expression_or_signal_ref is not None:
            row.expression_or_signal_ref = expression_or_signal_ref
        if signals_config is not None:
            row.signals_config = signals_config
        if description is not None:
            row.description = description
        if is_active is not None:
            row.is_active = is_active
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
