"""reDUP — Code duplication analyzer and refactoring planner for LLMs."""

from __future__ import annotations

__version__ = "0.4.20"

# Click compatibility shim for older typer versions
# This must run before any typer imports
import click
if not hasattr(click.Choice, "__class_getitem__") or not callable(click.Choice.__class_getitem__):
    click.Choice.__class_getitem__ = classmethod(lambda cls, item: cls)

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
