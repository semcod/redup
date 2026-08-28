from enum import Enum
from pathlib import Path
from typing import Any

from redup.core.config import normalize_extensions


def json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(json_safe(k)): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(i) for i in value]
    return value


def resolve_path(raw: Any) -> Path:
    if raw is None:
        raise ValueError("Path is required")
    path = Path(str(raw)).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


def parse_extensions(value: Any) -> list[str] | None:
    """Backward-compatible MCP alias for the shared extension normalizer."""
    return normalize_extensions(value)
