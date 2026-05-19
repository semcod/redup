"""Path and file selection helpers for the scanner."""

from __future__ import annotations

import os
from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.scanner_cache import _should_exclude


def _project_relative_path(file_path: Path, project_root: Path) -> Path:
    """Return a path relative to the project root when possible."""
    try:
        return file_path.relative_to(project_root)
    except ValueError:
        return file_path


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    name = path.name.lower()
    dir_parts = [part.lower() for part in path.parts]
    if any("pytest-" in part for part in dir_parts):
        return False
    test_patterns = ["test_", "_test.", "tests.", "spec_", "_spec."]
    if any(pattern in name for pattern in test_patterns):
        return True
    return any("test" in part and "pytest-" not in part for part in dir_parts)


def _collect_files(config: ScanConfig) -> list[Path]:
    """Collect all files to scan based on configuration.

    Uses os.walk with topdown pruning to skip hidden directories early,
    avoiding descent into .rebuild_ev/, .regres/, etc.
    """
    files = []
    ext_set = set(config.extensions)
    exclude_patterns = tuple(config.exclude_patterns)
    root_str = str(config.root)

    for dirpath, dirnames, filenames in os.walk(root_str, topdown=True):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        for filename in filenames:
            file_path = Path(os.path.join(dirpath, filename))
            if file_path.suffix not in ext_set:
                continue
            relative_path = _project_relative_path(file_path, config.root)
            if _should_exclude(relative_path, exclude_patterns):
                continue
            if not config.include_tests and _is_test_file(relative_path):
                continue
            try:
                if file_path.stat().st_size > config.max_file_size_kb * 1024:
                    continue
            except OSError:
                continue
            files.append(file_path)
    return files
