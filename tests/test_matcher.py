"""Tests for reDUP matcher."""

from redup.core.hasher import HashedBlock
from redup.core.matcher import (
    sequence_similarity,
    fuzzy_similarity,
    match_candidates,
    refine_structural_matches,
)
from redup.core.scanner import CodeBlock


def _make_hashed(file: str, text: str, func: str = "f") -> HashedBlock:
    return HashedBlock(
        block=CodeBlock(file=file, line_start=1, line_end=5, text=text, function_name=func),
        exact_hash="abc",
        structural_hash="def",
    )


def test_sequence_similarity_identical():
    assert sequence_similarity("x = 1", "x = 1") == 1.0


def test_sequence_similarity_different():
    sim = sequence_similarity("x = 1", "for i in range(100): print(i)")
    assert sim < 0.5


def test_fuzzy_similarity_close():
    a = "def foo(x):\n    return x + 1"
    b = "def foo(y):\n    return y + 1"
    sim = fuzzy_similarity(a, b)
    assert sim > 0.8


def test_match_candidates_above_threshold():
    text = "def foo():\n    return 42\n    pass"
    a = _make_hashed("a.py", text)
    b = _make_hashed("b.py", text)
    matches = match_candidates([a, b], min_similarity=0.85)
    assert len(matches) == 1
    assert matches[0].similarity >= 0.99


def test_match_candidates_below_threshold():
    a = _make_hashed("a.py", "def foo():\n    return 1")
    b = _make_hashed("b.py", "class Bar:\n    pass\n    x = 99")
    matches = match_candidates([a, b], min_similarity=0.85)
    assert len(matches) == 0


def test_refine_structural_same_location_skipped():
    text = "x = 1\ny = 2\nz = 3"
    a = HashedBlock(
        block=CodeBlock(file="a.py", line_start=1, line_end=3, text=text, function_name="f"),
        exact_hash="x", structural_hash="y",
    )
    # Same file and line — should be skipped
    b = HashedBlock(
        block=CodeBlock(file="a.py", line_start=1, line_end=3, text=text, function_name="f"),
        exact_hash="x", structural_hash="y",
    )
    matches = refine_structural_matches([a, b], min_similarity=0.5)
    assert len(matches) == 0
