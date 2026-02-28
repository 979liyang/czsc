# -*- coding: utf-8 -*-
"""
原始数据存储服务

实现分钟数据和日线数据的双分区存储
"""
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
from loguru import logger

from backend.data.storage_manager import StorageManager
from backend.utils.compression_config import get_parquet_write_options
from backend.data.schema_registry import SchemaRegistry


class RawDataStorage(StorageManager):
    """原始数据存储服务"""
    
    def __init__(self, base_path: Path = None):
        """
        初始化原始数据存储服务
        
        :param base_path: 基础路径，默认为项目根目录下的stock_data文件夹
        """
        super().__init__(base_path)
        self.schema_registry = SchemaRegistry()
        logger.info("原始数据存储服务初始化完成")
    
    def save_minute_data_by_date(
        self,
        df: pd.DataFrame,
        partition_date: date,
        incremental: bool = True
    ) -> bool:
        """
        按日期分区保存分钟数据
        
        :param df: 分钟数据DataFrame（必须包含timestamp, stock_code等列）
        :param partition_date: 分区日期
        :param incremental: 是否增量更新
        :return: 是否成功
        """
        try:
            # 数据验证
            if not self._validate_minute_data(df):
                return False
            
            # 如果增量更新，读取现有数据并合并
            if incremental:
                existing_df = self.read_partitioned_data(
                    "minute",
                    "by_date",
                    date=partition_date
                )
                
                if existing_df is not None and len(existing_df) > 0:
                    # 合并数据并去重
                    df = self._merge_and_deduplicate(existing_df, df, ['timestamp', 'stock_code'])
            
            # 写入分区数据
            return self.write_partitioned_data(
                df,
                "minute",
                "by_date",
                file_name="part-00000.parquet",
                date=partition_date
            )
        except Exception as e:
            logger.error(f"按日期分区保存分钟数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_minute_data_by_stock(
        self,
        df: pd.DataFrame,
        stock_code: str,
        year: int,
        month: int,
        incremental: bool = True,
        minute_subdir: Optional[str] = None,
    ) -> bool:
        """
        按股票分区保存分钟数据。

        :param df: 分钟数据DataFrame
        :param stock_code: 股票代码
        :param year: 年份
        :param month: 月份
        :param incremental: 是否增量更新
        :param minute_subdir: 1min 不传或 None 存 raw/minute_by_stock；60min 传 minute_60_by_stock 存 raw/minute_60_by_stock
        :return: 是否成功
        """
        try:
            # 数据验证
            if not self._validate_minute_data(df):
                return False

            kwargs = dict(stock_code=stock_code, year=year, month=month)
            if minute_subdir:
                kwargs["minute_subdir"] = minute_subdir

            # 如果增量更新，读取现有数据并合并
            if incremental:
                file_path = self.get_partition_path("minute", "by_stock", **kwargs)

                if file_path.exists():
                    existing_df = pd.read_parquet(file_path)
                    if existing_df is not None and len(existing_df) > 0:
                        df = self._merge_and_deduplicate(existing_df, df, ['timestamp', 'stock_code'])

            # 写入分区数据
            return self.write_partitioned_data(df, "minute", "by_stock", **kwargs)
        except Exception as e:
            logger.error(f"按股票分区保存分钟数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_daily_data_by_date(
        self,
        df: pd.DataFrame,
        partition_date: date,
        incremental: bool = True
    ) -> bool:
        """
        按日期分区保存日线数据
        
        :param df: 日线数据DataFrame（必须包含date, stock_code等列）
        :param partition_date: 分区日期
        :param incremental: 是否增量更新
        :return: 是否成功
        """
        try:
            # 数据验证
            if not self._validate_daily_data(df):
                return False
            
            # 如果增量更新，读取现有数据并合并
            if incremental:
                existing_df = self.read_partitioned_data(
                    "daily",
                    "by_date",
                    date=partition_date
                )
                
                if existing_df is not None and len(existing_df) > 0:
                    df = self._merge_and_deduplicate(existing_df, df, ['date', 'stock_code'])
            
            # 写入分区数据
            return self.write_partitioned_data(
                df,
                "daily",
                "by_date",
                file_name="part-00000.parquet",
                date=partition_date
            )
        except Exception as e:
            logger.error(f"按日期分区保存日线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_daily_data_by_stock(
        self,
        df: pd.DataFrame,
        stock_code: str,
        incremental: bool = True,
        year: int = None
    ) -> bool:
        """
        按股票分区保存日线数据（支持按年份分区）
        
        :param df: 日线数据DataFrame（必须包含date列）
        :param stock_code: 股票代码
        :param incremental: 是否增量更新
        :param year: 年份（可选，如果提供则按该年份分区；如果不提供则从数据中推断年份并按年份分组存储）
        :return: 是否成功
        """
        try:
            # 数据验证
            if not self._validate_daily_data(df):
                return False
            
            # 如果DataFrame为空，直接返回成功
            if len(df) == 0:
                logger.debug(f"{stock_code} 数据为空，跳过保存")
                return True
            
            # 确保date列是datetime类型
            if 'date' not in df.columns:
                logger.error("DataFrame必须包含date列")
                return False
            
            # 转换date列为datetime类型
            # 如果已经是datetime类型，直接使用；如果是date类型，转换为datetime
            if df['date'].dtype == 'object' or not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])
            elif hasattr(df['date'].dtype, 'tz') and df['date'].dtype.tz is not None:
                # 如果有时区信息，转换为无时区的datetime
                df['date'] = df['date'].dt.tz_localize(None)
            
            # 显示数据的时间范围（用于调试）
            if len(df) > 0:
                actual_start = df['date'].min()
                actual_end = df['date'].max()
                logger.debug(f"{stock_code} 数据时间范围: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}")
                logger.debug(f"{stock_code} 数据年份: {sorted(df['date'].dt.year.unique().tolist())}")
            
            # 如果没有提供year参数，尝试从数据中推断年份
            # 如果数据跨多个年份，按年份分组存储
            if year is None:
                # 获取数据中的所有年份
                years = sorted(df['date'].dt.year.unique().tolist())
                
                if len(years) == 1:
                    # 单一年份，使用该年份
                    year = years[0]
                    logger.info(f"从数据推断年份: {year} (数据时间范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')})")
                else:
                    # 多个年份，按年份分组存储
                    logger.info(f"{stock_code} 数据跨多个年份 {years}，将按年份分组存储")
                    success = True
                    for y in years:
                        year_df = df[df['date'].dt.year == y].copy()
                        if len(year_df) > 0:
                            result = self.save_daily_data_by_stock(
                                year_df, stock_code, incremental=incremental, year=y
                            )
                            if not result:
                                success = False
                    return success
            
            # 验证年份信息
            if year is not None:
                # 过滤出该年份的数据
                df_year = df[df['date'].dt.year == year].copy()
                if len(df_year) == 0:
                    logger.warning(f"{stock_code} 在 {year} 年没有数据，跳过保存")
                    return True
                df = df_year
            
            # 如果增量更新，读取现有数据并合并
            if incremental:
                file_path = self.get_partition_path(
                    "daily",
                    "by_stock",
                    stock_code=stock_code,
                    year=year
                )
                
                if file_path.exists():
                    try:
                        existing_df = pd.read_parquet(file_path)
                        if existing_df is not None and len(existing_df) > 0:
                            # 确保date列是datetime类型
                            existing_df['date'] = pd.to_datetime(existing_df['date'])
                            df = self._merge_and_deduplicate(existing_df, df, ['date', 'stock_code'])
                            logger.debug(f"合并现有数据: {stock_code}, {year}, 合并后 {len(df)} 条记录")
                    except Exception as e:
                        logger.warning(f"读取现有数据失败，将覆盖: {e}")
            
            # 写入分区数据
            return self.write_partitioned_data(
                df,
                "daily",
                "by_stock",
                stock_code=stock_code,
                year=year
            )
        except Exception as e:
            logger.error(f"按股票分区保存日线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_daily_data_by_index(
        self,
        df: pd.DataFrame,
        index_code: str,
        incremental: bool = True,
        year: int = None
    ) -> bool:
        """
        按指数分区保存日线数据到 raw/daily/by_index/index_code=xxx/。

        :param df: 日线数据 DataFrame（须含 date, index_code, open, high, low, close, volume, amount）
        :param index_code: 指数代码（如 000001.SH）
        :param incremental: 是否增量更新
        :param year: 年份（不传则按数据推断并按年分组写入）
        :return: 是否成功
        """
        try:
            if not self._validate_index_daily_data(df):
                return False
            if len(df) == 0:
                logger.debug(f"{index_code} 指数日线数据为空，跳过保存")
                return True
            if "date" not in df.columns:
                logger.error("DataFrame 必须包含 date 列")
                return False
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            if year is None:
                years = sorted(df["date"].dt.year.unique().tolist())
                if len(years) == 1:
                    year = years[0]
                else:
                    success = True
                    for y in years:
                        year_df = df[df["date"].dt.year == y].copy()
                        if len(year_df) > 0:
                            if not self.save_daily_data_by_index(year_df, index_code, incremental=incremental, year=y):
                                success = False
                    return success
            df_year = df[df["date"].dt.year == year].copy()
            if len(df_year) == 0:
                logger.warning(f"{index_code} 在 {year} 年无数据，跳过")
                return True
            df = df_year
            if incremental:
                file_path = self.get_partition_path("daily", "by_index", index_code=index_code, year=year)
                if file_path.exists():
                    try:
                        existing_df = pd.read_parquet(file_path)
                        if existing_df is not None and len(existing_df) > 0:
                            existing_df["date"] = pd.to_datetime(existing_df["date"])
                            df = self._merge_and_deduplicate(existing_df, df, ["date", "index_code"])
                    except Exception as e:
                        logger.warning(f"读取已有指数日线失败，将覆盖: {e}")
            return self.write_partitioned_data(
                df, "daily", "by_index", index_code=index_code, year=year
            )
        except Exception as e:
            logger.error(f"按指数分区保存日线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _validate_index_daily_data(self, df: pd.DataFrame) -> bool:
        """验证指数日线数据（须含 index_code）"""
        required = ["date", "index_code", "open", "high", "low", "close", "volume", "amount"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.error(f"指数日线数据缺少列: {missing}")
            return False
        if (df["high"] < df["low"]).any():
            logger.error("指数日线数据价格不合理：high < low")
            return False
        return True
    
    def _validate_minute_data(self, df: pd.DataFrame) -> bool:
        """验证分钟数据"""
        required_cols = ['timestamp', 'stock_code', 'open', 'high', 'low', 'close', 'volume', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.error(f"分钟数据缺少必需列: {missing_cols}")
            return False
        
        # 验证价格合理性
        if (df['high'] < df['low']).any():
            logger.error("分钟数据价格不合理：high < low")
            return False
        
        return True
    
    def _validate_daily_data(self, df: pd.DataFrame) -> bool:
        """验证日线数据"""
        required_cols = ['date', 'stock_code', 'open', 'high', 'low', 'close', 'volume', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.error(f"日线数据缺少必需列: {missing_cols}")
            return False
        
        # 验证价格合理性
        if (df['high'] < df['low']).any():
            logger.error("日线数据价格不合理：high < low")
            return False
        
        return True
    
    def _merge_and_deduplicate(
        self,
        existing_df: pd.DataFrame,
        new_df: pd.DataFrame,
        subset: list
    ) -> pd.DataFrame:
        """合并数据并去重。排除空 DataFrame 与全 NA 列后再 concat，避免 FutureWarning。"""
        if existing_df.empty and new_df.empty:
            return existing_df.copy()
        if existing_df.empty:
            return new_df.copy()
        if new_df.empty:
            return existing_df.copy()
        # 去掉全 NA 列，避免 concat 时触发 dtype 推断的 FutureWarning
        existing_clean = existing_df.dropna(axis=1, how='all')
        new_clean = new_df.dropna(axis=1, how='all')
        combined_df = pd.concat([existing_clean, new_clean], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
        
        # 按时间排序
        if 'timestamp' in combined_df.columns:
            combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)
        elif 'date' in combined_df.columns:
            combined_df = combined_df.sort_values('date').reset_index(drop=True)
        
        return combined_df
