# -*- coding: utf-8 -*-
"""
缓存管理服务

提供内存缓存功能，使用functools.lru_cache和字典缓存。
"""
from functools import lru_cache
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger


class Cache:
    """缓存管理类"""

    def __init__(self, max_size: int = 128, ttl_seconds: Optional[int] = None):
        """
        初始化缓存

        :param max_size: LRU缓存最大大小
        :param ttl_seconds: 缓存过期时间（秒），None表示不过期
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict = {}
        self._timestamps: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        :param key: 缓存键
        :return: 缓存值，如果不存在或已过期返回None
        """
        if key not in self._cache:
            return None

        # 检查是否过期
        if self.ttl_seconds and key in self._timestamps:
            if datetime.now() - self._timestamps[key] > timedelta(seconds=self.ttl_seconds):
                self.delete(key)
                return None

        return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        设置缓存值

        :param key: 缓存键
        :param value: 缓存值
        """
        self._cache[key] = value
        if self.ttl_seconds:
            self._timestamps[key] = datetime.now()

        # 如果超过最大大小，删除最旧的项
        if len(self._cache) > self.max_size:
            self._evict_oldest()

    def delete(self, key: str) -> None:
        """
        删除缓存项

        :param key: 缓存键
        """
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        self._timestamps.clear()
        logger.info("缓存已清空")

    def _evict_oldest(self) -> None:
        """删除最旧的缓存项"""
        if not self._timestamps:
            # 如果没有时间戳，删除第一个
            if self._cache:
                key = next(iter(self._cache))
                self.delete(key)
            return

        # 找到最旧的项
        oldest_key = min(self._timestamps.items(), key=lambda x: x[1])[0]
        self.delete(oldest_key)

    def size(self) -> int:
        """
        获取缓存大小

        :return: 缓存项数量
        """
        return len(self._cache)


# 全局缓存实例
_global_cache: Optional[Cache] = None


def get_cache(max_size: int = 128, ttl_seconds: Optional[int] = None) -> Cache:
    """
    获取全局缓存实例

    :param max_size: LRU缓存最大大小
    :param ttl_seconds: 缓存过期时间（秒）
    :return: Cache实例
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = Cache(max_size=max_size, ttl_seconds=ttl_seconds)
    return _global_cache


def cached(max_size: int = 128, ttl_seconds: Optional[int] = None):
    """
    装饰器：为函数添加缓存功能

    :param max_size: LRU缓存最大大小
    :param ttl_seconds: 缓存过期时间（秒）
    :return: 装饰器函数
    """
    cache = get_cache(max_size=max_size, ttl_seconds=ttl_seconds)

    def decorator(func: Callable) -> Callable:
        @lru_cache(maxsize=max_size)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_value = cache.get(key)

            if cached_value is not None:
                logger.debug(f"缓存命中：{key}")
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)
            cache.set(key, result)
            logger.debug(f"缓存设置：{key}")

            return result

        return wrapper

    return decorator
