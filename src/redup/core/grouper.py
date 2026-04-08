"""Compatibility wrapper for duplicate grouping helpers."""

from __future__ import annotations

from redup.core.lazy_grouper import DuplicateGroupCollector, find_all_duplicates_lazy
from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType, DuplicationMap

__all__ = [
    "DuplicateFragment",
    "DuplicateGroup",
    "DuplicateType",
    "DuplicationMap",
    "find_all_duplicates_lazy",
    "DuplicateGroupCollector",
]