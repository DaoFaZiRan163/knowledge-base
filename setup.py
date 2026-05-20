"""
FDE Knowledge Hub - Setup Script
Forward Deployed Engineer 专业知识管理系统
"""

from setuptools import setup, find_packages
import os

# 读取 README 文件
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name="fde-knowledge-hub",
    version="1.0.0",
    description="Forward Deployed Engineer 专业知识的工程化管理系统",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    author="邵炎炎",
    author_email="shaoyanyan91@163.com",
    url="https://github.com/yourusername/FDE-Knowledge-Hub",

    packages=find_packages(),
    include_package_data=True,

    install_requires=[
        'langchain>=0.1.0',
        'openai>=1.10.0',
        'anthropic>=0.18.0',
        'pandas>=2.0.0',
        'unstructured[all]>=0.11.0',
        'qdrant-client>=1.7.0',
        'networkx>=3.0',
        'rich>=13.0.0',
        'click>=8.1.0',
    ],

    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.5.0',
        ],
        'gpu': [
            'faiss-gpu>=1.7.0',
            'torch>=2.0.0',
            'transformers>=4.30.0',
        ],
    },

    entry_points={
        'console_scripts': [
            'fde-cli=automation.cli:main',
            'fde-ingest=automation.knowledge_ingestion:main',
            'fde-interview=automation.interview_prep:main',
        ],
    },

    python_requires='>=3.9',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)