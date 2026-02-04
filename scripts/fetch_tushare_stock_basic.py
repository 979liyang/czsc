#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拉取上证/深证股票基本信息（stock_basic），生成 CSV，并可选写入 MySQL。

背景：
- `scripts/stock_basic_import.py` 负责“把 CSV upsert 到 MySQL”
- 本脚本负责“从 Tushare 获取 stock_basic 并生成符合导入约定的 CSV”

输出 CSV 列（与 stock_basic_import.py 对齐）：
- symbol,name,market,list_date,delist_date

用法示例：
1）只生成 CSV（推荐先检查文件内容）
    python scripts/fetch_tushare_stock_basic.py --out-csv .stock_data/metadata/stock_basic.csv

2）生成 CSV 并写入 MySQL（要求先完成 db_init_mysql.py，且已配置 CZSC_MYSQL_*）
    python scripts/fetch_tushare_stock_basic.py --to-mysql

3）仅拉取上证 / 深证
    python scripts/fetch_tushare_stock_basic.py --exchange SSE
    python scripts/fetch_tushare_stock_basic.py --exchange SZSE
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
from loguru import logger


DEFAULT_TUSHARE_TOKEN = "5049652140394706635"
DEFAULT_HTTP_URL = "http://stk_mins.xiximiao.com/dataapi"


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _parse_args() -> argparse.Namespace:
    """解析命令行参数"""

    parser = argparse.ArgumentParser(description="拉取 Tushare stock_basic 并生成 CSV/可选入库")
    parser.add_argument("--token", type=str, default=None, help="Tushare Token（可选；不传则使用脚本内置默认 token）")
    parser.add_argument("--http-url", type=str, default=DEFAULT_HTTP_URL, help="Tushare DataApi http_url（默认分钟权限端点）")
    parser.add_argument(
        "--exchange",
        type=str,
        default="SSE,SZSE",
        help="交易所列表（逗号分隔），可选 SSE,SZSE；默认同时拉取上证/深证",
    )
    parser.add_argument("--list-status", type=str, default="L", help="上市状态：L=上市 D=退市 P=暂停上市；默认 L")
    parser.add_argument(
        "--out-csv",
        type=str,
        default=".stock_data/metadata/stock_basic.csv",
        help="输出 CSV 路径（默认 .stock_data/metadata/stock_basic.csv）",
    )
    parser.add_argument("--to-mysql", action="store_true", help="生成 CSV 后直接 upsert 写入 MySQL（等价于再跑 stock_basic_import.py）")
    return parser.parse_args()


def _build_pro(token: str, http_url: str):
    """按照 scripts/set_token.py 的方式构建 pro（自定义端点）"""

    import tushare as ts

    pro = ts.pro_api(token="不用管这里")  # 不留空即可
    pro._DataApi__token = token
    pro._DataApi__http_url = http_url
    return pro


def _parse_exchanges(v: str) -> List[str]:
    """解析交易所参数"""

    items = [x.strip().upper() for x in (v or "").split(",") if x.strip()]
    allowed = {"SSE", "SZSE"}
    out = [x for x in items if x in allowed]
    if not out:
        raise ValueError("exchange 不能为空，且仅支持 SSE,SZSE")
    return out


def _fetch_stock_basic(pro, exchanges: List[str], list_status: str) -> pd.DataFrame:
    """拉取 stock_basic 并合并为单表"""

    fields = "ts_code,name,exchange,list_status,list_date,delist_date"
    dfs = []
    for ex in exchanges:
        df = pro.stock_basic(exchange=ex, list_status=list_status, fields=fields)
        if df is None or len(df) == 0:
            logger.warning(f"stock_basic 返回空数据：exchange={ex} list_status={list_status}")
            continue
        dfs.append(df)
    if not dfs:
        return pd.DataFrame(columns=["ts_code", "name", "exchange", "list_status", "list_date", "delist_date"])
    return pd.concat(dfs, ignore_index=True)


def _to_import_df(df: pd.DataFrame) -> pd.DataFrame:
    """转换为 stock_basic_import.py 约定的 CSV 列"""

    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["symbol", "name", "market", "list_date", "delist_date"])

    out = df.copy()
    out["symbol"] = out["ts_code"].astype(str).str.upper()
    out["name"] = out.get("name", "").fillna("").astype(str)

    out["market"] = ""
    out.loc[out["symbol"].str.endswith(".SH", na=False), "market"] = "SH"
    out.loc[out["symbol"].str.endswith(".SZ", na=False), "market"] = "SZ"

    out["list_date"] = out.get("list_date", "").fillna("").astype(str)
    out["delist_date"] = out.get("delist_date", "").fillna("").astype(str)

    out = out[out["symbol"].str.endswith((".SH", ".SZ"), na=False)]
    out = out[["symbol", "name", "market", "list_date", "delist_date"]]
    out = out.drop_duplicates(subset=["symbol"], keep="last").sort_values("symbol").reset_index(drop=True)
    return out


def _write_csv(df: pd.DataFrame, out_csv: Path) -> None:
    """写出 CSV 文件"""

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8")
    logger.info(f"已生成 CSV：{out_csv} rows={len(df)}")


def _upsert_mysql(rows: List[dict]) -> int:
    """批量写入 MySQL（upsert）"""

    from backend.src.storage.mysql_db import get_session_maker
    from backend.src.storage.stock_basic_repo import StockBasicRepo

    SessionMaker = get_session_maker()
    session = SessionMaker()
    try:
        repo = StockBasicRepo(session)
        n = repo.bulk_upsert(rows)
        session.commit()
        return int(n)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> int:
    """脚本入口"""

    _bootstrap()
    args = _parse_args()
    token = (args.token or "").strip() or DEFAULT_TUSHARE_TOKEN
    exchanges = _parse_exchanges(args.exchange)
    pro = _build_pro(token=token, http_url=str(args.http_url).strip())

    raw = _fetch_stock_basic(pro, exchanges=exchanges, list_status=str(args.list_status).strip().upper())
    out_df = _to_import_df(raw)
    out_csv = Path(args.out_csv)
    _write_csv(out_df, out_csv=out_csv)

    if args.to_mysql:
        rows = out_df.to_dict(orient="records")
        n = _upsert_mysql(rows)
        logger.info(f"已写入 MySQL：rows={n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

