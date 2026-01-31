# -*- coding: utf-8 -*-
"""
交易管理模块

提供交易信号生成、交易执行等功能
"""
from typing import List, Dict, Optional
from loguru import logger
from czsc.traders import CzscTrader, CzscSignals, generate_czsc_signals
from czsc.traders.base import CzscTrader as BaseCzscTrader
from czsc.objects import RawBar, Position, Signal
from czsc.utils.bar_generator import BarGenerator
from czsc.enum import Freq


class TradingManager:
    """交易管理器

    提供交易信号生成、交易执行等功能的封装
    """

    def __init__(self, symbol: str, base_freq: Freq, freqs: List[str] = None):
        """初始化交易管理器

        :param symbol: 标的代码
        :param base_freq: 基础K线周期
        :param freqs: K线周期列表，如果不提供则只使用base_freq
        """
        self.symbol = symbol
        self.base_freq = base_freq
        self.freqs = freqs or [str(base_freq.value)]
        self.trader: Optional[CzscTrader] = None
        self.bg: Optional[BarGenerator] = None

    def init_bar_generator(self, bars: List[RawBar], market: str = "A"):
        """初始化K线合成器

        :param bars: 基础周期K线数据
        :param market: 市场类型，默认为"A"（A股）
        :return: 交易管理器实例自身
        """
        try:
            freqs = self.freqs[1:] if len(self.freqs) > 1 else []
            self.bg = BarGenerator(
                base_freq=str(self.base_freq.value),
                freqs=freqs,
                market=market
            )
            # 初始化BarGenerator
            for bar in bars:
                self.bg.update(bar)
            logger.info(f"{self.symbol} K线合成器初始化完成")
            return self
        except Exception as e:
            logger.error(f"初始化K线合成器失败: {e}")
            raise

    def init_trader(self, positions: List[Position], signals_config: List[Dict] = None):
        """初始化交易者

        :param positions: 持仓策略列表
        :param signals_config: 信号配置列表，如果不提供则从positions中提取
        :return: 交易管理器实例自身
        """
        if self.bg is None:
            raise ValueError("请先调用 init_bar_generator 初始化K线合成器")

        try:
            from czsc.traders.sig_parse import get_signals_config

            if signals_config is None:
                # 从positions中提取信号配置
                unique_signals = []
                for pos in positions:
                    unique_signals.extend(pos.unique_signals)
                unique_signals = list(set(unique_signals))
                signals_config = get_signals_config(unique_signals, "czsc.signals")

            self.trader = CzscTrader(
                bg=self.bg,
                positions=positions,
                signals_config=signals_config
            )
            logger.info(f"{self.symbol} 交易者初始化完成，共 {len(positions)} 个持仓策略")
            return self
        except Exception as e:
            logger.error(f"初始化交易者失败: {e}")
            raise

    def update(self, bar: RawBar):
        """更新交易状态

        :param bar: 新的K线数据
        """
        if self.trader is None:
            raise ValueError("请先调用 init_trader 初始化交易者")
        if self.bg is None:
            raise ValueError("请先调用 init_bar_generator 初始化K线合成器")

        self.bg.update(bar)
        self.trader.on_bar(bar)

    def get_signals(self) -> Dict:
        """获取当前信号

        :return: 信号字典
        """
        if self.trader is None:
            raise ValueError("请先调用 init_trader 初始化交易者")
        return self.trader.s

    def get_positions(self) -> List[Position]:
        """获取持仓策略列表

        :return: 持仓策略列表
        """
        if self.trader is None:
            raise ValueError("请先调用 init_trader 初始化交易者")
        return self.trader.positions

    def get_operates(self) -> List[Dict]:
        """获取操作记录

        :return: 操作记录列表
        """
        if self.trader is None:
            raise ValueError("请先调用 init_trader 初始化交易者")
        operates = []
        for pos in self.trader.positions:
            operates.extend(pos.operates)
        return sorted(operates, key=lambda x: x['dt'])

    def generate_signals(self, bars: List[RawBar], freqs: List[str], 
                        signals_config: List[Dict], init_n: int = 2000, 
                        sdt: str = "20200101") -> Dict:
        """生成交易信号

        :param bars: K线数据列表
        :param freqs: K线周期列表
        :param signals_config: 信号配置列表
        :param init_n: 初始化K线数量
        :param sdt: 开始日期
        :return: 信号字典
        """
        try:
            signals = generate_czsc_signals(
                bars=bars,
                freqs=freqs,
                init_n=init_n,
                sdt=sdt,
                signals_config=signals_config
            )
            logger.info(f"{self.symbol} 信号生成完成，共 {len(signals)} 个信号")
            return signals
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            raise

    def get_czsc_signals(self) -> Optional[CzscSignals]:
        """获取CzscSignals对象

        :return: CzscSignals对象
        """
        if self.bg is None:
            raise ValueError("请先调用 init_bar_generator 初始化K线合成器")
        
        try:
            signals = CzscSignals(bg=self.bg)
            return signals
        except Exception as e:
            logger.error(f"获取CzscSignals失败: {e}")
            raise

