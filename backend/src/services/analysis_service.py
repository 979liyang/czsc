# -*- coding: utf-8 -*-
"""
缠论分析服务

封装缠论分析业务逻辑。
"""
from typing import Dict, Any
import pandas as pd
from loguru import logger
from czsc.analyze import CZSC
from czsc.objects import RawBar

from ..utils import CZSCAdapter
from ..models.serializers import serialize_bis, serialize_fxs, serialize_zss


def _date_str(dt) -> str:
    """将 datetime 转为 YYYY-MM-DD 字符串便于展示"""
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


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
            # 数据可用范围（先用本次实际 bars 的范围，后续可替换为本地全量覆盖范围）
            'data_start_dt': bars[0].dt.isoformat() if bars else None,
            'data_end_dt': bars[-1].dt.isoformat() if bars else None,
            'requested_sdt': sdt,
            'requested_edt': edt,
            # 实际使用范围（YYYY-MM-DD），便于前端展示「实际使用范围」与 data_range_note 一致
            'effective_sdt': _date_str(bars[0].dt) if bars else None,
            'effective_edt': _date_str(bars[-1].dt) if bars else None,
            'gaps_summary': None,
        }

        # 当实际数据未覆盖请求区间时，生成说明（便于用户理解“为啥实际开始不是 sdt”）
        if bars:
            req_start = pd.to_datetime(sdt).date()
            req_end = pd.to_datetime(edt).date()
            actual_start = bars[0].dt.date() if hasattr(bars[0].dt, "date") else pd.to_datetime(bars[0].dt).date()
            actual_end = bars[-1].dt.date() if hasattr(bars[-1].dt, "date") else pd.to_datetime(bars[-1].dt).date()
            notes = []
            if actual_start > req_start:
                notes.append(f"请求开始时间为 {sdt}，但数据源中该标的最早数据为 {_date_str(bars[0].dt)}，分析基于实际可用数据。")
            if actual_end < req_end:
                notes.append(f"请求结束时间为 {edt}，但数据源中最晚数据为 {_date_str(bars[-1].dt)}。")
            if notes:
                result['data_range_note'] = " ".join(notes)

        # 计算统计信息（类似 demo/analyze.py）
        result['bars_raw_count'] = len(czsc.bars_raw)
        result['bars_ubi_count'] = len(czsc.bars_ubi)
        result['fx_count'] = len(czsc.fx_list)
        result['finished_bi_count'] = len(czsc.finished_bis)
        result['bi_count'] = len(czsc.bi_list)
        # ubi 是一个字典，需要检查是否存在
        ubi = czsc.ubi
        result['ubi_count'] = 1 if ubi else 0
        result['last_bi_extend'] = czsc.last_bi_extend

        # 提取最后一笔信息
        if czsc.finished_bis:
            last_bi = czsc.finished_bis[-1]
            result['last_bi_direction'] = last_bi.direction.value
            result['last_bi_power'] = last_bi.power
        else:
            result['last_bi_direction'] = None
            result['last_bi_power'] = None

        logger.info(f"缠论分析完成：{symbol} {freq}，笔{len(result['bis'])}条，"
                   f"分型{len(result['fxs'])}个，中枢{len(result['zss'])}个")

        return result
