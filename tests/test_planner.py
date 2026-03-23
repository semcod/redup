"""Tests for reDUP planner."""

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    RefactorAction,
)
from redup.core.planner import generate_suggestions


def test_generate_suggestions_basic():
    dm = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="E0001",
                duplicate_type=DuplicateType.EXACT,
                normalized_name="calculate_tax",
                fragments=[
                    DuplicateFragment(file="billing.py", line_start=1, line_end=10, function_name="calculate_tax"),
                    DuplicateFragment(file="shipping.py", line_start=1, line_end=10, function_name="calculate_tax"),
                    DuplicateFragment(file="returns.py", line_start=1, line_end=10, function_name="calculate_tax"),
                ],
            ),
        ],
    )
    suggestions = generate_suggestions(dm)
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s.priority == 1
    assert s.action == RefactorAction.EXTRACT_FUNCTION
    assert len(s.original_files) == 3
    assert "saves 20 lines" in s.rationale


def test_no_suggestions_for_single_occurrence():
    dm = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="E0002",
                duplicate_type=DuplicateType.EXACT,
                fragments=[
                    DuplicateFragment(file="a.py", line_start=1, line_end=5),
                ],
            ),
        ],
    )
    suggestions = generate_suggestions(dm)
    assert len(suggestions) == 0


def test_priority_ordering():
    dm = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="small",
                duplicate_type=DuplicateType.EXACT,
                fragments=[
                    DuplicateFragment(file="a.py", line_start=1, line_end=3),
                    DuplicateFragment(file="b.py", line_start=1, line_end=3),
                ],
            ),
            DuplicateGroup(
                id="big",
                duplicate_type=DuplicateType.EXACT,
                fragments=[
                    DuplicateFragment(file="c.py", line_start=1, line_end=50),
                    DuplicateFragment(file="d.py", line_start=1, line_end=50),
                ],
            ),
        ],
    )
    suggestions = generate_suggestions(dm)
    assert len(suggestions) == 2
    # big should be priority 1
    assert suggestions[0].group_id == "big"
    assert suggestions[0].priority == 1


def test_large_block_extract_module():
    dm = DuplicationMap(
        groups=[
            DuplicateGroup(
                id="huge",
                duplicate_type=DuplicateType.EXACT,
                fragments=[
                    DuplicateFragment(file="a.py", line_start=1, line_end=60, function_name="big_func"),
                    DuplicateFragment(file="b.py", line_start=1, line_end=60, function_name="big_func"),
                ],
            ),
        ],
    )
    suggestions = generate_suggestions(dm)
    assert suggestions[0].action == RefactorAction.EXTRACT_MODULE
