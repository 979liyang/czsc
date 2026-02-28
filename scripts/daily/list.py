#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拉取上证/深证股票基本信息（stock_basic）及可选每日指标（daily_basic），全量字段保存到 CSV 与 MySQL。

可获取并保存的数据：

1）stock_basic（基础信息，必拉）
   symbol,name,market,list_date,delist_date, area,industry, fullname,enname,cnspell,
   exchange,curr_type,list_status, is_hs, act_name,act_ent_type

2）daily_basic（每日指标，--with-daily-basic 时拉取）
   接口文档：https://tushare.pro/document/2?doc_id=32
   拉取日期由 pro.trade_cal 得到的「最后交易日」决定（与 scripts/info/trade_cal.py 一致）。
   输出中增加 daily_basic_date 列，表示本次 daily_basic 对应的交易日（YYYYMMDD）。
   使用 --http-url（默认 DEFAULT_HTTP_URL）请求。

用法示例：
1）全量拉取（基础信息 + 最近交易日指标），写 CSV 与 MySQL
    python scripts/daily/list.py --with-daily-basic --to-mysql

2）只写 CSV（推荐先检查文件）
    python scripts/daily/list.py --out-csv .stock_data/metadata/stock_basic.csv

3）仅拉取上证 / 深证
    python scripts/daily/list.py --exchange SSE --exchange SZSE
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd
from loguru import logger


DEFAULT_TUSHARE_TOKEN = "5049750782419706635"
DEFAULT_HTTP_URL = "http://stk_mins.xiximiao.com/dataapi"

# stock_basic 接口全部可请求字段（部分端点可能不返回全部，缺失则填空）
STOCK_BASIC_FIELDS = (
    "ts_code,name,symbol,area,industry,fullname,enname,cnspell,"
    "market,exchange,curr_type,list_status,list_date,delist_date,"
    "is_hs,act_name,act_ent_type"
)
# daily_basic 每日指标全字段，与 https://tushare.pro/document/2?doc_id=32 输出一致
DAILY_BASIC_FIELDS = (
    "ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,"
    "pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,"
    "total_share,float_share,free_share,total_mv,circ_mv"
)


def _bootstrap() -> None:
    """将项目根目录加入 sys.path，便于从 scripts/ 直接运行"""

    root = Path(__file__).resolve().parents[2]
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
    parser.add_argument(
        "--with-daily-basic",
        action="store_true",
        default=True,
        help="同时拉取最近交易日每日指标（daily_basic）全字段，默认开启",
    )
    parser.add_argument("--no-daily-basic", dest="with_daily_basic", action="store_false", help="不拉取 daily_basic，仅 stock_basic")
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
    """拉取 stock_basic 全字段并合并为单表"""

    dfs = []
    for ex in exchanges:
        try:
            df = pro.stock_basic(exchange=ex, list_status=list_status, fields=STOCK_BASIC_FIELDS)
        except Exception as e:
            # 部分自定义端点可能不支持全字段，回退为最小字段集
            logger.warning(f"stock_basic 全字段请求失败，尝试最小字段：{e}")
            df = pro.stock_basic(
                exchange=ex, list_status=list_status,
                fields="ts_code,name,exchange,list_status,list_date,delist_date,area,industry",
            )
        if df is None or len(df) == 0:
            logger.warning(f"stock_basic 返回空数据：exchange={ex} list_status={list_status}")
            continue
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def _get_latest_trade_date(pro, exchange: str = "SSE") -> Optional[str]:
    """
    通过 pro.trade_cal 获取最后交易日（is_open=1 的最大 cal_date），与 trade_cal.py 逻辑一致。
    """
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


