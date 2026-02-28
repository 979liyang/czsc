#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用自定义 Tushare 分钟权限接口（stk_mins）批量采集上证/深证股票 60 分钟级别数据并保存到本地 parquet。
仅支持 60 分钟周期，数据存 raw/minute_60_by_stock。单次请求最多返回 8000 条，按前半年/后半年分片请求。
带请求速率限制（令牌桶）。

加速建议（在接口不报限流的前提下）：
1. 提高每分钟请求数：--max-requests-per-minute 450（或接口允许的上限）
2. 提高并发数：--concurrency 4 或 6
示例：
  python scripts/minute60/fetch.py --start-date "2018-01-01 09:00:00" --end-date "2026-02-13 19:00:00"
  python scripts/minute60/fetch.py --detect-missing   # 仅对当前缺失或未更新至昨日的股票请求数据

  # 先检测缺失，只对缺失/未更新到昨日的股票请求数据（目标日=昨天）
	python scripts/minute60/fetch.py --detect-missing

	# 指定目标日：只对“未更新到 2026-02-13”的股票请求
	python scripts/minute60/fetch.py --detect-missing --end-date 2026-02-13

	# 在指定股票范围内做缺失检测
	python scripts/minute60/fetch.py --stocks 600078.SH,000001.SZ --detect-missing
若出现限流/429，可适当降低上述两个参数。
"""

import argparse
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from collections import deque

import pandas as pd
from loguru import logger

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 默认 Tushare token（按你的要求写死）
DEFAULT_TUSHARE_TOKEN = "5049750782419706635"
# 5049750782419706635   

# 单次请求最多返回 8000 条，60 分钟线约半年内可控制在 8000 条以内，按前半年/后半年分片
CHUNK_MONTHS = 6
MINUTE_60_FREQ = "60min"
MINUTE_60_SUBDIR = "minute_60_by_stock"


class RateLimiter:
    """请求速率限制器，使用令牌桶算法"""
    
    def __init__(self, max_requests_per_minute: int = 450, concurrency: int = 1):
        """
        初始化速率限制器
        
        Args:
            max_requests_per_minute: 每分钟最大请求数
            concurrency: 并发度（同时进行的请求数）
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.concurrency = concurrency
        print(f"max_requests_per_minute: {max_requests_per_minute}, concurrency: {concurrency}")
        
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
    """默认 checkpoint 路径（60 分钟专用）"""
    d = project_root / ".stock_data" / ".checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d / "fetch_stk_mins_60min.txt"


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


def _list_month_files(base_dir: Path) -> List[Path]:
    """列出某股票目录下的所有月度 parquet 文件"""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("year=*/**/*.parquet"))


def _get_latest_timestamp(stock_code: str) -> Optional[pd.Timestamp]:
    """获取某股票 60 分钟数据的本地最新时间戳（用于增量）。"""
    base_dir = project_root / ".stock_data" / "raw" / MINUTE_60_SUBDIR / f"stock_code={stock_code}"
    files = _list_month_files(base_dir)
    if not files:
        return None
    latest_file = files[-1]
    try:
        df = pd.read_parquet(latest_file)
        if df is None or len(df) == 0:
            return None
        if "period" in df.columns:
            df = df[df["period"] == 60]
        if "timestamp" not in df.columns or len(df) == 0:
            return None
        return pd.to_datetime(df["timestamp"]).max()
    except Exception as e:
        logger.warning(f"读取最新时间戳失败: {latest_file} - {e}")
        return None


