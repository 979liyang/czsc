# -*- coding: utf-8 -*-
"""
本地 CZSC 分析服务

从本地 `.stock_data/raw/minute_by_stock` 读取 1分钟 数据，按需重采样到 1/5/15/30/60 分钟（可选日线），
并输出前端可用的 CZSC 分析结果（bars + fxs + bis + stats）。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
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
    """
    标准化 freqs 参数，返回排序去重后的字符串，如 '1,5,15,30,60'
    支持单周期请求：如 "30"、"60"、"日线"
    """
    if not freqs:
        return "1,5,15,30,60"
    parts = [p.strip() for p in str(freqs).split(",") if p.strip()]
    mins: List[int] = []
    for p in parts:
        # 支持 "日线" 字符串（在 _targets_from 中处理）
        if p == "日线" or p == "日":
            continue
        if not p.isdigit():
            continue
        mins.append(int(p))
    allow = {1, 5, 15, 30, 60}
    mins = sorted({m for m in mins if m in allow})
    return ",".join(str(m) for m in mins) if mins else "1,5,15,30,60"


def _targets_from(freqs: str, include_daily: bool) -> List[Freq]:
    """
    由 freqs 字符串生成目标周期列表
    支持单周期请求：如 "30"、"60"、"日线"
    """
    # 检查是否包含 "日线" 字符串
    freqs_str = str(freqs) if freqs else ""
    has_daily_in_freqs = "日线" in freqs_str or "日" in freqs_str
    
    mins = [int(x) for x in _normalize_freqs(freqs).split(",") if x.strip().isdigit()]
    out = [Freq(f"{m}分钟") for m in mins]
    if include_daily or has_daily_in_freqs:
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


def _get_recent_months_range(edt: pd.Timestamp, recent_months: int = 3) -> pd.Timestamp:
    """
    计算最近N个月的开始日期
    
    时间范围控制说明：
    - 用于计算K线数据的过滤时间范围
    - 根据结束日期向前推 recent_months 个月，作为K线数据的开始日期
    - 例如：edt=2024-12-31, recent_months=3 -> 返回 2024-10-01（最近3个月的开始日期）
    
    :param edt: 结束日期
    :param recent_months: 最近几个月（默认3）
    :return: 开始日期（edt 向前推 recent_months 个月）
    """
    # 计算开始日期：从 edt 向前推 recent_months 个月
    # 使用 relativedelta 或手动计算月份
    try:
        from dateutil.relativedelta import relativedelta
        sdt = edt - relativedelta(months=recent_months)
    except ImportError:
        # 如果没有 dateutil，使用简单的月份计算
        year = edt.year
        month = edt.month
        # 向前推 recent_months 个月
        month -= recent_months
        while month <= 0:
            month += 12
            year -= 1
        sdt = pd.Timestamp(year=year, month=month, day=1)
    return sdt


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
    symbol: str,
    sdt: str,
    edt: str,
    base_freq: str,
    targets: List[str],
    df_minute: pd.DataFrame,
    meta: Dict[str, Any],
    bars_offset: int = 0,
    bars_limit: int = 0,
    fxs_offset: int = 0,
    fxs_limit: int = 0,
    bis_offset: int = 0,
    bis_limit: int = 0,
    recent_months: int = 0,
) -> Tuple[Dict[str, Any], Dict[str, int], Dict[str, Any]]:
    """
    用 BarGenerator 生成多周期 bars 并分析，返回 (items, counts, meta)
    
    时间范围控制说明：
    - 使用全量 bars 进行 CZSC 分析（确保分析准确性）
    - 如果 recent_months > 0，返回的 bars 只包含最近 recent_months 个月的数据
    - 分析数据（fxs、bis）基于全量数据计算，返回全量结果
    
    支持分页参数，只返回请求范围的数据
    """
    minute_bars = _df_to_raw_bars(df_minute, "1分钟")
    base_bars = _build_base_bars(minute_bars, base_freq)
    if not base_bars:
        msg = f"base_freq={base_freq} 合成后 bars 为空"
        meta["warnings"].append(msg)
        logger.warning(f"本地CZSC {symbol} {msg} | minute_bars={len(minute_bars)} | {sdt} ~ {edt}")
        return {}, {}, meta
    bars_map = _build_multi_freq_bars(base_bars, base_freq, targets)
    
    # 计算结束日期（用于时间范围过滤）
    edt_dt = pd.to_datetime(edt)
    
    items: Dict[str, Any] = {}
    counts: Dict[str, int] = {}
    for f, bars in bars_map.items():
        counts[f] = int(len(bars))
        if len(bars) == 0:
            logger.warning(f"本地CZSC合成后为空: {symbol} | base={base_freq} | target={f} | {sdt} ~ {edt}")
        else:
            logger.info(f"本地CZSC合成完成: {symbol} | base={base_freq} | target={f} | bars={len(bars)}")
        
        # 分析：使用全量 bars 进行分析，但返回的 bars 可能被过滤
        analyze_result = _analyze_one(
            bars,
            bars_offset,
            bars_limit,
            fxs_offset,
            fxs_limit,
            bis_offset,
            bis_limit,
            recent_months,
            edt_dt,
        )
        
        # 计算指标：基于全量 bars 计算指标（确保指标准确性）
        # 注意：指标应该基于全量数据计算，而不是过滤后的数据
        # 这样可以确保指标（如均线、MACD）的准确性
        indicators = _calc_indicators(bars)
        
        items[f] = {
            "freq": f,
            "indicators": indicators,
            **analyze_result,
        }
        
        # 记录时间范围信息
        if recent_months > 0 and bars:
            bars_start_dt = _get_recent_months_range(edt_dt, recent_months)
            logger.info(
                f"时间范围控制: {symbol} {f} 全量bars={len(bars)}条 "
                f"返回bars={len(analyze_result['bars'])}条 "
                f"分析数据(fxs={len(analyze_result['fxs'])}, bis={len(analyze_result['bis'])})基于全量数据 "
                f"K线时间范围={bars_start_dt.strftime('%Y-%m-%d')} ~ {edt_dt.strftime('%Y-%m-%d')}"
            )
    
    return items, counts, meta


def _analyze_one(
    bars: List[RawBar],
    bars_offset: int = 0,
    bars_limit: int = 0,
    fxs_offset: int = 0,
    fxs_limit: int = 0,
    bis_offset: int = 0,
    bis_limit: int = 0,
    recent_months: int = 0,
    edt: Optional[pd.Timestamp] = None,
) -> Dict[str, Any]:
    """
    对单一周期 bars 做 CZSC 分析并序列化
    
    时间范围控制说明（核心功能）：
    - 使用全量 bars 进行 CZSC 分析（确保分析准确性）
    - 如果 recent_months > 0，返回的 bars 只包含最近 recent_months 个月的数据
    - 分析数据（fxs、bis）基于全量数据计算，返回全量结果（不受 recent_months 限制）
    - 这确保了分析准确性（基于全量数据），同时减少了K线数据传输量（只传输最近N个月）
    
    分页参数说明（与 recent_months 配合使用）：
    - 数据按时间升序排列（最老的在前面，最新的在后面）
    - offset: 跳过前面的 offset 条（从最老的数据开始跳过）
    - limit: 返回 limit 条数据（0 表示返回全部）
    """
    if not bars:
        return {"bars": [], "bis": [], "fxs": [], "stats": {"bars_raw_count": 0}}
    
    # 使用全量 bars 进行 CZSC 分析（确保分析准确性）
    cz = CZSC(bars)
    
    # 获取总数（用于分页元数据）
    bars_total = len(bars)
    fxs_total = len(cz.fx_list)
    bis_total = len(cz.bi_list)
    
    # 序列化数据（bars 已经是按时间升序的）
    bars_serialized = serialize_raw_bars(bars)
    fxs_serialized = serialize_fxs(cz.fx_list)  # 分析数据：基于全量数据，返回全量结果
    bis_serialized = serialize_bis(cz.bi_list)  # 分析数据：基于全量数据，返回全量结果
    
    # 时间范围过滤：如果指定了 recent_months，只返回最近N个月的 bars
    if recent_months > 0 and edt is not None and bars_serialized:
        # 计算最近N个月的开始日期
        bars_start_dt = _get_recent_months_range(edt, recent_months)
        # 过滤 bars：只保留最近N个月的数据
        bars_serialized = [b for b in bars_serialized if pd.to_datetime(b["dt"]) >= bars_start_dt]
        logger.info(
            f"K线数据时间范围过滤: 全量={bars_total}条 过滤后={len(bars_serialized)}条 "
            f"时间范围={bars_start_dt.strftime('%Y-%m-%d')} ~ {edt.strftime('%Y-%m-%d')}"
        )
    
    # 分页处理：从末尾开始取（最新的数据在末尾）
    # offset=0, limit=100: 取最后100条（最新的）
    # offset=100, limit=100: 取倒数101-200条（更早的）
    if bars_limit > 0:
        start_idx = max(0, len(bars_serialized) - bars_offset - bars_limit)
        end_idx = len(bars_serialized) - bars_offset
        bars_serialized = bars_serialized[start_idx:end_idx] if end_idx > 0 else []
    elif bars_offset > 0:
        bars_serialized = bars_serialized[: len(bars_serialized) - bars_offset] if bars_offset < len(bars_serialized) else []
    
    if fxs_limit > 0:
        start_idx = max(0, fxs_total - fxs_offset - fxs_limit)
        end_idx = fxs_total - fxs_offset
        fxs_serialized = fxs_serialized[start_idx:end_idx] if end_idx > 0 else []
    elif fxs_offset > 0:
        fxs_serialized = fxs_serialized[: fxs_total - fxs_offset] if fxs_offset < fxs_total else []
    
    if bis_limit > 0:
        start_idx = max(0, bis_total - bis_offset - bis_limit)
        end_idx = bis_total - bis_offset
        bis_serialized = bis_serialized[start_idx:end_idx] if end_idx > 0 else []
    elif bis_offset > 0:
        bis_serialized = bis_serialized[: bis_total - bis_offset] if bis_offset < bis_total else []
    
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
    
    result = {
        "bars": bars_serialized,
        "bis": bis_serialized,  # 全量结果
        "fxs": fxs_serialized,  # 全量结果
        "stats": stats,
    }
    
    # 保存总数（用于分页元数据，后续会被清理）
    result["_bars_total"] = bars_total
    result["_fxs_total"] = fxs_total
    result["_bis_total"] = bis_total
    
    return result


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
        bars_offset: int = 0,
        bars_limit: int = 0,
        fxs_offset: int = 0,
        fxs_limit: int = 0,
        bis_offset: int = 0,
        bis_limit: int = 0,
        recent_months: int = 0,
    ) -> Dict[str, Any]:
        """
        对指定分钟周期（可选日线）进行分析并返回
        
        时间范围控制说明：
        - recent_months: 返回的K线数据只包含最近N个月（默认0表示返回全部）
        - 分析数据（fxs、bis）基于全量历史数据计算，返回全量结果（不受 recent_months 限制）
        
        分页参数说明：
        - offset: 数据偏移量（从第几条开始）
        - limit: 数据数量限制（0 表示返回全部，>0 时只返回指定数量）
        """
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
            bars_offset,
            bars_limit,
            fxs_offset,
            fxs_limit,
            bis_offset,
            bis_limit,
            recent_months,
        )


def _analyze_cached(
    base_path: str,
    symbol: str,
    sdt: str,
    edt: str,
    freqs: str,
    include_daily: bool,
    base_freq: str,
    bars_offset: int = 0,
    bars_limit: int = 0,
    fxs_offset: int = 0,
    fxs_limit: int = 0,
    bis_offset: int = 0,
    bis_limit: int = 0,
    recent_months: int = 0,
) -> Dict[str, Any]:
    """
    带缓存的分析入口（避免重复计算）
    
    注意：由于分页参数会影响返回结果，缓存键需要包含分页参数。但为了性能，我们只在没有分页参数时使用缓存。
    """
    bp = Path(base_path)
    sdt_dt = pd.to_datetime(sdt)
    edt_dt = pd.to_datetime(edt)
    requested = _requested_freq_values(freqs, include_daily)
    targets, warnings = _validate_freqs(base_freq, requested)
    
    # 判断是否有分页参数
    has_pagination = bars_limit > 0 or fxs_limit > 0 or bis_limit > 0
    
    logger.info(
        f"本地CZSC分析(BarGenerator): {symbol} base={base_freq} 请求周期={freqs} include_daily={include_daily} -> 目标周期={','.join(targets)} | {sdt} ~ {edt} "
        f"分页参数: bars({bars_offset},{bars_limit}) fxs({fxs_offset},{fxs_limit}) bis({bis_offset},{bis_limit}) "
        f"时间范围控制: recent_months={recent_months}"
    )
    df_minute, df_meta = _load_minute_df_with_meta(bp, symbol, sdt_dt, edt_dt)
    meta = _build_meta(bp, df_minute, df_meta, base_freq, requested, targets, warnings)
    if df_minute.empty:
        logger.warning(
            f"本地CZSC分析无数据: {symbol} | base={base_freq} | parquet={meta['parquet_count']} | {sdt} ~ {edt} | freqs={freqs} | include_daily={include_daily}"
        )
        return _empty_result(symbol, sdt, edt, base_freq, meta)

    items, counts, meta = _analyze_items(
        symbol,
        sdt,
        edt,
        base_freq,
        targets,
        df_minute,
        meta,
        bars_offset,
        bars_limit,
        fxs_offset,
        fxs_limit,
        bis_offset,
        bis_limit,
        recent_months,
    )
    meta["generated_bar_counts"] = counts

    # 确保 items 只包含 targets 中的周期（数据一致性保证）
    filtered_items = {k: v for k, v in items.items() if k in targets}
    if len(filtered_items) != len(items):
        logger.warning(
            f"本地CZSC数据过滤: {symbol} 过滤前周期={list(items.keys())} 过滤后周期={list(filtered_items.keys())} 目标周期={targets}"
        )

    # 构建分页元数据
    pagination = {}
    for freq_key, item_data in filtered_items.items():
        freq_pagination = {}
        if "bars" in item_data:
            bars_total = item_data.get("_bars_total", len(item_data["bars"]))
            bars_returned = len(item_data["bars"])
            freq_pagination["bars"] = {
                "total": bars_total,
                "offset": bars_offset,
                "limit": bars_limit if bars_limit > 0 else bars_total,
                "returned": bars_returned,
                "has_more": bars_limit > 0 and (bars_offset + bars_returned) < bars_total,
            }
        if "fxs" in item_data:
            fxs_total = item_data.get("_fxs_total", len(item_data["fxs"]))
            fxs_returned = len(item_data["fxs"])
            freq_pagination["fxs"] = {
                "total": fxs_total,
                "offset": fxs_offset,
                "limit": fxs_limit if fxs_limit > 0 else fxs_total,
                "returned": fxs_returned,
                "has_more": fxs_limit > 0 and (fxs_offset + fxs_returned) < fxs_total,
            }
        if "bis" in item_data:
            bis_total = item_data.get("_bis_total", len(item_data["bis"]))
            bis_returned = len(item_data["bis"])
            freq_pagination["bis"] = {
                "total": bis_total,
                "offset": bis_offset,
                "limit": bis_limit if bis_limit > 0 else bis_total,
                "returned": bis_returned,
                "has_more": bis_limit > 0 and (bis_offset + bis_returned) < bis_total,
            }
        if freq_pagination:
            pagination[freq_key] = freq_pagination
        # 清理临时字段
        item_data.pop("_bars_total", None)
        item_data.pop("_fxs_total", None)
        item_data.pop("_bis_total", None)

    logger.info(
        f"本地CZSC分析完成: {symbol} 返回周期={list(filtered_items.keys())} 目标周期={targets} | {sdt} ~ {edt} "
        f"分页信息={pagination}"
    )
    return {
        "symbol": symbol,
        "sdt": sdt,
        "edt": edt,
        "base_freq": base_freq,
        "items": filtered_items,
        "meta": meta,
        "pagination": pagination,
    }

