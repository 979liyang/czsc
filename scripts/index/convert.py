#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定股票的分钟数据 parquet 文件批量转换为 CSV；支持 --fetch 检测所有股票并请求缺失/尾段数据。

功能：
- 自动检测 raw/daily/stock_code={code} 下的所有 parquet 文件
- 转换为 CSV 并保存到指定输出目录（保持目录结构或扁平化）
- --fetch：检测所有股票（或 --index 指定一只），对缺失月份及“最后一天到当天”的尾段请求数据

使用示例：
  # 转换 600078.SH 的所有 parquet 文件
  python scripts/index/convert.py --index 000001.SH     

  # 检测所有股票并请求缺失/尾段数据（不指定 --index 即扫描 daily 下全部）
  python scripts/index/convert.py --fetch

  # 指定输出目录
  python scripts/index/convert.py --index 000001.SH --output-dir ./csv_output

  # 扁平化输出
  python scripts/index/convert.py --index 000001.SH --flatten
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd
from loguru import logger

# 添加项目根目录与 scripts 到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
scripts_dir = project_root / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

BASE_PATH = project_root / ".stock_data"
FETCH_SCRIPT = project_root / "scripts" / "minute" / "fetch"


def find_all_parquet_files(stock_code: str, base_path: Path = None) -> List[Path]:
    """查找指定股票目录下的所有 parquet 文件"""
    base_path = base_path or project_root / ".stock_data"
    base_dir = base_path / "raw" / "daily" / "by_stock" / f"stock_code={stock_code}"
    if not base_dir.exists():
        logger.error(f"目录不存在: {base_dir}")
        return []
    
    parquet_files = sorted(base_dir.rglob("*.parquet"))
    logger.info(f"找到 {len(parquet_files)} 个 parquet 文件")
    return parquet_files


def convert_parquet_to_csv(parquet_path: Path, csv_path: Path) -> bool:
    """将单个 parquet 文件转换为 CSV"""
    try:
        df = pd.read_parquet(parquet_path)
        if df is None or len(df) == 0:
            logger.warning(f"文件为空，跳过: {parquet_path}")
            return False
        
        # 确保输出目录存在
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为 CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ 转换成功: {parquet_path.name} → {csv_path} ({len(df)} 行)")
        return True
    except Exception as e:
        logger.error(f"❌ 转换失败: {parquet_path} - {e}")
        return False


def convert_with_structure(parquet_files: List[Path], output_base: Path, stock_code: str) -> int:
    """保持目录结构转换（year=xxx/xxx.csv）"""
    success_count = 0
    for parquet_path in parquet_files:
        # 计算相对路径（相对于 stock_code=xxx 目录）
        rel_path = parquet_path.relative_to(parquet_path.parents[2])
        csv_path = output_base / rel_path.with_suffix('.csv')
        if convert_parquet_to_csv(parquet_path, csv_path):
            success_count += 1
    return success_count


def convert_flattened(parquet_files: List[Path], output_dir: Path) -> int:
    """扁平化转换（所有 CSV 放在同一目录）"""
    success_count = 0
    for parquet_path in parquet_files:
        # 生成扁平化文件名：year=2024_600078.SH_2024-01.csv
        parts = parquet_path.parts
        year_part = [p for p in parts if p.startswith('year=')][0] if any(p.startswith('year=') for p in parts) else 'unknown'
        file_name = f"{year_part}_{parquet_path.name}".replace('=', '_').replace('.parquet', '.csv')
        csv_path = output_dir / file_name
        if convert_parquet_to_csv(parquet_path, csv_path):
            success_count += 1
    return success_count


