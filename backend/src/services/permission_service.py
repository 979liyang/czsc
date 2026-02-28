# -*- coding: utf-8 -*-
"""
积分与权限校验服务

根据用户积分与特殊权限判断可用功能（基础/高级/特色），供 API 与前端使用。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.mysql_models import User, PointsTier, SpecialPermission


# 默认积分档位：2000 基础 / 5000 高级 / 10000 高级+特色
DEFAULT_TIERS = [
    {"min_points": 2000, "tier_name": "基础功能", "feature_flags": ["basic"]},
    {"min_points": 5000, "tier_name": "高级功能", "feature_flags": ["basic", "advanced"]},
    {"min_points": 10000, "tier_name": "高级+特色", "feature_flags": ["basic", "advanced", "premium"]},
]


class PermissionService:
    """积分与权限校验服务"""

    def __init__(self, session: Session):
        self.session = session

    def get_user_tier(self, user: User) -> Dict[str, Any]:
        """
        根据用户积分返回当前档位信息。

        :param user: 用户 ORM
        :return: {"tier_name": str, "min_points": int, "feature_flags": list}
        """
        tiers = (
            self.session.query(PointsTier)
            .filter(PointsTier.min_points <= getattr(user, "points", 0))
            .order_by(PointsTier.min_points.desc())
            .all()
        )
        if not tiers:
            return {"tier_name": "无", "min_points": 0, "feature_flags": []}
        t = tiers[0]
        flags = []
        if t.feature_flags:
            try:
                flags = json.loads(t.feature_flags) if isinstance(t.feature_flags, str) else t.feature_flags
            except Exception:
                flags = []
        return {"tier_name": t.tier_name, "min_points": t.min_points, "feature_flags": flags}

    def get_user_special_permission_ids(self, user: User) -> List[int]:
        """获取用户特殊权限 ID 列表（从 User.special_permission_ids JSON 或关联表解析）"""
        if getattr(user, "special_permission_ids", None):
            try:
                raw = getattr(user, "special_permission_ids")
                ids = json.loads(raw)
                return [int(x) for x in ids] if isinstance(ids, list) else []
            except Exception:
                pass
        return []

    def has_feature(self, user: User, feature: str) -> bool:
        """
        判断用户是否拥有某功能（按积分档位或特殊权限）。

        :param user: 用户
        :param feature: 功能标识，如 basic / advanced / premium
        :return: 是否拥有
        """
        tier = self.get_user_tier(user)
        if feature in (tier.get("feature_flags") or []):
            return True
        if getattr(user, "role", None) == "admin":
            return True
        return False

    def can_access_advanced(self, user: User) -> bool:
        """是否可访问高级功能"""
        return self.has_feature(user, "advanced")

    def can_access_premium(self, user: User) -> bool:
        """是否可访问特色服务"""
        return self.has_feature(user, "premium")
