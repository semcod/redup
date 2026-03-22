"""Matcher — detailed similarity comparison for candidate duplicate pairs."""

from __future__ import annotations

import difflib
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


def match_candidates(
    candidates: list[HashedBlock],
    min_similarity: float = 0.85,
) -> list[MatchResult]:
    """Compare all pairs in a candidate group and return matches above threshold.

    Uses the first block as reference and compares all others against it.
    """
    if len(candidates) < 2:
        return []

    results: list[MatchResult] = []
    ref = candidates[0]

    for other in candidates[1:]:
        sim = fuzzy_similarity(ref.block.text, other.block.text)
        if sim >= min_similarity:
            method = "exact" if sim >= 0.999 else "fuzzy"
            results.append(MatchResult(
                block_a=ref, block_b=other, similarity=sim, method=method
            ))

    return results


def refine_structural_matches(
    candidates: list[HashedBlock],
    min_similarity: float = 0.80,
) -> list[MatchResult]:
    """For structural hash collisions, verify with text similarity.

    Structural hashes normalize variable names, so we use a lower threshold
    and verify the overall shape matches.
    """
    if len(candidates) < 2:
        return []

    results: list[MatchResult] = []
    ref = candidates[0]

    for other in candidates[1:]:
        if ref.block.file == other.block.file and ref.block.line_start == other.block.line_start:
            continue
        sim = sequence_similarity(ref.block.text, other.block.text)
        if sim >= min_similarity:
            results.append(MatchResult(
                block_a=ref, block_b=other, similarity=sim, method="structural"
            ))

    return results
