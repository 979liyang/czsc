#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用自定义 Tushare 分钟权限接口（stk_mins）批量采集上证股票分钟数据并保存到本地 parquet。

只获取上证股票：不指定 --stocks 时拉取上海证券交易所（SSE）全部上市股票（.SH）；
指定 --stocks 时仅保留其中的 .SH 代码，非上证代码（如 .SZ）会被忽略。

要求：
- 入参与 scripts/fetch_tushare_minute_data.py 保持一致
- 存储结构保持一致：
  .stock_data/raw/minute_by_stock/stock_code={ts_code}/year={year}/{ts_code}_{year}-{month:02d}.parquet

数据源：
- 参考 scripts/set_token.py 的方式设置 token 与 http_url
- 使用 pro.stk_mins 获取分钟级别数据

使用案例：
1）先小规模验证（推荐）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --limit 10

2）不指定股票时仅采集上证股票
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --checkpoint

3）采集指定上证股票（逗号分隔）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --stocks 600000.SH,600519.SH

4）指定日期范围（支持两种格式）
    - YYYYMMDD：内部会转换为 stk_mins 的 datetime 字符串
    - YYYY-MM-DD HH:MM:SS：原样传给 stk_mins
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --start-date 20240101 --end-date 20240105 --limit 10
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-02-02 19:00:00"
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-02-02 19:00:00" --stocks 601127.SH

5）覆盖模式（不与本地已有数据合并去重）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --no-incremental --limit 10

6）控制频率（避免被限速/封禁）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --sleep 0.2 --limit 10

7）断点续跑（从某只股票之后继续）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --resume-after 600000.SH
    python scripts_o/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --start-date "2018-01-01 09:00:00" --end-date "2026-02-02 19:00:00" --resume-after 600310.SH

8）断点续跑（自动 checkpoint）
    python scripts/fetch_tushare_minute_data_stk_mins_sh.py --freq 1min --checkpoint

说明：
- 本脚本已内置默认 token（按需写死），默认不需要传入 --token / 设置环境变量
- 如需临时覆盖，可传入 --token

数据落盘说明：
- 输出为 parquet，按股票 + 年份目录、按月份文件拆分
- 文件示例：
  .stock_data/raw/minute_by_stock/stock_code=600000.SH/year=2024/600000.SH_2024-01.parquet
- parquet 内字段（至少包含）：
  timestamp, stock_code, open, high, low, close, volume, amount, period
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed


project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# 默认 Tushare token（按你的要求写死）
DEFAULT_TUSHARE_TOKEN = "5049750782419706635"
# 5049750782419706635
# 5049652140394706635

# 长区间请求可能被接口行数/条数限制截断，这里固定按“两个月两个月”分片请求
CHUNK_MONTHS = 2


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


def _default_checkpoint_path(freq: str) -> Path:
    """默认 checkpoint 路径（按 freq 区分，上证脚本单独文件）"""
    d = project_root / ".stock_data" / ".checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"fetch_stk_mins_sh_{freq}.txt"


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


def _get_latest_timestamp(stock_code: str, period: int) -> Optional[pd.Timestamp]:
    """获取某股票某周期的本地最新时间戳（用于增量）"""
    base_dir = project_root / ".stock_data" / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    files = _list_month_files(base_dir)
    if not files:
        return None
    latest_file = files[-1]
    try:
        df = pd.read_parquet(latest_file)
        if df is None or len(df) == 0:
            return None
        if "period" in df.columns:
            df = df[df["period"] == period]
        if "timestamp" not in df.columns or len(df) == 0:
            return None
        return pd.to_datetime(df["timestamp"]).max()
    except Exception as e:
        logger.warning(f"读取最新时间戳失败: {latest_file} - {e}")
        return None


def _normalize_freq(freq: str) -> str:
    """标准化分钟频率字符串"""
    f = str(freq).strip().lower()
    if f.isdigit():
        f = f"{f}min"
    if f not in {"1min", "5min", "15min", "30min", "60min"}:
        raise ValueError(f"不支持的分钟周期: {freq}，可选：1min/5min/15min/30min/60min")
    return f


