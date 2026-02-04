# -*- coding: utf-8 -*-
"""
原始数据加载器

从新架构的分区存储中加载原始数据
"""
from pathlib import Path
from typing import Optional, List
from datetime import date, datetime
import pandas as pd
from loguru import logger

from backend.data.raw_data_storage import RawDataStorage


class RawDataLoader:
    """原始数据加载器"""
    
    def __init__(self, base_path: Path = None):
        """
        初始化原始数据加载器
        
        :param base_path: 基础路径，默认为项目根目录下的stock_data文件夹
        """
        self.storage = RawDataStorage(base_path)
        logger.info("原始数据加载器初始化完成")
    
    def load_minute_data(
        self,
        partition_date: date = None,
        stock_code: str = None,
        start_date: date = None,
        end_date: date = None,
        year: int = None,
        month: int = None
    ) -> Optional[pd.DataFrame]:
        """
        加载分钟数据
        
        :param partition_date: 分区日期（按日期分区查询）
        :param stock_code: 股票代码（按股票分区查询）
        :param start_date: 开始日期（时间范围查询）
        :param end_date: 结束日期（时间范围查询）
        :param year: 年份（按股票分区查询）
        :param month: 月份（按股票分区查询）
        :return: DataFrame或None
        """
        try:
            if partition_date:
                # 按日期分区加载
                df = self.storage.read_partitioned_data(
                    "minute",
                    "by_date",
                    date=partition_date
                )
                if df is not None:
                    logger.info(f"按日期分区加载分钟数据成功: {partition_date}，共 {len(df)} 条记录")
                return df
            
            elif stock_code and year:
                # 按股票分区加载
                df = self.storage.read_partitioned_data(
                    "minute",
                    "by_stock",
                    stock_code=stock_code,
                    year=year,
                    month=month
                )
                if df is not None:
                    logger.info(f"按股票分区加载分钟数据成功: {stock_code}, {year}-{month}，共 {len(df)} 条记录")
                return df
            
            elif start_date and end_date:
                # 时间范围查询（需要遍历多个分区）
                logger.warning("时间范围查询需要遍历多个分区，性能可能较慢")
                # TODO: 实现时间范围查询优化
                return None
            
            else:
                logger.error("参数不足，无法确定查询方式")
                return None
                
        except Exception as e:
            logger.error(f"加载分钟数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_all_minute_data_by_stock(
        self,
        stock_code: str,
        start_dt: datetime = None,
        end_dt: datetime = None,
        period: int = None
    ) -> Optional[pd.DataFrame]:
        """
        加载某只股票的全部分钟数据（聚合本地 parquet）

        :param stock_code: 股票代码（如：600078.SH）
        :param start_dt: 起始时间（可选）
        :param end_dt: 结束时间（可选）
        :param period: 分钟周期过滤（可选，如 1/5/15/30/60）
        :return: DataFrame 或 None
        """
        try:
            base_dir = self.storage.base_path / "raw" / "minute_by_stock" / f"stock_code={stock_code}"
            files = sorted(base_dir.glob("year=*/**/*.parquet"))
            if not files:
                logger.warning(f"未找到分钟数据文件: {base_dir}")
                return None
            dfs = []
            for fp in files:
                df = self._read_parquet_safe(fp)
                if df is not None and len(df) > 0:
                    dfs.append(df)
            if not dfs:
                return None
            df_all = pd.concat(dfs, ignore_index=True)
            df_all = self._filter_minute_df(df_all, start_dt=start_dt, end_dt=end_dt, period=period)
            logger.info(f"加载分钟数据成功: {stock_code}，共 {len(df_all)} 条记录")
            return df_all
        except Exception as e:
            logger.error(f"加载股票分钟数据失败: {stock_code} - {e}")
            return None

    @staticmethod
    def _read_parquet_safe(file_path: Path) -> Optional[pd.DataFrame]:
        """安全读取 parquet 文件"""
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            logger.warning(f"读取 parquet 失败: {file_path} - {e}")
            return None

    @staticmethod
    def _filter_minute_df(df: pd.DataFrame, start_dt: datetime, end_dt: datetime, period: Optional[int]) -> pd.DataFrame:
        """对分钟数据做时间与周期过滤并排序"""
        if df is None or len(df) == 0:
            return df
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            if start_dt:
                df = df[df["timestamp"] >= pd.to_datetime(start_dt)]
            if end_dt:
                df = df[df["timestamp"] <= pd.to_datetime(end_dt)]
        if period is not None and "period" in df.columns:
            df = df[df["period"] == int(period)]
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df
    
    def load_daily_data(
        self,
        partition_date: date = None,
        stock_code: str = None,
        start_date: date = None,
        end_date: date = None,
        year: int = None,
        start_year: int = None,
        end_year: int = None
    ) -> Optional[pd.DataFrame]:
        """
        加载日线数据（支持年份范围查询）
        
        :param partition_date: 分区日期（按日期分区查询）
        :param stock_code: 股票代码（按股票分区查询）
        :param start_date: 开始日期（时间范围查询）
        :param end_date: 结束日期（时间范围查询）
        :param year: 年份（按股票分区查询时指定单个年份）
        :param start_year: 开始年份（年份范围查询）
        :param end_year: 结束年份（年份范围查询）
        :return: DataFrame或None
        """
        try:
            if partition_date:
                # 按日期分区加载
                df = self.storage.read_partitioned_data(
                    "daily",
                    "by_date",
                    date=partition_date
                )
                if df is not None:
                    logger.info(f"按日期分区加载日线数据成功: {partition_date}，共 {len(df)} 条记录")
                return df
            
            elif stock_code:
                # 按股票分区加载（支持年份范围）
                dfs = []
                
                # 确定需要查询的年份列表
                years_to_query = []
                
                if year is not None:
                    # 单个年份
                    years_to_query = [year]
                elif start_year is not None or end_year is not None:
                    # 年份范围（必须显式给出 start_year 与 end_year）
                    if start_year is None or end_year is None:
                        raise ValueError("按股票分区加载日线数据：年份范围查询需要同时提供 start_year 和 end_year")
                    years_to_query = list(range(start_year, end_year + 1))
                    logger.debug(f"年份范围查询: {start_year} - {end_year}")
                else:
                    raise ValueError("按股票分区加载日线数据必须提供 year 或 start_year/end_year（新格式按年份分区）")
                
                # 按年份查询并合并
                for y in years_to_query:
                    df_year = self.storage.read_partitioned_data(
                        "daily",
                        "by_stock",
                        stock_code=stock_code,
                        year=y
                    )
                    if df_year is not None and len(df_year) > 0:
                        dfs.append(df_year)
                
                if dfs:
                    df = pd.concat(dfs, ignore_index=True)
                    # 按日期排序
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df = df.sort_values('date').reset_index(drop=True)
                    logger.info(f"按股票分区加载日线数据成功: {stock_code}, 年份 {years_to_query}，共 {len(df)} 条记录")
                else:
                    df = None
                
                if df is not None and len(df) > 0:
                    # 如果指定了时间范围，进行过滤
                    if start_date or end_date:
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            if start_date:
                                df = df[df['date'] >= pd.to_datetime(start_date)]
                            if end_date:
                                df = df[df['date'] <= pd.to_datetime(end_date)]
                            logger.info(f"时间范围过滤后，共 {len(df)} 条记录")
                
                return df
            
            elif start_date and end_date:
                # 时间范围查询（需要遍历多个分区）
                logger.warning("时间范围查询需要遍历多个分区，性能可能较慢")
                # TODO: 实现时间范围查询优化
                return None
            
            else:
                logger.error("参数不足，无法确定查询方式")
                return None
                
        except Exception as e:
            logger.error(f"加载日线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_multiple_stocks_daily(
        self,
        stock_codes: List[str],
        start_date: date = None,
        end_date: date = None
    ) -> Optional[pd.DataFrame]:
        """
        批量加载多只股票的日线数据
        
        :param stock_codes: 股票代码列表
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 合并后的DataFrame或None
        """
        try:
            dfs = []
            # 按股票分区读取日线数据需要显式年份范围，这里从 start_date/end_date 推断
            start_year = start_date.year if start_date else datetime.now().year
            end_year = end_date.year if end_date else datetime.now().year
            for stock_code in stock_codes:
                df = self.load_daily_data(
                    stock_code=stock_code,
                    start_year=start_year,
                    end_year=end_year,
                    start_date=start_date,
                    end_date=end_date
                )
                if df is not None and len(df) > 0:
                    dfs.append(df)
            
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                logger.info(f"批量加载 {len(stock_codes)} 只股票日线数据成功，共 {len(combined_df)} 条记录")
                return combined_df
            else:
                logger.warning("没有加载到任何数据")
                return None
                
        except Exception as e:
            logger.error(f"批量加载日线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None
