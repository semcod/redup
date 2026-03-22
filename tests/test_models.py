"""Tests for reDUP data models."""

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    RefactorSuggestion,
    RefactorAction,
    RiskLevel,
    ScanConfig,
    ScanStats,
)


def test_fragment_line_count():
    f = DuplicateFragment(file="a.py", line_start=10, line_end=20)
    assert f.line_count == 11


def test_group_saved_lines():
    g = DuplicateGroup(
        id="G1",
        duplicate_type=DuplicateType.EXACT,
        fragments=[
            DuplicateFragment(file="a.py", line_start=1, line_end=10),
            DuplicateFragment(file="b.py", line_start=5, line_end=14),
            DuplicateFragment(file="c.py", line_start=20, line_end=29),
        ],
    )
    assert g.occurrences == 3
    assert g.total_lines == 10
    assert g.saved_lines_potential == 20  # 10 * (3-1)


def test_group_single_occurrence_no_savings():
    g = DuplicateGroup(
        id="G2",
        duplicate_type=DuplicateType.EXACT,
        fragments=[DuplicateFragment(file="a.py", line_start=1, line_end=5)],
    )
    assert g.saved_lines_potential == 0


def test_group_impact_score():
    g = DuplicateGroup(
        id="G3",
        duplicate_type=DuplicateType.FUZZY,
        similarity_score=0.9,
        fragments=[
            DuplicateFragment(file="a.py", line_start=1, line_end=10),
            DuplicateFragment(file="b.py", line_start=1, line_end=10),
        ],
    )
    assert g.impact_score == 10 * 0.9  # saved_lines * similarity


def test_duplication_map_sorted_by_impact():
    big = DuplicateGroup(
        id="big",
        duplicate_type=DuplicateType.EXACT,
        fragments=[
            DuplicateFragment(file="a.py", line_start=1, line_end=50),
            DuplicateFragment(file="b.py", line_start=1, line_end=50),
        ],
    )
    small = DuplicateGroup(
        id="small",
        duplicate_type=DuplicateType.EXACT,
        fragments=[
            DuplicateFragment(file="c.py", line_start=1, line_end=3),
            DuplicateFragment(file="d.py", line_start=1, line_end=3),
        ],
    )
    dm = DuplicationMap(groups=[small, big])
    ranked = dm.sorted_by_impact()
    assert ranked[0].id == "big"
    assert ranked[1].id == "small"


def test_duplication_map_totals():
    dm = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="G1",
                duplicate_type=DuplicateType.EXACT,
                fragments=[
                    DuplicateFragment(file="a.py", line_start=1, line_end=10),
                    DuplicateFragment(file="b.py", line_start=1, line_end=10),
                ],
            ),
        ],
    )
    assert dm.total_groups == 1
    assert dm.total_fragments == 2
    assert dm.total_saved_lines == 10


def test_scan_config_defaults():
    config = ScanConfig()
    assert ".py" in config.extensions
    assert config.min_block_lines == 3
    assert config.min_similarity == 0.85
    assert not config.include_tests
