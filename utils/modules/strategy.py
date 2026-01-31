# -*- coding: utf-8 -*-
"""
策略管理模块

提供策略创建、回测、评估等功能
"""
from typing import List, Dict, Optional, Callable
from pathlib import Path
from loguru import logger
from czsc.strategies import CzscStrategyBase
from czsc.traders import DummyBacktest
from czsc.objects import Position, RawBar
from czsc.enum import Freq


class StrategyManager:
    """策略管理器

    提供策略创建、回测、评估等功能的封装
    """

    def __init__(self, strategy_class: type = None):
        """初始化策略管理器

        :param strategy_class: 策略类，必须是CzscStrategyBase的子类
        """
        self.strategy_class = strategy_class
        self.strategy: Optional[CzscStrategyBase] = None

    def create_strategy(self, symbol: str, **kwargs) -> CzscStrategyBase:
        """创建策略实例

        :param symbol: 标的代码
        :param kwargs: 策略初始化参数
        :return: 策略实例
        """
        if self.strategy_class is None:
            raise ValueError("请先设置策略类 strategy_class")

        if not issubclass(self.strategy_class, CzscStrategyBase):
            raise ValueError("策略类必须是 CzscStrategyBase 的子类")

        try:
            self.strategy = self.strategy_class(symbol=symbol, **kwargs)
            logger.info(f"{symbol} 策略创建成功")
            return self.strategy
        except Exception as e:
            logger.error(f"创建策略失败: {e}")
            raise

    def set_strategy(self, strategy: CzscStrategyBase):
        """设置策略实例

        :param strategy: 策略实例
        """
        if not isinstance(strategy, CzscStrategyBase):
            raise ValueError("策略必须是 CzscStrategyBase 的实例")
        self.strategy = strategy

    def get_positions(self) -> List[Position]:
        """获取持仓策略列表

        :return: 持仓策略列表
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")
        return self.strategy.positions

    def get_signals_config(self) -> List[Dict]:
        """获取信号配置

        :return: 信号配置列表
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")
        return self.strategy.signals_config

    def get_freqs(self) -> List[str]:
        """获取K线周期列表

        :return: K线周期列表
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")
        return self.strategy.sorted_freqs

    def init_trader(self, bars: List[RawBar], **kwargs):
        """初始化交易者

        :param bars: 基础周期K线数据
        :param kwargs: 初始化参数（sdt, n, bg等）
        :return: 交易者实例
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")

        try:
            trader = self.strategy.init_trader(bars=bars, **kwargs)
            logger.info(f"{self.strategy.symbol} 交易者初始化完成")
            return trader
        except Exception as e:
            logger.error(f"初始化交易者失败: {e}")
            raise

    def replay(self, bars: List[RawBar], res_path: str = None, 
               sdt: str = "20200101", refresh: bool = True):
        """回放策略执行过程

        :param bars: 基础周期K线数据
        :param res_path: 结果保存路径
        :param sdt: 开始日期
        :param refresh: 是否刷新结果
        :return: 交易者实例
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")

        try:
            if res_path:
                res_path = Path(res_path)
                res_path.mkdir(parents=True, exist_ok=True)

            trader = self.strategy.replay(
                bars=bars,
                res_path=res_path,
                sdt=sdt,
                refresh=refresh
            )
            logger.info(f"{self.strategy.symbol} 策略回放完成")
            return trader
        except Exception as e:
            logger.error(f"策略回放失败: {e}")
            raise

    def save_positions(self, save_path: str):
        """保存持仓策略到文件

        :param save_path: 保存路径
        """
        if self.strategy is None:
            raise ValueError("请先创建或设置策略")

        try:
            save_path = Path(save_path)
            save_path.mkdir(parents=True, exist_ok=True)
            self.strategy.save_positions(save_path)
            logger.info(f"持仓策略已保存到 {save_path}")
        except Exception as e:
            logger.error(f"保存持仓策略失败: {e}")
            raise

    def create_dummy_backtest(self, read_bars: Callable, signals_module_name: str = "czsc.signals",
                             sdt: str = "20200101", edt: str = "20230101",
                             signals_path: str = None, results_path: str = None) -> DummyBacktest:
        """创建快速回测对象

        :param read_bars: 读取K线数据的函数
        :param signals_module_name: 信号模块名称
        :param sdt: 开始日期
        :param edt: 结束日期
        :param signals_path: 信号保存路径
        :param results_path: 结果保存路径
        :return: DummyBacktest实例
        """
        if self.strategy_class is None:
            raise ValueError("请先设置策略类 strategy_class")

        try:
            dummy = DummyBacktest(
                strategy=self.strategy_class,
                read_bars=read_bars,
                signals_module_name=signals_module_name,
                sdt=sdt,
                edt=edt,
                signals_path=signals_path,
                results_path=results_path
            )
            logger.info("快速回测对象创建成功")
            return dummy
        except Exception as e:
            logger.error(f"创建快速回测对象失败: {e}")
            raise

