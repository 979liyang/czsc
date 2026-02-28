# -*- coding: utf-8 -*-
"""
可复用信号配置仓储：list、get_by_name、create、update、delete
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import SignalsConfig


class SignalsConfigRepo:
    """signals_config 表仓储，以 name 为唯一键"""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[SignalsConfig]:
        """查询全部配置，按 name 排序"""
        return (
            self.session.query(SignalsConfig)
            .order_by(SignalsConfig.name)
            .all()
        )

    def get_by_name(self, name: str) -> Optional[SignalsConfig]:
        """按 name 查询"""
        return (
            self.session.query(SignalsConfig)
            .filter(SignalsConfig.name == name)
            .first()
        )

    def get_by_id(self, id: int) -> Optional[SignalsConfig]:
        """按 id 查询"""
        return self.session.query(SignalsConfig).filter(SignalsConfig.id == id).first()

    def create(
        self,
        name: str,
        config_json: str,
        description: Optional[str] = None,
    ) -> SignalsConfig:
        """新增一条配置；name 重复则抛错或由调用方先检查"""
        row = SignalsConfig(
            name=name,
            description=description or "",
            config_json=config_json,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def update(
        self,
        name: str,
        config_json: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[SignalsConfig]:
        """按 name 更新；不存在返回 None"""
        row = self.get_by_name(name)
        if not row:
            return None
        if config_json is not None:
            row.config_json = config_json
        if description is not None:
            row.description = description
        self.session.flush()
        return row

    def delete(self, name: str) -> bool:
        """按 name 删除；存在则删并返回 True，否则返回 False"""
        row = self.get_by_name(name)
        if not row:
            return False
        self.session.delete(row)
        self.session.flush()
        return True

    def get_config_as_list(self, name: str) -> Optional[List[Dict[str, Any]]]:
        """按 name 查询并将 config_json 解析为 List[dict]，供 CzscSignals 使用"""
        row = self.get_by_name(name)
        if not row or not row.config_json:
            return None
        try:
            return json.loads(row.config_json)
        except (json.JSONDecodeError, TypeError):
            return None
