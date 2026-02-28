# -*- coding: utf-8 -*-
"""
按 strategy_type + 参数动态构建 Position，并封装为可回测的策略

供 run_backtest_by_strategy 使用：根据策略库中的 strategy_type 调用对应
czsc.strategies.create_*，传入 symbol 与合并后的 params，得到 Position，
再封装为单 Position 的 CzscStrategyBase 用于 backtest。
"""
from __future__ import annotations

from typing import Any, Dict, List

from czsc.objects import Position
from czsc.strategies import CzscStrategyBase
from loguru import logger

from .strategy_params_schema import get_default_params


# strategy_type -> (create_func_name, 是否需要 ma_name 等额外位置参数)
_CREATORS = {
    "single_ma_long": ("create_single_ma_long", ["ma_name"]),
    "single_ma_short": ("create_single_ma_short", ["ma_name"]),
    "macd_long": ("create_macd_long", []),
    "macd_short": ("create_macd_short", []),
    "cci_long": ("create_cci_long", []),
    "cci_short": ("create_cci_short", []),
    "emv_long": ("create_emv_long", []),
    "emv_short": ("create_emv_short", []),
    "third_buy_long": ("create_third_buy_long", []),
    "third_sell_short": ("create_third_sell_short", []),
    "long_short_bi": ("create_long_short_bi", []),
}


def build_position(strategy_type: str, symbol: str, params: Dict[str, Any] | None = None) -> Position:
    """
    根据 strategy_type 调用对应 czsc.strategies.create_*，传入 symbol 与合并后的 kwargs。
    params 与 schema 默认值合并，is_stocks 默认 True。
    """
    if strategy_type not in _CREATORS:
        raise ValueError(f"不支持的 strategy_type: {strategy_type}，支持: {list(_CREATORS.keys())}")
    func_name, pos_args = _CREATORS[strategy_type]
    defaults = get_default_params(strategy_type)
    merged = dict(defaults)
    if params:
        for k, v in params.items():
            if v is not None:
                merged[k] = v
    merged.setdefault("is_stocks", True)

    from czsc import strategies as czsc_strategies
    create_fn = getattr(czsc_strategies, func_name, None)
    if not create_fn:
        raise ValueError(f"czsc.strategies 中未找到 {func_name}")

    if pos_args:
        # 需要位置参数，如 ma_name
        pos_values = [merged.pop(a, defaults.get(a)) for a in pos_args]
        pos = create_fn(symbol, *pos_values, **merged)
    else:
        pos = create_fn(symbol, **merged)
    logger.debug(f"build_position {strategy_type} symbol={symbol} -> {pos.name}")
    return pos


class _SinglePositionStrategy(CzscStrategyBase):
    """单 Position 策略包装，供 backtest 使用"""

    def __init__(self, symbol: str, position: Position):
        super().__init__(symbol=symbol)
        self._position = position

    @property
    def positions(self) -> List[Position]:
        return [self._position]


def make_strategy_with_position(symbol: str, position: Position) -> CzscStrategyBase:
    """将单个 Position 封装为 CzscStrategyBase，用于 backtest(bars, sdt=...)"""
    return _SinglePositionStrategy(symbol=symbol, position=position)