def _yyyymmdd_to_dt_str(x: str, hhmmss: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD HH:MM:SS"""
    dt = datetime.strptime(x, "%Y%m%d")
    return dt.strftime("%Y-%m-%d") + f" {hhmmss}"


def _is_yyyymmdd(x: Optional[str]) -> bool:
    """判断是否为 YYYYMMDD"""
    return bool(x) and len(x) == 8 and str(x).isdigit()


def _to_dt_string(x: str, default_time: str) -> str:
    """将日期/时间字符串规范为 stk_mins 需要的 YYYY-MM-DD HH:MM:SS"""
    s = str(x).strip()
    if _is_yyyymmdd(s):
        return _yyyymmdd_to_dt_str(s, default_time)
    # 兼容 YYYY-MM-DD / YYYY-MM-DD HH:MM:SS
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return f"{s} {default_time}"
    return s


def _build_stk_mins_range(
    start_arg: Optional[str],
    end_arg: Optional[str],
    fallback_sdt: str,
    fallback_edt: str
) -> Tuple[str, str]:
    """构建 stk_mins 的 start_date/end_date（YYYY-MM-DD HH:MM:SS）"""
    s_raw = start_arg if start_arg else fallback_sdt
    e_raw = end_arg if end_arg else fallback_edt
    start_dt = _to_dt_string(s_raw, "09:00:00")
    end_dt = _to_dt_string(e_raw, "19:00:00")
    return start_dt, end_dt


def _parse_dt(x: str) -> pd.Timestamp:
    """解析时间字符串为 Timestamp（支持 YYYYMMDD / YYYY-MM-DD / YYYY-MM-DD HH:MM:SS）"""
    return pd.to_datetime(str(x).strip())


def _format_dt(x: pd.Timestamp) -> str:
    """格式化为 stk_mins 需要的 YYYY-MM-DD HH:MM:SS"""
    ts = pd.to_datetime(x)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _end_of_month(ts: pd.Timestamp) -> pd.Timestamp:
    """返回所在月份最后一天（保持时分秒不变由调用方设置）"""
    return (pd.to_datetime(ts) + pd.offsets.MonthEnd(0)).normalize()


def _iter_month_chunks(start_dt: str, end_dt: str, months: int = CHUNK_MONTHS) -> List[Tuple[str, str]]:
    """按月分片（每片 months 个月），返回 (start_dt, end_dt) 的 datetime 字符串列表"""
    s = _parse_dt(start_dt)
    e = _parse_dt(end_dt)
    if s > e:
        s, e = e, s

    chunks: List[Tuple[str, str]] = []
    cur = s
    while cur <= e:
        # 本片结束月：cur 月向后 (months-1) 月
        end_month_base = (cur + pd.DateOffset(months=months - 1)).normalize()
        end_day = _end_of_month(end_month_base)
        # 结束时间默认 19:00:00；若用户给了更早的 e，则用 e
        chunk_end = end_day + pd.Timedelta(hours=19)
        if chunk_end > e:
            chunk_end = e
        chunks.append((_format_dt(cur), _format_dt(chunk_end)))
        # 下一片起始：chunk_end 次日 09:00:00
        next_day = (chunk_end.normalize() + pd.Timedelta(days=1)) + pd.Timedelta(hours=9)
        cur = next_day
    return chunks


def _fetch_stk_mins_chunked(pro, ts_code: str, start_dt: str, end_dt: str,
                           rate_limiter: Optional[RateLimiter] = None) -> Optional[pd.DataFrame]:
    """按半年分片调用 stk_mins（单次最多 8000 条），合并去重后返回标准化 60 分钟 DataFrame"""
    chunks = _iter_month_chunks(start_dt, end_dt, months=CHUNK_MONTHS)
    logger.info(f"{ts_code} 将按 {CHUNK_MONTHS} 个月（前半年/后半年）分片请求，共 {len(chunks)} 段")

    dfs = []
    for i, (s1, e1) in enumerate(chunks, 1):
        if rate_limiter:
            rate_limiter.acquire()
        
        try:
            logger.info(f"{ts_code} 请求分片 {i}/{len(chunks)}: {s1} ~ {e1}")
            df1 = pro.stk_mins(ts_code=ts_code, freq=MINUTE_60_FREQ, start_date=s1, end_date=e1)
            df1 = _standardize_stk_mins_df(df1, ts_code=ts_code)
            if df1 is not None and len(df1) > 0:
                dfs.append(df1)
        finally:
            if rate_limiter:
                rate_limiter.release()
        
        # 显示速率状态
        if rate_limiter and i % 5 == 0:
            status = rate_limiter.get_status()
            logger.info(f"速率状态: {status['recent_requests_per_minute']:.1f} 请求/分钟, "
                       f"可用令牌: {status['tokens_available']}/{status['max_tokens']}")

    if not dfs:
        return None
    df_all = pd.concat(dfs, ignore_index=True)
    # 去重：以 timestamp 为主键（同一股票同一周期）
    df_all = df_all.drop_duplicates(subset=["timestamp", "stock_code", "period"], keep="last")
    df_all = df_all.sort_values("timestamp").reset_index(drop=True)
    return df_all


def _calc_fetch_range(
    stock_code: str,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, str]:
    """计算采集日期范围（YYYYMMDD）"""
    edt = end_date or datetime.now().strftime("%Y%m%d")
    if not incremental or start_date:
        return start_date or edt, edt
    last_ts = _get_latest_timestamp(stock_code)
    if last_ts is None:
        return edt, edt
    sdt = pd.to_datetime(last_ts).strftime("%Y%m%d")
    return sdt, edt


def build_pro(token: str):
    """按照 set_token.py 的方式构建 pro（自定义分钟接口端点）"""
    import tushare as ts

    pro = ts.pro_api(token="不用管这里")  # 不留空即可
    pro._DataApi__token = token
    pro._DataApi__http_url = "http://stk_mins.xiximiao.com/dataapi"
    return pro


def _standardize_stk_mins_df(df: pd.DataFrame, ts_code: str) -> Optional[pd.DataFrame]:
    """将 pro.stk_mins 返回的数据标准化为本项目 60 分钟存储格式"""
    if df is None or len(df) == 0:
        return None

    out = df.copy()
    dt_col = _pick_dt_col(out)
    out = _rename_common_cols(out)
    out = _ensure_volume_col(out)
    out = _ensure_amount_col(out)
    out = _attach_meta_cols(out, ts_code=ts_code, dt_col=dt_col)
    out = _coerce_numeric_cols(out)
    out = _select_and_validate(out)
    return out


def _pick_dt_col(df: pd.DataFrame) -> str:
    """选择时间列名"""
    for c in ["trade_time", "datetime", "time"]:
        if c in df.columns:
            return c
    raise ValueError(f"stk_mins 返回缺少时间列，实际列：{list(df.columns)}")


def _rename_common_cols(df: pd.DataFrame) -> pd.DataFrame:
    """兼容常见列名大小写"""
    rename = {}
    for c in ["open", "high", "low", "close", "vol", "amount"]:
        if c not in df.columns and c.capitalize() in df.columns:
            rename[c.capitalize()] = c
    # 常见别名兼容
    if "amount" not in df.columns and "amt" in df.columns:
        rename["amt"] = "amount"
    if "vol" not in df.columns and "volume" in df.columns:
        rename["volume"] = "vol"
    return df.rename(columns=rename) if rename else df


def _ensure_volume_col(df: pd.DataFrame) -> pd.DataFrame:
    """确保存在 volume 列"""
    if "volume" not in df.columns and "vol" in df.columns:
        df = df.copy()
        df["volume"] = df["vol"]
    return df


def _ensure_amount_col(df: pd.DataFrame) -> pd.DataFrame:
    """确保存在 amount 列（如缺失尝试从成交额别名映射）"""
    if "amount" in df.columns:
        return df
    if "turnover" in df.columns:
        out = df.copy()
        out["amount"] = out["turnover"]
        return out
    return df


def _coerce_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    """将价格/量额列转为数值类型，便于后续校验与存储"""
    out = df.copy()
    for c in ["open", "high", "low", "close", "volume", "amount"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    # 去掉关键字段为空的行
    out = out.dropna(subset=["timestamp", "open", "high", "low", "close"])
    return out


def _attach_meta_cols(df: pd.DataFrame, ts_code: str, dt_col: str) -> pd.DataFrame:
    """添加 timestamp、stock_code、period 等元信息列（60 分钟固定 period=60）"""
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out[dt_col])
    out["stock_code"] = ts_code
    out["period"] = 60
    return out


def _select_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """选择字段并验证必需列"""
    required = ["timestamp", "stock_code", "open", "high", "low", "close", "volume", "amount", "period"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"stk_mins 数据缺少必需列: {missing}；实际列：{list(df.columns)}")
    return df[required].sort_values("timestamp").reset_index(drop=True)


def _save_minute_df(df: pd.DataFrame, stock_code: str, incremental: bool) -> bool:
    """按年月分组保存 60 分钟数据到 RawDataStorage（minute_60_by_stock）。"""
    from backend.data.raw_data_storage import RawDataStorage

    if df is None or len(df) == 0:
        return True
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["year"] = df["timestamp"].dt.year
    df["month"] = df["timestamp"].dt.month

    storage = RawDataStorage()
    ok_any = False
    for (y, m), g in df.groupby(["year", "month"]):
        g2 = g.drop(columns=["year", "month"])
        ok = storage.save_minute_data_by_stock(
            g2, stock_code=stock_code, year=int(y), month=int(m),
            incremental=incremental, minute_subdir=MINUTE_60_SUBDIR
        )
        ok_any = ok_any or ok
    return ok_any


def fetch_one_stock(pro, ts_code: str, incremental: bool,
                    sdt: Optional[str], edt: Optional[str],
                    rate_limiter: Optional[RateLimiter] = None) -> bool:
    """采集单只股票 60 分钟数据并保存（使用 stk_mins，按半年分片单次最多 8000 条）"""
    stock_code = ts_code.upper()

    # 兼容两类入参
    if (sdt and not _is_yyyymmdd(sdt)) or (edt and not _is_yyyymmdd(edt)):
        fallback = datetime.now().strftime("%Y%m%d")
        start_dt, end_dt = _build_stk_mins_range(start_arg=sdt, end_arg=edt,
                                                  fallback_sdt=fallback, fallback_edt=fallback)
    else:
        sdt2, edt2 = _calc_fetch_range(
            stock_code=stock_code, incremental=incremental,
            start_date=sdt, end_date=edt
        )
        start_dt, end_dt = _build_stk_mins_range(start_arg=None, end_arg=None,
                                                  fallback_sdt=sdt2, fallback_edt=edt2)

    logger.info(f"采集 {stock_code} 60分钟数据(stk_mins): start={start_dt}, end={end_dt}, incremental={incremental}")

    if rate_limiter:
        rate_limiter.acquire()

    try:
        # 按半年分片请求，单次最多 8000 条，避免接口截断
        span_days = (_parse_dt(end_dt) - _parse_dt(start_dt)).days if start_dt and end_dt else 0
        if span_days > 31:
            df = _fetch_stk_mins_chunked(pro, stock_code, start_dt, end_dt, rate_limiter)
        else:
            df = pro.stk_mins(ts_code=stock_code, freq=MINUTE_60_FREQ, start_date=start_dt, end_date=end_dt)
            df = _standardize_stk_mins_df(df, ts_code=stock_code)
    finally:
        if rate_limiter:
            rate_limiter.release()

    if df is None or len(df) == 0:
        logger.warning(f"{stock_code} 返回空数据")
        return True

    ok = _save_minute_df(df, stock_code=stock_code, incremental=incremental)
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


def _detect_missing_stocks(
    stocks: List[str],
    target_end_date: Optional[pd.Timestamp] = None,
) -> List[str]:
    """
    检测当前哪些股票缺失 60 分钟数据或数据未更新至目标日。

    :param stocks: 待检测的股票代码列表
    :param target_end_date: 目标截止日（本地最新时间戳早于此日则视为缺失）。默认昨日。
    :return: 缺失或未更新至目标日的股票代码列表
    """
    if not stocks:
        return []
    if target_end_date is None:
        target_end_date = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
    else:
        target_end_date = pd.to_datetime(target_end_date).normalize()

    missing = []
    for ts_code in stocks:
        latest = _get_latest_timestamp(ts_code)
        if latest is None:
            missing.append(ts_code)
            continue
        if pd.to_datetime(latest).normalize() < target_end_date:
            missing.append(ts_code)
    return sorted(missing)


def build_stock_list(pro, stocks_arg: Optional[str], limit: Optional[int], 
                     missing_list_path: Optional[str] = None) -> List[str]:
    """构建待处理股票列表（优先用户指定；其次从缺失列表；否则用 stock_basic 拉全市场）"""
    stocks = _parse_stocks(stocks_arg)
    
    # 如果指定了缺失列表文件，优先使用
    if stocks is None and missing_list_path:
        missing_path = Path(missing_list_path)
        stocks = _read_missing_list(missing_path)
    
    if stocks is None:
        # stock_basic 用 trade_date 接口：这里直接用 pro.stock_basic
        df = pro.stock_basic(exchange="", list_status="L", fields="ts_code")
        stocks = sorted(df["ts_code"].dropna().unique().tolist()) if df is not None and len(df) > 0 else []
        stocks = [x for x in stocks if str(x).endswith((".SH", ".SZ"))]
    if limit:
        stocks = stocks[:limit]
    return stocks


def main():
    """主函数（增加速率限制参数）"""
    args = _parse_args()
    token = _get_token_from_args(args)
    
    # 初始化速率限制器
    rate_limiter = RateLimiter(
        max_requests_per_minute=args.max_requests_per_minute,
        concurrency=args.concurrency
    )
    
    pro = build_pro(token)
    stocks = build_stock_list(pro, stocks_arg=args.stocks, limit=args.limit, 
                              missing_list_path=args.from_missing_list)

    if args.detect_missing:
        target_end = None
        if args.end_date:
            target_end = _parse_dt(_to_dt_string(args.end_date.strip(), "19:00:00"))
        missing = _detect_missing_stocks(stocks, target_end_date=target_end)
        logger.info(f"检测缺失：共 {len(stocks)} 只候选，其中 {len(missing)} 只缺失或未更新至目标日，将仅请求这些")
        stocks = missing
        if not stocks:
            logger.info("无缺失股票，无需请求数据")
            return

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

    _run_batch(pro, stocks, args, ckpt_path if args.checkpoint else None, rate_limiter)


def _parse_args():
    """解析命令行参数（仅 60 分钟，带速率限制）"""
    parser = argparse.ArgumentParser(description="Tushare stk_mins 60 分钟数据批量采集（按半年分片，单次最多 8000 条）")
    parser.add_argument("--token", type=str, default=None, help="Tushare Token（可选；不传则使用脚本内置默认 token）")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期（YYYYMMDD 或 YYYY-MM-DD HH:MM:SS，可选）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期（YYYYMMDD 或 YYYY-MM-DD HH:MM:SS，可选）")
    parser.add_argument("--stocks", type=str, default=None, help="指定股票列表（逗号分隔），如 600078.SH,000001.SZ")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少只股票（用于测试）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票处理间隔（秒）")
    parser.add_argument("--incremental", action="store_true", default=True, help="增量模式（默认启用）")
    parser.add_argument("--no-incremental", dest="incremental", action="store_false", help="覆盖模式（不增量）")
    parser.add_argument("--resume-after", type=str, default=None, help="从某只股票之后继续（跳过该股票本身），如 000615.SZ")
    parser.add_argument("--checkpoint", action="store_true", help="启用断点续跑 checkpoint（自动读取/写入 .stock_data/.checkpoints/ 下的文件）")
    parser.add_argument("--from-missing-list", type=str, default=None, help="从缺失股票列表文件读取股票代码（由 stock_minute_scan.py 生成），如 .stock_data/metadata/missing_stocks_20240204_160000.txt")
    parser.add_argument("--detect-missing", action="store_true", help="先检测当前哪些股票缺失或未更新至目标日，仅对缺失的股票请求数据（目标日默认昨日，可用 --end-date 指定）")
    
    # 速率限制：提高可加速，过高可能触发 API 限流
    parser.add_argument("--max-requests-per-minute", type=int, default=600,
                       help="每分钟最大请求数（默认450，限流时可调低）")
    parser.add_argument("--concurrency", type=int, default=4,
                       help="并发请求数（默认6，网络 I/O 时可并发多路请求以加速）")
    
    return parser.parse_args()


def _get_token_from_args(args) -> str:
    """从参数或环境变量获取 token"""
    token = (args.token or "").strip()
    return token or DEFAULT_TUSHARE_TOKEN


def _run_batch(pro, stocks: List[str], args, ckpt_path: Optional[Path], 
               rate_limiter: RateLimiter) -> None:
    """批量执行采集（带速率限制）"""
    ok_cnt = 0
    start_time = time.time()
    
    for i, ts_code in enumerate(stocks, 1):
        try:
            ok = fetch_one_stock(pro, ts_code, args.incremental,
                                 args.start_date, args.end_date, rate_limiter)
            ok_cnt += 1 if ok else 0
            if ok and ckpt_path:
                _write_checkpoint(ckpt_path, ts_code)
        except Exception as e:
            logger.error(f"处理失败: {ts_code} - {e}")
        
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
    main()