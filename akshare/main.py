# -*- coding: utf-8 -*-
"""
主程序：使用 AkShare 获取股票数据并存储到 MySQL

功能：
1. 获取上证、深证、创业板股票列表
2. 获取历史K线数据
3. 存储到 MySQL 数据库
4. 提供对接 CZSC 的接口
"""
import argparse
from datetime import datetime, timedelta
from loguru import logger
from czsc.akshare.database import init_database, get_db_manager
from czsc.akshare.fetch_data import get_stock_list_by_market
from czsc.akshare.store_data import sync_all_stocks, batch_store_stocks
from czsc.akshare.czsc_adapter import get_symbols, get_raw_bars, check_data_availability
from czsc.objects import Freq


def main_fetch_and_store(markets=None, start_date=None, end_date=None, 
                         adjust="qfq", freq="D", delay=0.1):
    """主函数：获取并存储股票数据
    
    :param markets: 市场列表，如 ['sh', 'sz', 'cyb']
    :param start_date: 开始日期，格式：YYYYMMDD
    :param end_date: 结束日期，格式：YYYYMMDD
    :param adjust: 复权类型
    :param freq: K线周期
    :param delay: 请求延迟（秒）
    """
    logger.info("=" * 60)
    logger.info("开始获取并存储股票数据")
    logger.info("=" * 60)
    
    # 初始化数据库
    logger.info("初始化数据库...")
    init_database()
    
    # 如果没有指定开始日期，默认获取最近1年数据
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    logger.info(f"数据时间范围: {start_date} - {end_date}")
    logger.info(f"市场: {markets if markets else '全部'}")
    logger.info(f"复权类型: {adjust}")
    logger.info(f"K线周期: {freq}")
    
    # 同步数据
    results = sync_all_stocks(
        markets=markets,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
        freq=freq,
        delay=delay
    )
    
    # 统计结果
    total = len(results)
    success = sum(1 for v in results.values() if v > 0)
    total_records = sum(results.values())
    
    logger.info("=" * 60)
    logger.info("数据获取和存储完成")
    logger.info(f"成功: {success}/{total} 只股票")
    logger.info(f"总记录数: {total_records} 条")
    logger.info("=" * 60)
    
    return results


def main_test_czsc_adapter():
    """测试 CZSC 适配器"""
    logger.info("=" * 60)
    logger.info("测试 CZSC 适配器")
    logger.info("=" * 60)
    
    # 获取标的列表
    symbols = get_symbols("all")
    logger.info(f"数据库中共有 {len(symbols)} 个标的")
    
    if len(symbols) == 0:
        logger.warning("数据库中没有数据，请先运行数据获取程序")
        return
    
    # 测试获取单只股票数据
    test_symbol = symbols[0]
    logger.info(f"\n测试标的: {test_symbol}")
    
    # 检查数据可用性
    availability = check_data_availability(test_symbol, Freq.D, "前复权")
    logger.info(f"数据可用性: {availability}")
    
    if availability['available']:
        # 获取K线数据
        bars = get_raw_bars(test_symbol, Freq.D, "20230101", "20231231", "前复权")
        logger.info(f"获取到 {len(bars)} 根K线")
        
        if len(bars) > 0:
            logger.info(f"第一根K线: {bars[0].dt} - 收盘价: {bars[0].close}")
            logger.info(f"最后一根K线: {bars[-1].dt} - 收盘价: {bars[-1].close}")
            
            # 测试使用 CZSC 分析
            try:
                from czsc.analyze import CZSC
                c = CZSC(bars)
                logger.info(f"CZSC 分析完成，识别出 {len(c.bi_list)} 笔")
            except Exception as e:
                logger.warning(f"CZSC 分析失败: {e}")


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(description='AkShare 股票数据获取和存储工具')
    
    parser.add_argument('--action', type=str, default='fetch',
                       choices=['fetch', 'test'],
                       help='操作类型：fetch-获取并存储数据，test-测试适配器')
    
    parser.add_argument('--markets', type=str, nargs='+',
                       choices=['sh', 'sz', 'cyb'],
                       help='要获取的市场，可以指定多个，如 --markets sh sz')
    
    parser.add_argument('--start-date', type=str,
                       help='开始日期，格式：YYYYMMDD')
    
    parser.add_argument('--end-date', type=str,
                       help='结束日期，格式：YYYYMMDD')
    
    parser.add_argument('--adjust', type=str, default='qfq',
                       choices=['qfq', 'hfq', 'none'],
                       help='复权类型：qfq-前复权，hfq-后复权，none-不复权')
    
    parser.add_argument('--freq', type=str, default='D',
                       choices=['1min', '5min', '15min', '30min', '60min', 'D', 'W', 'M'],
                       help='K线周期')
    
    parser.add_argument('--delay', type=float, default=0.1,
                       help='请求延迟（秒），避免请求过快')
    
    args = parser.parse_args()
    
    if args.action == 'fetch':
        main_fetch_and_store(
            markets=args.markets,
            start_date=args.start_date,
            end_date=args.end_date,
            adjust=args.adjust,
            freq=args.freq,
            delay=args.delay
        )
    elif args.action == 'test':
        main_test_czsc_adapter()


if __name__ == "__main__":
    # 如果直接运行，默认执行测试
    import sys
    if len(sys.argv) == 1:
        # 没有参数时，先尝试获取少量数据测试
        logger.info("没有指定参数，执行测试模式")
        main_test_czsc_adapter()
    else:
        main()

