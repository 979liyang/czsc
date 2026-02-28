#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测本地股票分钟数据是否完整（按月份），找出缺失月份，并可调用 fetch_tushare_minute_data_stk_mins_limit.py 补拉。

期望范围：未指定 --start-date/--end-date 时，为 max(20180101, list_date) ～ 昨日（当日数据尚未产出）；
使用 --use-stock-basic 时从 metadata/stock_basic.csv 读取 list_date，否则统一 20180101～昨日。
可选 --check-9am：校验每月 parquet 首条 K 线是否从 9 点开始，否则视为缺失。

存储结构（与 fetch_tushare_minute_data_stk_mins_limit.py 一致）：
  .stock_data/raw/minute_by_stock/stock_code={ts_code}/year={year}/{ts_code}_{year}-{month:02d}.parquet

使用示例：
  python scripts/check_loacal_stock_new.py --fetch
  # 检测指定股票缺失月份（不补拉）
  python scripts/check_loacal_stock_new.py --stocks 600066.SH

  # 使用 stock_basic.csv 的上市日，期望 20180101～昨日
  python scripts/check_loacal_stock_new.py --scan --use-stock-basic

  # 校验每月首条是否 9 点开始
  python scripts/check_loacal_stock_new.py --scan --use-stock-basic --check-9am

  # 检测后自动调用 fetch 脚本补拉缺失月份
  python scripts/check_loacal_stock_new.py --stocks 600066.SH --fetch
"""

import argparse
import re
import subprocess
import sys
from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 默认数据根目录（与 fetch_tushare_minute_data_stk_mins_limit 一致）
DEFAULT_BASE_PATH = project_root / ".stock_data"
FETCH_SCRIPT = project_root / "scripts" / "fetch_tushare_minute_data_stk_mins_limit.py"

# 本地统一期望：起始 20180101，结束为昨日（当日数据尚未产出）
DEFAULT_START_YYYYMMDD = "20180101"


def _data_end_yyyymmdd() -> str:
    """数据截止日期：昨天（因当日数据尚未产出）"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


# 从 parquet 路径解析 (year, month)，例如 year=2024/600066.SH_2024-01.parquet
RE_YEAR_MONTH = re.compile(r"(\d{4})-(\d{2})\.parquet$")


def _is_trading_weekday(d: datetime) -> bool:
    """是否为交易日（周一至周五，不含节假日；此处仅按周一到周五近似）"""
    return d.weekday() < 5


