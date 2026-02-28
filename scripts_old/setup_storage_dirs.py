#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建存储目录结构脚本（新架构）

根据新架构设计创建完整的目录结构

功能说明:
- 创建新架构的分层存储目录结构
- 包括原始数据层、加工数据层、缓存层、模型层、配置层、元数据层
- 数据存储根目录：stock_data/

目录结构:
  stock_data/
  ├── raw/                    # 原始数据层（双分区）
  ├── processed/              # 加工数据层
  ├── cache/                  # 缓存层
  ├── models/                 # 模型层
  ├── config/                 # 配置层
  └── metadata/               # 元数据层

使用示例:
  python scripts/setup_storage_dirs.py

替代关系:
- 替代了setup_minute_data_dirs.py（旧架构，创建data/上证等目录）
"""
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def create_all_directories() -> bool:
    """创建所有必需的目录结构"""
    logger.info("=" * 80)
    logger.info("创建存储目录结构")
    logger.info("=" * 80)
    
    # 存储根目录
    storage_root = project_root / ".stock_data"
    
    # 定义目录结构
    directories = [
        # 原始数据层
        storage_root / "raw" / "minute_by_date",
        storage_root / "raw" / "minute_by_stock",
        storage_root / "raw" / "daily" / "by_date",
        storage_root / "raw" / "daily" / "by_stock",
        
        # 加工数据层
        storage_root / "processed" / "indicators_daily",
        storage_root / "processed" / "minute_features",
        storage_root / "processed" / "factors" / "momentum",
        storage_root / "processed" / "factors" / "value",
        storage_root / "processed" / "factors" / "quality",
        storage_root / "processed" / "derived" / "cross_sectional",
        storage_root / "processed" / "derived" / "time_series",
        
        # 缓存层
        storage_root / "cache" / "duckdb",
        storage_root / "cache" / "redis",
        storage_root / "cache" / "precomputed" / "correlations",
        storage_root / "cache" / "precomputed" / "returns",
        storage_root / "cache" / "precomputed" / "volatility",
        
        # 模型层
        storage_root / "models" / "ml_models" / "trained" / "xgboost",
        storage_root / "models" / "ml_models" / "trained" / "lightgbm",
        storage_root / "models" / "ml_models" / "trained" / "neural_networks",
        storage_root / "models" / "ml_models" / "predictions",
        storage_root / "models" / "ml_models" / "features",
        storage_root / "models" / "backtest" / "strategies" / "trend_following",
        storage_root / "models" / "backtest" / "strategies" / "mean_reversion",
        storage_root / "models" / "backtest" / "strategies" / "arbitrage",
        storage_root / "models" / "backtest" / "results" / "equity_curves",
        storage_root / "models" / "backtest" / "results" / "performance",
        storage_root / "models" / "backtest" / "results" / "trades",
        storage_root / "models" / "backtest" / "reports",
        storage_root / "models" / "optimization" / "parameter_grids",
        storage_root / "models" / "optimization" / "best_params",
        
        # 配置层
        storage_root / "config" / "stocks",
        storage_root / "config" / "stocks" / "sectors",
        storage_root / "config" / "indicators" / "custom",
        storage_root / "config" / "strategies" / "params",
        storage_root / "config" / "strategies" / "signals",
        
        # 元数据层
        storage_root / "metadata" / "schema_registry",
        storage_root / "metadata" / "quality",
        storage_root / "metadata" / "lineage",
    ]
    
    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ {directory.relative_to(project_root)}")
            created_count += 1
        except Exception as e:
            logger.error(f"✗ 创建目录失败: {directory}, 错误: {e}")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"✅ 目录结构创建完成，共创建 {created_count} 个目录")
    logger.info("=" * 80)
    
    return True


def main():
    """主函数"""
    try:
        create_all_directories()
        return 0
    except Exception as e:
        logger.error(f"❌ 创建目录结构失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
