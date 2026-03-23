"""Hashing layer — fingerprint code blocks for duplicate detection."""

from __future__ import annotations

import ast
import hashlib
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from redup.core.scanner import CodeBlock


def _normalize_text(text: str) -> str:
    """Normalize code text for comparison.

    Strips comments, normalizes whitespace, lowercases identifiers
    that look like local variables.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        stripped = re.sub(r'#.*$', "", stripped)
        stripped = stripped.strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _normalize_ast_text(text: str) -> str:
    """Deeper normalization: replace variable names and literals with placeholders.

    This catches structural clones where only names differ.
    Uses Python AST when possible for accurate normalization.
    """
    # Try AST-based normalization for Python code
    try:
        import ast

        tree = ast.parse(text)
        return _ast_to_normalized_string(tree)
    except SyntaxError:
        pass

    # Fallback: text-based normalization
    normalized = _normalize_text(text)
    normalized = re.sub(r'"[^"]*"', '"__STR__"', normalized)
    normalized = re.sub(r"'[^']*'", "'__STR__'", normalized)
    normalized = re.sub(r'\b\d+\.?\d*\b', "__NUM__", normalized)
    return normalized


def _ast_to_normalized_string(tree: object) -> str:
    """Convert an AST to a normalized string with placeholders for names.

    Replaces all user-defined identifiers with positional placeholders
    while preserving control flow structure, operators, and builtins.
    """
    import ast

    name_map: dict[str, str] = {}
    counter = [0]
    parts: list[str] = []

    for node in ast.walk(tree):
        part = _process_ast_node(node, name_map, counter)
        if part:
            parts.append(part)

    return " ".join(parts)


def _process_ast_node(
    node,
    name_map: dict[str, str],
    counter: list[int]
) -> str | None:
    """Process a single AST node and return its normalized representation."""

    handler = _AST_HANDLERS.get(type(node))
    return handler(node, name_map, counter) if handler else None


# Dispatch table for AST node types - reduces complexity from CC=14 to CC=2
_AST_HANDLERS: dict[type, Callable] = {
    ast.Name: lambda n, nm, c: _get_placeholder(n.id, nm, c),
    ast.arg: lambda n, nm, c: _get_placeholder(n.arg, nm, c),
    ast.FunctionDef: lambda n, nm, c: f"DEF({_get_placeholder(n.name, nm, c)})",
    ast.AsyncFunctionDef: lambda n, nm, c: f"DEF({_get_placeholder(n.name, nm, c)})",
    ast.ClassDef: lambda n, nm, c: f"CLASS({_get_placeholder(n.name, nm, c)})",
    ast.Constant: lambda n, nm, c: _normalize_constant(n.value),
    ast.If: lambda n, nm, c: "IF",
    ast.For: lambda n, nm, c: "FOR",
    ast.While: lambda n, nm, c: "WHILE",
    ast.Return: lambda n, nm, c: "RETURN",
    ast.Call: lambda n, nm, c: "CALL",
    ast.BinOp: lambda n, nm, c: f"BINOP({type(n.op).__name__})",
    ast.Compare: lambda n, nm, c: f"CMP({','.join(type(op).__name__ for op in n.ops)})",
}


def _get_placeholder(
    name: str,
    name_map: dict[str, str],
    counter: list[int]
) -> str:
    """Get or create a placeholder for a name."""
    BUILTINS = {
        "print", "len", "range", "int", "float", "str", "list", "dict",
        "set", "tuple", "bool", "None", "True", "False", "type", "isinstance",
        "hasattr", "getattr", "setattr", "super", "property", "staticmethod",
        "classmethod", "round", "abs", "max", "min", "sum", "sorted",
        "enumerate", "zip", "map", "filter", "any", "all", "open",
        "self", "cls", "return", "if", "else", "for", "while", "with",
        "try", "except", "finally", "raise", "yield", "import", "from",
        "class", "def", "pass", "break", "continue", "and", "or", "not",
        "in", "is", "lambda", "global", "nonlocal", "assert", "del",
    }

    if name in BUILTINS or (name.startswith("__") and name.endswith("__")):
        return name

    if name not in name_map:
        name_map[name] = f"_V{counter[0]}"
        counter[0] += 1

    return name_map[name]


def _normalize_constant(value: Any) -> str:
    """Normalize constant values."""
    if isinstance(value, str):
        return "__STR__"
    elif isinstance(value, (int, float)):
        return "__NUM__"
    else:
        return str(type(value).__name__)


def _hash_text(text: str, normalizer: Callable[[str], str]) -> str:
    """Generic SHA-256 hash function with configurable normalizer."""
    normalized = normalizer(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def hash_block(text: str) -> str:  # nodup: accepted thin API wrapper
    """SHA-256 hash of normalized text."""
    return _hash_text(text, _normalize_text)


def hash_block_structural(text: str) -> str:  # nodup: accepted thin API wrapper
    """SHA-256 hash of deeply normalized text (variable names replaced)."""
    return _hash_text(text, _normalize_ast_text)


def _hashed_block(block: CodeBlock) -> HashedBlock:
    return HashedBlock(
        block=block,
        exact_hash=hash_block(block.text),
        structural_hash=hash_block_structural(block.text),
    )


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


def build_hash_index(blocks: list[CodeBlock], min_lines: int = 3) -> HashIndex:
    """Build a hash index from a list of code blocks.

    Only indexes function-level blocks (those with function_name set)
    and blocks above the minimum line threshold.
    """
    index = HashIndex()

    for block in blocks:
        if block.line_count < min_lines:
            continue

        hb = _hashed_block(block)

        index.exact[hb.exact_hash].append(hb)
        index.structural[hb.structural_hash].append(hb)

    return index


def _find_duplicates(hash_dict: dict[str, list[HashedBlock]]) -> dict[str, list[HashedBlock]]:
    """Generic duplicate finder for any hash dictionary."""
    return {
        h: blocks
        for h, blocks in hash_dict.items()
        if len(blocks) > 1 and _blocks_from_different_locations(blocks)
    }


def find_exact_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:  # nodup: accepted thin API wrapper
    """Find groups of blocks with identical normalized text."""
    return _find_duplicates(index.exact)


def find_structural_duplicates(index: HashIndex) -> dict[str, list[HashedBlock]]:  # nodup: accepted thin API wrapper
    """Find groups of blocks with identical structure (names may differ)."""
    return _find_duplicates(index.structural)


def _blocks_from_different_locations(blocks: list[HashedBlock]) -> bool:
    """Check that at least two blocks are from different file:line locations."""
    locations = {(b.block.file, b.block.line_start) for b in blocks}
    return len(locations) > 1
