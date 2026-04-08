"""Hashing layer — fingerprint code blocks for duplicate detection."""

from __future__ import annotations

import ast
import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    import xxhash
except ImportError:
    xxhash = None

from redup.core.scanner import CodeBlock


def _fast_hash(data: bytes) -> str:
    """Return a short stable hash string for the given bytes."""
    if xxhash is not None:
        return xxhash.xxh64(data).hexdigest()[:16]
    return hashlib.sha256(data).hexdigest()[:16]


_normalize_cache: dict[str, str] = {}
_MAX_CACHE_SIZE = 10_000
_COMMENT_RE = re.compile(r"#.*$")
_MULTILINE_STRING_RE = re.compile(r'^\s*("""|\'\'\')')


def _normalize_text(text: str) -> str:
    """Normalize code text for comparison."""
    cached = _normalize_cache.get(text)
    if cached is not None:
        return cached

    result_lines: list[str] = []
    for line in text.splitlines():
        if _MULTILINE_STRING_RE.match(line):
            continue
        cleaned = _COMMENT_RE.sub("", line).strip()
        if cleaned:
            result_lines.append(cleaned)

    result = "\n".join(result_lines)
    if len(_normalize_cache) >= _MAX_CACHE_SIZE:
        _normalize_cache.pop(next(iter(_normalize_cache)))
    _normalize_cache[text] = result
    return result


def _ast_to_normalized_string(tree: object) -> str:
    """Convert an AST to a coarse structural fingerprint."""
    import ast as _ast

    tokens: list[str] = []
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Load, _ast.Store, _ast.Del, _ast.Param)):
            continue
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            token = "FUNC"
        elif isinstance(node, _ast.ClassDef):
            token = "CLASS"
        elif isinstance(node, _ast.Name):
            token = "IDENT"
        elif isinstance(node, _ast.arg):
            token = "ARG"
        elif isinstance(node, _ast.Attribute):
            token = "ATTR"
        elif isinstance(node, _ast.Constant):
            token = f"CONST_{type(node.value).__name__}"
        elif isinstance(node, _ast.BinOp):
            token = f"BINOP_{type(node.op).__name__}"
        elif isinstance(node, _ast.Compare):
            token = "CMP_" + "_".join(type(op).__name__ for op in node.ops)
        else:
            token = type(node).__name__.upper()
        tokens.append(token)

    return " ".join(tokens)


def _normalize_ast_text(text: str) -> str:
    """Deeper normalization: replace variable names and literals with placeholders."""
    cache_key = f"ast:{text}"
    cached = _normalize_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        tree = ast.parse(text)
    except SyntaxError:
        result = _normalize_text(text)
        result = re.sub(r'"[^"]*"', '"__STR__"', result)
        result = re.sub(r"'[^']*'", "'__STR__'", result)
        result = re.sub(r'\b\d+\.?\d*\b', "__NUM__", result)
    else:
        result = _ast_to_normalized_string(tree)

    if len(_normalize_cache) >= _MAX_CACHE_SIZE:
        _normalize_cache.pop(next(iter(_normalize_cache)))
    _normalize_cache[cache_key] = result
    return result


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


def _hashed_block(block: CodeBlock) -> HashedBlock:
    return HashedBlock(
        block=block,
        exact_hash=hash_block(block.text),
        structural_hash=hash_block_structural(block.text),
    )


def _blocks_from_different_locations(blocks: list[HashedBlock]) -> bool:
    """Check that at least two blocks are from different file:line locations."""
    locations = {(b.block.file, b.block.line_start) for b in blocks}
    return len(locations) > 1


def _find_duplicates(hash_dict: dict[str, list[HashedBlock]]) -> dict[str, list[HashedBlock]]:
    """Generic duplicate finder for any hash dictionary."""
    return {
        hash_value: blocks
        for hash_value, blocks in hash_dict.items()
        if len(blocks) > 1 and _blocks_from_different_locations(blocks)
    }


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


def find_exact_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    """Find groups of blocks with identical normalized text."""
    return _find_duplicates(index.exact)


def find_structural_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:
    """Find groups of blocks with identical structure (names may differ)."""
    return _find_duplicates(index.structural)


__all__ = [
    "HashedBlock",
    "HashIndex",
    "build_hash_index",
    "find_exact_duplicates",
    "find_structural_duplicates",
    "hash_block",
    "hash_block_structural",
    "_normalize_text",
    "_normalize_ast_text",
    "_hash_text",
    "_blocks_from_different_locations",
    "_find_duplicates",
]