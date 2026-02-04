# -*- coding: utf-8 -*-
"""
MySQL 数据库连接管理

说明：
- 采用 SQLAlchemy 2.0 同步引擎 + Session
- 为避免在 import 阶段就强依赖外部环境（驱动/连通性），引擎创建采用延迟初始化
"""

from __future__ import annotations

from typing import Generator, Optional

from loguru import logger

from ..utils.settings import get_settings

_ENGINE = None
_SESSION_MAKER = None


def _create_engine():
    """创建 SQLAlchemy Engine（延迟初始化）"""

    from sqlalchemy import create_engine

    settings = get_settings()
    if not settings.mysql_password:
        logger.warning("CZSC_MYSQL_PASSWORD 为空，将尝试以无密码方式连接 MySQL（如连接失败请检查 .env / 环境变量）")
    engine = create_engine(
        settings.mysql_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
        future=True,
    )
    return engine


def get_engine():
    """获取全局 Engine（单例）"""

    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _create_engine()
        logger.info("MySQL Engine 初始化完成")
    return _ENGINE


def get_session_maker():
    """获取 Session maker（单例）"""

    global _SESSION_MAKER
    if _SESSION_MAKER is None:
        from sqlalchemy.orm import sessionmaker

        _SESSION_MAKER = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False, future=True)
        logger.info("MySQL SessionMaker 初始化完成")
    return _SESSION_MAKER


def get_db_session() -> Generator:
    """FastAPI 依赖：获取数据库会话"""

    session = get_session_maker()()
    try:
        yield session
    finally:
        session.close()


def ping_mysql(timeout_seconds: int = 3) -> bool:
    """检查 MySQL 连通性（用于脚本/健康检查）"""

    try:
        from sqlalchemy import text

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"MySQL 连通性检查失败：{e}")
        return False

