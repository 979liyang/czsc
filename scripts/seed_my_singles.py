#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
my_singles 测试数据批量导入（仅限测试/演示环境）

为指定 user_id 批量插入收藏项，便于本地或测试环境造数。生产环境请勿使用；用户收藏应通过 API 由用户自行入库。

用法：
    python scripts/seed_my_singles.py --user-id 1
    python scripts/seed_my_singles.py --user-id 1 --dry-run
    python scripts/seed_my_singles.py --user-id 1 --file items.json  # 从 JSON 文件读取列表

JSON 文件格式（可选）：[{"item_type": "signal"|"symbol", "item_id": "xxx", "sort_order": 0}, ...]

依赖：已运行 db_init_mysql.py，且 user 表中存在对应用户。
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


def _default_items() -> list[dict]:
    """默认测试数据：若干 signal/symbol"""
    return [
        {"item_type": "signal", "item_id": "czsc.signals.cxt_bi_status_V230101", "sort_order": 0},
        {"item_type": "signal", "item_id": "czsc.signals.tas_ma_base_V230313", "sort_order": 1},
        {"item_type": "symbol", "item_id": "000001.SZ", "sort_order": 2},
    ]


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(
        description="为指定 user_id 批量插入 my_singles（仅限测试环境）"
    )
    parser.add_argument("--user-id", type=int, required=True, help="用户 ID")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写库")
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="JSON 文件路径，每行为 [{\"item_type\", \"item_id\", \"sort_order\"}, ...]",
    )
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            logger.error(f"文件不存在: {path}")
            return 1
        try:
            items = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"解析 JSON 失败: {e}")
            return 1
    else:
        items = _default_items()

    if not items:
        logger.warning("无待插入项")
        return 0

    try:
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.my_singles_repo import MySinglesRepo
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    if args.dry_run:
        logger.info(
            f"[dry-run] 将为 user_id={args.user_id} 写入 {len(items)} 条 my_singles"
        )
        for i, it in enumerate(items[:5]):
            logger.info(f"  {i+1}. {it.get('item_type')} {it.get('item_id')}")
        return 0

    session_maker = get_session_maker()
    session = session_maker()
    try:
        repo = MySinglesRepo(session)
        for it in items:
            item_type = it.get("item_type") or "signal"
            item_id = str(it.get("item_id", ""))
            sort_order = int(it.get("sort_order", 0))
            if item_type not in ("signal", "symbol") or not item_id:
                logger.warning(f"跳过无效项: {it}")
                continue
            repo.add(args.user_id, item_type, item_id, sort_order)
        session.commit()
        logger.info(
            f"已为 user_id={args.user_id} 写入 {len(items)} 条 my_singles（仅测试用）"
        )
    except Exception as e:
        session.rollback()
        logger.exception(f"写入失败: {e}")
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
