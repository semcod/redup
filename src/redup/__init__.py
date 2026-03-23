"""reDUP — Code duplication analyzer and refactoring planner for LLMs."""

from __future__ import annotations

__version__ = "0.3.3"

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicationMap,
    RefactorSuggestion,
    ScanConfig,
)
from redup.core.pipeline import analyze
from redup.core.scanner import scan_project

__all__ = [
    "analyze",
    "scan_project",
    "DuplicateFragment",
    "DuplicateGroup",
    "DuplicationMap",
    "RefactorSuggestion",
    "ScanConfig",
]
