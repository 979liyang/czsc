# -*- coding: utf-8 -*-
"""
策略回测服务

封装策略回测业务逻辑。对应 czsc：strategy_config 含 strategy_class（策略类）、
strategy_kwargs（如 signals_config），通过策略的 backtest(bars, sdt=...) 得到交易记录与绩效。
"""
from typing import Dict, List, Any
from loguru import logger
from czsc.objects import RawBar, Position
from czsc.traders.base import CzscTrader
from czsc.utils.bar_generator import BarGenerator
from czsc.utils import import_by_name

from ..utils import CZSCAdapter
from .strategy_runner import build_position, make_strategy_with_position


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

        :param strategy_config: 策略配置，包含 strategy_class（czsc 策略类全限定名）、
                               strategy_kwargs（如 signals_config，与 czsc 策略入参一致）
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

    def run_backtest_by_strategy(
        self,
        strategy_type: str,
        symbol: str,
        sdt: str,
        edt: str,
        params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        按策略库 strategy_type + 参数执行个股回测。
        根据 strategy_type 调用对应 create_* 得到 Position，封装为策略后执行 backtest。
        """
        logger.info(f"开始按策略回测：strategy_type={strategy_type} symbol={symbol} {sdt} - {edt}")
        position = build_position(strategy_type, symbol, params)
        strategy = make_strategy_with_position(symbol, position)
        base_freq = strategy.base_freq
        bars = self.adapter.get_bars(symbol, base_freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {base_freq} {sdt} - {edt}")
        trader = strategy.backtest(bars, sdt=sdt)
        pairs = self._serialize_pairs(trader)
        operates = self._serialize_operates(trader)
        result = {
            "pairs": pairs,
            "operates": operates,
            "positions": self._serialize_positions(trader),
            "positions_summary": self._build_positions_summary(trader, pairs, last_n=5),
        }
        logger.info(f"按策略回测完成：{symbol}，共{len(operates)}次操作")
        return result

    def _build_positions_summary(
        self,
        trader: CzscTrader,
        pairs: Dict[str, Any],
        last_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """按持仓汇总：pos_name、operate_count、last_operates、evaluate，供前端按 demo 分块展示。"""
        summary = []
        for pos in trader.positions:
            pos_operates = []
            if hasattr(pos, "operates"):
                for op in pos.operates[-last_n:]:
                    pos_operates.append(self._serialize_one_operate(op, pos.name))
            summary.append({
                "pos_name": pos.name,
                "operate_count": len(pos.operates) if hasattr(pos, "operates") else 0,
                "last_operates": pos_operates,
                "evaluate": pairs.get(pos.name, {}),
            })
        return summary

    def _serialize_pairs(self, trader: CzscTrader) -> Dict[str, Any]:
        """序列化回测结果对。按多空/多头/空头分别调用 evaluate，供前端展示评估内容。"""
        pairs = {}
        for pos in trader.positions:
            if hasattr(pos, "evaluate"):
                try:
                    pairs[pos.name] = {
                        "多空合并": pos.evaluate("多空"),
                        "多头": pos.evaluate("多头"),
                        "空头": pos.evaluate("空头"),
                    }
                except Exception as e:
                    logger.warning(f"持仓 {pos.name} evaluate 失败: {e}")
                    pairs[pos.name] = {"多空合并": {}, "多头": {}, "空头": {}}
            else:
                pairs[pos.name] = {"多空合并": {}, "多头": {}, "空头": {}}
        return pairs

    def _op_to_readable(self, op_val: Any) -> str:
        """将 czsc Operate 枚举或其它值转为可读短名（如 LO/LE/SO/SE）。"""
        if op_val is None:
            return ""
        if hasattr(op_val, "name"):
            return getattr(op_val, "name", str(op_val))
        if hasattr(op_val, "value"):
            return str(getattr(op_val, "value", op_val))
        return str(op_val)

    def _serialize_one_operate(self, op: Any, pos_name: str) -> Dict[str, Any]:
        """将单条 operate（dict 或对象）转为 API 所需结构（dt、op、bid、price、amount）。"""
        if isinstance(op, dict):
            dt_val = op.get("dt")
            dt_str = dt_val.isoformat() if hasattr(dt_val, "isoformat") else str(dt_val)
            op_val = op.get("op", "")
            return {
                "pos_name": pos_name,
                "dt": dt_str,
                "op": self._op_to_readable(op_val),
                "bid": op.get("bid", 0),
                "price": op.get("price", 0),
                "amount": op.get("amount", 0),
            }
        dt_val = getattr(op, "dt", None)
        dt_str = dt_val.isoformat() if hasattr(dt_val, "isoformat") else str(dt_val)
        return {
            "pos_name": pos_name,
            "dt": dt_str,
            "op": self._op_to_readable(getattr(op, "op", "")),
            "bid": getattr(op, "bid", 0),
            "price": getattr(op, "price", 0),
            "amount": getattr(op, "amount", 0),
        }

    def _serialize_operates(self, trader: CzscTrader) -> List[Dict[str, Any]]:
        """序列化操作记录。czsc Position.operates 为字典列表，含 dt、op、bid、price 等。"""
        operates = []
        for pos in trader.positions:
            if hasattr(pos, "operates"):
                for op in pos.operates:
                    operates.append(self._serialize_one_operate(op, pos.name))
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
