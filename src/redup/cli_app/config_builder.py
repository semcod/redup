"""Configuration builders for reDUP CLI."""

from pathlib import Path
from typing import Any

from redup.core.config import config_to_scan_config, load_config
from redup.core.models import ScanConfig


def build_config(
    path: Path,
    extensions: str,
    min_lines: int,
    min_similarity: float,
    include_tests: bool
) -> ScanConfig:
    """Build basic scan configuration."""
    config = load_config()
    return config_to_scan_config(config, path)


def build_config_with_file_support(
    path: Path,
    extensions: Any,
    min_lines: Any,
    min_similarity: Any,
    include_tests: Any,
    parallel: bool = False,
    max_workers: Any = None,
    incremental: bool = False,
    memory_cache: bool = False,
    max_cache_mb: int = 512,
    functions_only: bool = False
) -> ScanConfig:
    """Build scan configuration with advanced options."""
    config = load_config()
    scan_config = config_to_scan_config(config, path)
    
    # Override with CLI parameters if provided
    if extensions is not None:
        scan_config.extensions = [e.strip() for e in extensions.split(',')]
    if min_lines is not None:
        scan_config.min_lines = min_lines
    if min_similarity is not None:
        scan_config.min_similarity = min_similarity
    if include_tests is not None:
        scan_config.include_tests = include_tests
    if functions_only:
        scan_config.function_level_only = functions_only
    
    return scan_config
