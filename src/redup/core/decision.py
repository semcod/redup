"""Refactoring decision engine — merge / split / extract recommendations.

Combines cross-project comparison metrics with community detection results
to produce actionable refactoring recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from redup.core.comparator import CrossProjectComparison
from redup.core.community import CodeCommunity


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
    overlap = shared_loc / total_loc if total_loc > 0 else 0.0

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
            f"{len(communities)} clusters). Extract to shared library."
        )
        confidence = 0.8
    elif overlap > 0.05:
        decision = RefactorDecision.EXTRACT_SHARED_LIB
        rationale = (
            f"Small overlap ({overlap:.0%}) but {len(communities)} "
            f"well-defined clusters — worth extracting."
        )
        confidence = 0.6
    else:
        decision = RefactorDecision.KEEP_SEPARATE
        rationale = (
            f"Projects are {overlap:.1%} similar — distinct concerns, "
            f"no refactoring needed."
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
