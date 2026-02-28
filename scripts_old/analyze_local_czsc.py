#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于本地 `.stock_data` 数据进行 CZSC 分析并生成 HTML 图表报告。

说明：
- 分析逻辑参考 `demo/analyze.py`
- 数据读取复用 `scripts/get_stock_data.py` 的 `get_raw_bars`（确保与 CZSC 对接一致）

使用示例：
  # 分析本地 1 分钟数据并生成 HTML
  python scripts/analyze_local_czsc.py --symbol 600078.SH --freq 1分钟 --sdt 20180101 --edt 20181231

  # 分析日线
  python scripts/analyze_local_czsc.py --symbol 600078.SH --freq 日线 --sdt 20200101 --edt 20231231

  # 使用 BarGenerator：先以 1分钟 为基础合成 5/15/30/60分钟，再分别分析并生成多个 HTML（输出元数据）
  python scripts/analyze_local_czsc.py --symbol 600078.SH --base-freq 1分钟 --freqs 1,5,15,30,60 --sdt 20180101 --edt 20181231
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _parse_args():
    """解析命令行参数"""
    p = argparse.ArgumentParser(description="本地数据 CZSC 分析并生成 HTML")
    p.add_argument("--symbol", required=True, type=str, help="标的代码，如 600078.SH")
    p.add_argument("--freq", required=False, type=str, default=None, help="周期，如 1分钟 / 30分钟 / 日线")
    p.add_argument("--base-freq", type=str, default="1分钟", help="BarGenerator 基础周期（默认 1分钟）")
    p.add_argument("--freqs", type=str, default=None, help="分钟周期列表（逗号分隔），用于 BarGenerator 多周期分析，如 1,5,15,30,60")
    p.add_argument("--include-indicators", action="store_true", help="输出 vol/sma/macd 指标元数据（用于 TradingVue 对照）")
    p.add_argument("--sdt", required=True, type=str, help="开始时间，如 20180101")
    p.add_argument("--edt", required=True, type=str, help="结束时间，如 20181231")
    p.add_argument("--base-path", type=str, default=None, help="本地存储根目录（默认：项目根目录/.stock_data）")
    p.add_argument("--out-dir", type=str, default=None, help="输出目录（默认：项目根目录/.results）")
    p.add_argument("--width", type=str, default="1400px", help="图表宽度（默认 1400px）")
    p.add_argument("--height", type=str, default="580px", help="图表高度（默认 580px）")
    return p.parse_args()


