"""JSON reporter — machine-readable duplication map."""

from __future__ import annotations

import json
from typing import Any

from redup.core.models import DuplicationMap


def _group_to_dict(group: Any, include_snippets: bool = False) -> dict:
    fragments = []
    for f in group.fragments:
        fragment_data = {
            "file": f.file,
            "line_start": f.line_start,
            "line_end": f.line_end,
            "function_name": f.function_name,
            "class_name": f.class_name,
        }
        
        # Include code snippet if requested
        if include_snippets and hasattr(f, 'text') and f.text:
            fragment_data["snippet"] = f.text
        
        fragments.append(fragment_data)
    
    return {
        "id": group.id,
        "type": group.duplicate_type.value,
        "normalized_name": group.normalized_name,
        "similarity_score": round(group.similarity_score, 3),
        "normalized_hash": group.normalized_hash,
        "total_lines": group.total_lines,
        "occurrences": group.occurrences,
        "saved_lines_potential": group.saved_lines_potential,
        "impact_score": round(group.impact_score, 1),
        "fragments": fragments,
    }


def _suggestion_to_dict(s: Any) -> dict:
    return {
        "group_id": s.group_id,
        "priority": s.priority,
        "action": s.action.value,
        "new_module": s.new_module,
        "function_name": s.function_name,
        "original_files": s.original_files,
        "risk_level": s.risk_level.value,
        "rationale": s.rationale,
    }


def to_json(dup_map: DuplicationMap, indent: int = 2, include_snippets: bool = False) -> str:
    """Serialize a DuplicationMap to JSON string."""
    data = {
        "project_path": dup_map.project_path,
        "stats": {
            "files_scanned": dup_map.stats.files_scanned,
            "total_lines": dup_map.stats.total_lines,
            "total_blocks": dup_map.stats.total_blocks,
            "scan_time_ms": round(dup_map.stats.scan_time_ms, 1),
        },
        "summary": {
            "total_groups": dup_map.total_groups,
            "total_fragments": dup_map.total_fragments,
            "total_saved_lines": dup_map.total_saved_lines,
        },
        "groups": [_group_to_dict(g, include_snippets) for g in dup_map.sorted_by_impact()],
        "refactor_suggestions": [_suggestion_to_dict(s) for s in dup_map.suggestions],
    }
    return json.dumps(data, indent=indent, ensure_ascii=False)
