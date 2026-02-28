#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
signals_config 表预设入库（可选）

向 signals_config 表写入若干条命名配置，便于 API/回测按名称加载。预设来自 README 示例或固定列表。

用法：
    python scripts/seed_signals_config.py           # 执行写入
    python scripts/seed_signals_config.py --dry-run # 仅打印不写库

依赖：已运行 scripts/db_init_mysql.py。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loguru import logger


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _presets() -> list[dict]:
    """预设列表：name、config_json、description"""
    return [
        {
            "name": "README示例日线组合",
            "description": "日线均线+五笔（与 README signals_config 示例一致）",
            "config_json": json.dumps(
                [
                    {
                        "name": "czsc.signals.tas_ma_base_V230313",
                        "freq": "日线",
                        "di": 1,
                        "ma_type": "SMA",
                        "timeperiod": 40,
                        "max_overlap": 5,
                    },
                    {
                        "name": "czsc.signals.cxt_five_bi_V230619",
                        "freq": "日线",
                        "di": 1,
                    },
                ],
                ensure_ascii=False,
            ),
        },
        {
            "name": "日线单信号笔状态",
            "description": "日线笔状态单信号配置",
            "config_json": json.dumps(
                [
                    {
                        "name": "czsc.signals.cxt_bi_status_V230101",
                        "freq": "日线",
                        "di": 1,
                    },
                ],
                ensure_ascii=False,
            ),
        },
    ]


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(
        description="向 signals_config 表写入预设配置"
    )
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写库")
    args = parser.parse_args()

    try:
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.signals_config_repo import SignalsConfigRepo
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    presets = _presets()
    if args.dry_run:
        logger.info(f"[dry-run] 将写入 {len(presets)} 条预设，示例：")
        for p in presets[:2]:
            logger.info(f"  name={p['name']} description={p['description']}")
        return 0

    session_maker = get_session_maker()
    session = session_maker()
    try:
        repo = SignalsConfigRepo(session)
        added = 0
        for p in presets:
            if repo.get_by_name(p["name"]):
                continue
            repo.create(
                name=p["name"],
                config_json=p["config_json"],
                description=p.get("description"),
            )
            added += 1
        session.commit()
        logger.info(f"signals_config 预设写入完成，本次新增 {added} 条（共 {len(presets)} 条预设）")
    except Exception as e:
        session.rollback()
        logger.exception(f"写入失败: {e}")
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