def _ensure_out_dir(out_dir: Optional[str]) -> Path:
    """获取输出目录并确保存在"""
    d = Path(out_dir) if out_dir else (project_root / ".results")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _build_out_file(out_dir: Path, symbol: str) -> Path:
    """构建输出文件路径"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"czsc_chart_local_{symbol}_{ts}.html"
    return out_dir / name


def _normalize_freqs(freqs: str) -> List[str]:
    """将 1,5,15,30,60 转为 ['1分钟','5分钟',...]"""
    parts = [p.strip() for p in str(freqs or "").split(",") if p.strip()]
    mins = sorted({int(p) for p in parts if p.isdigit() and int(p) in {1, 5, 15, 30, 60}})
    return [f"{m}分钟" for m in mins]


def _freq_minutes(freq_value: str) -> int:
    """将周期字符串映射为分钟数"""
    if freq_value == "日线":
        return 1440
    if freq_value.endswith("分钟"):
        return int(freq_value.replace("分钟", ""))
    return 10**9


def _validate_targets(base_freq: str, targets: List[str]) -> List[str]:
    """过滤掉小于 base_freq 的周期"""
    base_m = _freq_minutes(base_freq)
    out: List[str] = []
    for f in targets:
        if _freq_minutes(f) < base_m:
            logger.warning(f"目标周期 {f} 小于 base_freq {base_freq}，已跳过")
            continue
        out.append(f)
    return out


def _build_base_bars(minute_bars: list, base_freq: str) -> list:
    """从 1分钟 bars 合成 base_freq bars"""
    from czsc.utils import BarGenerator

    if base_freq == "1分钟":
        return minute_bars
    bg = BarGenerator(base_freq="1分钟", freqs=[base_freq])
    for bar in minute_bars:
        bg.update(bar)
    return bg.bars.get(base_freq, [])


def _build_multi_bars(base_bars: list, base_freq: str, targets: List[str]) -> Dict[str, list]:
    """用 BarGenerator 从 base_freq 合成 targets 周期 bars"""
    from czsc.utils import BarGenerator

    freqs = [f for f in targets if f != base_freq]
    bg = BarGenerator(base_freq=base_freq, freqs=freqs)
    for bar in base_bars:
        bg.update(bar)
    out: Dict[str, list] = {base_freq: bg.bars.get(base_freq, []) or base_bars}
    for f in freqs:
        out[f] = bg.bars.get(f, [])
    return out


def _calc_indicators(bars: list) -> dict:
    """计算 to_echarts 默认指标元数据（vol/sma/macd）"""
    if not bars:
        return {}
    import numpy as np
    from czsc.utils.ta import SMA, MACD

    close = np.array([b.close for b in bars], dtype=np.double)
    vol = [[int(b.dt.timestamp() * 1000), float(b.vol)] for b in bars]
    diff, dea, macd = MACD(close)
    macd_series = [[int(bars[i].dt.timestamp() * 1000), float(diff[i]), float(dea[i]), float(macd[i])] for i in range(len(bars))]
    sma = {}
    for p in [5, 13, 21]:
        ma = SMA(close, timeperiod=p)
        sma[f"MA{p}"] = [[int(bars[i].dt.timestamp() * 1000), float(ma[i])] for i in range(len(bars))]
    return {"vol": vol, "macd": macd_series, "sma": sma}


def _print_stats(czsc_obj) -> None:
    """打印 CZSC 对象关键统计信息"""
    logger.info(f"{len(czsc_obj.bars_raw)} 原始K线列表")
    logger.info(f"{len(czsc_obj.bars_ubi)} 未完成笔K线列表")
    logger.info(f"{len(czsc_obj.fx_list)} 分型列表")
    logger.info(f"{len(czsc_obj.finished_bis)} 已完成笔列表")
    logger.info(f"{len(czsc_obj.bi_list)} 所有笔列表（含未完成）")
    logger.info(f"{1 if czsc_obj.ubi else 0} 未完成的笔")
    logger.info(f"{czsc_obj.last_bi_extend} 最后一笔是否在延伸")


def main():
    """命令行入口"""
    args = _parse_args()
    from czsc.analyze import CZSC
    from scripts.get_stock_data import get_raw_bars

    out_dir = _ensure_out_dir(args.out_dir)
    if args.freqs:
        minute_bars = get_raw_bars(
            symbol=args.symbol,
            freq="1分钟",
            sdt=args.sdt,
            edt=args.edt,
            base_path=args.base_path,
            raw_bars=True,
        )
        if not minute_bars:
            logger.error("未读取到任何 1分钟 数据，无法进行多周期合成")
            raise SystemExit(1)
        base_freq = args.base_freq
        targets = _validate_targets(base_freq, _normalize_freqs(args.freqs))
        base_bars = _build_base_bars(minute_bars, base_freq)
        if not base_bars:
            logger.error(f"base_freq={base_freq} 合成后 bars 为空，无法继续")
            raise SystemExit(1)
        bars_map = _build_multi_bars(base_bars, base_freq, targets)
        meta = {
            "symbol": args.symbol,
            "sdt": args.sdt,
            "edt": args.edt,
            "base_freq": base_freq,
            "targets": targets,
            "counts": {k: len(v) for k, v in bars_map.items()},
        }
        logger.info(f"meta: {meta}")
        for f, bars in bars_map.items():
            if not bars:
                logger.warning(f"{f} bars 为空，跳过生成图表")
                continue
            if args.include_indicators:
                ind = _calc_indicators(bars)
                logger.info(
                    f"{f} indicators: vol={len(ind.get('vol', []))} macd={len(ind.get('macd', []))} sma_keys={list((ind.get('sma') or {}).keys())}"
                )
            out_file = _build_out_file(out_dir, f"{args.symbol}_{f}")
            czsc_obj = CZSC(bars)
            logger.info(f"=== {f} ===")
            _print_stats(czsc_obj)
            chart = czsc_obj.to_echarts(width=args.width, height=args.height)
            chart.render(str(out_file))
            logger.info(f"✓ 图表已保存到: {out_file.absolute()}")
        return

    if not args.freq:
        logger.error("请提供 --freq 或 --freqs")
        raise SystemExit(2)

    out_file = _build_out_file(out_dir, args.symbol)
    bars = get_raw_bars(symbol=args.symbol, freq=args.freq, sdt=args.sdt, edt=args.edt, base_path=args.base_path, raw_bars=True)
    if not bars:
        logger.error("未读取到任何 K 线数据，无法生成图表")
        raise SystemExit(1)
    if args.include_indicators:
        ind = _calc_indicators(bars)
        logger.info(
            f"{args.freq} indicators: vol={len(ind.get('vol', []))} macd={len(ind.get('macd', []))} sma_keys={list((ind.get('sma') or {}).keys())}"
        )
    czsc_obj = CZSC(bars)
    _print_stats(czsc_obj)
    chart = czsc_obj.to_echarts(width=args.width, height=args.height)
    chart.render(str(out_file))
    logger.info(f"✓ 图表已保存到: {out_file.absolute()}")
    logger.info("  请在浏览器中打开该文件查看图表")


if __name__ == "__main__":
    main()

