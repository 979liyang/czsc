# -*- coding: utf-8 -*-
"""
信号同步服务：从 DocService 获取全部信号并转为 signals 表行数据
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from loguru import logger

from ..services.doc_service import DocService


def _param_template_from_signal_info(signal_info: Dict[str, Any]) -> Optional[str]:
    """从 DocService 返回的 signal_info 中提取 param_template"""
    params = signal_info.get("params") or []
    for p in params:
        if p.get("name") == "参数模板" and p.get("default"):
            return str(p["default"])
    signals = signal_info.get("signals") or []
    if signals:
        return signals[0]
    desc = signal_info.get("description") or ""
    m = re.search(r"参数模板[：:]\s*[\"']([^\"']+)[\"']", desc)
    if m:
        return m.group(1)
    return None


def build_signal_func_rows(signals_module: str = "czsc.signals") -> List[Dict[str, Any]]:
    """
    调用 DocService.get_all_signals()，将每条转为 signals 表所需字段。

    :param signals_module: 信号模块名，默认 czsc.signals
    :return: List[Dict]，每项含 name, module_path, category, param_template, description
    """
    doc_svc = DocService(signals_module=signals_module)
    all_signals = doc_svc.get_all_signals()
    rows = []
    for s in all_signals:
        full_name = s.get("full_name") or ""
        module_path = ".".join(full_name.split(".")[:-1]) if full_name else "czsc.signals"
        param_template = _param_template_from_signal_info(s)
        rows.append({
            "name": s.get("name", ""),
            "module_path": module_path or "czsc.signals",
            "category": s.get("category"),
            "param_template": param_template,
            "description": s.get("description"),
        })
    logger.info(f"从 {signals_module} 生成 {len(rows)} 条 signals 行数据")
    return rows
