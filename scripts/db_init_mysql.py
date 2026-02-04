# -*- coding: utf-8 -*-
"""
初始化 / 升级 MySQL 表结构（幂等）

用法示例：
    python scripts/db_init_mysql.py

环境变量（可选）：
    CZSC_MYSQL_HOST / CZSC_MYSQL_PORT / CZSC_MYSQL_USER / CZSC_MYSQL_PASSWORD / CZSC_MYSQL_DATABASE
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote_plus

def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _get_logger():
    """获取 logger（优先 loguru；未安装则降级为 print）"""

    try:
        from loguru import logger as _logger

        return _logger
    except Exception:
        class _PrintLogger:
            def info(self, msg: str):
                print(f"[INFO] {msg}")

            def warning(self, msg: str):
                print(f"[WARN] {msg}")

            def error(self, msg: str):
                print(f"[ERROR] {msg}")

        return _PrintLogger()


def main() -> int:
    """脚本入口"""

    _bootstrap()
    logger = _get_logger()
    try:
        from backend.src.storage.mysql_db import get_engine
        from backend.src.models.mysql_models import Base
        from backend.src.utils.settings import get_settings
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    engine = get_engine()
    logger.info("开始创建/检查 MySQL 表结构（create_all 幂等）")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        if _is_unknown_database_error(e):
            settings = get_settings()
            logger.warning(f"MySQL 数据库不存在：{settings.mysql_database}，将尝试自动创建后重试")
            _create_database_if_not_exists(settings, logger)
            Base.metadata.create_all(bind=get_engine())
        else:
            raise
    logger.info("MySQL 表结构初始化完成")
    return 0


def _is_unknown_database_error(err: Exception) -> bool:
    """判断是否为“数据库不存在”的异常"""

    msg = str(err)
    return "Unknown database" in msg or "(1049," in msg or "1049" in msg


def _create_database_if_not_exists(settings, logger) -> None:
    """创建数据库（如果不存在）"""

    import re
    from sqlalchemy import create_engine, text

    if not re.fullmatch(r"[0-9A-Za-z_]+", settings.mysql_database or ""):
        raise ValueError("CZSC_MYSQL_DATABASE 只能包含字母/数字/下划线")
    if not re.fullmatch(r"[0-9A-Za-z_]+", settings.mysql_charset or ""):
        raise ValueError("CZSC_MYSQL_CHARSET 只能包含字母/数字/下划线")

    user = quote_plus(settings.mysql_user)
    password = quote_plus(settings.mysql_password)
    # 这里不依赖 settings.mysql_url()（它包含 database），避免再次触发 1049
    url = f"mysql+pymysql://{user}:{password}@{settings.mysql_host}:{settings.mysql_port}/?charset={settings.mysql_charset}"
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600, future=True)
    with engine.connect() as conn:
        conn.execute(
            text(
                "CREATE DATABASE IF NOT EXISTS "
                f"`{settings.mysql_database}` CHARACTER SET {settings.mysql_charset}"
            )
        )
        conn.commit()
    logger.info(f"MySQL 数据库已就绪：{settings.mysql_database}")


if __name__ == "__main__":
    raise SystemExit(main())

