"""Regression coverage for real LSH candidates and mutable scanner blocks."""

import random

import pytest

from redup.core import lsh_matcher, tokens_hasher
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


def test_native_minhash_matches_signature_and_is_order_invariant():
    pytest.importorskip("datasketch")
    native = pytest.importorskip("redup_fast_hash")
    first = lsh_matcher._create_minhash("alpha beta gamma delta epsilon")
    reordered = lsh_matcher._create_minhash("epsilon delta alpha beta gamma gamma")
    expected = native.compute_minhash_signature(
        list(dict.fromkeys(lsh_matcher._normalize_text("alpha beta gamma delta epsilon").split())),
        128,
    )
    assert list(first.hashvalues) == list(expected)
    assert first.jaccard(reordered) == 1.0


def test_batch_minhash_signature():
    pytest.importorskip("datasketch")
    native = pytest.importorskip("redup_fast_hash")
    assert hasattr(native, "batch_minhash_signature")
    items = [
        ["alpha", "beta"],
        ["gamma", "delta"],
    ]
    sigs = native.batch_minhash_signature(items, 128)
    assert len(sigs) == 2
    assert sigs[0] == native.compute_minhash_signature(items[0], 128)
    assert sigs[1] == native.compute_minhash_signature(items[1], 128)


def test_index_add_blocks_batch(backend):
    blocks = [
        block("b1.py", "alpha beta gamma delta epsilon"),
        block("b2.py", "alpha beta gamma delta epsilon"),
        block("b3.py", "one two three four five"),
    ]
    index = lsh_matcher.LSHIndex(threshold=0.8)
    index.add_blocks(blocks)
    assert len(index.blocks) == 3
    matches = index.find_near_duplicates(block("query.py", "alpha beta gamma delta epsilon"))
    assert len(matches) == 2


@pytest.fixture
def simple_backend(monkeypatch):
    monkeypatch.setattr(lsh_matcher, "MinHash", None)
    monkeypatch.setattr(lsh_matcher, "MinHashLSH", None)
    monkeypatch.setattr(tokens_hasher, "redup_fast_hash", None)


def signature(values):
    result = object.__new__(lsh_matcher._SimpleMinHash)
    result.num_perm = len(values)
    result.hash_values = values
    return result


def exhaustive_matches(index, query):
    matches = []
    for candidate, stored in zip(index.blocks, index.minhashes, strict=True):
        if isinstance(stored, lsh_matcher._SimpleMinHash):
            score = query.jaccard(stored)
            if score >= index.threshold:
                matches.append((candidate, score))
    return sorted(matches, key=lambda item: item[1], reverse=True)


@pytest.mark.parametrize("width", [7, 25, 128])
@pytest.mark.parametrize("threshold", [0, 0.1, 7 / 25, 0.5, 0.85, 1, 1.1])
def test_fallback_matches_exhaustive_scores_and_stable_order(
    simple_backend, monkeypatch, width, threshold
):
    rng = random.Random(731)
    anchor = [rng.getrandbits(128) for _ in range(width)]
    vectors = [anchor, list(anchor)]
    for equal in range(width + 1):
        vector = [rng.getrandbits(128) for _ in range(width)]
        for position in rng.sample(range(width), equal):
            vector[position] = anchor[position]
        vectors.append(vector)
    signatures = {str(i): signature(vector) for i, vector in enumerate(vectors)}
    monkeypatch.setattr(lsh_matcher, "_create_simple_minhash", lambda text, _: signatures[text])
    index = lsh_matcher.LSHIndex(threshold=threshold, num_perm=width)
    index.add_blocks([block(str(i), str(i)) for i in range(len(vectors))])
    for query in index.blocks[:6]:
        assert index.find_near_duplicates(query) == exhaustive_matches(
            index, signatures[query.text]
        )


def test_fallback_prunes_comparisons_and_refreshes_after_add(simple_backend, monkeypatch):
    signatures = {str(i): signature([i * 1000 + j for j in range(128)]) for i in range(1000)}
    signatures["duplicate"] = signatures["0"]
    monkeypatch.setattr(lsh_matcher, "_create_simple_minhash", lambda text, _: signatures[text])
    index = lsh_matcher.LSHIndex(threshold=0.85)
    index.add_blocks([block(str(i), str(i)) for i in range(1000)])
    calls = []
    original = lsh_matcher._SimpleMinHash.jaccard

    def counted(left, right):
        calls.append(1)
        return original(left, right)

    monkeypatch.setattr(lsh_matcher._SimpleMinHash, "jaccard", counted)
    assert index.find_near_duplicates(index.blocks[0]) == [(index.blocks[0], 1.0)]
    assert len(calls) == 1
    calls.clear()
    duplicate = block("duplicate.py", "duplicate")
    index.add(duplicate)
    assert index.find_near_duplicates(index.blocks[0]) == [(index.blocks[0], 1.0), (duplicate, 1.0)]
    assert len(calls) == 2


def test_fallback_refreshes_after_threshold_change(simple_backend, monkeypatch):
    signatures = {
        "query": signature(list(range(25))),
        "partial": signature(list(range(7)) + [-1] * 18),
    }
    monkeypatch.setattr(lsh_matcher, "_create_simple_minhash", lambda text, _: signatures[text])
    index = lsh_matcher.LSHIndex(threshold=0.85, num_perm=25)
    query, partial = block(text="query"), block("partial.py", "partial")
    index.add_blocks([query, partial])
    assert index.find_near_duplicates(query) == [(query, 1.0)]
    index.threshold = 7 / 25
    assert index.find_near_duplicates(query) == [(query, 1.0), (partial, 7 / 25)]


def test_fallback_preserves_native_scorer_semantics(simple_backend, monkeypatch):
    from types import SimpleNamespace

    index = lsh_matcher.LSHIndex(threshold=0.85)
    left, other = block(), block("other.py", "unrelated tokens entirely")
    index.add_blocks([left, other])
    # A native scorer is an independent backend; do not assume equality-count semantics.
    monkeypatch.setattr(
        tokens_hasher, "redup_fast_hash", SimpleNamespace(minhash_jaccard=lambda a, b: 1.0)
    )
    assert index.find_near_duplicates(left) == [(left, 1.0), (other, 1.0)]


def test_fallback_groups_match_exhaustive_grouping(simple_backend, monkeypatch):
    blocks = [block(f"{i}.py", f"alpha beta gamma {i % 3} epsilon") for i in range(30)]
    indexed = lsh_matcher.find_near_duplicates(blocks, threshold=0.7)

    def exhaustive(self, query):
        return exhaustive_matches(
            self, lsh_matcher._create_simple_minhash(query.text, self.num_perm)
        )

    monkeypatch.setattr(lsh_matcher.LSHIndex, "_find_near_duplicates_simple", exhaustive)
    assert indexed == lsh_matcher.find_near_duplicates(blocks, threshold=0.7)
