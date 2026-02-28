#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测本地股票分钟数据：仅校验每月**首条 K 线日期**是否为该月首个交易日；不对则拉取当月数据补齐。

当存在 .stock_data/metadata/stock_basic.csv 时，会读取每只股票的 list_date（上市日）：
期望数据范围为 max(20180101, list_date)～昨日，上市日之前的月份不要求补位；上市当月首条为 max(当月首交, list_date)。

每年每月仅导出**首个交易日**（无结束日）到 .stock_data/metadata/monthly_trading_calendar.csv。
交易日历优先从参考数据（parquet 或 csv_output）中按每月首条推导；无参考时按周一～周五近似（未排除节假日）。

存储结构（与 fetch_limit.py 一致）：
  .stock_data/raw/minute_by_stock/stock_code={ts_code}/year={year}/{ts_code}_{year}-{month:02d}.parquet

使用示例：
  # 仅导出每年每月首个交易日（单列 start_yyyymmdd）
  python scripts/minute/check.py --export-calendar

  # 检测指定股票：开始时间不对的月份会列出，加 --fetch 则拉取当月数据
  python scripts/minute/check.py --stocks 600066.SH
  python scripts/minute/check.py --stocks 600066.SH --fetch

  # 扫描所有股票，开始时间不对的月份直接补拉
  python scripts/minute/check.py --scan --fetch --freq 1min

  # 从某只股票后面开始（跳过该股票及之前的）
  python scripts/minute/check.py --scan --fetch --resume-after 600066.SH
  python scripts/minute/check.py --scan --fetch --resume-after 301097.SZ

  # 补拉「最后交易日」到目标结束日：从本地 parquet 推导最后日期；可指定 --end-date，不指定则默认昨日
  # 若股票最后一天已是结束日则不拉取，否则从最后一天下一日拉到结束日
  python scripts/minute/check.py --catch-up --stocks 600066.SH --freq 1min
  python scripts/minute/check.py --catch-up --stocks 600079.SH --end-date 20260219
  python scripts/minute/check.py --catch-up --scan --end-date 20260219
"""

import argparse
import csv
import re
import subprocess
import sys
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_BASE_PATH = project_root / ".stock_data"
CSV_OUTPUT_ROOT = project_root / "csv_output"
FETCH_SCRIPT = project_root / "scripts" / "minute" /"fetch_limit.py"
DEFAULT_START_YYYYMMDD = "20180101"
RE_YEAR_MONTH = re.compile(r"(\d{4})-(\d{2})\.parquet$")


def _data_end_yyyymmdd() -> str:
    """数据截止日期：昨天（因当日数据尚未产出）"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _is_trading_weekday(d: datetime) -> bool:
    """是否为交易日（周一至周五近似，未排除节假日）"""
    return d.weekday() < 5


def last_trading_day_of_month(year: int, month: int) -> str:
    """当月最后一个交易日（从月末往前取第一个周一～周五），返回 YYYYMMDD。"""
    _, last_day = monthrange(year, month)
    for day in range(last_day, 0, -1):
        d = datetime(year, month, day)
        if _is_trading_weekday(d):
            return d.strftime("%Y%m%d")
    return f"{year}{month:02d}{last_day}"


def build_first_trading_day_only(
    start_yyyymmdd: str,
    end_yyyymmdd: str,
) -> Dict[Tuple[int, int], str]:
    """
    生成每年每月的首个交易日（仅按周一～周五近似）。
    返回 (year, month) -> start_yyyymmdd。
    """
    start_d = datetime.strptime(start_yyyymmdd[:8], "%Y%m%d")
    end_d = datetime.strptime(end_yyyymmdd[:8], "%Y%m%d")
    if start_d > end_d:
        start_d, end_d = end_d, start_d
    out = {}
    y, m = start_d.year, start_d.month
    ey, em = end_d.year, end_d.month
    while (y, m) <= (ey, em):
        _, last_day = monthrange(y, m)
        for day in range(1, last_day + 1):
            d = datetime(y, m, day)
            if _is_trading_weekday(d):
                out[(y, m)] = d.strftime("%Y%m%d")
                break
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _first_bar_date_from_parquet(parquet_path: Path) -> Optional[str]:
    """从 parquet 读取首条 K 线日期，返回 YYYYMMDD；失败返回 None。"""
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path, columns=None)
        if df is None or len(df) == 0:
            return None
        for c in ("timestamp", "datetime", "dt", "date", "trade_time"):
            if c in df.columns:
                first_ts = pd.to_datetime(df[c].iloc[0])
                return first_ts.strftime("%Y%m%d")
        return None
    except Exception:
        return None


