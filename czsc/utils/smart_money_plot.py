# -*- coding: utf-8 -*-
"""
Smart Money Concepts 可视化（pyecharts / ECharts）。

本模块将 `czsc.indicators.smart_money` 的计算结果渲染成单图 K 线 HTML：
- 矩形区域：OB / FVG / Premium-Discount Zones 使用 markArea
- 事件点：BOS / CHoCH / EQH / EQL 使用 Scatter
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Kline, Scatter
from pyecharts.commons.utils import JsCode

from czsc.indicators.smart_money import SMCEvent, SMCResult


def _dt_str(dt: pd.Timestamp) -> str:
    return pd.to_datetime(dt).strftime("%Y-%m-%d")


def _kline_items(df: pd.DataFrame) -> tuple[list[str], list[opts.CandleStickItem]]:
    dts = [_dt_str(x) for x in pd.to_datetime(df["dt"]).to_list()]
    items = []
    for i, row in df.iterrows():
        items.append(opts.CandleStickItem(name=i, value=[float(row["open"]), float(row["close"]), float(row["low"]), float(row["high"])]))
    return dts, items


def _areas_to_markarea_data(areas: List[SMCArea]) -> list:
    data = []
    for a in areas:
        data.append(
            [
                {
                    "name": a.name,
                    "xAxis": _dt_str(a.sdt),
                    "yAxis": round(float(a.bottom), 4),
                    "itemStyle": {"color": a.color_rgba, "borderColor": a.border_color, "borderWidth": 1},
                },
                {"xAxis": _dt_str(a.edt), "yAxis": round(float(a.top), 4)},
            ]
        )
    return data


def _events_to_scatters(events: List[SMCEvent]) -> List[Scatter]:
    """按 scope 分组输出多个 Scatter，减少混乱。"""
    if not events:
        return []
    groups = {"internal": [], "swing": [], "other": []}
    for e in events:
        groups.get(getattr(e, "scope", "other") or "other", groups["other"]).append(e)

    scatters: List[Scatter] = []
    style = {
        "internal": {"color": "#FFD166", "symbol": "circle", "size": 10},
        "swing": {"color": "#06D6A0", "symbol": "diamond", "size": 11},
        "other": {"color": "#9b9da9", "symbol": "triangle", "size": 9},
    }
    for scope, evs in groups.items():
        if not evs:
            continue
        xs = [_dt_str(e.dt) for e in evs]
        ys = [[float(e.price), f"{e.etype}({e.bias}) {e.text}"] for e in evs]
        sc = (
            Scatter()
            .add_xaxis(xs)
            .add_yaxis(
                series_name=f"SMC-{scope}",
                y_axis=ys,
                symbol_size=style[scope]["size"],
                symbol=style[scope]["symbol"],
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(color=style[scope]["color"]),
                tooltip_opts=opts.TooltipOpts(formatter=JsCode("function (params) {return params.value[2];}")),
            )
        )
        scatters.append(sc)
    return scatters


def smc_kline_chart(
    kline_df: pd.DataFrame,
    smc: SMCResult,
    title: str = "Smart Money Concepts",
    width: str = "1400px",
    height: str = "620px",
) -> Kline:
    """渲染 SMC 单图 K 线（返回 pyecharts Kline，可 render 为 HTML）。"""
    df = kline_df.copy()
    df["dt"] = pd.to_datetime(df["dt"])
    dts, k_items = _kline_items(df)
    chart = _build_base_kline(dts, k_items, title=title, width=width, height=height)

    ma_data = _areas_to_markarea_data(smc.areas)
    if ma_data:
        chart.set_series_opts(markarea_opts=opts.MarkAreaOpts(data=ma_data))

    for sc in _events_to_scatters(smc.events):
        chart = chart.overlap(sc)
    return chart


def _build_base_kline(
    dts: list[str],
    k_items: list[opts.CandleStickItem],
    title: str,
    width: str,
    height: str,
) -> Kline:
    bg_color = "#1f212d"
    up_color = "#F9293E"
    down_color = "#00aa3b"
    k_style = opts.ItemStyleOpts(color=up_color, color0=down_color, border_color=up_color, border_color0=down_color, opacity=0.9)
    chart = Kline(opts.InitOpts(bg_color=bg_color, width=width, height=height, animation_opts=opts.AnimationOpts(False)))
    chart.add_xaxis(dts)
    chart.add_yaxis("Kline", k_items, itemstyle_opts=k_style)
    _set_kline_global_opts(chart, title=title, up_color=up_color)
    return chart


def _set_kline_global_opts(chart: Kline, title: str, up_color: str) -> None:
    chart.set_global_opts(
        title_opts=opts.TitleOpts(title=title, pos_top="1%", title_textstyle_opts=opts.TextStyleOpts(color=up_color, font_size=18)),
        datazoom_opts=[
            opts.DataZoomOpts(False, "inside", range_start=80, range_end=100),
            opts.DataZoomOpts(True, "slider", pos_top="94%"),
        ],
        yaxis_opts=opts.AxisOpts(is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=False)),
        xaxis_opts=opts.AxisOpts(type_="category", axislabel_opts=opts.LabelOpts(is_show=True, color="#c7c7c7", font_size=9)),
        tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
        legend_opts=opts.LegendOpts(is_show=True, pos_top="1%", pos_left="30%", textstyle_opts=opts.TextStyleOpts(color="#0e99e2")),
    )

