# -*- coding: utf-8 -*-
"""
将 TradingView Pine 指标 Smart Money Concepts（LuxAlgo 版本思路）移植为 Python 计算模块。

说明：
- 本实现以“可视化输出”为目标：输出矩形区域（OB/FVG/溢价折价区）与事件点（BOS/CHoCH、EQH/EQL）。
- 由于 Pine 脚本包含多时间框架（request.security）与大量交互绘制细节，本模块默认在单一周期上计算；
  后续可在此基础上扩展 MTF levels / internal filter confluence 等功能。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

import numpy as np
import pandas as pd


Bias = Literal["bull", "bear"]
Scope = Literal["internal", "swing", "other"]
EventType = Literal["BOS", "CHoCH", "EQH", "EQL", "StrongHigh", "WeakHigh", "StrongLow", "WeakLow"]
Mode = Literal["historical", "present"]
Style = Literal["colored", "monochrome"]
OBFilter = Literal["atr", "cmr"]  # Atr / Cumulative Mean Range
OBMitigation = Literal["close", "highlow"]


@dataclass
class SMCEvent:
    """SMC 事件点：用于在图上打点或标注。"""

    dt: pd.Timestamp
    price: float
    etype: EventType
    bias: Bias
    text: str
    scope: Scope = "other"


@dataclass
class SMCConfig:
    """与 TradingView LuxAlgo SMC 脚本默认值对齐的配置。"""

    mode: Mode = "historical"
    style: Style = "colored"

    # 结构（internal & swing）
    show_internal_structure: bool = True
    internal_size: int = 5
    internal_filter_confluence: bool = False
    show_swing_structure: bool = True
    swing_size: int = 50

    # Swing 辅助
    show_high_low_swings: bool = True

    # Order Blocks
    show_internal_order_blocks: bool = True
    internal_order_blocks_size: int = 5
    show_swing_order_blocks: bool = False
    swing_order_blocks_size: int = 5
    order_block_filter: OBFilter = "atr"
    order_block_mitigation: OBMitigation = "highlow"

    # EQH / EQL
    show_equal_highs_lows: bool = True
    equal_highs_lows_length: int = 3
    equal_highs_lows_threshold: float = 0.1

    # Fair Value Gaps
    show_fair_value_gaps: bool = False
    fair_value_gaps_auto_threshold: bool = True
    fair_value_gaps_extend: int = 1

    # Premium / Discount Zones
    show_premium_discount_zones: bool = False


@dataclass
class SMCArea:
    """SMC 矩形区域：用于 markArea（如 OB、FVG、溢价折价区）。"""

    sdt: pd.Timestamp
    edt: pd.Timestamp
    top: float
    bottom: float
    name: str
    kind: str
    color_rgba: str
    border_color: str


@dataclass
class SMCResult:
    """Smart Money Concepts 计算结果。"""

    areas: List[SMCArea]
    events: List[SMCEvent]


@dataclass
class _SMCInputs:
    dts: List[pd.Timestamp]
    open_: np.ndarray
    close: np.ndarray
    high: np.ndarray
    low: np.ndarray
    atr200: np.ndarray
    parsed_high: np.ndarray
    parsed_low: np.ndarray


@dataclass
class _SMCState:
    sw_high: "_Pivot"
    sw_low: "_Pivot"
    in_high: "_Pivot"
    in_low: "_Pivot"
    eq_high: "_Pivot"
    eq_low: "_Pivot"
    sw_trend: "_Trend"
    in_trend: "_Trend"
    internal_obs: List["_OrderBlock"]
    swing_obs: List["_OrderBlock"]
    fvgs: List["_FVG"]
    fvg_cum_abs_delta: float
    areas: List[SMCArea]
    events: List[SMCEvent]
    trailing: "_TrailingExtremes"


def _ensure_dt(df: pd.DataFrame) -> pd.DataFrame:
    if "dt" not in df.columns:
        raise ValueError("df 必须包含 dt 列（datetime）")
    out = df.copy()
    out["dt"] = pd.to_datetime(out["dt"])
    out = out.sort_values("dt").reset_index(drop=True)
    return out


def _true_range(df: pd.DataFrame) -> np.ndarray:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    return tr


def _rma(values: np.ndarray, n: int) -> np.ndarray:
    """Wilder RMA（与 Pine ta.atr / ta.rma 一致的平滑方式）。"""
    out = np.full_like(values, fill_value=np.nan, dtype=float)
    if len(values) == 0:
        return out
    alpha = 1.0 / float(n)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1 - alpha) * out[i - 1]
    return out


def atr_wilder(df: pd.DataFrame, n: int = 200) -> np.ndarray:
    """计算 ATR（Wilder 版本）。"""
    tr = _true_range(df)
    return _rma(tr, n)


def cumulative_mean_range(df: pd.DataFrame) -> np.ndarray:
    """累计均值波动（对应 Pine: ta.cum(ta.tr)/bar_index）。"""
    tr = _true_range(df)
    csum = np.cumsum(tr)
    idx = np.arange(1, len(tr) + 1, dtype=float)
    return csum / idx


def _detect_pivot_at(df: pd.DataFrame, i: int, size: int) -> Tuple[bool, bool, int]:
    """
    在当前索引 i 时刻，检查是否在 (i-size) 处形成 pivot high / pivot low。

    对齐 Pine 写法：
    - newLegHigh = high[size] > ta.highest(size)
    - newLegLow  = low[size]  < ta.lowest(size)
    """
    p = i - size
    if p < 0:
        return False, False, -1
    hi = df["high"].to_numpy(dtype=float)
    lo = df["low"].to_numpy(dtype=float)
    win_hi = hi[p + 1 : i + 1]
    win_lo = lo[p + 1 : i + 1]
    if len(win_hi) < size:
        return False, False, -1
    is_ph = hi[p] > np.nanmax(win_hi)
    is_pl = lo[p] < np.nanmin(win_lo)
    return bool(is_ph), bool(is_pl), p


@dataclass
class _Pivot:
    current: float = np.nan
    last: float = np.nan
    crossed: bool = False
    dt: Optional[pd.Timestamp] = None
    idx: int = -1


@dataclass
class _Trend:
    bias: Bias = "bear"


@dataclass
class _OrderBlock:
    top: float
    bottom: float
    bias: Bias
    sdt: pd.Timestamp
    sidx: int
    edt: Optional[pd.Timestamp] = None
    eidx: Optional[int] = None


@dataclass
class _FVG:
    top: float
    bottom: float
    bias: Bias
    sdt: pd.Timestamp
    sidx: int
    edt: Optional[pd.Timestamp] = None
    eidx: Optional[int] = None


def _parsed_hilo(df: pd.DataFrame, vol_measure: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """按 Pine 逻辑对高低点做“波动过滤”后的解析值。"""
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    rng = high - low
    hv = rng >= (2.0 * vol_measure)
    parsed_high = np.where(hv, low, high)
    parsed_low = np.where(hv, high, low)
    return parsed_high, parsed_low


def _cross_over(a0: float, a1: float, level: float) -> bool:
    return (a0 <= level) and (a1 > level)


def _cross_under(a0: float, a1: float, level: float) -> bool:
    return (a0 >= level) and (a1 < level)


def _ob_style(scope: Scope, bias: Bias, style: Style = "colored") -> Tuple[str, str]:
    """Order Block 的颜色（对齐 Pine 默认颜色）。"""
    if style == "monochrome":
        return ("rgba(189, 189, 189, 0.18)", "#b2b5be") if bias == "bull" else ("rgba(93, 96, 107, 0.18)", "#5d606b")
    if scope == "swing":
        if bias == "bull":
            return "rgba(24, 72, 204, 0.22)", "#1848cc"
        return "rgba(178, 40, 51, 0.22)", "#b22833"
    # internal
    if bias == "bull":
        return "rgba(49, 121, 245, 0.22)", "#3179f5"
    return "rgba(247, 124, 128, 0.22)", "#f77c80"


def _fvg_style(bias: Bias, style: Style = "colored") -> Tuple[str, str]:
    """FVG 的颜色（对齐 Pine 默认颜色）。"""
    if style == "monochrome":
        return ("rgba(189, 189, 189, 0.18)", "#b2b5be") if bias == "bull" else ("rgba(93, 96, 107, 0.18)", "#5d606b")
    if bias == "bull":
        return "rgba(0, 255, 104, 0.20)", "#00ff68"
    return "rgba(255, 0, 8, 0.20)", "#ff0008"


def _zone_style(kind: str) -> Tuple[str, str]:
    if kind == "premium":
        return "rgba(242, 54, 69, 0.10)", "#F23645"
    if kind == "discount":
        return "rgba(8, 153, 129, 0.10)", "#089981"
    return "rgba(135, 139, 148, 0.08)", "#878b94"


def _make_area(sdt: pd.Timestamp, edt: pd.Timestamp, top: float, bottom: float, name: str, kind: str, color: str, border: str) -> SMCArea:
    return SMCArea(sdt=sdt, edt=edt, top=float(top), bottom=float(bottom), name=name, kind=kind, color_rgba=color, border_color=border)


def _append_zone_areas(
    areas: List[SMCArea], sdt: pd.Timestamp, edt: pd.Timestamp, top: float, bottom: float
) -> None:
    """添加溢价/折价/均衡区域（按 LuxAlgo 默认比例）。"""
    if not np.isfinite(top) or not np.isfinite(bottom) or top <= bottom:
        return
    premium_bottom = 0.95 * top + 0.05 * bottom
    discount_top = 0.95 * bottom + 0.05 * top
    eq = 0.5 * (top + bottom)
    eq_top = 0.525 * top + 0.475 * bottom
    eq_bottom = 0.525 * bottom + 0.475 * top

    c1, b1 = _zone_style("premium")
    areas.append(_make_area(sdt, edt, top, premium_bottom, "Premium", "zone_premium", c1, b1))
    c2, b2 = _zone_style("equilibrium")
    areas.append(_make_area(sdt, edt, eq_top, eq_bottom, "Equilibrium", "zone_eq", c2, b2))
    c3, b3 = _zone_style("discount")
    areas.append(_make_area(sdt, edt, discount_top, bottom, "Discount", "zone_discount", c3, b3))


def smart_money_concepts(df: pd.DataFrame, config: Optional[SMCConfig] = None) -> SMCResult:
    """计算 Smart Money Concepts（尽量对齐 LuxAlgo Pine 默认逻辑与默认开关）。"""
    cfg = config or SMCConfig()
    df = _ensure_dt(df)
    if len(df) < max(cfg.swing_size, cfg.internal_size) + 10:
        return SMCResult(areas=[], events=[])
    x = _prepare_inputs(df, cfg.order_block_filter)
    st = _init_state(df, x)
    for i in range(1, len(df)):
        _process_one_bar(i=i, df=df, x=x, st=st, cfg=cfg)
    _finalize_last_bar(df=df, x=x, st=st, cfg=cfg)
    return SMCResult(areas=_merge_small_areas(st.areas), events=st.events)


def _prepare_inputs(df: pd.DataFrame, ob_filter: OBFilter) -> _SMCInputs:
    dts = pd.to_datetime(df["dt"]).to_list()
    open_ = df["open"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    atr200 = atr_wilder(df, 200)
    cmr = cumulative_mean_range(df)
    vol_measure = atr200 if ob_filter == "atr" else cmr
    vm = np.nan_to_num(vol_measure, nan=float(np.nanmean(vol_measure)))
    parsed_high, parsed_low = _parsed_hilo(df, vm)
    return _SMCInputs(dts=dts, open_=open_, close=close, high=high, low=low, atr200=atr200, parsed_high=parsed_high, parsed_low=parsed_low)


@dataclass
class _TrailingExtremes:
    top: float
    bottom: float
    anchor_dt: pd.Timestamp
    last_top_dt: pd.Timestamp
    last_bottom_dt: pd.Timestamp


def _init_state(df: pd.DataFrame, x: _SMCInputs) -> _SMCState:
    dt0 = x.dts[0]
    trailing = _TrailingExtremes(
        top=float(x.high[0]),
        bottom=float(x.low[0]),
        anchor_dt=dt0,
        last_top_dt=dt0,
        last_bottom_dt=dt0,
    )
    return _SMCState(
        sw_high=_Pivot(),
        sw_low=_Pivot(),
        in_high=_Pivot(),
        in_low=_Pivot(),
        eq_high=_Pivot(),
        eq_low=_Pivot(),
        sw_trend=_Trend("bear"),
        in_trend=_Trend("bear"),
        internal_obs=[],
        swing_obs=[],
        fvgs=[],
        fvg_cum_abs_delta=0.0,
        areas=[],
        events=[],
        trailing=trailing,
    )


def _process_one_bar(i: int, df: pd.DataFrame, x: _SMCInputs, st: _SMCState, cfg: SMCConfig) -> None:
    need_internal = cfg.show_internal_structure or cfg.show_internal_order_blocks
    need_swing = (
        cfg.show_swing_structure
        or cfg.show_swing_order_blocks
        or cfg.show_equal_highs_lows
        or cfg.show_premium_discount_zones
        or cfg.show_high_low_swings
    )
    if need_internal:
        _update_structure_pivots(df, i, cfg.internal_size, st.in_high, st.in_low)
    if need_swing:
        updated = _update_structure_pivots(df, i, cfg.swing_size, st.sw_high, st.sw_low)
        _sync_trailing_on_swing_pivot(updated, x, st)

    if cfg.show_equal_highs_lows:
        _update_equal_high_low(df, i, x, st, cfg)

    if cfg.show_high_low_swings or cfg.show_premium_discount_zones:
        _update_trailing_extremes(i, x, st)

    if cfg.show_internal_structure:
        _process_structure_break(i, x, st, scope="internal", cfg=cfg)
    if cfg.show_swing_structure:
        _process_structure_break(i, x, st, scope="swing", cfg=cfg)

    if cfg.show_internal_order_blocks or cfg.show_swing_order_blocks:
        _delete_mitigated_order_blocks(i, x, st, cfg)

    if cfg.show_fair_value_gaps:
        _delete_filled_fvg(i, x, st)
        _detect_fvg_luxalgo(i, x, st, cfg)


def _update_structure_pivots(
    df: pd.DataFrame, i: int, size: int, p_high: _Pivot, p_low: _Pivot
) -> Optional[Tuple[str, pd.Timestamp, float]]:
    is_ph, is_pl, p = _detect_pivot_at(df, i, size)
    if p < 0 or (not is_ph and not is_pl):
        return None
    dtp = pd.to_datetime(df["dt"].iloc[p])
    if is_pl:
        p_low.last = p_low.current
        p_low.current = float(df["low"].iloc[p])
        p_low.crossed = False
        p_low.dt = dtp
        p_low.idx = p
        return ("low", dtp, p_low.current)
    if is_ph:
        p_high.last = p_high.current
        p_high.current = float(df["high"].iloc[p])
        p_high.crossed = False
        p_high.dt = dtp
        p_high.idx = p
        return ("high", dtp, p_high.current)


def _process_structure_break(i: int, x: _SMCInputs, st: _SMCState, scope: Scope, cfg: SMCConfig) -> None:
    p_high, p_low, trend = _pick_scope_state(st, scope)
    if p_high.dt is not None:
        _try_break_level(i, x, st, scope, cfg, p_high, trend, side="high")
    if p_low.dt is not None:
        _try_break_level(i, x, st, scope, cfg, p_low, trend, side="low")


def _pick_scope_state(st: _SMCState, scope: Scope) -> Tuple[_Pivot, _Pivot, _Trend]:
    if scope == "internal":
        return st.in_high, st.in_low, st.in_trend
    return st.sw_high, st.sw_low, st.sw_trend


def _try_break_level(
    i: int,
    x: _SMCInputs,
    st: _SMCState,
    scope: Scope,
    cfg: SMCConfig,
    pivot: _Pivot,
    trend: _Trend,
    side: Literal["high", "low"],
) -> None:
    if pivot.crossed or (not np.isfinite(pivot.current)):
        return
    if scope == "internal" and (not _internal_extra_condition(i, x, st, cfg, side)):
        return

    prev_close = float(x.close[i - 1])
    cur_close = float(x.close[i])
    level = float(pivot.current)
    crossed = _cross_over(prev_close, cur_close, level) if side == "high" else _cross_under(prev_close, cur_close, level)
    if not crossed:
        return

    bullish = side == "high"
    etype: EventType = "CHoCH" if ((trend.bias == "bear") == bullish) else "BOS"
    trend.bias = "bull" if bullish else "bear"
    pivot.crossed = True
    st.events.append(
        SMCEvent(dt=x.dts[i], price=cur_close, etype=etype, bias=("bull" if bullish else "bear"), scope=scope, text=f"{scope}:{etype}")
    )
    _maybe_store_order_block(i, x, st, cfg, pivot, bias=("bull" if bullish else "bear"), scope=scope)


def _internal_extra_condition(i: int, x: _SMCInputs, st: _SMCState, cfg: SMCConfig, side: str) -> bool:
    if not cfg.internal_filter_confluence:
        return True
    # 对齐 Pine 的 bullishBar / bearishBar 过滤逻辑
    upper = float(x.high[i]) - float(max(x.close[i], x.open_[i]))
    lower = float(min(x.close[i], x.open_[i])) - float(x.low[i])
    bullish_bar = upper > lower
    bearish_bar = upper < lower
    if side == "high":
        return bullish_bar and (st.in_high.current != st.sw_high.current)
    return bearish_bar and (st.in_low.current != st.sw_low.current)


def _maybe_store_order_block(i: int, x: _SMCInputs, st: _SMCState, cfg: SMCConfig, pivot: _Pivot, bias: Bias, scope: Scope) -> None:
    if scope == "internal" and (not cfg.show_internal_order_blocks):
        return
    if scope == "swing" and (not cfg.show_swing_order_blocks):
        return
    target = st.internal_obs if scope == "internal" else st.swing_obs
    ob = _make_order_block_from_pivot(pivot, i, x, bias=bias)
    if ob is None:
        return
    target.insert(0, ob)
    if len(target) > 100:
        target.pop()


def _make_order_block_from_pivot(pivot: _Pivot, i: int, x: _SMCInputs, bias: Bias) -> Optional[_OrderBlock]:
    if pivot.idx < 0 or pivot.idx >= i:
        return None
    s = pivot.idx
    if bias == "bear":
        arr = x.parsed_high[s:i]
        if len(arr) == 0:
            return None
        idx = s + int(np.nanargmax(arr))
    else:
        arr = x.parsed_low[s:i]
        if len(arr) == 0:
            return None
        idx = s + int(np.nanargmin(arr))
    top = float(x.parsed_high[idx])
    bottom = float(x.parsed_low[idx])
    if (not np.isfinite(top)) or (not np.isfinite(bottom)) or top <= bottom:
        return None
    return _OrderBlock(top=top, bottom=bottom, bias=bias, sdt=x.dts[idx], sidx=idx)


def _delete_mitigated_order_blocks(i: int, x: _SMCInputs, st: _SMCState, cfg: SMCConfig) -> None:
    bear_src = float(x.close[i]) if cfg.order_block_mitigation == "close" else float(x.high[i])
    bull_src = float(x.close[i]) if cfg.order_block_mitigation == "close" else float(x.low[i])
    st.internal_obs = _filter_active_obs(st.internal_obs, bear_src, bull_src)
    st.swing_obs = _filter_active_obs(st.swing_obs, bear_src, bull_src)


def _filter_active_obs(obs: List[_OrderBlock], bear_src: float, bull_src: float) -> List[_OrderBlock]:
    out = []
    for ob in obs:
        if ob.bias == "bear" and bear_src > ob.top:
            continue
        if ob.bias == "bull" and bull_src < ob.bottom:
            continue
        out.append(ob)
    return out


def _delete_filled_fvg(i: int, x: _SMCInputs, st: _SMCState) -> None:
    if not st.fvgs:
        return
    cur_low = float(x.low[i])
    cur_high = float(x.high[i])
    out = []
    for g in st.fvgs:
        if (g.bias == "bull" and cur_low < g.bottom) or (g.bias == "bear" and cur_high > g.top):
            continue
        out.append(g)
    st.fvgs = out


def _detect_fvg_luxalgo(i: int, x: _SMCInputs, st: _SMCState, cfg: SMCConfig) -> None:
    if i < 2:
        return
    last_close = float(x.close[i - 1])
    last_open = float(x.open_[i - 1])
    last2_high = float(x.high[i - 2])
    last2_low = float(x.low[i - 2])
    current_high = float(x.high[i])
    current_low = float(x.low[i])

    bar_delta_percent = (last_close - last_open) / (last_open * 100.0) if last_open != 0 else 0.0
    st.fvg_cum_abs_delta += abs(bar_delta_percent)
    threshold = (st.fvg_cum_abs_delta / max(i, 1)) * 2.0 if cfg.fair_value_gaps_auto_threshold else 0.0
    extend = max(int(cfg.fair_value_gaps_extend), 0)
    end_i = min(i + extend, len(x.dts) - 1)

    bullish = current_low > last2_high and last_close > last2_high and bar_delta_percent > threshold
    bearish = current_high < last2_low and last_close < last2_low and (-bar_delta_percent) > threshold
    if bullish:
        st.fvgs.insert(0, _FVG(top=current_low, bottom=last2_high, bias="bull", sdt=x.dts[i - 1], sidx=i - 1, edt=x.dts[end_i], eidx=end_i))
    if bearish:
        st.fvgs.insert(0, _FVG(top=last2_low, bottom=current_high, bias="bear", sdt=x.dts[i - 1], sidx=i - 1, edt=x.dts[end_i], eidx=end_i))
    if len(st.fvgs) > 200:
        st.fvgs = st.fvgs[:200]


def _update_trailing_extremes(i: int, x: _SMCInputs, st: _SMCState) -> None:
    h = float(x.high[i])
    l = float(x.low[i])
    if h >= st.trailing.top:
        st.trailing.top = h
        st.trailing.last_top_dt = x.dts[i]
    if l <= st.trailing.bottom:
        st.trailing.bottom = l
        st.trailing.last_bottom_dt = x.dts[i]


def _sync_trailing_on_swing_pivot(updated, x: _SMCInputs, st: _SMCState) -> None:
    if not updated:
        return
    side, dtp, price = updated
    st.trailing.anchor_dt = dtp
    if side == "high":
        st.trailing.top = float(price)
        st.trailing.last_top_dt = dtp
    if side == "low":
        st.trailing.bottom = float(price)
        st.trailing.last_bottom_dt = dtp


def _update_equal_high_low(df: pd.DataFrame, i: int, x: _SMCInputs, st: _SMCState, cfg: SMCConfig) -> None:
    updated = _update_structure_pivots(df, i, cfg.equal_highs_lows_length, st.eq_high, st.eq_low)
    if not updated:
        return
    thr = float(x.atr200[i]) * float(cfg.equal_highs_lows_threshold) if i < len(x.atr200) and np.isfinite(x.atr200[i]) else np.nan
    if not np.isfinite(thr) or thr <= 0:
        return
    side, dtp, price = updated
    if side == "high" and np.isfinite(st.eq_high.last) and abs(float(st.eq_high.current) - float(st.eq_high.last)) < thr:
        st.events.append(SMCEvent(dt=dtp, price=float(price), etype="EQH", bias="bear", scope="other", text="EQH"))
    if side == "low" and np.isfinite(st.eq_low.last) and abs(float(st.eq_low.current) - float(st.eq_low.last)) < thr:
        st.events.append(SMCEvent(dt=dtp, price=float(price), etype="EQL", bias="bull", scope="other", text="EQL"))


def _finalize_last_bar(df: pd.DataFrame, x: _SMCInputs, st: _SMCState, cfg: SMCConfig) -> None:
    last_dt = x.dts[-1]
    if cfg.show_internal_order_blocks and st.internal_obs:
        _append_ob_areas(st, st.internal_obs[: cfg.internal_order_blocks_size], scope="internal", cfg=cfg, end_dt=last_dt)
    if cfg.show_swing_order_blocks and st.swing_obs:
        _append_ob_areas(st, st.swing_obs[: cfg.swing_order_blocks_size], scope="swing", cfg=cfg, end_dt=last_dt)
    if cfg.show_fair_value_gaps and st.fvgs:
        _append_fvg_areas(st, st.fvgs, cfg=cfg)
    if cfg.show_premium_discount_zones:
        _append_premium_discount_areas(st, end_dt=last_dt)
    if cfg.show_high_low_swings:
        _append_high_low_events(st, dt=last_dt)


def _append_ob_areas(st: _SMCState, obs: List[_OrderBlock], scope: Scope, cfg: SMCConfig, end_dt: pd.Timestamp) -> None:
    for ob in obs:
        color, border = _ob_style(scope=scope, bias=ob.bias, style=cfg.style)
        st.areas.append(_make_area(ob.sdt, end_dt, ob.top, ob.bottom, "OrderBlock", f"ob_{scope}_{ob.bias}", color, border))


def _append_fvg_areas(st: _SMCState, fvgs: List[_FVG], cfg: SMCConfig) -> None:
    for g in fvgs:
        color, border = _fvg_style(bias=g.bias, style=cfg.style)
        st.areas.append(_make_area(g.sdt, g.edt or g.sdt, g.top, g.bottom, "FVG", f"fvg_{g.bias}", color, border))


def _append_premium_discount_areas(st: _SMCState, end_dt: pd.Timestamp) -> None:
    _append_zone_areas(st.areas, st.trailing.anchor_dt, end_dt, st.trailing.top, st.trailing.bottom)


def _append_high_low_events(st: _SMCState, dt: pd.Timestamp) -> None:
    et_hi: EventType = "StrongHigh" if st.sw_trend.bias == "bear" else "WeakHigh"
    et_lo: EventType = "StrongLow" if st.sw_trend.bias == "bull" else "WeakLow"
    st.events.append(SMCEvent(dt=dt, price=float(st.trailing.top), etype=et_hi, bias="bear", scope="swing", text=str(et_hi)))
    st.events.append(SMCEvent(dt=dt, price=float(st.trailing.bottom), etype=et_lo, bias="bull", scope="swing", text=str(et_lo)))


def _merge_small_areas(areas: List[SMCArea]) -> List[SMCArea]:
    """简单去重与合并：同 kind + 同价格带 + 相邻日期重叠则合并。"""
    if not areas:
        return []
    areas_sorted = sorted(areas, key=lambda x: (x.kind, x.bottom, x.top, x.sdt))
    out: List[SMCArea] = []
    cur = areas_sorted[0]
    for a in areas_sorted[1:]:
        same_band = (a.kind == cur.kind) and (abs(a.top - cur.top) < 1e-6) and (abs(a.bottom - cur.bottom) < 1e-6)
        if same_band and a.sdt <= cur.edt:
            cur.edt = max(cur.edt, a.edt)
            continue
        out.append(cur)
        cur = a
    out.append(cur)
    return out

