#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tushare 每日指标接口 daily_basic 获取日线数据并保存到本地 raw/daily/by_stock。

数据通过 pro.daily_basic(ts_code, start_date, end_date) 获取，
参见：https://tushare.pro/document/2?doc_id=32 （每日指标）。
返回字段全部保留：ts_code, trade_date, close, turnover_rate, turnover_rate_f,
volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share,
float_share, free_share, total_mv, circ_mv；为兼容存储格式补充 open/high/low=close, volume=0, amount=0。

优化点：
1. --max-requests-per-minute / --concurrency 速率限制
2. 令牌桶算法控制请求频率
3. Token 支持：--token > 环境变量 TUSHARE_TOKEN / CZSC_TOKEN > 脚本默认

# 全市场日线（增量，token 可从 .env 的 CZSC_TOKEN 读取）
python scripts/fetch_tushare_daily.py

# 指定日期范围
python scripts/fetch_tushare_daily.py --start-date 20150101 --end-date 20260213
python scripts/fetch_tushare_daily.py --start-date 20150101 --end-date 20260213 --resume-after 000089.SH

# 指定股票
python scripts/fetch_tushare_daily.py --stocks 600078.SH,000001.SZ --start-date 20150101 --end-date 20260213

# 断点续跑、缺失列表
python scripts/fetch_tushare_daily.py --checkpoint --from-missing-list .stock_data/metadata/missing_stocks_xxx.txt
"""

import argparse
import os
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

# 默认 Tushare token（未设置环境变量时使用）
DEFAULT_TUSHARE_TOKEN = "5e9c54c85a447442caecc0963668564d88759db1e24b5f8ccefd6187"

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
    return d / "fetch_daily.txt"


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
                dfs.append(df)
        if not dfs:
            return None
        combined = pd.concat(dfs, ignore_index=True)
        combined["date"] = pd.to_datetime(combined["date"])
        return combined["date"].max()
    except Exception as e:
        logger.warning(f"读取日线最新日期失败: {base_dir} - {e}")
        return None


def _is_yyyymmdd(x: Optional[str]) -> bool:
    """判断是否为 YYYYMMDD"""
    return bool(x) and len(x) == 8 and str(x).isdigit()


def _to_yyyymmdd(x: Optional[str], default: str) -> str:
    """将日期参数规范为 YYYYMMDD（pro.daily_basic 使用）"""
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


def _calc_fetch_range_daily(
    stock_code: str,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, str]:
    """计算日线采集日期范围（YYYYMMDD）"""
    edt = end_date or datetime.now().strftime("%Y%m%d")
    if not incremental or start_date:
        return start_date or edt, edt
    last_ts = _get_latest_timestamp(stock_code)
    if last_ts is None:
        return edt, edt
    # 从下一交易日开始（简单用 +1 天）
    next_d = (pd.to_datetime(last_ts) + pd.Timedelta(days=1)).strftime("%Y%m%d")
    return next_d, edt


def build_pro(token: str):
    """构建 Tushare pro，日线数据使用官方 pro.daily 接口（日线行情）"""
    import tushare as ts
    pro = ts.pro_api(token=token)
    return pro


def _standardize_daily_basic_df(df: pd.DataFrame, ts_code: str) -> Optional[pd.DataFrame]:
    """
    将 pro.daily_basic 返回的数据标准化为 raw/daily/by_stock 存储格式。
    保留 daily_basic 全部字段；为兼容存储校验补充 open/high/low=close, volume=0, amount=0。
    参见：https://tushare.pro/document/2?doc_id=32
    """
    if df is None or len(df) == 0:
        return None
    out = df.copy()
    if "trade_date" not in out.columns:
        raise ValueError(f"daily_basic 数据缺少 trade_date 列，实际列：{list(out.columns)}")
    out["date"] = pd.to_datetime(out["trade_date"].astype(str), format="%Y%m%d")
    out["stock_code"] = ts_code
    # daily_basic 仅有 close，无 open/high/low/volume；补全以通过 RawDataStorage 校验
    if "close" not in out.columns:
        raise ValueError(f"daily_basic 数据缺少 close 列，实际列：{list(out.columns)}")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["open"] = out["high"] = out["low"] = out["close"]
    if "volume" not in out.columns:
        out["volume"] = 0
    if "amount" not in out.columns:
        out["amount"] = 0
    out = out.dropna(subset=["date", "close"])
    required = ["date", "stock_code", "open", "high", "low", "close", "volume", "amount"]
    for c in required:
        if c not in out.columns:
            raise ValueError(f"日线数据缺少必需列: {c}；实际列：{list(out.columns)}")
    # 保留所有列（含 turnover_rate, pe, pb, total_mv 等），排序后返回
    return out.sort_values("date").reset_index(drop=True)


def _save_daily_df(df: pd.DataFrame, stock_code: str, incremental: bool) -> bool:
    """保存日线数据到 RawDataStorage（raw/daily/by_stock）"""
    from backend.data.raw_data_storage import RawDataStorage

    if df is None or len(df) == 0:
        return True
    storage = RawDataStorage()
    return storage.save_daily_data_by_stock(
        df=df, stock_code=stock_code, incremental=incremental
    )


def fetch_one_stock(pro, ts_code: str, incremental: bool,
                    sdt: Optional[str], edt: Optional[str],
                    rate_limiter: Optional[RateLimiter] = None) -> bool:
    """采集单只股票每日指标并保存到 raw/daily/by_stock（使用 pro.daily_basic）"""
    stock_code = ts_code.strip().upper()
    fallback_edt = datetime.now().strftime("%Y%m%d")
    start_date, end_date = _build_daily_range(
        start_arg=sdt, end_arg=edt, fallback_sdt=fallback_edt, fallback_edt=fallback_edt
    )
    if incremental and not sdt:
        start_date, end_date = _calc_fetch_range_daily(
            stock_code=stock_code, incremental=True, start_date=None, end_date=edt or fallback_edt
        )

    logger.info(f"采集 {stock_code} 日线数据(daily_basic): start={start_date}, end={end_date}, incremental={incremental}")

    if rate_limiter:
        rate_limiter.acquire()
    try:
        # Tushare 每日指标接口：https://tushare.pro/document/2?doc_id=32
        df = pro.daily_basic(ts_code=stock_code, start_date=start_date, end_date=end_date)
        df = _standardize_daily_basic_df(df, ts_code=stock_code)
    finally:
        if rate_limiter:
            rate_limiter.release()

    if df is None or len(df) == 0:
        logger.warning(f"{stock_code} 返回空数据")
        return True

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
                     end_date: Optional[str] = None) -> List[str]:
    """构建待处理股票列表（优先用户指定；其次从缺失列表；否则用 daily_basic 按交易日取全市场 ts_code）"""
    stocks = _parse_stocks(stocks_arg)

    # 如果指定了缺失列表文件，优先使用
    if stocks is None and missing_list_path:
        missing_path = Path(missing_list_path)
        stocks = _read_missing_list(missing_path)

    if stocks is None:
        # 使用 daily_basic 接口：按某一交易日取全部股票代码（单次最多 6000 条）
        # 参见：https://tushare.pro/document/2?doc_id=32
        trade_date = end_date or datetime.now().strftime("%Y%m%d")
        df = pro.daily_basic(trade_date=trade_date, fields="ts_code")
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
    # 默认每分钟最多 40 次请求，可通过 --max-requests-per-minute 覆盖
    rate_limiter = RateLimiter(
        max_requests_per_minute=args.max_requests_per_minute,
        concurrency=args.concurrency
    )
    
    pro = build_pro(token)
    end_date = (args.end_date or datetime.now().strftime("%Y%m%d"))
    if not _is_yyyymmdd(end_date) and len(str(end_date or "")) >= 10:
        end_date = _to_yyyymmdd(end_date, datetime.now().strftime("%Y%m%d"))
    stocks = build_stock_list(
        pro, stocks_arg=args.stocks, limit=args.limit,
        missing_list_path=args.from_missing_list, end_date=end_date
    )
    
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
    parser.add_argument("--checkpoint", action="store_true", help="启用断点续跑 checkpoint（自动读取/写入 .stock_data/.checkpoints/ 下的文件）")
    parser.add_argument("--from-missing-list", type=str, default=None, help="从缺失股票列表文件读取股票代码（由 stock_minute_scan.py 生成），如 .stock_data/metadata/missing_stocks_20240204_160000.txt")
    
    # 新增参数：速率限制
    parser.add_argument("--max-requests-per-minute", type=int, default=40,
                       help="每分钟最大请求数（默认40，根据API限制调整）")
    parser.add_argument("--concurrency", type=int, default=1, 
                       help="并发请求数（默认1，建议根据网络情况和服务器承受能力调整）")
    
    return parser.parse_args()


def _get_token_from_args(args) -> str:
    """从参数或环境变量获取 token：--token > TUSHARE_TOKEN > CZSC_TOKEN > 默认"""
    token = (args.token or "").strip()
    if token:
        return token
    token = (os.getenv("TUSHARE_TOKEN") or os.getenv("CZSC_TOKEN") or "").strip()
    print(f"token: {token or DEFAULT_TUSHARE_TOKEN}")
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