def _last_bar_date_from_parquet(parquet_path: Path) -> Optional[str]:
    """从 parquet 读取末条 K 线日期，返回 YYYYMMDD；失败返回 None。"""
    try:
        import pandas as pd
        df = pd.read_parquet(parquet_path, columns=None)
        if df is None or len(df) == 0:
            return None
        for c in ("timestamp", "datetime", "dt", "date", "trade_time"):
            if c in df.columns:
                last_ts = pd.to_datetime(df[c].iloc[-1])
                return last_ts.strftime("%Y%m%d")
        return None
    except Exception:
        return None


def get_stock_last_bar_date(base_path: Path, stock_code: str) -> Optional[str]:
    """
    从本地 parquet 扫描该股票所有月份文件，返回最后一条 K 线的日期 YYYYMMDD；
    无文件或失败返回 None。
    """
    base_dir = base_path / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    files = _list_month_files(base_dir)
    if not files:
        return None
    last_yyyymmdd = None
    for fp in files:
        d = _last_bar_date_from_parquet(fp)
        if d and (last_yyyymmdd is None or d > last_yyyymmdd):
            last_yyyymmdd = d
    return last_yyyymmdd


def _first_bar_date_from_csv(csv_path: Path) -> Optional[str]:
    """从 CSV 首条数据行读取日期，返回 YYYYMMDD；失败返回 None。"""
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("timestamp"):
                    continue
                # 格式如 2018-01-02 09:30:00 或 20180102
                part = line.split(",")[0].strip()
                if len(part) >= 10 and part[4] == "-":
                    return part[:10].replace("-", "")
                if len(part) >= 8 and part.isdigit():
                    return part[:8]
                return None
        return None
    except Exception:
        return None


def build_first_trading_days_from_reference(
    base_path: Path,
    end_yyyymmdd: str,
) -> Dict[Tuple[int, int], str]:
    """
    从参考数据推导每月首个交易日：优先 parquet（000001.SZ），其次 csv_output/000001.SZ。
    返回 (year, month) -> start_yyyymmdd；无数据的月份不包含。
    """
    out = {}
    # 1) 尝试 .stock_data parquet
    ref_dir = base_path / "raw" / "minute_by_stock" / "stock_code=000001.SZ"
    if ref_dir.exists():
        for fp in sorted(ref_dir.glob("year=*/**/*.parquet")):
            m = RE_YEAR_MONTH.search(fp.name)
            if m:
                y, mo = int(m.group(1)), int(m.group(2))
                if (y, mo) in out:
                    continue
                first = _first_bar_date_from_parquet(fp)
                if first:
                    out[(y, mo)] = first
        if out:
            logger.debug(f"从 parquet 000001.SZ 推导 {len(out)} 个月的首个交易日")
            return out
    # 2) 尝试 csv_output
    ref_csv_dir = CSV_OUTPUT_ROOT / "000001.SZ" / "stock_code=000001.SZ"
    if ref_csv_dir.exists():
        for fp in sorted(ref_csv_dir.glob("year=*/*.csv")):
            m = re.search(r"(\d{4})-(\d{2})\.csv$", fp.name)
            if m:
                y, mo = int(m.group(1)), int(m.group(2))
                if (y, mo) in out:
                    continue
                first = _first_bar_date_from_csv(fp)
                if first:
                    out[(y, mo)] = first
        if out:
            logger.debug(f"从 csv_output 000001.SZ 推导 {len(out)} 个月的首个交易日")
            return out
    return out


def load_list_dates_from_stock_basic(base_path: Path) -> Dict[str, str]:
    """
    从 stock_basic.csv 读取每只股票的上市日期 list_date（YYYYMMDD）。
    返回 symbol -> list_date，未找到或无效则无该 key。
    """
    csv_path = base_path / "metadata" / "stock_basic.csv"
    out: Dict[str, str] = {}
    if not csv_path.exists():
        logger.debug(f"stock_basic 不存在: {csv_path}，将不按上市日裁剪期望范围")
        return out
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = (row.get("symbol") or "").strip().upper()
                list_date = (row.get("list_date") or "").strip()
                if symbol and len(list_date) >= 8 and list_date[:8].isdigit():
                    out[symbol] = list_date[:8]
    except Exception as e:
        logger.warning(f"读取 stock_basic 失败: {csv_path} - {e}")
    return out


