#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性迁移：将表 signal_func 重命名为 signals

在已将 table_signal_func 改为 table_signals 后，对已有数据库执行本脚本即可。
新环境直接运行 db_init_mysql.py 会创建 signals 表，无需本脚本。

用法：
    python scripts/migrate_rename_signal_func_to_signals.py
    python scripts/migrate_rename_signal_func_to_signals.py --dry-run  # 仅打印将要执行的 SQL
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
    parser = argparse.ArgumentParser(description="将表 signal_func 重命名为 signals")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 SQL 不执行")
    args = parser.parse_args()

    try:
        from sqlalchemy import text
        from backend.src.storage.mysql_db import get_engine
        from backend.src.utils.settings import get_settings
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    settings = get_settings()
    old_table = "signal_func"
    new_table = get_settings().table_signals  # "signals"
    sql = f"RENAME TABLE `{old_table}` TO `{new_table}`"

    if args.dry_run:
        logger.info(f"[dry-run] 将执行: {sql}")
        return 0

    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        logger.info(f"已执行: {sql}")
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        if "Unknown table" in str(e) or "1146" in str(e):
            logger.info("若该库为新环境，请直接运行 db_init_mysql.py，无需本脚本")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
