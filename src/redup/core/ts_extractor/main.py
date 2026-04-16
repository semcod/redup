"""Main tree-sitter extraction API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tree_sitter
except ImportError:
    tree_sitter = None

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.config import LANGUAGE_MAPPING, language_registry


def _get_tree_sitter_language(language_name: str) -> Any:
    """Get tree-sitter language parser."""
    return language_registry.get_language(language_name)


def _get_dispatcher():
    """Lazy import dispatcher to avoid circular imports."""
    from redup.core.ts_extractor.dispatcher import (
        initialize_language_dispatcher,
        language_dispatcher,
    )
    # Initialize dispatcher on first use
    if not language_dispatcher._extractors:
        initialize_language_dispatcher()
    return language_dispatcher


def extract_functions_treesitter(source: str, file_path: str) -> list[CodeBlock]:
    """Extract functions using tree-sitter for multi-language support."""
    if tree_sitter is None:
        return []
    
    # Get initialized dispatcher (lazy import)
    dispatcher = _get_dispatcher()
    
    # Determine language from file extension
    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower()
    
    # Handle special cases (Dockerfile, Makefile)
    if not file_ext:
        file_name = file_path_obj.name
        if file_name in LANGUAGE_MAPPING:
            language_name = LANGUAGE_MAPPING[file_name]
        else:
            return []
    else:
        language_name = LANGUAGE_MAPPING.get(file_ext)
    
    if not language_name:
        return []
    
    # Skip Python - use existing AST extractor
    if language_name == "python":
        return []
    
    # Get language parser
    language = _get_tree_sitter_language(language_name)
    if language is None:
        return []
    
    # Parse the source code
    parser = tree_sitter.Parser(language)
    
    try:
        tree = parser.parse(bytes(source, "utf8"))
    except Exception:
        return []
    
    source_lines = source.splitlines()
    
    # Use dispatcher to extract functions
    return dispatcher.extract_functions(
        language_name, tree.root_node, source_lines, file_path
    )


def get_supported_languages() -> list[str]:
    """Get list of supported languages for tree-sitter extraction."""
    if tree_sitter is None:
        return []
    
    supported = []
    for ext, lang in LANGUAGE_MAPPING.items():
        if _get_tree_sitter_language(lang) is not None:
            supported.append(ext)
    
    return supported


def is_language_supported(file_path: str) -> bool:
    """Check if a file extension is supported by tree-sitter extraction."""
    file_path_obj = Path(file_path)
    file_ext = file_path_obj.suffix.lower()
    
    # Handle special cases
    if not file_ext:
        file_name = file_path_obj.name
        if file_name in LANGUAGE_MAPPING:
            language_name = LANGUAGE_MAPPING[file_name]
        else:
            return False
    else:
        language_name = LANGUAGE_MAPPING.get(file_ext)
    
    if not language_name or language_name == "python":
        return False
    
    return _get_tree_sitter_language(language_name) is not None