# 缓存：每月首个交易日 (year, month) -> start_yyyymmdd
_FIRST_DAY_CALENDAR_CACHE: Optional[Dict[Tuple[int, int], str]] = None


def get_first_trading_day_calendar(base_path: Path) -> Dict[Tuple[int, int], str]:
    """
    获取每月首个交易日。优先从参考数据推导；缺的月份用周一～周五近似补全。
    """
    global _FIRST_DAY_CALENDAR_CACHE
    if _FIRST_DAY_CALENDAR_CACHE is not None:
        return _FIRST_DAY_CALENDAR_CACHE
    end_yyyymmdd = datetime.now().strftime("%Y%m%d")
    ref = build_first_trading_days_from_reference(base_path, end_yyyymmdd)
    fallback = build_first_trading_day_only(DEFAULT_START_YYYYMMDD, end_yyyymmdd)
    merged = dict(fallback)
    for k, v in ref.items():
        merged[k] = v
    _FIRST_DAY_CALENDAR_CACHE = merged
    logger.debug(f"已生成 {len(merged)} 个月的首个交易日历")
    return _FIRST_DAY_CALENDAR_CACHE


def export_calendar_csv(base_path: Path) -> Path:
    """仅导出每年每月首个交易日到 CSV（无结束日）。"""
    cal = get_first_trading_day_calendar(base_path)
    meta_dir = base_path / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    out_path = meta_dir / "monthly_trading_calendar.csv"
    rows = [("year", "month", "start_yyyymmdd")]
    for (y, m) in sorted(cal.keys()):
        rows.append((str(y), f"{m:02d}", cal[(y, m)]))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    logger.info(f"已导出每月首个交易日: {out_path}，共 {len(cal)} 个月（仅起始日，无结束日）")
    return out_path


def _list_month_files(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("year=*/**/*.parquet"))


def _parse_year_month_from_path(file_path: Path) -> Optional[Tuple[int, int]]:
    m = RE_YEAR_MONTH.search(file_path.name)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def get_existing_year_months(base_dir: Path) -> Set[Tuple[int, int]]:
    files = _list_month_files(base_dir)
    out = set()
    for fp in files:
        ym = _parse_year_month_from_path(fp)
        if ym:
            out.add(ym)
    return out


def list_expected_months(
    start_yyyymmdd: str,
    end_yyyymmdd: str,
) -> List[Tuple[int, int]]:
    start = datetime.strptime(start_yyyymmdd[:8], "%Y%m%d")
    end = datetime.strptime(end_yyyymmdd[:8], "%Y%m%d")
    if start > end:
        start, end = end, start
    out = []
    y, m = start.year, start.month
    ey, em = end.year, end.month
    while (y, m) <= (ey, em):
        out.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def get_parquet_path(base_path: Path, stock_code: str, year: int, month: int) -> Path:
    """某股票某月 parquet 路径"""
    return (
        base_path
        / "raw"
        / "minute_by_stock"
        / f"stock_code={stock_code}"
        / f"year={year}"
        / f"{stock_code}_{year}-{month:02d}.parquet"
    )


def _effective_first_of_month(
    y: int,
    m: int,
    first_day_calendar: Dict[Tuple[int, int], str],
    list_date: Optional[str],
) -> Optional[str]:
    """
    该月应出现数据的首个交易日。上市当月为 max(当月首个交易日, list_date)，其余月份为当月首个交易日。
    """
    expected = first_day_calendar.get((y, m))
    if not expected:
        return None
    if not list_date or len(list_date) < 8:
        return expected
    list_ym = (int(list_date[:4]), int(list_date[4:6]))
    if (y, m) < list_ym:
        return None
    if (y, m) == list_ym:
        return max(expected, list_date[:8])
    return expected