def run_fetch_all(args) -> None:
    """检测所有股票（或 --index 指定的一只）并请求缺失月份及尾段数据。"""
    import check_loacal_stock_new as check_mod

    base_path = BASE_PATH
    if not base_path.exists():
        logger.error(f"数据根目录不存在: {base_path}")
        return

    list_dates = check_mod.load_list_dates_from_stock_basic(base_path)
    first_trading_days = check_mod.get_first_trading_days_by_month()

    if args.stock:
        stocks = [args.stock.upper()]
        logger.info(f"检测并补拉指定股票: {stocks[0]}")
    else:
        stocks = check_mod.list_stocks_from_dirs(base_path)
        if not stocks:
            logger.warning("未扫描到任何股票目录")
            return
        logger.info(f"检测并补拉全部股票，共 {len(stocks)} 只")

    freq = getattr(args, "freq", "1min")
    token = getattr(args, "token", None)
    sleep = getattr(args, "sleep", 0.0)

    for i, stock_code in enumerate(stocks, 1):
        if i % 50 == 0 or i == len(stocks):
            logger.info(f"进度 {i}/{len(stocks)}")
        list_date = list_dates.get(stock_code)
        existing, expected, missing = check_mod.check_stock(
            stock_code, base_path, None, None,
            list_date=list_date, check_9am=False, first_trading_days=first_trading_days,
        )
        for y, m in missing:
            if FETCH_SCRIPT.exists():
                check_mod.run_fetch_for_missing_month(
                    stock_code, y, m, freq, FETCH_SCRIPT, token=token, sleep=sleep,
                )
        last_local = check_mod.get_last_local_date(stock_code, base_path)
        today_yyyymmdd = datetime.now().strftime("%Y%m%d")
        if last_local and last_local < today_yyyymmdd:
            next_d = (datetime.strptime(last_local[:8], "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
            if check_mod.has_trading_days_between(next_d, today_yyyymmdd):
                logger.warning(f"{stock_code}: 本地最后 {last_local} 至当天仍有交易日，补拉尾段")
                if FETCH_SCRIPT.exists():
                    check_mod.run_fetch_for_range(
                        stock_code, next_d, today_yyyymmdd, freq, FETCH_SCRIPT,
                        token=token, sleep=sleep,
                    )
    logger.info("检测与请求数据阶段结束")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量将分钟数据 parquet 转换为 CSV；支持 --fetch 检测并请求数据")
    parser.add_argument('--index', type=str, default=None, help='股票代码（如：600078.SH）；与 --fetch 同用时可选，仅 fetch 时可不传以检测全部')
    parser.add_argument('--output-dir', type=str, default=None, help='输出目录（默认：项目根目录/csv_output/{stock_code}）')
    parser.add_argument('--flatten', action='store_true', help='扁平化输出（所有 CSV 放在同一目录）')
    parser.add_argument('--fetch', action='store_true', help='检测所有股票（或 --index 指定的一只）并请求缺失/尾段数据')
    parser.add_argument('--freq', type=str, default='1min', help='--fetch 时传给 fetch 脚本的分钟周期')
    parser.add_argument('--token', type=str, default=None, help='--fetch 时传给 fetch 的 token（可选）')
    parser.add_argument('--sleep', type=float, default=0, help='--fetch 时每只股票间隔秒数')

    args = parser.parse_args()

    if args.fetch:
        run_fetch_all(args)
        if not args.stock:
            logger.info("未指定 --index，仅执行了检测与请求数据；若需转换 CSV 请指定 --index 再运行")
            return

    stock_code = (args.stock or "").upper()
    if not stock_code or "." not in stock_code:
        if not args.fetch:
            logger.error("请指定 --index（如：600078.SH），或使用 --fetch 检测并请求所有股票数据")
        return

    # 查找所有 parquet 文件
    parquet_files = find_all_parquet_files(stock_code, BASE_PATH)
    if not parquet_files:
        logger.error(f"未找到任何 parquet 文件: {stock_code}")
        return

    # 确定输出目录
    if args.output_dir:
        output_base = Path(args.output_dir)
    else:
        output_base = project_root / "csv_output" / stock_code

    output_base.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_base}")

    # 执行转换
    if args.flatten:
        success_count = convert_flattened(parquet_files, output_base)
    else:
        success_count = convert_with_structure(parquet_files, output_base, stock_code)

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"转换完成：成功 {success_count}/{len(parquet_files)} 个文件")
    logger.info(f"输出目录: {output_base}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
