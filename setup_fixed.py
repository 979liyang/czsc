# coding: utf-8
"""
修复版本的setup.py，避免在构建时导入czsc模块导致依赖问题
"""
from os import path
from setuptools import setup, find_packages
import re

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "requirements.txt"), encoding="utf-8") as f:
    install_requires = f.read().strip().split("\n")

# 直接从__init__.py读取版本信息，避免导入整个模块
init_file = path.join(here, "czsc", "__init__.py")
with open(init_file, encoding="utf-8") as f:
    content = f.read()
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    author_match = re.search(r'__author__\s*=\s*["\']([^"\']+)["\']', content)
    email_match = re.search(r'__email__\s*=\s*["\']([^"\']+)["\']', content)
    
    version = version_match.group(1) if version_match else "0.9.69"
    author = author_match.group(1) if author_match else "zengbin93"
    email = email_match.group(1) if email_match else "zeng_bin8888@163.com"

setup(
    name="czsc",
    version=version,
    author=author,
    author_email=email,
    keywords=["缠论", "技术分析", "A股", "期货", "缠中说禅", "量化", "QUANT", "程序化交易"],
    description="缠中说禅技术分析工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache Software License",
    url="https://github.com/waditu/czsc",
    packages=find_packages(include=["czsc", "czsc.*"]),
    include_package_data=True,
    install_requires=install_requires,
    package_data={"": ["utils/china_calendar.feather", "utils/minutes_split.feather"]},
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ]
)
