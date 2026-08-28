"""Compact JSON payloads for cross-project comparisons."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from redup.core.community import CodeCommunity
    from redup.core.comparator import CrossProjectComparison


def _make_relative_path(path: str, project_a: str, project_b: str) -> str:
    """Strip either project root from a matched file path."""
    for root in (project_a, project_b):
        try:
            return Path(path).relative_to(root).as_posix()
        except ValueError:
            continue
    return Path(path).as_posix()


def _deduplicate_matches(
    comparison: CrossProjectComparison,
) -> list[dict[str, Any]]:
    """Keep the strongest result for each function/file pair."""
    project_a = str(comparison.project_a)
    project_b = str(comparison.project_b)
    deduplicated: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for match in comparison.matches:
        key = (match.function_a, match.function_b, match.file_a, match.file_b)
        candidate = {
            "type": match.similarity_type,
            "similarity": round(match.similarity, 3),
            "function_a": match.function_a,
            "function_b": match.function_b,
            "file_a": _make_relative_path(match.file_a, project_a, project_b),
            "file_b": _make_relative_path(match.file_b, project_a, project_b),
            "lines_a": list(match.lines_a),
            "lines_b": list(match.lines_b),
            "loc": max(
                match.lines_a[1] - match.lines_a[0] + 1,
                match.lines_b[1] - match.lines_b[0] + 1,
            ),
        }
        current = deduplicated.get(key)
        if current is None or candidate["similarity"] > current["similarity"]:
            deduplicated[key] = candidate

    return sorted(deduplicated.values(), key=lambda item: item["loc"], reverse=True)


def _compact_community(
    community: CodeCommunity,
    project_a: str,
    project_b: str,
) -> dict[str, Any]:
    """Convert a graph community to an LLM-friendly structure."""
    members = []
    for project, node_key in community.members:
        parts = node_key.split("::")
        file_path = parts[-2] if len(parts) >= 3 else ""
        function_name = parts[-1]
        members.append(
            {
                "project": "A" if project == project_a else "B",
                "file": _make_relative_path(file_path, project_a, project_b),
                "function": function_name,
            }
        )
    return {
        "name": community.extraction_candidate_name,
        "similarity": round(community.avg_similarity, 3),
        "loc": community.total_loc,
        "members": members,
    }


def comparison_to_dict(
    comparison: CrossProjectComparison,
    communities: list[CodeCommunity],
    *,
    max_matches: int | None = None,
) -> dict[str, Any]:
    """Build one shared report shape for the CLI and MCP interfaces."""
    if max_matches is not None and max_matches < 0:
        raise ValueError("max_matches must be zero or greater")

    project_a = str(comparison.project_a)
    project_b = str(comparison.project_b)
    matches = _deduplicate_matches(comparison)
    returned_matches = matches[:max_matches] if max_matches else matches
    compact_communities = [
        _compact_community(community, project_a, project_b)
        for community in communities
        if community.total_loc >= 8
    ][:20]

    recommendation = None
    if communities:
        from redup.core.decision import recommend

        result = recommend(comparison, communities)
        recommendation = {
            "decision": result.decision.value,
            "rationale": result.rationale,
            "overlap_pct": round(result.overlap_percent, 4),
            "shared_loc": result.shared_loc,
            "confidence": result.confidence,
        }

    payload = {
        "project_a": project_a,
        "project_b": project_b,
        "stats": {"a": comparison.stats_a, "b": comparison.stats_b},
        "total_matches": len(matches),
        "shared_loc_potential": comparison.shared_loc_potential,
        "recommendation": recommendation,
        "communities": compact_communities,
        "matches": returned_matches,
    }
    if max_matches is not None:
        payload["selection"] = {
            "max_matches": max_matches,
            "returned_matches": len(returned_matches),
            "omitted_matches": len(matches) - len(returned_matches),
            "truncated": len(returned_matches) < len(matches),
        }
    return payload


__all__ = ["comparison_to_dict"]
