#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tushare 官方日线接口获取日线数据并保存到本地 raw/daily/by_stock。

日线数据通过 Tushare 标准接口 pro.daily(ts_code, start_date, end_date) 获取，
参见：https://tushare.pro/document/2?doc_id=27 （日线行情）。

优化点：
1. --max-requests-per-minute / --concurrency 速率限制
2. 令牌桶算法控制请求频率
3. Token 支持：--token > 环境变量 TUSHARE_TOKEN / CZSC_TOKEN > 脚本默认

无参数执行时，默认拉取「当天」或「当日最近交易日」的全市场日线（单日 pro.daily(trade_date=...)），
便于定时任务或前端一键拉取当日数据。

# 拉取当天全市场日线（无参数即默认当天）
python scripts/daily/fetch.py

# 历史某一天全市场（日线 pro.daily(trade_date=...) + 每日指标 pro.daily_basic(trade_date=...)）
python scripts/daily/fetch.py --trade-date 20180810
python scripts/daily/fetch.py --trade-date 20180726 --no-daily-basic

# 指定日期范围
python scripts/daily/fetch.py --start-date 20260212 --end-date 20260213 
python scripts/daily/fetch.py --start-date 20150101 --end-date 20260213 --resume-after 000089.SH

# 指定股票
python scripts/daily/fetch.py --stocks 600078.SH,000001.SZ
python scripts/daily/fetch.py --stocks 000001.SZ --start-date 20150101 --end-date 20260213 

# 断点续跑、缺失列表（日线遗漏列表可由 check_daily_missing.py 生成）
python scripts/daily/fetch.py --checkpoint --from-missing-list .stock_data/metadata/missing_stocks_xxx.txt
python scripts/daily/fetch.py --from-missing-list .stock_data/metadata/missing_daily_stocks_20260213_120000.txt

# 默认会将每日指标（市盈率、市值、换手率等）合并到日线；不需要时可关闭
python scripts/daily/fetch.py --no-daily-basic --stocks 600078.SH,000001.SZ

# 从数据库获取股票列表（未指定 --stocks/--from-missing-list 时优先 DB）
python scripts/daily/fetch.py

# --check：检测本地日线是否完整（本地最后日期 < trade_cal 最后交易日则拉取），拉取失败的写入 metadata 下文件
python scripts/daily/fetch.py --check
"""

import argparse
import os
import re
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from collections import deque

import pandas as pd
from loguru import logger

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 默认 Tushare token（未设置环境变量时使用）
DEFAULT_TUSHARE_TOKEN = "5049750782419706635"
# daily_basic 为日线指标接口，自定义端点可能未实现，可改用官方 API
OFFICIAL_TUSHARE_API = "https://api.tushare.pro"
DAILY_BASIC_FIELDS = (
    "ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,"
    "pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,"
    "total_share,float_share,free_share,total_mv,circ_mv"
)

class RateLimiter:
    """请求速率限制器，使用令牌桶算法"""
    
    def __init__(self, max_requests_per_minute: int = 400, concurrency: int = 1):
        """
        初始化速率限制器
        
        Args:
            max_requests_per_minute: 每分钟最大请求数
            concurrency: 并发度（同时进行的请求数）
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.concurrency = concurrency
        
        # 计算令牌生成间隔（秒）
        self.token_interval = 60.0 / max_requests_per_minute
        
        # 令牌桶状态
        self.tokens = max_requests_per_minute  # 初始满桶
        self.last_refill_time = time.time()
        self.lock = threading.RLock()
        
        # 请求历史记录（用于监控和调试）
        self.request_history = deque(maxlen=100)
        
        # 并发控制
        self.semaphore = threading.Semaphore(concurrency)
        self.active_requests = 0
        
        logger.info(f"速率限制器初始化: {max_requests_per_minute} 请求/分钟, 并发度: {concurrency}")
    
    def acquire(self) -> None:
        """获取一个请求令牌，如果超过限制则等待"""
        with self.semaphore:
            self._wait_for_token()
            with self.lock:
                self.tokens -= 1
                self.active_requests += 1
                self.request_history.append(time.time())
    
    def release(self) -> None:
        """释放请求资源"""
        with self.lock:
            self.active_requests -= 1
    
    def _wait_for_token(self) -> None:
        """等待直到有可用令牌"""
        while True:
            with self.lock:
                # 补充令牌
                now = time.time()
                time_passed = now - self.last_refill_time
                new_tokens = int(time_passed / self.token_interval)
                
                if new_tokens > 0:
                    self.tokens = min(self.max_requests_per_minute, 
                                     self.tokens + new_tokens)
                    self.last_refill_time = now
                
                # 如果有可用令牌，立即返回
                if self.tokens > 0:
                    return
            
            # 计算需要等待的时间
            wait_time = self.token_interval - (now - self.last_refill_time)
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # 小步休眠避免CPU占用
    
    def get_status(self) -> dict:
        """获取当前状态"""
        with self.lock:
            now = time.time()
            
            # 计算最近一分钟的请求数
            one_minute_ago = now - 60
            recent_requests = sum(1 for t in self.request_history if t > one_minute_ago)
            
            return {
                'tokens_available': self.tokens,
                'max_tokens': self.max_requests_per_minute,
                'active_requests': self.active_requests,
                'max_concurrency': self.concurrency,
                'recent_requests_per_minute': recent_requests,
                'token_interval_seconds': self.token_interval
            }


