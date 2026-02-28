# -*- coding: utf-8 -*-
"""
指数信息仓储

负责对 MySQL 的 index_info 表进行读写：列出有效指数代码、更新日线数据起止日期等。
"""

from __future__ import annotations

from datetime import date, datetime, time as dt_time
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import IndexInfo


def _to_datetime(d: Optional[date]) -> Optional[datetime]:
    """将 date 转为 datetime（当日 00:00:00），便于写入 start_dt/end_dt。"""
    if d is None:
        return None
    return datetime.combine(d, dt_time.min)


class IndexInfoRepo:
    """指数信息仓储"""

    def __init__(self, session: Session):
        """
        初始化仓储

        :param session: SQLAlchemy Session
        """
        self.session = session

    def list_active_index_codes(self) -> List[str]:
        """列出所有有效指数的 index_code（带后缀，如 000300.SH）。"""
        rows = (
            self.session.query(IndexInfo.index_code)
            .filter(IndexInfo.is_active == 1)
            .order_by(IndexInfo.index_code)
            .all()
        )
        return [r[0] for r in rows]

    def update_data_range(self, index_code: str, start_date: Optional[date], end_date: Optional[date]) -> bool:
        """
        更新某指数的日线数据起止时间（start_dt / end_dt）。

        :param index_code: 指数代码（带后缀）
        :param start_date: 日线数据起始日
        :param end_date: 日线数据截止日
        :return: 是否更新到记录
        """
        row = self.session.query(IndexInfo).filter(IndexInfo.index_code == index_code).first()
        if not row:
            logger.warning(f"index_info 中未找到指数: {index_code}")
            return False
        row.start_dt = _to_datetime(start_date)
        row.end_dt = _to_datetime(end_date)
        logger.debug(f"更新指数日线区间: {index_code} -> {start_date} ~ {end_date}")
        return True
