"""Regression coverage for real LSH candidates and mutable scanner blocks."""

import pytest

from redup.core import lsh_matcher
from redup.core.models import DuplicateType, ScanConfig
from redup.core.pipeline.duplicate_finder import find_near_duplicate_groups
from redup.core.scanner import CodeBlock


@pytest.fixture(params=["native", "fallback"])
def backend(request, monkeypatch):
    if request.param == "native":
        pytest.importorskip("datasketch")
        assert lsh_matcher.MinHash is not None
    else:
        monkeypatch.setattr(lsh_matcher, "MinHash", None)
        monkeypatch.setattr(lsh_matcher, "MinHashLSH", None)
    return request.param


def block(file="left.py", text="alpha beta gamma delta epsilon", lines=12):
    return CodeBlock(file, 1, lines, text, function_name="sample")


def test_index_returns_real_candidates_above_threshold(backend):
    left, unrelated = block(), block("other.py", "one two three four five")
    index = lsh_matcher.LSHIndex(threshold=0.8)
    index.add(left)
    index.add(unrelated)
    assert index.find_near_duplicates(block("query.py")) == [(left, 1.0)]


@pytest.mark.parametrize("failure", ["query_error", "no_index"])
def test_native_candidate_selection_failure_compares_stored_hashes(monkeypatch, failure):
    pytest.importorskip("datasketch")
    left = block()
    index = lsh_matcher.LSHIndex(threshold=0.8)
    index.add(left)
    index.add(block("other.py", "one two three four five"))
    if failure == "query_error":

        def fail_query(query):
            raise RuntimeError("candidate backend unavailable")

        monkeypatch.setattr(index.lsh, "query", fail_query)
    else:
        index.lsh = None
    assert index.find_near_duplicates(block("query.py")) == [(left, 1.0)]


def test_groups_use_mutable_blocks_once_and_omit_singletons(backend):
    left, right, third = block(), block("right.py"), block("third.py")
    unrelated = block("unique.py", "one two three four five")
    short = block("short.py", lines=2)
    groups = lsh_matcher.find_near_duplicates(
        [left, right, third, unrelated, short], threshold=0.8, min_lines=10
    )
    assert list(groups) == ["LSH_0000"]
    members = groups["LSH_0000"]
    assert len(members) == 3
    assert {id(member) for member, _ in members} == {id(left), id(right), id(third)}
    assert all(similarity == 1.0 for _, similarity in members)


def test_equal_blocks_are_distinct_occurrences(backend):
    left, right = block(), block()
    assert left == right and left is not right
    groups = lsh_matcher.find_near_duplicates([left, right], min_lines=10)
    assert len(groups) == 1
    assert {id(member) for member, _ in next(iter(groups.values()))} == {id(left), id(right)}


def test_single_occurrence_is_not_a_duplicate_group(backend):
    assert lsh_matcher.find_near_duplicates([block()], min_lines=10) == {}
    assert lsh_matcher.find_near_duplicates([], min_lines=10) == {}


def test_pipeline_receives_two_real_occurrences(backend):
    left, right = block(), block("right.py")
    groups = find_near_duplicate_groups(
        [left, right], ScanConfig(lsh_enabled=True, lsh_min_lines=10, lsh_threshold=0.8)
    )
    assert len(groups) == 1
    assert groups[0].duplicate_type == DuplicateType.NEAR_DUPLICATE
    assert {fragment.file for fragment in groups[0].fragments} == {"left.py", "right.py"}
    assert groups[0].occurrences == 2
    assert groups[0].similarity_score == 1.0
