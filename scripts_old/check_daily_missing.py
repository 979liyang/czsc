#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测日线（daily）数据遗漏：从 metadata/stock_basic.csv 读取 symbol 与 list_date，以已上市 A 股为基准，
找出无数据或数据未更新至昨日的股票，并生成缺失列表文件。支持 --fetch 自动调用 fetch_tushare_daily 补拉。

期望：每只股票在 raw/daily/by_stock/stock_code={code}/ 下有 parquet，且最新日期 >= 昨日（当日数据尚未产出）。
- 无目录或无 parquet → 遗漏
- 有数据但最新日期 < 昨日 → 遗漏（需补拉）

补拉时请求到「今日」：接口有今日数据则落库今日，没有则落库到昨日最新。

使用示例：
  # 使用默认路径，缺失列表写入 .stock_data/metadata/missing_daily_stocks_YYYYMMDD_HHMMSS.txt
  python scripts/check_daily_missing.py

  # 检测并自动补拉遗漏（请求到今日，有今日则存今日否则昨日）
  python scripts/check_daily_missing.py --fetch

  # 指定输出文件
  python scripts/check_daily_missing.py --output .stock_data/metadata/missing_daily.txt

  # 仅检测不写文件（只打印遗漏数量与样例）
  python scripts/check_daily_missing.py --dry-run

  # 手动补拉（使用本脚本生成的缺失列表）
  python scripts/fetch_tushare_daily.py --from-missing-list .stock_data/metadata/missing_daily_stocks_20260213_195111.txt
"""

import argparse
import csv
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_BASE_PATH = project_root / ".stock_data"
FETCH_SCRIPT = project_root / "scripts" / "fetch_tushare_daily.py"


def _data_end_yyyymmdd() -> str:
    """数据截止日期：昨天（因当日数据尚未产出）"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _list_daily_parquet_files(base_dir: Path) -> List[Path]:
    """列出某股票日线目录下所有 parquet 文件"""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("*.parquet"))


