"""Configuration management for reDUP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

from redup.core.models import ScanConfig


def _load_toml_file(file_path: Path) -> dict[str, Any]:
    """Load TOML file and return as dictionary."""
    if tomllib is None:
        return {}
    
    if not file_path.exists():
        return {}
    
    try:
        with open(file_path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _get_config_from_pyproject() -> dict[str, Any]:
    """Get reDUP configuration from pyproject.toml [tool.redup] section."""
    pyproject_path = Path.cwd() / "pyproject.toml"
    data = _load_toml_file(pyproject_path)
    return data.get("tool", {}).get("redup", {})


def _get_config_from_redup_toml() -> dict[str, Any]:
    """Get reDUP configuration from redup.toml file."""
    redup_toml_path = Path.cwd() / "redup.toml"
    return _load_toml_file(redup_toml_path)


def load_config() -> dict[str, Any]:
    """Load reDUP configuration from available sources.
    
    Priority order:
    1. Environment variables (REDUP_*)
    2. redup.toml in current directory
    3. [tool.redup] in pyproject.toml
    4. Defaults
    """
    config = {}
    
    # Load from redup.toml
    config.update(_get_config_from_redup_toml())
    
    # Load from pyproject.toml (overwrites redup.toml)
    config.update(_get_config_from_pyproject())
    
    # Override with environment variables
    env_mappings = {
        "REDUP_EXTENSIONS": ("extensions", str),
        "REDUP_MIN_LINES": ("min_lines", int),
        "REDUP_MIN_SIMILARITY": ("min_similarity", float),
        "REDUP_INCLUDE_TESTS": ("include_tests", bool),
        "REDUP_OUTPUT": ("output", str),
        "REDUP_FORMAT": ("format", str),
        "REDUP_MAX_GROUPS": ("max_groups", int),
        "REDUP_MAX_LINES": ("max_lines", int),
    }
    
    for env_var, (key, type_func) in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            try:
                if type_func == bool:
                    config[key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    config[key] = type_func(value)
            except (ValueError, TypeError):
                pass  # Ignore invalid environment variables
    
    return config


def config_to_scan_config(config: dict[str, Any], path: Path) -> ScanConfig:
    """Convert configuration dict to ScanConfig object."""
    extensions = config.get("extensions", ".py")
    if isinstance(extensions, str):
        ext_list = [e.strip() if e.startswith(".") else f".{e.strip()}" 
                   for e in extensions.split(",")]
    else:
        ext_list = extensions
    
    return ScanConfig(
        root=path,
        extensions=ext_list,
        min_block_lines=config.get("min_lines", 3),
        min_similarity=config.get("min_similarity", 0.85),
        include_tests=config.get("include_tests", False),
    )


def create_sample_redup_toml() -> str:
    """Create a sample redup.toml configuration file content."""
    return """# reDUP Configuration File
# See https://github.com/semcod/redup for documentation

[scan]
# File extensions to scan (comma-separated)
extensions = ".py,.js,.ts,.go,.rs,.java"
# Minimum block size in lines to consider as duplicate
min_lines = 3
# Minimum similarity score (0.0-1.0) for fuzzy matches
min_similarity = 0.85
# Include test files in analysis
include_tests = false

[check]
# CI gate thresholds
max_groups = 10
max_lines = 100

[output]
# Default output format
format = "toon"
# Default output directory (relative to project root)
output = "redup_output"

[reporting]
# Include code snippets in JSON output
include_snippets = false
# Generate suggestions for refactoring
generate_suggestions = true
"""
