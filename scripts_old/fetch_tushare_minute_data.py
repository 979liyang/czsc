#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tushare 批量采集上证/深证股票分钟数据并保存到本地 parquet。

存储结构（与现有脚本一致）：
.stock_data/raw/minute_by_stock/stock_code={ts_code}/year={year}/{ts_code}_{year}-{month:02d}.parquet

使用示例：
  # 采集全市场（上证/深证）1分钟数据（默认增量）
  python scripts/fetch_tushare_minute_data.py --freq 1min

  # 只跑前 10 只做验证
  python scripts/fetch_tushare_minute_data.py --freq 1min --limit 10

  # 指定 token
  python scripts/fetch_tushare_minute_data.py --token YOUR_TOKEN --freq 1min

  # 仅采集指定股票
  python scripts/fetch_tushare_minute_data.py --stocks 600078.SH,000001.SZ --freq 1min

  # 指定日期范围（YYYYMMDD）
  python scripts/fetch_tushare_minute_data.py --freq 1min --start-date 20240101 --end-date 20240201
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger


project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_stocks(stocks: Optional[str]) -> Optional[List[str]]:
    """解析股票列表参数"""
    if not stocks:
        return None
    items = [x.strip().upper() for x in stocks.split(",") if x.strip()]
    return items or None


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


def _calc_fetch_range(
    stock_code: str,
    freq: str,
    incremental: bool,
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, str]:
    """计算采集日期范围（YYYYMMDD）"""
    period = int(freq.replace("min", ""))
    edt = end_date or datetime.now().strftime("%Y%m%d")
    if not incremental or start_date:
        return start_date or edt, edt
    last_ts = _get_latest_timestamp(stock_code, period=period)
    if last_ts is None:
        return edt, edt
    sdt = pd.to_datetime(last_ts).strftime("%Y%m%d")
    return sdt, edt


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
        ok = storage.save_minute_data_by_stock(g2, stock_code=stock_code, year=int(y), month=int(m), incremental=incremental)
        ok_any = ok_any or ok
    return ok_any


def collect_one_stock(client, ts_code: str, freq: str, incremental: bool, sdt: Optional[str], edt: Optional[str]) -> bool:
    """采集单只股票分钟数据并保存"""
    from backend.data.tushare_client import _normalize_freq

    f = _normalize_freq(freq)
    stock_code = ts_code.upper()
    sdt2, edt2 = _calc_fetch_range(stock_code=stock_code, freq=f, incremental=incremental, start_date=sdt, end_date=edt)
    logger.info(f"采集 {stock_code} 分钟数据: freq={f}, start={sdt2}, end={edt2}, incremental={incremental}")
    df = client.fetch_minute_bars(ts_code=stock_code, freq=f, start_date=sdt2, end_date=edt2)
    if df is None or len(df) == 0:
        logger.warning(f"{stock_code} 返回空数据")
        return True
    ok = _save_minute_df(df, stock_code=stock_code, incremental=incremental)
    logger.info(f"{stock_code} 保存结果: {ok}, 行数: {len(df)}")
    return ok


def build_stock_list(token: Optional[str], stocks_arg: Optional[str], limit: Optional[int]) -> List[str]:
    """构建待处理股票列表"""
    from backend.data.tushare_client import TushareClient

    stocks = _parse_stocks(stocks_arg)
    if stocks is None:
        client = TushareClient(token=token)
        stocks = client.list_a_stocks_sh_sz(list_status="L")
    if limit:
        stocks = stocks[:limit]
    return stocks


def run_batch(client, stocks: List[str], args) -> None:
    """批量执行采集"""
    ok_cnt = 0
    for i, ts_code in enumerate(stocks, 1):
        try:
            ok = collect_one_stock(client, ts_code, args.freq, args.incremental, args.start_date, args.end_date)
            ok_cnt += 1 if ok else 0
        except Exception as e:
            logger.error(f"处理失败: {ts_code} - {e}")
        if args.sleep and args.sleep > 0:
            import time

            time.sleep(args.sleep)
        if i % 50 == 0:
            logger.info(f"进度: {i}/{len(stocks)}，成功: {ok_cnt}")
    logger.info(f"完成：成功 {ok_cnt}/{len(stocks)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Tushare 分钟数据批量采集")
    parser.add_argument("--token", type=str, default=None, help="Tushare Token（也可用环境变量 TUSHARE_TOKEN）")
    parser.add_argument("--freq", type=str, default="1min", choices=["1min", "5min", "15min", "30min", "60min"], help="分钟周期")
    parser.add_argument("--start-date", type=str, default=None, help="开始日期 YYYYMMDD（可选）")
    parser.add_argument("--end-date", type=str, default=None, help="结束日期 YYYYMMDD（可选）")
    parser.add_argument("--stocks", type=str, default=None, help="指定股票列表（逗号分隔），如 600078.SH,000001.SZ")
    parser.add_argument("--limit", type=int, default=None, help="最多处理多少只股票（用于测试）")
    parser.add_argument("--sleep", type=float, default=0.0, help="每只股票处理间隔（秒）")
    parser.add_argument("--incremental", action="store_true", default=True, help="增量模式（默认启用）")
    parser.add_argument("--no-incremental", dest="incremental", action="store_false", help="覆盖模式（不增量）")

    args = parser.parse_args()
    from backend.data.tushare_client import TushareClient

    stocks = build_stock_list(token=args.token, stocks_arg=args.stocks, limit=args.limit)
    logger.info(f"待处理股票数量: {len(stocks)}")
    client = TushareClient(token=args.token)
    run_batch(client, stocks, args)


if __name__ == "__main__":
    main()

