#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 signals 表全量同步到 factors 表

使所有已入库信号在 factors 中有对应因子（name、expression_or_signal_ref、description、is_active）。

用法：
    python scripts/sync_factor_def_from_signal_func.py           # 执行同步
    python scripts/sync_factor_def_from_signal_func.py --dry-run # 仅打印不写库
    python scripts/sync_factor_def_from_signal_func.py --active-only # 仅同步 is_active=1 的信号

依赖：先运行 scripts/db_init_mysql.py，建议先运行 scripts/sync_czsc_signals_to_db.py 再执行本脚本。
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
    parser = argparse.ArgumentParser(
        description="从 signals 全量同步到 factors"
    )
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写库")
    parser.add_argument(
        "--active-only",
        action="store_true",
        help="仅同步 signals 中 is_active=1 的记录",
    )
    args = parser.parse_args()

    try:
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.signals_repo import SignalsRepo
        from backend.src.storage.factors_repo import FactorsRepo
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    session_maker = get_session_maker()
    session = session_maker()
    try:
        sig_repo = SignalsRepo(session)
        rows = sig_repo.list_all(active_only=args.active_only)
        if not rows:
            logger.warning("signals 表无数据，请先运行 sync_czsc_signals_to_db.py")
            return 0

        if args.dry_run:
            logger.info(
                f"[dry-run] 将同步 {len(rows)} 条到 factors，前 3 条示例："
            )
            for r in rows[:3]:
                ref = (
                    f"{r.module_path}.{r.name}"
                    if r.module_path
                    else r.name
                )
                logger.info(f"  name={r.name} expression_or_signal_ref={ref}")
            return 0

        factor_repo = FactorsRepo(session)
        for r in rows:
            expression_or_signal_ref = (
                f"{r.module_path}.{r.name}" if r.module_path else r.name
            )
            factor_repo.upsert(
                name=r.name,
                expression_or_signal_ref=expression_or_signal_ref,
                description=r.description,
                is_active=r.is_active,
            )
        session.commit()
        logger.info(f"已从 signals 同步 {len(rows)} 条到 factors 表")
    except Exception as e:
        session.rollback()
        logger.exception(f"同步失败: {e}")
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
