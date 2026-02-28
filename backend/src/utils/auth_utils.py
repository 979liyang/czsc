# -*- coding: utf-8 -*-
"""
认证工具：密码哈希与校验（直接使用 bcrypt，避免 passlib 与新版 bcrypt 不兼容）
"""
import bcrypt

# bcrypt 最多 72 字节，超出部分截断
_MAX_PASSWORD_BYTES = 72


def _to_bytes(plain: str) -> bytes:
    """转为 bytes 并截断到 72 字节"""
    b = plain.encode("utf-8")
    if len(b) > _MAX_PASSWORD_BYTES:
        b = b[:_MAX_PASSWORD_BYTES]
    return b


def hash_password(plain: str) -> str:
    """对明文密码做 bcrypt 哈希"""
    return bcrypt.hashpw(_to_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否一致"""
    try:
        return bcrypt.checkpw(_to_bytes(plain), hashed.encode("utf-8"))
    except Exception:
        return False
