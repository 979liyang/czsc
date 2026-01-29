# -*- coding: utf-8 -*-
"""
数据获取服务

封装数据获取业务逻辑。
"""
from typing import List
from loguru import logger
from czsc.objects import RawBar

from ..utils import CZSCAdapter
from ..models.serializers import serialize_raw_bars


class DataService:
    """数据获取服务"""

    def __init__(self, czsc_adapter: CZSCAdapter):
        """
        初始化数据服务

        :param czsc_adapter: CZSC适配器
        """
        self.adapter = czsc_adapter

    def get_bars(self, symbol: str, freq: str, sdt: str, edt: str) -> List[dict]:
        """
        获取K线数据

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 序列化后的K线数据列表
        """
        logger.info(f"获取K线数据：{symbol} {freq} {sdt} - {edt}")

        bars = self.adapter.get_bars(symbol, freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {freq} {sdt} - {edt}")

        # 序列化
        result = serialize_raw_bars(bars)
        logger.info(f"获取K线数据完成：{symbol} {freq}，共{len(result)}条")
        return result
