# -*- coding: utf-8 -*-
"""
Smart Money Concepts（LuxAlgo 思路）本地 Demo。

功能：
- 拉取指定股票日线数据
- 计算 SMC（结构/OB/FVG/EQH-EQL/溢价折价区）
- 输出本地 HTML（ECharts / pyecharts）
- 可选一键打开 TradingView 对照链接

示例：
python demo/step1-analyzes/smart_money_demo.py --symbol 300308.SZ --sdt 20180101 --open-tv
"""

from __future__ import annotations

import argparse
import webbrowser
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from czsc import Freq
from czsc.connectors import research
from czsc.indicators.smart_money import SMCConfig, smart_money_concepts
from czsc.utils.smart_money_plot import smc_kline_chart


TV_URL_300308 = "https://cn.tradingview.com/chart/gcSZ1uLD/?symbol=SZSE%3A300308"


def _bars_to_df(bars: list) -> pd.DataFrame:
    rows = []
    for b in bars:
        rows.append(
            {
                "dt": b.dt,
                "open": float(b.open),
                "close": float(b.close),
                "high": float(b.high),
                "low": float(b.low),
                "vol": float(getattr(b, "vol", 0) or getattr(b, "volume", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("dt").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Money Concepts 本地可视化 Demo")
    parser.add_argument("--symbol", type=str, default="300308.SZ", help="股票代码，如 300308.SZ")
    parser.add_argument("--sdt", type=str, default="20180101", help="开始日期，如 20180101")
    parser.add_argument("--edt", type=str, default=None, help="结束日期，默认今天")
    parser.add_argument("--open-tv", action="store_true", help="打开 TradingView 对照链接（300308）")
    parser.add_argument("--open-html", action="store_true", help="生成后自动打开本地 HTML")
    parser.add_argument("--show-fvg", action="store_true", help="显示 Fair Value Gaps（TradingView 脚本默认关闭）")
    parser.add_argument("--show-zones", action="store_true", help="显示 Premium/Discount Zones（TradingView 脚本默认关闭）")
    parser.add_argument("--show-swing-ob", action="store_true", help="显示 Swing Order Blocks（TradingView 脚本默认关闭）")
    parser.add_argument("--no-internal-ob", action="store_true", help="不显示 Internal Order Blocks（TradingView 脚本默认开启）")
    args = parser.parse_args()

    symbol = (args.symbol or "").strip().upper()
    if not symbol or "." not in symbol:
        logger.error("--symbol 需为 代码.市场，如 300308.SZ")
        return

    edt = args.edt or datetime.now().strftime("%Y%m%d")
    logger.info(f"获取数据: {symbol} {args.sdt} ~ {edt}")
    bars = research.get_raw_bars_daily(symbol=symbol, freq=Freq.D, sdt=args.sdt, edt=edt)
    if not bars or len(bars) < 200:
        logger.error(f"数据不足或无法获取: {symbol}，bars={0 if not bars else len(bars)}")
        return

    df = _bars_to_df(bars)
    cfg = SMCConfig(
        show_fair_value_gaps=bool(args.show_fvg),
        show_premium_discount_zones=bool(args.show_zones),
        show_swing_order_blocks=bool(args.show_swing_ob),
        show_internal_order_blocks=not bool(args.no_internal_ob),
    )
    smc = smart_money_concepts(df, config=cfg)
    chart = smc_kline_chart(df, smc, title=f"{symbol} Smart Money Concepts")

    project_root = Path(__file__).parent.parent
    out_dir = project_root / ".results"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"smc_{symbol.replace('.', '_')}_{ts}.html"
    chart.render(str(out_file))
    logger.info(f"✓ 已生成: {out_file.absolute()}")

    if args.open_html:
        webbrowser.open(str(out_file.absolute()))
    if args.open_tv:
        webbrowser.open(TV_URL_300308)


if __name__ == "__main__":
    main()