def check_stock_start_dates(
    stock_code: str,
    base_path: Path,
    start_date: Optional[str],
    end_date: Optional[str],
    first_day_calendar: Dict[Tuple[int, int], str],
    list_date: Optional[str] = None,
) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]], List[Tuple[Tuple[int, int], Optional[str]]]]:
    """
    只检测每月开始时间是否正确：已有文件的月份若首条 K 线日期 != 该月首个交易日（或上市日），则视为需补拉。
    若提供 list_date（上市日），期望范围为 max(20180101, list_date)～昨日，且上市当月首条日期为 max(当月首交, list_date)。
    :return: (existing_ym_set, expected_ym_set, need_fetch_list)，need_fetch_list 每项为 ((y,m), actual_first_or_none)。
    actual_first 有值时表示该月有文件但首日不对，只补「应有首日～实际首日前一天」；None 表示整月缺失，补整月。
    """
    base_dir = base_path / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    existing = get_existing_year_months(base_dir)
    end_yyyymmdd = _data_end_yyyymmdd()
    if start_date and end_date:
        s, e = start_date.strip()[:8], end_date.strip()[:8]
        if s.isdigit() and e.isdigit():
            expected = set(list_expected_months(s, e))
        else:
            expected = set(list_expected_months(DEFAULT_START_YYYYMMDD, end_yyyymmdd))
    else:
        effective_start = DEFAULT_START_YYYYMMDD
        if list_date and len(list_date) >= 8 and list_date[:8].isdigit():
            effective_start = max(DEFAULT_START_YYYYMMDD, list_date[:8])
        expected = set(list_expected_months(effective_start, end_yyyymmdd))

    need_fetch: List[Tuple[Tuple[int, int], Optional[str]]] = []
    for (y, m) in sorted(expected):
        expected_first = _effective_first_of_month(y, m, first_day_calendar, list_date)
        if not expected_first:
            need_fetch.append(((y, m), None))
            continue
        parquet_path = get_parquet_path(base_path, stock_code, y, m)
        if not parquet_path.exists():
            need_fetch.append(((y, m), None))
            continue
        actual_first = _first_bar_date_from_parquet(parquet_path)
        if actual_first is None or actual_first != expected_first:
            need_fetch.append(((y, m), actual_first))
    return existing, expected, need_fetch


def list_stocks_from_dirs(base_path: Path) -> List[str]:
    root = base_path / "raw" / "minute_by_stock"
    if not root.exists():
        return []
    stocks = []
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith("stock_code="):
            code = d.name.replace("stock_code=", "").strip()
            if code:
                stocks.append(code)
    return sorted(stocks)


def _day_before(yyyyymmdd: str) -> str:
    """返回前一天的 YYYYMMDD"""
    d = datetime.strptime(yyyyymmdd[:8], "%Y%m%d") - timedelta(days=1)
    return d.strftime("%Y%m%d")


def _day_after(yyyyymmdd: str) -> str:
    """返回后一天的 YYYYMMDD"""
    d = datetime.strptime(yyyyymmdd[:8], "%Y%m%d") + timedelta(days=1)
    return d.strftime("%Y%m%d")


def run_catch_up_fetch(
    stock_code: str,
    start_yyyymmdd: str,
    end_yyyymmdd: str,
    freq: str,
    script_path: Path,
    token: Optional[str] = None,
    sleep: float = 0,
) -> bool:
    """
    拉取 [start_yyyymmdd, end_yyyymmdd] 区间数据（从「最后交易日」的下一天到当前最新）。
    """
    cmd = [
        sys.executable,
        str(script_path),
        "--freq", freq,
        "--stocks", stock_code,
        "--start-date", start_yyyymmdd,
        "--end-date", end_yyyymmdd,
    ]
    if token:
        cmd.extend(["--token", token])
    if sleep and sleep > 0:
        cmd.extend(["--sleep", str(sleep)])
    logger.info(f"补拉尾段 {stock_code} [{start_yyyymmdd}～{end_yyyymmdd}]")
    try:
        ret = subprocess.run(cmd, cwd=str(project_root), timeout=1200)
        return ret.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"补拉尾段超时: {stock_code}")
        return False
    except Exception as e:
        logger.error(f"补拉尾段失败: {stock_code} - {e}")
        return False


