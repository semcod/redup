"""YAML reporter — human-readable duplication map."""

from __future__ import annotations

from redup.core.models import DuplicationMap


def to_yaml(dup_map: DuplicationMap) -> str:
    """Serialize a DuplicationMap to YAML string."""
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml is required for YAML output: pip install pyyaml") from None

    from redup.reporters.json_reporter import duplication_map_to_dict

    data = duplication_map_to_dict(dup_map)
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
