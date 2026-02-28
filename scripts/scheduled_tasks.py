#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务统一入口（供 cron 或任务调度调用）

子命令：
- init：初始化/升级 MySQL 表结构（调用 db_init_mysql.py）
- fetch_daily：拉取日线数据（调用 scripts/daily/fetch.py）
- fetch_minute：扫描分钟数据覆盖并更新 coverage 表（调用 scripts/minute/scan.py）
- fetch_minute_data：拉取分钟 K 线数据（调用 scripts/minute/fetch.py）
- fetch_index：拉取指数日线数据（调用 scripts/index/fetch.py）
- run_screen：执行信号/因子筛选并写入 screen_result 表（调用 backend 筛选逻辑）

用法示例：
    python scripts/scheduled_tasks.py init
    python scripts/scheduled_tasks.py fetch_daily
    python scripts/scheduled_tasks.py fetch_minute --market SH,SZ
    python scripts/scheduled_tasks.py fetch_index --skip-if-done-today
    python scripts/scheduled_tasks.py run_screen --trade-date 20260222

Cron 示例见 docs/instructions/cron_examples.md。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _bootstrap_backend() -> None:
    """将项目根目录加入 sys.path，便于从 scripts 内 import backend"""
    root = _project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _run_script(script_path: Path, extra_args: list[str]) -> int:
    """在项目根目录下执行脚本，返回退出码。"""
    root = _project_root()
    cmd = [sys.executable, str(script_path)] + extra_args
    logger.info(f"执行: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(root),
            timeout=3600 * 2,
        )
        ret = result.returncode
        if ret == 2:
            logger.warning("子进程返回 2，已规范为 1")
            return 1
        return ret
    except subprocess.TimeoutExpired:
        logger.error("命令执行超时")
        return 1
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1


def cmd_init(_: argparse.Namespace) -> int:
    """初始化/升级 MySQL 表结构"""
    script = _project_root() / "scripts" / "db_init_mysql.py"
    if not script.exists():
        logger.error(f"脚本不存在: {script}")
        return 1
    return _run_script(script, [])


def cmd_fetch_daily(args: argparse.Namespace) -> int:
    """拉取日线数据"""
    if getattr(args, "skip_if_done_today", False):
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                if repo.get_today_success("daily"):
                    logger.info("今日已执行过 daily，跳过")
                    return 0
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"检查今日是否已执行失败，继续执行拉取: {e}")

    use_simple = getattr(args, "test_simple", False)
    if use_simple:
        script = _project_root() / "scripts" / "daily" / "fetch_daily_simple.py"
        logger.info("使用极简日线测试脚本（--test-simple）")
    else:
        script = _project_root() / "scripts" / "daily" / "fetch.py"
    if not script.exists():
        logger.error(f"脚本不存在: {script}")
        return 1
    extra = [] if use_simple else []
    if not use_simple:
        if getattr(args, "start_date", None):
            extra.extend(["--start-date", args.start_date])
        if getattr(args, "end_date", None):
            extra.extend(["--end-date", args.end_date])
        if getattr(args, "check", False):
            extra.append("--check")
    ret = _run_script(script, extra)

    if ret == 0:
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                repo.create(task_type="daily", trigger="scheduled", status="success")
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"写入 data_fetch_run 记录失败: {e}")
    return ret


def cmd_fetch_minute(args: argparse.Namespace) -> int:
    """扫描分钟数据覆盖并更新 coverage 表"""
    if getattr(args, "skip_if_done_today", False):
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                if repo.get_today_success("minute"):
                    logger.info("今日已执行过 minute，跳过")
                    return 0
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"检查今日是否已执行失败，继续执行: {e}")

    script = _project_root() / "scripts" / "minute" / "scan.py"
    if not script.exists():
        logger.error(f"脚本不存在: {script}")
        return 1
    extra = []
    if getattr(args, "market", None):
        extra.extend(["--market", args.market])
    if getattr(args, "limit", 0):
        extra.extend(["--limit", str(args.limit)])
    ret = _run_script(script, extra)

    if ret == 0:
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                repo.create(task_type="minute", trigger="scheduled", status="success")
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"写入 data_fetch_run 记录失败: {e}")
    return ret


def cmd_fetch_minute_data(args: argparse.Namespace) -> int:
    """拉取分钟 K 线数据（调用 scripts/minute/fetch.py）"""
    if getattr(args, "skip_if_done_today", False):
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                if repo.get_today_success("minute"):
                    logger.info("今日已执行过 minute，跳过")
                    return 0
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"检查今日是否已执行失败，继续执行: {e}")

    script = _project_root() / "scripts" / "minute" / "fetch.py"
    if not script.exists():
        logger.error(f"脚本不存在: {script}")
        return 1
    extra = []
    if getattr(args, "end_date", None):
        extra.extend(["--end-date", args.end_date])
    if getattr(args, "limit", 0):
        extra.extend(["--limit", str(args.limit)])
    ret = _run_script(script, extra)

    if ret == 0:
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                repo.create(task_type="minute", trigger="scheduled", status="success")
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"写入 data_fetch_run 记录失败: {e}")
    return ret


