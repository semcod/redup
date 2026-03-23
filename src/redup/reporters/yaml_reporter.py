"""YAML reporter — human-readable duplication map."""

from __future__ import annotations

from redup.core.models import DuplicationMap


def to_yaml(dup_map: DuplicationMap) -> str:
    """Serialize a DuplicationMap to YAML string."""
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml is required for YAML output: pip install pyyaml") from None

    from redup.reporters.json_reporter import _group_to_dict, _suggestion_to_dict

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
        "groups": [_group_to_dict(g) for g in dup_map.sorted_by_impact()],
        "refactor_suggestions": [_suggestion_to_dict(s) for s in dup_map.suggestions],
    }

    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