def _parse_stocks(stocks: Optional[str]) -> Optional[List[str]]:
    """解析股票列表参数"""
    if not stocks:
        return None
    items = [x.strip().upper() for x in stocks.split(",") if x.strip()]
    return items or None


def _normalize_ts_code(x: Optional[str]) -> Optional[str]:
    """标准化 ts_code（用于 resume 参数）"""
    if not x:
        return None
    s = str(x).strip().upper()
    if not s:
        return None
    # 兼容 SH600078 / SZ000001
    if s.startswith("SH") and len(s) == 8 and s[2:].isdigit():
        return f"{s[2:]}.SH"
    if s.startswith("SZ") and len(s) == 8 and s[2:].isdigit():
        return f"{s[2:]}.SZ"
    return s


def _default_checkpoint_path() -> Path:
    """默认 checkpoint 路径（日线采集）"""
    d = project_root / ".stock_data" / ".checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d / "daily.txt"


def _read_checkpoint(path: Path) -> Optional[str]:
    """读取 checkpoint，返回 resume-after ts_code"""
    try:
        if not path.exists():
            return None
        s = path.read_text(encoding="utf-8").strip()
        return _normalize_ts_code(s)
    except Exception as e:
        logger.warning(f"读取 checkpoint 失败: {path} - {e}")
        return None


def _write_checkpoint(path: Path, ts_code: str) -> None:
    """写入 checkpoint（保存最后成功处理的 ts_code）"""
    try:
        path.write_text(str(ts_code).strip().upper(), encoding="utf-8")
    except Exception as e:
        logger.warning(f"写入 checkpoint 失败: {path} - {e}")


def _apply_resume(stocks: List[str], resume_after: Optional[str]) -> List[str]:
    """根据 resume-after 过滤股票列表（从指定股票之后开始）"""
    ra = _normalize_ts_code(resume_after)
    if not ra:
        return stocks
    if ra not in stocks:
        logger.warning(f"resume-after 未命中股票列表: {ra}；将从头开始")
        return stocks
    idx = stocks.index(ra)
    return stocks[idx + 1 :]


def _list_daily_year_files(base_dir: Path) -> List[Path]:
    """列出某股票日线目录下所有 parquet 文件（stock_code=xxx 下直接存 xxx_2015.parquet，无 year 子目录）"""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("*.parquet"))


def _get_latest_timestamp(stock_code: str) -> Optional[pd.Timestamp]:
    """获取某股票日线本地最新交易日（用于增量）"""
    base_dir = project_root / ".stock_data" / "raw" / "daily" / "by_stock" / f"stock_code={stock_code}"
    files = _list_daily_year_files(base_dir)
    if not files:
        return None
    try:
        dfs = []
        for fp in files:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0 and "date" in df.columns:
                df_clean = df.dropna(axis=1, how='all')
                if not df_clean.empty:
                    dfs.append(df_clean)
        if not dfs:
            return None
        combined = pd.concat(dfs, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"])
        return combined["date"].max()
    except Exception as e:
        logger.warning(f"读取日线最新日期失败: {base_dir} - {e}")
        return None


def _get_latest_trade_date_from_cal(pro, exchange: str = "SSE") -> Optional[str]:
    """通过 pro.trade_cal 获取最后交易日（is_open=1 的最大 cal_date），与 trade_cal.py 一致。"""
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


def _get_latest_trade_date_yyyymmdd(stock_code: str) -> Optional[str]:
    """获取某股票本地日线最新交易日，返回 YYYYMMDD；无数据返回 None。"""
    ts = _get_latest_timestamp(stock_code)
    if ts is None:
        return None
    return pd.to_datetime(ts).strftime("%Y%m%d")


def _load_stock_list_from_db() -> Tuple[List[str], bool]:
    """从 MySQL stock_basic 表读取股票代码列表。返回 (codes, True)；失败或空返回 ([], False)。"""
    try:
        from backend.src.storage.mysql_db import get_session_maker
        from backend.src.storage.stock_basic_repo import StockBasicRepo

        session_maker = get_session_maker()
        session = session_maker()
        try:
            repo = StockBasicRepo(session)
            codes = repo.list_symbols()
            codes = [c for c in codes if c and str(c).endswith((".SH", ".SZ"))]
            if codes:
                logger.info(f"从 stock_basic 表加载 {len(codes)} 只股票")
                return (sorted(codes), True)
            return ([], False)
        finally:
            session.close()
    except Exception as e:
        logger.debug(f"从数据库加载股票列表失败，将回退到 pro.stock_basic: {e}")
        return ([], False)


def _is_yyyymmdd(x: Optional[str]) -> bool:
    """判断是否为 YYYYMMDD"""
    return bool(x) and len(x) == 8 and str(x).isdigit()


def _to_yyyymmdd(x: Optional[str], default: str) -> str:
    """将日期参数规范为 YYYYMMDD（pro.daily 使用）"""
    if not x:
        return default
    s = str(x).strip()
    if _is_yyyymmdd(s):
        return s
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10].replace("-", "")
    return default


