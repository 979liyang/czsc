# -*- coding: utf-8 -*-
"""
AkShare 模块使用示例

演示如何使用 AkShare 数据源与 CZSC 框架集成
"""
from akshare.manager import AkShareDataManager
from akshare.base import get_real_time_data, get_minute_data, get_historical_data
from modules.analyze import CZSCAnalyzer
from czsc.objects import Freq


def example_basic_usage():
    """基础使用示例"""
    print("=" * 50)
    print("示例1：基础数据获取")
    print("=" * 50)
    
    # 创建数据管理器
    manager = AkShareDataManager()
    
    # 获取历史日线数据
    bars = manager.get_raw_bars(
        symbol="000001",  # 支持多种格式
        freq=Freq.D,
        sdt="20230101",
        edt="20231231"
    )
    print(f"获取到 {len(bars)} 根日线K线")
    
    # 获取分钟数据
    bars_5min = manager.get_raw_bars(
        symbol="000001.SZ",
        freq=Freq.F5,
        sdt="20231201",
        edt="20231231"
    )
    print(f"获取到 {len(bars_5min)} 根5分钟K线")
    
    # 获取标的列表
    symbols = manager.get_symbols("A股")
    print(f"获取到 {len(symbols)} 个标的")
    print(f"前5个标的：{symbols[:5]}")


def example_with_analyzer():
    """与分析器集成示例"""
    print("\n" + "=" * 50)
    print("示例2：与 CZSC 分析器集成")
    print("=" * 50)
    
    # 创建数据管理器
    manager = AkShareDataManager()
    
    # 获取K线数据
    bars = manager.get_raw_bars("000001", Freq.D, "20200101", "20231231")
    
    if len(bars) > 0:
        # 创建分析器
        analyzer = CZSCAnalyzer(symbol="000001.SZ", freq=Freq.D)
        
        # 加载并分析
        analyzer.load_bars(bars)
        
        # 获取分析结果
        bis = analyzer.get_bis()
        print(f"识别出 {len(bis)} 笔")
        
        fxs = analyzer.get_fxs()
        print(f"识别出 {len(fxs)} 个分型")
        
        # 获取最后一笔
        last_bi = analyzer.get_last_bi()
        if last_bi:
            print(f"最后一笔方向：{last_bi.direction.value}")
            print(f"最后一笔高低点：{last_bi.low} - {last_bi.high}")


def example_real_time_data():
    """实时数据示例"""
    print("\n" + "=" * 50)
    print("示例3：获取实时行情数据")
    print("=" * 50)
    
    # 获取实时行情
    real_time_df = get_real_time_data()
    
    if real_time_df is not None:
        print(f"获取到 {len(real_time_df)} 只股票实时数据")
        # 显示前5只股票
        if '代码' in real_time_df.columns and '名称' in real_time_df.columns:
            print(real_time_df[['代码', '名称', '最新价', '涨跌幅', '成交量']].head())


def example_minute_data():
    """分钟数据示例"""
    print("\n" + "=" * 50)
    print("示例4：获取分钟级别数据")
    print("=" * 50)
    
    # 获取5分钟数据
    minute_df = get_minute_data("sz000001", period="5")
    
    if minute_df is not None:
        print(f"获取到 {len(minute_df)} 条5分钟数据")
        print(minute_df.head())


if __name__ == "__main__":
    try:
        # 运行示例
        example_basic_usage()
        example_with_analyzer()
        example_real_time_data()
        example_minute_data()
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        print("=" * 50)
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()

