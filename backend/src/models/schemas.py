# -*- coding: utf-8 -*-
"""
Pydantic数据模型

定义API请求和响应的数据模型。
"""
from datetime import datetime
from typing import List, Dict, Optional, Any, Literal
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
    # 统计信息
    bars_raw_count: int = Field(..., description="原始K线数量")
    bars_ubi_count: int = Field(..., description="未完成笔的K线数量")
    fx_count: int = Field(..., description="分型数量")
    finished_bi_count: int = Field(..., description="已完成笔数量")
    bi_count: int = Field(..., description="所有笔数量（包括未完成）")
    ubi_count: int = Field(..., description="未完成笔数量")
    last_bi_extend: bool = Field(..., description="最后一笔是否在延伸")
    last_bi_direction: Optional[str] = Field(None, description="最后一笔方向")
    last_bi_power: Optional[float] = Field(None, description="最后一笔幅度")
    # 数据可用范围与缺口摘要（可选，用于提示“本地数据不足/缺失”）
    data_start_dt: Optional[str] = Field(None, description="本次分析实际使用数据的开始时间（ISO格式）")
    data_end_dt: Optional[str] = Field(None, description="本次分析实际使用数据的结束时间（ISO格式）")
    requested_sdt: Optional[str] = Field(None, description="本次请求的开始时间（与入参 sdt 一致）")
    requested_edt: Optional[str] = Field(None, description="本次请求的结束时间（与入参 edt 一致）")
    effective_sdt: Optional[str] = Field(None, description="本次分析实际使用的开始日期（YYYY-MM-DD），与 data_start_dt 日期部分一致")
    effective_edt: Optional[str] = Field(None, description="本次分析实际使用的结束日期（YYYY-MM-DD），与 data_end_dt 日期部分一致")
    data_range_note: Optional[str] = Field(None, description="当实际数据未覆盖请求区间时的说明")
    gaps_summary: Optional[str] = Field(None, description="缺口摘要（可选，后续由数据质量模块填充）")


class LocalCzscItem(BaseModel):
    """本地多周期 CZSC 分析单项（单一周期）"""

    freq: str = Field(..., description="周期，如 1分钟/5分钟/15分钟/30分钟/60分钟（可选日线）")
    bars: List[Dict[str, Any]] = Field(default_factory=list, description="RawBar 序列化列表")
    bis: List[Dict[str, Any]] = Field(default_factory=list, description="BI 序列化列表")
    fxs: List[Dict[str, Any]] = Field(default_factory=list, description="FX 序列化列表")
    indicators: Dict[str, Any] = Field(
        default_factory=dict,
        description="指标序列（用于 TradingVue 复刻 to_echarts）：vol / macd(diff,dea,macd) / sma(MA5/MA13/MA21)",
    )
    stats: Dict[str, Any] = Field(default_factory=dict, description="统计信息")


class LocalCzscMeta(BaseModel):
    """本地数据加载与多周期合成元数据（用于排障与解释数据范围）"""

    data_root: Optional[str] = Field(None, description="本地数据根目录（.stock_data）")
    parquet_count: int = Field(0, description="命中的 parquet 文件数量（按月聚合）")
    rows_before_filter: int = Field(0, description="过滤前总行数（合并后）")
    rows_after_filter: int = Field(0, description="按 period 与时间范围过滤后行数")
    period_filtered: bool = Field(False, description="是否按 period==1 过滤为 1分钟数据")
    dt_min: Optional[str] = Field(None, description="过滤后最小时间")
    dt_max: Optional[str] = Field(None, description="过滤后最大时间")
    base_freq: str = Field(..., description="BarGenerator 合成与分析的基础周期")
    requested_freqs: List[str] = Field(default_factory=list, description="请求的周期列表（字符串）")
    target_freqs: List[str] = Field(default_factory=list, description="实际输出的周期列表（字符串）")
    generated_bar_counts: Dict[str, int] = Field(default_factory=dict, description="各周期合成后 bars 数量")
    warnings: List[str] = Field(default_factory=list, description="校验/合成过程中的警告信息")


class PaginationInfo(BaseModel):
    """分页信息（单个数据类型的）"""

    total: int = Field(..., description="总数据量")
    offset: int = Field(..., description="当前偏移量（已跳过的数据量）")
    limit: int = Field(..., description="每页数量（0 表示返回全部）")
    returned: int = Field(..., description="本次返回的数据量")
    has_more: bool = Field(..., description="是否还有更多数据")


class FrequencyPagination(BaseModel):
    """单个周期的分页信息"""

    bars: Optional[PaginationInfo] = Field(None, description="K线数据分页信息")
    fxs: Optional[PaginationInfo] = Field(None, description="分型数据分页信息")
    bis: Optional[PaginationInfo] = Field(None, description="笔数据分页信息")