def cmd_fetch_index(args: argparse.Namespace) -> int:
    """拉取指数日线数据（调用 scripts/index/fetch.py）"""
    if getattr(args, "skip_if_done_today", False):
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                if repo.get_today_success("index"):
                    logger.info("今日已执行过 index，跳过")
                    return 0
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"检查今日是否已执行失败，继续执行: {e}")

    script = _project_root() / "scripts" / "index" / "fetch.py"
    if not script.exists():
        logger.error(f"脚本不存在: {script}")
        return 1
    extra = []
    if getattr(args, "start_date", None):
        extra.extend(["--start-date", args.start_date])
    if getattr(args, "end_date", None):
        extra.extend(["--end-date", args.end_date])
    ret = _run_script(script, extra)

    if ret == 0:
        _bootstrap_backend()
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.data_fetch_run_repo import DataFetchRunRepo

            session = get_session_maker()()
            try:
                repo = DataFetchRunRepo(session)
                repo.create(task_type="index", trigger="scheduled", status="success")
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning(f"写入 data_fetch_run 记录失败: {e}")
    return ret


def cmd_run_screen(args: argparse.Namespace) -> int:
    """执行信号/因子筛选并写入结果表"""
    root = _project_root()
    trade_date = getattr(args, "trade_date", None) or ""
    cmd = [
        sys.executable,
        "-m",
        "backend.src.jobs.screen_task",
        "--trade-date",
        trade_date,
    ]
    if getattr(args, "market", None):
        cmd.extend(["--market", args.market])
    logger.info(f"执行: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=str(root), timeout=3600 * 2)
        return result.returncode
    except subprocess.TimeoutExpired:
        logger.error("筛选任务执行超时")
        return 1
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="定时任务统一入口（init / fetch_daily / fetch_minute / run_screen）"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="初始化/升级 MySQL 表结构")

    p_daily = subparsers.add_parser("fetch_daily", help="拉取日线数据")
    p_daily.add_argument("--start-date", type=str, default="", help="开始日期 YYYYMMDD")
    p_daily.add_argument("--end-date", type=str, default="", help="结束日期 YYYYMMDD")
    p_daily.add_argument("--check", action="store_true", help="检测并拉取缺失日线")
    p_daily.add_argument("--skip-if-done-today", action="store_true", dest="skip_if_done_today",
                         help="若今日已有成功记录则跳过")
    p_daily.add_argument("--test-simple", action="store_true", dest="test_simple",
                         help="使用极简测试脚本验证退出码，不拉取真实数据")

    p_minute = subparsers.add_parser("fetch_minute", help="扫描分钟数据覆盖并更新 coverage")
    p_minute.add_argument("--market", type=str, default="SH,SZ", help="市场，如 SH,SZ")
    p_minute.add_argument("--limit", type=int, default=0, help="限制扫描股票数，0 表示不限制")
    p_minute.add_argument("--skip-if-done-today", action="store_true", dest="skip_if_done_today",
                         help="若今日已有成功记录则跳过")

    p_minute_data = subparsers.add_parser("fetch_minute_data", help="拉取分钟 K 线数据（minute/fetch.py）")
    p_minute_data.add_argument("--end-date", type=str, default="", help="结束日期 YYYYMMDD")
    p_minute_data.add_argument("--limit", type=int, default=0, help="限制股票数，0 表示不限制")
    p_minute_data.add_argument("--skip-if-done-today", action="store_true", dest="skip_if_done_today",
                               help="若今日已有成功记录则跳过")

    p_index = subparsers.add_parser("fetch_index", help="拉取指数日线数据（index/fetch.py）")
    p_index.add_argument("--start-date", type=str, default="", help="开始日期 YYYYMMDD")
    p_index.add_argument("--end-date", type=str, default="", help="结束日期 YYYYMMDD")
    p_index.add_argument("--skip-if-done-today", action="store_true", dest="skip_if_done_today",
                         help="若今日已有成功记录则跳过")

    p_screen = subparsers.add_parser("run_screen", help="执行信号/因子筛选")
    p_screen.add_argument(
        "--trade-date",
        type=str,
        default="",
        help="交易日 YYYYMMDD，默认当天",
    )
    p_screen.add_argument("--market", type=str, default="", help="市场过滤，如 SH,SZ")

    args = parser.parse_args()
    handlers = {
        "init": cmd_init,
        "fetch_daily": cmd_fetch_daily,
        "fetch_minute": cmd_fetch_minute,
        "fetch_minute_data": cmd_fetch_minute_data,
        "fetch_index": cmd_fetch_index,
        "run_screen": cmd_run_screen,
    }
    handler = handlers[args.command]
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
