# -*- coding: utf-8 -*-
"""
本地 CZSC 分析服务

从本地 `.stock_data/raw/minute_by_stock` 读取 1分钟 数据，按需重采样到 1/5/15/30/60 分钟（可选日线），
并输出前端可用的 CZSC 分析结果（bars + fxs + bis + stats）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from czsc.analyze import CZSC
from czsc.objects import Freq, RawBar
from czsc.utils import BarGenerator
from czsc.utils.ta import MACD, SMA

from ..models.serializers import serialize_raw_bars, serialize_fxs, serialize_bis


def _project_root() -> Path:
    """获取项目根目录路径"""
    return Path(__file__).parent.parent.parent.parent


def _default_stock_data_root() -> Path:
    """获取 `.stock_data` 根目录"""
    return _project_root() / ".stock_data"


def _normalize_symbol(symbol: str) -> str:
    """标准化股票代码格式（仅用于 demo：600078 -> 600078.SH）"""
    s = str(symbol).strip().upper()
    # 兼容路由形式：SH600078 / SZ000001
    if s.startswith("SH") and len(s) == 8 and s[2:].isdigit():
        return f"{s[2:]}.SH"
    if s.startswith("SZ") and len(s) == 8 and s[2:].isdigit():
        return f"{s[2:]}.SZ"
    if "." in s:
        return s
    if s.startswith("6"):
        return f"{s}.SH"
    return f"{s}.SZ"


def _parse_dt(x: Optional[str], fallback: str) -> pd.Timestamp:
    """解析日期/时间字符串"""
    v = x if x else fallback
    return pd.to_datetime(v)


def _ym_range(sdt: pd.Timestamp, edt: pd.Timestamp) -> List[Tuple[int, int]]:
    """生成 sdt~edt 覆盖的 (year, month) 列表"""
    cur = pd.Timestamp(year=int(sdt.year), month=int(sdt.month), day=1)
    end = pd.Timestamp(year=int(edt.year), month=int(edt.month), day=1)
    out: List[Tuple[int, int]] = []
    while cur <= end:
        out.append((int(cur.year), int(cur.month)))
        cur = (cur + pd.offsets.MonthBegin(1)).normalize()
    return out


def _minute_files(base_path: Path, symbol: str, y: int, m: int) -> Path:
    """按约定生成月度 parquet 文件路径"""
    p = base_path / "raw" / "minute_by_stock" / f"stock_code={symbol}" / f"year={y}"
    return p / f"{symbol}_{y}-{m:02d}.parquet"


def _normalize_freqs(freqs: Optional[str]) -> str:
    """标准化 freqs 参数，返回排序去重后的字符串，如 '1,5,15,30,60'"""
    if not freqs:
        return "1,5,15,30,60"
    parts = [p.strip() for p in str(freqs).split(",") if p.strip()]
    mins: List[int] = []
    for p in parts:
        if not p.isdigit():
            continue
        mins.append(int(p))
    allow = {1, 5, 15, 30, 60}
    mins = sorted({m for m in mins if m in allow})
    return ",".join(str(m) for m in mins) if mins else "1,5,15,30,60"


def _targets_from(freqs: str, include_daily: bool) -> List[Freq]:
    """由 freqs 字符串生成目标周期列表"""
    mins = [int(x) for x in _normalize_freqs(freqs).split(",")]
    out = [Freq(f"{m}分钟") for m in mins]
    if include_daily:
        out.append(Freq("日线"))
    return out


def _load_minute_df_with_meta(
    base_path: Path, symbol: str, sdt: pd.Timestamp, edt: pd.Timestamp
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """加载分钟数据（按月 parquet 聚合），返回 (df, meta)"""
    dfs: List[pd.DataFrame] = []
    parquet_count = 0
    for y, m in _ym_range(sdt, edt):
        fp = _minute_files(base_path, symbol, y, m)
        if not fp.exists():
            continue
        df = pd.read_parquet(fp)
        if df is not None and len(df) > 0:
            dfs.append(df)
            parquet_count += 1
    if not dfs:
        return pd.DataFrame(), {"parquet_count": 0, "rows_before_filter": 0, "rows_after_filter": 0, "period_filtered": False}
    df_all = pd.concat(dfs, ignore_index=True)
    rows_before = int(len(df_all))
    df_std, rows_after, period_filtered = _standardize_minute_df(df_all, symbol, sdt, edt)
    meta = {"parquet_count": parquet_count, "rows_before_filter": rows_before, "rows_after_filter": rows_after, "period_filtered": period_filtered}
    return df_std, meta


def _standardize_minute_df(
    df: pd.DataFrame, symbol: str, sdt: pd.Timestamp, edt: pd.Timestamp
) -> Tuple[pd.DataFrame, int, bool]:
    """标准化分钟数据到 K 线序列化需要的列，并返回过滤后行数与是否按 period 过滤"""
    if df is None or len(df) == 0:
        return pd.DataFrame(), 0, False
    x = df.copy()
    if "timestamp" not in x.columns:
        raise ValueError("分钟数据缺少 timestamp 列")
    x["dt"] = pd.to_datetime(x["timestamp"])
    period_filtered = False
    if "period" in x.columns:
        x = x[x["period"].astype(int) == 1].copy()
        period_filtered = True
    x = x[(x["dt"] >= sdt) & (x["dt"] <= edt)].copy()
    if x.empty:
        return pd.DataFrame(), 0, period_filtered
    x["symbol"] = symbol
    x["vol"] = x["volume"] if "volume" in x.columns else x.get("vol", 0)
    x["amount"] = x["amount"] if "amount" in x.columns else 0
    cols = ["symbol", "dt", "open", "close", "high", "low", "vol", "amount"]
    out = x[cols].sort_values("dt").reset_index(drop=True)
    return out, int(len(out)), period_filtered


def _normalize_base_freq(base_freq: Optional[str]) -> str:
    """标准化 base_freq 参数"""
    v = str(base_freq or "1分钟").strip()
    allow = {"1分钟", "5分钟", "15分钟", "30分钟", "60分钟"}
    return v if v in allow else "1分钟"


def _freq_minutes(freq_value: str) -> int:
    """将周期字符串映射到分钟数，用于比较大小；日线视作 1440 分钟"""
    if freq_value == "日线":
        return 1440
    if freq_value.endswith("分钟"):
        return int(freq_value.replace("分钟", ""))
    return 10**9


def _requested_freq_values(freqs: str, include_daily: bool) -> List[str]:
    """将请求参数转换为周期字符串列表，如 ['1分钟','5分钟',...]"""
    targets = _targets_from(freqs, include_daily)
    return [t.value for t in targets]


def _validate_freqs(base_freq: str, requested: List[str]) -> Tuple[List[str], List[str]]:
    """校验目标周期与 base_freq 的相对关系，返回可用周期与警告列表"""
    out: List[str] = []
    warnings: List[str] = []
    base_m = _freq_minutes(base_freq)
    for f in requested:
        if _freq_minutes(f) < base_m:
            warnings.append(f"目标周期 {f} 小于 base_freq {base_freq}，已跳过")
            continue
        out.append(f)
    return out, warnings


def _df_to_raw_bars(df: pd.DataFrame, freq_value: str) -> List[RawBar]:
    """将标准化 DataFrame 转为 RawBar 列表"""
    if df is None or len(df) == 0:
        return []
    freq = Freq(freq_value)
    bars: List[RawBar] = []
    for i, row in enumerate(df.itertuples(index=False), start=1):
        bars.append(
            RawBar(
                symbol=getattr(row, "symbol"),
                id=i,
                dt=getattr(row, "dt").to_pydatetime(),
                freq=freq,
                open=float(getattr(row, "open")),
                close=float(getattr(row, "close")),
                high=float(getattr(row, "high")),
                low=float(getattr(row, "low")),
                vol=float(getattr(row, "vol")),
                amount=float(getattr(row, "amount")),
            )
        )
    return bars


def _build_base_bars(minute_bars: List[RawBar], base_freq: str) -> List[RawBar]:
    """从 1分钟 bars 合成 base_freq bars（若 base_freq=1分钟，则直接返回）"""
    if base_freq == "1分钟":
        return minute_bars
    bg = BarGenerator(base_freq="1分钟", freqs=[base_freq])
    for bar in minute_bars:
        bg.update(bar)
    return bg.bars.get(base_freq, [])


def _build_multi_freq_bars(base_bars: List[RawBar], base_freq: str, targets: List[str]) -> Dict[str, List[RawBar]]:
    """用 BarGenerator 从 base_bars 合成 targets 周期 bars（targets 包含 base 也没问题）"""
    freqs = [f for f in targets if f != base_freq]
    bg = BarGenerator(base_freq=base_freq, freqs=freqs)
    for bar in base_bars:
        bg.update(bar)
    out: Dict[str, List[RawBar]] = {base_freq: bg.bars.get(base_freq, []) or base_bars}
    for f in freqs:
        out[f] = bg.bars.get(f, [])
    return out


def _build_meta(
    base_path: Path,
    df_minute: pd.DataFrame,
    df_meta: Dict[str, Any],
    base_freq: str,
    requested: List[str],
    targets: List[str],
    warnings: List[str],
) -> Dict[str, Any]:
    """构建元数据字典"""
    return {
        "data_root": str(base_path),
        "parquet_count": int(df_meta.get("parquet_count", 0)),
        "rows_before_filter": int(df_meta.get("rows_before_filter", 0)),
        "rows_after_filter": int(df_meta.get("rows_after_filter", 0)),
        "period_filtered": bool(df_meta.get("period_filtered", False)),
        "dt_min": str(df_minute["dt"].min()) if not df_minute.empty else None,
        "dt_max": str(df_minute["dt"].max()) if not df_minute.empty else None,
        "base_freq": base_freq,
        "requested_freqs": requested,
        "target_freqs": targets,
        "generated_bar_counts": {},
        "warnings": warnings,
    }


def _empty_result(symbol: str, sdt: str, edt: str, base_freq: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """统一返回空结果结构"""
    return {"symbol": symbol, "sdt": sdt, "edt": edt, "base_freq": base_freq, "items": {}, "meta": meta}


def _analyze_items(
    symbol: str, sdt: str, edt: str, base_freq: str, targets: List[str], df_minute: pd.DataFrame, meta: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, int], Dict[str, Any]]:
    """用 BarGenerator 生成多周期 bars 并分析，返回 (items, counts, meta)"""
    minute_bars = _df_to_raw_bars(df_minute, "1分钟")
    base_bars = _build_base_bars(minute_bars, base_freq)
    if not base_bars:
        msg = f"base_freq={base_freq} 合成后 bars 为空"
        meta["warnings"].append(msg)
        logger.warning(f"本地CZSC {symbol} {msg} | minute_bars={len(minute_bars)} | {sdt} ~ {edt}")
        return {}, {}, meta
    bars_map = _build_multi_freq_bars(base_bars, base_freq, targets)
    items: Dict[str, Any] = {}
    counts: Dict[str, int] = {}
    for f, bars in bars_map.items():
        counts[f] = int(len(bars))
        if len(bars) == 0:
            logger.warning(f"本地CZSC合成后为空: {symbol} | base={base_freq} | target={f} | {sdt} ~ {edt}")
        else:
            logger.info(f"本地CZSC合成完成: {symbol} | base={base_freq} | target={f} | bars={len(bars)}")
        items[f] = {"freq": f, "indicators": _calc_indicators(bars), **_analyze_one(bars)}
    return items, counts, meta


def _analyze_one(bars: List[RawBar]) -> Dict[str, Any]:
    """对单一周期 bars 做 CZSC 分析并序列化"""
    if not bars:
        return {"bars": [], "bis": [], "fxs": [], "stats": {"bars_raw_count": 0}}
    cz = CZSC(bars)
    stats = {
        "bars_raw_count": len(cz.bars_raw),
        "bars_ubi_count": len(cz.bars_ubi),
        "fx_count": len(cz.fx_list),
        "finished_bi_count": len(cz.finished_bis),
        "bi_count": len(cz.bi_list),
        "ubi_count": 1 if cz.ubi else 0,
        "last_bi_extend": bool(cz.last_bi_extend),
        "last_bi_direction": cz.finished_bis[-1].direction.value if cz.finished_bis else None,
        "last_bi_power": float(cz.finished_bis[-1].power) if cz.finished_bis else None,
    }
    return {"bars": serialize_raw_bars(bars), "bis": serialize_bis(cz.bi_list), "fxs": serialize_fxs(cz.fx_list), "stats": stats}


def _calc_vol_series(bars: List[RawBar]) -> List[List[float]]:
    """计算成交量序列：[[ts_ms, vol], ...]"""
    return [[float(int(b.dt.timestamp() * 1000)), float(b.vol)] for b in bars]


def _calc_sma_series(bars: List[RawBar], periods: List[int]) -> Dict[str, List[List[float]]]:
    """计算均线序列：{'MA5': [[ts, v], ...], ...}"""
    if not bars:
        return {}
    close = np.array([b.close for b in bars], dtype=np.double)
    ts = [float(int(b.dt.timestamp() * 1000)) for b in bars]
    out: Dict[str, List[List[float]]] = {}
    for p in periods:
        ma = SMA(close, timeperiod=p)
        out[f"MA{p}"] = [[ts[i], float(ma[i])] for i in range(len(ts))]
    return out


def _calc_macd_series(bars: List[RawBar]) -> List[List[float]]:
    """计算 MACD 序列：[[ts_ms, diff, dea, macd], ...]"""
    if not bars:
        return []
    close = np.array([b.close for b in bars], dtype=np.double)
    ts = [float(int(b.dt.timestamp() * 1000)) for b in bars]
    diff, dea, macd = MACD(close)
    return [[ts[i], float(diff[i]), float(dea[i]), float(macd[i])] for i in range(len(ts))]


def _calc_indicators(bars: List[RawBar]) -> Dict[str, Any]:
    """计算 to_echarts 默认指标（vol / sma / macd）"""
    if not bars:
        return {}
    return {"vol": _calc_vol_series(bars), "sma": _calc_sma_series(bars, [5, 13, 21]), "macd": _calc_macd_series(bars)}


@dataclass
class LocalCzscService:
    """本地 CZSC 多周期分析服务"""

    base_path: Optional[Path] = None

    def __post_init__(self):
        """初始化默认路径"""
        self.base_path = Path(self.base_path) if self.base_path else _default_stock_data_root()

    def analyze_multi(
        self,
        symbol: str,
        sdt: Optional[str],
        edt: Optional[str],
        freqs: Optional[str] = None,
        include_daily: bool = False,
        base_freq: Optional[str] = None,
    ) -> Dict[str, Any]:
        """对指定分钟周期（可选日线）进行分析并返回"""
        sym = _normalize_symbol(symbol)
        sdt_dt = _parse_dt(sdt, "20180101")
        edt_dt = _parse_dt(edt, datetime.now().strftime("%Y%m%d"))
        if sdt_dt > edt_dt:
            sdt_dt, edt_dt = edt_dt, sdt_dt
        freqs_norm = _normalize_freqs(freqs)
        base_freq_norm = _normalize_base_freq(base_freq)
        return _analyze_cached(
            str(self.base_path),
            sym,
            sdt_dt.strftime("%Y%m%d"),
            edt_dt.strftime("%Y%m%d"),
            freqs_norm,
            bool(include_daily),
            base_freq_norm,
        )


@lru_cache(maxsize=64)
def _analyze_cached(
    base_path: str, symbol: str, sdt: str, edt: str, freqs: str, include_daily: bool, base_freq: str
) -> Dict[str, Any]:
    """带缓存的分析入口（避免重复计算）"""
    bp = Path(base_path)
    sdt_dt = pd.to_datetime(sdt)
    edt_dt = pd.to_datetime(edt)
    requested = _requested_freq_values(freqs, include_daily)
    targets, warnings = _validate_freqs(base_freq, requested)
    logger.info(
        f"本地CZSC分析(BarGenerator): {symbol} base={base_freq} -> {','.join(targets)} | {sdt} ~ {edt}"
    )
    df_minute, df_meta = _load_minute_df_with_meta(bp, symbol, sdt_dt, edt_dt)
    meta = _build_meta(bp, df_minute, df_meta, base_freq, requested, targets, warnings)
    if df_minute.empty:
        logger.warning(
            f"本地CZSC分析无数据: {symbol} | base={base_freq} | parquet={meta['parquet_count']} | {sdt} ~ {edt} | freqs={freqs} | include_daily={include_daily}"
        )
        return _empty_result(symbol, sdt, edt, base_freq, meta)

    items, counts, meta = _analyze_items(symbol, sdt, edt, base_freq, targets, df_minute, meta)
    meta["generated_bar_counts"] = counts
    return {"symbol": symbol, "sdt": sdt, "edt": edt, "base_freq": base_freq, "items": items, "meta": meta}

