#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 表结构初始化 / 升级（幂等）

根据 backend 中 ORM 模型创建或校验表结构；若数据库不存在则先创建库再建表。

用法：
    python scripts/db_init_mysql.py

环境变量（参考 backend/src/utils/settings.py）：
    CZSC_MYSQL_HOST / CZSC_MYSQL_PORT / CZSC_MYSQL_USER / CZSC_MYSQL_PASSWORD / CZSC_MYSQL_DATABASE
    可选：CZSC_MYSQL_CHARSET（默认 utf8mb4）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _is_unknown_database_error(err: Exception) -> bool:
    """判断是否为「数据库不存在」类错误"""
    msg = str(err)
    return "Unknown database" in msg or "(1049," in msg or "1049" in msg


def _create_database_if_not_exists(settings) -> None:
    """在无 database 的 URL 下执行 CREATE DATABASE IF NOT EXISTS"""
    from sqlalchemy import create_engine, text

    if not re.fullmatch(r"[0-9A-Za-z_]+", settings.mysql_database or ""):
        raise ValueError("CZSC_MYSQL_DATABASE 只能包含字母、数字、下划线")
    charset = settings.mysql_charset or "utf8mb4"
    if not re.fullmatch(r"[0-9A-Za-z_]+", charset):
        raise ValueError("CZSC_MYSQL_CHARSET 只能包含字母、数字、下划线")

    user = quote_plus(settings.mysql_user or "")
    password = quote_plus(settings.mysql_password or "")
    url = (
        f"mysql+pymysql://{user}:{password}@{settings.mysql_host}:{settings.mysql_port}/"
        f"?charset={charset}"
    )
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600, future=True)
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE DATABASE IF NOT EXISTS "
                f"`{settings.mysql_database}` CHARACTER SET {charset}"
            )
        )
        conn.commit()
    logger.info(f"数据库已就绪：{settings.mysql_database}")


def main() -> int:
    _bootstrap()
    try:
        from backend.src.models.mysql_models import Base
        from backend.src.storage.mysql_db import get_engine
        from backend.src.utils.settings import get_settings
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    settings = get_settings()
    logger.info("开始创建/校验 MySQL 表结构（create_all 幂等）")
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        if _is_unknown_database_error(e):
            logger.warning(f"数据库不存在：{settings.mysql_database}，尝试先创建库再建表")
            _create_database_if_not_exists(settings)
            engine = get_engine()
            Base.metadata.create_all(bind=engine)
        else:
            raise
    logger.info("MySQL 表结构初始化完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
