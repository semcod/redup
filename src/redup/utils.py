import json
import platform
import sys
from enum import Enum
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from redup import __version__

def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(_json_safe(key)): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in value]
    return value

def _resolve_path(raw: Any) -> Path:
    if raw is None:
        raise ValueError("Path is required")
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()

def _parse_extensions(value: Any) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.split(",")
    else:
        parts = list(value)
    extensions = []
    for part in parts:
        ext = str(part).strip()
        if not ext:
            continue
        extensions.append(ext if ext.startswith(".") else f".{ext}")
    return extensions or None