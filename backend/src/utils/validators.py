# -*- coding: utf-8 -*-
"""
数据验证工具

验证RawBar数据格式和完整性。
"""
from typing import List
from loguru import logger
from czsc.objects import RawBar


def validate_raw_bar(bar: RawBar) -> bool:
    """
    验证单个RawBar数据格式

    :param bar: RawBar对象
    :return: 验证是否通过
    """
    errors = []

    # 验证必需字段
    if not bar.symbol:
        errors.append("symbol不能为空")
    if bar.id < 1:
        errors.append(f"id必须大于0，当前值：{bar.id}")
    if not bar.dt:
        errors.append("dt不能为空")
    if bar.freq is None:
        errors.append("freq不能为空")

    # 验证价格字段
    if bar.open < 0:
        errors.append(f"open必须大于等于0，当前值：{bar.open}")
    if bar.close < 0:
        errors.append(f"close必须大于等于0，当前值：{bar.close}")
    if bar.high < 0:
        errors.append(f"high必须大于等于0，当前值：{bar.high}")
    if bar.low < 0:
        errors.append(f"low必须大于等于0，当前值：{bar.low}")

    # 验证价格逻辑
    if bar.high < max(bar.open, bar.close):
        errors.append(f"high必须大于等于max(open, close)，当前值：high={bar.high}, "
                     f"open={bar.open}, close={bar.close}")
    if bar.low > min(bar.open, bar.close):
        errors.append(f"low必须小于等于min(open, close)，当前值：low={bar.low}, "
                     f"open={bar.open}, close={bar.close}")
    if bar.high < bar.low:
        errors.append(f"high必须大于等于low，当前值：high={bar.high}, low={bar.low}")

    # 验证成交量
    if bar.vol < 0:
        errors.append(f"vol必须大于等于0，当前值：{bar.vol}")
    if bar.amount < 0:
        errors.append(f"amount必须大于等于0，当前值：{bar.amount}")

    if errors:
        logger.error(f"RawBar验证失败：{bar.symbol} {bar.dt}，错误：{errors}")
        return False

    return True


def validate_bars(bars: List[RawBar]) -> tuple[bool, List[str]]:
    """
    验证RawBar列表的完整性和一致性

    :param bars: RawBar对象列表
    :return: (是否通过, 错误列表)
    """
    if not bars:
        return True, []

    errors = []
    symbol = bars[0].symbol
    freq = bars[0].freq

    # 验证每个bar
    for i, bar in enumerate(bars):
        if not validate_raw_bar(bar):
            errors.append(f"第{i+1}条K线验证失败")

        # 验证symbol和freq一致性
        if bar.symbol != symbol:
            errors.append(f"第{i+1}条K线的symbol不一致：期望{symbol}，实际{bar.symbol}")
        if bar.freq != freq:
            errors.append(f"第{i+1}条K线的freq不一致：期望{freq.value}，实际{bar.freq.value}")

    # 验证时间序列连续性
    dts = [bar.dt for bar in bars]
    if dts != sorted(dts):
        errors.append("时间序列不连续，dt必须按时间顺序排列")

    # 验证ID连续性
    ids = [bar.id for bar in bars]
    expected_ids = list(range(1, len(bars) + 1))
    if ids != expected_ids:
        errors.append(f"ID不连续，期望{expected_ids[:5]}...，实际{ids[:5]}...")

    # 验证时间唯一性
    if len(dts) != len(set(dts)):
        errors.append("存在重复的时间戳")

    if errors:
        logger.error(f"RawBar列表验证失败：{symbol} {freq.value}，共{len(errors)}个错误")
        return False, errors

    logger.debug(f"RawBar列表验证通过：{symbol} {freq.value}，共{len(bars)}条")
    return True, []


def validate_time_range(sdt: str, edt: str) -> bool:
    """
    验证时间范围

    :param sdt: 开始时间
    :param edt: 结束时间
    :return: 验证是否通过
    """
    from datetime import datetime

    try:
        sdt_dt = datetime.strptime(sdt.replace('-', ''), '%Y%m%d')
        edt_dt = datetime.strptime(edt.replace('-', ''), '%Y%m%d')

        if sdt_dt > edt_dt:
            logger.error(f"开始时间不能晚于结束时间：{sdt} > {edt}")
            return False

        return True
    except ValueError as e:
        logger.error(f"时间格式错误：{e}")
        return False