def _period_minutes(freq: str) -> int:
    """将 freq 转换成分钟数"""
    return int(freq.replace("min", ""))


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


def _fetch_stk_mins_chunked(pro, ts_code: str, freq: str, start_dt: str, end_dt: str) -> Optional[pd.DataFrame]:
    """按两个月分片调用 stk_mins，合并去重后返回标准化 DataFrame"""
    chunks = _iter_month_chunks(start_dt, end_dt, months=CHUNK_MONTHS)
    logger.info(f"{ts_code} 将按 {CHUNK_MONTHS} 个月分片请求，共 {len(chunks)} 段")

    dfs = []
    for i, (s1, e1) in enumerate(chunks, 1):
        logger.info(f"{ts_code} 请求分片 {i}/{len(chunks)}: {s1} ~ {e1}")
        df1 = pro.stk_mins(ts_code=ts_code, freq=freq, start_date=s1, end_date=e1)
        df1 = _standardize_stk_mins_df(df1, ts_code=ts_code, freq=freq)
        if df1 is not None and len(df1) > 0:
            dfs.append(df1)

    if not dfs:
        return None
    df_all = pd.concat(dfs, ignore_index=True)
    # 去重：以 timestamp 为主键（同一股票同一周期）
    df_all = df_all.drop_duplicates(subset=["timestamp", "stock_code", "period"], keep="last")
    df_all = df_all.sort_values("timestamp").reset_index(drop=True)
    return df_all


def _calc_fetch_range(
    stock_code: str,
    freq: str,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, str]:
    """计算采集日期范围（YYYYMMDD）"""
    period = _period_minutes(freq)
    edt = end_date or datetime.now().strftime("%Y%m%d")
    if not incremental or start_date:
        return start_date or edt, edt
    last_ts = _get_latest_timestamp(stock_code, period=period)
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


def _standardize_stk_mins_df(df: pd.DataFrame, ts_code: str, freq: str) -> Optional[pd.DataFrame]:
    """将 pro.stk_mins 返回的数据标准化为本项目分钟存储格式"""
    if df is None or len(df) == 0:
        return None

    out = df.copy()

    dt_col = _pick_dt_col(out)
    out = _rename_common_cols(out)
    out = _ensure_volume_col(out)
    out = _ensure_amount_col(out)
    out = _attach_meta_cols(out, ts_code=ts_code, freq=freq, dt_col=dt_col)
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


def _attach_meta_cols(df: pd.DataFrame, ts_code: str, freq: str, dt_col: str) -> pd.DataFrame:
    """添加 timestamp、stock_code、period 等元信息列"""
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out[dt_col])
    out["stock_code"] = ts_code
    out["period"] = _period_minutes(freq)
    return out


def _select_and_validate(df: pd.DataFrame) -> pd.DataFrame:
    """选择字段并验证必需列"""
    required = ["timestamp", "stock_code", "open", "high", "low", "close", "volume", "amount", "period"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"stk_mins 数据缺少必需列: {missing}；实际列：{list(df.columns)}")
    return df[required].sort_values("timestamp").reset_index(drop=True)


def _save_minute_df(df: pd.DataFrame, stock_code: str, incremental: bool) -> bool:
    """按年月分组保存分钟数据到 RawDataStorage"""
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
            g2, stock_code=stock_code, year=int(y), month=int(m), incremental=incremental
        )
        ok_any = ok_any or ok
    return ok_any


