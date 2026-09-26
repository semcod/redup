"""Matcher — detailed similarity comparison for candidate duplicate pairs."""

from __future__ import annotations

import difflib
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from redup.core.hasher import HashedBlock, _normalize_text
from redup.core.lsh_matcher import find_near_duplicates
from redup.core.tokens_hasher import find_rust_hasher_binary


@dataclass
class MatchResult:
    """Result of comparing two code blocks."""

    block_a: HashedBlock
    block_b: HashedBlock
    similarity: float
    method: str  # "exact", "sequence", "fuzzy"


def sequence_similarity_rust(
    text_a: str, text_b: str, binary_path: Path | None = None
) -> float | None:
    """Execute native Rust sequence similarity engine.

    Returns None if binary is missing or execution fails.
    """
    bin_path = binary_path or find_rust_hasher_binary()
    if not bin_path:
        return None
    try:
        proc = subprocess.run(
            [str(bin_path), "--similarity", text_a, text_b],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return float(proc.stdout.strip())
    except (subprocess.SubprocessError, ValueError, OSError):
        return None


def sequence_similarity(text_a: str, text_b: str, *, prefer_rust: bool = False) -> float:
    """SequenceMatcher ratio between two normalized texts."""
    norm_a = _normalize_text(text_a)
    norm_b = _normalize_text(text_b)
    if not norm_a or not norm_b:
        return 0.0
    if norm_a == norm_b:
        return 1.0

    if prefer_rust or os.getenv("REDUP_USE_RUST") == "1":
        rust_sim = sequence_similarity_rust(norm_a, norm_b)
        if rust_sim is not None:
            return rust_sim

    try:
        from rapidfuzz import fuzz

        return fuzz.ratio(norm_a, norm_b) / 100.0
    except ImportError:
        return difflib.SequenceMatcher(None, norm_a, norm_b).ratio()


def fuzzy_similarity(text_a: str, text_b: str, *, prefer_rust: bool = False) -> float:
    """Fuzzy similarity using rapidfuzz or Rust if available, fallback to SequenceMatcher."""
    return sequence_similarity(text_a, text_b, prefer_rust=prefer_rust)


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
    """Compare all pairs in a candidate group and return matches above threshold."""
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
    """For structural hash collisions, verify with text similarity."""
    return _compare_against_reference(
        candidates,
        min_similarity,
        sequence_similarity,
        lambda _sim: "structural",
        skip_same_location=True,
    )


__all__ = [
    "MatchResult",
    "sequence_similarity",
    "sequence_similarity_rust",
    "fuzzy_similarity",
    "match_candidates",
    "refine_structural_matches",
    "find_near_duplicates",
]
