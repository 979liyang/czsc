# -*- coding: utf-8 -*-
"""
K线数据存储服务

提供K线数据的存储、加载、更新功能，使用Parquet格式存储数据。
"""
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
from loguru import logger
from czsc.objects import RawBar, Freq


class KlineStorage:
    """K线数据存储服务"""

    def __init__(self, base_path: Path):
        """
        初始化K线存储服务

        :param base_path: 数据存储基础路径，如 Path("data/klines")
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_path / "index.json"

    def _bars_to_df(self, bars: List[RawBar]) -> pd.DataFrame:
        """
        将RawBar列表转换为DataFrame

        :param bars: RawBar对象列表
        :return: DataFrame，包含所有K线数据
        """
        if not bars:
            return pd.DataFrame()

        data = []
        for bar in bars:
            data.append({
                'symbol': bar.symbol,
                'id': bar.id,
                'dt': bar.dt,
                'freq': bar.freq.value,
                'open': bar.open,
                'close': bar.close,
                'high': bar.high,
                'low': bar.low,
                'vol': bar.vol,
                'amount': bar.amount,
            })

        df = pd.DataFrame(data)
        df['dt'] = pd.to_datetime(df['dt'])
        return df

    def _df_to_bars(self, df: pd.DataFrame, symbol: str, freq: str) -> List[RawBar]:
        """
        将DataFrame转换为RawBar列表

        :param df: DataFrame，包含K线数据
        :param symbol: 标的代码
        :param freq: K线周期
        :return: RawBar对象列表
        """
        if df.empty:
            return []

        bars = []
        for _, row in df.iterrows():
            bar = RawBar(
                symbol=symbol,
                id=int(row['id']) if 'id' in row else 0,
                dt=pd.to_datetime(row['dt']).to_pydatetime(),
                freq=Freq(freq),
                open=float(row['open']),
                close=float(row['close']),
                high=float(row['high']),
                low=float(row['low']),
                vol=float(row['vol']),
                amount=float(row['amount']),
            )
            bars.append(bar)

        return bars

    def _get_file_path(self, symbol: str, freq: str) -> Path:
        """
        获取数据文件路径

        :param symbol: 标的代码
        :param freq: K线周期
        :return: Parquet文件路径
        """
        return self.base_path / symbol / freq / "data.parquet"

    def _get_metadata_path(self, symbol: str) -> Path:
        """
        获取元数据文件路径

        :param symbol: 标的代码
        :return: 元数据文件路径
        """
        return self.base_path / symbol / "metadata.json"

    def save_bars(self, symbol: str, freq: str, bars: List[RawBar]) -> None:
        """
        保存K线数据到Parquet文件

        :param symbol: 标的代码
        :param freq: K线周期
        :param bars: RawBar对象列表
        """
        if not bars:
            logger.warning(f"保存空数据：{symbol} {freq}")
            return

        file_path = self._get_file_path(symbol, freq)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        df = self._bars_to_df(bars)
        df.to_parquet(file_path, compression='snappy', index=False)

        # 更新元数据
        self._update_metadata(symbol, freq, bars)

        # 更新索引
        self._update_index(symbol, freq)

        logger.info(f"保存K线数据：{symbol} {freq}，共{len(bars)}条")

    def load_bars(self, symbol: str, freq: str, sdt: Optional[str] = None,
                  edt: Optional[str] = None) -> List[RawBar]:
        """
        从Parquet文件加载K线数据

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始时间（可选），格式：YYYYMMDD或YYYY-MM-DD
        :param edt: 结束时间（可选），格式：YYYYMMDD或YYYY-MM-DD
        :return: RawBar对象列表
        """
        file_path = self._get_file_path(symbol, freq)
        if not file_path.exists():
            logger.warning(f"数据文件不存在：{file_path}")
            return []

        df = pd.read_parquet(file_path)

        # 时间范围过滤
        if sdt or edt:
            if 'dt' not in df.columns and 'datetime' in df.columns:
                df['dt'] = pd.to_datetime(df['datetime'])

            if sdt:
                sdt_dt = pd.to_datetime(sdt)
                df = df[df['dt'] >= sdt_dt]

            if edt:
                edt_dt = pd.to_datetime(edt)
                df = df[df['dt'] <= edt_dt]

        # 确保id连续
        if 'id' not in df.columns or df['id'].isna().any():
            df = df.sort_values('dt').reset_index(drop=True)
            df['id'] = range(1, len(df) + 1)

        bars = self._df_to_bars(df, symbol, freq)
        logger.info(f"加载K线数据：{symbol} {freq}，共{len(bars)}条")
        return bars

    def _update_metadata(self, symbol: str, freq: str, bars: List[RawBar]) -> None:
        """
        更新元数据

        :param symbol: 标的代码
        :param freq: K线周期
        :param bars: RawBar对象列表
        """
        metadata_path = self._get_metadata_path(symbol)

        # 读取现有元数据
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # 更新该周期的元数据
        if bars:
            dts = [bar.dt for bar in bars]
            metadata[freq] = {
                'count': len(bars),
                'start_dt': min(dts).strftime('%Y-%m-%d %H:%M:%S'),
                'end_dt': max(dts).strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

        # 保存元数据
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _update_index(self, symbol: str, freq: str) -> None:
        """
        更新全局索引

        :param symbol: 标的代码
        :param freq: K线周期
        """
        # 读取现有索引
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {'symbols': {}, 'updated_at': None}

        # 更新索引
        if symbol not in index['symbols']:
            index['symbols'][symbol] = {'freqs': []}

        if freq not in index['symbols'][symbol]['freqs']:
            index['symbols'][symbol]['freqs'].append(freq)

        index['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 保存索引
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def append_bars(self, symbol: str, freq: str, bars: List[RawBar]) -> None:
        """
        追加K线数据到现有文件（增量更新）

        :param symbol: 标的代码
        :param freq: K线周期
        :param bars: 新的RawBar对象列表
        """
        if not bars:
            return

        file_path = self._get_file_path(symbol, freq)

        # 读取现有数据
        existing_bars = []
        if file_path.exists():
            existing_bars = self.load_bars(symbol, freq)

        # 合并数据（去重，保留最新的）
        existing_dts = {bar.dt for bar in existing_bars}
        new_bars = [bar for bar in bars if bar.dt not in existing_dts]

        if new_bars:
            all_bars = existing_bars + new_bars
            # 按时间排序并重新分配id
            all_bars.sort(key=lambda x: x.dt)
            for i, bar in enumerate(all_bars, 1):
                bar.id = i

            # 保存合并后的数据
            self.save_bars(symbol, freq, all_bars)
            logger.info(f"增量更新K线数据：{symbol} {freq}，新增{len(new_bars)}条")
        else:
            logger.info(f"无新数据需要更新：{symbol} {freq}")

    def get_metadata(self, symbol: str) -> dict:
        """
        获取标的的元数据

        :param symbol: 标的代码
        :return: 元数据字典
        """
        metadata_path = self._get_metadata_path(symbol)
        if not metadata_path.exists():
            return {}

        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_symbols(self) -> List[str]:
        """
        列出所有已存储的标的代码

        :return: 标的代码列表
        """
        if not self.index_file.exists():
            return []

        with open(self.index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        return list(index.get('symbols', {}).keys())

    def validate_data_quality(self, symbol: str, freq: str) -> Dict[str, Any]:
        """
        验证K线数据的完整性和正确性

        :param symbol: 标的代码
        :param freq: K线周期
        :return: 数据质量报告
        """
        bars = self.load_bars(symbol, freq)
        if not bars:
            return {
                'valid': False,
                'errors': ['数据文件不存在或为空'],
                'warnings': [],
                'stats': {},
            }

        errors = []
        warnings = []
        stats = {
            'total_bars': len(bars),
            'date_range': None,
            'missing_dates': [],
            'duplicate_dates': [],
            'invalid_prices': [],
        }

        # 检查时间连续性
        dts = [bar.dt for bar in bars]
        if dts:
            stats['date_range'] = {
                'start': min(dts).isoformat(),
                'end': max(dts).isoformat(),
            }

        # 检查ID连续性
        ids = [bar.id for bar in bars]
        expected_ids = list(range(1, len(bars) + 1))
        if ids != expected_ids:
            errors.append('ID不连续')

        # 检查价格有效性
        for i, bar in enumerate(bars):
            if bar.high < bar.low:
                errors.append(f'第{i+1}条K线：最高价低于最低价')
                stats['invalid_prices'].append(i + 1)
            if bar.open < 0 or bar.close < 0 or bar.high < 0 or bar.low < 0:
                errors.append(f'第{i+1}条K线：价格不能为负数')
                stats['invalid_prices'].append(i + 1)
            if bar.vol < 0 or bar.amount < 0:
                warnings.append(f'第{i+1}条K线：成交量或成交额为负数')

        # 检查时间顺序
        for i in range(1, len(bars)):
            if bars[i].dt <= bars[i-1].dt:
                errors.append(f'第{i+1}条K线：时间顺序错误')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'stats': stats,
        }

    def export_bars(self, symbol: str, freq: str, sdt: Optional[str] = None,
                   edt: Optional[str] = None, format: str = 'parquet') -> Path:
        """
        导出K线数据

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始时间（可选）
        :param edt: 结束时间（可选）
        :param format: 导出格式（parquet、csv、json）
        :return: 导出文件路径
        """
        bars = self.load_bars(symbol, freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到数据：{symbol} {freq}")

        df = self._bars_to_df(bars)
        export_dir = self.base_path / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if format == 'parquet':
            file_path = export_dir / f"{symbol}_{freq}_{timestamp}.parquet"
            df.to_parquet(file_path, compression='snappy', index=False)
        elif format == 'csv':
            file_path = export_dir / f"{symbol}_{freq}_{timestamp}.csv"
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
        elif format == 'json':
            file_path = export_dir / f"{symbol}_{freq}_{timestamp}.json"
            df.to_json(file_path, orient='records', date_format='iso', force_ascii=False)
        else:
            raise ValueError(f"不支持的导出格式：{format}")

        logger.info(f"导出K线数据：{file_path}，共{len(bars)}条")
        return file_path

    def batch_import(self, data_source: str, symbols: List[str], freqs: List[str],
                    sdt: str, edt: str) -> Dict[str, Any]:
        """
        批量导入数据

        :param data_source: 数据源（research、tushare等）
        :param symbols: 标的代码列表
        :param freqs: K线周期列表
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 导入结果统计
        """
        from czsc.connectors import research

        results = {
            'total': len(symbols) * len(freqs),
            'success': 0,
            'failed': 0,
            'errors': [],
        }

        for symbol in symbols:
            for freq in freqs:
                try:
                    # 从数据源获取数据
                    if data_source == 'research':
                        bars = research.get_raw_bars(symbol, freq, sdt, edt)
                    else:
                        raise ValueError(f"不支持的数据源：{data_source}")

                    if bars:
                        # 保存到本地存储
                        self.append_bars(symbol, freq, bars)
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"{symbol} {freq}: 未获取到数据")

                except Exception as e:
                    results['failed'] += 1
                    error_msg = f"{symbol} {freq}: {str(e)}"
                    results['errors'].append(error_msg)
                    logger.error(f"批量导入失败：{error_msg}")

        logger.info(f"批量导入完成：成功{results['success']}，失败{results['failed']}")
        return results

    def cleanup_old_data(self, before_date: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        清理旧数据

        :param before_date: 清理此日期之前的数据（YYYYMMDD或YYYY-MM-DD）
        :param dry_run: 是否仅预览（不实际删除）
        :return: 清理结果统计
        """
        before_dt = pd.to_datetime(before_date)
        results = {
            'total_files': 0,
            'files_to_delete': 0,
            'total_size': 0,
            'size_to_free': 0,
            'files': [],
        }

        # 遍历所有数据文件
        for symbol_dir in self.base_path.iterdir():
            if not symbol_dir.is_dir() or symbol_dir.name == 'exports':
                continue

            for freq_dir in symbol_dir.iterdir():
                if not freq_dir.is_dir():
                    continue

                file_path = freq_dir / "data.parquet"
                if not file_path.exists():
                    continue

                results['total_files'] += 1
                file_size = file_path.stat().st_size
                results['total_size'] += file_size

                # 检查文件中的数据是否都在清理日期之前
                try:
                    df = pd.read_parquet(file_path)
                    if 'dt' in df.columns:
                        df['dt'] = pd.to_datetime(df['dt'])
                        if df['dt'].max() < before_dt:
                            results['files_to_delete'] += 1
                            results['size_to_free'] += file_size
                            results['files'].append({
                                'path': str(file_path.relative_to(self.base_path)),
                                'size': file_size,
                                'last_date': df['dt'].max().isoformat(),
                            })
                except Exception as e:
                    logger.warning(f"检查文件失败：{file_path}，错误：{e}")

        # 执行删除
        if not dry_run and results['files_to_delete'] > 0:
            for file_info in results['files']:
                file_path = self.base_path / file_info['path']
                try:
                    file_path.unlink()
                    logger.info(f"删除文件：{file_path}")
                except Exception as e:
                    logger.error(f"删除文件失败：{file_path}，错误：{e}")

        return results