def _latest_trade_date_yyyymmdd() -> str:
    """最近交易日（昨日），仅当 trade_cal 不可用时的回退"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def _fetch_daily_basic(pro, trade_date: str) -> pd.DataFrame:
    """
    拉取指定交易日的每日指标（daily_basic），参见 https://tushare.pro/document/2?doc_id=32 。
    使用当前 pro 的 http_url（默认 DEFAULT_HTTP_URL），返回全字段。
    """
    try:
        df = pro.daily_basic(trade_date=trade_date, fields=DAILY_BASIC_FIELDS)
        if df is not None and len(df) > 0:
            df["ts_code"] = df["ts_code"].astype(str).str.upper()
            return df
    except Exception as e:
        logger.warning(f"daily_basic 拉取失败（trade_date={trade_date}）：{e}")
    return pd.DataFrame()


def _str_col(s: pd.Series) -> pd.Series:
    """转为字符串列，NaN 为空字符串"""
    return s.fillna("").astype(str)


def _to_import_df(
    df: pd.DataFrame,
    daily_basic: Optional[pd.DataFrame] = None,
    daily_basic_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    合并 stock_basic 与 daily_basic，输出全量列供 CSV/MySQL 使用。
    daily_basic_date：本次 daily_basic 对应的交易日（YYYYMMDD），写入列 daily_basic_date。
    列顺序：必选 5 列 -> stock_basic 扩展 -> daily_basic_date -> daily_basic 扩展。
    """

    # 必选 + stock_basic 全量扩展列（与 Tushare 输出一致）
    base_cols = ["symbol", "name", "market", "list_date", "delist_date"]
    sb_ext = ["area", "industry", "fullname", "enname", "cnspell", "exchange", "curr_type", "list_status", "is_hs", "act_name", "act_ent_type"]
    db_cols = [
        "daily_basic_date",
        "trade_date", "close", "turnover_rate", "turnover_rate_f", "volume_ratio",
        "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm",
        "total_share", "float_share", "free_share", "total_mv", "circ_mv",
    ]

    if df is None or len(df) == 0:
        all_cols = base_cols + sb_ext + db_cols
        return pd.DataFrame(columns=all_cols)

    out = df.copy()
    out["symbol"] = out["ts_code"].astype(str).str.upper()
    out = out[out["symbol"].str.endswith((".SH", ".SZ"), na=False)]

    out["name"] = _str_col(out.get("name", pd.Series(dtype=object)))
    out["market"] = ""
    out.loc[out["symbol"].str.endswith(".SH", na=False), "market"] = "SH"
    out.loc[out["symbol"].str.endswith(".SZ", na=False), "market"] = "SZ"
    out["list_date"] = _str_col(out.get("list_date", pd.Series(dtype=object)))
    out["delist_date"] = _str_col(out.get("delist_date", pd.Series(dtype=object)))
    for c in sb_ext:
        out[c] = _str_col(out.get(c, pd.Series(dtype=object)))

    # daily_basic_date：本次拉取 daily_basic 使用的交易日（全表同一值）
    out["daily_basic_date"] = (daily_basic_date or "").strip() if daily_basic_date else ""

    if daily_basic is not None and len(daily_basic) > 0:
        out = out.merge(daily_basic, on="ts_code", how="left")
        for c in db_cols:
            if c == "daily_basic_date":
                continue
            if c in out.columns:
                out[c] = out[c].apply(lambda x: "" if pd.isna(x) else str(x))
            else:
                out[c] = ""
    else:
        for c in db_cols:
            if c == "daily_basic_date":
                continue
            out[c] = ""

    out = out.drop_duplicates(subset=["symbol"], keep="last").sort_values("symbol").reset_index(drop=True)
    final_cols = base_cols + sb_ext + db_cols
    out = out[[c for c in final_cols if c in out.columns]]
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
    daily_basic: Optional[pd.DataFrame] = None
    trade_date: Optional[str] = None
    if args.with_daily_basic:
        trade_date = _get_latest_trade_date(pro, exchange="SSE")
        if not trade_date:
            trade_date = _latest_trade_date_yyyymmdd()
            logger.warning(f"trade_cal 未返回最后交易日，回退为昨日: {trade_date}")
        else:
            logger.info(f"最后交易日（trade_cal）: {trade_date}")
        logger.info(f"拉取每日指标：trade_date={trade_date}")
        daily_basic = _fetch_daily_basic(pro, trade_date=trade_date)
        if len(daily_basic) > 0:
            logger.info(f"daily_basic 获取 {len(daily_basic)} 条")
        else:
            logger.warning("daily_basic 未获取到数据（可能当前端点不支持该接口或积分不足，CSV 中相关列为空）")
    out_df = _to_import_df(raw, daily_basic=daily_basic, daily_basic_date=trade_date)
    out_csv = Path(args.out_csv)
    _write_csv(out_df, out_csv=out_csv)

    if args.to_mysql:
        rows = out_df.to_dict(orient="records")
        n = _upsert_mysql(rows)
        logger.info(f"已写入 MySQL：rows={n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

