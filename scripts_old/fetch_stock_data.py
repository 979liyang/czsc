#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据采集脚本

用于采集指定股票的日线或分钟级数据并存储到本地。

功能说明:
- 支持采集日线数据
- 支持采集分钟级数据（1/5/15/30/60分钟）
- 数据存储到新格式：.stock_data/raw/daily/by_stock/stock_code={code}/year={year}/...
- 支持增量更新模式

使用示例:
  # 采集600078的日线数据
  python scripts/fetch_stock_data.py --stock 600078.SH --start-date 20240101 --end-date 20241231
  
  # 采集600078的1分钟数据
  python scripts/fetch_stock_data.py --stock 600078.SH --period 1 --start-date 20240101 --end-date 20241231
  
  # 增量更新
  python scripts/fetch_stock_data.py --stock 600078.SH --incremental
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger
import pandas as pd


def collect_minute_data(stock_code: str, period: int = 1, start_date: str = None, 
                       end_date: str = None, incremental: bool = True, 
                       save_available: bool = False) -> bool:
    """
    采集股票的分钟级数据
    
    注意：fetch_minute_data API 不支持历史日期范围参数，只能获取最近的数据。
    如果指定了历史日期范围（早于当前日期），将无法获取数据并返回错误。
    
    :param stock_code: 股票代码（如：600078.SH）
    :param period: 分钟周期（1/5/15/30/60）
    :param start_date: 开始日期（YYYYMMDD格式），如果指定历史日期可能无法获取数据
    :param end_date: 结束日期（YYYYMMDD格式），如果指定历史日期可能无法获取数据
    :param incremental: 是否增量更新
    :param save_available: 如果数据不在请求范围内，是否仍保存当前可用的数据（默认False）
    :return: 是否成功
    """
    logger.info(f"开始采集 {stock_code} 的{period}分钟数据...")
    
    # 提前检查是否请求历史数据
    if start_date or end_date:
        current_date = datetime.now().date()
        if start_date:
            try:
                start_dt_check = datetime.strptime(start_date, '%Y%m%d').date()
                if start_dt_check < current_date:
                    logger.warning(f"⚠️  检测到请求历史数据（开始日期: {start_date}）")
                    logger.warning(f"   注意：fetch_minute_data API 不支持历史日期范围，只能获取最近的数据")
                    logger.warning(f"   如果API返回的数据不在指定范围内，将无法保存")
            except ValueError:
                logger.warning(f"⚠️  开始日期格式可能不正确: {start_date}")
        
        if end_date:
            try:
                end_dt_check = datetime.strptime(end_date, '%Y%m%d').date()
                if end_dt_check < current_date:
                    logger.warning(f"⚠️  检测到请求历史数据（结束日期: {end_date}）")
                    logger.warning(f"   注意：fetch_minute_data API 不支持历史日期范围，只能获取最近的数据")
                    logger.warning(f"   如果API返回的数据不在指定范围内，将无法保存")
            except ValueError:
                logger.warning(f"⚠️  结束日期格式可能不正确: {end_date}")
    
    try:
        from backend.data.akshare_client import AkShareClient
        from backend.data.raw_data_storage import RawDataStorage
        
        client = AkShareClient()
        storage = RawDataStorage()
        
        # 提取股票代码（去掉市场后缀）
        code = stock_code.split('.')[0]
        
        # 获取分钟级数据
        logger.info(f"从数据源获取 {stock_code} 的{period}分钟数据...")
        # 注意：AkShare的分钟数据API可能不支持历史日期范围，但尝试传入日期参数
        df = client.fetch_minute_data(code, str(period), start_date=start_date, end_date=end_date)
        
        # 如果指定了日期但获取不到数据，尝试不指定日期使用默认范围
        if (df is None or len(df) == 0) and (start_date or end_date):
            logger.warning(f"⚠️  使用指定日期范围 ({start_date or '无'} 至 {end_date or '无'}) 未获取到数据")
            logger.warning(f"   尝试使用默认日期范围（最近5个交易日）重新获取...")
            df = client.fetch_minute_data(code, str(period), start_date=None, end_date=None)
        
        if df is None or len(df) == 0:
            logger.error(f"❌ 未获取到 {stock_code} 的{period}分钟数据")
            return False
        
        # 数据清洗和格式化
        df = client.clean_and_format_minute_data(df, stock_code)
        
        if df is None or len(df) == 0:
            logger.error(f"❌ {stock_code} {period}分钟数据清洗失败")
            return False
        
        # 转换列名为存储期望的格式
        if 'symbol' in df.columns:
            df['stock_code'] = df['symbol']
            df = df.drop(columns=['symbol'])
        elif 'stock_code' not in df.columns:
            df['stock_code'] = stock_code
        
        # 转换 dt -> timestamp
        if 'dt' in df.columns:
            df['timestamp'] = pd.to_datetime(df['dt'])
            df = df.drop(columns=['dt'])
        elif 'timestamp' not in df.columns:
            logger.error(f"❌ 数据缺少时间列（dt 或 timestamp）")
            logger.error(f"当前列名: {list(df.columns)}")
            return False
        
        # 转换 vol -> volume
        if 'vol' in df.columns:
            df['volume'] = df['vol']
            df = df.drop(columns=['vol'])
        elif 'volume' not in df.columns:
            logger.error(f"❌ 数据缺少成交量列（vol 或 volume）")
            logger.error(f"当前列名: {list(df.columns)}")
            return False
        
        # 确保 amount 列存在（如果不存在，通过 volume * close 估算）
        if 'amount' not in df.columns:
            logger.warning(f"⚠️  数据缺少成交额列（amount），将通过 volume * close 估算")
            if 'volume' in df.columns and 'close' in df.columns:
                df['amount'] = df['volume'] * df['close']
            else:
                logger.error(f"❌ 无法估算成交额，缺少 volume 或 close 列")
                return False
        
        # 确保所有必需的列都存在
        required_cols = ['timestamp', 'stock_code', 'open', 'high', 'low', 'close', 'volume', 'amount']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"❌ 数据缺少必需列: {missing_cols}")
            logger.error(f"当前列名: {list(df.columns)}")
            return False
        
        # 添加周期信息
        df['period'] = period
        
        # 显示实际数据的时间范围
        actual_start = df['timestamp'].min()
        actual_end = df['timestamp'].max()
        actual_years = sorted(df['timestamp'].dt.year.unique().tolist())
        logger.info(f"实际数据时间范围: {actual_start.strftime('%Y-%m-%d %H:%M:%S')} 至 {actual_end.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"实际数据年份: {actual_years}")
        
        # 如果指定了日期范围，进行过滤
        if start_date or end_date:
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y%m%d')
                original_count = len(df)
                df = df[df['timestamp'] >= start_dt]
                logger.info(f"应用开始日期过滤 ({start_date}): {original_count} -> {len(df)} 条记录")
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y%m%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                before_end_filter = len(df)
                df = df[df['timestamp'] <= end_dt]
                logger.info(f"应用结束日期过滤 ({end_date}): {before_end_filter} -> {len(df)} 条记录")
        
        # 检查过滤后是否还有数据
        if len(df) == 0:
            logger.error(f"❌ 过滤后没有数据")
            if start_date or end_date:
                logger.error(f"  指定的日期范围: {start_date or '无'} 至 {end_date or '无'}")
                logger.error(f"  实际数据时间范围: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}")
                logger.error(f"  原因：fetch_minute_data API 不支持历史日期范围参数，只能获取最近的数据")
            return False
        
        # 按年月分组保存
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        
        success_count = 0
        total_groups = 0
        for (year, month), group_df in df.groupby(['year', 'month']):
            total_groups += 1
            group_df_to_save = group_df.drop(columns=['year', 'month']).copy()
            
            try:
                success = storage.save_minute_data_by_stock(
                    df=group_df_to_save,
                    stock_code=stock_code,
                    year=year,
                    month=month,
                    incremental=incremental
                )
                if success:
                    success_count += 1
                    logger.info(f"✅ 成功保存 {year}-{month:02d} 的数据，共 {len(group_df_to_save)} 条记录")
                else:
                    logger.error(f"❌ 保存 {year}-{month:02d} 的数据失败")
            except Exception as e:
                logger.error(f"❌ 保存 {year}-{month:02d} 的数据时发生异常: {e}")
        
        if success_count > 0:
            logger.info(f"✅ {stock_code} {period}分钟数据采集成功，共 {len(df)} 条记录，成功保存 {success_count}/{total_groups} 个分组")
            return True
        else:
            logger.error(f"❌ {stock_code} {period}分钟数据保存失败，共 {total_groups} 个分组，全部失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def collect_daily_data(stock_code: str, start_date: str = None, 
                      end_date: str = None, incremental: bool = True) -> bool:
    """
    采集股票的日线数据
    
    :param stock_code: 股票代码（如：600078.SH）
    :param start_date: 开始日期（YYYYMMDD格式）
    :param end_date: 结束日期（YYYYMMDD格式）
    :param incremental: 是否增量更新
    :return: 是否成功
    """
    logger.info(f"开始采集 {stock_code} 的日线数据...")
    
    try:
        from backend.data.akshare_client import AkShareClient
        from backend.data.raw_data_storage import RawDataStorage
        
        client = AkShareClient()
        storage = RawDataStorage()
        
        # 提取股票代码（去掉市场后缀）
        code = stock_code.split('.')[0]
        
        # 获取日线数据
        logger.info(f"从数据源获取 {stock_code} 的日线数据...")
        df = client.fetch_historical_data(code, start_date, end_date)
        
        # 如果指定了日期但获取不到数据，尝试不指定日期使用默认范围
        if (df is None or len(df) == 0) and (start_date or end_date):
            logger.warning(f"⚠️  使用指定日期范围 ({start_date or '无'} 至 {end_date or '无'}) 未获取到数据")
            logger.warning(f"   尝试不指定日期范围重新获取（获取所有可用数据）...")
            df = client.fetch_historical_data(code, None, None)
        
        if df is None or len(df) == 0:
            logger.error(f"❌ 未获取到 {stock_code} 的数据")
            return False
        
        # 数据清洗和格式化
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        })
        
        # 添加股票代码
        df['stock_code'] = stock_code
        
        # 转换日期列为datetime类型
        df['date'] = pd.to_datetime(df['date'])
        
        # 显示数据的时间范围
        if len(df) > 0:
            actual_start = df['date'].min()
            actual_end = df['date'].max()
            logger.info(f"数据时间范围: {actual_start.strftime('%Y-%m-%d')} 至 {actual_end.strftime('%Y-%m-%d')}")
            logger.info(f"数据年份: {df['date'].dt.year.unique().tolist()}")
        
        # 保存数据（使用新格式：按股票分区，按年份拆分）
        logger.info(f"保存 {stock_code} 的数据到新格式存储...")
        success = storage.save_daily_data_by_stock(
            df=df,
            stock_code=stock_code,
            incremental=incremental
        )
        
        if success:
            logger.info(f"✅ {stock_code} 数据采集成功，共 {len(df)} 条记录")
            return True
        else:
            logger.error(f"❌ {stock_code} 数据保存失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='股票数据采集脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    示例:
        # 采集600078的日线数据
        python scripts/fetch_stock_data.py --stock 600078.SH --start-date 20240101 --end-date 20241231
        
        # 采集600078的1分钟数据
        python scripts/fetch_stock_data.py --stock 600078.SH --period 1 --start-date 20240101 --end-date 20241231
        
        # 增量更新
        python scripts/fetch_stock_data.py --stock 600078.SH --incremental
        
        # 采集多个股票（需要循环调用）
        for stock in 600078.SH 000001.SZ; do
            python scripts/fetch_stock_data.py --stock $stock --start-date 20240101 --end-date 20241231
        done
        """
    )
    
    parser.add_argument('--stock', type=str, required=True,
                       help='股票代码（如：600078.SH 或 000001.SZ）')
    parser.add_argument('--start-date', type=str, default=None,
                       help='开始日期（YYYYMMDD格式，如：20240101）')
    parser.add_argument('--end-date', type=str, default=None,
                       help='结束日期（YYYYMMDD格式，如：20241231）')
    parser.add_argument('--incremental', action='store_true', default=True,
                       help='增量更新模式（默认启用）')
    parser.add_argument('--no-incremental', dest='incremental', action='store_false',
                       help='覆盖模式（不增量更新）')
    parser.add_argument('--period', type=int, default=None,
                       choices=[1, 5, 15, 30, 60],
                       help='分钟周期（1/5/15/30/60分钟），如果指定则处理分钟级数据，否则处理日线数据')
    parser.add_argument('--save-available', action='store_true',
                       help='如果数据不在请求范围内，仍保存当前可用的数据（仅适用于分钟级数据）')
    
    args = parser.parse_args()
    
    # 验证股票代码格式
    if '.' not in args.stock:
        logger.error(f"❌ 股票代码格式错误，应为：代码.市场（如：600078.SH 或 000001.SZ）")
        return
    
    logger.info("=" * 80)
    logger.info("执行数据采集操作")
    logger.info("=" * 80)
    logger.info(f"股票代码: {args.stock}")
    if args.period:
        logger.info(f"数据周期: {args.period}分钟")
    else:
        logger.info(f"数据周期: 日线")
    if args.start_date:
        logger.info(f"开始日期: {args.start_date}")
    if args.end_date:
        logger.info(f"结束日期: {args.end_date}")
    logger.info(f"更新模式: {'增量更新' if args.incremental else '覆盖模式'}")
    logger.info("=" * 80)
    
    if args.period:
        # 采集分钟级数据
        success = collect_minute_data(
            stock_code=args.stock,
            period=args.period,
            start_date=args.start_date,
            end_date=args.end_date,
            incremental=args.incremental,
            save_available=args.save_available
        )
    else:
        # 采集日线数据
        success = collect_daily_data(
            stock_code=args.stock,
            start_date=args.start_date,
            end_date=args.end_date,
            incremental=args.incremental
        )
    
    if success:
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ 数据采集完成")
        logger.info("=" * 80)
    else:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ 数据采集失败")
        logger.error("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    main()
