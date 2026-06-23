"""间隔重复系统（SM-2 算法）单元测试。

覆盖核心学习逻辑：难易度因子（ease factor）演化、复习间隔递增/重置、
遗忘指数计算、到期项目筛选与排序、复习时间估算等纯逻辑分支。

这些测试不依赖任何外部服务（向量库 / LLM），全部基于内存数据，
通过把数据文件重定向到 pytest 的临时目录来隔离副作用。
"""

import json
from datetime import datetime, timedelta

import pytest

from automation.spaced_repetition import SpacedRepetitionSystem, ReviewItem


@pytest.fixture
def srs(tmp_path):
    """构造一个数据隔离的间隔重复系统。

    把 review_data_file 指向临时目录，并清空内存中的项目，
    使每个用例从干净状态开始，且不会污染真实 docs/review_data.json。
    """
    system = SpacedRepetitionSystem(config={})
    system.review_data_file = tmp_path / "review_data.json"
    system.review_items = {}
    return system


# ─────────────────────────── 添加项目 ───────────────────────────

def test_add_review_item_sets_defaults(srs):
    srs.add_review_item("note-1", "Transformer", "ai-engineering", "expert", "high")
    item = srs.review_items["note-1"]

    assert item.repetition_count == 0
    assert item.interval_days == 1
    assert item.ease_factor == srs.default_ease_factor
    assert item.importance == "high"
    # 首次复习安排在明天
    next_review = datetime.fromisoformat(item.next_review)
    last_review = datetime.fromisoformat(item.last_review)
    assert (next_review - last_review).days == 1


def test_add_review_item_is_idempotent(srs):
    """同一 ID 重复添加应被忽略，不覆盖已有进度。"""
    srs.add_review_item("note-1", "Transformer", "ai-engineering", "expert")
    srs.review_items["note-1"].repetition_count = 5  # 模拟已有进度
    srs.add_review_item("note-1", "新标题", "foundation", "beginner")

    assert srs.review_items["note-1"].repetition_count == 5
    assert srs.review_items["note-1"].title == "Transformer"


# ─────────────────────────── SM-2 间隔演化 ───────────────────────────

