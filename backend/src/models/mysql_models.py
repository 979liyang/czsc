# -*- coding: utf-8 -*-
"""
MySQL 表结构（SQLAlchemy ORM）

覆盖数据：
- 股票主数据：stock_basic
- 分钟覆盖概况：stock_minute_coverage
- 分钟日统计：stock_minute_daily_stats
- 分钟缺口明细：stock_minute_gaps
- 用户与自选股：user, watchlist
- CZSC 信号库、因子与配置：signals, signals_config, factors
- 筛选任务与结果：screen_task_run, screen_result
- 数据拉取运行记录：data_fetch_run
"""

from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import Column, Date, DateTime, Float, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

from ..utils.settings import get_settings

Base = declarative_base()


def _now() -> datetime:
    return datetime.now()


class StockBasic(Base):
    """股票主数据（含 stock_basic 全字段 + daily_basic 最近一日指标）"""

    __tablename__ = get_settings().table_stock_basic

    symbol = Column(String(32), primary_key=True, comment="股票代码，如 000001.SZ / 600000.SH")
    name = Column(String(64), nullable=True, comment="中文名称")
    market = Column(String(8), nullable=True, comment="市场：SH / SZ")
    list_date = Column(String(16), nullable=True, comment="上市日期 YYYYMMDD")
    delist_date = Column(String(16), nullable=True, comment="退市日期 YYYYMMDD")
    # stock_basic 扩展
    area = Column(String(64), nullable=True, comment="地域")
    industry = Column(String(64), nullable=True, comment="所属行业")
    fullname = Column(String(256), nullable=True, comment="股票全称")
    enname = Column(String(256), nullable=True, comment="英文全称")
    cnspell = Column(String(32), nullable=True, comment="拼音缩写")
    exchange = Column(String(16), nullable=True, comment="交易所 SSE/SZSE")
    curr_type = Column(String(8), nullable=True, comment="交易货币")
    list_status = Column(String(4), nullable=True, comment="上市状态 L/D/P")
    is_hs = Column(String(4), nullable=True, comment="沪深港通 N/H/S")
    act_name = Column(String(128), nullable=True, comment="实控人名称")
    act_ent_type = Column(String(64), nullable=True, comment="实控人企业性质")
    # daily_basic 最近交易日指标
    trade_date = Column(String(16), nullable=True, comment="每日指标日期 YYYYMMDD")
    close = Column(Float, nullable=True, comment="收盘价")
    turnover_rate = Column(Float, nullable=True, comment="换手率%")
    turnover_rate_f = Column(Float, nullable=True, comment="换手率(自由流通股)%")
    volume_ratio = Column(Float, nullable=True, comment="量比")
    pe = Column(Float, nullable=True, comment="市盈率")
    pe_ttm = Column(Float, nullable=True, comment="市盈率TTM")
    pb = Column(Float, nullable=True, comment="市净率")
    ps = Column(Float, nullable=True, comment="市销率")
    ps_ttm = Column(Float, nullable=True, comment="市销率TTM")
    dv_ratio = Column(Float, nullable=True, comment="股息率%")
    dv_ttm = Column(Float, nullable=True, comment="股息率TTM%")
    total_share = Column(Float, nullable=True, comment="总股本万股")
    float_share = Column(Float, nullable=True, comment="流通股本万股")
    free_share = Column(Float, nullable=True, comment="自由流通股本万")
    total_mv = Column(Float, nullable=True, comment="总市值万元")
    circ_mv = Column(Float, nullable=True, comment="流通市值万元")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class IndexInfo(Base):
    """A股核心指数信息表（带交易所后缀）"""

    __tablename__ = get_settings().table_index_info

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    index_code = Column(String(20), nullable=False, unique=True, comment="指数代码（带后缀，如 000300.SH）")
    index_code_raw = Column(String(20), nullable=False, comment="原始指数代码（无后缀）")
    index_name = Column(String(100), nullable=False, comment="指数名称")
    exchange_suffix = Column(String(10), nullable=True, comment="交易所后缀（SH/SZ/HK/CSI等）")
    level_category = Column(String(50), nullable=True, comment="观察层级（第一层：市场之锚/第二层：风格之矛/第三层：行业主题）")
    sector_category = Column(String(50), nullable=True, comment="大类板块（如：核心宽基/规模风格/科技TMT/医药健康等）")
    style_position = Column(String(200), nullable=True, comment="风格与定位描述")
    base_date = Column(Date, nullable=True, comment="基日")
    start_dt = Column(DateTime, nullable=True, comment="开始时间（日线数据起始）")
    end_dt = Column(DateTime, nullable=True, comment="结束时间（日线数据截止）")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否有效 1:有效 0:无效")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class StockMinuteCoverage(Base):
    """分钟数据覆盖概况（每只股票一行）"""

    __tablename__ = get_settings().table_minute_coverage

    symbol = Column(String(32), primary_key=True, comment="股票代码")
    start_dt = Column(DateTime, nullable=True, comment="最早分钟时间")
    end_dt = Column(DateTime, nullable=True, comment="最晚分钟时间")
    coverage_ratio = Column(Float, nullable=True, comment="覆盖率（可选，依赖日统计）")
    last_scan_at = Column(DateTime, default=_now, nullable=False, comment="最近扫描时间")
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class StockMinuteDailyStats(Base):
    """分钟日统计（每股票每交易日）"""

    __tablename__ = get_settings().table_minute_daily_stats

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日")
    actual_count = Column(Integer, nullable=False, comment="实际分钟条数")
    expected_count = Column(Integer, nullable=True, comment="期望分钟条数（可选）")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    __table_args__ = (UniqueConstraint("symbol", "trade_date", name="uq_symbol_trade_date"),)


