# -*- coding: utf-8 -*-
"""
策略参数 Schema 与默认值

按 strategy_type 返回可展示的参数列表（name、type、default、description），
与 czsc.strategies 各 create_* 的 kwargs 一致，供前端渲染表单并预填默认值。
"""
from __future__ import annotations

from typing import Any, Dict, List

# 周期选项（与 czsc 常用一致，供前端 select）
_FREQ_OPTIONS = ["1分钟", "5分钟", "15分钟", "30分钟", "60分钟", "日线"]

# 通用参数（多数策略共有）
_COMMON = [
    {
        "name": "freq",
        "type": "string",
        "default": "15分钟",
        "description": "信号周期",
        "options": _FREQ_OPTIONS,
    },
    {
        "name": "base_freq",
        "type": "string",
        "default": "15分钟",
        "description": "基础周期",
        "options": _FREQ_OPTIONS,
    },
    {"name": "is_stocks", "type": "boolean", "default": True, "description": "是否 A 股（涨跌停过滤）"},
    {"name": "T0", "type": "boolean", "default": False, "description": "是否 T+0"},
    {"name": "interval", "type": "number", "default": 7200, "description": "同向开仓间隔(秒)"},
    {"name": "timeout", "type": "number", "default": 480, "description": "超时出场(K线数)"},
    {"name": "stop_loss", "type": "number", "default": 300, "description": "止损(点数)"},
]

# 单均线专用
_MA_EXTRA = [
    {
        "name": "ma_name",
        "type": "string",
        "default": "SMA#5",
        "description": "均线名称",
        "options": ["SMA#5", "SMA#10", "SMA#20", "SMA#40"],
    },
    {"name": "max_overlap", "type": "number", "default": 5, "description": "最大重叠数"},
]

# MACD 专用
_MACD_EXTRA = [
    {"name": "max_overlap", "type": "number", "default": 5, "description": "最大重叠数"},
]

# CCI 专用
_CCI_EXTRA = [
    {"name": "cci_timeperiod", "type": "number", "default": 14, "description": "CCI 周期"},
]

# EMV 专用
_EMV_EXTRA = [
    {"name": "di", "type": "number", "default": 1, "description": "EMV 日线偏移"},
]

# 三买/三卖 使用通用参数即可（timeout 默认 100 与 czsc 一致）
_THIRD_EXTRA = []

# 笔非多即空：仅 freq + interval/timeout/stop_loss/is_stocks（不用通用 base_freq/T0）
_LONG_SHORT_BI_SCHEMA = [
    {
        "name": "freq",
        "type": "string",
        "default": "30分钟",
        "description": "笔周期",
        "options": ["30分钟", "60分钟", "日线"],
    },
    {"name": "is_stocks", "type": "boolean", "default": True, "description": "是否 A 股（涨跌停过滤）"},
    {"name": "interval", "type": "number", "default": 3600 * 4, "description": "同向开仓间隔(秒)"},
    {"name": "timeout", "type": "number", "default": 16 * 30, "description": "超时出场(K线数)"},
    {"name": "stop_loss", "type": "number", "default": 500, "description": "止损(点数)"},
]


def _common_with_defaults(overrides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """通用参数 + 覆盖默认值（如 timeout 不同）"""
    base = [x.copy() for x in _COMMON]
    for ov in overrides:
        for b in base:
            if b.get("name") == ov.get("name"):
                b["default"] = ov["default"]
                break
    return base


# strategy_type -> 参数列表（与 czsc create_* kwargs 一致）
STRATEGY_PARAMS_SCHEMA: Dict[str, List[Dict[str, Any]]] = {
    "single_ma_long": _common_with_defaults([]) + _MA_EXTRA,
    "single_ma_short": _common_with_defaults([]) + _MA_EXTRA,
    "macd_long": _common_with_defaults([]) + _MACD_EXTRA,
    "macd_short": _common_with_defaults([]) + _MACD_EXTRA,
    "cci_long": _common_with_defaults([{"name": "timeout", "default": 480}]) + _CCI_EXTRA,
    "cci_short": _common_with_defaults([{"name": "timeout", "default": 480}]) + _CCI_EXTRA,
    "emv_long": _common_with_defaults([{"name": "timeout", "default": 100}]) + _EMV_EXTRA,
    "emv_short": _common_with_defaults([{"name": "timeout", "default": 100}]) + _EMV_EXTRA,
    "third_buy_long": _common_with_defaults([{"name": "timeout", "default": 100}]),
    "third_sell_short": _common_with_defaults([{"name": "timeout", "default": 100}]),
    "long_short_bi": _LONG_SHORT_BI_SCHEMA,
}


def get_params_schema(strategy_type: str | None) -> List[Dict[str, Any]]:
    """
    按 strategy_type 返回参数 schema（名称、类型、默认值、说明、可选 options）。
    未知类型返回空列表。
    """
    if not strategy_type:
        return []
    return [p.copy() for p in STRATEGY_PARAMS_SCHEMA.get(strategy_type, [])]


def get_default_params(strategy_type: str | None) -> Dict[str, Any]:
    """按 strategy_type 返回参数字典（仅 default 值），用于合并前端提交的 params。"""
    schema = get_params_schema(strategy_type)
    out: Dict[str, Any] = {}
    for p in schema:
        name = p.get("name")
        if name and "default" in p:
            out[name] = p["default"]
    return out
