"""Project scanner public API compatibility layer."""
from __future__ import annotations

from redup.core.scanner_cache import MemoryFileCache
from redup.core.scanner_filters import (
    _collect_files,
    _is_test_file,
    _project_relative_path,
    _should_exclude,
)
from redup.core.scanner_loader import _preload_files
from redup.core.scanner_types import CodeBlock, ScanStrategy, ScannedFile

__all__ = [
    'CodeBlock',
    'ScannedFile',
    'ScanStrategy',
    'MemoryFileCache',
    '_should_exclude',
    '_project_relative_path',
    '_collect_files',
    '_is_test_file',
    '_preload_files',
]
