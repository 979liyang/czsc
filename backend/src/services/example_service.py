# -*- coding: utf-8 -*-
"""
策略示例服务

管理策略示例的元信息和代码。
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger


class ExampleService:
    """策略示例服务"""

    def __init__(self, examples_path: Path):
        """
        初始化示例服务

        :param examples_path: 策略示例目录路径
        """
        self.examples_path = Path(examples_path)

    def _parse_strategy_file(self, file_path: Path) -> Dict[str, Any]:
        """
        解析策略文件，提取元信息

        :param file_path: 策略文件路径
        :return: 策略元信息字典
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 提取策略名称
            name_match = re.search(r'"""\s*(.+?)\s*"""', content, re.DOTALL)
            name = name_match.group(1).split('\n')[0].strip() if name_match else file_path.stem

            # 提取策略说明
            doc_match = re.search(r'"""\s*(.+?)\s*"""', content, re.DOTALL)
            description = ''
            if doc_match:
                lines = doc_match.group(1).split('\n')
                description_lines = []
                for line in lines[1:]:  # 跳过第一行（名称）
                    if line.strip() and not line.strip().startswith('适用'):
                        description_lines.append(line.strip())
                description = '\n'.join(description_lines)

            # 提取适用市场
            market_match = re.search(r'适用市场[：:]\s*(.+)', content)
            market = market_match.group(1).strip() if market_match else '未知'

            # 提取适用周期
            freq_match = re.search(r'适用周期[：:]\s*(.+)', content)
            freq = freq_match.group(1).strip() if freq_match else '未知'

            # 检查是否有README文件
            readme_path = file_path.parent / f"{file_path.stem}_README.md"
            has_readme = readme_path.exists()

            return {
                'id': file_path.stem,
                'name': name,
                'description': description,
                'market': market,
                'freq': freq,
                'file_path': str(file_path.relative_to(self.examples_path)),
                'category': file_path.parent.name,
                'has_readme': has_readme,
            }
        except Exception as e:
            logger.error(f"解析策略文件失败：{file_path}，错误：{e}")
            return {
                'id': file_path.stem,
                'name': file_path.stem,
                'description': '',
                'market': '未知',
                'freq': '未知',
                'file_path': str(file_path.relative_to(self.examples_path)),
                'category': file_path.parent.name,
                'has_readme': False,
            }

    def get_all_examples(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有策略示例列表

        :param category: 分类（stock、future、etf），可选
        :return: 策略示例列表
        """
        examples = []
        strategies_dir = self.examples_path / "strategies"

        if not strategies_dir.exists():
            logger.warning(f"策略示例目录不存在：{strategies_dir}")
            return examples

        # 遍历策略目录
        for category_dir in strategies_dir.iterdir():
            if not category_dir.is_dir():
                continue

            if category and category_dir.name != category:
                continue

            # 查找所有策略文件
            for file_path in category_dir.glob("strategy_*.py"):
                if file_path.is_file():
                    example_info = self._parse_strategy_file(file_path)
                    examples.append(example_info)

        # 按ID排序
        examples.sort(key=lambda x: x['id'])
        return examples

    def get_example_detail(self, example_id: str) -> Optional[Dict[str, Any]]:
        """
        获取策略示例详情

        :param example_id: 示例ID
        :return: 策略示例详情，如果不存在返回None
        """
        # 查找策略文件
        for category_dir in (self.examples_path / "strategies").iterdir():
            if not category_dir.is_dir():
                continue

            file_path = category_dir / f"{example_id}.py"
            if file_path.exists():
                example_info = self._parse_strategy_file(file_path)
                
                # 读取代码内容
                try:
                    code = file_path.read_text(encoding='utf-8')
                    example_info['code'] = code
                except Exception as e:
                    logger.error(f"读取策略文件失败：{file_path}，错误：{e}")
                    example_info['code'] = ''

                # 读取README内容
                readme_path = category_dir / f"{example_id}_README.md"
                if readme_path.exists():
                    try:
                        readme = readme_path.read_text(encoding='utf-8')
                        example_info['readme'] = readme
                    except Exception as e:
                        logger.error(f"读取README文件失败：{readme_path}，错误：{e}")
                        example_info['readme'] = ''
                else:
                    example_info['readme'] = ''

                return example_info

        return None

    def get_categories(self) -> List[str]:
        """
        获取所有分类列表

        :return: 分类名称列表
        """
        categories = []
        strategies_dir = self.examples_path / "strategies"

        if not strategies_dir.exists():
            return categories

        for category_dir in strategies_dir.iterdir():
            if category_dir.is_dir():
                categories.append(category_dir.name)

        return sorted(categories)
