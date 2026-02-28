# -*- coding: utf-8 -*-
"""
扫描 raw/minute_by_stock 下所有股票，运行四策略信号，生成 HTML 报告。
支持按结论（看多/看空/震荡）排序、筛选。

# 在项目根目录、使用已安装 czsc/pandas 等依赖的 Python 环境运行
cd /Users/liyang/Desktop/npc-czsc

# 扫描全部股票（耗时会较长）
python demo/step2-signals/signals5.py

# 仅扫前 50 只（测试）
python demo/step2-signals/signals5.py --limit 50

# 指定日期与输出路径
python demo/step2-signals/signals5.py --sdt 20220101 --edt 20260212 --output demo/.results/signals5.html
"""
import os
import argparse
from pathlib import Path
from datetime import datetime

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
import sys
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from czsc.traders import CzscSignals
from czsc.utils import BarGenerator
from czsc.objects import Freq
from czsc.connectors import research

# minute_by_stock 所在目录（与 research 一致）
cache_path = os.environ.get("czsc_research_cache", str(project_root / ".stock_data" / "raw"))
MINUTE_ROOT = Path(cache_path) / "minute_by_stock"

MA_NAME = "SMA#40"
SDT = "20200101"
EDT = "20260212"
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


def get_symbols_from_minute_stock():
    """从 raw/minute_by_stock 下列出所有股票代码。"""
    if not MINUTE_ROOT.exists():
        logger.warning(f"minute_by_stock 不存在: {MINUTE_ROOT}")
        return []
    symbols = []
    for d in MINUTE_ROOT.iterdir():
        if d.is_dir() and d.name.startswith("stock_code="):
            symbols.append(d.name.replace("stock_code=", ""))
    return sorted(symbols)


def compute_one(symbol: str, sdt: str = SDT, edt: str = EDT):
    """
    对单只股票计算四策略信号，返回一行的字典；失败返回 None。
    """
    try:
        bars = research.get_raw_bars_minute(
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
    <option value="latest_price">最新价</option>
    <option value="n_third_buy">三买次数</option>
    <option value="n_third_sell">三卖次数</option>
  </select>
</div>
<table>
<thead>
<tr>
  <th data-sort="symbol">标的</th>
  <th data-sort="end_dt">结束时间</th>
  <th data-sort="latest_price">最新价</th>
  <th data-sort="conclusion">结论</th>
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
        html += f"""<tr data-conclusion="{r['conclusion']}">
  <td>{r['symbol']}</td>
  <td>{r['end_dt']}</td>
  <td>{r['latest_price']}</td>
  <td class="{cls}">{r['conclusion']}</td>
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
    tr.innerHTML = `<td>${r.symbol}</td><td>${r.end_dt}</td><td>${r.latest_price}</td><td class="${cls}">${r.conclusion}</td><td>${r.ma_bull}</td><td>${r.ma_bear}</td><td>${r.third_buy_now}</td><td>${r.third_sell_now}</td><td>${r.n_third_buy}</td><td>${r.n_third_sell}</td><td>${r.last_third_buy}</td><td>${r.last_third_sell}</td>`;
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
    parser = argparse.ArgumentParser(description="扫描 minute_by_stock 下所有股票，生成四策略信号 HTML 报告")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 只股票（测试用）")
    parser.add_argument("--sdt", type=str, default=SDT, help="开始日期 YYYYMMDD")
    parser.add_argument("--edt", type=str, default=EDT, help="结束日期 YYYYMMDD")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出 HTML 路径，默认 demo/.results/signals5.html",
    )
    args = parser.parse_args()

    symbols = get_symbols_from_minute_stock()
    if not symbols:
        logger.error("未找到任何股票，请检查 minute_by_stock 路径")
        return

    if args.limit:
        symbols = symbols[: args.limit]
    logger.info(f"共 {len(symbols)} 只股票待扫描")

    rows = []
    for i, symbol in enumerate(symbols, 1):
        if i % 50 == 0 or i == len(symbols):
            logger.info(f"进度 {i}/{len(symbols)}")
        row = compute_one(symbol, sdt=args.sdt, edt=args.edt)
        if row is not None:
            rows.append(row)

    logger.info(f"有效结果 {len(rows)} 条")

    out_path = args.output or (project_root / "demo" / ".results" / "signals5.html")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    build_html(rows, out_path, build_time)
    print(f"报告已生成: {out_path.absolute()}")


if __name__ == "__main__":
    main()
