#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从本地 .stock_data/raw/minute_by_stock 读取股票分钟数据，返回 startDate、endDate 与原始数据。

存储结构（与 fetch_tushare_minute_data_stk_mins.py 一致）：
  .stock_data/raw/minute_by_stock/stock_code={ts_code}/year={year}/{ts_code}_{year}-{month:02d}.parquet

使用示例：
  python scripts/read.py --stocks 600066.SH
  python scripts/read.py --stocks 600066.SH --start-date 20240101 --end-date 20241231
  python scripts/read.py --stocks 600066.SH,000001.SZ
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Any

import pandas as pd
from loguru import logger

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _list_month_files(base_dir: Path) -> List[Path]:
    """列出某股票目录下的所有月度 parquet 文件（与 fetch_tushare_minute_data_stk_mins 一致）"""
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("year=*/**/*.parquet"))


def _normalize_stock_code(code: str) -> str:
    """标准化股票代码（如 600066.SH、SH600066 -> 600066.SH）"""
    s = str(code).strip().upper()
    if not s:
        return s
    if s.startswith("SH") and len(s) == 8 and s[2:].replace(".", "").isdigit():
        return f"{s[2:].replace('.', '')}.SH" if "." not in s[2:] else s
    if s.startswith("SZ") and len(s) == 8 and s[2:].replace(".", "").isdigit():
        return f"{s[2:].replace('.', '')}.SZ" if "." not in s[2:] else s
    return s


def _parse_date(s: Optional[str]) -> Optional[pd.Timestamp]:
    """解析 YYYYMMDD 或 YYYY-MM-DD 为 Timestamp"""
    if not s or not str(s).strip():
        return None
    s = str(s).strip()
    if len(s) == 8 and s.isdigit():
        return pd.to_datetime(s, format="%Y%m%d")
    return pd.to_datetime(s)


