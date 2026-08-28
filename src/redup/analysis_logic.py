from pathlib import Path
from typing import Any

from redup.core.config import config_to_scan_config, load_config, normalize_extensions
from redup.core.models import ScanConfig


def _build_scan_config(path: Path, params: dict[str, Any]) -> ScanConfig:
    scan_config = config_to_scan_config(load_config(path), path)

    extensions = normalize_extensions(params.get("extensions"))
    if extensions is not None:
        scan_config.extensions = extensions

    if params.get("min_lines") is not None:
        scan_config.min_block_lines = int(params["min_lines"])

    # other parameters...

    return scan_config
