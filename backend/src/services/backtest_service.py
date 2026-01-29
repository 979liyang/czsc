# -*- coding: utf-8 -*-
"""
策略回测服务

封装策略回测业务逻辑。
"""
from typing import Dict, List, Any
from loguru import logger
from czsc.objects import RawBar, Position
from czsc.traders.base import CzscTrader
from czsc.utils.bar_generator import BarGenerator
from czsc.utils import import_by_name

from ..utils import CZSCAdapter


class BacktestService:
    """策略回测服务"""

    def __init__(self, czsc_adapter: CZSCAdapter):
        """
        初始化回测服务

        :param czsc_adapter: CZSC适配器
        """
        self.adapter = czsc_adapter

    def run_backtest(self, strategy_config: Dict[str, Any], symbol: str,
                    sdt: str, edt: str) -> Dict[str, Any]:
        """
        执行策略回测

        :param strategy_config: 策略配置，包含strategy_class、positions、signals_config等
        :param symbol: 标的代码
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 回测结果字典
        """
        logger.info(f"开始策略回测：{symbol} {sdt} - {edt}")

        # 获取策略类
        strategy_class_name = strategy_config.get('strategy_class')
        if not strategy_class_name:
            raise ValueError("策略配置中必须包含strategy_class字段")

        try:
            StrategyClass = import_by_name(strategy_class_name)
        except Exception as e:
            raise ValueError(f"无法导入策略类：{strategy_class_name}，错误：{e}")

        # 创建策略实例
        strategy_kwargs = strategy_config.get('strategy_kwargs', {})
        strategy = StrategyClass(symbol=symbol, **strategy_kwargs)

        # 获取K线数据
        base_freq = strategy.base_freq
        bars = self.adapter.get_bars(symbol, base_freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {base_freq} {sdt} - {edt}")

        # 执行回测
        trader = strategy.backtest(bars, sdt=sdt)

        # 序列化结果
        result = {
            'pairs': self._serialize_pairs(trader),
            'operates': self._serialize_operates(trader),
            'positions': self._serialize_positions(trader),
        }

        logger.info(f"策略回测完成：{symbol}，共{len(result['operates'])}次操作")
        return result

    def _serialize_pairs(self, trader: CzscTrader) -> Dict[str, Any]:
        """序列化回测结果对"""
        pairs = {}
        for pos in trader.positions:
            if hasattr(pos, 'evaluate'):
                eval_result = pos.evaluate()
                pairs[pos.name] = {
                    '多空合并': eval_result.get('多空合并', {}),
                    '多头': eval_result.get('多头', {}),
                    '空头': eval_result.get('空头', {}),
                }
        return pairs

    def _serialize_operates(self, trader: CzscTrader) -> List[Dict[str, Any]]:
        """序列化操作记录"""
        operates = []
        for pos in trader.positions:
            if hasattr(pos, 'operates'):
                for op in pos.operates:
                    operates.append({
                        'pos_name': pos.name,
                        'dt': op.dt.isoformat() if hasattr(op.dt, 'isoformat') else str(op.dt),
                        'op': str(op.op),
                        'price': op.price,
                        'amount': op.amount,
                    })
        return operates

    def _serialize_positions(self, trader: CzscTrader) -> List[Dict[str, Any]]:
        """序列化持仓记录"""
        positions = []
        for pos in trader.positions:
            positions.append({
                'name': pos.name,
                'symbol': pos.symbol,
                'pos': pos.pos if hasattr(pos, 'pos') else 0,
            })
        return positions