def _get_dt_range_from_parquet(base_dir: Path, period: Optional[int]) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    从本地 parquet 文件推断该股票数据的最早、最晚时间（不加载全量数据，只读首尾文件）。
    """
    files = _list_month_files(base_dir)
    if not files:
        return None, None
    min_ts = None
    max_ts = None
    for fp in [files[0], files[-1]]:
        if fp == files[-1] and len(files) == 1:
            pass
        try:
            df = pd.read_parquet(fp)
            if df is None or len(df) == 0:
                continue
            if "period" in df.columns and period is not None:
                df = df[df["period"] == period]
            if "timestamp" not in df.columns or len(df) == 0:
                continue
            ts = pd.to_datetime(df["timestamp"])
            t_min, t_max = ts.min(), ts.max()
            if min_ts is None or t_min < min_ts:
                min_ts = t_min
            if max_ts is None or t_max > max_ts:
                max_ts = t_max
        except Exception as e:
            logger.warning(f"读取 parquet 失败: {fp} - {e}")
    return min_ts, max_ts


def load_local_minute_df(
    stock_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[int] = None,
    base_path: Optional[Path] = None,
) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp], Optional[pd.DataFrame]]:
    """
    从本地 minute_by_stock 目录加载单只股票分钟数据。

    :param stock_code: 股票代码（如 600066.SH）
    :param start_date: 开始日期，可选，YYYYMMDD 或 YYYY-MM-DD
    :param end_date: 结束日期，可选
    :param period: 分钟周期过滤，可选（1/5/15/30/60）
    :param base_path: 数据根目录，默认 project_root/.stock_data
    :return: (start_ts, end_ts, df)。若未传日期则 start/end 为本地实际范围；df 为过滤后的 DataFrame
    """
    base = base_path or project_root / ".stock_data"
    base_dir = base / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
    files = _list_month_files(base_dir)
    if not files:
        logger.warning(f"未找到本地数据: {base_dir}")
        return None, None, None

    dfs = []
    for fp in files:
        try:
            df = pd.read_parquet(fp)
            if df is not None and len(df) > 0:
                dfs.append(df)
        except Exception as e:
            logger.warning(f"读取 parquet 失败: {fp} - {e}")
    if not dfs:
        return None, None, None

    df_all = pd.concat(dfs, ignore_index=True)
    df_all["timestamp"] = pd.to_datetime(df_all["timestamp"])
    if period is not None and "period" in df_all.columns:
        df_all = df_all[df_all["period"] == int(period)]
    if "timestamp" in df_all.columns:
        df_all = df_all.sort_values("timestamp").reset_index(drop=True)

    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    if start_dt is not None:
        df_all = df_all[df_all["timestamp"] >= start_dt]
    if end_dt is not None:
        df_all = df_all[df_all["timestamp"] <= end_dt]
    if "timestamp" in df_all.columns and len(df_all) > 0:
        df_all = df_all.sort_values("timestamp").reset_index(drop=True)

    if len(df_all) == 0:
        logger.warning(f"过滤后无数据: {stock_code}, start={start_date}, end={end_date}")
        return start_dt, end_dt, None

    actual_start = df_all["timestamp"].min()
    actual_end = df_all["timestamp"].max()
    return actual_start, actual_end, df_all


def read(
    stocks: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[int] = 1,
    base_path: Optional[Path] = None,
) -> List[dict]:
    """
    获取本地股票数据，返回数据对象列表。每个对象包含 startDate、endDate、data（原始数据）。

    :param stocks: 股票代码列表
    :param start_date: 开始日期，不传则用本地数据实际最早日期
    :param end_date: 结束日期，不传则用本地数据实际最晚日期
    :param period: 分钟周期，默认 1
    :param base_path: 数据根目录
    :return: [{"stock_code": str, "startDate": str, "endDate": str, "data": pd.DataFrame}, ...]
    """
    base = base_path or project_root / ".stock_data"
    result = []
    for code in stocks:
        sc = _normalize_stock_code(code)
        start_ts, end_ts, df = load_local_minute_df(
            stock_code=sc,
            start_date=start_date,
            end_date=end_date,
            period=period,
            base_path=base,
        )
        if df is None:
            result.append({
                "stock_code": sc,
                "startDate": None,
                "endDate": None,
                "data": None,
            })
            continue
        start_str = start_ts.strftime("%Y%m%d") if start_ts is not None else None
        end_str = end_ts.strftime("%Y%m%d") if end_ts is not None else None
        result.append({
            "stock_code": sc,
            "startDate": start_str,
            "endDate": end_str,
            "data": df,
        })
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从本地 minute_by_stock 读取股票数据，返回 startDate、endDate 与原始数据",
    )
    parser.add_argument("--stocks", type=str, required=True, help="股票代码，逗号分隔，如 600066.SH,000001.SZ")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期，可选，YYYYMMDD 或 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期，可选")
    parser.add_argument("--freq", type=str, default="1min", help="分钟周期：1min/5min/15min/30min/60min，默认 1min")
    parser.add_argument("--base-path", type=str, default=None, help="数据根目录，默认项目根目录/.stock_data")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出（data 为 list of dict）")
    return parser.parse_args()


def _freq_to_period(freq: str) -> int:
    """1min -> 1, 5min -> 5, ..."""
    f = str(freq).strip().lower()
    if f.isdigit():
        return int(f)
    if f.endswith("min"):
        return int(f.replace("min", ""))
    raise ValueError(f"不支持的频率: {freq}")


def main() -> int:
    args = _parse_args()
    base_path = Path(args.base_path).resolve() if args.base_path else None
    period = _freq_to_period(args.freq)
    stocks = [x.strip() for x in args.stocks.split(",") if x.strip()]
    if not stocks:
        logger.error("请提供 --stocks，如 --stocks 600066.SH")
        return 1

    rows = read(
        stocks=stocks,
        start_date=args.start_date,
        end_date=args.end_date,
        period=period,
        base_path=base_path,
    )

    for r in rows:
        sc = r["stock_code"]
        if r["data"] is None:
            logger.warning(f"{sc}: 无数据")
            if args.json:
                print(json.dumps({"stock_code": sc, "startDate": None, "endDate": None, "data": []}, ensure_ascii=False))
            continue
        df = r["data"]
        logger.info(f"{sc}: startDate={r['startDate']}, endDate={r['endDate']}, rows={len(df)}")
        if args.json:
            out = {
                "stock_code": sc,
                "startDate": r["startDate"],
                "endDate": r["endDate"],
                "data": df.to_dict(orient="records"),
            }
            for row in out["data"]:
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
            print(json.dumps(out, ensure_ascii=False, default=str))
        else:
            print(f"stock_code={sc} startDate={r['startDate']} endDate={r['endDate']} rows={len(df)}")
            print(df.head(10).to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
