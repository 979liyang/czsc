#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测指数日线数据遗漏：从 metadata/index_basic.csv 读取指数列表，
找出无数据或数据未更新至昨日的指数，生成缺失列表。支持 --fetch 自动调用 fetch_tushare_index_daily 补拉。

数据位置：raw/daily/by_index/index_code={code}/ 下 parquet，最新日期应 >= 昨日。

使用示例：
  python scripts/index/check.py
  python scripts/index/check.py --fetch
  python scripts/index/check.py --output .stock_data/metadata/missing_index_daily.txt
  python scripts/index/check.py --dry-run
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
FETCH_SCRIPT = project_root / "scripts" / "fetch_tushare_index_daily.py"


def _data_end_yyyymmdd() -> str:
    """数据截止日期：昨天。"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _list_index_daily_parquet(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("*.parquet"))


def _get_latest_date_from_index_daily(index_code: str, base_path: Path) -> Optional[str]:
    """获取某指数日线本地最新交易日（YYYYMMDD）。"""
    base_dir = base_path / "raw" / "daily" / "by_index" / f"index_code={index_code}"
    files = _list_index_daily_parquet(base_dir)
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
        logger.debug(f"读取指数日线最新日期失败: {index_code} - {e}")
        return None


def load_indices_from_index_basic(base_path: Path) -> List[str]:
    """从 metadata/index_basic.csv 读取指数 symbol 列表。"""
    csv_path = base_path / "metadata" / "index_basic.csv"
    out = []
    if not csv_path.exists():
        logger.warning(f"index_basic 不存在: {csv_path}，请先运行 fetch_index_list.py")
        return out
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = (row.get("symbol") or "").strip().upper()
            if s:
                out.append(s)
    return sorted(out)


def check_index_daily_missing(
    base_path: Path,
    data_end_yyyymmdd: str,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    检测指数日线遗漏：无数据或最新日期早于 data_end 的指数。

    :return: (完全无数据的指数列表, (有数据但滞后的指数, 最新日期))
    """
    symbols = load_indices_from_index_basic(base_path)
    if not symbols:
        logger.warning("未从 index_basic 加载到任何指数")
        return [], []

    no_data: List[str] = []
    stale: List[Tuple[str, str]] = []

    for code in symbols:
        latest = _get_latest_date_from_index_daily(code, base_path)
        if latest is None:
            no_data.append(code)
            continue
        if latest < data_end_yyyymmdd:
            stale.append((code, latest))

    return no_data, stale


def _run_fetch(missing_list_path: Path, token: Optional[str] = None, sleep: float = 0) -> None:
    """调用 fetch_tushare_index_daily.py 对缺失列表补拉。"""
    cmd = [sys.executable, str(FETCH_SCRIPT), "--from-missing-list", str(missing_list_path.resolve())]
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


def main() -> int:
    parser = argparse.ArgumentParser(description="检测指数日线数据遗漏，生成缺失列表")
    parser.add_argument("--base-path", type=str, default=None, help="数据根目录，默认 .stock_data")
    parser.add_argument("--output", type=str, default=None,
                        help="缺失列表输出路径，默认 .stock_data/metadata/missing_index_daily_YYYYMMDD_HHMMSS.txt")
    parser.add_argument("--dry-run", action="store_true", help="仅检测并打印统计，不写入文件")
    parser.add_argument("--fetch", action="store_true", help="检测到遗漏后自动调用 fetch_tushare_index_daily 补拉")
    parser.add_argument("--token", type=str, default=None, help="补拉时传给 fetch 的 Tushare token")
    parser.add_argument("--sleep", type=float, default=0, help="补拉时每个指数间隔秒数")
    args = parser.parse_args()

    base_path = Path(args.base_path).resolve() if args.base_path else DEFAULT_BASE_PATH
    if not base_path.exists():
        logger.error(f"数据根目录不存在: {base_path}")
        return 1

    data_end = _data_end_yyyymmdd()
    logger.info(f"数据截止日期（昨日）: {data_end}")

    no_data, stale = check_index_daily_missing(base_path, data_end)
    missing_codes = sorted(set(no_data) | {c for c, _ in stale})

    logger.info(f"完全无日线数据: {len(no_data)} 个指数")
    logger.info(f"有数据但滞后于 {data_end}: {len(stale)} 个指数")
    logger.info(f"遗漏合计: {len(missing_codes)} 个指数")

    if no_data and len(no_data) <= 20:
        logger.info(f"无数据样例: {no_data[:20]}")
    elif no_data:
        logger.info(f"无数据样例: {no_data[:10]} ...")
    if stale and len(stale) <= 10:
        for c, d in stale[:10]:
            logger.info(f"  滞后: {c} 最新={d}")
    elif stale:
        logger.info(f"滞后样例: {stale[0][0]} 最新={stale[0][1]} ...")

    if args.dry_run:
        return 0

    if not missing_codes:
        logger.info("无遗漏，不生成缺失文件")
        return 0

    if args.output:
        out_path = Path(args.output)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = base_path / "metadata" / f"missing_index_daily_{ts}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(missing_codes) + "\n", encoding="utf-8")
    logger.info(f"已写入缺失列表: {out_path}，共 {len(missing_codes)} 个指数")

    if args.fetch and FETCH_SCRIPT.exists():
        _run_fetch(out_path, token=args.token, sleep=args.sleep)
    elif args.fetch and not FETCH_SCRIPT.exists():
        logger.warning(f"未找到拉取脚本: {FETCH_SCRIPT}，跳过自动补拉")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
