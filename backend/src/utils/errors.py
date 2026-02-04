# -*- coding: utf-8 -*-
"""
统一错误码与错误响应工具

用于 API 层快速构造一致的错误输出，避免散落的字符串判断。
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from fastapi import HTTPException
from loguru import logger


class ErrorCode(str, Enum):
    """错误码枚举"""

    INVALID_PARAMS = "INVALID_PARAMS"
    DB_CONNECT_FAILED = "DB_CONNECT_FAILED"
    DB_TABLE_NOT_FOUND = "DB_TABLE_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def http_error(status_code: int, code: ErrorCode, message: str, detail: Optional[Any] = None) -> HTTPException:
    """构造统一格式的 HTTPException"""

    payload: Dict[str, Any] = {"code": code.value, "message": message}
    if detail is not None:
        payload["detail"] = detail
    return HTTPException(status_code=status_code, detail=payload)


def log_and_http_500(e: Exception, message: str = "内部服务器错误") -> HTTPException:
    """记录异常并返回统一 500 错误"""

    logger.error(f"{message}：{e}", exc_info=True)
    return http_error(500, ErrorCode.INTERNAL_ERROR, message)

