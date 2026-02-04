# -*- coding: utf-8 -*-
"""
存储管理器

提供分区数据的读写功能
"""
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from loguru import logger

from backend.utils.partition_utils import PartitionPathGenerator
from backend.utils.compression_config import get_parquet_write_options, get_parquet_engine_options


class StorageManager:
    """存储管理器基类"""
    
    def __init__(self, base_path: Path = None):
        """
        初始化存储管理器
        
        :param base_path: 基础路径，默认为项目根目录下的stock_data文件夹
        """
        if base_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / ".stock_data"
        else:
            self.base_path = Path(base_path)
        
        self.partition_generator = PartitionPathGenerator(self.base_path)
        logger.debug(f"存储管理器初始化，基础路径: {self.base_path}")
    
    def get_partition_path(
        self,
        data_type: str,
        partition_strategy: str,
        **kwargs
    ) -> Path:
        """
        获取分区路径
        
        :param data_type: 数据类型（'minute', 'daily'）
        :param partition_strategy: 分区策略（'by_date', 'by_stock'）
        :param kwargs: 其他参数
        :return: 分区路径
        """
        return self.partition_generator.get_file_path(data_type, partition_strategy, **kwargs)
    
    def write_partitioned_data(
        self,
        df: pd.DataFrame,
        data_type: str,
        partition_strategy: str,
        file_name: str = None,
        **kwargs
    ) -> bool:
        """
        写入分区数据
        
        :param df: 要写入的DataFrame
        :param data_type: 数据类型（'minute', 'daily'）
        :param partition_strategy: 分区策略（'by_date', 'by_stock'）
        :param file_name: 文件名（可选，如果不提供则使用默认命名）
        :param kwargs: 其他参数（用于生成分区路径）
        :return: 是否成功
        """
        try:
            # 获取分区路径
            partition_path = self.get_partition_path(data_type, partition_strategy, **kwargs)
            
            # 确保目录存在
            if file_name:
                file_path = partition_path / file_name
            else:
                # 默认文件名
                if partition_strategy == "by_date":
                    file_path = partition_path / "part-00000.parquet"
                else:
                    # by_stock策略：检查 partition_path 是否已经是文件路径
                    # generate_stock_partition_path 在提供 month 时会返回文件路径
                    if partition_path.suffix == '.parquet':
                        # 已经是文件路径，直接使用
                        file_path = partition_path
                    else:
                        # 是目录路径，需要生成文件名
                        if data_type == "minute" and "stock_code" in kwargs and "year" in kwargs and "month" in kwargs:
                            stock_code = kwargs['stock_code']
                            year = kwargs['year']
                            month = kwargs['month']
                            file_name = f"{stock_code}_{year}-{month:02d}.parquet"
                            file_path = partition_path / file_name
                        else:
                            # 无法生成文件名，使用默认
                            file_path = partition_path
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 获取压缩配置
            write_options = get_parquet_write_options(data_type)
            engine_options = get_parquet_engine_options()
            
            # 写入文件
            df.to_parquet(
                file_path,
                index=False,
                **write_options,
                **engine_options
            )
            
            logger.debug(f"写入分区数据成功: {file_path}，共 {len(df)} 条记录")
            return True
        except Exception as e:
            logger.error(f"写入分区数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_partitioned_data(
        self,
        data_type: str,
        partition_strategy: str,
        file_name: str = None,
        **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        读取分区数据
        
        :param data_type: 数据类型（'minute', 'daily'）
        :param partition_strategy: 分区策略（'by_date', 'by_stock'）
        :param file_name: 文件名（可选）
        :param kwargs: 其他参数（用于生成分区路径）
          - 日线数据按股票分区：必须提供 year（新格式按年份分区）
        :return: DataFrame或None
        """
        try:
            # 日线数据按股票分区：强制使用新格式（按年份），year 必填
            if data_type == "daily" and partition_strategy == "by_stock" and "year" not in kwargs:
                raise ValueError("日线数据按股票分区读取必须提供 year（新格式按年份分区）")
            
            # 获取分区路径
            partition_path = self.get_partition_path(data_type, partition_strategy, **kwargs)
            
            # 确定文件路径
            if file_name:
                file_path = partition_path / file_name
            else:
                # 如果路径是文件，直接使用
                if partition_path.is_file():
                    file_path = partition_path
                else:
                    # 尝试查找parquet文件
                    parquet_files = list(partition_path.glob("*.parquet"))
                    if not parquet_files:
                        logger.debug(f"未找到Parquet文件: {partition_path}")
                        return None
                    file_path = parquet_files[0]  # 使用第一个文件
            
            if not file_path.exists():
                logger.debug(f"文件不存在: {file_path}")
                return None
            
            # 读取文件
            df = pd.read_parquet(file_path)
            logger.debug(f"读取分区数据成功: {file_path}，共 {len(df)} 条记录")
            return df
        except Exception as e:
            logger.error(f"读取分区数据失败: {e}")
            return None
