"""JSON reporter — machine-readable duplication map."""

from __future__ import annotations

import json
from typing import Any

from redup.core.models import DuplicateType, DuplicationMap

_GROUP_SCOPES = frozenset({"all", "non_generated", "refactor", "review", "generated"})


def _fragment_to_dict(fragment: Any, include_snippets: bool, *, compact: bool) -> dict[str, Any]:
    payload = {
        "file": fragment.file,
        "line_start": fragment.line_start,
        "line_end": fragment.line_end,
        "function_name": fragment.function_name,
        "class_name": fragment.class_name,
    }
    if compact:
        payload = {key: value for key, value in payload.items() if value is not None}
    if include_snippets and hasattr(fragment, "text") and fragment.text:
        payload["snippet"] = fragment.text
    return payload


def _group_to_dict(
    group: Any,
    include_snippets: bool = False,
    *,
    compact: bool = False,
) -> dict[str, Any]:
    fragments = []
    for f in group.fragments:
        fragments.append(_fragment_to_dict(f, include_snippets, compact=compact))

    payload = {
        "id": group.id,
        "type": group.duplicate_type.value,
        "normalized_name": group.normalized_name,
        "similarity_score": round(group.similarity_score, 3),
        "total_lines": group.total_lines,
        "occurrences": group.occurrences,
        "saved_lines_potential": group.saved_lines_potential,
        "impact_score": round(group.impact_score, 1),
        "fragments": fragments,
    }
    if not compact:
        payload["normalized_hash"] = group.normalized_hash
    if group.metadata:
        if compact:
            for field in ("actionability", "provenance", "reason"):
                if group.metadata.get(field) is not None:
                    payload[field] = group.metadata[field]
            if group.metadata.get("model"):
                payload["engine"] = group.metadata["model"]
            semantic_evidence = group.metadata.get("semantic_evidence", {})
            if semantic_evidence:
                shared = semantic_evidence.get("shared", {})
                payload["evidence"] = {
                    "languages": semantic_evidence.get("languages", []),
                    "intent_similarity": semantic_evidence.get("intent_similarity"),
                    "shared": {
                        field: shared[field]
                        for field in ("purpose", "calls", "data", "operations")
                        if shared.get(field)
                    },
                }
        else:
            payload["metadata"] = group.metadata
    if group.duplicate_type == DuplicateType.INTENT:
        payload["engine"] = "intract"
    return payload


def _suggestion_to_dict(s: Any) -> dict[str, Any]:
    return {
        "group_id": s.group_id,
        "priority": s.priority,
        "action": s.action.value,
        "new_module": s.new_module,
        "function_name": s.function_name,
        "class_name": s.class_name,
        "original_files": s.original_files,
        "risk_level": s.risk_level.value,
        "rationale": s.rationale,
    }


def duplication_map_to_dict(
    dup_map: DuplicationMap,
    *,
    include_snippets: bool = False,
    group_scope: str = "all",
    max_groups: int | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    """Convert a DuplicationMap to a serializable dictionary.

    ``group_scope`` and ``max_groups`` let API clients bound large reports without
    changing the totals in ``summary``. The default remains the complete report for
    backwards compatibility with the CLI and Python API.
    """
    if group_scope not in _GROUP_SCOPES:
        choices = ", ".join(sorted(_GROUP_SCOPES))
        raise ValueError(f"Unsupported group scope '{group_scope}'; choose one of: {choices}")
    if max_groups is not None and max_groups < 0:
        raise ValueError("max_groups must be zero or greater")

    ranked_groups = dup_map.sorted_by_impact()
    if group_scope == "non_generated":
        matching_groups = [
            group for group in ranked_groups if group.metadata.get("actionability") != "generated"
        ]
    elif group_scope == "all":
        matching_groups = ranked_groups
    else:
        matching_groups = [
            group for group in ranked_groups if group.metadata.get("actionability") == group_scope
        ]

    selected_groups = matching_groups
    if max_groups:
        selected_groups = matching_groups[:max_groups]
    selected_ids = {group.id for group in selected_groups}

    payload = {
        "project_path": dup_map.project_path,
        "stats": {
            "files_scanned": dup_map.stats.files_scanned,
            "total_lines": dup_map.stats.total_lines,
            "total_blocks": dup_map.stats.total_blocks,
            "scan_time_ms": round(dup_map.stats.scan_time_ms, 1),
        },
        "summary": {
            "total_groups": dup_map.total_groups,
            "actionable_groups": dup_map.actionable_groups,
            "review_groups": dup_map.review_groups,
            "generated_groups": dup_map.generated_groups,
            "actionable_saved_lines": dup_map.saved_lines_for("refactor"),
            "review_saved_lines": dup_map.saved_lines_for("review"),
            "generated_saved_lines": dup_map.saved_lines_for("generated"),
            "total_fragments": dup_map.total_fragments,
            "total_saved_lines": dup_map.total_saved_lines,
        },
        "groups": [
            _group_to_dict(group, include_snippets, compact=compact) for group in selected_groups
        ],
        "refactor_suggestions": [
            (
                {
                    "group_id": suggestion.group_id,
                    "action": suggestion.action.value,
                    "risk_level": suggestion.risk_level.value,
                }
                if compact
                else _suggestion_to_dict(suggestion)
            )
            for suggestion in dup_map.suggestions
            if suggestion.group_id in selected_ids
        ],
    }
    if group_scope != "all" or max_groups is not None:
        payload["selection"] = {
            "group_scope": group_scope,
            "max_groups": max_groups,
            "matching_groups": len(matching_groups),
            "returned_groups": len(selected_groups),
            "omitted_groups": len(matching_groups) - len(selected_groups),
            "truncated": len(selected_groups) < len(matching_groups),
        }
    return payload


def to_json(
    dup_map: DuplicationMap,
    indent: int = 2,
    include_snippets: bool = False,
    *,
    group_scope: str = "all",
    max_groups: int | None = None,
    compact: bool = False,
) -> str:
    """Serialize a DuplicationMap to JSON string."""
    data = duplication_map_to_dict(
        dup_map,
        include_snippets=include_snippets,
        group_scope=group_scope,
        max_groups=max_groups,
        compact=compact,
    )
    return json.dumps(data, indent=indent, ensure_ascii=False)
