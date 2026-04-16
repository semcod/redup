"""Path and file selection helpers for the scanner."""
from __future__ import annotations

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
    if any(('pytest-' in part for part in dir_parts)):
        return False
    test_patterns = ['test_', '_test.', 'tests.', 'spec_', '_spec.']
    if any((pattern in name for pattern in test_patterns)):
        return True
    if any(('test' in part and 'pytest-' not in part for part in dir_parts)):
        return True
    return False


def _collect_files(config: ScanConfig) -> list[Path]:
    """Collect all files to scan based on configuration."""
    files = []
    for file_path in config.root.rglob('*'):
        if file_path.is_file():
            relative_path = _project_relative_path(file_path, config.root)
            if file_path.suffix not in config.extensions:
                continue
            if _should_exclude(relative_path, tuple(config.exclude_patterns)):
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
