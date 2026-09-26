"""Exact and structural duplicate collision indexer.

Provides collision mapping and location de-duplication for hashed code blocks.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from redup.core.scanner_types import CodeBlock


@dataclass
class HashedBlock:
    """A code block with its computed fingerprints."""

    block: CodeBlock
    exact_hash: str = ""
    structural_hash: str = ""


@dataclass
class HashIndex:
    """Index mapping hashes to blocks for fast lookup."""

    exact: dict[str, list[HashedBlock]] = field(default_factory=lambda: defaultdict(list))
    structural: dict[str, list[HashedBlock]] = field(default_factory=lambda: defaultdict(list))


def blocks_from_different_locations(blocks: Sequence[HashedBlock]) -> bool:
    """Check that at least two blocks are from different file:line locations."""
    locations = {(b.block.file, b.block.line_start) for b in blocks}
    return len(locations) > 1


def find_duplicates(
    hash_dict: dict[str, list[HashedBlock]]
) -> dict[str, list[HashedBlock]]:
    """Generic duplicate finder for any hash dictionary."""
    return {
        hash_value: blocks
        for hash_value, blocks in hash_dict.items()
        if len(blocks) > 1 and blocks_from_different_locations(blocks)
    }


def find_exact_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    """Find groups of blocks with identical normalized text."""
    return find_duplicates(index.exact)


def find_structural_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    """Find groups of blocks with identical structure (names may differ)."""
    return find_duplicates(index.structural)


# Backward compatibility aliases
_blocks_from_different_locations = blocks_from_different_locations
_find_duplicates = find_duplicates

__all__ = [
    "HashedBlock",
    "HashIndex",
    "blocks_from_different_locations",
    "find_duplicates",
    "find_exact_duplicates",
    "find_structural_duplicates",
    "_blocks_from_different_locations",
    "_find_duplicates",
]