def test_first_successful_review_interval_is_one(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    srs.record_review("n", quality=4)
    assert srs.review_items["n"].interval_days == 1
    assert srs.review_items["n"].repetition_count == 1


def test_second_successful_review_interval_is_six(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    srs.record_review("n", quality=4)  # rep 0 -> 1, interval 1
    srs.record_review("n", quality=4)  # rep 1 -> 2, interval 6
    assert srs.review_items["n"].interval_days == 6
    assert srs.review_items["n"].repetition_count == 2


def test_third_review_interval_scales_by_ease_factor(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    srs.record_review("n", quality=5)
    srs.record_review("n", quality=5)
    interval_before = srs.review_items["n"].interval_days  # 6
    srs.record_review("n", quality=5)
    # 第三次起 interval = round(上次 interval * 本次更新后的 ease_factor)
    # 注意：record_review 先更新 ease_factor，再用新值计算间隔
    ef_after = srs.review_items["n"].ease_factor
    assert srs.review_items["n"].interval_days == round(interval_before * ef_after)


def test_failure_resets_repetition_and_interval(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    srs.record_review("n", quality=5)
    srs.record_review("n", quality=5)
    assert srs.review_items["n"].repetition_count == 2

    srs.record_review("n", quality=1)  # 质量 < 3 视为遗忘
    assert srs.review_items["n"].repetition_count == 0
    assert srs.review_items["n"].interval_days == 1


def test_ease_factor_never_below_minimum(srs):
    """连续低质量复习不应让 ease factor 跌破下限 1.3。"""
    srs.add_review_item("n", "t", "c", "intermediate")
    for _ in range(10):
        srs.record_review("n", quality=0)
    assert srs.review_items["n"].ease_factor >= srs.minimum_ease_factor


def test_high_quality_increases_ease_factor(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    before = srs.review_items["n"].ease_factor
    srs.record_review("n", quality=5)
    assert srs.review_items["n"].ease_factor > before


def test_record_review_unknown_item_raises(srs):
    with pytest.raises(ValueError):
        srs.record_review("does-not-exist", quality=4)


def test_record_review_persists_to_disk(srs):
    srs.add_review_item("n", "t", "c", "intermediate")
    srs.record_review("n", quality=4)
    assert srs.review_data_file.exists()
    saved = json.loads(srs.review_data_file.read_text(encoding="utf-8"))
    assert saved["n"]["repetition_count"] == 1


# ─────────────────────────── 遗忘指数 ───────────────────────────

def test_forgetting_index_within_bounds(srs):
    item = ReviewItem(
        id="x", title="t", category="c", difficulty="intermediate",
        last_review="", next_review="", interval_days=1, ease_factor=2.5,
        repetition_count=0, quality_scores=[0, 1, 2, 3, 4, 5],
        importance="medium", forgetting_index=1.0,
    )
    fi = srs._calculate_forgetting_index(item)
    assert 0.0 <= fi <= 1.0


def test_forgetting_index_no_history_is_one(srs):
    item = ReviewItem(
        id="x", title="t", category="c", difficulty="intermediate",
        last_review="", next_review="", interval_days=1, ease_factor=2.5,
        repetition_count=0, quality_scores=[], importance="medium",
        forgetting_index=0.0,
    )
    assert srs._calculate_forgetting_index(item) == 1.0


def test_higher_quality_means_lower_forgetting(srs):
    good = ReviewItem("a", "t", "c", "intermediate", "", "", 1, 2.5, 0,
                      [5, 5, 5, 5, 5], "medium", 0.0)
    bad = ReviewItem("b", "t", "c", "intermediate", "", "", 1, 2.5, 0,
                     [1, 1, 1, 1, 1], "medium", 0.0)
    assert srs._calculate_forgetting_index(good) < srs._calculate_forgetting_index(bad)


# ─────────────────────────── 到期筛选与排序 ───────────────────────────

def _make_item(item_id, *, next_review, importance="medium", forgetting=0.5):
    return ReviewItem(
        id=item_id, title=item_id, category="c", difficulty="intermediate",
        last_review=datetime.now().isoformat(), next_review=next_review,
        interval_days=1, ease_factor=2.5, repetition_count=1,
        quality_scores=[4], importance=importance, forgetting_index=forgetting,
    )


def test_get_due_items_only_returns_past_due(srs):
    now = datetime.now()
    srs.review_items = {
        "past": _make_item("past", next_review=(now - timedelta(days=2)).isoformat()),
        "future": _make_item("future", next_review=(now + timedelta(days=5)).isoformat()),
    }
    due_ids = [d["id"] for d in srs.get_due_review_items()]
    assert "past" in due_ids
    assert "future" not in due_ids


def test_due_items_sorted_by_importance_first(srs):
    now = datetime.now()
    past = (now - timedelta(days=1)).isoformat()
    srs.review_items = {
        "low": _make_item("low", next_review=past, importance="low", forgetting=0.9),
        "high": _make_item("high", next_review=past, importance="high", forgetting=0.1),
    }
    due = srs.get_due_review_items()
    # 高重要性优先，即使其遗忘指数更低
    assert due[0]["id"] == "high"


# ─────────────────────────── 辅助计算 ───────────────────────────

@pytest.mark.parametrize("days,expected", [
    (1, "1天"),
    (5, "1周内"),
    (20, "1月内"),
    (60, "3月内"),
    (200, "3月以上"),
])
def test_interval_range_buckets(srs, days, expected):
    assert srs._get_interval_range(days) == expected


def test_estimate_review_time_scales_with_difficulty(srs):
    easy = ReviewItem("a", "t", "c", "beginner", "", "", 1, 2.5, 0, [], "medium", 0.0)
    hard = ReviewItem("b", "t", "c", "expert", "", "", 1, 2.5, 0, [], "medium", 0.0)
    assert srs._estimate_review_time(hard) > srs._estimate_review_time(easy)
    assert srs._estimate_review_time(easy) > 0


def test_statistics_empty_state(srs):
    stats = srs.get_review_statistics()
    assert stats["total_items"] == 0
    assert "suggestion" in stats


def test_statistics_reports_counts(srs):
    now = datetime.now()
    srs.review_items = {
        "a": _make_item("a", next_review=(now - timedelta(days=1)).isoformat(), importance="high"),
        "b": _make_item("b", next_review=(now + timedelta(days=3)).isoformat(), importance="low"),
    }
    stats = srs.get_review_statistics()
    assert stats["total_items"] == 2
    assert stats["due_items"] == 1
    assert stats["importance_distribution"] == {"high": 1, "low": 1}
