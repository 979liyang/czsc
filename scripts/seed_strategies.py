#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略库种子数据：将 czsc.strategies 中全部 create_* 策略写入 strategies 表

覆盖：create_single_ma_long/short、create_macd_long/short、create_cci_long/short、
create_emv_long/short、create_third_buy_long、create_third_sell_short、create_long_short_bi。
按 name 做 upsert，幂等；支持 --dry-run、--force。

用法：
    python scripts/seed_strategies.py           # 执行写入（幂等 upsert）
    python scripts/seed_strategies.py --dry-run # 仅打印不写库
    python scripts/seed_strategies.py --force   # 强制更新已存在记录的 config_json
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


def main() -> int:
    _bootstrap()
    parser = argparse.ArgumentParser(description="将 czsc 全部策略入库到 strategies 表")
    parser.add_argument("--dry-run", action="store_true", help="仅打印不写库")
    parser.add_argument("--force", action="store_true", help="强制更新已存在策略的 config_json")
    args = parser.parse_args()

    try:
        from czsc.strategies import (
            create_single_ma_long,
            create_single_ma_short,
            create_macd_long,
            create_macd_short,
            create_cci_long,
            create_cci_short,
            create_emv_long,
            create_emv_short,
            create_third_buy_long,
            create_third_sell_short,
            create_long_short_bi,
        )
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.strategies_repo import StrategiesRepo
    except Exception as e:
        logger.error(f"导入失败：{e}")
        return 1

    symbol = "000001.SZ"
    seeds = []

    # 单均线多头/空头（多种 ma_name）
    for ma_name in ["SMA#5", "SMA#10", "SMA#20", "SMA#40"]:
        pos = create_single_ma_long(symbol, ma_name, is_stocks=True)
        seeds.append({"name": pos.name, "strategy_type": "single_ma_long", "pos": pos})
    for ma_name in ["SMA#5", "SMA#10", "SMA#20", "SMA#40"]:
        pos = create_single_ma_short(symbol, ma_name, is_stocks=True)
        seeds.append({"name": pos.name, "strategy_type": "single_ma_short", "pos": pos})

    # MACD 多头/空头
    pos = create_macd_long(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "macd_long", "pos": pos})
    pos = create_macd_short(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "macd_short", "pos": pos})

    # CCI 多头/空头
    pos = create_cci_long(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "cci_long", "pos": pos})
    pos = create_cci_short(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "cci_short", "pos": pos})

    # EMV 多头/空头
    pos = create_emv_long(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "emv_long", "pos": pos})
    pos = create_emv_short(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "emv_short", "pos": pos})

    # 缠论三买/三卖
    pos = create_third_buy_long(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "third_buy_long", "pos": pos})
    pos = create_third_sell_short(symbol, is_stocks=True)
    seeds.append({"name": pos.name, "strategy_type": "third_sell_short", "pos": pos})

    # 笔非多即空（30分钟/60分钟/日线）
    for freq in ["30分钟", "60分钟", "日线"]:
        pos = create_long_short_bi(symbol, freq=freq, is_stocks=True)
        seeds.append({"name": pos.name, "strategy_type": "long_short_bi", "pos": pos})

    if args.dry_run:
        logger.info(f"[dry-run] 将写入 {len(seeds)} 条策略，前 5 条：")
        for s in seeds[:5]:
            cfg = s["pos"].dump()
            logger.info(f"  name={s['name']} strategy_type={s['strategy_type']} config_keys={list(cfg.keys())}")
        return 0

    session_maker = get_session_maker()
    session = session_maker()
    try:
        repo = StrategiesRepo(session)
        for s in seeds:
            config_json = json.dumps(s["pos"].dump(), ensure_ascii=False)
            repo.upsert(
                name=s["name"],
                description=f"czsc 策略：{s['strategy_type']}",
                strategy_type=s["strategy_type"],
                config_json=config_json,
                is_active=1,
            )
        session.commit()
        logger.info(f"已写入 {len(seeds)} 条策略到 strategies 表（幂等 upsert）")
    except Exception as e:
        session.rollback()
        logger.exception(f"种子数据写入失败: {e}")
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