class StockMinuteGap(Base):
    """分钟缺口明细（按日、按缺口区间）"""

    __tablename__ = get_settings().table_minute_gaps

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(32), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日")
    gap_start = Column(DateTime, nullable=False, comment="缺口开始时间（含）")
    gap_end = Column(DateTime, nullable=False, comment="缺口结束时间（不含）")
    gap_minutes = Column(Integer, nullable=False, comment="缺口分钟数")
    details = Column(Text, nullable=True, comment="缺口描述/定位信息（JSON 或文本）")
    created_at = Column(DateTime, default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("symbol", "trade_date", "gap_start", "gap_end", name="uq_gap_range"),)


class User(Base):
    """用户表（登录认证 + 昵称、签名、手机、邮箱、积分、特殊权限、身份）"""

    __tablename__ = get_settings().table_user

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    username = Column(String(64), nullable=False, unique=True, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    nickname = Column(String(64), nullable=True, comment="昵称")
    signature = Column(String(255), nullable=True, comment="签名")
    phone = Column(String(32), nullable=True, index=True, comment="手机号")
    email = Column(String(128), nullable=True, index=True, comment="邮箱")
    points = Column(Integer, default=0, nullable=False, comment="积分")
    role = Column(String(16), default="user", nullable=False, comment="身份：admin / user")
    special_permission_ids = Column(Text, nullable=True, comment="特殊权限ID列表，JSON数组如 [1,2]")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class Watchlist(Base):
    """自选股表（按用户隔离）"""

    __tablename__ = get_settings().table_watchlist

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    symbol = Column(String(32), nullable=False, comment="股票代码，如 000001.SZ")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序序号")
    created_at = Column(DateTime, default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_user_symbol"),)


class SignalFunc(Base):
    """信号库（与 czsc.signals 对应，供定时筛选与 API 查询）"""

    __tablename__ = get_settings().table_signals

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = Column(String(128), nullable=False, unique=True, index=True, comment="信号函数名，如 cxt_bi_status_V230101")
    module_path = Column(String(256), nullable=True, comment="模块路径，如 czsc.signals")
    category = Column(String(32), nullable=True, comment="分类：cxt/tas/bar/vol 等")
    param_template = Column(String(256), nullable=True, comment="参数模板（信号名称模板）")
    description = Column(Text, nullable=True, comment="说明")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 1:是 0:否")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class SignalsConfig(Base):
    """可复用的命名信号配置表（存储多套信号入参 JSON，供 API/回测/筛选按名称加载）"""

    __tablename__ = get_settings().table_signals_config

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = Column(String(128), nullable=False, unique=True, index=True, comment="配置名称，如 策略A日线组合")
    description = Column(String(512), nullable=True, comment="说明")
    config_json = Column(Text, nullable=False, comment="信号配置 JSON 数组，与 CzscSignals(signals_config=...) 入参一致")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class FactorDef(Base):
    """因子库表（一因子对应多条信号配置 signals_config，供筛选任务使用）"""

    __tablename__ = get_settings().table_factors

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = Column(String(128), nullable=False, unique=True, index=True, comment="因子名称")
    expression_or_signal_ref = Column(String(512), nullable=True, comment="[已废弃] 表达式或关联信号函数名，兼容旧数据")
    signals_config = Column(Text, nullable=True, comment="多条信号配置 JSON 数组，每项含 name/freq/di 及信号参数字段，与 factor_usage_demo 的 FACTOR_CONFIGS 一致")
    description = Column(Text, nullable=True, comment="说明")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 1:是 0:否")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class Strategy(Base):
    """策略库表（存 czsc Position 的 opens/exits 等可序列化配置，与 Position.load/dump 兼容）"""

    __tablename__ = get_settings().table_strategies

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = Column(String(128), nullable=False, unique=True, index=True, comment="策略名称")
    description = Column(Text, nullable=True, comment="说明")
    strategy_type = Column(String(64), nullable=True, index=True, comment="策略类型，如 single_ma_long / third_buy_long")
    config_json = Column(Text, nullable=False, comment="Position 配置 JSON，与 czsc Position.load/dump 兼容")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 1:是 0:否")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class ScreenTaskRun(Base):
    """筛选任务运行记录表"""

    __tablename__ = get_settings().table_screen_task_run

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    task_type = Column(String(32), nullable=False, index=True, comment="任务类型：signal/factor")
    run_at = Column(DateTime, default=_now, nullable=False, comment="运行时间")
    status = Column(String(16), nullable=False, default="running", comment="状态：running/success/failed")
    params_json = Column(Text, nullable=True, comment="任务参数 JSON")
    created_at = Column(DateTime, default=_now, nullable=False)


class ScreenResult(Base):
    """筛选结果表（每只股票每条信号/因子的结果）"""

    __tablename__ = get_settings().table_screen_result

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    task_run_id = Column(Integer, nullable=False, index=True, comment="关联 screen_task_run.id")
    symbol = Column(String(32), nullable=False, index=True, comment="股票代码")
    signal_name = Column(String(128), nullable=True, index=True, comment="信号函数名（信号筛选时）")
    factor_id = Column(Integer, nullable=True, index=True, comment="因子ID（因子筛选时）")
    trade_date = Column(String(16), nullable=False, index=True, comment="交易日 YYYYMMDD")
    value_result = Column(Text, nullable=True, comment="信号值或因子值（可 JSON）")
    created_at = Column(DateTime, default=_now, nullable=False)


class DataFetchRun(Base):
    """数据拉取运行记录表（日线/分钟拉取，手动或定时）"""

    __tablename__ = get_settings().table_data_fetch_run

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    task_type = Column(String(32), nullable=False, index=True, comment="任务类型：daily / minute")
    run_at = Column(DateTime, default=_now, nullable=False, comment="运行时间")
    trigger = Column(String(16), nullable=False, comment="触发方式：manual / scheduled")
    status = Column(String(16), nullable=False, default="running", comment="状态：running / success / failed")
    summary = Column(Text, nullable=True, comment="摘要，如「成功 5000 只」")
    params_json = Column(Text, nullable=True, comment="任务参数 JSON")
    created_at = Column(DateTime, default=_now, nullable=False)


class PointsTier(Base):
    """用户积分权限档位表（2000 基础 / 5000 高级 / 10000 高级+特色）"""

    __tablename__ = get_settings().table_points_tier

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    min_points = Column(Integer, nullable=False, unique=True, comment="最低积分，如 2000/5000/10000")
    tier_name = Column(String(32), nullable=False, comment="档位名称：基础功能/高级功能/高级+特色")
    feature_flags = Column(Text, nullable=True, comment="功能标识 JSON 数组，如 [\"basic\",\"advanced\"]")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class SpecialPermission(Base):
    """特殊权限表（独立开通的权限，名称、描述）"""

    __tablename__ = get_settings().table_special_permission

    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")
    name = Column(String(64), nullable=False, unique=True, index=True, comment="权限名称")
    description = Column(String(255), nullable=True, comment="描述")
    is_active = Column(SmallInteger, default=1, nullable=False, comment="是否启用 1:是 0:否")
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class UserSpecialPermission(Base):
    """用户与特殊权限关联表（多对多）"""

    __tablename__ = get_settings().table_user_special_permission

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    permission_id = Column(Integer, nullable=False, index=True, comment="特殊权限ID")
    created_at = Column(DateTime, default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),)


class MySingles(Base):
    """用户收藏 my_singles（信号或标的）"""

    __tablename__ = get_settings().table_my_singles

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True, comment="用户ID")
    item_type = Column(String(16), nullable=False, comment="类型：signal / symbol")
    item_id = Column(String(128), nullable=False, comment="信号名称或标的代码")
    sort_order = Column(Integer, default=0, nullable=False, comment="排序")
    created_at = Column(DateTime, default=_now, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "item_type", "item_id", name="uq_user_single"),)