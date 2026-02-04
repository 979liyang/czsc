#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定股票的分钟数据 parquet 文件批量转换为 CSV

功能：
- 自动检测 raw/minute_by_stock/stock_code={code} 下的所有 parquet 文件
- 转换为 CSV 并保存到指定输出目录（保持目录结构或扁平化）

使用示例：
  # 转换 600078.SH 的所有 parquet 文件
  python scripts/convert_minute_parquet_to_csv.py --stock 600078.SH

  # 指定输出目录
  python scripts/convert_minute_parquet_to_csv.py --stock 600078.SH --output-dir ./csv_output

  # 扁平化输出（所有 CSV 放在同一目录，文件名包含路径信息）
  python scripts/convert_minute_parquet_to_csv.py --stock 600078.SH --flatten
"""

import argparse
import sys
from pathlib import Path
from typing import List

import pandas as pd
from loguru import logger

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def find_all_parquet_files(stock_code: str) -> List[Path]:
    """查找指定股票目录下的所有 parquet 文件"""
    base_dir = project_root / ".stock_data" / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="批量将分钟数据 parquet 转换为 CSV")
    parser.add_argument('--stock', type=str, required=True, help='股票代码（如：600078.SH）')
    parser.add_argument('--output-dir', type=str, default=None, help='输出目录（默认：项目根目录/csv_output/{stock_code}）')
    parser.add_argument('--flatten', action='store_true', help='扁平化输出（所有 CSV 放在同一目录）')
    
    args = parser.parse_args()
    
    stock_code = args.stock.upper()
    if '.' not in stock_code:
        logger.error(f"股票代码格式错误，应为：代码.市场（如：600078.SH）")
        return
    
    # 查找所有 parquet 文件
    parquet_files = find_all_parquet_files(stock_code)
    if not parquet_files:
        logger.error(f"未找到任何 parquet 文件")
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
