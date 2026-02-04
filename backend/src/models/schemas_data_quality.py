# -*- coding: utf-8 -*-
"""
数据质量相关 Pydantic 模型

用于描述：
- 覆盖概况（start/end/ratio）
- 按日统计（actual/expected）
- 缺口区间（gap ranges）
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CoverageItem(BaseModel):
    """单只股票分钟覆盖概况"""

    symbol: str = Field(..., description="股票代码")
    start_dt: Optional[datetime] = Field(None, description="最早分钟时间")
    end_dt: Optional[datetime] = Field(None, description="最晚分钟时间")
    coverage_ratio: Optional[float] = Field(None, description="覆盖率（可选）")
    last_scan_at: Optional[datetime] = Field(None, description="最近扫描时间")


class DailyStatItem(BaseModel):
    """单只股票某交易日分钟统计"""

    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日")
    actual_count: int = Field(..., description="实际分钟条数")
    expected_count: Optional[int] = Field(None, description="期望分钟条数（可选）")


class GapRange(BaseModel):
    """缺口区间（半开区间 [start, end)）"""

    start: datetime = Field(..., description="缺口开始时间（含）")
    end: datetime = Field(..., description="缺口结束时间（不含）")
    minutes: int = Field(..., description="缺口分钟数")
    details: Optional[Dict[str, Any]] = Field(None, description="缺口细节（可选）")


class GapQueryResult(BaseModel):
    """缺口查询结果"""

    symbol: str = Field(..., description="股票代码")
    trade_date: date = Field(..., description="交易日")
    expected_count: Optional[int] = Field(None, description="期望分钟条数")
    actual_count: Optional[int] = Field(None, description="实际分钟条数")
    gaps: List[GapRange] = Field(default_factory=list, description="缺口区间列表")


class CoverageListResponse(BaseModel):
    """覆盖概况列表响应"""

    items: List[CoverageItem] = Field(default_factory=list, description="覆盖概况列表")
    count: int = Field(..., description="数量")


class DailyStatsResponse(BaseModel):
    """日统计响应"""

    items: List[DailyStatItem] = Field(default_factory=list)
    count: int = Field(..., description="数量")

