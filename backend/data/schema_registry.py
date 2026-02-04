# -*- coding: utf-8 -*-
"""
Schema注册服务

管理数据Schema定义和验证
"""
from pathlib import Path
from typing import Dict, Any, Optional
import json
from loguru import logger


class SchemaRegistry:
    """Schema注册表"""
    
    def __init__(self, registry_path: Path = None):
        """
        初始化Schema注册表
        
        :param registry_path: Schema注册表路径，默认为stock_data/metadata/schema_registry/
        """
        if registry_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.registry_path = project_root / ".stock_data" / "metadata" / "schema_registry"
        else:
            self.registry_path = Path(registry_path)
        
        # 确保目录存在
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已注册的Schema
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """加载已注册的Schema"""
        schemas = {}
        
        if self.registry_path.exists():
            for schema_file in self.registry_path.glob("*.json"):
                schema_name = schema_file.stem
                try:
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        schemas[schema_name] = json.load(f)
                    logger.debug(f"加载Schema: {schema_name}")
                except Exception as e:
                    logger.error(f"加载Schema失败: {schema_name}, 错误: {e}")
        
        return schemas
    
    def register_schema(self, schema_name: str, schema: Dict[str, Any]) -> bool:
        """
        注册Schema
        
        :param schema_name: Schema名称（如：minute_schema, daily_schema）
        :param schema: Schema定义字典
        :return: 是否成功
        """
        try:
            schema_file = self.registry_path / f"{schema_name}.json"
            
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            
            # 更新内存中的Schema
            self.schemas[schema_name] = schema
            
            logger.info(f"注册Schema成功: {schema_name}")
            return True
        except Exception as e:
            logger.error(f"注册Schema失败: {schema_name}, 错误: {e}")
            return False
    
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        获取Schema
        
        :param schema_name: Schema名称
        :return: Schema定义或None
        """
        return self.schemas.get(schema_name)
    
    def validate_schema(self, schema_name: str, data: Dict[str, Any]) -> bool:
        """
        验证数据是否符合Schema
        
        :param schema_name: Schema名称
        :param data: 数据字典
        :return: 是否符合Schema
        """
        schema = self.get_schema(schema_name)
        if schema is None:
            logger.warning(f"Schema不存在: {schema_name}")
            return False
        
        # 简单的字段检查（可以根据需要扩展）
        required_fields = schema.get('required_fields', [])
        for field in required_fields:
            if field not in data:
                logger.warning(f"缺少必需字段: {field}")
                return False
        
        return True
