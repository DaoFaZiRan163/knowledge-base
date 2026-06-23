"""知识统计模块单元测试。

覆盖：阶段名→分类映射、线性回归进步趋势判定、YAML front matter 解析、
以及对临时知识库目录的概览统计（笔记数 / 链接数 / 分类聚合）。

KnowledgeStats 只读文件系统、不触网，测试通过 tmp_path 构造一个迷你知识库。
"""

import pytest

from automation.knowledge_stats import KnowledgeStats


@pytest.fixture
def stats(tmp_path):
    return KnowledgeStats(project_root=tmp_path)


# ─────────────────── 阶段名 → 分类映射 ───────────────────

@pytest.mark.parametrize("phase,expected", [
    ("Phase 1 Foundation", "技术基础"),
    ("第一阶段 基础", "技术基础"),
    ("AI Engineering", "AI工程化"),
    ("Product Thinking", "产品业务"),
    ("Consulting Delivery", "咨询交付"),
    ("Something Else", "其他"),
])
def test_extract_category_from_phase(stats, phase, expected):
    assert stats._extract_category_from_phase(phase) == expected


# ─────────────────── 进步趋势（线性回归斜率）───────────────────

def test_trend_insufficient_data(stats):
    assert stats._calculate_progress_trend([1.0, 2.0]) == "insufficient_data"


def test_trend_improving_rapidly(stats):
    assert stats._calculate_progress_trend([1.0, 2.0, 3.0, 4.0]) == "improving_rapidly"


def test_trend_stable(stats):
    assert stats._calculate_progress_trend([3.0, 3.0, 3.0, 3.0]) == "stable"


def test_trend_declining_rapidly(stats):
    assert stats._calculate_progress_trend([5.0, 4.0, 3.0, 2.0]) == "declining_rapidly"


# ─────────────────── YAML front matter 解析 ───────────────────

def test_parse_frontmatter_reads_yaml(stats, tmp_path):
    note = tmp_path / "note.md"
    note.write_text(
        "---\ntitle: Transformer\ndifficulty: expert\n---\n\n正文内容",
        encoding="utf-8",
    )
    meta = stats._parse_frontmatter(note)
    assert meta["title"] == "Transformer"
    assert meta["difficulty"] == "expert"


def test_parse_frontmatter_no_yaml_returns_empty(stats, tmp_path):
    note = tmp_path / "plain.md"
    note.write_text("# 没有 front matter 的笔记", encoding="utf-8")
    assert stats._parse_frontmatter(note) == {}


def test_read_note_content_missing_file_returns_empty(stats, tmp_path):
    assert stats._read_note_content(tmp_path / "nope.md") == ""


# ─────────────────── 概览统计（端到端，临时知识库）───────────────────

def test_overview_counts_notes_and_links(tmp_path):
    core = tmp_path / "core"
    core.mkdir()
    (core / "a.md").write_text(
        "---\ntype: concept\ndifficulty: expert\n---\n"
        "关联 [[b]] 和 [[c]] 两个笔记",
        encoding="utf-8",
    )
    (core / "b.md").write_text("# B\n指向 [[a]]", encoding="utf-8")

    stats = KnowledgeStats(project_root=tmp_path)
    overview = stats.get_overview_stats()

    assert overview["total_notes"] == 2          # a.md + b.md
    assert overview["total_links"] == 3          # [[b]],[[c]],[[a]]
    assert overview["core_notes"] == 2
    assert overview["note_difficulties"].get("expert") == 1
