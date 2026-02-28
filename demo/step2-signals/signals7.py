# -*- coding: utf-8 -*-
"""
用日线数据运行四策略信号，生成 HTML 报告；并支持「涨停后回调至支撑位」形态筛选与可视化。
股票列表与名称来自 stock_basic.csv 全量，K 线来自 get_raw_bars_daily（daily/by_stock）。

筛选逻辑（涨停回调支撑）：
  - N 天内有涨停：过去 limit_days 日内涨幅 >= limit_pct（默认 9.5%）
  - 当前处于回调：当前收盘 < 涨停日收盘（已回吐）
  - 回踩支撑：收盘在 MA60 的 -3%～+1% 或 接近近 20 日最低
  - 止跌迹象：今日阳线或长下影线，且量能温和放大

# 在项目根目录、使用已安装 czsc/pandas 等依赖的 Python 环境运行
cd /Users/liyang/Desktop/npc-czsc

# 扫描全部股票（含涨停回调支撑标记）
python demo/step2-signals/signals7.py --sdt 20240101

# 仅分析单只股票：输出 K 线图（符合形态区间标在图上）+ Tab「形态区间」表（起始/结束日期）
python demo/step2-signals/signals7.py --sdt 20240101 --stock 600078.SH
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import pandas as pd

try:
    from loguru import logger
except ImportError:
    class _Logger:
        def info(self, msg, *a, **k): print("[INFO]", msg % a if a else msg)
        def warning(self, msg, *a, **k): print("[WARN]", msg % a if a else msg)
        def error(self, msg, *a, **k): print("[ERR]", msg % a if a else msg)
        def debug(self, msg, *a, **k): pass
    logger = _Logger()

# 项目根目录（demo/step2-signals/xxx.py -> step2-signals -> demo -> 根）
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research

# daily/by_stock 所在目录（与 research 一致，cache_path 为 .stock_data/raw）
cache_path = os.environ.get("czsc_research_cache", str(project_root / ".stock_data" / "raw"))
DAILY_ROOT = Path(cache_path) / "daily" / "by_stock"
STOCK_BASIC_CSV = project_root / ".stock_data" / "metadata" / "stock_basic.csv"

MA_NAME = "SMA#40"
SDT = "20200101"
# 默认结束日期为当天（数据源有今日则到今日，否则到昨日等最新）
def _default_edt() -> str:
    return datetime.now().strftime("%Y%m%d")


INIT_N = 300

SIGNALS_CONFIG = [
    {
        "name": "czsc.signals.tas_ma_base_V230313",
        "freq": "日线",
        "di": 1,
        "ma_type": "SMA",
        "timeperiod": 40,
        "max_overlap": 5,
    },
    {"name": "czsc.signals.cxt_five_bi_V230619", "freq": "日线", "di": 1},
]


def _bars_to_klinedf(bars: list) -> pd.DataFrame:
    """将 RawBar 列表转为 K 线 DataFrame，列：dt, open, close, high, low, volume。按 dt 升序。"""
    if not bars:
        return pd.DataFrame()
    rows = []
    for b in bars:
        vol = getattr(b, "vol", None) or getattr(b, "volume", 0)
        rows.append({
            "dt": b.dt,
            "open": float(b.open),
            "close": float(b.close),
            "high": float(b.high),
            "low": float(b.low),
            "volume": float(vol) if vol is not None else 0,
        })
    return pd.DataFrame(rows).sort_values("dt").reset_index(drop=True)


def find_limit_pullback_support(
    df: pd.DataFrame,
    lookback_days: int = 60,
    limit_days: int = 5,
    limit_pct: float = 9.5,
    ma60_low_pct: float = -0.03,
    ma60_high_pct: float = 0.01,
    lld_days: int = 20,
    lld_low_pct: float = -0.02,
    lld_high_pct: float = 0.05,
    volume_ratio_min: float = 1.0,
    lower_shadow_ratio_min: float = 0.5,
) -> bool:
    """
    筛选「涨停后回调至支撑位」形态：N 天内有涨停 -> 当前已回调 -> 回踩 MA60 或前低 -> 止跌/放量。

    :param df: K 线 DataFrame，列 dt, open, close, high, low, volume，按日期升序
    :param lookback_days: 均线回溯天数
    :param limit_days: 寻找涨停的最近交易日数
    :param limit_pct: 涨停阈值（涨幅%，如 9.5）
    :param ma60_low_pct: 收盘相对 MA60 下限（如 -0.03 表示 -3%）
    :param ma60_high_pct: 收盘相对 MA60 上限（如 0.01 表示 +1%）
    :param lld_days: 前低回溯天数
    :param lld_low_pct / lld_high_pct: 收盘相对前低区间
    :param volume_ratio_min: 今日量/昨日量 最小比值（止跌放量）
    :param lower_shadow_ratio_min: 下影线占整根 K 线比例阈值（长下影）
    :return: True 表示符合形态
    """
    if df is None or len(df) < lookback_days:
        return False
    df = df.copy()
    df["MA60"] = df["close"].rolling(window=60, min_periods=1).mean()
    df["prev_close"] = df["close"].shift(1)
    df["pct_chg"] = (df["close"] - df["prev_close"]) / df["prev_close"].replace(0, pd.NA) * 100

    # 1. 最近 limit_days 内是否有涨停
    recent_limit = False
    limit_day_close = 0.0
    for i in range(1, min(limit_days + 1, len(df))):
        pct = df["pct_chg"].iloc[-i]
        if pd.notna(pct) and pct >= limit_pct:
            recent_limit = True
            limit_day_close = float(df["close"].iloc[-i])
            break
    if not recent_limit or limit_day_close <= 0:
        return False

    current_close = float(df["close"].iloc[-1])
    # 2. 已回调：当前收盘 < 涨停日收盘，且不在涨停价附近
    if current_close >= limit_day_close * 0.98:
        return False

    # 3. 回踩支撑：MA60 或 前低
    current_ma60 = float(df["MA60"].iloc[-1])
    if current_ma60 <= 0:
        return False
    ma60_ok = (current_close >= current_ma60 * (1 + ma60_low_pct)) and (
        current_close <= current_ma60 * (1 + ma60_high_pct)
    )
    recent_low = float(df["low"].iloc[-lld_days:].min())
    if recent_low <= 0:
        lld_ok = False
    else:
        lld_ok = (current_close >= recent_low * (1 + lld_low_pct)) and (
            current_close <= recent_low * (1 + lld_high_pct)
        )
    if not (ma60_ok or lld_ok):
        return False

    # 4. 止跌：今日阳线 或 长下影线，且量能温和放大
    last = df.iloc[-1]
    o, c, h, l_ = float(last["open"]), float(last["close"]), float(last["high"]), float(last["low"])
    is_yang = c > o
    range_ = h - l_
    if range_ > 1e-8:
        lower_shadow = min(o, c) - l_
        lower_ratio = lower_shadow / range_
    else:
        lower_ratio = 0.0
    long_lower_shadow = lower_ratio >= lower_shadow_ratio_min

    vol_today = float(df["volume"].iloc[-1])
    vol_yesterday = float(df["volume"].iloc[-2]) if len(df) >= 2 else vol_today
    if vol_yesterday > 1e-8:
        volume_ratio = vol_today / vol_yesterday
    else:
        volume_ratio = 1.0
    volume_ok = volume_ratio >= volume_ratio_min

    if (is_yang or long_lower_shadow) and volume_ok:
        return True
    return False


def find_all_limit_pullback_ranges(
    df: pd.DataFrame,
    lookback_days: int = 60,
    **kwargs,
) -> list:
    """
    扫描全历史，找出所有「涨停回调支撑」形态成立的日期，合并连续日为 (start_dt, end_dt) 区间。
    :return: [(start_dt, end_dt), ...]，dt 为 pandas Timestamp 或 datetime
    """
    if df is None or len(df) < lookback_days:
        return []
    pattern_dates = []
    for i in range(lookback_days, len(df)):
        slice_df = df.iloc[: i + 1].copy()
        if find_limit_pullback_support(slice_df, lookback_days=lookback_days, **kwargs):
            pattern_dates.append(df["dt"].iloc[i])
    if not pattern_dates:
        return []
    pattern_dates = sorted(set(pattern_dates))
    # 合并连续日期为区间
    ranges = []
    start = pattern_dates[0]
    end = pattern_dates[0]
    for d in pattern_dates[1:]:
        delta = (d - end).days if hasattr(d - end, "days") else getattr(d - end, "days", 999)
        if delta <= 3:
            end = d
        else:
            ranges.append((start, end))
            start = d
            end = d
    ranges.append((start, end))
    return ranges


def _build_pattern_chart_and_tab(
    symbol: str,
    bars: list,
    kline_df: pd.DataFrame,
    output_path: Path,
    width: str = "1400px",
    height: str = "580px",
) -> None:
    """
    用 CZSC.to_echarts() 的 kline_pro 画 K 线，将符合「涨停回调支撑」的区间标在图上，
    并用 Tab 增加「形态区间」表（起始日期、结束日期）。输出为单个 HTML。
    """
    if not bars or kline_df is None or len(kline_df) < 60:
        logger.warning("数据不足，无法生成 K 线图")
        return
    try:
        from czsc.analyze import CZSC
        from czsc.utils.echarts_plot import kline_pro
        from pyecharts.charts import Tab
        from pyecharts.components import Table
        from pyecharts.options import ComponentTitleOpts
    except ImportError as e:
        logger.warning(f"依赖缺失，无法生成图表: {e}")
        return

    czsc = CZSC(bars)
    kline = [
        {
            "dt": b.dt,
            "open": float(b.open),
            "close": float(b.close),
            "high": float(b.high),
            "low": float(b.low),
            "vol": float(getattr(b, "vol", 0) or getattr(b, "volume", 0)),
        }
        for b in czsc.bars_raw
    ]
    if len(czsc.bi_list) > 0:
        bi = [
            {"dt": x.fx_a.dt, "bi": x.fx_a.fx}
            for x in czsc.bi_list
        ] + [{"dt": czsc.bi_list[-1].fx_b.dt, "bi": czsc.bi_list[-1].fx_b.fx}]
        fx = [{"dt": x.dt, "fx": x.fx} for x in czsc.fx_list]
    else:
        bi = []
        fx = []

    ranges = find_all_limit_pullback_ranges(kline_df)
    pattern_zs = []
    for (s, e) in ranges:
        sub = kline_df[(kline_df["dt"] >= s) & (kline_df["dt"] <= e)]
        if len(sub) > 0:
            pattern_zs.append({
                "sdt": s,
                "edt": e,
                "zg": float(sub["high"].max()),
                "zd": float(sub["low"].min()),
            })

    chart = kline_pro(
        kline,
        bi=bi,
        fx=fx,
        zs=pattern_zs,
        width=width,
        height=height,
        title=f"{symbol} 涨停回调支撑",
    )

    table_headers = ["起始日期", "结束日期"]
    table_rows = []
    for (s, e) in ranges:
        s_str = s.strftime("%Y-%m-%d") if hasattr(s, "strftime") else str(pd.Timestamp(s))[:10]
        e_str = e.strftime("%Y-%m-%d") if hasattr(e, "strftime") else str(pd.Timestamp(e))[:10]
        table_rows.append([s_str, e_str])
    if not table_rows:
        table_rows = [["无", "无"]]
    t = Table()
    t.add(table_headers, table_rows)
    t.set_global_opts(
        title_opts=ComponentTitleOpts(title="涨停回调支撑 形态区间", subtitle="符合该模式的所有起始日期与结束日期")
    )

    tab = Tab()
    tab.add(chart, "K线图")
    tab.add(t, "形态区间")
    out = output_path.with_suffix(".html")
    tab.render(str(out))
    logger.info(f"K 线图+形态区间已保存: {out}")


def load_stock_basic() -> tuple:
    """
    从 metadata/stock_basic.csv 读取全量 A 股：symbol 列表 + symbol->name 映射。
    仅保留 list_date 有效且代码为 SH/SZ 的标的。
    :return: (symbols: List[str], symbol_to_name: Dict[str, str])
    """
    import csv
    symbols = []
    symbol_to_name = {}
    if not STOCK_BASIC_CSV.exists():
        logger.warning(f"stock_basic 不存在: {STOCK_BASIC_CSV}，将无名称且无全量列表")
        return [], {}
    try:
        with open(STOCK_BASIC_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = (row.get("symbol") or "").strip().upper()
                if not symbol or not symbol.endswith((".SH", ".SZ")):
                    continue
                list_date = (row.get("list_date") or "").strip()
                if len(list_date) < 8 or not list_date[:8].isdigit():
                    continue
                name = (row.get("name") or "").strip() or symbol
                symbol_to_name[symbol] = name
                symbols.append(symbol)
    except Exception as e:
        logger.warning(f"读取 stock_basic 失败: {STOCK_BASIC_CSV} - {e}")
    return sorted(symbols), symbol_to_name


def compute_one(symbol: str, sdt: str = SDT, edt: str = None):
    """
    对单只股票用日线数据计算四策略信号，返回一行的字典；失败返回 None。
    edt 默认当天（数据源有今日则到今日，否则到最新可用日）。
    """
    if edt is None:
        edt = _default_edt()
    try:
        bars = research.get_raw_bars_daily(
            symbol=symbol, freq=Freq.D, sdt=sdt, edt=edt
        )
        if not bars or len(bars) < INIT_N + 50:
            return None

        bg = BarGenerator(base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value])
        for bar in bars:
            bg.update(bar)

        cs = CzscSignals(bg=bg, signals_config=SIGNALS_CONFIG)

        # 回放收集三买/三卖日期
        bg_replay = BarGenerator(
            base_freq=Freq.D.value, freqs=[Freq.D.value, Freq.W.value]
        )
        for bar in bars[:INIT_N]:
            bg_replay.update(bar)

        third_buy_dates = []
        third_sell_dates = []
        for bar in bars[INIT_N:]:
            bg_replay.update(bar)
            cs_replay = CzscSignals(bg=bg_replay, signals_config=SIGNALS_CONFIG)
            for k, v in cs_replay.s.items():
                if not isinstance(k, str) or v is None:
                    continue
                v_str = str(v)
                if "形态V230619" in k and "类三买" in v_str:
                    third_buy_dates.append(bar.dt)
                    break
            for k, v in cs_replay.s.items():
                if not isinstance(k, str) or v is None:
                    continue
                v_str = str(v)
                if "形态V230619" in k and "类三卖" in v_str:
                    third_sell_dates.append(bar.dt)
                    break

        # 当前信号
        signals = cs.s
        ma_bull = False
        ma_bear = False
        third_buy_now = False
        third_sell_now = False
        for k, v in signals.items():
            if not isinstance(k, str) or v is None:
                continue
            v_str = str(v)
            if "BS辅助V230313" in k:
                if "看多" in v_str:
                    ma_bull = True
                if "看空" in v_str:
                    ma_bear = True
            if "形态V230619" in k and "类三买" in v_str:
                third_buy_now = True
            if "形态V230619" in k and "类三卖" in v_str:
                third_sell_now = True

        if (ma_bull or third_buy_now) and not (ma_bear or third_sell_now):
            conclusion = "看多"
        elif (ma_bear or third_sell_now) and not (ma_bull or third_buy_now):
            conclusion = "看空"
        else:
            conclusion = "震荡"

        end_dt = cs.end_dt
        latest_price = cs.latest_price
        if end_dt is None:
            end_dt = bars[-1].dt if bars else None
        if latest_price is None and bars:
            latest_price = bars[-1].close

        def _last_dates(dates, n=5):
            return [d.strftime("%Y-%m-%d") for d in dates[-n:]]

        # 涨停后回调至支撑位形态
        kline_df = _bars_to_klinedf(bars)
        limit_pullback_support = find_limit_pullback_support(kline_df)

        return {
            "symbol": symbol,
            "end_dt": end_dt,
            "latest_price": latest_price,
            "conclusion": conclusion,
            "ma_bull": ma_bull,
            "ma_bear": ma_bear,
            "third_buy_now": third_buy_now,
            "third_sell_now": third_sell_now,
            "n_third_buy": len(third_buy_dates),
            "n_third_sell": len(third_sell_dates),
            "last_third_buy": _last_dates(third_buy_dates),
            "last_third_sell": _last_dates(third_sell_dates),
            "limit_pullback_support": limit_pullback_support,
        }
    except Exception as e:
        logger.debug(f"{symbol} 计算失败: {e}")
        return None


def build_html(rows: list, output_path: Path, build_time: str) -> None:
    """生成可按结论等排序的 HTML 文件。"""
    conclusion_order = {"看多": 0, "震荡": 1, "看空": 2}

    rows_json = []
    for r in rows:
        end_dt_str = r["end_dt"].strftime("%Y-%m-%d %H:%M") if r.get("end_dt") else ""
        price_str = f"{r.get('latest_price') or 0:.2f}"
        rows_json.append({
            "symbol": r["symbol"],
            "name": r.get("name") or r["symbol"],
            "end_dt": end_dt_str,
            "latest_price": price_str,
            "conclusion": r["conclusion"],
            "conclusion_order": conclusion_order.get(r["conclusion"], 1),
            "ma_bull": "是" if r.get("ma_bull") else "否",
            "ma_bear": "是" if r.get("ma_bear") else "否",
            "third_buy_now": "是" if r.get("third_buy_now") else "否",
            "third_sell_now": "是" if r.get("third_sell_now") else "否",
            "n_third_buy": r.get("n_third_buy", 0),
            "n_third_sell": r.get("n_third_sell", 0),
            "last_third_buy": ", ".join(r.get("last_third_buy") or []),
            "last_third_sell": ", ".join(r.get("last_third_sell") or []),
            "limit_pullback_support": "是" if r.get("limit_pullback_support") else "否",
        })

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>四策略信号扫描结果</title>
<style>
  body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
  h1 {{ color: #eee; }}
  .meta {{ color: #888; margin-bottom: 16px; }}
  .filter {{ margin-bottom: 12px; }}
  .filter label {{ margin-right: 8px; }}
  .filter select {{ padding: 6px 10px; background: #16213e; color: #eee; border: 1px solid #0f3460; border-radius: 4px; }}
  table {{ border-collapse: collapse; width: 100%; background: #16213e; }}
  th, td {{ border: 1px solid #0f3460; padding: 8px 12px; text-align: left; }}
  th {{ background: #0f3460; cursor: pointer; user-select: none; }}
  th:hover {{ background: #1a1a2e; }}
  tr:nth-child(even) {{ background: #1a1a2e; }}
  .conclusion-看多 {{ color: #4ade80; }}
  .conclusion-看空 {{ color: #f87171; }}
  .conclusion-震荡 {{ color: #fbbf24; }}
</style>
</head>
<body>
<h1>四策略信号扫描结果</h1>
<div class="meta">生成时间: {build_time} | 股票数: {len(rows)}</div>
<div class="filter">
  <label>按结论筛选:</label>
  <select id="filterConclusion" onchange="applyFilter()">
    <option value="">全部</option>
    <option value="看多">看多</option>
    <option value="看空">看空</option>
    <option value="震荡">震荡</option>
  </select>
  <label style="margin-left:16px">排序:</label>
  <select id="sortBy" onchange="sortTable()">
    <option value="conclusion">结论(看多→震荡→看空)</option>
    <option value="conclusion_desc">结论(看空→震荡→看多)</option>
    <option value="symbol">标的</option>
    <option value="name">名称</option>
    <option value="latest_price">最新价</option>
    <option value="n_third_buy">三买次数</option>
    <option value="n_third_sell">三卖次数</option>
    <option value="limit_pullback_support">涨停回调支撑</option>
  </select>
</div>
<table>
<thead>
<tr>
  <th data-sort="symbol">标的</th>
  <th data-sort="name">名称</th>
  <th data-sort="end_dt">结束时间</th>
  <th data-sort="latest_price">最新价</th>
  <th data-sort="conclusion">结论</th>
  <th data-sort="limit_pullback_support">涨停回调支撑</th>
  <th>均线看多</th>
  <th>均线看空</th>
  <th>类三买</th>
  <th>类三卖</th>
  <th data-sort="n_third_buy">三买次数</th>
  <th data-sort="n_third_sell">三卖次数</th>
  <th>三买最近日期</th>
  <th>三卖最近日期</th>
</tr>
</thead>
<tbody id="tbody">
"""
    for r in rows_json:
        cls = f"conclusion-{r['conclusion']}"
        name_esc = (r.get("name") or r["symbol"]).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html += f"""<tr data-conclusion="{r['conclusion']}">
  <td>{r['symbol']}</td>
  <td>{name_esc}</td>
  <td>{r['end_dt']}</td>
  <td>{r['latest_price']}</td>
  <td class="{cls}">{r['conclusion']}</td>
  <td>{r.get('limit_pullback_support', '否')}</td>
  <td>{r['ma_bull']}</td>
  <td>{r['ma_bear']}</td>
  <td>{r['third_buy_now']}</td>
  <td>{r['third_sell_now']}</td>
  <td>{r['n_third_buy']}</td>
  <td>{r['n_third_sell']}</td>
  <td>{r['last_third_buy']}</td>
  <td>{r['last_third_sell']}</td>
</tr>
"""
    html += """</tbody>
</table>
<script>
const rows = """ + __import__("json").dumps(rows_json, ensure_ascii=False) + """;

function getSortKey(r, key) {
  const order = { "看多": 0, "震荡": 1, "看空": 2 };
  if (key === "conclusion") return order[r.conclusion] ?? 1;
  if (key === "conclusion_desc") return -(order[r.conclusion] ?? 1);
  if (key === "latest_price") return parseFloat(r.latest_price) || 0;
  if (key === "n_third_buy") return r.n_third_buy;
  if (key === "n_third_sell") return r.n_third_sell;
  if (key === "name") return (r.name || "").toString();
  if (key === "limit_pullback_support") return (r.limit_pullback_support || "否") === "是" ? 1 : 0;
  return (r[key] || "").toString();
}

function sortTable() {
  const sel = document.getElementById("sortBy");
  const key = sel.value;
  const desc = key.endsWith("_desc");
  const k = desc ? key.replace("_desc", "") : key;
  rows.sort((a, b) => {
    const va = getSortKey(a, k);
    const vb = getSortKey(b, k);
    if (typeof va === "number" && typeof vb === "number") return desc ? vb - va : va - vb;
    return desc ? String(vb).localeCompare(va) : String(va).localeCompare(vb);
  });
  applyFilter();
}

function applyFilter() {
  const filter = document.getElementById("filterConclusion").value;
  const tbody = document.getElementById("tbody");
  tbody.innerHTML = "";
  const filtered = filter ? rows.filter(r => r.conclusion === filter) : rows;
  filtered.forEach(r => {
    const cls = "conclusion-" + r.conclusion;
    const tr = document.createElement("tr");
    tr.setAttribute("data-conclusion", r.conclusion);
    const name = (r.name || r.symbol || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const lps = r.limit_pullback_support || "否";
    tr.innerHTML = `<td>${r.symbol}</td><td>${name}</td><td>${r.end_dt}</td><td>${r.latest_price}</td><td class="${cls}">${r.conclusion}</td><td>${lps}</td><td>${r.ma_bull}</td><td>${r.ma_bear}</td><td>${r.third_buy_now}</td><td>${r.third_sell_now}</td><td>${r.n_third_buy}</td><td>${r.n_third_sell}</td><td>${r.last_third_buy}</td><td>${r.last_third_sell}</td>`;
    tbody.appendChild(tr);
  });
}

document.getElementById("sortBy").value = "conclusion";
sortTable();
</script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    logger.info(f"已写入: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="扫描全量股票（stock_basic）用日线生成四策略信号 HTML 报告")
    parser.add_argument("--stock", type=str, default=None, help="仅分析指定股票，输出 K 线图+形态区间 Tab，如 600078.SH")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 只股票（测试用）")
    parser.add_argument("--sdt", type=str, default=SDT, help="开始日期 YYYYMMDD")
    parser.add_argument("--edt", type=str, default=None, help="结束日期 YYYYMMDD，默认当天")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 HTML 路径，默认 demo/.results/signals6.html（分片时为 signals6_shard{i}_of{n}.html）",
    )
    parser.add_argument(
        "--shard",
        type=int,
        default=None,
        metavar="N",
        help="分片数 N：自动启动 N 个子进程并行跑数据，每片独立输出 HTML",
    )
    parser.add_argument("--shard-index", type=int, default=None, help="(内部)当前片索引，由 --shard 启动的子进程使用")
    parser.add_argument("--shard-total", type=int, default=None, help="(内部)总片数，由 --shard 启动的子进程使用")
    args = parser.parse_args()

    # 单股模式：--stock 时只输出 K 线图（标出符合形态区间）+ Tab「形态区间」表，不输出原表格 HTML
    if args.stock:
        symbol_raw = (args.stock or "").strip().upper()
        if not symbol_raw or "." not in symbol_raw:
            logger.error("--stock 需为 代码.市场，如 600078.SH、000001.SZ")
            return
        edt = args.edt or _default_edt()
        logger.info(f"单股分析: {symbol_raw}，日期范围 {args.sdt}～{edt}")
        bars = research.get_raw_bars_daily(
            symbol=symbol_raw, freq=Freq.D, sdt=args.sdt, edt=edt
        )
        if not bars or len(bars) < 60:
            logger.error(f"数据不足或无法获取: {symbol_raw}")
            return
        kline_df = _bars_to_klinedf(bars)
        out_path = Path(args.output) if args.output else (
            project_root / "demo" / ".results" / f"signals7_{symbol_raw.replace('.', '_')}.html"
        )
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _build_pattern_chart_and_tab(symbol_raw, bars, kline_df, out_path)
        print(f"K 线图+形态区间已生成: {out_path.absolute()}")
        return

    # 启动器模式：--shard N 时自动 spawn N 个子进程
    if args.shard is not None and args.shard > 0 and args.shard_index is None and args.shard_total is None:
        script = Path(__file__).resolve()
        edt = args.edt or _default_edt()
        cmd_base = [sys.executable, str(script), "--sdt", args.sdt, "--edt", edt]
        if args.limit is not None:
            cmd_base.extend(["--limit", str(args.limit)])
        procs = []
        for i in range(args.shard):
            cmd = cmd_base + ["--shard-index", str(i), "--shard-total", str(args.shard)]
            procs.append(subprocess.Popen(cmd, cwd=str(project_root)))
        for p in procs:
            p.wait()
        logger.info(f"分片 {args.shard} 个子进程已全部结束")
        return

    # 以下为单进程或子进程（worker）逻辑：以 stock_basic 全量为列表
    symbols, symbol_to_name = load_stock_basic()
    if not symbols:
        logger.error("未从 stock_basic 加载到任何股票，请检查 .stock_data/metadata/stock_basic.csv")
        return

    if args.limit:
        symbols = symbols[: args.limit]

    shard_index = args.shard_index
    shard_total = args.shard_total
    if shard_index is not None and shard_total is not None:
        if shard_total < 1 or shard_index < 0 or shard_index >= shard_total:
            logger.error(f"无效分片: --shard-index {shard_index} --shard-total {shard_total}")
            return
        symbols = [s for i, s in enumerate(symbols) if i % shard_total == shard_index]
        logger.info(f"分片 {shard_index + 1}/{shard_total}，本片 {len(symbols)} 只股票")

    edt = args.edt or _default_edt()
    logger.info(f"日期范围 {args.sdt}～{edt}，本进程共 {len(symbols)} 只待扫描")

    rows = []
    for i, symbol in enumerate(symbols, 1):
        if i % 50 == 0 or i == len(symbols):
            logger.info(f"进度 {i}/{len(symbols)}")
        row = compute_one(symbol, sdt=args.sdt, edt=edt)
        if row is not None:
            row["name"] = symbol_to_name.get(row["symbol"], row["symbol"])
            rows.append(row)

    logger.info(f"有效结果 {len(rows)} 条")

    if args.output:
        out_path = Path(args.output)
    elif shard_index is not None and shard_total is not None:
        out_path = project_root / "demo" / ".results" / f"signals6_shard{shard_index}_of_{shard_total}.html"
    else:
        out_path = project_root / "demo" / ".results" / "signals6.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_html(rows, out_path, build_time)
    print(f"报告已生成: {out_path.absolute()}")


if __name__ == "__main__":
    main()
