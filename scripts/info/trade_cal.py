#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取交易日历（pro.trade_cal）并输出当前最后交易日日期。

接口文档：https://tushare.pro/document/2?doc_id=26
输出：exchange, cal_date, is_open, pretrade_date；根据 is_open=1 得到最后交易日。

使用示例：
  python scripts/info/trade_cal.py
  python scripts/info/trade_cal.py --exchange SSE --end-date 20261231
  python scripts/info/trade_cal.py --out-csv .stock_data/metadata/trade_cal.csv
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

# 脚本在 scripts/info/trade_cal.py，项目根为 scripts 的上两级
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_TOKEN = "5049750782419706635"
DEFAULT_HTTP_URL = "http://stk_mins.xiximiao.com/dataapi"
DEFAULT_BASE_PATH = project_root / ".stock_data"
DEFAULT_CSV = DEFAULT_BASE_PATH / "metadata" / "trade_cal.csv"


def _get_token(args) -> str:
    """优先级：--token > 环境变量 TUSHARE_TOKEN/CZSC_TOKEN > 默认值。"""
    token = (getattr(args, "token", None) or "").strip()
    if token:
        return token
    token = (os.getenv("TUSHARE_TOKEN") or os.getenv("CZSC_TOKEN") or "").strip()
    return token or DEFAULT_TOKEN


def fetch_trade_cal(pro, exchange: str, start_date: str, end_date: str) -> pd.DataFrame:
    """拉取交易日历。"""
    try:
        df = pro.trade_cal(
            exchange=exchange,
            start_date=start_date,
            end_date=end_date,
        )
        if df is not None and len(df) > 0:
            return df
    except Exception as e:
        logger.warning(f"trade_cal 拉取失败: {e}")
    return pd.DataFrame()


def get_latest_trade_date(df: pd.DataFrame) -> Optional[str]:
    """从日历中取 is_open=1 的最后交易日（cal_date 最大）。"""
    if df is None or len(df) == 0:
        return None
    if "is_open" not in df.columns or "cal_date" not in df.columns:
        return None
    open_days = df[df["is_open"].astype(str).str.strip() == "1"]
    if len(open_days) == 0:
        return None
    return str(open_days["cal_date"].max()).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="获取交易日历并输出当前最后交易日")
    parser.add_argument("--token", type=str, default=None, help="Tushare token（可选）")
    parser.add_argument("--http-url", type=str, default=DEFAULT_HTTP_URL, help="DataApi 地址")
    parser.add_argument("--exchange", type=str, default="SSE", help="交易所：SSE/SZSE，默认 SSE")
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="开始日期 YYYYMMDD，默认约一年前",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="结束日期 YYYYMMDD，默认今日",
    )
    parser.add_argument("--out-csv", type=str, default=None, help=f"输出 CSV 路径，默认不写；示例 {DEFAULT_CSV}")
    args = parser.parse_args()

    try:
        import tushare as ts
    except ImportError:
        logger.error("请安装 tushare: pip install tushare")
        return 1

    token = _get_token(args)
    pro = ts.pro_api(token=token)
    pro._DataApi__http_url = (args.http_url or DEFAULT_HTTP_URL).strip()

    end_d = (args.end_date or "").strip() or datetime.now().strftime("%Y%m%d")
    start_d = (args.start_date or "").strip()
    if not start_d:
        start_dt = datetime.now() - timedelta(days=365)
        start_d = start_dt.strftime("%Y%m%d")

    df = fetch_trade_cal(pro, exchange=args.exchange.strip() or "SSE", start_date=start_d, end_date=end_d)
    if df.empty:
        logger.error("未获取到交易日历数据")
        return 1

    latest = get_latest_trade_date(df)
    if latest:
        print(latest)
        logger.info(f"当前最后交易日: {latest}")
    else:
        logger.warning("日历中无 is_open=1 的交易日")

    if args.out_csv:
        out_path = Path(args.out_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        logger.info(f"已写入交易日历: {out_path} rows={len(df)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
