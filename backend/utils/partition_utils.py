# -*- coding: utf-8 -*-
"""
分区路径生成工具

提供Hive分区格式的路径生成功能
"""
from pathlib import Path
from datetime import datetime, date
from typing import Optional


class PartitionPathGenerator:
    """分区路径生成器"""
    
    def __init__(self, base_path: Path = None):
        """
        初始化分区路径生成器
        
        :param base_path: 基础路径，默认为项目根目录下的stock_data文件夹
        """
        if base_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / ".stock_data"
        else:
            self.base_path = Path(base_path)
    
    def generate_date_partition_path(
        self,
        data_type: str,
        partition_date: date,
        partition_strategy: str = "by_date"
    ) -> Path:
        """
        生成按日期分区的路径（Hive分区格式）
        
        :param data_type: 数据类型（'minute', 'daily'）
        :param partition_date: 分区日期
        :param partition_strategy: 分区策略（'by_date' 或 'by_stock'）
        :return: 分区路径
        """
        if isinstance(partition_date, str):
            partition_date = datetime.strptime(partition_date, "%Y-%m-%d").date()
        elif isinstance(partition_date, datetime):
            partition_date = partition_date.date()
        
        if data_type == "minute" and partition_strategy == "by_date":
            # 按日期分区：raw/minute_by_date/year=2024/month=01/date=2024-01-15/
            path = (
                self.base_path / "raw" / "minute_by_date" /
                f"year={partition_date.year}" /
                f"month={partition_date.month:02d}" /
                f"date={partition_date.strftime('%Y-%m-%d')}"
            )
        elif data_type == "minute" and partition_strategy == "by_stock":
            # 按股票分区：raw/minute_by_stock/stock_code={stock_code}/year=2024/
            # 注意：这个方法需要stock_code参数，应该使用generate_stock_partition_path
            raise ValueError("使用generate_stock_partition_path方法生成按股票分区的路径")
        elif data_type == "daily" and partition_strategy == "by_date":
            # 按日期分区：raw/daily/by_date/year=2024/month=01/
            path = (
                self.base_path / "raw" / "daily" / "by_date" /
                f"year={partition_date.year}" /
                f"month={partition_date.month:02d}"
            )
        elif data_type == "indicators" and partition_strategy == "by_date":
            # 指标数据按日期分区：processed/indicators_daily/year=2024/month=01/
            year = partition_date.year
            month = partition_date.month
            return self.base_path / "processed" / "indicators_daily" / f"year={year}" / f"month={month:02d}"
        elif data_type == "factors" and partition_strategy == "by_date":
            # 因子数据按日期分区：processed/factors/year=2024/month=01/
            year = partition_date.year
            month = partition_date.month
            return self.base_path / "processed" / "factors" / f"year={year}" / f"month={month:02d}"
        elif data_type == "signals" and partition_strategy == "by_date":
            # 信号数据按日期分区：processed/signals/year=2024/month=01/
            year = partition_date.year
            month = partition_date.month
            return self.base_path / "processed" / "signals" / f"year={year}" / f"month={month:02d}"
        else:
            raise ValueError(f"不支持的数据类型或分区策略: {data_type}, {partition_strategy}")
        
        return path
    
    def generate_stock_partition_path(
        self,
        data_type: str,
        stock_code: str,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Path:
        """
        生成按股票分区的路径
        
        :param data_type: 数据类型（'minute', 'daily'）
        :param stock_code: 股票代码（如：000001.SZ）
        :param year: 年份（日线数据和分钟数据按股票分区时必需）
        :param month: 月份（可选，如果提供则生成月度文件路径）
        :return: 分区路径
        """
        if data_type == "minute":
            # 分钟数据按股票分区需要year参数
            if year is None:
                raise ValueError("分钟数据按股票分区需要提供year参数")
            
            # 按股票分区：raw/minute_by_stock/stock_code={stock_code}/year={year}/
            path = (
                self.base_path / "raw" / "minute_by_stock" /
                f"stock_code={stock_code}" /
                f"year={year}"
            )
            
            # 如果提供了月份，返回文件路径
            if month is not None:
                file_name = f"{stock_code}_{year}-{month:02d}.parquet"
                return path / file_name
            
            return path
        elif data_type == "daily":
            # 按股票分区（新格式，按年份分区）：
            # raw/daily/by_stock/stock_code={stock_code}/year={year}/stock_code={stock_code}_{year}.parquet
            if year is None:
                raise ValueError("日线数据按股票分区需要提供year参数（新格式按年份分区）")
            
            # 新格式：按年份分区
            path = (
                self.base_path / "raw" / "daily" / "by_stock" /
                f"stock_code={stock_code}" /
                f"year={year}"
            )
            
            # 如果提供了月份，返回月度文件路径（可选功能）
            if month is not None:
                file_name = f"stock_code={stock_code}_{year}-{month:02d}.parquet"
                return path / file_name
            
            # 默认返回年度文件路径
            file_name = f"stock_code={stock_code}_{year}.parquet"
            return path / file_name
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
    
    def get_file_path(
        self,
        data_type: str,
        partition_strategy: str,
        **kwargs
    ) -> Path:
        """
        获取文件路径（统一接口）
        
        :param data_type: 数据类型（'minute', 'daily', 'indicators', 'factors', 'signals'）
        :param partition_strategy: 分区策略（'by_date', 'by_stock'）
        :param kwargs: 其他参数
          - by_date: date, stock_code (可选)
          - by_stock: stock_code, year, month (可选)
        :return: 文件路径
        """
        if partition_strategy == "by_date":
            partition_date = kwargs.get('date')
            if partition_date is None:
                raise ValueError("按日期分区需要提供date参数")
            return self.generate_date_partition_path(data_type, partition_date, partition_strategy)
        elif partition_strategy == "by_stock":
            stock_code = kwargs.get('stock_code')
            year = kwargs.get('year')
            month = kwargs.get('month')
            
            # 日线数据按股票分区（新格式按年份分区，year 必填）
            if data_type == "daily":
                if stock_code is None:
                    raise ValueError("按股票分区需要提供stock_code参数")
                if year is None:
                    raise ValueError("日线数据按股票分区需要提供year参数（新格式按年份分区）")
                return self.generate_stock_partition_path(data_type, stock_code, year, month)
            else:
                # 分钟数据按股票分区需要year参数
                if stock_code is None or year is None:
                    raise ValueError("按股票分区需要提供stock_code和year参数")
                return self.generate_stock_partition_path(data_type, stock_code, year, month)
        else:
            raise ValueError(f"不支持的分区策略: {partition_strategy}")
