# -*- coding: utf-8 -*-
"""
用户仓储：按用户名查询、创建用户
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import User


class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        """按用户名查询"""
        return self.session.query(User).filter(User.username == username).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        """按 id 查询"""
        return self.session.get(User, user_id)

    def create_user(self, username: str, password_hash: str) -> User:
        """创建用户，返回新用户（已 flush 以便拿到 id）"""
        user = User(username=username, password_hash=password_hash)
        self.session.add(user)
        self.session.flush()
        return user
