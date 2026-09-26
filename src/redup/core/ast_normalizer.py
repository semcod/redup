"""AST structural normalizer for structural duplicate detection.

Converts Python AST or code text into coarse structural token streams
invariant to variable and argument names.
"""

from __future__ import annotations

import ast
import re

from redup.core.tokens_hasher import (
    _MAX_CACHE_SIZE,
    _normalize_cache,
    normalize_text,
)


def ast_to_normalized_string(tree: object) -> str:
    """Convert an AST to a coarse structural fingerprint."""
    tokens: list[str] = []
    for node in ast.walk(tree):  # type: ignore[arg-type]
        if isinstance(node, (ast.Load, ast.Store, ast.Del, ast.Param)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            token = "FUNC"
        elif isinstance(node, ast.ClassDef):
            token = "CLASS"
        elif isinstance(node, ast.Name):
            token = "IDENT"
        elif isinstance(node, ast.arg):
            token = "ARG"
        elif isinstance(node, ast.Attribute):
            token = "ATTR"
        elif isinstance(node, ast.Constant):
            token = "CONST"
        elif isinstance(node, ast.BinOp):
            token = f"BINOP_{type(node.op).__name__}"
        elif isinstance(node, ast.Compare):
            token = "CMP_" + "_".join(type(op).__name__ for op in node.ops)
        else:
            token = type(node).__name__.upper()
        tokens.append(token)

    return " ".join(tokens)


def normalize_ast_text(text: str) -> str:
    """Deeper normalization: replace variable names and literals with structural placeholders."""
    cache_key = f"ast:{text}"
    cached = _normalize_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        tree = ast.parse(text)
    except SyntaxError:
        result = normalize_text(text)
        result = re.sub(r'"[^"]*"', '"__STR__"', result)
        result = re.sub(r"'[^']*'", "'__STR__'", result)
        result = re.sub(r"\b\d+\.?\d*\b", "__NUM__", result)
    else:
        result = ast_to_normalized_string(tree)

    if len(_normalize_cache) >= _MAX_CACHE_SIZE:
        _normalize_cache.pop(next(iter(_normalize_cache)))
    _normalize_cache[cache_key] = result
    return result


# Backward compatibility aliases
_ast_to_normalized_string = ast_to_normalized_string
_normalize_ast_text = normalize_ast_text

__all__ = [
    "ast_to_normalized_string",
    "normalize_ast_text",
    "_ast_to_normalized_string",
    "_normalize_ast_text",
]
