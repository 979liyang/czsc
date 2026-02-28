# -*- coding: utf-8 -*-
"""
从 czsc/signals 源码中提取各信号函数的 docstring，生成 czsc_api2/czsc.signals/*.md 详细说明页。
与 readthedocs 单页一致：参数模板、信号逻辑、信号列表、Parameters、Returns。
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parents[1]
SIGNALS_DIR = ROOT / "czsc" / "signals"
OUT_DIR = ROOT / "czsc_api2" / "czsc.signals"


def _parse_init_exports() -> list[tuple[str, list[str]]]:
    """解析 czsc/signals/__init__.py，得到 [(module, [name, ...]), ...]。"""
    init_path = SIGNALS_DIR / "__init__.py"
    text = init_path.read_text(encoding="utf-8")
    result = []
    for m in re.finditer(r"from czsc\.signals\.(\w+) import\s*\((.*?)\)", text, re.DOTALL):
        module = m.group(1)
        names = [
            n.strip()
            for n in m.group(2).split(",")
            if n.strip() and not n.strip().startswith("#")
        ]
        result.append((module, names))
    return result


def _get_docstring_from_file(module: str, func_name: str) -> str | None:
    """从 czsc/signals/{module}.py 中获取函数 func_name 的 docstring。"""
    path = SIGNALS_DIR / f"{module}.py"
    if not path.exists():
        return None
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.get_docstring(node)
    return None


def _docstring_to_md(func_name: str, doc: str | None, module: str) -> str:
    """将 docstring 转为与 readthedocs 一致的 Markdown。"""
    lines = []
    lines.append(f"# {func_name}\n")
    lines.append("`czsc.signals." + func_name + "(c: CZSC, **kwargs) -> OrderedDict`\n")
    if doc:
        doc = doc.strip()
        # 在首个 :param 前加 ## Parameters，:return 前加 ## Returns
        doc = re.sub(r"(\n\s*)(:param\s+)", r"\n\n## Parameters\n\n\1- ", doc, count=1)
        doc = re.sub(r"\n\s*- :param\s+(\w+):\s*", r"\n- **\1**: ", doc)
        doc = re.sub(r"\n\s*:param\s+(\w+):\s*", r"\n- **\1**: ", doc)
        doc = re.sub(r"\n\s*:return\s+", r"\n\n## Returns\n\n", doc)
        doc = re.sub(r"^:return:\s*", "", doc)  # 行首残留 :return: 去掉
        lines.append(doc)
    else:
        lines.append("（暂无详细 docstring，请参考源码。）")
    lines.append("\n\n---")
    lines.append(f"\n*源码: `czsc/signals/{module}.py`*")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exports = _parse_init_exports()
    written = []
    for module, names in exports:
        for func_name in names:
            doc = _get_docstring_from_file(module, func_name)
            md = _docstring_to_md(func_name, doc, module)
            out_path = OUT_DIR / f"{func_name}.md"
            out_path.write_text(md, encoding="utf-8")
            written.append(func_name)
    # 更新 czsc.signals/README 中的“按字母列表”（简单列举）
    readme_path = OUT_DIR / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if "<!-- 由脚本生成索引时填充" in readme:
        block = "\n".join([f"- [{n}]({n}.md)" for n in sorted(written)])
        readme = readme.replace(
            "<!-- 由脚本生成索引时填充，或见各子 README -->",
            block,
        )
        readme_path.write_text(readme, encoding="utf-8")
    print(f"Generated {len(written)} signal docs in {OUT_DIR}")


if __name__ == "__main__":
    main()
