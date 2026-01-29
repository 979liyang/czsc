# -*- coding: utf-8 -*-
"""
缠论分析服务

封装缠论分析业务逻辑。
"""
from typing import Dict, Any
from loguru import logger
from czsc.analyze import CZSC
from czsc.objects import RawBar

from ..utils import CZSCAdapter
from ..models.serializers import serialize_bis, serialize_fxs, serialize_zss


class AnalysisService:
    """缠论分析服务"""

    def __init__(self, czsc_adapter: CZSCAdapter):
        """
        初始化分析服务

        :param czsc_adapter: CZSC适配器
        """
        self.adapter = czsc_adapter

    def analyze(self, symbol: str, freq: str, sdt: str, edt: str) -> Dict[str, Any]:
        """
        执行缠论分析

        :param symbol: 标的代码
        :param freq: K线周期
        :param sdt: 开始时间
        :param edt: 结束时间
        :return: 分析结果字典，包含bis、fxs、zss
        """
        logger.info(f"开始缠论分析：{symbol} {freq} {sdt} - {edt}")

        # 获取K线数据
        bars = self.adapter.get_bars(symbol, freq, sdt, edt)
        if not bars:
            raise ValueError(f"未找到K线数据：{symbol} {freq} {sdt} - {edt}")

        # 执行缠论分析
        czsc = self.adapter.analyze(bars)

        # 序列化结果
        # 注意：CZSC类没有zs_list属性，中枢需要从笔中提取或单独计算
        result = {
            'symbol': symbol,
            'freq': freq,
            'bis': serialize_bis(czsc.bi_list),
            'fxs': serialize_fxs(czsc.fx_list),
            'zss': [],  # 中枢需要单独计算，暂时返回空列表
        }

        logger.info(f"缠论分析完成：{symbol} {freq}，笔{len(result['bis'])}条，"
                   f"分型{len(result['fxs'])}个，中枢{len(result['zss'])}个")

        return result
