# -*- coding: utf-8 -*-
"""
JWT 签发与解析
"""
from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt

from .settings import get_settings


def create_access_token(sub: Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    签发 access_token，sub 建议为 user_id（整数或字符串）。
    """
    settings = get_settings()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    payload = {"sub": str(sub), "exp": expire}
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[dict]:
    """解析 token，失败返回 None"""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