def run_fetch_for_month(
    stock_code: str,
    year: int,
    month: int,
    freq: str,
    script_path: Path,
    first_day_calendar: Dict[Tuple[int, int], str],
    actual_first: Optional[str] = None,
    list_date: Optional[str] = None,
    token: Optional[str] = None,
    sleep: float = 0,
) -> bool:
    """
    只补确实缺失的天：若 actual_first 有且大于应有首日，只拉 [应有首日, actual_first-1]；
    否则（整月缺失或首日错乱）拉整月 [应有首日, min(月末最后交易日, 昨日)]。
    若有 list_date，上市当月应有首日为 max(当月首交, list_date)。
    """
    start_yyyymmdd = _effective_first_of_month(
        year, month, first_day_calendar, list_date
    ) or first_day_calendar.get((year, month))
    if not start_yyyymmdd:
        _, last = monthrange(year, month)
        start_yyyymmdd = f"{year}{month:02d}01"
    yesterday = _data_end_yyyymmdd()
    if actual_first and actual_first > start_yyyymmdd:
        # 只补缺的开头几天：应有首日 ～ 实际首日的前一天
        end_yyyymmdd = _day_before(actual_first)
        if end_yyyymmdd < start_yyyymmdd:
            return True
    else:
        month_last_trading = last_trading_day_of_month(year, month)
        end_yyyymmdd = min(month_last_trading, yesterday)
    cmd = [
        sys.executable,
        str(script_path),
        "--freq", freq,
        "--stocks", stock_code,
        "--start-date", start_yyyymmdd,
        "--end-date", end_yyyymmdd,
    ]
    if token:
        cmd.extend(["--token", token])
    if sleep and sleep > 0:
        cmd.extend(["--sleep", str(sleep)])
    logger.info(f"补拉 {stock_code} {year}-{month:02d} [{start_yyyymmdd}～{end_yyyymmdd}]")
    try:
        ret = subprocess.run(cmd, cwd=str(project_root), timeout=600)
        return ret.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"补拉超时: {stock_code} {year}-{month:02d}")
        return False
    except Exception as e:
        logger.error(f"补拉失败: {stock_code} {year}-{month:02d} - {e}")
        return False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检测本地股票每月首条 K 线日期是否正确，不对则拉取当月数据补齐",
    )
    parser.add_argument("--stocks", type=str, default=None, help="股票代码逗号分隔")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="扫描 .stock_data/raw/minute_by_stock 下所有股票",
    )
    parser.add_argument("--start-date", type=str, default=None, help="期望起始 YYYYMMDD，不传则 20180101")
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="期望结束 YYYYMMDD；月度检测时表示范围结束，catch-up 时表示补拉目标结束日，不传则昨日（当前最后交易日）",
    )
    parser.add_argument("--base-path", type=str, default=None, help="数据根目录，默认 .stock_data")
    parser.add_argument("--freq", type=str, default="1min", help="补拉时传给 fetch 的周期")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="检测到开始时间不对或缺失时，拉取当月数据",
    )
    parser.add_argument("--sleep", type=float, default=0, help="补拉时每只股票间隔秒数")
    parser.add_argument("--token", type=str, default=None, help="补拉时传给 fetch 的 token")
    parser.add_argument(
        "--output-missing",
        type=str,
        default=None,
        help="将需补拉的月份写入文件，每行 stock_code,yyyy,mm",
    )
    parser.add_argument(
        "--export-calendar",
        action="store_true",
        help="仅导出每年每月首个交易日到 monthly_trading_calendar.csv（无结束日）后退出",
    )
    parser.add_argument(
        "--resume-after",
        type=str,
        default=None,
        help="从指定股票之后开始处理（该股票及之前的跳过），如 600066.SH",
    )
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="补拉尾段：从本地最后一条 K 线下一日拉到 --end-date（不传则昨日）；若最后一天已是结束日则不拉取",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    base_path = Path(args.base_path).resolve() if args.base_path else DEFAULT_BASE_PATH

    if args.export_calendar:
        base_path.mkdir(parents=True, exist_ok=True)
        export_calendar_csv(base_path)
        return 0

    if not base_path.exists():
        logger.error(f"数据根目录不存在: {base_path}")
        return 1

    # 补拉「最后交易日」到当前最新
    if args.catch_up:
        if args.scan:
            stocks = list_stocks_from_dirs(base_path)
            if not stocks:
                logger.warning("未扫描到任何股票目录")
                return 0
            logger.info(f"扫描到 {len(stocks)} 只股票，执行尾段补拉")
        elif args.stocks:
            stocks = [x.strip().upper() for x in args.stocks.split(",") if x.strip()]
        else:
            logger.error("--catch-up 需配合 --stocks 或 --scan")
            return 1
        if args.resume_after:
            resume = args.resume_after.strip().upper()
            try:
                idx = stocks.index(resume)
                stocks = stocks[idx + 1:]
                logger.info(f"从 {resume} 之后开始，共 {len(stocks)} 只股票")
            except ValueError:
                logger.warning(f"未找到股票 {resume}，将处理全部 {len(stocks)} 只")
        # 结束日：指定则用指定值，否则默认昨日（当前最后交易日）
        if args.end_date:
            raw = args.end_date.strip()[:8]
            if len(raw) == 8 and raw.isdigit():
                end_yyyymmdd = raw
            else:
                logger.warning(f"忽略无效 --end-date: {args.end_date}，使用昨日")
                end_yyyymmdd = _data_end_yyyymmdd()
        else:
            end_yyyymmdd = _data_end_yyyymmdd()
        if not FETCH_SCRIPT.exists():
            logger.error(f"拉取脚本不存在: {FETCH_SCRIPT}")
            return 1
        for stock_code in stocks:
            last_yyyymmdd = get_stock_last_bar_date(base_path, stock_code)
            if not last_yyyymmdd:
                logger.warning(f"{stock_code}: 无本地数据，无法推导最后日期，跳过")
                continue
            # 若股票最后一天已是结束日则不拉取
            if last_yyyymmdd >= end_yyyymmdd:
                logger.info(f"{stock_code}: 最后本地日期 {last_yyyymmdd} 已>=结束日 {end_yyyymmdd}，无需补拉")
                continue
            start_yyyymmdd = _day_after(last_yyyymmdd)
            if start_yyyymmdd > end_yyyymmdd:
                logger.info(f"{stock_code}: 已是最新（最后本地日期 {last_yyyymmdd}），无需补拉")
                continue
            ok = run_catch_up_fetch(
                stock_code, start_yyyymmdd, end_yyyymmdd, args.freq, FETCH_SCRIPT,
                token=args.token, sleep=args.sleep,
            )
            if not ok:
                logger.warning(f"尾段补拉未成功: {stock_code}")
        return 0

    first_day_calendar = get_first_trading_day_calendar(base_path)
    list_dates = load_list_dates_from_stock_basic(base_path)
    if list_dates:
        logger.info(f"已从 stock_basic 加载 {len(list_dates)} 只股票的 list_date，上市日之前不要求补位")

    if args.scan:
        stocks = list_stocks_from_dirs(base_path)
        if not stocks:
            logger.warning("未扫描到任何股票目录")
            return 0
        logger.info(f"扫描到 {len(stocks)} 只股票")
    elif args.stocks:
        stocks = [x.strip().upper() for x in args.stocks.split(",") if x.strip()]
        if not stocks:
            logger.error("请提供 --stocks 或 --scan")
            return 1
    else:
        logger.error("请提供 --stocks 或 --scan")
        return 1

    if args.resume_after:
        resume = args.resume_after.strip().upper()
        try:
            idx = stocks.index(resume)
            stocks = stocks[idx + 1:]
            logger.info(f"从 {resume} 之后开始，共 {len(stocks)} 只股票")
        except ValueError:
            logger.warning(f"未找到股票 {resume}，将处理全部 {len(stocks)} 只")

    missing_lines = []
    total_need = 0
    for stock_code in stocks:
        list_date = list_dates.get(stock_code) if list_dates else None
        existing, expected, need_fetch = check_stock_start_dates(
            stock_code, base_path, args.start_date, args.end_date, first_day_calendar,
            list_date=list_date,
        )
        if not need_fetch:
            logger.info(f"{stock_code}: 每月开始时间均正确（共 {len(expected)} 个月）")
            continue
        if not existing:
            logger.info(f"{stock_code}: 无本地数据，将补拉 {len(need_fetch)} 个月")
        else:
            logger.warning(
                f"{stock_code}: 共 {len(need_fetch)} 个月需补拉（开始时间不对或缺失）: "
                f"{[f'{y}-{m:02d}' for (y, m), _ in need_fetch]}"
            )
        total_need += len(need_fetch)
        for (y, m), actual_first in need_fetch:
            missing_lines.append(f"{stock_code},{y},{m:02d}")
            if args.fetch and FETCH_SCRIPT.exists():
                ok = run_fetch_for_month(
                    stock_code, y, m, args.freq, FETCH_SCRIPT,
                    first_day_calendar=first_day_calendar,
                    actual_first=actual_first,
                    list_date=list_date,
                    token=args.token, sleep=args.sleep,
                )
                if not ok:
                    logger.warning(f"补拉未成功: {stock_code} {y}-{m:02d}")

    if args.output_missing and missing_lines:
        out_path = Path(args.output_missing)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(missing_lines) + "\n", encoding="utf-8")
        logger.info(f"已写入需补拉列表: {out_path}，共 {len(missing_lines)} 条")

    if total_need > 0 and not args.fetch:
        logger.info(f"共 {total_need} 个月需补拉，可使用 --fetch 拉取当月数据")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
