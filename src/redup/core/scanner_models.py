"""Backward-compatible scanner model imports.

The canonical dataclasses live in :mod:`redup.core.scanner_types`. This module
keeps older imports working without duplicating the model definitions.
"""

from __future__ import annotations

from redup.core.scanner_types import CodeBlock, ScannedFile, ScanStrategy

__all__ = ["CodeBlock", "ScannedFile", "ScanStrategy"]
