from enum import Enum
from pathlib import Path
from typing import Any

def json_safe(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if isinstance(value, dict): return {str(json_safe(k)): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)): return [json_safe(i) for i in value]
    return value

def resolve_path(raw: Any) -> Path:
    if raw is None: raise ValueError("Path is required")
    path = Path(str(raw)).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()

def parse_extensions(value: Any) -> list[str] | None:
    if value is None: return None
    parts = value.split(",") if isinstance(value, str) else list(value)
    exts = [str(p).strip() for p in parts if str(p).strip()]
    return [e if e.startswith(".") else f".{e}" for e in exts] or None