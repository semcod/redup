"""File loading and preload helpers for scanner operations."""
from __future__ import annotations

# Re-export _preload_files from scanner_utils to avoid duplication
from redup.core.scanner_utils import _preload_files

__all__ = ["_preload_files"]
