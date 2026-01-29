# -*- coding: utf-8 -*-
"""
信号计算服务

封装信号计算业务逻辑。
"""
from typing import Dict, List, Any
from loguru import logger
from czsc.objects import RawBar
from czsc.utils.bar_generator import BarGenerator
from czsc.objects import RawBar
from czsc.traders.base import CzscSignals
from czsc.utils import import_by_name

from ..utils import CZSCAdapter


class SignalService:
    """信号计算服务"""

    def __init__(self, czsc_adapter: CZSCAdapter):
        """
        初始化信号服务

        :param czsc_adapter: CZSC适配器
        """
        self.adapter = czsc_adapter

    def calculate_signal(self, symbol: str, freq: str, signal_name: str,
                        sdt: str, edt: str, **params) -> Dict[str, str]:
        """
        计算单个信号

        :param symbol: 标的代码
        :param freq: K线周期
        :param signal_name: 信号函数名称（如：czsc.signals.cxt_bi_status_V230101）
        :param sdt: 开始时间
        :param edt: 结束时间
        :param params: 信号函数参数
        :return: 信号字典
        """
        logger.info(f"计算信号：{symbol} {freq} {signal_name}")

        # 获取K线数据
        bars = self.adapter.get_bars(symbol, freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {freq} {sdt} - {edt}")

        # 创建BarGenerator并初始化
        bg = BarGenerator(base_freq=freq, freqs=[])
        for bar in bars:
            bg.update(bar)

        # 创建信号配置
        signal_config = {
            'name': signal_name,
            'freq': freq,
            **params
        }

        # 计算信号
        signals = self.adapter.calculate_signals(bg, [signal_config])

        logger.info(f"信号计算完成：{symbol} {freq} {signal_name}，共{len(signals)}个信号")
        return signals

    def calculate_batch(self, symbol: str, freq: str, signal_configs: List[Dict[str, Any]],
                       sdt: str, edt: str) -> Dict[str, str]:
        """
        批量计算多个信号

        :param symbol: 标的代码
        :param freq: K线周期
        :param signal_configs: 信号配置列表
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 信号字典
        """
        logger.info(f"批量计算信号：{symbol} {freq}，共{len(signal_configs)}个信号")

        # 获取K线数据
        bars = self.adapter.get_bars(symbol, freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {freq} {sdt} - {edt}")

        # 创建BarGenerator并初始化
        bg = BarGenerator(base_freq=freq, freqs=[])
        for bar in bars:
            bg.update(bar)

        # 计算信号
        signals = self.adapter.calculate_signals(bg, signal_configs)

        logger.info(f"批量信号计算完成：{symbol} {freq}，共{len(signals)}个信号")
        return signals
