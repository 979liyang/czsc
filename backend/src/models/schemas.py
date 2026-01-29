# -*- coding: utf-8 -*-
"""
Pydantic数据模型

定义API请求和响应的数据模型。
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class BarRequest(BaseModel):
    """K线数据请求模型"""
    symbol: str = Field(..., description="标的代码")
    freq: str = Field(..., description="K线周期")
    sdt: str = Field(..., description="开始时间（YYYYMMDD或YYYY-MM-DD）")
    edt: str = Field(..., description="结束时间（YYYYMMDD或YYYY-MM-DD）")


class BarResponse(BaseModel):
    """K线数据响应模型"""
    symbol: str
    freq: str
    bars: List[Dict[str, Any]] = Field(..., description="RawBar序列化后的字典列表")


class AnalysisRequest(BaseModel):
    """缠论分析请求模型"""
    symbol: str = Field(..., description="标的代码")
    freq: str = Field(..., description="K线周期")
    sdt: str = Field(..., description="开始时间（YYYYMMDD或YYYY-MM-DD）")
    edt: str = Field(..., description="结束时间（YYYYMMDD或YYYY-MM-DD）")


class AnalysisResponse(BaseModel):
    """缠论分析响应模型"""
    symbol: str
    freq: str
    bis: List[Dict[str, Any]] = Field(..., description="BI序列化后的字典列表")
    fxs: List[Dict[str, Any]] = Field(..., description="FX序列化后的字典列表")
    zss: List[Dict[str, Any]] = Field(..., description="ZS序列化后的字典列表")


class SignalRequest(BaseModel):
    """信号计算请求模型"""
    symbol: str = Field(..., description="标的代码")
    freq: str = Field(..., description="K线周期")
    signal_name: str = Field(..., description="信号函数名称")
    params: Dict[str, Any] = Field(default_factory=dict, description="信号函数参数")


class SignalResponse(BaseModel):
    """信号计算响应模型"""
    signals: Dict[str, str] = Field(..., description="信号字典")


class BatchSignalRequest(BaseModel):
    """批量信号计算请求模型"""
    symbol: str = Field(..., description="标的代码")
    freq: str = Field(..., description="K线周期")
    signal_configs: List[Dict[str, Any]] = Field(..., description="信号配置列表")
    sdt: str = Field(..., description="开始时间（YYYYMMDD或YYYY-MM-DD）")
    edt: str = Field(..., description="结束时间（YYYYMMDD或YYYY-MM-DD）")


class BacktestRequest(BaseModel):
    """策略回测请求模型"""
    strategy_config: Dict[str, Any] = Field(..., description="策略配置")
    symbol: str = Field(..., description="标的代码")
    sdt: str = Field(..., description="开始时间（YYYYMMDD或YYYY-MM-DD）")
    edt: str = Field(..., description="结束时间（YYYYMMDD或YYYY-MM-DD）")


class BacktestResponse(BaseModel):
    """策略回测响应模型"""
    pairs: Dict[str, Any] = Field(..., description="回测结果对")
    operates: List[Dict[str, Any]] = Field(..., description="操作记录列表")
    positions: List[Dict[str, Any]] = Field(..., description="持仓记录列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")
