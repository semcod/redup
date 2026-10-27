"""Refactoring decision engine — merge / split / extract recommendations.

Combines cross-project comparison metrics with community detection results
to produce actionable refactoring recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from redup.core.community import CodeCommunity
from redup.core.comparator import CrossProjectComparison


class RefactorDecision(str, Enum):
    MERGE_PROJECTS = "merge_projects"
    EXTRACT_SHARED_LIB = "extract_shared_lib"
    KEEP_SEPARATE = "keep_separate"
    SPLIT_PROJECT = "split_project"


@dataclass
class DecisionRecommendation:
    """Actionable recommendation produced by the decision engine."""

    decision: RefactorDecision
    rationale: str
    overlap_percent: float
    shared_loc: int
    communities: list[CodeCommunity] = field(default_factory=list)
    confidence: float = 0.0


def _matched_nodes_loc(comparison: CrossProjectComparison) -> int:
    """Calculate total deduplicated LOC across matched nodes in both projects."""
    nodes: dict[tuple[str, str, str, tuple[int, int]], int] = {}
    for match in comparison.matches:
        key_a = (match.project_a, match.file_a, match.function_a, match.lines_a)
        key_b = (match.project_b, match.file_b, match.function_b, match.lines_b)
        nodes[key_a] = max(0, match.lines_a[1] - match.lines_a[0] + 1)
        nodes[key_b] = max(0, match.lines_b[1] - match.lines_b[0] + 1)
    return sum(nodes.values())


def recommend(
    comparison: CrossProjectComparison,
    communities: list[CodeCommunity],
) -> DecisionRecommendation:
    """Generate a refactoring recommendation from comparison + communities.

    Decision thresholds:
        >60 % overlap → merge projects
        >20 % overlap → extract shared library
        >5 %  overlap → extract (lower confidence)
        ≤5 %  overlap → keep separate

    Args:
        comparison: Result of ``compare_projects``.
        communities: Detected code communities.

    Returns:
        A single ``DecisionRecommendation``.
    """
    total_loc_a = comparison.stats_a.get("lines", 0)
    total_loc_b = comparison.stats_b.get("lines", 0)
    total_loc = total_loc_a + total_loc_b
    shared_loc = sum(c.total_loc for c in communities)
    if shared_loc == 0 and not communities and comparison.matches:
        shared_loc = _matched_nodes_loc(comparison)
    overlap = shared_loc / total_loc if total_loc > 0 else 0.0
    cluster_count = len(communities) if communities else len(comparison.matches)

    if overlap > 0.60:
        decision = RefactorDecision.MERGE_PROJECTS
        rationale = (
            f"{overlap:.0%} of code is shared — projects are nearly identical. "
            f"Merging eliminates {shared_loc} duplicate lines."
        )
        confidence = 0.9
    elif overlap > 0.20:
        decision = RefactorDecision.EXTRACT_SHARED_LIB
        rationale = (
            f"{overlap:.0%} overlap ({shared_loc} shared lines, "
            f"{cluster_count} clusters). Extract to shared library."
        )
        confidence = 0.8
    elif overlap > 0.05:
        decision = RefactorDecision.EXTRACT_SHARED_LIB
        rationale = (
            f"Small overlap ({overlap:.0%}) but {cluster_count} "
            f"well-defined clusters — worth extracting."
        )
        confidence = 0.6
    else:
        decision = RefactorDecision.KEEP_SEPARATE
        rationale = (
            f"Projects are {overlap:.1%} similar — distinct concerns, no refactoring needed."
        )
        confidence = 0.9

    return DecisionRecommendation(
        decision=decision,
        rationale=rationale,
        overlap_percent=overlap,
        shared_loc=shared_loc,
        communities=communities,
        confidence=confidence,
    )
