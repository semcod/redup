"""Hashing layer — fingerprint code blocks for duplicate detection.

This module acts as a unified facade coordinating text normalization,
AST structural normalization, and collision indexing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable

try:
    import xxhash
except ImportError:
    xxhash = None

from redup.core.ast_normalizer import (
    _ast_to_normalized_string,
    _normalize_ast_text,
    ast_to_normalized_string,
    normalize_ast_text,
)
from redup.core.exact_matcher import (
    HashedBlock,
    HashIndex,
    _blocks_from_different_locations,
    _find_duplicates,
    blocks_from_different_locations,
    find_duplicates,
    find_exact_duplicates,
    find_structural_duplicates,
)
from redup.core.scanner_types import CodeBlock
from redup.core.tokens_hasher import (
    _MAX_CACHE_SIZE,
    _normalize_cache,
    normalize_text,
)
from redup.core.tokens_hasher import (
    normalize_text as _normalize_text,
)


def _fast_hash(data: bytes) -> str:
    """Return a short stable hash string for the given bytes."""
    if xxhash is not None:
        return xxhash.xxh64(data).hexdigest()[:16]
    return hashlib.sha256(data).hexdigest()[:16]


def _hash_text(text: str, normalizer: Callable[[str], str]) -> str:
    """Hash normalized text using the configured normalizer."""
    normalized = normalizer(text)
    return _fast_hash(normalized.encode("utf-8"))


def hash_block(text: str) -> str:
    """SHA-256-compatible hash of normalized text."""
    return _hash_text(text, _normalize_text)


def hash_block_structural(text: str) -> str:
    """Hash of deeply normalized text (variable names replaced)."""
    return _hash_text(text, _normalize_ast_text)


def _hashed_block(block: CodeBlock) -> HashedBlock:
    return HashedBlock(
        block=block,
        exact_hash=hash_block(block.text),
        structural_hash=hash_block_structural(block.text),
    )


def build_hash_index(blocks: list[CodeBlock], min_lines: int = 3) -> HashIndex:
    """Build a hash index from a list of code blocks."""
    index = HashIndex()

    for block in blocks:
        if block.line_count < min_lines:
            continue

        hashed_block = _hashed_block(block)
        index.exact[hashed_block.exact_hash].append(hashed_block)
        index.structural[hashed_block.structural_hash].append(hashed_block)

    return index


__all__ = [
    "HashedBlock",
    "HashIndex",
    "build_hash_index",
    "find_exact_duplicates",
    "find_structural_duplicates",
    "hash_block",
    "hash_block_structural",
    "normalize_text",
    "normalize_ast_text",
    "ast_to_normalized_string",
    "blocks_from_different_locations",
    "find_duplicates",
    "_normalize_text",
    "_normalize_ast_text",
    "_ast_to_normalized_string",
    "_hash_text",
    "_blocks_from_different_locations",
    "_find_duplicates",
    "_MAX_CACHE_SIZE",
    "_normalize_cache",
]
