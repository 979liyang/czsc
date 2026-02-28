#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取所有指数列表并保存到 metadata/index_basic.csv。

使用 Tushare index_basic 接口（https://tushare.pro/document/2?doc_id=94），
可指定多个市场（SSE/SZSE/CSI 等）。输出列与接口一致：symbol, name, fullname,
market, publisher, category, index_type, base_date, base_point, list_date,
weight_rule, desc, exp_date。

使用示例：
  python scripts/index/list.py
  python scripts/index/list.py --token YOUR_TOKEN
  python scripts/index/list.py --output .stock_data/metadata/index_basic.csv --markets SSE,SZSE,CSI
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

DEFAULT_TOKEN = "5049750782419706635"
DEFAULT_BASE_PATH = project_root / ".stock_data"
DEFAULT_CSV = DEFAULT_BASE_PATH / "metadata" / "index_basic.csv"

# 常用市场：SSE 上交所, SZSE 深交所, CSI 中证, CICC 中金, SW 申万 等
DEFAULT_MARKETS = ["SSE", "SZSE", "CSI"]
# 与 test.py 一致：自定义 DataApi 地址
DEFAULT_HTTP_URL = "http://stk_mins.xiximiao.com/dataapi"


def _get_token(args) -> str:
    """优先级：--token > 环境变量 TUSHARE_TOKEN/CZSC_TOKEN > 默认值。"""
    token = (getattr(args, "token", None) or "").strip()
    if token:
        return token
    token = (os.getenv("TUSHARE_TOKEN") or os.getenv("CZSC_TOKEN") or "").strip()
    return token or DEFAULT_TOKEN


def fetch_index_basic(pro, markets: list) -> pd.DataFrame:
    """拉取多市场的指数列表并合并。"""
    all_dfs = []
    for market in markets:
        try:
            df = pro.index_basic(market=market)
            if df is not None and len(df) > 0:
                df["market"] = market
                all_dfs.append(df)
                logger.info(f"市场 {market}: {len(df)} 条指数")
        except Exception as e:
            logger.warning(f"拉取 {market} 失败: {e}")
    if not all_dfs:
        logger.error("未获取到任何指数数据")
        return pd.DataFrame()
    out = pd.concat(all_dfs, ignore_index=True)
    out = out.drop_duplicates(subset=["ts_code"], keep="first")
    return out


def to_csv_columns(df: pd.DataFrame) -> pd.DataFrame:
    """规范为 CSV 输出列，与 index_basic 接口一致：symbol, name, fullname, market 等。"""
    df = df.rename(columns={"ts_code": "symbol"})
    # 与 https://tushare.pro/document/2?doc_id=94 输出参数一致
    col_order = [
        "symbol", "name", "fullname", "market", "publisher", "category",
        "index_type", "base_date", "base_point", "list_date", "weight_rule", "desc", "exp_date"
    ]
    existing = [c for c in col_order if c in df.columns]
    return df[existing].sort_values("symbol").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="获取所有指数列表并保存到 metadata/index_basic.csv")
    parser.add_argument("--output", type=str, default=None, help=f"输出 CSV 路径，默认 {DEFAULT_CSV}")
    parser.add_argument("--markets", type=str, default=",".join(DEFAULT_MARKETS),
                        help="逗号分隔的市场代码，如 SSE,SZSE,CSI")
    parser.add_argument("--token", type=str, default=None,
                        help="Tushare token（可选；不传则用环境变量 TUSHARE_TOKEN/CZSC_TOKEN 或默认）")
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
    markets = [x.strip() for x in args.markets.split(",") if x.strip()]
    if not markets:
        logger.error("至少指定一个市场")
        return 1

    df = fetch_index_basic(pro, markets)
    if df.empty:
        return 1

    out_df = to_csv_columns(df)
    out_path = Path(args.output) if args.output else DEFAULT_CSV
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"已写入 {len(out_df)} 条指数到 {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
