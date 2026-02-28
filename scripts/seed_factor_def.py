#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子定义表种子数据（可选）

向 factors 表插入若干条示例因子，便于测试 run_factor_screen 与 GET /api/v1/factors。

用法：
    python scripts/seed_factor_def.py

依赖：MySQL 已配置且已运行 scripts/db_init_mysql.py。
"""
from __future__ import annotations

import sys
from pathlib import Path


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    _bootstrap()
    from loguru import logger
    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.factors_repo import FactorsRepo

    # 示例因子：引用常见信号函数，便于跑因子筛选
    seeds = [
        {
            "name": "日线笔状态",
            "expression_or_signal_ref": "czsc.signals.cxt_bi_status_V230101",
            "description": "日线笔状态信号，用于因子筛选示例",
        },
        {
            "name": "日线均线基础",
            "expression_or_signal_ref": "czsc.signals.tas_ma_base_V230313",
            "description": "日线均线基础信号示例",
        },
    ]

    try:
        session_maker = get_session_maker()
        session = session_maker()
        try:
            repo = FactorsRepo(session)
            for s in seeds:
                repo.upsert(
                    name=s["name"],
                    expression_or_signal_ref=s["expression_or_signal_ref"],
                    description=s["description"],
                    is_active=1,
                )
            session.commit()
            logger.info(f"已写入 {len(seeds)} 条因子定义种子数据")
            return 0
        finally:
            session.close()
    except Exception as e:
        logger.exception(f"种子数据写入失败: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
