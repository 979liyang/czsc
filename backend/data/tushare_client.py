# -*- coding: utf-8 -*-
"""
Tushare 数据客户端（分钟数据）

说明：
- 仅封装分钟级别数据的获取与标准化
- 输出 DataFrame 列对齐 RawDataStorage 的分钟数据存储要求：
  timestamp, stock_code, open, high, low, close, volume, amount, period
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd
from loguru import logger


def _get_token(token: Optional[str]) -> str:
    """获取 Tushare Token（优先参数，其次环境变量）"""
    import os

    t = (token or os.getenv("TUSHARE_TOKEN") or "").strip()
    if not t:
        raise ValueError("未找到 Tushare Token；请传入 --token 或设置环境变量 TUSHARE_TOKEN")
    return t


def _normalize_freq(freq: str) -> str:
    """标准化分钟频率字符串"""
    f = str(freq).strip().lower()
    if f.isdigit():
        f = f"{f}min"
    if f not in {"1min", "5min", "15min", "30min", "60min"}:
        raise ValueError(f"不支持的分钟周期: {freq}，可选：1min/5min/15min/30min/60min")
    return f


def _to_period_minutes(freq: str) -> int:
    """将频率字符串转换成分钟数"""
    return int(freq.replace("min", ""))


def _clean_ts_code(ts_code: str) -> str:
    """清理并校验 ts_code（例如 600078.SH）"""
    s = str(ts_code).strip().upper()
    if "." not in s:
        raise ValueError(f"ts_code 格式错误: {ts_code}，应为 600078.SH / 000001.SZ")
    if not (s.endswith(".SH") or s.endswith(".SZ")):
        raise ValueError(f"仅支持上证/深证股票: {ts_code}")
    return s


def _standardize_minute_df(df: pd.DataFrame, ts_code: str, freq: str) -> Optional[pd.DataFrame]:
    """将 tushare 返回的分钟K线 df 标准化为存储格式"""
    if df is None or len(df) == 0:
        return None

    dt_col = "trade_time" if "trade_time" in df.columns else "datetime"
    if dt_col not in df.columns:
        raise ValueError(f"分钟数据缺少时间列 trade_time/datetime，实际列：{list(df.columns)}")

    out = df.copy()
    out["timestamp"] = pd.to_datetime(out[dt_col])
    out["stock_code"] = _clean_ts_code(ts_code)
    out["period"] = _to_period_minutes(freq)

    rename_map = {"vol": "volume"}
    for k, v in rename_map.items():
        if k in out.columns and v not in out.columns:
            out[v] = out[k]

    required = ["timestamp", "stock_code", "open", "high", "low", "close", "volume", "amount", "period"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError(f"分钟数据缺少必需列: {missing}；实际列：{list(out.columns)}")

    out = out[required].sort_values("timestamp").reset_index(drop=True)
    return out


@dataclass
class TushareClient:
    """Tushare 分钟数据客户端"""

    token: Optional[str] = None

    def __post_init__(self):
        """初始化 tushare client"""
        self.token = _get_token(self.token)
        try:
            import tushare as ts
        except Exception as e:
            raise ImportError("未安装 tushare，请先 pip install tushare") from e
        self._ts = ts
        self._ts.set_token(self.token)
        self._pro = self._ts.pro_api(self.token)
        logger.info("Tushare 客户端初始化完成")

    def list_a_stocks_sh_sz(self, list_status: str = "L") -> List[str]:
        """获取上证/深证 A 股股票列表（默认仅在市）"""
        df = self._pro.stock_basic(exchange="", list_status=list_status, fields="ts_code,exchange")
        if df is None or len(df) == 0:
            return []
        df = df[df["ts_code"].str.endswith((".SH", ".SZ"), na=False)]
        return sorted(df["ts_code"].dropna().unique().tolist())

    def fetch_minute_bars(
        self,
        ts_code: str,
        freq: str = "1min",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adj: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """获取分钟K线并标准化（返回 None 表示无数据）"""
        code = _clean_ts_code(ts_code)
        f = _normalize_freq(freq)
        sdt = start_date
        edt = end_date
        if sdt is None:
            sdt = datetime.now().strftime("%Y%m%d")
        if edt is None:
            edt = datetime.now().strftime("%Y%m%d")

        df = self._ts.pro_bar(ts_code=code, start_date=sdt, end_date=edt, freq=f, asset="E", adj=adj)
        return _standardize_minute_df(df, ts_code=code, freq=f)

