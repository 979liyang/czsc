# -*- coding: utf-8 -*-
"""
CZSC 功能对接示例脚本

展示如何使用 MySQL 数据库中的数据对接 czsc 的各种功能模块
"""
from datetime import datetime
from loguru import logger
from czsc.objects import Freq, RawBar
from czsc.analyze import CZSC
from czsc.akshare.czsc_adapter import get_symbols, get_raw_bars, check_data_availability


def example_1_basic_analysis():
    """示例1：基础缠论分析"""
    logger.info("=" * 60)
    logger.info("示例1：基础缠论分析")
    logger.info("=" * 60)
    
    # 获取标的列表
    symbols = get_symbols("all")
    if len(symbols) == 0:
        logger.warning("数据库中没有数据")
        return
    
    # 选择一只股票
    symbol = symbols[0]
    logger.info(f"分析标的: {symbol}")
    
    # 获取K线数据
    bars = get_raw_bars(symbol, Freq.D, "20220101", "20231231", "前复权")
    if len(bars) == 0:
        logger.warning("未获取到K线数据")
        return
    
    logger.info(f"获取到 {len(bars)} 根K线")
    
    # 创建 CZSC 分析对象
    c = CZSC(bars)
    
    # 获取分析结果
    logger.info(f"识别出 {len(c.bi_list)} 笔")
    logger.info(f"识别出 {len(c.fx_list)} 个分型")
    
    # 获取最后一笔
    if len(c.bi_list) > 0:
        last_bi = c.bi_list[-1]
        logger.info(f"最后一笔方向: {last_bi.direction.value}")
        logger.info(f"最后一笔高低点: {last_bi.low:.2f} - {last_bi.high:.2f}")


def example_2_multi_freq_analysis():
    """示例2：多周期分析"""
    logger.info("=" * 60)
    logger.info("示例2：多周期分析")
    logger.info("=" * 60)
    
    symbol = "000001.SZ"
    
    # 获取不同周期的数据
    freqs = [Freq.D, Freq.W]
    
    for freq in freqs:
        logger.info(f"\n分析周期: {freq.value}")
        
        # 检查数据可用性
        availability = check_data_availability(symbol, freq, "前复权")
        if not availability['available']:
            logger.warning(f"{freq.value} 数据不可用")
            continue
        
        # 获取K线数据
        bars = get_raw_bars(symbol, freq, "20220101", "20231231", "前复权")
        if len(bars) == 0:
            continue
        
        # 创建分析对象
        c = CZSC(bars)
        logger.info(f"  - K线数量: {len(bars)}")
        logger.info(f"  - 笔数量: {len(c.bi_list)}")
        logger.info(f"  - 分型数量: {len(c.fx_list)}")


def example_3_signals_analysis():
    """示例3：信号分析"""
    logger.info("=" * 60)
    logger.info("示例3：信号分析")
    logger.info("=" * 60)
    
    symbol = "000001.SZ"
    
    # 获取K线数据
    bars = get_raw_bars(symbol, Freq.D, "20220101", "20231231", "前复权")
    if len(bars) == 0:
        logger.warning("未获取到K线数据")
        return
    
    # 创建 CZSC 分析对象
    c = CZSC(bars)
    
    # 获取信号（如果有自定义信号函数）
    if c.signals:
        logger.info("信号分析结果:")
        for signal, value in list(c.signals.items())[:5]:  # 只显示前5个
            logger.info(f"  - {signal}: {value}")
    else:
        logger.info("当前没有信号数据")


def example_4_batch_analysis():
    """示例4：批量分析多只股票"""
    logger.info("=" * 60)
    logger.info("示例4：批量分析多只股票")
    logger.info("=" * 60)
    
    # 获取标的列表（限制数量）
    symbols = get_symbols("all")[:10]  # 只分析前10只
    
    results = []
    
    for symbol in symbols:
        try:
            # 获取K线数据
            bars = get_raw_bars(symbol, Freq.D, "20220101", "20231231", "前复权")
            if len(bars) < 100:  # 数据太少跳过
                continue
            
            # 创建分析对象
            c = CZSC(bars)
            
            result = {
                'symbol': symbol,
                'bars_count': len(bars),
                'bi_count': len(c.bi_list),
                'fx_count': len(c.fx_list)
            }
            
            # 获取最后一笔信息
            if len(c.bi_list) > 0:
                last_bi = c.bi_list[-1]
                result['last_bi_direction'] = last_bi.direction.value
                result['last_bi_range'] = f"{last_bi.low:.2f}-{last_bi.high:.2f}"
            
            results.append(result)
            logger.info(f"{symbol}: {len(c.bi_list)} 笔, {len(c.fx_list)} 分型")
            
        except Exception as e:
            logger.warning(f"{symbol} 分析失败: {e}")
    
    logger.info(f"\n批量分析完成，共分析 {len(results)} 只股票")


