"""Matcher — detailed similarity comparison for candidate duplicate pairs."""

from __future__ import annotations

import difflib
from collections.abc import Callable
from dataclasses import dataclass

from redup.core.hasher import HashedBlock, _normalize_text


@dataclass
class MatchResult:
    """Result of comparing two code blocks."""

    block_a: HashedBlock
    block_b: HashedBlock
    similarity: float
    method: str  # "exact", "sequence", "fuzzy"


def sequence_similarity(text_a: str, text_b: str) -> float:
    """SequenceMatcher ratio between two normalized texts."""
    norm_a = _normalize_text(text_a)
    norm_b = _normalize_text(text_b)
    if not norm_a or not norm_b:
        return 0.0
    return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def fuzzy_similarity(text_a: str, text_b: str) -> float:
    """Fuzzy similarity using rapidfuzz if available, fallback to SequenceMatcher."""
    try:
        from rapidfuzz import fuzz

        norm_a = _normalize_text(text_a)
        norm_b = _normalize_text(text_b)
        return fuzz.ratio(norm_a, norm_b) / 100.0
    except ImportError:
        return sequence_similarity(text_a, text_b)


def _compare_against_reference(
    candidates: list[HashedBlock],
    min_similarity: float,
    similarity_fn: Callable[[str, str], float],
    method_fn: Callable[[float], str],
    skip_same_location: bool = False,
) -> list[MatchResult]:
    if len(candidates) < 2:
        return []

    results: list[MatchResult] = []
    ref = candidates[0]

    for other in candidates[1:]:
        if skip_same_location and (
            ref.block.file == other.block.file and ref.block.line_start == other.block.line_start
        ):
            continue

        sim = similarity_fn(ref.block.text, other.block.text)
        if sim >= min_similarity:
            results.append(
                MatchResult(
                    block_a=ref,
                    block_b=other,
                    similarity=sim,
                    method=method_fn(sim),
                )
            )

    return results


def match_candidates(
    candidates: list[HashedBlock],
    min_similarity: float = 0.85,
) -> list[MatchResult]:
    """Compare all pairs in a candidate group and return matches above threshold.

    Uses the first block as reference and compares all others against it.
    """
    return _compare_against_reference(
        candidates,
        min_similarity,
        fuzzy_similarity,
        lambda sim: "exact" if sim >= 0.999 else "fuzzy",
    )


def refine_structural_matches(
    candidates: list[HashedBlock],
    min_similarity: float = 0.80,
) -> list[MatchResult]:
    """For structural hash collisions, verify with text similarity.

    Structural hashes normalize variable names, so we use a lower threshold
    and verify the overall shape matches.
    """
    return _compare_against_reference(
        candidates,
        min_similarity,
        sequence_similarity,
        lambda _sim: "structural",
        skip_same_location=True,
    )
