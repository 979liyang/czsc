# -*- coding: utf-8 -*-
"""
股票主数据仓储

负责对 MySQL 的 stock_basic 表进行读写（增删改查、批量 upsert）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from ..models.mysql_models import StockBasic


class StockBasicRepo:
    """股票主数据仓储"""

    def __init__(self, session: Session):
        """
        初始化仓储

        :param session: SQLAlchemy Session
        """

        self.session = session

    def get(self, symbol: str) -> Optional[StockBasic]:
        """获取单条"""

        return self.session.get(StockBasic, symbol)

    def _row_to_float(self, v: Any) -> Optional[float]:
        """将 CSV/字典中的值转为 float，空字符串或无效为 None"""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def upsert_one(self, symbol: str, **kwargs: Any) -> None:
        """单条 upsert，kwargs 中与模型同名的键会写入数据库"""

        obj = self.get(symbol)
        if obj is None:
            obj = StockBasic(symbol=symbol)
            self.session.add(obj)

        # 数值型列（从 CSV 读入为字符串需转 float）
        float_keys = {
            "close", "turnover_rate", "turnover_rate_f", "volume_ratio",
            "pe", "pe_ttm", "pb", "ps", "ps_ttm", "dv_ratio", "dv_ttm",
            "total_share", "float_share", "free_share", "total_mv", "circ_mv",
        }
        col_names = {c.key for c in StockBasic.__table__.columns if c.key not in ("created_at", "updated_at")}
        for key, value in kwargs.items():
            if key not in col_names or key == "symbol":
                continue
            if value is None or (isinstance(value, str) and value.strip() == ""):
                setattr(obj, key, None)
                continue
            if key in float_keys:
                setattr(obj, key, self._row_to_float(value))
            else:
                setattr(obj, key, value if not isinstance(value, str) else value.strip())
        obj.updated_at = datetime.now()

    def bulk_upsert(self, rows: Iterable[Dict[str, Any]]) -> int:
        """
        批量 upsert，支持全量字段（symbol 必填，其余按 CSV/接口列写入）。

        :param rows: 每行至少包含 symbol，可含 name/market/list_date/delist_date 及扩展列
        :return: 处理行数
        """

        n = 0
        for r in rows:
            symbol = (r.get("symbol") or "").strip()
            if not symbol:
                continue
            self.upsert_one(symbol=symbol, **{k: v for k, v in r.items() if k != "symbol"})
            n += 1

        logger.info(f"stock_basic 批量 upsert 完成：rows={n}")
        return n

    def list_symbols(self, market: Optional[str] = None) -> List[str]:
        """列出股票代码"""

        q = self.session.query(StockBasic.symbol)
        if market:
            q = q.filter(StockBasic.market == market)
        return [x[0] for x in q.all()]

