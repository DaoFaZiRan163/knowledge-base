"""知识摄取模块的纯函数单元测试。

聚焦不依赖网络/向量库的文本处理逻辑：文本清洗、分块 ID 生成、
代码注释与函数签名提取、文件名元数据解析、以及模型→向量维度映射。

knowledge_ingestion 在模块顶部 import 了若干重依赖（qdrant / openai /
langchain / pymupdf）。若环境未安装则整体 importorskip 跳过；被测方法本身
不使用这些依赖，因此用 __new__ 绕过 __init__，避免构造真实的向量库客户端。
"""

import pytest

# 缺少重依赖时跳过整个文件，而不是报错
ki = pytest.importorskip("automation.knowledge_ingestion")


@pytest.fixture
def ingester():
    """绕过 __init__（不创建 Qdrant/embedding 客户端）的实例，仅用于测试纯方法。"""
    obj = ki.FDEKnowledgeIngester.__new__(ki.FDEKnowledgeIngester)
    return obj


# ─────────────────── 文本清洗 ───────────────────

def test_clean_text_collapses_whitespace(ingester):
    assert ingester._clean_text("a   b\n\nc\t d") == "a b c d"


def test_clean_text_keeps_chinese_and_ascii(ingester):
    # 中文字符与英文均保留；全角标点（）！不在白名单内会被移除
    out = ingester._clean_text("机器学习（ML）很重要！")
    assert "机器学习" in out
    assert "ML" in out


def test_clean_text_keeps_ascii_punctuation(ingester):
    out = ingester._clean_text("Hello, world! (test)")
    assert "," in out and "!" in out and "(" in out


def test_clean_text_strips_control_symbols(ingester):
    assert "@" not in ingester._clean_text("hello@@@world")


# ─────────────────── 分块 ID ───────────────────

def test_chunk_id_is_deterministic(ingester):
    a = ingester._generate_chunk_id("path/to/file.md", 0)
    b = ingester._generate_chunk_id("path/to/file.md", 0)
    assert a == b


def test_chunk_id_varies_by_index(ingester):
    a = ingester._generate_chunk_id("path/to/file.md", 0)
    b = ingester._generate_chunk_id("path/to/file.md", 1)
    assert a != b


def test_chunk_id_format(ingester):
    cid = ingester._generate_chunk_id("x.md", 3)
    prefix, idx = cid.rsplit("_", 1)
    assert len(prefix) == 8        # md5 前 8 位
    assert idx == "3"


# ─────────────────── 代码解析 ───────────────────

def test_extract_code_comments(ingester):
    code = "x = 1  # 设置初始值\n# 顶行注释\nprint(x)"
    comments = ingester._extract_code_comments(code)
    assert "# 设置初始值" in comments
    assert "# 顶行注释" in comments


def test_extract_functions_with_docstring(ingester):
    code = 'def add(a, b):\n    """两数相加"""\n    return a + b\n'
    funcs = ingester._extract_functions(code)
    assert len(funcs) == 1
    assert funcs[0]["name"] == "add"
    assert funcs[0]["docstring"] == "两数相加"
    assert funcs[0]["signature"] == "def add(a, b):"


def test_extract_functions_without_docstring_ignored(ingester):
    code = "def no_doc(x):\n    return x\n"
    assert ingester._extract_functions(code) == []


# ─────────────────── 文件名元数据解析 ───────────────────

def test_book_metadata_full_filename(ingester, tmp_path):
    f = tmp_path / "深度学习_Goodfellow_2016_ai-engineering_expert.pdf"
    f.touch()
    meta = ingester._extract_book_metadata(f)
    assert meta["title"] == "深度学习"
    assert meta["author"] == "Goodfellow"
    assert meta["year"] == "2016"
    assert meta["difficulty"] == "expert"


def test_book_metadata_falls_back_on_short_name(ingester, tmp_path):
    f = tmp_path / "随手笔记.pdf"
    f.touch()
    meta = ingester._extract_book_metadata(f)
    assert meta["title"] == "随手笔记"
    assert meta["author"] == "Unknown"
    assert meta["difficulty"] == "intermediate"   # 默认值


# ─────────────────── 模型 → 向量维度映射 ───────────────────

def test_known_dims_contains_expected_models():
    assert ki._KNOWN_DIMS["BAAI/bge-m3"] == 1024
    assert ki._KNOWN_DIMS["embo-01"] == 1536
    assert ki._KNOWN_DIMS["text-embedding-3-large"] == 3072