def fetch_one_stock(pro, ts_code: str, freq: str, incremental: bool, sdt: Optional[str], edt: Optional[str]) -> bool:
    """采集单只股票分钟数据并保存（使用 stk_mins）"""
    stock_code = ts_code.upper()
    f = _normalize_freq(freq)
    # 兼容两类入参：
    # - YYYYMMDD（脚本内会转换为 YYYY-MM-DD HH:MM:SS）
    # - YYYY-MM-DD HH:MM:SS（按用户示例，原样传给 stk_mins）
    # 如果用户传入的是完整时间字符串（如 2018-01-01 09:00:00），则按用户原始参数去请求 stk_mins
    if (sdt and not _is_yyyymmdd(sdt)) or (edt and not _is_yyyymmdd(edt)):
        fallback = datetime.now().strftime("%Y%m%d")
        start_dt, end_dt = _build_stk_mins_range(start_arg=sdt, end_arg=edt, fallback_sdt=fallback, fallback_edt=fallback)
    else:
        sdt2, edt2 = _calc_fetch_range(
            stock_code=stock_code, freq=f, incremental=incremental, start_date=sdt, end_date=edt
        )
        start_dt, end_dt = _build_stk_mins_range(start_arg=None, end_arg=None, fallback_sdt=sdt2, fallback_edt=edt2)

    logger.info(f"采集 {stock_code} 分钟数据(stk_mins): freq={f}, start={start_dt}, end={end_dt}, incremental={incremental}")
    # 长区间容易被接口限制截断：当跨度超过 ~70 天，启用“两个月两个月”分片请求
    span_days = (_parse_dt(end_dt) - _parse_dt(start_dt)).days if start_dt and end_dt else 0
    if span_days >= 70:
        df = _fetch_stk_mins_chunked(pro, stock_code, f, start_dt, end_dt)
    else:
        df = pro.stk_mins(ts_code=stock_code, freq=f, start_date=start_dt, end_date=end_dt)
        df = _standardize_stk_mins_df(df, ts_code=stock_code, freq=f)

    if df is None or len(df) == 0:
        logger.warning(f"{stock_code} 返回空数据")
        return True
    ok = _save_minute_df(df, stock_code=stock_code, incremental=incremental)
    logger.info(f"{stock_code} 保存结果: {ok}, 行数: {len(df)}")
    return ok


def build_stock_list(pro, stocks_arg: Optional[str], limit: Optional[int]) -> List[str]:
    """构建待处理股票列表：仅上证股票。不指定 --stocks 时拉取上证全部；指定时仅保留 .SH，忽略 .SZ 等。"""
    stocks = _parse_stocks(stocks_arg)
    if stocks is None:
        # 仅上证所有股票：exchange="SSE"
        df = pro.stock_basic(exchange="SSE", list_status="L", fields="ts_code")
        stocks = sorted(df["ts_code"].dropna().unique().tolist()) if df is not None and len(df) > 0 else []
        stocks = [x for x in stocks if str(x).endswith(".SH")]
    else:
        # 用户指定了 --stocks 时也只保留上证 .SH，忽略其它
        before = len(stocks)
        stocks = [x for x in stocks if str(x).endswith(".SH")]
        dropped = before - len(stocks)
        if dropped:
            logger.info(f"仅采集上证股票，已忽略 {dropped} 只非上证代码（.SZ 等）")
    if limit:
        stocks = stocks[:limit]
    return stocks


def main():
    """主函数（入参与原脚本一致）"""
    args = _parse_args()
    token = _get_token_from_args(args)
    pro = build_pro(token)
    stocks = build_stock_list(pro, stocks_arg=args.stocks, limit=args.limit)
    ckpt_path = _default_checkpoint_path(args.freq)
    resume_after = args.resume_after
    if args.checkpoint:
        resume_after = resume_after or _read_checkpoint(ckpt_path)
        if resume_after:
            logger.info(f"checkpoint 启用：将从 {resume_after} 之后继续；文件: {ckpt_path}")
        else:
            logger.info(f"checkpoint 启用：未找到历史记录，将从头开始；文件: {ckpt_path}")
    stocks = _apply_resume(stocks, resume_after=resume_after)
    logger.info(f"待处理股票数量: {len(stocks)}")
    _run_batch(pro, stocks, args, ckpt_path if args.checkpoint else None)


