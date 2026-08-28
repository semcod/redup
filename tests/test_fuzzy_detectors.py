"""Tests for shared fuzzy detector mechanics."""

from redup.core.fuzzy_similarity import _find_similar_pairs
from redup.core.scanner import CodeBlock


def test_find_similar_pairs_extracts_once_and_skips_missing_signatures() -> None:
    blocks = [
        CodeBlock("one.py", 1, 1, "10"),
        CodeBlock("two.py", 1, 1, "11"),
        CodeBlock("ignored.py", 1, 1, "missing"),
        CodeBlock("far.py", 1, 1, "30"),
    ]
    extracted = []

    def extract(block: CodeBlock) -> int | None:
        extracted.append(block.file)
        return None if block.text == "missing" else int(block.text)

    def similarity(left: int, right: int) -> float:
        return 1.0 - abs(left - right) / 10

    pairs = _find_similar_pairs(blocks, extract, similarity, threshold=0.8)

    assert extracted == ["one.py", "two.py", "ignored.py", "far.py"]
    assert pairs == [(blocks[0], blocks[1], 0.9)]
