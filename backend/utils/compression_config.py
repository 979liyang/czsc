# -*- coding: utf-8 -*-
"""
压缩配置工具

根据不同数据类型返回优化的Parquet写入配置
"""
from typing import Dict, Any


def get_parquet_write_options(data_type: str) -> Dict[str, Any]:
    """
    根据不同数据类型返回优化配置
    
    :param data_type: 数据类型（'minute', 'daily', 'indicators'）
    :return: Parquet写入选项字典
    """
    configs = {
        'minute': {
            'compression': 'zstd',
            'compression_level': 3,
            'row_group_size': 100000,  # 较大的行组
            'use_dictionary': True,
            'dictionary_pagesize_limit': 2 * 1024 * 1024,  # 2MB
            'data_page_size': 1 * 1024 * 1024,  # 1MB
            'write_statistics': True,  # 启用统计信息（谓词下推）
            'store_schema': True,
            'version': '2.6'  # Parquet版本
        },
        'daily': {
            'compression': 'snappy',  # 日线数据小，用快速压缩
            'row_group_size': 50000,
            'use_dictionary': True,
            'write_statistics': True,
            'store_schema': True,
        },
        'indicators': {
            'compression': 'zstd',
            'compression_level': 5,  # 更高压缩比
            'row_group_size': 50000,
            'use_dictionary': True,
            'write_statistics': True,
            'store_schema': True,
        }
    }
    
    return configs.get(data_type, configs['minute'])


def get_parquet_engine_options() -> Dict[str, Any]:
    """
    获取Parquet引擎选项
    
    :return: 引擎选项字典
    """
    return {
        'engine': 'pyarrow',
    }
