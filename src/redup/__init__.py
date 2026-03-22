"""reDUP — Code duplication analyzer and refactoring planner for LLMs."""

from __future__ import annotations

__version__ = "0.1.1"

from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicationMap,
    RefactorSuggestion,
    ScanConfig,
)
from redup.core.scanner import scan_project
from redup.core.pipeline import analyze

__all__ = [
    "analyze",
    "scan_project",
    "DuplicateFragment",
    "DuplicateGroup",
    "DuplicationMap",
    "RefactorSuggestion",
    "ScanConfig",
]
