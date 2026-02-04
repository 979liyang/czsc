# -*- coding: utf-8 -*-
"""
FastAPI应用入口

配置CORS、中间件、日志系统等。
"""
import os
import sys
from pathlib import Path

# 确保可以导入 src 模块
# 如果从项目根目录运行，需要添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# 确保可以导入 czsc 模块（项目根目录的 czsc 目录）
project_root = backend_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=os.getenv("LOG_LEVEL", "INFO")
)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=os.getenv("LOG_LEVEL", "INFO")
)

# 创建logs目录
Path("logs").mkdir(exist_ok=True)

# 创建FastAPI应用
app = FastAPI(
    title="CZSC API",
    description="CZSC缠论分析API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常：{exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "detail": str(exc) if os.getenv("DEBUG", "False").lower() == "true" else None
        }
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录API请求日志"""
    logger.info(f"{request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "CZSC API服务",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


# 导入API路由
from .api.v1 import analysis, bars, signals, backtest, symbols, docs, examples, data_management, data_quality
app.include_router(analysis.router, prefix="/api/v1", tags=["缠论分析"])
app.include_router(bars.router, prefix="/api/v1", tags=["K线数据"])
app.include_router(signals.router, prefix="/api/v1", tags=["信号计算"])
app.include_router(backtest.router, prefix="/api/v1", tags=["策略回测"])
app.include_router(symbols.router, prefix="/api/v1", tags=["股票列表"])
app.include_router(docs.router, prefix="/api/v1", tags=["信号函数文档"])
app.include_router(examples.router, prefix="/api/v1", tags=["策略示例"])
app.include_router(data_management.router, prefix="/api/v1", tags=["数据管理"])
app.include_router(data_quality.router, prefix="/api/v1", tags=["数据质量"])


if __name__ == "__main__":
    import uvicorn
    # 直接运行 app 对象，而不是使用字符串路径
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
