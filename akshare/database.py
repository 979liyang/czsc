# -*- coding: utf-8 -*-
"""
MySQL 数据库模型定义

用于存储股票列表和K线数据
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from loguru import logger

Base = declarative_base()


class StockInfo(Base):
    """股票基本信息表"""
    __tablename__ = 'stock_info'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, comment='股票代码，格式：000001.SZ')
    code = Column(String(10), nullable=False, comment='股票代码，不含市场后缀')
    name = Column(String(50), comment='股票名称')
    market = Column(String(10), comment='市场：SH-上海，SZ-深圳，CYB-创业板')
    list_date = Column(DateTime, comment='上市日期')
    industry = Column(String(50), comment='所属行业')
    area = Column(String(50), comment='所属地区')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        Index('idx_symbol', 'symbol'),
        Index('idx_code', 'code'),
        Index('idx_market', 'market'),
    )


class StockKline(Base):
    """股票K线数据表"""
    __tablename__ = 'stock_kline'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment='股票代码，格式：000001.SZ')
    dt = Column(DateTime, nullable=False, comment='K线时间')
    freq = Column(String(20), nullable=False, comment='K线周期：1min, 5min, 15min, 30min, 60min, D, W, M')
    open = Column(Float, nullable=False, comment='开盘价')
    close = Column(Float, nullable=False, comment='收盘价')
    high = Column(Float, nullable=False, comment='最高价')
    low = Column(Float, nullable=False, comment='最低价')
    vol = Column(Float, default=0, comment='成交量（股）')
    amount = Column(Float, default=0, comment='成交额（元）')
    adjust = Column(String(10), default='qfq', comment='复权类型：qfq-前复权，hfq-后复权，none-不复权')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    __table_args__ = (
        Index('idx_symbol_dt_freq', 'symbol', 'dt', 'freq'),
        Index('idx_symbol_freq', 'symbol', 'freq'),
        Index('idx_dt', 'dt'),
    )


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, database_uri: str = None):
        """
        初始化数据库管理器
        
        :param database_uri: 数据库连接字符串，格式：mysql+mysqlconnector://user:password@host:port/database
        """
        if database_uri is None:
            database_uri = "mysql+mysqlconnector://root:root123456@localhost:3306/kylin"
        
        self.database_uri = database_uri
        self.engine = create_engine(
            database_uri,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        self.Session = sessionmaker(bind=self.engine)
        logger.info(f"数据库连接初始化完成: {database_uri}")
    
    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话"""
        return self.Session()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()
        logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager = None


def get_db_manager(database_uri: str = None) -> DatabaseManager:
    """获取数据库管理器实例（单例模式）"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_uri)
    return _db_manager


def init_database(database_uri: str = None):
    """初始化数据库（创建表）"""
    db_manager = get_db_manager(database_uri)
    db_manager.create_tables()
    logger.info("数据库初始化完成")


if __name__ == "__main__":
    # 测试数据库连接和表创建
    init_database()
    print("数据库初始化完成！")

