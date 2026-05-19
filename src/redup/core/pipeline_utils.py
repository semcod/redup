"""Backward-compatible pipeline utility imports."""

from __future__ import annotations

from redup.core.pipeline.groups import blocks_to_group, deduplicate_groups

__all__ = ["blocks_to_group", "deduplicate_groups"]
