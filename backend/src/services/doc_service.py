# -*- coding: utf-8 -*-
"""
信号函数文档服务

自动分析czsc.signals模块，提取信号函数信息。
"""
import inspect
import re
from typing import List, Dict, Any, Optional
from loguru import logger
from czsc.utils import import_by_name
from czsc.objects import Signal


class DocService:
    """信号函数文档服务"""

    def __init__(self, signals_module: str = 'czsc.signals'):
        """
        初始化文档服务

        :param signals_module: 信号函数模块名称
        """
        self.signals_module = signals_module
        self._signals_cache: Optional[List[Dict[str, Any]]] = None

    def _get_category(self, signal_name: str) -> str:
        """
        根据信号函数名称获取分类

        :param signal_name: 信号函数名称
        :return: 分类名称
        """
        # 提取前缀（第一个下划线前的部分）
        if '_' in signal_name:
            prefix = signal_name.split('_')[0]
            category_map = {
                'cxt': '缠论类',
                'tas': '技术指标类',
                'bar': 'K线形态类',
                'vol': '成交量类',
                'stock': '股票特定类',
                'pos': '持仓状态类',
                'ang': '角度类',
                'jcc': '基础类',
                'coo': '其他类',
                'byi': '笔相关',
                'xls': '选股类',
            }
            return category_map.get(prefix, '其他类')
        return '其他类'

    def _extract_params(self, doc: str) -> List[Dict[str, Any]]:
        """
        从docstring中提取参数说明

        :param doc: 函数docstring
        :return: 参数列表
        """
        params = []
        if not doc:
            return params

        # 提取参数模板
        param_template_match = re.search(r'参数模板[：:]\s*"([^"]+)"', doc)
        if param_template_match:
            params.append({
                'name': '参数模板',
                'type': 'str',
                'description': '信号名称模板',
                'default': param_template_match.group(1),
                'required': True,
            })

        # 提取kwargs参数说明
        lines = doc.split('\n')
        in_params_section = False
        for line in lines:
            if ':param' in line or ':param ' in line:
                in_params_section = True
                # 解析参数行
                # 格式：:param name: description
                match = re.match(r':param\s+(\w+)[：:]?\s*(.*)', line)
                if match:
                    param_name = match.group(1)
                    param_desc = match.group(2).strip()
                    if param_name != 'cat':  # 跳过cat参数
                        params.append({
                            'name': param_name,
                            'type': 'any',
                            'description': param_desc,
                            'default': None,
                            'required': False,
                        })

        return params

    def _extract_signals(self, doc: str) -> List[str]:
        """
        从docstring中提取信号列表

        :param doc: 函数docstring
        :return: 信号名称列表
        """
        if not doc:
            return []

        # 提取Signal列表
        signals = re.findall(r"Signal\('([^']+)'\)", doc)
        return signals

    def _get_data_requirements(self, signal_func_name: str) -> Dict[str, Any]:
        """
        给信号函数打一个“经验性”的数据需求标签

        说明：
        - CZSC 信号的真实数据需求与具体实现有关，这里给一个“够用”的经验值用于指导数据维护
        - 后续如需更精确，可按信号函数内部用到的指标窗口长度进一步细化
        """

        prefix = signal_func_name.split("_")[0] if "_" in signal_func_name else signal_func_name
        # 经验规则：大多数信号至少需要 200~500 根基础K线，缠论类一般更长
        if prefix in {"cxt", "byi"}:
            return {"freq": "1分钟", "needed_bars": 3000}
        if prefix in {"tas", "bar", "vol"}:
            return {"freq": "1分钟", "needed_bars": 1000}
        if prefix in {"pos", "stock", "xls"}:
            return {"freq": "日线", "needed_bars": 500}
        return {"freq": "1分钟", "needed_bars": 800}

    def get_all_signals(self) -> List[Dict[str, Any]]:
        """
        获取所有信号函数信息

        :return: 信号函数信息列表
        """
        if self._signals_cache is not None:
            return self._signals_cache

        signals = []
        try:
            signals_module = import_by_name(self.signals_module)
            for name in dir(signals_module):
                # 跳过私有函数和特殊函数
                if name.startswith('_') or not '_' in name:
                    continue

                try:
                    func = getattr(signals_module, name)
                    if not inspect.isfunction(func):
                        continue

                    doc = inspect.getdoc(func)
                    sig = inspect.signature(func)

                    # 提取参数信息
                    params = self._extract_params(doc)
                    # 提取函数签名中的参数
                    for param_name, param in sig.parameters.items():
                        if param_name == 'cat':
                            continue
                        # 检查是否已在params中
                        if not any(p['name'] == param_name for p in params):
                            params.append({
                                'name': param_name,
                                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'any',
                                'description': '',
                                'default': param.default if param.default != inspect.Parameter.empty else None,
                                'required': param.default == inspect.Parameter.empty,
                            })

                    # 提取信号列表
                    signal_list = self._extract_signals(doc)

                    # 提取函数说明
                    description = ''
                    if doc:
                        lines = doc.split('\n')
                        description_lines = []
                        for line in lines:
                            if line.strip() and not line.strip().startswith(':') and '参数模板' not in line:
                                if 'Signal(' not in line:
                                    description_lines.append(line.strip())
                                else:
                                    break
                        description = '\n'.join(description_lines).strip()

                    signal_info = {
                        'name': name,
                        'full_name': f'{self.signals_module}.{name}',
                        'category': self._get_category(name),
                        'description': description,
                        'params': params,
                        'signals': signal_list,
                        'signature': str(sig),
                        'data_requirements': self._get_data_requirements(name),
                    }
                    signals.append(signal_info)

                except Exception as e:
                    logger.warning(f"提取信号函数 {name} 信息失败：{e}")
                    continue

            # 按分类和名称排序
            signals.sort(key=lambda x: (x['category'], x['name']))
            self._signals_cache = signals
            logger.info(f"提取信号函数信息完成，共{len(signals)}个")

        except Exception as e:
            logger.error(f"获取信号函数列表失败：{e}", exc_info=True)

        return signals

    def get_signal_detail(self, signal_name: str) -> Optional[Dict[str, Any]]:
        """
        获取单个信号函数的详细信息

        :param signal_name: 信号函数名称（可以是完整名称或短名称）
        :return: 信号函数详细信息，如果不存在返回None
        """
        # 如果是完整名称，提取短名称
        if '.' in signal_name:
            signal_name = signal_name.split('.')[-1]

        all_signals = self.get_all_signals()
        for signal in all_signals:
            if signal['name'] == signal_name or signal['full_name'] == signal_name:
                return signal

        return None

    def get_signals_by_category(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        按分类获取信号函数列表

        :param category: 分类名称（可选）
        :return: 信号函数列表
        """
        all_signals = self.get_all_signals()
        if category:
            return [s for s in all_signals if s['category'] == category]
        return all_signals

    def get_categories(self) -> List[str]:
        """
        获取所有分类列表

        :return: 分类名称列表
        """
        all_signals = self.get_all_signals()
        categories = list(set(s['category'] for s in all_signals))
        categories.sort()
        return categories
