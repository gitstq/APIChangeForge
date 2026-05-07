#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APIChangeForge - 轻量级API变更智能检测与影响分析引擎
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ""

setup(
    name="apichangeforge",
    version="1.0.0",
    description="轻量级API变更智能检测与影响分析引擎 CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="APIChangeForge Team",
    author_email="",
    url="https://github.com/yourusername/APIChangeForge",
    py_modules=["apichangeforge"],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "apichangeforge=apichangeforge:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="api openapi swagger diff changes breaking impact analysis cli",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/APIChangeForge/issues",
        "Source": "https://github.com/yourusername/APIChangeForge",
    },
)