def example_5_with_traders():
    """示例5：与交易模块集成"""
    logger.info("=" * 60)
    logger.info("示例5：与交易模块集成")
    logger.info("=" * 60)
    
    try:
        from czsc.traders import CzscTrader, CzscSignals
        from czsc.utils.bar_generator import BarGenerator
        
        symbol = "000001.SZ"
        
        # 获取K线数据
        bars = get_raw_bars(symbol, Freq.D, "20220101", "20231231", "前复权")
        if len(bars) == 0:
            logger.warning("未获取到K线数据")
            return
        
        # 创建 BarGenerator
        bg = BarGenerator(base_freq=Freq.D, freqs=[Freq.D, Freq.W])
        
        # 更新数据
        for bar in bars:
            bg.update(bar)
        
        logger.info(f"BarGenerator 初始化完成")
        logger.info(f"  - 日线K线: {len(bg.bars[Freq.D])}")
        if Freq.W in bg.bars:
            logger.info(f"  - 周线K线: {len(bg.bars[Freq.W])}")
        
        # 创建信号对象（需要配置信号）
        # signals_config = [...]
        # cs = CzscSignals(bg, signals_config=signals_config)
        
    except ImportError as e:
        logger.warning(f"交易模块导入失败: {e}")


def example_6_with_strategies():
    """示例6：与策略模块集成"""
    logger.info("=" * 60)
    logger.info("示例6：与策略模块集成")
    logger.info("=" * 60)
    
    try:
        from czsc.strategies import CzscStrategyBase
        
        symbol = "000001.SZ"
        
        # 获取K线数据
        bars = get_raw_bars(symbol, Freq.D, "20220101", "20231231", "前复权")
        if len(bars) == 0:
            logger.warning("未获取到K线数据")
            return
        
        # 创建策略（需要自定义策略类）
        # class MyStrategy(CzscStrategyBase):
        #     ...
        # 
        # strategy = MyStrategy(symbol=symbol)
        # trader = strategy.replay(bars)
        
        logger.info("策略模块集成示例（需要自定义策略类）")
        
    except ImportError as e:
        logger.warning(f"策略模块导入失败: {e}")


def example_7_data_quality_check():
    """示例7：数据质量检查"""
    logger.info("=" * 60)
    logger.info("示例7：数据质量检查")
    logger.info("=" * 60)
    
    # 获取标的列表
    symbols = get_symbols("all")[:20]  # 检查前20只
    
    quality_report = {
        'total': len(symbols),
        'has_data': 0,
        'no_data': 0,
        'incomplete_data': 0
    }
    
    for symbol in symbols:
        availability = check_data_availability(symbol, Freq.D, "前复权")
        
        if availability['available']:
            quality_report['has_data'] += 1
            
            # 检查数据完整性
            if availability['count'] < 100:
                quality_report['incomplete_data'] += 1
                logger.warning(f"{symbol}: 数据不完整，只有 {availability['count']} 条")
        else:
            quality_report['no_data'] += 1
            logger.warning(f"{symbol}: 无数据")
    
    logger.info("\n数据质量报告:")
    logger.info(f"  总标的数: {quality_report['total']}")
    logger.info(f"  有数据: {quality_report['has_data']}")
    logger.info(f"  无数据: {quality_report['no_data']}")
    logger.info(f"  数据不完整: {quality_report['incomplete_data']}")


def run_all_examples():
    """运行所有示例"""
    logger.info("开始运行所有 CZSC 功能对接示例\n")
    
    try:
        example_1_basic_analysis()
        print()
        
        example_2_multi_freq_analysis()
        print()
        
        example_3_signals_analysis()
        print()
        
        example_4_batch_analysis()
        print()
        
        example_5_with_traders()
        print()
        
        example_6_with_strategies()
        print()
        
        example_7_data_quality_check()
        print()
        
        logger.info("=" * 60)
        logger.info("所有示例运行完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()