def build_first_trading_days_by_month(
    start_yyyymmdd: str,
    end_yyyymmdd: str,
) -> Dict[Tuple[int, int], str]:
    """
    生成从 start 到 end 之间每个月的第一个交易日（按“当月第一个周一～周五”近似，不含节假日）。
    返回 (year, month) -> YYYYMMDD。
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


# 2018 年至今每月第一个交易日（脚本加载后首次使用时生成）
_FIRST_TRADING_DAYS_CACHE: Optional[Dict[Tuple[int, int], str]] = None


def get_first_trading_days_by_month() -> Dict[Tuple[int, int], str]:
    """获取 20180101 至当天每月第一个交易日，使用缓存。"""
    global _FIRST_TRADING_DAYS_CACHE
    if _FIRST_TRADING_DAYS_CACHE is None:
        end_yyyymmdd = datetime.now().strftime("%Y%m%d")
        _FIRST_TRADING_DAYS_CACHE = build_first_trading_days_by_month(
            DEFAULT_START_YYYYMMDD, end_yyyymmdd
        )
        logger.debug(f"已生成 {len(_FIRST_TRADING_DAYS_CACHE)} 个月的首个交易日")
    return _FIRST_TRADING_DAYS_CACHE


def _list_month_files(base_dir: Path) -> List[Path]:
    """列出某股票目录下的所有月度 parquet 文件"""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("year=*/**/*.parquet"))


def _parse_year_month_from_path(file_path: Path) -> Optional[Tuple[int, int]]:
    """从文件路径解析 (year, month)，文件名如 600066.SH_2024-01.parquet"""
    m = RE_YEAR_MONTH.search(file_path.name)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def get_existing_year_months(base_dir: Path) -> Set[Tuple[int, int]]:
    """获取某股票目录下已存在的 (year, month) 集合"""
    files = _list_month_files(base_dir)
    out = set()
    for fp in files:
        ym = _parse_year_month_from_path(fp)
        if ym:
            out.add(ym)
    return out


def get_last_local_date(stock_code: str, base_path: Path) -> Optional[str]:
    """
    获取某股票本地 parquet 中的最后一条数据日期（YYYYMMDD）。
    通过读取最新月份 parquet 的最后一笔时间得到；无数据返回 None。
    """
    base_dir = base_path / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    files = _list_month_files(base_dir)
    if not files:
        return None
    # 按 (year, month) 排序，取最后一个文件
    with_ym = [(_parse_year_month_from_path(f), f) for f in files]
    with_ym = [(ym, f) for ym, f in with_ym if ym]
    if not with_ym:
        return None
    with_ym.sort(key=lambda x: x[0])
    last_fp = with_ym[-1][1]
    try:
        import pandas as pd
        df = pd.read_parquet(last_fp, columns=None)
        if df is None or len(df) == 0:
            return None
        for c in ("timestamp", "datetime", "dt", "date"):
            if c in df.columns:
                last_ts = pd.to_datetime(df[c].iloc[-1])
                return last_ts.strftime("%Y%m%d")
        return None
    except Exception:
        return None


def has_trading_days_between(start_yyyymmdd: str, end_yyyymmdd: str) -> bool:
    """判断 [start_yyyymmdd, end_yyyymmdd] 闭区间内是否至少有一个交易日（按周一～周五近似）。"""
    start_d = datetime.strptime(start_yyyymmdd[:8], "%Y%m%d")
    end_d = datetime.strptime(end_yyyymmdd[:8], "%Y%m%d")
    if start_d > end_d:
        return False
    d = start_d
    while d <= end_d:
        if _is_trading_weekday(d):
            return True
        d = d + timedelta(days=1)
    return False


def list_expected_months(
    start_yyyymmdd: str,
    end_yyyymmdd: str,
) -> List[Tuple[int, int]]:
    """根据起止日期生成期望的 (year, month) 列表（闭区间，按自然月）"""
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


def month_start_end(year: int, month: int) -> Tuple[str, str]:
    """返回该月的首日与末日 YYYYMMDD"""
    _, last = monthrange(year, month)
    s = f"{year}{month:02d}01"
    e = f"{year}{month:02d}{last}"
    return s, e


def load_list_dates_from_stock_basic(base_path: Path) -> Dict[str, str]:
    """
    从 stock_basic.csv 读取每只股票的上市日期 list_date（YYYYMMDD）。
    返回 symbol -> list_date，未找到或无效则无该 key 或 list_date 为空。
    """
    csv_path = base_path / "metadata" / "stock_basic.csv"
    out = {}
    if not csv_path.exists():
        logger.warning(f"stock_basic 不存在: {csv_path}，将不按上市日裁剪期望范围")
        return out
    try:
        import csv
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


def _expected_first_day_of_month(
    year: int,
    month: int,
    list_date: Optional[str],
    first_trading_days: Dict[Tuple[int, int], str],
) -> Optional[str]:
    """
    该月应出现数据的首个交易日：上市当月为 max(当月首个交易日, list_date)，其余月份为当月首个交易日。
    """
    key = (year, month)
    first = first_trading_days.get(key)
    if not first:
        return None
    if not list_date or len(list_date) < 8:
        return first
    list_ym = (int(list_date[:4]), int(list_date[4:6]))
    if (year, month) < list_ym:
        return None
    if (year, month) == list_ym:
        return max(first, list_date[:8])
    return first


def _parquet_first_bar_from_9am(
    base_dir: Path,
    year: int,
    month: int,
    list_date: Optional[str] = None,
    first_trading_days: Optional[Dict[Tuple[int, int], str]] = None,
) -> Optional[bool]:
    """
    检查该月 parquet 首条 K 线是否从 9 点开始（09:00 或 09:31），
    且首条日期不早于该月应出现的首个交易日（结合 list_date 与每月首个交易日）。
    若文件不存在返回 None；存在则读首条时间，返回 True 表示合规，False 视为缺失。
    """
    parquet_dir = base_dir / f"year={year}"
    if not parquet_dir.exists():
        return None
    pattern = f"*_{year}-{month:02d}.parquet"
    files = list(parquet_dir.glob(pattern))
    if not files:
        return None
    try:
        import pandas as pd
        df = pd.read_parquet(files[0], columns=None)
        if df is None or len(df) == 0:
            return False
        ts_col = None
        for c in ("timestamp", "datetime", "dt", "date"):
            if c in df.columns:
                ts_col = c
                break
        if ts_col is None:
            return True
        first_ts = pd.to_datetime(df[ts_col].iloc[0])
        hour, minute = first_ts.hour, first_ts.minute
        first_date_str = first_ts.strftime("%Y%m%d") if hasattr(first_ts, "strftime") else None
        if first_trading_days and list_date is not None:
            expected_first = _expected_first_day_of_month(
                year, month, list_date, first_trading_days
            )
            if expected_first and first_date_str and first_date_str < expected_first:
                return False
        if hour == 9 and minute in (0, 31):
            return True
        if hour < 9:
            return True
        return False
    except Exception:
        return None


def check_stock(
    stock_code: str,
    base_path: Path,
    start_date: Optional[str],
    end_date: Optional[str],
    list_date: Optional[str] = None,
    check_9am: bool = False,
    first_trading_days: Optional[Dict[Tuple[int, int], str]] = None,
) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    检测单只股票缺失月份。检测时先根据当前股票的 list_date 确定期望区间。

    期望范围：若未传 start_date/end_date，则用 max(20180101, list_date) ～ 昨日；
    若传了则用指定范围。可选 check_9am：对已有 parquet 校验当月首条是否从 9 点开始且不早于该月应出现的首日，否则视为缺失。

    :return: (existing_ym_set, expected_ym_set, missing_ym_list)
    """
    base_dir = base_path / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    existing = get_existing_year_months(base_dir)

    if start_date and end_date:
        s = start_date.strip()[:8]
        e = end_date.strip()[:8]
        if s.isdigit() and e.isdigit():
            expected = set(list_expected_months(s, e))
        else:
            expected = set(list_expected_months(DEFAULT_START_YYYYMMDD, _data_end_yyyymmdd()))
    else:
        # 先检查当前股票的 list_date：期望范围 max(20180101, list_date) ～ 昨日
        end_yyyymmdd = _data_end_yyyymmdd()
        if list_date and str(list_date).strip()[:8].isdigit():
            start_yyyymmdd = max(DEFAULT_START_YYYYMMDD, str(list_date).strip()[:8])
        else:
            start_yyyymmdd = DEFAULT_START_YYYYMMDD
        expected = set(list_expected_months(start_yyyymmdd, end_yyyymmdd))

    if not existing:
        missing = sorted(expected)
        return existing, expected, missing

    missing_set = set(expected - existing)

    if check_9am and first_trading_days is not None:
        for (y, m) in list(expected):
            if (y, m) in missing_set:
                continue
            ok = _parquet_first_bar_from_9am(
                base_dir, y, m,
                list_date=list_date,
                first_trading_days=first_trading_days,
            )
            if ok is False:
                missing_set.add((y, m))
            elif ok is None:
                missing_set.add((y, m))

    missing = sorted(missing_set)
    return existing, expected, missing


