# -*- coding: utf-8 -*-
"""
缠论分析模块

提供缠论分型、笔识别等核心分析功能
"""
from typing import List, Optional, Dict
from loguru import logger
from czsc.analyze import CZSC
from czsc.objects import RawBar, BI, FX, NewBar
from czsc.enum import Freq


class CZSCAnalyzer:
    """缠论分析器封装类

    提供对CZSC分析功能的便捷封装
    """

    def __init__(self, symbol: str, freq: Freq, max_bi_num: int = 50):
        """初始化分析器

        :param symbol: 标的代码
        :param freq: K线周期
        :param max_bi_num: 最大保留笔数量
        """
        self.symbol = symbol
        self.freq = freq
        self.max_bi_num = max_bi_num
        self.czsc: Optional[CZSC] = None

    def load_bars(self, bars: List[RawBar], get_signals=None):
        """加载K线数据并进行分析

        :param bars: K线数据列表
        :param get_signals: 自定义信号计算函数，可选
        :return: 分析器实例自身
        """
        try:
            self.czsc = CZSC(
                bars=bars,
                get_signals=get_signals,
                max_bi_num=self.max_bi_num
            )
            logger.info(f"{self.symbol} - {self.freq.value} 分析器初始化完成，共 {len(bars)} 根K线")
            return self
        except Exception as e:
            logger.error(f"加载K线数据失败: {e}")
            raise

    def update(self, bar: RawBar):
        """更新分析结果

        :param bar: 新的K线数据
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        self.czsc.update(bar)

    def get_bis(self) -> List[BI]:
        """获取已完成的笔列表

        :return: 笔列表
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.finished_bis

    def get_fxs(self) -> List[FX]:
        """获取分型列表

        :return: 分型列表
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.fx_list

    def get_last_bi(self) -> Optional[BI]:
        """获取最后一笔

        :return: 最后一笔，如果没有则返回None
        """
        bis = self.get_bis()
        return bis[-1] if bis else None

    def is_last_bi_extending(self) -> bool:
        """判断最后一笔是否在延伸中

        :return: True表示正在延伸，False表示未延伸
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.last_bi_extend

    def get_ubi(self) -> Optional[Dict]:
        """获取未完成的笔

        :return: 未完成笔的字典，包含方向、高低点等信息
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.ubi

    def get_signals(self) -> Dict:
        """获取计算出的信号

        :return: 信号字典
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.signals or {}

    def to_echarts(self, width: str = "1400px", height: str = '580px', bs=None):
        """生成ECharts图表

        :param width: 图表宽度
        :param height: 图表高度
        :param bs: 交易标记列表
        :return: ECharts图表对象
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.to_echarts(width=width, height=height, bs=bs or [])

    def to_plotly(self):
        """生成Plotly图表

        :return: Plotly图表对象
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.to_plotly()

    def open_in_browser(self, width: str = "1400px", height: str = '580px'):
        """在浏览器中打开分析结果

        :param width: 图表宽度
        :param height: 图表高度
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        self.czsc.open_in_browser(width=width, height=height)

    def get_bars_raw(self) -> List[RawBar]:
        """获取原始K线序列

        :return: 原始K线列表
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.bars_raw

    def get_bars_ubi(self) -> List[NewBar]:
        """获取未完成笔的无包含关系K线序列

        :return: 无包含关系K线列表
        """
        if self.czsc is None:
            raise ValueError("请先调用 load_bars 加载K线数据")
        return self.czsc.bars_ubi

