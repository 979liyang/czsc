# -*- coding: utf-8 -*-
"""
数据拉取运行记录仓储

负责 data_fetch_run 表的创建、状态更新、按日查询今日是否已成功执行。
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..models.mysql_models import DataFetchRun


class DataFetchRunRepo:
    """数据拉取运行记录仓储"""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        task_type: str,
        trigger: str,
        status: str = "running",
        params_json: Optional[str] = None,
    ) -> DataFetchRun:
        """创建一条运行记录，返回实例（已 flush 可拿 id）"""
        row = DataFetchRun(
            task_type=task_type,
            trigger=trigger,
            status=status,
            params_json=params_json,
        )
        self.session.add(row)
        self.session.flush()
        return row

    def update_status(
        self,
        run_id: int,
        status: str,
        summary: Optional[str] = None,
    ) -> None:
        """更新运行状态及可选摘要"""
        row = self.session.get(DataFetchRun, run_id)
        if row:
            row.status = status
            if summary is not None:
                row.summary = summary

    def get_today_success(self, task_type: str) -> Optional[DataFetchRun]:
        """查询当日是否已有同类型的成功记录。
        使用服务器本地日期（date.today()）与 run_at 的日期比较，MySQL 侧用 func.date(run_at)。
        若 run_at 存为 UTC，需在应用层或库配置中统一时区后再比较。
        """
        today = date.today()
        q = (
            self.session.query(DataFetchRun)
            .filter(
                and_(
                    DataFetchRun.task_type == task_type,
                    DataFetchRun.status == "success",
                    func.date(DataFetchRun.run_at) == today,
                )
            )
            .order_by(DataFetchRun.run_at.desc())
            .limit(1)
        )
        return q.first()

    def get_by_id(self, run_id: int) -> Optional[DataFetchRun]:
        """按 id 查询单条"""
        return self.session.get(DataFetchRun, run_id)

    def list_runs(
        self,
        task_type: Optional[str] = None,
        limit: int = 20,
        run_date: Optional[date] = None,
    ):
        """分页查询运行记录，支持按 task_type、日期筛选"""
        q = self.session.query(DataFetchRun).order_by(DataFetchRun.run_at.desc())
        if task_type:
            q = q.filter(DataFetchRun.task_type == task_type)
        if run_date is not None:
            q = q.filter(func.date(DataFetchRun.run_at) == run_date)
        return q.limit(limit).all()
