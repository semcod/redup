from pathlib import Path
from typing import Any

from redup.core.models import ScanConfig
from redup.core.pipeline import analyze, analyze_optimized, analyze_parallel
from redup.core.config import config_to_scan_config, load_config

def _parse_extensions(ext_string: str | None) -> list[str] | None:
    """Parse comma-separated extension string into list."""
    if ext_string is None:
        return None
    return [e.strip() for e in ext_string.split(",") if e.strip()]

def _build_scan_config(path: Path, params: dict[str, Any]) -> ScanConfig:
    scan_config = config_to_scan_config(load_config(), path)

    extensions = _parse_extensions(params.get("extensions"))
    if extensions is not None:
        scan_config.extensions = extensions

    if params.get("min_lines") is not None:
        scan_config.min_lines = int(params["min_lines"])

    # other parameters...

    return scan_config