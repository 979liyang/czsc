#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性迁移：将表 factor_def 重命名为 factors，并添加 signals_config 列

在已将 table_factor_def 改为 table_factors 且模型增加 signals_config 后，
对已有数据库执行本脚本即可。新环境直接运行 db_init_mysql.py 会创建 factors 表，无需本脚本。

用法：
    python scripts/migrate_rename_factor_def_to_factors.py
    python scripts/migrate_rename_factor_def_to_factors.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="将表 factor_def 重命名为 factors 并添加 signals_config")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 SQL 不执行")
    args = parser.parse_args()

    try:
        from sqlalchemy import text
        from backend.src.storage.mysql_db import get_engine
        from backend.src.utils.settings import get_settings
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    new_table = get_settings().table_factors  # "factors"
    if args.dry_run:
        logger.info(f"[dry-run] 将执行: RENAME TABLE factor_def TO {new_table}")
        logger.info("[dry-run] 将执行: ALTER TABLE ... ADD COLUMN signals_config TEXT NULL")
        return 0

    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text(f"RENAME TABLE `factor_def` TO `{new_table}`"))
            conn.commit()
        logger.info(f"已执行: RENAME TABLE factor_def TO {new_table}")
        with engine.connect() as conn:
            conn.execute(text(
                f"ALTER TABLE `{new_table}` ADD COLUMN `signals_config` TEXT NULL "
                "COMMENT '多条信号配置 JSON 数组' AFTER `expression_or_signal_ref`"
            ))
            conn.commit()
        logger.info("已添加列 signals_config")
    except Exception as e:
        err = str(e)
        if "Unknown table" in err or "1146" in err:
            logger.info("若该库为新环境，请直接运行 db_init_mysql.py，无需本脚本")
        elif "Duplicate column" in err or "1060" in err:
            logger.info("signals_config 列已存在，仅需确认表名已为 factors")
        else:
            logger.error(f"迁移失败: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