class LocalCzscResponse(BaseModel):
    """本地分钟数据驱动的多周期 CZSC 分析响应"""

    symbol: str = Field(..., description="标的代码")
    sdt: str = Field(..., description="开始时间（YYYYMMDD）")
    edt: str = Field(..., description="结束时间（YYYYMMDD）")
    base_freq: str = Field(..., description="合成与分析的基础周期（如 1分钟）")
    items: Dict[str, LocalCzscItem] = Field(
        default_factory=dict,
        description="key 为周期名称（与 LocalCzscItem.freq 一致），如 1分钟/5分钟/15分钟/30分钟/60分钟（可选日线）",
    )
    meta: Optional[LocalCzscMeta] = Field(None, description="数据加载/过滤/合成元数据")
    pagination: Optional[Dict[str, FrequencyPagination]] = Field(
        None, description="分页信息，key 为周期名称，value 为该周期的分页信息"
    )


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
    positions_summary: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="按持仓汇总：pos_name、operate_count、last_operates、evaluate（run-by-strategy 返回）",
    )


class BacktestByStrategyRequest(BaseModel):
    """按策略库执行回测请求：策略 id/name、标的、日期、参数覆盖"""
    strategy_id: Optional[int] = Field(None, description="策略库 id")
    strategy_name: Optional[str] = Field(None, description="策略库 name（与 strategy_id 二选一）")
    symbol: str = Field(..., description="标的代码")
    sdt: str = Field(..., description="开始时间 YYYYMMDD 或 YYYY-MM-DD")
    edt: str = Field(..., description="结束时间 YYYYMMDD 或 YYYY-MM-DD")
    params: Optional[Dict[str, Any]] = Field(None, description="策略参数覆盖，与 params_schema 默认值合并")


class SymbolItem(BaseModel):
    """股票信息条目"""

    symbol: str = Field(..., description="股票代码，如 000001.SZ / 600000.SH")
    name: Optional[str] = Field(None, description="中文名称")
    market: Optional[str] = Field(None, description="市场：SH / SZ")
    list_date: Optional[str] = Field(None, description="上市日期 YYYYMMDD")
    delist_date: Optional[str] = Field(None, description="退市日期 YYYYMMDD")


class SymbolListResponse(BaseModel):
    """股票列表响应"""

    items: List[SymbolItem] = Field(default_factory=list, description="股票信息列表")
    count: int = Field(..., description="数量")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")


# ---------- 认证 ----------
class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=6, max_length=72)


class UserResponse(BaseModel):
    """用户信息（响应）"""
    id: int
    username: str
    nickname: Optional[str] = None
    signature: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    points: int = 0
    role: str = "user"
    tier_name: Optional[str] = None
    feature_flags: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """用户资料更新（可选字段）"""
    nickname: Optional[str] = Field(None, max_length=64)
    signature: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    email: Optional[str] = Field(None, max_length=128)


class MySinglesItem(BaseModel):
    """my_singles 收藏项"""
    id: int
    item_type: str
    item_id: str
    sort_order: int = 0

    class Config:
        from_attributes = True


class MySinglesAdd(BaseModel):
    """添加 my_singles 请求"""
    item_type: str = Field(..., description="signal / symbol")
    item_id: str = Field(..., min_length=1, max_length=128)
    sort_order: int = 0


class MySinglesResponse(BaseModel):
    """my_singles 列表响应"""
    items: List[MySinglesItem] = Field(default_factory=list)


class LoginResponse(BaseModel):
    """登录成功响应"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------- 自选股 ----------
class WatchlistAdd(BaseModel):
    """添加自选股请求"""
    symbol: str = Field(..., min_length=1, max_length=32)


class WatchlistItem(BaseModel):
    """自选股单项（含富化字段：名称、最新价、涨跌、涨跌%）"""
    symbol: str
    sort_order: int = 0
    name: Optional[str] = None
    latest_price: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None

    class Config:
        from_attributes = True


class WatchlistResponse(BaseModel):
    """自选股列表响应"""
    items: List[WatchlistItem] = Field(default_factory=list)


# ---------- 数据拉取运行记录 ----------
class DataFetchTriggerRequest(BaseModel):
    """触发数据拉取请求"""
    task_type: Literal["daily", "minute", "index"] = Field(
        ..., description="任务类型：daily 日线 / minute 分钟 / index 指数"
    )


class DataFetchRunResponse(BaseModel):
    """数据拉取运行记录响应"""
    id: int
    task_type: str
    run_at: datetime
    trigger: str
    status: str
    summary: Optional[str] = None
    params_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
