# -*- coding: utf-8 -*-
"""
分钟数据维护统一 CLI

子命令：
- scan：扫描每只股票分钟起止时间 → coverage
- daily：按交易日统计分钟条数 → daily_stats
- check：按日完整性校验并生成缺口 → gaps

示例：
    python scripts/stock_minute_cli.py scan --market SH,SZ
    python scripts/stock_minute_cli.py daily --sdt 2024-01-01 --edt 2024-01-31 --market SH,SZ
    python scripts/stock_minute_cli.py check --date 2024-01-04 --market SH,SZ
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loguru import logger


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _setup_logger() -> None:
    Path("logs").mkdir(exist_ok=True)
    logger.remove()
    logger.add(
        "logs/stock_minute_cli_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    )


def _parse_markets(v: str) -> list[str] | None:
    v = (v or "").strip()
    if not v:
        return None
    return [x.strip().upper() for x in v.split(",") if x.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="分钟数据维护统一 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="扫描分钟起止时间 → coverage")
    p_scan.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    p_scan.add_argument("--limit", type=int, default=0, help="股票数量限制，0 表示不限制")

    p_daily = sub.add_parser("daily", help="按日统计分钟条数 → daily_stats")
    p_daily.add_argument("--sdt", required=True, help="开始日期 YYYY-MM-DD")
    p_daily.add_argument("--edt", required=True, help="结束日期 YYYY-MM-DD")
    p_daily.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    p_daily.add_argument("--limit", type=int, default=0, help="股票数量限制，0 表示不限制")

    p_check = sub.add_parser("check", help="按日完整性校验并生成缺口 → gaps")
    p_check.add_argument("--symbol", default="", help="股票代码（可选）")
    p_check.add_argument("--date", default="", help="单日校验 YYYY-MM-DD（可选）")
    p_check.add_argument("--sdt", default="", help="开始日期 YYYY-MM-DD（可选）")
    p_check.add_argument("--edt", default="", help="结束日期 YYYY-MM-DD（可选）")
    p_check.add_argument("--market", default="", help="市场过滤，如 SH,SZ；为空表示不过滤")
    p_check.add_argument("--limit", type=int, default=0, help="股票数量限制，0 表示不限制")

    return parser


def _run_module(module: str, argv: list[str]) -> int:
    """
    统一入口：复用既有脚本 main，不重复实现逻辑

    说明：这里不使用 subprocess，直接调用目标脚本的 main 函数。
    """

    import importlib
    import sys

    mod = importlib.import_module(module)
    if not hasattr(mod, "main"):
        raise RuntimeError(f"{module} 缺少 main()")

    old_argv = sys.argv
    try:
        sys.argv = [module] + argv
        return int(mod.main())
    finally:
        sys.argv = old_argv


def main() -> int:
    _bootstrap()
    _setup_logger()
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.cmd == "scan":
            argv = []
            if args.market:
                argv += ["--market", args.market]
            argv += ["--limit", str(args.limit)]
            return _run_module("scripts.stock_minute_scan", argv)

        if args.cmd == "daily":
            argv = ["--sdt", args.sdt, "--edt", args.edt, "--limit", str(args.limit)]
            if args.market:
                argv += ["--market", args.market]
            return _run_module("scripts.stock_minute_scan_daily", argv)

        if args.cmd == "check":
            argv = ["--limit", str(args.limit)]
            if args.symbol:
                argv += ["--symbol", args.symbol]
            if args.date:
                argv += ["--date", args.date]
            if args.sdt:
                argv += ["--sdt", args.sdt]
            if args.edt:
                argv += ["--edt", args.edt]
            if args.market:
                argv += ["--market", args.market]
            return _run_module("scripts.stock_minute_check", argv)

        raise RuntimeError(f"未知命令：{args.cmd}")
    except Exception as e:
        logger.error(f"执行失败：{e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

