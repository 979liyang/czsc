# -*- coding: utf-8 -*-
"""
信号库仓储：list_all、get_by_name、upsert
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import SignalFunc


class SignalsRepo:
    """signals 表仓储，以 name 为唯一键"""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self, active_only: bool = False) -> List[SignalFunc]:
        """查询全部，可选仅 is_active=1"""
        q = self.session.query(SignalFunc)
        if active_only:
            q = q.filter(SignalFunc.is_active == 1)
        return q.order_by(SignalFunc.category, SignalFunc.name).all()

    def get_by_name(self, name: str) -> Optional[SignalFunc]:
        """按 name 查询"""
        return self.session.query(SignalFunc).filter(SignalFunc.name == name).first()

    def upsert(
        self,
        name: str,
        module_path: Optional[str] = None,
        category: Optional[str] = None,
        param_template: Optional[str] = None,
        description: Optional[str] = None,
        is_active: int = 1,
    ) -> SignalFunc:
        """
        以 name 为唯一键插入或更新。
        存在则更新 module_path、category、param_template、description、is_active、updated_at；
        不存在则 insert。
        """
        row = self.get_by_name(name)
        if row:
            if module_path is not None:
                row.module_path = module_path
            if category is not None:
                row.category = category
            if param_template is not None:
                row.param_template = param_template
            if description is not None:
                row.description = description
            row.is_active = is_active
            self.session.flush()
            return row
        row = SignalFunc(
            name=name,
            module_path=module_path or "czsc.signals",
            category=category,
            param_template=param_template,
            description=description,
            is_active=is_active,
        )
        self.session.add(row)
        self.session.flush()
        return row
