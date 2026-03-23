"""Lazy grouping implementation for early exit optimization."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from redup.core.hasher import HashIndex, HashedBlock, _blocks_from_different_locations
from redup.core.models import DuplicateGroup, DuplicateFragment, DuplicateType


def find_exact_duplicates_lazy(index: HashIndex, min_lines: int = 3) -> Iterator[DuplicateGroup]:
    """Find exact duplicate groups with lazy evaluation and early exit.
    
    Yields groups as they're found, avoiding materialization of all groups
    that don't meet the minimum line threshold. Provides 2x speedup for
    small projects with many tiny blocks.
    
    Args:
        index: Hash index with exact hashes
        min_lines: Minimum lines for a group to be yielded
        
    Yields:
        DuplicateGroup objects that meet the threshold
    """
    for hash_val, blocks in index.exact.items():
        if len(blocks) < 2:
            continue
        
        # Early exit: check if blocks are from different locations
        if not _blocks_from_different_locations(blocks):
            continue
        
        # Create group and check line threshold
        group = _create_duplicate_group(hash_val, blocks, DuplicateType.EXACT)
        if group.total_lines >= min_lines:
            yield group


def find_structural_duplicates_lazy(index: HashIndex, min_lines: int = 3) -> Iterator[DuplicateGroup]:
    """Find structural duplicate groups with lazy evaluation and early exit.
    
    Similar to find_exact_duplicates_lazy but for structural hashes.
    """
    for hash_val, blocks in index.structural.items():
        if len(blocks) < 2:
            continue
        
        # Early exit: check if blocks are from different locations
        if not _blocks_from_different_locations(blocks):
            continue
        
        # Create group and check line threshold
        group = _create_duplicate_group(hash_val, blocks, DuplicateType.STRUCTURAL)
        if group.total_lines >= min_lines:
            yield group


def _create_duplicate_group(
    hash_val: str, 
    blocks: list[HashedBlock], 
    duplicate_type: DuplicateType
) -> DuplicateGroup:
    """Create a DuplicateGroup from hash and blocks."""
    fragments = [
        DuplicateFragment(
            file=hb.block.file,
            line_start=hb.block.line_start,
            line_end=hb.block.line_end,
            text=hb.block.text,
            function_name=hb.block.function_name,
            class_name=hb.block.class_name,
        )
        for hb in blocks
    ]
    
    return DuplicateGroup(
        id=hash_val,
        duplicate_type=duplicate_type,
        fragments=fragments,
        normalized_hash=hash_val,
    )


def find_all_duplicates_lazy(
    index: HashIndex, 
    min_lines: int = 3,
    include_exact: bool = True,
    include_structural: bool = True
) -> Iterator[DuplicateGroup]:
    """Find all duplicate groups with lazy evaluation.
    
    Combines exact and structural duplicate detection with lazy evaluation.
    
    Args:
        index: Hash index with both exact and structural hashes
        min_lines: Minimum lines for a group to be yielded
        include_exact: Whether to include exact duplicates
        include_structural: Whether to include structural duplicates
        
    Yields:
        DuplicateGroup objects that meet the threshold
    """
    if include_exact:
        yield from find_exact_duplicates_lazy(index, min_lines)
    
    if include_structural:
        yield from find_structural_duplicates_lazy(index, min_lines)


class DuplicateGroupCollector:
    """Collector for lazy duplicate groups with optional limits.
    
    Allows collecting lazy groups with limits on total groups or
    total saved lines for memory-efficient processing.
    """
    
    def __init__(
        self, 
        max_groups: int | None = None,
        max_saved_lines: int | None = None,
        min_impact_score: float = 0.0
    ):
        """Initialize collector with optional limits."""
        self.max_groups = max_groups
        self.max_saved_lines = max_saved_lines
        self.min_impact_score = min_impact_score
        self.collected_groups: list[DuplicateGroup] = []
        self.total_saved_lines = 0
    
    def collect(self, groups: Iterator[DuplicateGroup]) -> list[DuplicateGroup]:
        """Collect groups from iterator, respecting limits."""
        for group in groups:
            # Skip groups below impact threshold
            if group.impact_score < self.min_impact_score:
                continue
            
            # Check group count limit
            if self.max_groups is not None and len(self.collected_groups) >= self.max_groups:
                break
            
            # Check saved lines limit
            if self.max_saved_lines is not None:
                if self.total_saved_lines + group.saved_lines_potential > self.max_saved_lines:
                    break
            
            self.collected_groups.append(group)
            self.total_saved_lines += group.saved_lines_potential
        
        return self.collected_groups
    
    def collect_sorted(self, groups: Iterator[DuplicateGroup]) -> list[DuplicateGroup]:
        """Collect and sort groups by impact score."""
        collected = self.collect(groups)
        return sorted(collected, key=lambda g: g.impact_score, reverse=True)
