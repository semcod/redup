"""Tests for reDUP hasher."""

from redup.core.hasher import (
    build_hash_index,
    find_exact_duplicates,
    find_structural_duplicates,
    hash_block,
    hash_block_structural,
)
from redup.core.scanner import CodeBlock


def test_identical_blocks_same_hash():
    text = "def foo():\n    return 42"
    assert hash_block(text) == hash_block(text)


def test_comment_stripping():
    a = "x = 1\n# comment\ny = 2"
    b = "x = 1\ny = 2"
    assert hash_block(a) == hash_block(b)


def test_different_blocks_different_hash():
    a = "def foo():\n    return 1"
    b = "def bar():\n    return 2"
    assert hash_block(a) != hash_block(b)


def test_structural_hash_ignores_literals():
    a = 'name = "alice"\nage = 25'
    b = 'name = "bob"\nage = 30'
    assert hash_block_structural(a) == hash_block_structural(b)


def test_structural_hash_different_structure():
    a = "x = 1\ny = 2"
    b = "for i in range(10):\n    print(i)"
    assert hash_block_structural(a) != hash_block_structural(b)


def test_build_hash_index_groups_duplicates():
    blocks = [
        CodeBlock(
            file="a.py",
            line_start=1,
            line_end=5,
            text="def foo():\n    return 1\n    pass",
            function_name="foo",
        ),
        CodeBlock(
            file="b.py",
            line_start=1,
            line_end=5,
            text="def foo():\n    return 1\n    pass",
            function_name="foo",
        ),
        CodeBlock(
            file="c.py",
            line_start=1,
            line_end=5,
            text="def bar():\n    return 99\n    pass",
            function_name="bar",
        ),
    ]
    index = build_hash_index(blocks, min_lines=2)
    exact = find_exact_duplicates(index)
    # a.py and b.py should group together
    assert len(exact) >= 1
    for _h, group in exact.items():
        files = {b.block.file for b in group}
        assert len(files) >= 2


def test_find_structural_duplicates():
    blocks = [
        CodeBlock(
            file="a.py",
            line_start=1,
            line_end=5,
            text='name = "alice"\nage = 25\nprint(name)',
            function_name="f1",
        ),
        CodeBlock(
            file="b.py",
            line_start=1,
            line_end=5,
            text='name = "bob"\nage = 30\nprint(name)',
            function_name="f2",
        ),
    ]
    index = build_hash_index(blocks, min_lines=2)
    structural = find_structural_duplicates(index)
    assert len(structural) >= 1