def list_stocks_from_dirs(base_path: Path) -> List[str]:
    """从 minute_by_stock 下 stock_code=* 目录扫描股票代码"""
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


def run_fetch_for_missing_month(
    stock_code: str,
    year: int,
    month: int,
    freq: str,
    script_path: Path,
    token: Optional[str] = None,
    sleep: float = 0,
) -> bool:
    """对单个缺失月份调用 fetch_tushare_minute_data_stk_mins_limit.py"""
    s, e = month_start_end(year, month)
    cmd = [
        sys.executable,
        str(script_path),
        "--freq", freq,
        "--stocks", stock_code,
        "--start-date", s,
        "--end-date", e,
    ]
    if token:
        cmd.extend(["--token", token])
    if sleep and sleep > 0:
        cmd.extend(["--sleep", str(sleep)])
    logger.info(f"补拉 {stock_code} {year}-{month:02d}: {' '.join(cmd)}")
    try:
        ret = subprocess.run(cmd, cwd=str(project_root), timeout=600)
        return ret.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"补拉超时: {stock_code} {year}-{month:02d}")
        return False
    except Exception as e:
        logger.error(f"补拉失败: {stock_code} {year}-{month:02d} - {e}")
        return False


def run_fetch_for_range(
    stock_code: str,
    start_yyyymmdd: str,
    end_yyyymmdd: str,
    freq: str,
    script_path: Path,
    token: Optional[str] = None,
    sleep: float = 0,
) -> bool:
    """对指定日期区间调用 fetch_tushare_minute_data_stk_mins_limit.py 补拉（用于“最后一天到昨日”的尾段补拉）。"""
    cmd = [
        sys.executable,
        str(script_path),
        "--freq", freq,
        "--stocks", stock_code,
        "--start-date", start_yyyymmdd[:8],
        "--end-date", end_yyyymmdd[:8],
    ]
    if token:
        cmd.extend(["--token", token])
    if sleep and sleep > 0:
        cmd.extend(["--sleep", str(sleep)])
    logger.info(f"补拉尾段 {stock_code} {start_yyyymmdd}～{end_yyyymmdd}: {' '.join(cmd)}")
    try:
        ret = subprocess.run(cmd, cwd=str(project_root), timeout=600)
        return ret.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"补拉尾段超时: {stock_code}")
        return False
    except Exception as e:
        logger.error(f"补拉尾段失败: {stock_code} - {e}")
        return False


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="检测本地股票分钟数据缺失月份，并可调用 fetch 脚本补拉",
    )
    parser.add_argument("--stocks", type=str, default=None, help="股票代码逗号分隔，如 600066.SH,000001.SZ")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="扫描 .stock_data/raw/minute_by_stock 下所有股票（与 --stocks 二选一）",
    )
    parser.add_argument("--start-date", type=str, default=None, help="期望起始日期 YYYYMMDD，不传则用本地已有范围")
    parser.add_argument("--end-date", type=str, default=None, help="期望结束日期 YYYYMMDD")
    parser.add_argument("--base-path", type=str, default=None, help="数据根目录，默认项目根/.stock_data")
    parser.add_argument("--freq", type=str, default="1min", help="分钟周期，补拉时传给 fetch 脚本")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="检测到缺失后自动调用 fetch_tushare_minute_data_stk_mins_limit.py 补拉",
    )
    parser.add_argument("--sleep", type=float, default=0, help="补拉时每只股票间隔秒数")
    parser.add_argument("--token", type=str, default=None, help="补拉时传给 fetch 的 token（可选）")
    parser.add_argument(
        "--output-missing",
        type=str,
        default=None,
        help="将缺失月份写入文件，每行: stock_code,yyyy,mm",
    )
    parser.add_argument(
        "--use-stock-basic",
        action="store_true",
        help="从 metadata/stock_basic.csv 读取 list_date，期望范围 max(20180101,list_date)～昨日",
    )
    parser.add_argument(
        "--check-9am",
        action="store_true",
        help="校验每月 parquet 首条 K 线是否从 9 点开始，否则视为缺失",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    base_path = Path(args.base_path).resolve() if args.base_path else DEFAULT_BASE_PATH
    if not base_path.exists():
        logger.error(f"数据根目录不存在: {base_path}")
        return 1

    list_dates = {}
    if args.use_stock_basic:
        list_dates = load_list_dates_from_stock_basic(base_path)
        logger.info(f"已从 stock_basic 加载 {len(list_dates)} 只股票的 list_date")

    # 先生成 2018 年至今每月第一个交易日，供检测时结合 list_date 使用
    first_trading_days = get_first_trading_days_by_month()
    logger.debug(f"已生成 2018 年至今每月首个交易日，共 {len(first_trading_days)} 个月")

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

    missing_lines = []
    total_missing = 0
    for stock_code in stocks:
        list_date = list_dates.get(stock_code) if list_dates else None
        existing, expected, missing = check_stock(
            stock_code, base_path, args.start_date, args.end_date,
            list_date=list_date, check_9am=args.check_9am,
            first_trading_days=first_trading_days,
        )
        if not missing:
            logger.info(f"{stock_code}: 无缺失月份（共 {len(expected)} 个月）")
        else:
            logger.warning(f"{stock_code}: 缺失 {len(missing)} 个月: {[f'{y}-{m:02d}' for y, m in missing]}")
            total_missing += len(missing)
            for y, m in missing:
                missing_lines.append(f"{stock_code},{y},{m:02d}")
                if args.fetch and FETCH_SCRIPT.exists():
                    ok = run_fetch_for_missing_month(
                        stock_code, y, m, args.freq, FETCH_SCRIPT,
                        token=args.token, sleep=args.sleep,
                    )
                    if not ok:
                        logger.warning(f"补拉未成功: {stock_code} {y}-{m:02d}")

        # 若本地最后一天到昨日之间还有交易日，则请求该区间数据（当日数据尚未产出）
        last_local = get_last_local_date(stock_code, base_path)
        end_yyyymmdd = _data_end_yyyymmdd()
        if last_local and last_local < end_yyyymmdd:
            next_d = (datetime.strptime(last_local[:8], "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
            if has_trading_days_between(next_d, end_yyyymmdd):
                logger.warning(f"{stock_code}: 本地最后日期 {last_local} 至昨日 {end_yyyymmdd} 仍有交易日，将请求补拉")
                if args.fetch and FETCH_SCRIPT.exists():
                    ok = run_fetch_for_range(
                        stock_code, next_d, end_yyyymmdd, args.freq, FETCH_SCRIPT,
                        token=args.token, sleep=args.sleep,
                    )
                    if not ok:
                        logger.warning(f"补拉尾段未成功: {stock_code}")

    if args.output_missing and missing_lines:
        out_path = Path(args.output_missing)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(missing_lines) + "\n", encoding="utf-8")
        logger.info(f"已写入缺失列表: {out_path}，共 {len(missing_lines)} 条")

    if total_missing > 0 and not args.fetch:
        logger.info(f"共 {total_missing} 个缺失月份，可使用 --fetch 自动补拉")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