def _parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="Tushare stk_mins 分钟数据批量采集（仅上证股票）")
    parser.add_argument("--token", type=str, default=None, help="Tushare Token（可选；不传则使用脚本内置默认 token）")
    parser.add_argument("--freq", type=str, default="1min", choices=["1min", "5min", "15min", "30min", "60min"], help="分钟周期")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期（YYYYMMDD 或 YYYY-MM-DD HH:MM:SS，可选）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期（YYYYMMDD 或 YYYY-MM-DD HH:MM:SS，可选）")
    parser.add_argument("--stocks", type=str, default=None, help="指定股票列表（逗号分隔），如 600000.SH,600519.SH；不指定则拉取全部上证股票")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少只股票（用于测试）")
    parser.add_argument("--concurrency", type=int, default=2, help="并发请求股票数（默认 2）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票处理间隔（秒）")
    parser.add_argument("--incremental", action="store_true", default=True, help="增量模式（默认启用）")
    parser.add_argument("--no-incremental", dest="incremental", action="store_false", help="覆盖模式（不增量）")
    parser.add_argument("--resume-after", type=str, default=None, help="从某只股票之后继续（跳过该股票本身），如 600000.SH")
    parser.add_argument(
        "--checkpoint",
        action="store_true",
        help="启用断点续跑 checkpoint（自动读取/写入 .stock_data/.checkpoints/ 下的文件）",
    )
    return parser.parse_args()


def _get_token_from_args(args) -> str:
    """从参数或环境变量获取 token"""
    token = (args.token or "").strip()
    return token or DEFAULT_TUSHARE_TOKEN


def _run_batch(pro, stocks: List[str], args, ckpt_path: Optional[Path]) -> None:
    """批量执行采集"""
    ok_cnt = 0
    total = len(stocks)

    concurrency = int(getattr(args, "concurrency", 1) or 1)
    if concurrency <= 0:
        concurrency = 1

    logger.info(f"并发参数: concurrency={concurrency}")

    processed = 0
    stop_early = False

    def _one(ts_code: str) -> bool:
        return fetch_one_stock(pro, ts_code, args.freq, args.incremental, args.start_date, args.end_date)

    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for start in range(0, total, concurrency):
            chunk = stocks[start : start + concurrency]
            if not chunk:
                break

            futures = {ex.submit(_one, ts_code): ts_code for ts_code in chunk}
            results: dict[str, bool] = {}

            for fut in as_completed(futures):
                ts_code = futures[fut]
                try:
                    ok = bool(fut.result())
                except Exception as e:
                    ok = False
                    logger.error(f"处理失败: {ts_code} - {e}")
                results[ts_code] = ok

            # 按原顺序推进进度与 checkpoint：只要出现失败，就不再把 checkpoint 推进到失败之后
            for ts_code in chunk:
                processed += 1
                ok = results.get(ts_code, False)
                ok_cnt += 1 if ok else 0

                if ok and ckpt_path:
                    _write_checkpoint(ckpt_path, ts_code)
                elif (not ok) and ckpt_path:
                    # checkpoint 模式下，为避免跳过失败股票，遇到失败就停止后续批次
                    stop_early = True
                    break

            logger.info(f"进度: {processed}/{total}，成功: {ok_cnt}")

            if stop_early:
                logger.warning("checkpoint 模式下检测到失败；为避免跳过失败股票，已停止后续批次。请重试继续。")
                break

            # 每个 chunk 之间的节奏控制：仍保留 sleep（按“每只”语义近似处理）
            # 这里按 chunk 后 sleep 一次，避免并发时 sleep 被放大
            _sleep_if_needed(args.sleep)

    logger.info(f"完成：成功 {ok_cnt}/{total}")


def _sleep_if_needed(seconds: float) -> None:
    """根据参数睡眠"""
    if seconds and seconds > 0:
        import time

        time.sleep(seconds)


if __name__ == "__main__":
    main()

