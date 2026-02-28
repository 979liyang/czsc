# -*- coding: utf-8 -*-
"""
筛选任务服务：按信号函数/因子对股票池计算并写入 ScreenResult。

与 CZSC 对应关系：
- run_signal_screen：按 signals 表（信号库元数据）逐只、逐信号计算，对应 czsc 的「全量信号扫描」。
- run_factor_screen：按 factors 表（因子库，signals_config 多条信号或 expression_or_signal_ref 单条）逐只、逐因子计算，对应 czsc 的「因子维度」筛选，结果带 factor_id。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import FactorDef, ScreenResult, ScreenTaskRun, SignalFunc
from ..storage.stock_basic_repo import StockBasicRepo
from ..utils import CZSCAdapter
from ..storage import KlineStorage
from .signal_service import SignalService


def _default_data_path() -> Path:
    import os
    return Path(os.getenv("DATA_PATH", "data"))


def run_signal_screen(
    session: Session,
    trade_date: str,
    market: Optional[str] = None,
    signal_service: Optional[SignalService] = None,
    max_symbols: int = 0,
) -> int:
    """
    执行信号筛选：对股票池在 trade_date 计算已启用的信号函数，结果写入 ScreenResult。
    对应 czsc：使用 signals 表中的信号函数名参与 CzscSignals 计算，结果按「信号维度」落库。

    :param session: 数据库会话
    :param trade_date: 交易日 YYYYMMDD
    :param market: 市场过滤 SH/SZ，为空则全市场
    :param signal_service: 信号计算服务，为 None 时内部创建（需 K 线数据）
    :param max_symbols: 最多处理股票数，0 表示不限制
    :return: 写入的 ScreenResult 条数
    """
    task = ScreenTaskRun(
        task_type="signal",
        run_at=datetime.now(),
        status="running",
        params_json=json.dumps({"trade_date": trade_date, "market": market or ""}),
    )
    session.add(task)
    session.flush()
    task_run_id = task.id

    try:
        signal_funcs = (
            session.query(SignalFunc).filter(SignalFunc.is_active == 1).all()
        )
        if not signal_funcs:
            logger.warning("没有启用的信号函数，跳过筛选")
            task.status = "success"
            return 0

        symbols = StockBasicRepo(session).list_symbols(market=market)
        if max_symbols > 0:
            symbols = symbols[:max_symbols]
        if not symbols:
            logger.warning("股票池为空，跳过筛选")
            task.status = "success"
            return 0

        if signal_service is None:
            kline_storage = KlineStorage(_default_data_path() / "klines")
            adapter = CZSCAdapter(kline_storage=kline_storage)
            signal_service = SignalService(czsc_adapter=adapter)

        sdt = (
            datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=120)
        ).strftime("%Y%m%d")
        edt = trade_date
        freq = "日线"
        count = 0

        for symbol in symbols:
            for sig in signal_funcs:
                try:
                    config = {
                        "name": sig.module_path + "." + sig.name
                        if sig.module_path
                        else sig.name,
                        "freq": freq,
                        "di": 1,
                    }
                    signals = signal_service.calculate_batch(
                        symbol, freq, [config], sdt, edt
                    )
                    if not signals:
                        continue
                    row = ScreenResult(
                        task_run_id=task_run_id,
                        symbol=symbol,
                        signal_name=sig.name,
                        factor_id=None,
                        trade_date=trade_date,
                        value_result=json.dumps(signals, ensure_ascii=False),
                    )
                    session.add(row)
                    count += 1
                except Exception as e:
                    logger.debug(f"信号计算跳过 {symbol} {sig.name}: {e}")
                    continue

        task.status = "success"
        logger.info(f"信号筛选完成：task_run_id={task_run_id}，写入 {count} 条")
        return count
    except Exception as e:
        logger.exception(f"筛选任务失败: {e}")
        task.status = "failed"
        raise


def run_factor_screen(
    session: Session,
    trade_date: str,
    market: Optional[str] = None,
    signal_service: Optional[SignalService] = None,
    max_symbols: int = 0,
) -> int:
    """
    执行因子筛选：对股票池在 trade_date 计算已启用的因子（通过关联信号函数计算），
    结果写入 ScreenResult（factor_id、value_result）。
    对应 czsc：factors.signals_config 解析为多条信号配置参与计算，或 expression_or_signal_ref 单条，按「因子维度」落库供选股/报表使用。

    :param session: 数据库会话
    :param trade_date: 交易日 YYYYMMDD
    :param market: 市场过滤 SH/SZ，为空则全市场
    :param signal_service: 信号计算服务，为 None 时内部创建（需 K 线数据）
    :param max_symbols: 最多处理股票数，0 表示不限制
    :return: 写入的 ScreenResult 条数
    """
    task = ScreenTaskRun(
        task_type="factor",
        run_at=datetime.now(),
        status="running",
        params_json=json.dumps({"trade_date": trade_date, "market": market or ""}),
    )
    session.add(task)
    session.flush()
    task_run_id = task.id

    try:
        factor_defs_list = (
            session.query(FactorDef).filter(FactorDef.is_active == 1).all()
        )
        factor_defs_list = [
            f for f in factor_defs_list
            if f.signals_config or f.expression_or_signal_ref
        ]
        if not factor_defs_list:
            logger.warning("没有启用的因子或因子未配置 signals_config/expression_or_signal_ref，跳过筛选")
            task.status = "success"
            return 0

        symbols = StockBasicRepo(session).list_symbols(market=market)
        if max_symbols > 0:
            symbols = symbols[:max_symbols]
        if not symbols:
            logger.warning("股票池为空，跳过筛选")
            task.status = "success"
            return 0

        if signal_service is None:
            kline_storage = KlineStorage(_default_data_path() / "klines")
            adapter = CZSCAdapter(kline_storage=kline_storage)
            signal_service = SignalService(czsc_adapter=adapter)

        sdt = (
            datetime.strptime(trade_date, "%Y%m%d") - timedelta(days=120)
        ).strftime("%Y%m%d")
        edt = trade_date
        freq = "日线"
        count = 0

        for symbol in symbols:
            for fd in factor_defs_list:
                try:
                    if fd.signals_config:
                        try:
                            configs = json.loads(fd.signals_config)
                        except (TypeError, ValueError):
                            configs = []
                        if not isinstance(configs, list):
                            configs = []
                        # 每条为 CzscSignals 入参格式：name, freq, di, 及信号参数字段
                        signal_configs = [
                            {k: v for k, v in c.items() if k != "factor_name"}
                            for c in configs
                        ]
                    else:
                        signal_configs = [
                            {
                                "name": fd.expression_or_signal_ref,
                                "freq": freq,
                                "di": 1,
                            }
                        ]
                    if not signal_configs:
                        continue
                    signals = signal_service.calculate_batch(
                        symbol, freq, signal_configs, sdt, edt
                    )
                    if not signals:
                        continue
                    row = ScreenResult(
                        task_run_id=task_run_id,
                        symbol=symbol,
                        signal_name=None,
                        factor_id=fd.id,
                        trade_date=trade_date,
                        value_result=json.dumps(signals, ensure_ascii=False),
                    )
                    session.add(row)
                    count += 1
                except Exception as e:
                    logger.debug(f"因子计算跳过 {symbol} {fd.name}: {e}")
                    continue

        task.status = "success"
        logger.info(f"因子筛选完成：task_run_id={task_run_id}，写入 {count} 条")
        return count
    except Exception as e:
        logger.exception(f"因子筛选任务失败: {e}")
        task.status = "failed"
        raise
