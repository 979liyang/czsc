# -*- coding: utf-8 -*-
"""
项目配置管理

使用环境变量统一管理 MySQL 连接、数据表名、时区、交易时段等配置。

注意：
- 这里仅做“配置读取与约定集中”，不做具体数据库连接（连接在 storage 层实现）
- 所有字段提供合理默认值，便于本地快速启动
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class TradingSession:
    """交易时段"""

    start: str
    end: str


class Settings(BaseSettings):
    """应用配置"""

    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    _BACKEND_ROOT = _PROJECT_ROOT / "backend"

    model_config = SettingsConfigDict(
        env_prefix="CZSC_",
        extra="ignore",
        env_file=(
            str(_PROJECT_ROOT / ".env"),
            str(_BACKEND_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
    )

    # ---------- 基础 ----------
    timezone: str = "Asia/Shanghai"

    # ---------- MySQL 连接 ----------
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "czsc"
    mysql_charset: str = "utf8mb4"

    # ---------- 数据表名（可按需自定义） ----------
    table_stock_basic: str = "stock_basic"
    table_minute_bar: str = "stock_minute_bars"
    table_minute_coverage: str = "stock_minute_coverage"
    table_minute_daily_stats: str = "stock_minute_daily_stats"
    table_minute_gaps: str = "stock_minute_gaps"

    # ---------- 交易时段（A股默认） ----------
    # 说明：用于“期望分钟数”估算与缺口检查。格式为 HH:MM
    trading_sessions: List[Tuple[str, str]] = [
        ("09:30", "11:30"),
        ("13:00", "15:00"),
    ]

    def mysql_url(self) -> str:
        """生成 SQLAlchemy MySQL URL（PyMySQL 驱动）"""

        # 注意：密码可能包含特殊字符，需要做 URL 编码
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{self.mysql_user}:{password}@{self.mysql_host}:{self.mysql_port}"
            f"/{self.mysql_database}?charset={self.mysql_charset}"
        )

    def get_trading_sessions(self) -> List[TradingSession]:
        """获取交易时段列表"""

        return [TradingSession(start=s, end=e) for s, e in self.trading_sessions]


_SETTINGS: Settings | None = None


def get_settings() -> Settings:
    """获取全局配置单例"""

    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings()
    return _SETTINGS

