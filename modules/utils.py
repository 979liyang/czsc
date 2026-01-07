# -*- coding: utf-8 -*-
"""
工具函数模块

提供各种工具函数的封装
"""
from typing import List, Dict, Optional
from loguru import logger
from czsc.utils import (
    freqs_sorted,
    x_round,
    read_json,
    save_json,
    dill_dump,
    dill_load,
    home_path,
    clear_cache,
    clear_expired_cache,
    get_dir_size,
    empty_cache_path,
)
from czsc.utils.calendar import (
    is_trading_date,
    next_trading_date,
    prev_trading_date,
    get_trading_dates,
)
from czsc.utils.trade import adjust_holding_weights
from czsc import envs


class CZSCUtils:
    """CZSC工具函数封装类"""

    @staticmethod
    def sort_freqs(freqs: List[str]) -> List[str]:
        """对K线周期列表进行排序

        :param freqs: K线周期列表
        :return: 排序后的K线周期列表
        """
        return freqs_sorted(freqs)

    @staticmethod
    def round_number(x: float, digits: int = 4) -> float:
        """四舍五入数字

        :param x: 待四舍五入的数字
        :param digits: 保留小数位数
        :return: 四舍五入后的数字
        """
        return x_round(x, digits)

    @staticmethod
    def load_json(file_path: str) -> Dict:
        """加载JSON文件

        :param file_path: 文件路径
        :return: JSON数据字典
        """
        try:
            data = read_json(file_path)
            logger.info(f"JSON文件加载成功: {file_path}")
            return data
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            raise

    @staticmethod
    def save_json(data: Dict, file_path: str):
        """保存数据到JSON文件

        :param data: 要保存的数据
        :param file_path: 文件路径
        """
        try:
            save_json(data, file_path)
            logger.info(f"JSON文件保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            raise

    @staticmethod
    def save_dill(obj, file_path: str):
        """使用dill保存对象

        :param obj: 要保存的对象
        :param file_path: 文件路径
        """
        try:
            dill_dump(obj, file_path)
            logger.info(f"对象保存成功: {file_path}")
        except Exception as e:
            logger.error(f"保存对象失败: {e}")
            raise

    @staticmethod
    def load_dill(file_path: str):
        """使用dill加载对象

        :param file_path: 文件路径
        :return: 加载的对象
        """
        try:
            obj = dill_load(file_path)
            logger.info(f"对象加载成功: {file_path}")
            return obj
        except Exception as e:
            logger.error(f"加载对象失败: {e}")
            raise

    @staticmethod
    def get_cache_home_path() -> str:
        """获取缓存主目录路径

        :return: 缓存主目录路径
        """
        return str(home_path)

    @staticmethod
    def clear_all_cache():
        """清空所有缓存"""
        try:
            clear_cache()
            logger.info("所有缓存已清空")
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            raise

    @staticmethod
    def clear_expired_cache():
        """清空过期缓存"""
        try:
            clear_expired_cache()
            logger.info("过期缓存已清空")
        except Exception as e:
            logger.error(f"清空过期缓存失败: {e}")
            raise

    @staticmethod
    def get_cache_size(path: str = None) -> int:
        """获取缓存目录大小

        :param path: 目录路径，如果不提供则使用默认缓存路径
        :return: 目录大小（字节）
        """
        try:
            if path is None:
                path = home_path
            size = get_dir_size(path)
            logger.info(f"缓存目录大小: {size / (1024**3):.2f} GB")
            return size
        except Exception as e:
            logger.error(f"获取缓存大小失败: {e}")
            raise

    @staticmethod
    def empty_cache_path(path: str = None):
        """清空指定缓存路径

        :param path: 缓存路径，如果不提供则使用默认缓存路径
        """
        try:
            if path is None:
                path = home_path
            empty_cache_path(path)
            logger.info(f"缓存路径已清空: {path}")
        except Exception as e:
            logger.error(f"清空缓存路径失败: {e}")
            raise

    @staticmethod
    def is_trading_day(date: str) -> bool:
        """判断是否为交易日

        :param date: 日期字符串，格式：YYYYMMDD
        :return: True表示是交易日，False表示不是
        """
        from datetime import datetime
        dt = datetime.strptime(date, "%Y%m%d")
        return is_trading_date(dt)

    @staticmethod
    def get_next_trading_day(date: str) -> str:
        """获取下一个交易日

        :param date: 日期字符串，格式：YYYYMMDD
        :return: 下一个交易日，格式：YYYYMMDD
        """
        from datetime import datetime
        dt = datetime.strptime(date, "%Y%m%d")
        next_dt = next_trading_date(dt)
        return next_dt.strftime("%Y%m%d")

    @staticmethod
    def get_prev_trading_day(date: str) -> str:
        """获取上一个交易日

        :param date: 日期字符串，格式：YYYYMMDD
        :return: 上一个交易日，格式：YYYYMMDD
        """
        from datetime import datetime
        dt = datetime.strptime(date, "%Y%m%d")
        prev_dt = prev_trading_date(dt)
        return prev_dt.strftime("%Y%m%d")

    @staticmethod
    def get_trading_days_list(start_date: str, end_date: str) -> List[str]:
        """获取交易日列表

        :param start_date: 开始日期，格式：YYYYMMDD
        :param end_date: 结束日期，格式：YYYYMMDD
        :return: 交易日列表，格式：YYYYMMDD
        """
        from datetime import datetime
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")
        trading_days = get_trading_dates(start_dt, end_dt)
        return [dt.strftime("%Y%m%d") for dt in trading_days]

    @staticmethod
    def adjust_weights(weights: Dict[str, float], max_weight: float = 1.0) -> Dict[str, float]:
        """调整持仓权重

        :param weights: 权重字典，key为标的代码，value为权重
        :param max_weight: 最大权重限制
        :return: 调整后的权重字典
        """
        try:
            adjusted = adjust_holding_weights(weights, max_weight=max_weight)
            logger.info("权重调整完成")
            return adjusted
        except Exception as e:
            logger.error(f"权重调整失败: {e}")
            raise

    @staticmethod
    def get_min_bi_len() -> int:
        """获取最小笔长度

        :return: 最小笔长度
        """
        return envs.get_min_bi_len()

    @staticmethod
    def get_max_bi_num() -> int:
        """获取最大笔数量

        :return: 最大笔数量
        """
        return envs.get_max_bi_num()

    @staticmethod
    def get_verbose() -> bool:
        """获取是否输出详细信息

        :return: True表示输出详细信息，False表示不输出
        """
        return envs.get_verbose()

