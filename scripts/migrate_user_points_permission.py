#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户与积分权限表结构迁移（幂等）

为 user 表增加昵称、签名、手机、邮箱、积分、身份、特殊权限列表、updated_at；
创建 points_tier、special_permission、user_special_permission、my_singles 表由 db_init_mysql.py 的 create_all 完成。
本脚本仅对已有 user 表执行 ALTER 添加新列（MySQL 无 ADD COLUMN IF NOT EXISTS 时逐列 try/except）。

用法：
    python scripts/migrate_user_points_permission.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _bootstrap()
    try:
        from sqlalchemy import text

        from backend.src.storage.mysql_db import get_engine
        from backend.src.utils.settings import get_settings
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    settings = get_settings()
    table_user = settings.table_user
    engine = get_engine()

    logger.info("为 user 表添加扩展列（幂等）")
    columns = [
        ("nickname", "VARCHAR(64) NULL COMMENT '昵称'"),
        ("signature", "VARCHAR(255) NULL COMMENT '签名'"),
        ("phone", "VARCHAR(32) NULL COMMENT '手机号'"),
        ("email", "VARCHAR(128) NULL COMMENT '邮箱'"),
        ("points", "INT NOT NULL DEFAULT 0 COMMENT '积分'"),
        ("role", "VARCHAR(16) NOT NULL DEFAULT 'user' COMMENT '身份'"),
        ("special_permission_ids", "TEXT NULL COMMENT '特殊权限ID列表'"),
        ("updated_at", "DATETIME NULL ON UPDATE CURRENT_TIMESTAMP"),
    ]
    with engine.connect() as conn:
        for col, defn in columns:
            try:
                conn.execute(text(f"ALTER TABLE `{table_user}` ADD COLUMN `{col}` {defn}"))
                conn.commit()
                logger.info(f"已添加列 {table_user}.{col}")
            except Exception as e:
                if "Duplicate column" in str(e) or "1060" in str(e):
                    conn.rollback()
                    logger.debug(f"列已存在跳过: {col}")
                else:
                    raise
    logger.info("请先运行 python scripts/db_init_mysql.py 以创建 points_tier 等新表")
    logger.info("迁移完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