def _build_daily_range(
    start_arg: Optional[str],
    end_arg: Optional[str],
    fallback_sdt: str,
    fallback_edt: str
) -> Tuple[str, str]:
    """构建日线 start_date/end_date（YYYYMMDD）"""
    s_raw = start_arg if start_arg else fallback_sdt
    e_raw = end_arg if end_arg else fallback_edt
    return _to_yyyymmdd(s_raw, fallback_sdt), _to_yyyymmdd(e_raw, fallback_edt)


# 本地无该股票数据时，从该日期起拉取到当前最后交易日
DEFAULT_START_WHEN_NO_LOCAL = "20250101"


def _calc_fetch_range_daily(
    stock_code: str,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, str]:
    """计算日线采集日期范围（YYYYMMDD）。本地无数据时从 DEFAULT_START_WHEN_NO_LOCAL 拉到 end_date。"""
    edt = end_date or datetime.now().strftime("%Y%m%d")
    if not incremental or start_date:
        return start_date or edt, edt
    last_ts = _get_latest_timestamp(stock_code)
    if last_ts is None:
        return DEFAULT_START_WHEN_NO_LOCAL, edt
    # 从下一交易日开始（简单用 +1 天）
    next_d = (pd.to_datetime(last_ts) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    return next_d, edt


def build_pro(token: str, http_url: Optional[str] = None):
    """构建 Tushare pro；不传 http_url 时使用默认自定义端点。"""
    import tushare as ts
    pro = ts.pro_api(token=token)
    pro._DataApi__http_url = http_url or "http://stk_mins.xiximiao.com/dataapi"
    return pro


def _standardize_daily_df(df: pd.DataFrame, ts_code: str) -> Optional[pd.DataFrame]:
    """将 pro.daily 返回的数据标准化为 raw/daily/by_stock 存储格式（date, stock_code, open, high, low, close, volume, amount）"""
    if df is None or len(df) == 0:
        return None
    out = df.copy()
    if "trade_date" not in out.columns:
        raise ValueError(f"日线数据缺少 trade_date 列，实际列：{list(out.columns)}")
    out["date"] = pd.to_datetime(out["trade_date"].astype(str), format="%Y%m%d")
    out["stock_code"] = ts_code
    if "vol" in out.columns and "volume" not in out.columns:
        out["volume"] = out["vol"]
    if "amount" not in out.columns:
        out["amount"] = 0
    for c in ["open", "high", "low", "close", "volume", "amount"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date", "open", "high", "low", "close"])
    required = ["date", "stock_code", "open", "high", "low", "close", "volume", "amount"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"日线数据缺少必需列: {missing}；实际列：{list(out.columns)}")
    return out[required].sort_values("date").reset_index(drop=True)


def _standardize_daily_df_full_market(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    将 pro.daily(trade_date=...) 单日全市场返回的数据标准化为存储格式。
    输入 df 需含 ts_code、trade_date 列，输出含 date、stock_code、open、high、low、close、volume、amount。
    """
    if df is None or len(df) == 0:
        return None
    out = df.copy()
    if "trade_date" not in out.columns or "ts_code" not in out.columns:
        raise ValueError(f"日线全市场数据缺少 trade_date/ts_code 列，实际列：{list(out.columns)}")
    out["date"] = pd.to_datetime(out["trade_date"].astype(str), format="%Y%m%d")
    out["stock_code"] = out["ts_code"].astype(str).str.strip().str.upper()
    if "vol" in out.columns and "volume" not in out.columns:
        out["volume"] = out["vol"]
    if "amount" not in out.columns:
        out["amount"] = 0
    for c in ["open", "high", "low", "close", "volume", "amount"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["date", "stock_code", "open", "high", "low", "close"])
    required = ["date", "stock_code", "open", "high", "low", "close", "volume", "amount"]
    return out[required].sort_values(["stock_code", "date"]).reset_index(drop=True)


def _fetch_daily_basic_for_stock(
    pro, stock_code: str, start_date: str, end_date: str,
    token: str, http_url: str, rate_limiter: Optional[RateLimiter],
) -> Optional[pd.DataFrame]:
    """
    拉取单只股票在 [start_date, end_date] 的 daily_basic（每日指标）。
    若当前端点失败则用官方 API 重试一次。返回含 trade_date 及指标列的 DataFrame。
    """
    try:
        if rate_limiter:
            rate_limiter.acquire()
        try:
            df = pro.daily_basic(
                ts_code=stock_code, start_date=start_date, end_date=end_date,
                fields=DAILY_BASIC_FIELDS,
            )
        finally:
            if rate_limiter:
                rate_limiter.release()
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        logger.debug(f"daily_basic 拉取失败 {stock_code}: {e}")
    if http_url.rstrip("/") != OFFICIAL_TUSHARE_API.rstrip("/"):
        try:
            if rate_limiter:
                rate_limiter.acquire()
            try:
                pro_official = build_pro(token, http_url=OFFICIAL_TUSHARE_API)
                df = pro_official.daily_basic(
                    ts_code=stock_code, start_date=start_date, end_date=end_date,
                    fields=DAILY_BASIC_FIELDS,
                )
            finally:
                if rate_limiter:
                    rate_limiter.release()
            if df is not None and len(df) > 0:
                return df
        except Exception as e2:
            logger.debug(f"官方 API daily_basic 仍失败 {stock_code}: {e2}")
    return None


def _fetch_daily_basic_for_date(
    pro, trade_date: str, token: str, http_url: str,
    rate_limiter: Optional[RateLimiter],
) -> Optional[pd.DataFrame]:
    """
    拉取某一天全市场的每日指标：pro.daily_basic(trade_date=...)，不传 ts_code。
    失败时尝试官方 API。返回含 trade_date、ts_code 及指标列的 DataFrame。
    """
    try:
        if rate_limiter:
            rate_limiter.acquire()
        try:
            df = pro.daily_basic(trade_date=trade_date, fields=DAILY_BASIC_FIELDS)
        finally:
            if rate_limiter:
                rate_limiter.release()
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        logger.debug(f"daily_basic(trade_date={trade_date}) 拉取失败: {e}")
    if http_url.rstrip("/") != OFFICIAL_TUSHARE_API.rstrip("/"):
        try:
            if rate_limiter:
                rate_limiter.acquire()
            try:
                pro_official = build_pro(token, http_url=OFFICIAL_TUSHARE_API)
                df = pro_official.daily_basic(trade_date=trade_date, fields=DAILY_BASIC_FIELDS)
            finally:
                if rate_limiter:
                    rate_limiter.release()
            if df is not None and len(df) > 0:
                return df
        except Exception as e2:
            logger.debug(f"官方 API daily_basic(trade_date=...) 仍失败: {e2}")
    return None


def _merge_daily_basic(daily_df: pd.DataFrame, basic_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    将 daily_basic 按日期合并到日线 DataFrame。
    daily_df 必有 date 列，basic_df 有 trade_date (YYYYMMDD)；合并后追加 turnover_rate, pe_ttm, total_mv 等列。
    """
    if basic_df is None or len(basic_df) == 0:
        return daily_df
    out = daily_df.copy()
    basic = basic_df.copy()
    basic["date"] = pd.to_datetime(basic["trade_date"].astype(str), format="%Y%m%d")
    extra_cols = [
        "turnover_rate", "turnover_rate_f", "volume_ratio",
        "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm",
        "total_share", "float_share", "free_share", "total_mv", "circ_mv",
    ]
    cols_to_merge = ["date"] + [c for c in extra_cols if c in basic.columns]
    out = out.merge(basic[cols_to_merge], on="date", how="left")
    return out


def _merge_daily_basic_full_market(
    daily_df: pd.DataFrame, basic_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """
    将单日全市场 daily_basic 按 date+stock_code 合并到日线 DataFrame。
    daily_df 含 date、stock_code；basic_df 含 trade_date、ts_code，合并后追加指标列。
    """
    if basic_df is None or len(basic_df) == 0:
        return daily_df
    out = daily_df.copy()
    basic = basic_df.copy()
    basic["date"] = pd.to_datetime(basic["trade_date"].astype(str), format="%Y%m%d")
    basic["stock_code"] = basic["ts_code"].astype(str).str.strip().str.upper()
    extra_cols = [
        "turnover_rate", "turnover_rate_f", "volume_ratio",
        "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm",
        "total_share", "float_share", "free_share", "total_mv", "circ_mv",
    ]
    cols = ["date", "stock_code"] + [c for c in extra_cols if c in basic.columns]
    out = out.merge(basic[cols], on=["date", "stock_code"], how="left")
    return out


def _save_daily_df(df: pd.DataFrame, stock_code: str, incremental: bool) -> bool:
    """保存日线数据到 RawDataStorage（raw/daily/by_stock）"""
    from backend.data.raw_data_storage import RawDataStorage

    if df is None or len(df) == 0:
        return True
    storage = RawDataStorage()
    return storage.save_daily_data_by_stock(
        df=df, stock_code=stock_code, incremental=incremental
    )


def fetch_by_trade_date(
    pro,
    trade_date: str,
    rate_limiter: Optional[RateLimiter],
    with_daily_basic: bool,
    token: str,
    http_url: str,
    max_retries: int = 5,
) -> Tuple[int, List[str]]:
    """
    按单日全市场拉取：pro.daily(trade_date=...)、可选 pro.daily_basic(trade_date=...)，
    按股票拆分后保存到 raw/daily/by_stock。返回 (成功数, 失败列表)。
    """
    trade_date = _to_yyyymmdd(trade_date, datetime.now().strftime("%Y%m%d"))
    logger.info(f"按单日全市场拉取: trade_date={trade_date}, daily_basic={with_daily_basic}")

    df = None
    for attempt in range(max_retries):
        if rate_limiter:
            rate_limiter.acquire()
        try:
            df = pro.daily(trade_date=trade_date)
            df = _standardize_daily_df_full_market(df)
            break
        except Exception as e:
            err_str = str(e)
            if "请求过于频繁" in err_str:
                wait_sec = _parse_rate_limit_seconds(err_str)
                logger.warning(f"日线请求过于频繁，{wait_sec} 秒后重试（第 {attempt + 1}/{max_retries} 次）")
                time.sleep(wait_sec)
                continue
            raise
        finally:
            if rate_limiter:
                rate_limiter.release()

    if df is None or len(df) == 0:
        logger.error(f"trade_date={trade_date} 日线未获取到数据")
        return 0, []

    if with_daily_basic and token and http_url is not None:
        basic_df = _fetch_daily_basic_for_date(
            pro, trade_date, token, http_url, rate_limiter
        )
        df = _merge_daily_basic_full_market(df, basic_df)

    ok_cnt = 0
    failed_list: List[str] = []
    stock_codes = df["stock_code"].unique().tolist()
    for i, stock_code in enumerate(stock_codes, 1):
        try:
            sub = df[df["stock_code"] == stock_code].copy()
            if _save_daily_df(sub, stock_code=stock_code, incremental=True):
                ok_cnt += 1
            else:
                failed_list.append(stock_code)
        except Exception as e:
            logger.warning(f"{stock_code} 保存失败: {e}")
            failed_list.append(stock_code)
        if i % 500 == 0 or i == len(stock_codes):
            logger.info(f"保存进度: {i}/{len(stock_codes)}")
    logger.info(f"单日全市场完成: 成功 {ok_cnt}/{len(stock_codes)}，失败 {len(failed_list)} 只")
    return ok_cnt, failed_list


def _parse_rate_limit_seconds(err_msg: str, default: int = 25) -> int:
    """从「请求过于频繁…24秒后可用」类错误信息中解析等待秒数，解析不到则返回 default。"""
    s = str(err_msg)
    m = re.search(r"(\d+)\s*秒\s*后", s)
    if m:
        return max(1, int(m.group(1)))
    return default


def fetch_one_stock(
    pro,
    ts_code: str,
    incremental: bool,
    sdt: Optional[str],
    edt: Optional[str],
    rate_limiter: Optional[RateLimiter] = None,
    max_retries: int = 5,
    with_daily_basic: bool = True,
    token: str = "",
    http_url: str = "",
) -> bool:
    """
    采集单只股票日线数据并保存到 raw/daily/by_stock（使用 pro.daily）。
    默认会拉取 daily_basic 并将 turnover_rate/pe/pb/total_mv 等字段合并到日线后保存。
    """
    stock_code = ts_code.strip().upper()
    fallback_edt = datetime.now().strftime("%Y%m%d")
    start_date, end_date = _build_daily_range(
        start_arg=sdt, end_arg=edt, fallback_sdt=fallback_edt, fallback_edt=fallback_edt
    )
    if incremental and not sdt:
        start_date, end_date = _calc_fetch_range_daily(
            stock_code=stock_code, incremental=True, start_date=None, end_date=edt or fallback_edt
        )

    # 若起始日大于结束日，说明本地最后交易日已等于或晚于目标最后交易日，无需请求
    if start_date > end_date:
        logger.info(f"{stock_code} 本地已是最新（无需拉取），跳过")
        return True

    logger.info(f"采集 {stock_code} 日线数据(daily): start={start_date}, end={end_date}, incremental={incremental}")

    df = None
    for attempt in range(max_retries):
        if rate_limiter:
            rate_limiter.acquire()
        try:
            df = pro.daily(ts_code=stock_code, start_date=start_date, end_date=end_date)
            df = _standardize_daily_df(df, ts_code=stock_code)
            break
        except Exception as e:
            err_str = str(e)
            if "请求过于频繁" in err_str:
                wait_sec = _parse_rate_limit_seconds(err_str)
                logger.warning(f"{stock_code} 请求过于频繁，{wait_sec} 秒后重试（第 {attempt + 1}/{max_retries} 次）")
                time.sleep(wait_sec)
                continue
            raise
        finally:
            if rate_limiter:
                rate_limiter.release()

    if df is None:
        logger.error(f"{stock_code} 在 {max_retries} 次重试后仍因限频未获取到数据，跳过")
        return False
    if len(df) == 0:
        logger.warning(f"{stock_code} 返回空数据")
        return True

    if with_daily_basic and token and http_url is not None:
        basic_df = _fetch_daily_basic_for_stock(
            pro, stock_code, start_date, end_date, token, http_url, rate_limiter
        )
        df = _merge_daily_basic(df, basic_df)

    ok = _save_daily_df(df, stock_code=stock_code, incremental=incremental)
    logger.info(f"{stock_code} 保存结果: {ok}, 行数: {len(df)}")
    return ok


def _read_missing_list(file_path: Path) -> List[str]:
    """从缺失股票列表文件读取股票代码"""
    try:
        if not file_path.exists():
            logger.error(f"缺失股票列表文件不存在：{file_path}")
            return []
        content = file_path.read_text(encoding="utf-8").strip()
        stocks = [x.strip().upper() for x in content.split("\n") if x.strip()]
        stocks = [x for x in stocks if x.endswith((".SH", ".SZ"))]
        logger.info(f"从缺失列表读取到 {len(stocks)} 只股票：{file_path}")
        return sorted(stocks)
    except Exception as e:
        logger.error(f"读取缺失股票列表失败：{file_path} - {e}")
        return []


def build_stock_list(pro, stocks_arg: Optional[str], limit: Optional[int],
                     missing_list_path: Optional[str] = None,
                     from_db: bool = True) -> List[str]:
    """构建待处理股票列表：--stocks > --from-missing-list > 数据库 stock_basic > pro.stock_basic 全市场。"""
    stocks = _parse_stocks(stocks_arg)

    if stocks is None and missing_list_path:
        missing_path = Path(missing_list_path)
        stocks = _read_missing_list(missing_path)

    if stocks is None and from_db:
        stocks, ok = _load_stock_list_from_db()
        if not ok:
            stocks = None

    if stocks is None:
        df = pro.stock_basic(exchange="", list_status="L", fields="ts_code")
        stocks = sorted(df["ts_code"].dropna().unique().tolist()) if df is not None and len(df) > 0 else []
        stocks = [x for x in stocks if str(x).endswith((".SH", ".SZ"))]
    if limit:
        stocks = stocks[:limit]
    return stocks


def _check_incomplete_stocks(pro, latest_trade_date: str) -> List[str]:
    """检测本地日线不完整的股票：本地最后日期 < latest_trade_date 或无数据。股票列表优先 DB，空则 pro.stock_basic。"""
    stocks, _ = _load_stock_list_from_db()
    if not stocks:
        stocks = build_stock_list(pro, stocks_arg=None, limit=None, missing_list_path=None, from_db=False)
    if not stocks:
        return []
    incomplete = []
    for ts_code in stocks:
        local_last = _get_latest_trade_date_yyyymmdd(ts_code)
        if local_last is None or local_last < latest_trade_date:
            incomplete.append(ts_code)
    return incomplete


def main():
    """主函数（增加速率限制参数）"""
    args = _parse_args()
    token = _get_token_from_args(args)

    rate_limiter = RateLimiter(
        max_requests_per_minute=args.max_requests_per_minute,
        concurrency=args.concurrency
    )

    http_url = (getattr(args, "http_url", None) or "http://stk_mins.xiximiao.com/dataapi").strip()
    pro = build_pro(token, http_url=http_url)

    # 未指定任何日期时，默认拉取当天（或当日最近交易日）单日全市场
    if not args.start_date and not args.end_date and not getattr(args, "trade_date", None):
        latest_edt = _get_latest_trade_date_from_cal(pro)
        if latest_edt:
            args.trade_date = latest_edt
            logger.info(f"未指定日期，默认拉取当天（最近交易日）: trade_date={latest_edt}")

    # 增量且未指定日期时，用 trade_cal 最后交易日作为 end_date（仅当未走默认 trade_date 时）
    if args.incremental and not args.start_date and not args.end_date:
        latest_edt = _get_latest_trade_date_from_cal(pro)
        if latest_edt:
            args.end_date = latest_edt
            logger.info(f"增量 end_date 使用 trade_cal 最后交易日: {latest_edt}")

    if getattr(args, "trade_date", None):
        # --trade-date：单日全市场 pro.daily(trade_date=...) + 可选 pro.daily_basic(trade_date=...)
        with_daily_basic = getattr(args, "with_daily_basic", True)
        ok_cnt, failed_list = fetch_by_trade_date(
            pro, args.trade_date, rate_limiter,
            with_daily_basic=with_daily_basic, token=token, http_url=http_url,
        )
        if failed_list:
            out_dir = project_root / ".stock_data" / "metadata"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"daily_fetch_failed_trade_date_{ts}.txt"
            out_path.write_text("\n".join(failed_list), encoding="utf-8")
            logger.warning(f"保存失败 {len(failed_list)} 只，已写入: {out_path}")
        return

    if getattr(args, "check", False):
        # --check：只处理不完整的股票，拉取失败的写入文件
        latest_edt = args.end_date or _get_latest_trade_date_from_cal(pro)
        if not latest_edt:
            latest_edt = datetime.now().strftime("%Y%m%d")
        incomplete = _check_incomplete_stocks(pro, latest_edt)
        if not incomplete:
            logger.info("所有股票日线已完整，无需拉取")
            return
        logger.info(f"--check: 检测到 {len(incomplete)} 只股票不完整，开始拉取")
        stocks = incomplete
        args.start_date = None
        args.end_date = latest_edt
        failed_list: List[str] = []
        _run_batch(
            pro, stocks, args, None, rate_limiter,
            token=token, http_url=http_url, failed_out=failed_list,
        )
        if failed_list:
            out_dir = project_root / ".stock_data" / "metadata"
            out_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"daily_fetch_failed_{ts}.txt"
            out_path.write_text("\n".join(failed_list), encoding="utf-8")
            logger.warning(f"拉取失败 {len(failed_list)} 只，已写入: {out_path}")
        return

    stocks = build_stock_list(pro, stocks_arg=args.stocks, limit=args.limit,
                              missing_list_path=args.from_missing_list)

    ckpt_path = _default_checkpoint_path()
    resume_after = args.resume_after
    if args.checkpoint:
        resume_after = resume_after or _read_checkpoint(ckpt_path)
        if resume_after:
            logger.info(f"checkpoint 启用：将从 {resume_after} 之后继续；文件: {ckpt_path}")
        else:
            logger.info(f"checkpoint 启用：未找到历史记录，将从头开始；文件: {ckpt_path}")

    stocks = _apply_resume(stocks, resume_after=resume_after)
    logger.info(f"待处理股票数量: {len(stocks)}")

    failed_list: List[str] = []
    _run_batch(
        pro, stocks, args, ckpt_path if args.checkpoint else None, rate_limiter,
        token=token, http_url=http_url, failed_out=failed_list,
    )
    if failed_list:
        out_dir = project_root / ".stock_data" / "metadata"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"daily_fetch_failed_{ts}.txt"
        out_path.write_text("\n".join(failed_list), encoding="utf-8")
        logger.warning(f"拉取失败 {len(failed_list)} 只: {failed_list[:20]}{' ...' if len(failed_list) > 20 else ''}")
        logger.warning(f"失败列表已写入: {out_path}")

    sys.exit(0)


def _parse_args():
    """解析命令行参数（增加速率限制参数）"""
    parser = argparse.ArgumentParser(description="Tushare 日线数据批量采集，保存到 raw/daily/by_stock（带速率限制）")
    parser.add_argument("--token", type=str, default=None, help="Tushare Token（可选；不传则用环境变量 TUSHARE_TOKEN/CZSC_TOKEN 或默认值）")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期（YYYYMMDD 或 YYYY-MM-DD，可选）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期（YYYYMMDD 或 YYYY-MM-DD，可选）")
    parser.add_argument("--stocks", type=str, default=None, help="指定股票列表（逗号分隔），如 600078.SH,000001.SZ")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少只股票（用于测试）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票处理间隔（秒）")
    parser.add_argument("--incremental", action="store_true", default=True, help="增量模式（默认启用）")
    parser.add_argument("--no-incremental", dest="incremental", action="store_false", help="覆盖模式（不增量）")
    parser.add_argument("--resume-after", type=str, default=None, help="从某只股票之后继续（跳过该股票本身），如 000615.SZ")
    parser.add_argument("--checkpoint", action="store_true", help="启用断点续跑 checkpoint（自动读取/写入 .stock_data/.checkpoints/daily.txt）")
    parser.add_argument("--from-missing-list", type=str, default=None, help="从缺失股票列表文件读取股票代码（由 stock_minute_scan.py 生成），如 .stock_data/metadata/missing_stocks_20240204_160000.txt")
    parser.add_argument("--check", action="store_true", help="检测日线完整性：从 DB 取股票列表，本地最后日期 < trade_cal 最后交易日则拉取；拉取失败的写入 .stock_data/metadata/daily_fetch_failed_*.txt")
    parser.add_argument("--trade-date", type=str, default=None,
                        help="历史某一天全市场：日线用 pro.daily(trade_date=...)，每日指标用 pro.daily_basic(trade_date=...)。格式 YYYYMMDD，如 20180810")

    # 速率限制
    parser.add_argument("--max-requests-per-minute", type=int, default=400,
                       help="每分钟最大请求数（默认400，根据API限制调整）")
    parser.add_argument("--concurrency", type=int, default=1,
                       help="并发请求数（默认1，建议根据网络情况和服务器承受能力调整）")
    parser.add_argument(
        "--with-daily-basic",
        dest="with_daily_basic",
        action="store_true",
        help="拉取每日指标并合并到日线（默认已开启）",
    )
    parser.add_argument(
        "--no-daily-basic",
        dest="with_daily_basic",
        action="store_false",
        help="不拉取每日指标，仅保存 pro.daily 的 OHLCV",
    )
    parser.set_defaults(with_daily_basic=True)
    parser.add_argument(
        "--http-url",
        type=str,
        default="http://stk_mins.xiximiao.com/dataapi",
        help="Tushare DataApi 地址；daily_basic 若失败会自动用官方 API 重试",
    )
    return parser.parse_args()


def _get_token_from_args(args) -> str:
    """从参数或环境变量获取 token：--token > TUSHARE_TOKEN > CZSC_TOKEN > 默认"""
    token = (args.token or "").strip()
    if token:
        return token
    token = (os.getenv("TUSHARE_TOKEN") or os.getenv("CZSC_TOKEN") or "").strip()
    print(f"token: {token or DEFAULT_TUSHARE_TOKEN}")
    return token or DEFAULT_TUSHARE_TOKEN


def _run_batch(
    pro, stocks: List[str], args, ckpt_path: Optional[Path],
    rate_limiter: RateLimiter,
    token: str = "",
    http_url: str = "",
    failed_out: Optional[List[str]] = None,
) -> None:
    """批量执行采集（带速率限制）。failed_out 非空时，拉取失败的 ts_code 会追加到该列表。"""
    ok_cnt = 0
    start_time = time.time()
    with_daily_basic = getattr(args, "with_daily_basic", True)

    for i, ts_code in enumerate(stocks, 1):
        try:
            ok = fetch_one_stock(
                pro, ts_code, args.incremental,
                args.start_date, args.end_date, rate_limiter,
                with_daily_basic=with_daily_basic, token=token, http_url=http_url,
            )
            if ok:
                ok_cnt += 1
                if ckpt_path:
                    _write_checkpoint(ckpt_path, ts_code)
            else:
                if failed_out is not None:
                    failed_out.append(ts_code)
        except Exception as e:
            logger.error(f"处理失败: {ts_code} - {e}")
            if failed_out is not None:
                failed_out.append(ts_code)
        
        # 显示进度和速率状态
        if i % 10 == 0 or i == len(stocks):
            status = rate_limiter.get_status()
            elapsed = time.time() - start_time
            rate_per_minute = i / elapsed * 60 if elapsed > 0 else 0
            
            logger.info(f"进度: {i}/{len(stocks)} ({i/len(stocks)*100:.1f}%), "
                       f"成功: {ok_cnt}, "
                       f"速率: {rate_per_minute:.1f} 股票/分钟, "
                       f"请求: {status['recent_requests_per_minute']:.1f} 请求/分钟")
        
        # 原有的休眠（可选保留，但现在主要用速率限制器）
        if args.sleep and args.sleep > 0:
            time.sleep(args.sleep)
    
    total_time = time.time() - start_time
    logger.info(f"完成：成功 {ok_cnt}/{len(stocks)}，总耗时 {total_time:.1f} 秒")


if __name__ == "__main__":
    import traceback
    try:
        main()
        sys.exit(0)
    except SystemExit as e:
        # 将退出码 2（常见为用法错误）转为 1，便于前端/调度统一处理
        if e.code == 2:
            logger.warning("脚本以退出码 2 结束，已视为失败(1) 处理")
            sys.exit(1)
        raise
    except Exception as e:
        traceback.print_exc()
        logger.exception(f"日线拉取异常: {e}")
        sys.exit(1)