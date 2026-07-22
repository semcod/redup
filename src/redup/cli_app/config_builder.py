"""Configuration builders for reDUP CLI."""

from pathlib import Path
from typing import Any

from redup.core.config import config_to_scan_config, load_config
from redup.core.models import ScanConfig


def build_config(
    path: Path, extensions: str, min_lines: int, min_similarity: float, include_tests: bool
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
    functions_only: bool = False,
    fuzzy: bool = False,
    fuzzy_threshold: float = 0.8,
    semantic: bool | None = None,
    semantic_threshold: float = 0.80,
    semantic_model: str | None = None,
    intent: bool = False,
    intent_threshold: float = 0.84,
    intent_manifest: str | None = None,
    intent_fail_on: str | None = None,
    intent_warn_on: str | None = None,
    target_files: list[str] | None = None,
) -> ScanConfig:
    """Build scan configuration with advanced options."""
    config = load_config()
    scan_config = config_to_scan_config(config, path)

    # Override with CLI parameters if provided
    if extensions is not None:
        scan_config.extensions = [e.strip() for e in extensions.split(",")]
    if min_lines is not None:
        scan_config.min_block_lines = min_lines
    if min_similarity is not None:
        scan_config.min_similarity = min_similarity
    if include_tests is not None:
        scan_config.include_tests = include_tests
    if functions_only:
        scan_config.functions_only = functions_only

    # Performance and caching
    scan_config._parallel_enabled = parallel
    if max_workers is not None:
        scan_config.parallel_workers = max_workers
    elif parallel:
        scan_config.parallel_workers = None
    scan_config.enable_cache = incremental
    scan_config._memory_cache = memory_cache
    scan_config._max_cache_mb = max_cache_mb

    # Optional targeted scan (e.g. changed-only mode)
    if target_files is not None:
        scan_config.target_files = target_files

    # Add fuzzy support
    scan_config.fuzzy_enabled = fuzzy
    scan_config.fuzzy_threshold = fuzzy_threshold

    if semantic is not None:
        scan_config.semantic_enabled = semantic
    scan_config.semantic_threshold = semantic_threshold
    if semantic_model:
        scan_config.semantic_model = semantic_model

    scan_config.intent_enabled = intent
    scan_config.intent_threshold = intent_threshold
    if intent_manifest:
        scan_config.intent_manifest_path = Path(intent_manifest)
    if intent_fail_on:
        scan_config.intent_fail_on = intent_fail_on
    if intent_warn_on:
        scan_config.intent_warn_on = intent_warn_on

    return scan_config
