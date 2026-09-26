"""Tests for ast_normalizer and exact_matcher atomized modules."""

from __future__ import annotations

import ast

from redup.core.ast_normalizer import (
    ast_to_normalized_string,
    normalize_ast_text,
)
from redup.core.exact_matcher import (
    HashedBlock,
    HashIndex,
    blocks_from_different_locations,
    find_duplicates,
    find_exact_duplicates,
    find_structural_duplicates,
)
from redup.core.scanner_types import CodeBlock


def test_ast_to_normalized_string_function() -> None:
    code = "def compute(a, b):\n    return a + b"
    tree = ast.parse(code)
    norm = ast_to_normalized_string(tree)
    assert "FUNC" in norm
    assert "ARG" in norm
    assert "BINOP_Add" in norm


def test_normalize_ast_text_rename_invariance() -> None:
    code1 = "def foo(x):\n    val = x * 2\n    return val"
    code2 = "def bar(y):\n    out = y * 2\n    return out"
    norm1 = normalize_ast_text(code1)
    norm2 = normalize_ast_text(code2)
    assert norm1 == norm2


def test_normalize_ast_text_syntax_error_fallback() -> None:
    broken_code = "func(broken syntax [[[ {"
    norm = normalize_ast_text(broken_code)
    assert isinstance(norm, str)
    assert len(norm) > 0


def test_blocks_from_different_locations() -> None:
    b1 = HashedBlock(
        block=CodeBlock(file="a.py", line_start=10, line_end=15, text="code", function_name="f")
    )
    b2 = HashedBlock(
        block=CodeBlock(file="a.py", line_start=10, line_end=15, text="code", function_name="f")
    )
    # Same location -> False
    assert not blocks_from_different_locations([b1, b2])

    b3 = HashedBlock(
        block=CodeBlock(file="b.py", line_start=20, line_end=25, text="code", function_name="f")
    )
    # Different locations -> True
    assert blocks_from_different_locations([b1, b3])


def test_find_duplicates_filters_singletons() -> None:
    b1 = HashedBlock(
        block=CodeBlock(file="a.py", line_start=1, line_end=5, text="c1", function_name="f1")
    )
    b2 = HashedBlock(
        block=CodeBlock(file="b.py", line_start=1, line_end=5, text="c1", function_name="f2")
    )
    b3 = HashedBlock(
        block=CodeBlock(file="c.py", line_start=1, line_end=5, text="c2", function_name="f3")
    )

    hash_dict = {
        "hash_group": [b1, b2],
        "singleton_hash": [b3],
    }
    dups = find_duplicates(hash_dict)
    assert "hash_group" in dups
    assert "singleton_hash" not in dups
    assert len(dups["hash_group"]) == 2


def test_find_exact_and_structural_duplicates() -> None:
    index = HashIndex()
    b1 = HashedBlock(
        block=CodeBlock(file="a.py", line_start=1, line_end=5, text="x", function_name="f"),
        exact_hash="h_exact",
        structural_hash="h_struct",
    )
    b2 = HashedBlock(
        block=CodeBlock(file="b.py", line_start=1, line_end=5, text="x", function_name="f"),
        exact_hash="h_exact",
        structural_hash="h_struct",
    )
    index.exact["h_exact"].extend([b1, b2])
    index.structural["h_struct"].extend([b1, b2])

    exact = find_exact_duplicates(index)
    struct = find_structural_duplicates(index)
    assert "h_exact" in exact
    assert "h_struct" in struct
