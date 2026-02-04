# -*- coding: utf-8 -*-
"""
后端服务启动脚本

从项目根目录或 backend 目录都可以运行此脚本启动服务。
"""
import sys
from pathlib import Path

# 确保 backend 目录在 Python 路径中
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 确保可以导入 czsc 模块（项目根目录的 czsc 目录）
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入并运行应用
import uvicorn

if __name__ == "__main__":
    # 使用字符串路径以支持 reload 功能
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
