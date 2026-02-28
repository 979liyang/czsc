# -*- coding: utf-8 -*-
"""
创建认证相关表（user、watchlist）。无 Alembic 时运行此脚本一次即可。
从项目根目录执行: cd backend && python -c "from scripts.create_auth_tables import main; main()"
或从 backend 目录: python scripts/create_auth_tables.py
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.mysql_models import User, Watchlist
from src.storage.mysql_db import get_engine

def main():
    engine = get_engine()
    # 只创建 user 和 watchlist 表
    User.__table__.create(engine, checkfirst=True)
    Watchlist.__table__.create(engine, checkfirst=True)
    print("user、watchlist 表已就绪（已存在则跳过）。")

if __name__ == "__main__":
    main()
