#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 czsc.signals 全部信号同步到 signals 表（全量 upsert）

用法：
    python scripts/sync_czsc_signals_to_db.py           # 执行同步
    python scripts/sync_czsc_signals_to_db.py --dry-run # 仅打印，不写库
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
    parser = argparse.ArgumentParser(description="同步 czsc.signals 到 signals 表")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写库")
    parser.add_argument("--signals-module", default="czsc.signals", help="信号模块名")
    args = parser.parse_args()

    try:
        from backend.src.services.signal_sync_service import build_signal_func_rows
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.signals_repo import SignalsRepo
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    rows = build_signal_func_rows(signals_module=args.signals_module)
    if not rows:
        logger.warning("未获取到任何信号，请检查 czsc.signals 是否可导入")
        return 0

    if args.dry_run:
        logger.info(f"[dry-run] 将同步 {len(rows)} 条，前 3 条示例：")
        for r in rows[:3]:
            logger.info(f"  {r.get('name')} | {r.get('category')} | {r.get('param_template') or '-'}")
        return 0

    session_maker = get_session_maker()
    session = session_maker()
    try:
        repo = SignalsRepo(session)
        for r in rows:
            repo.upsert(
                name=r["name"],
                module_path=r.get("module_path"),
                category=r.get("category"),
                param_template=r.get("param_template"),
                description=r.get("description"),
                is_active=1,
            )
        session.commit()
        logger.info(f"已同步 {len(rows)} 条到 signals 表")
    except Exception as e:
        session.rollback()
        logger.error(f"同步失败：{e}", exc_info=True)
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
