#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tushare 获取指数日线并保存到 raw/daily/by_index。

数据源为 pro.index_daily(ts_code, start_date, end_date)，参见：
https://tushare.pro/document/2?doc_id=95 （指数日线行情）
存储路径：raw/daily/by_index/index_code={code}/{code}_{year}.parquet。

使用示例：
  python scripts/index/fetch.py
  python scripts/index/fetch.py --indices 399001.SZ
  python scripts/index/fetch.py --start-date 20150101 --end-date 20260213 --indices 399001.SZ
  未指定 --end-date 时，结束日期默认为 pro.trade_cal 的最后交易日。
  python scripts/index/fetch.py --from-missing-list .stock_data/metadata/missing_index_daily_xxx.txt
"""

import argparse
import csv
import os
import re
import sys
import time
import threading
from collections import deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger

# 脚本在 scripts/index/fetch.py，项目根为 scripts 的上一级
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_TOKEN = "5049750782419706635"
DEFAULT_BASE_PATH = project_root / ".stock_data"
INDEX_BASIC_CSV = DEFAULT_BASE_PATH / "metadata" / "index_basic.csv"
DEFAULT_HTTP_URL = "http://stk_mins.xiximiao.com/dataapi"


class RateLimiter:
    """请求速率限制器（令牌桶）。"""

    def __init__(self, max_requests_per_minute: int = 400, concurrency: int = 1):
        self.max_requests_per_minute = max_requests_per_minute
        self.concurrency = concurrency
        self.token_interval = 60.0 / max_requests_per_minute
        self.tokens = max_requests_per_minute
        self.last_refill_time = time.time()
        self.lock = threading.RLock()
        self.request_history = deque(maxlen=100)
        self.semaphore = threading.Semaphore(concurrency)

    def acquire(self) -> None:
        with self.semaphore:
            while True:
                with self.lock:
                    now = time.time()
                    time_passed = now - self.last_refill_time
                    new_tokens = int(time_passed / self.token_interval)
                    if new_tokens > 0:
                        self.tokens = min(self.max_requests_per_minute, self.tokens + new_tokens)
                        self.last_refill_time = now
                    if self.tokens > 0:
                        self.tokens -= 1
                        self.request_history.append(now)
                        return
                wait_time = self.token_interval - (now - self.last_refill_time)
                if wait_time > 0:
                    time.sleep(min(wait_time, 0.1))

    def release(self) -> None:
        pass


def _get_token(args) -> str:
    token = (args.token or "").strip()
    if token:
        return token
    token = (os.getenv("TUSHARE_TOKEN") or os.getenv("CZSC_TOKEN") or "").strip()
    return token or DEFAULT_TOKEN


def _parse_yyyymmdd(x: Optional[str], default: str) -> str:
    if not x:
        return default
    s = str(x).strip()
    if len(s) == 8 and s.isdigit():
        return s
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10].replace("-", "")
    return default


def _get_latest_trade_date_from_cal(pro, exchange: str = "SSE") -> Optional[str]:
    """通过 pro.trade_cal 获取最后交易日（is_open=1 的最大 cal_date），返回 YYYYMMDD。"""
    end_d = datetime.now().strftime("%Y%m%d")
    start_d = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    try:
        df = pro.trade_cal(exchange=exchange, start_date=start_d, end_date=end_d)
        if df is not None and len(df) > 0 and "is_open" in df.columns and "cal_date" in df.columns:
            open_days = df[df["is_open"].astype(str).str.strip() == "1"]
            if len(open_days) > 0:
                return str(open_days["cal_date"].max()).strip()
    except Exception as e:
        logger.warning(f"trade_cal 获取最后交易日失败: {e}")
    return None


def load_indices_from_csv(base_path: Path) -> List[str]:
    """从 metadata/index_basic.csv 读取 symbol 列表。"""
    csv_path = base_path / "metadata" / "index_basic.csv"
    out = []
    if not csv_path.exists():
        logger.warning(f"指数列表不存在: {csv_path}，请先运行 index_basic_import.py")
        return out
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = (row.get("symbol") or "").strip().upper()
            if s:
                out.append(s)
    return sorted(out)


def load_indices_from_db() -> Tuple[List[str], bool]:
    """
    从 MySQL index_info 表读取有效指数代码列表。

    :return: (指数代码列表, 是否来自 DB)。若 DB 不可用或表为空则返回 ([], False)。
    """
    try:
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.index_info_repo import IndexInfoRepo

        session_maker = get_session_maker()
        session = session_maker()
        try:
            repo = IndexInfoRepo(session)
            codes = repo.list_active_index_codes()
            if codes:
                logger.info(f"从 index_info 表加载 {len(codes)} 个指数")
                return (codes, True)
            return ([], False)
        finally:
            session.close()
    except Exception as e:
        logger.debug(f"从数据库加载指数列表失败，将回退到 CSV: {e}")
        return ([], False)


def _list_index_daily_parquet(base_dir: Path) -> List[Path]:
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("*.parquet"))


def _get_latest_date_index(index_code: str, base_path: Path) -> Optional[pd.Timestamp]:
    """获取某指数日线本地最新交易日。"""
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
        return combined["date"].max()
    except Exception as e:
        logger.warning(f"读取指数日线最新日期失败: {index_code} - {e}")
        return None


def _get_index_daily_date_range(index_code: str, base_path: Path) -> Tuple[Optional[date], Optional[date]]:
    """从本地 parquet 获取某指数日线数据的起止日期（用于回写 index_info）。"""
    base_dir = base_path / "raw" / "daily" / "by_index" / f"index_code={index_code}"
    files = _list_index_daily_parquet(base_dir)
    if not files:
        return (None, None)
    try:
        dfs = []
        for fp in files:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0 and "date" in df.columns:
                dfs.append(df)
        if not dfs:
            return (None, None)
        combined = pd.concat(dfs, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"])
        min_ts = combined["date"].min()
        max_ts = combined["date"].max()
        return (min_ts.date(), max_ts.date())
    except Exception as e:
        logger.warning(f"读取指数日线日期范围失败: {index_code} - {e}")
        return (None, None)


def _calc_fetch_range(
    index_code: str,
    base_path: Path,
    incremental: bool,
    start_arg: Optional[str],
    end_arg: Optional[str],
) -> Tuple[str, str]:
    edt = _parse_yyyymmdd(end_arg, datetime.now().strftime("%Y%m%d"))
    if not incremental or start_arg:
        sdt = _parse_yyyymmdd(start_arg, edt)
        return sdt, edt
    last_ts = _get_latest_date_index(index_code, base_path)
    if last_ts is None:
        return edt, edt
    next_d = (pd.to_datetime(last_ts) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    return next_d, edt


def _standardize_index_daily_df(df: pd.DataFrame, index_code: str) -> Optional[pd.DataFrame]:
    """将 pro.index_daily 返回数据标准化为 date, index_code, open, high, low, close, volume, amount。"""
    if df is None or len(df) == 0:
        return None
    out = df.copy()
    if "trade_date" not in out.columns:
        raise ValueError(f"指数日线缺少 trade_date，列: {list(out.columns)}")
    out["date"] = pd.to_datetime(out["trade_date"].astype(str), format="%Y%m%d")
    out["index_code"] = index_code
    if "vol" in out.columns and "volume" not in out.columns:
        out["volume"] = out["vol"]
    if "amount" not in out.columns:
        out["amount"] = 0
    for c in ["open", "high", "low", "close", "volume", "amount"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    required = ["date", "index_code", "open", "high", "low", "close", "volume", "amount"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"指数日线缺少列: {missing}")
    return out[required].sort_values("date").reset_index(drop=True)


def _save_index_daily(df: pd.DataFrame, index_code: str, incremental: bool) -> bool:
    from backend.data.raw_data_storage import RawDataStorage
    if df is None or len(df) == 0:
        return True
    storage = RawDataStorage()
    return storage.save_daily_data_by_index(df=df, index_code=index_code, incremental=incremental)


def _parse_rate_limit_seconds(err_msg: str, default: int = 25) -> int:
    m = re.search(r"(\d+)\s*秒\s*后", str(err_msg))
    return max(1, int(m.group(1))) if m else default


def fetch_one_index(
    pro,
    index_code: str,
    base_path: Path,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
    rate_limiter: Optional[RateLimiter] = None,
    max_retries: int = 5,
) -> bool:
    index_code = index_code.strip().upper()
    sdt, edt = _calc_fetch_range(index_code, base_path, incremental, start_date, end_date)
    if sdt > edt:
        logger.info(f"{index_code} 本地已是最新（无需请求），跳过")
        return True
    logger.info(f"采集指数 {index_code} 日线: start={sdt}, end={edt}, incremental={incremental}")

    df = None
    for attempt in range(max_retries):
        if rate_limiter:
            rate_limiter.acquire()
        try:
            raw = pro.index_daily(ts_code=index_code, start_date=sdt, end_date=edt)
            df = _standardize_index_daily_df(raw, index_code)
            break
        except Exception as e:
            err_str = str(e)
            if "请求过于频繁" in err_str:
                wait_sec = _parse_rate_limit_seconds(err_str)
                logger.warning(f"{index_code} 请求过于频繁，{wait_sec} 秒后重试 ({attempt + 1}/{max_retries})")
                time.sleep(wait_sec)
                continue
            raise
        finally:
            if rate_limiter:
                rate_limiter.release()

    if df is None:
        logger.error(f"{index_code} 在 {max_retries} 次重试后未获取到数据，跳过")
        return False
    if len(df) == 0:
        logger.warning(f"{index_code} 返回空数据")
        return True
    ok = _save_index_daily(df, index_code=index_code, incremental=incremental)
    logger.info(f"{index_code} 保存结果: {ok}, 行数: {len(df)}")
    return ok


def _read_missing_list(path: Path) -> List[str]:
    if not path.exists():
        logger.error(f"缺失列表不存在: {path}")
        return []
    text = path.read_text(encoding="utf-8").strip()
    codes = [x.strip().upper() for x in text.split("\n") if x.strip()]
    logger.info(f"从缺失列表读取 {len(codes)} 个指数: {path}")
    return sorted(codes)


def build_index_list(
    base_path: Path,
    indices_arg: Optional[str],
    from_missing_list: Optional[str],
    limit: Optional[int],
) -> Tuple[List[str], bool]:
    """
    构建待采集的指数代码列表。优先 DB(index_info)，其次 CSV。

    :return: (指数代码列表, 是否来自 DB，用于拉取后回写 data_start_date/data_end_date)
    """
    if from_missing_list:
        return (_read_missing_list(Path(from_missing_list)), False)
    if indices_arg:
        codes = [x.strip().upper() for x in indices_arg.split(",") if x.strip()]
        return (sorted(codes), False)
    codes, from_db = load_indices_from_db()
    if not codes:
        codes = load_indices_from_csv(base_path)
    if limit:
        codes = codes[:limit]
    return (codes, from_db)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tushare 指数日线采集，保存到 raw/daily/by_index")
    parser.add_argument("--token", type=str, default=None, help="Tushare token")
    parser.add_argument("--base-path", type=str, default=None, help=f"数据根目录，默认 {DEFAULT_BASE_PATH}")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期 YYYYMMDD")
    parser.add_argument("--end-date", type=str, default=None,
                        help="结束日期 YYYYMMDD，未指定时使用 pro.trade_cal 最后交易日")
    parser.add_argument("--indices", type=str, default=None, help="逗号分隔的指数代码，如 000001.SH,399001.SZ")
    parser.add_argument("--from-missing-list", type=str, default=None, help="缺失列表文件（由 check_index_daily_missing 生成）")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少个指数（测试用）")
    parser.add_argument("--incremental", action="store_true", default=True, help="增量模式")
    parser.add_argument("--no-incremental", dest="incremental", action="store_false")
    parser.add_argument("--max-requests-per-minute", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--http-url", type=str, default=DEFAULT_HTTP_URL,
                        help=f"DataApi 地址，默认 {DEFAULT_HTTP_URL}")
    args = parser.parse_args()

    try:
        import tushare as ts
    except ImportError:
        logger.error("请安装 tushare: pip install tushare")
        return 1

    token = _get_token(args)
    pro = ts.pro_api(token=token)
    pro._DataApi__http_url = (args.http_url or DEFAULT_HTTP_URL).strip()
    if not args.end_date:
        latest_edt = _get_latest_trade_date_from_cal(pro)
        args.end_date = latest_edt or datetime.now().strftime("%Y%m%d")
        if latest_edt:
            logger.info(f"未指定 --end-date，使用 trade_cal 最后交易日: {latest_edt}")
    base_path = Path(args.base_path).resolve() if args.base_path else DEFAULT_BASE_PATH
    indices, from_db = build_index_list(
        base_path, args.indices, args.from_missing_list, args.limit
    )
    if not indices:
        logger.error(
            "未得到任何指数代码，请先维护 index_info 表或运行 index_basic_import.py，或指定 --indices"
        )
        return 1

    db_session = None
    index_repo = None
    if from_db:
        try:
            from backend.src.storage.mysql_db import get_session_maker
            from backend.src.storage.index_info_repo import IndexInfoRepo

            db_session = get_session_maker()()
            index_repo = IndexInfoRepo(db_session)
        except Exception as e:
            logger.warning(f"无法连接数据库，将不回写日线起止时间: {e}")
            from_db = False

    rate_limiter = RateLimiter(
        max_requests_per_minute=args.max_requests_per_minute,
        concurrency=args.concurrency,
    )
    ok_cnt = 0
    start_time = time.time()
    for i, code in enumerate(indices, 1):
        try:
            ok = fetch_one_index(
                pro, code, base_path, args.incremental,
                args.start_date, args.end_date, rate_limiter,
            )
            if ok:
                ok_cnt += 1
                if from_db and index_repo:
                    start_d, end_d = _get_index_daily_date_range(code, base_path)
                    if start_d is not None and end_d is not None:
                        index_repo.update_data_range(code, start_d, end_d)
                        db_session.commit()
        except Exception as e:
            logger.error(f"处理失败: {code} - {e}")
        if i % 20 == 0 or i == len(indices):
            elapsed = time.time() - start_time
            logger.info(f"进度: {i}/{len(indices)}, 成功: {ok_cnt}, 耗时: {elapsed:.1f}s")
    if db_session is not None:
        try:
            db_session.close()
        except Exception:
            pass
    logger.info(f"完成: 成功 {ok_cnt}/{len(indices)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
