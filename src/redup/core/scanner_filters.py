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


def _collect_target_files(config: ScanConfig) -> list[Path]:
    """Collect an explicit target file list without walking the whole tree."""
    if not config.target_files:
        return []

    files: list[Path] = []
    seen: set[Path] = set()
    ext_set = set(config.extensions)
    exclude_patterns = tuple(config.exclude_patterns)

    for target in config.target_files:
        relative_path = Path(str(target)).as_posix().lstrip("./")
        file_path = (config.root / relative_path).resolve()
        try:
            project_relative = _project_relative_path(file_path, config.root)
        except ValueError:
            continue

        relative_posix = project_relative.as_posix().lstrip("./")
        if relative_posix != relative_path:
            continue
        if file_path in seen or not file_path.is_file():
            continue
        if file_path.suffix not in ext_set:
            continue
        if _should_exclude(project_relative, exclude_patterns):
            continue
        if not config.include_tests and _is_test_file(project_relative):
            continue
        try:
            if file_path.stat().st_size > config.max_file_size_kb * 1024:
                continue
        except OSError:
            continue
        seen.add(file_path)
        files.append(file_path)

    return files


def _collect_files(config: ScanConfig) -> list[Path]:
    """Collect all files to scan based on configuration.

    Uses os.walk with topdown pruning to skip hidden and excluded
    directories early, avoiding descent into .rebuild_ev/, venv/,
    node_modules/, site-packages/, etc. Without this, a populated
    virtualenv (tens of thousands of files) gets fully walked and
    stat'd before its files are filtered out, making every scan of a
    repo root dramatically slower than scanning a subdirectory.
    """
    if config.target_files is not None:
        return _collect_target_files(config)

    files = []
    ext_set = set(config.extensions)
    exclude_patterns = tuple(config.exclude_patterns)
    root_str = str(config.root)

    for dirpath, dirnames, filenames in os.walk(root_str, topdown=True):
        kept = []
        for d in dirnames:
            if d.startswith("."):
                continue
            relative_dir = _project_relative_path(Path(os.path.join(dirpath, d)), config.root)
            if _should_exclude(relative_dir, exclude_patterns):
                continue
            kept.append(d)
        dirnames[:] = kept

        for filename in filenames:
            file_path = Path(os.path.join(dirpath, filename))
            if file_path.suffix not in ext_set:
                continue
            relative_path = _project_relative_path(file_path, config.root)
            relative_posix = relative_path.as_posix().lstrip("./")
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