def _get_latest_date_from_daily(stock_code: str, base_path: Path) -> Optional[str]:
    """
    获取某股票日线本地最新交易日（YYYYMMDD）。
    无数据或读取失败返回 None。
    """
    base_dir = base_path / "raw" / "daily" / "by_stock" / f"stock_code={stock_code}"
    files = _list_daily_parquet_files(base_dir)
    if not files:
        return None
    try:
        dfs = []
        for fp in files:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0 and "date" in df.columns:
                dfs.append(df)
        if not dfs:
            return None
        combined = pd.concat(dfs, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"])
        max_ts = combined["date"].max()
        return max_ts.strftime("%Y%m%d")
    except Exception as e:
        logger.debug(f"读取日线最新日期失败: {stock_code} - {e}")
        return None


def load_symbols_from_stock_basic(base_path: Path) -> List[str]:
    """
    从 metadata/stock_basic.csv 读取 symbol 与 list_date，仅保留 list_date 有效且为 A 股（SH/SZ）的代码。
    返回已上市股票 symbol 列表。
    """
    csv_path = base_path / "metadata" / "stock_basic.csv"
    out = []
    if not csv_path.exists():
        logger.warning(f"stock_basic 不存在: {csv_path}")
        return out
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = (row.get("symbol") or "").strip().upper()
                if not symbol or not symbol.endswith((".SH", ".SZ")):
                    continue
                list_date = (row.get("list_date") or "").strip()
                if len(list_date) >= 8 and list_date[:8].isdigit():
                    out.append(symbol)
    except Exception as e:
        logger.warning(f"读取 stock_basic 失败: {csv_path} - {e}")
    return sorted(out)


def check_daily_missing(
    base_path: Path,
    data_end_yyyymmdd: str,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    检测日线遗漏：无数据或最新日期早于 data_end 的股票。

    :return: (完全无数据的股票列表, (有数据但滞后的股票, 最新日期))
    """
    symbols = load_symbols_from_stock_basic(base_path)
    if not symbols:
        logger.warning("未从 stock_basic 加载到任何股票")
        return [], []

    no_data: List[str] = []
    stale: List[Tuple[str, str]] = []

    for symbol in symbols:
        latest = _get_latest_date_from_daily(symbol, base_path)
        if latest is None:
            no_data.append(symbol)
            continue
        if latest < data_end_yyyymmdd:
            stale.append((symbol, latest))

    return no_data, stale


def main() -> int:
    parser = argparse.ArgumentParser(
        description="检测日线数据遗漏，生成缺失股票列表文件",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="数据根目录，默认 .stock_data",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="缺失列表输出路径，默认 .stock_data/metadata/missing_daily_stocks_YYYYMMDD_HHMMSS.txt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅检测并打印统计，不写入文件",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="检测到遗漏后自动调用 fetch_tushare_daily 补拉（请求到今日，有今日则存今日否则昨日）",
    )
    parser.add_argument("--token", type=str, default=None, help="补拉时传给 fetch 的 Tushare token（可选）")
    parser.add_argument("--sleep", type=float, default=0, help="补拉时每只股票间隔秒数")
    args = parser.parse_args()

    base_path = Path(args.base_path).resolve() if args.base_path else DEFAULT_BASE_PATH
    if not base_path.exists():
        logger.error(f"数据根目录不存在: {base_path}")
        return 1

    data_end = _data_end_yyyymmdd()
    logger.info(f"数据截止日期（昨日）: {data_end}")

    no_data, stale = check_daily_missing(base_path, data_end)
    missing_symbols = sorted(set(no_data) | {s for s, _ in stale})

    logger.info(f"完全无日线数据: {len(no_data)} 只")
    logger.info(f"有数据但滞后于 {data_end}: {len(stale)} 只")
    logger.info(f"遗漏合计: {len(missing_symbols)} 只")

    if no_data and len(no_data) <= 20:
        logger.info(f"无数据样例: {no_data[:20]}")
    elif no_data:
        logger.info(f"无数据样例: {no_data[:10]} ...")
    if stale and len(stale) <= 10:
        for s, d in stale[:10]:
            logger.info(f"  滞后: {s} 最新={d}")
    elif stale:
        logger.info(f"滞后样例: {stale[0][0]} 最新={stale[0][1]} ...")

    if args.dry_run:
        return 0

    if not missing_symbols:
        logger.info("无遗漏，不生成缺失文件")
        return 0

    if args.output:
        out_path = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = base_path / "metadata" / f"missing_daily_stocks_{ts}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(missing_symbols) + "\n", encoding="utf-8")
    logger.info(f"已写入缺失列表: {out_path}，共 {len(missing_symbols)} 只")

    if args.fetch and FETCH_SCRIPT.exists():
        _run_fetch(out_path, token=args.token, sleep=args.sleep)
    elif args.fetch and not FETCH_SCRIPT.exists():
        logger.warning(f"未找到拉取脚本: {FETCH_SCRIPT}，跳过自动补拉")
    return 0


def _run_fetch(missing_list_path: Path, token: Optional[str] = None, sleep: float = 0) -> None:
    """
    调用 fetch_tushare_daily.py 对缺失列表中的股票补拉日线。
    请求到今日：接口有今日数据则落库今日，没有则落库到昨日最新。
    """
    cmd = [
        sys.executable,
        str(FETCH_SCRIPT),
        "--from-missing-list",
        str(missing_list_path.resolve()),
    ]
    if token:
        cmd.extend(["--token", token])
    if sleep and sleep > 0:
        cmd.extend(["--sleep", str(sleep)])
    logger.info(f"执行补拉: {' '.join(cmd)}")
    try:
        ret = subprocess.run(cmd, cwd=str(project_root), timeout=86400)
        if ret.returncode != 0:
            logger.warning(f"补拉进程退出码: {ret.returncode}")
    except subprocess.TimeoutExpired:
        logger.error("补拉超时")
    except Exception as e:
        logger.error(f"补拉失败: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
