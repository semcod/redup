"""Tree-sitter multi-language extraction package."""

from __future__ import annotations

# Main API functions
from redup.core.ts_extractor.main import (
    extract_functions_treesitter,
    get_supported_languages,
    is_language_supported,
)

# Configuration and registry
from redup.core.ts_extractor.config import LANGUAGE_MAPPING, language_registry

# Internal extractor functions (needed by tests) - exported with underscore prefix
from redup.core.ts_extractor.extractors.markup import extract_blocks_html_xml as _extract_blocks_html_xml
from redup.core.ts_extractor.extractors.stylesheet import extract_blocks_css as _extract_blocks_css
from redup.core.ts_extractor.extractors.query import extract_blocks_sql as _extract_blocks_sql
from redup.core.ts_extractor.extractors.c_family import extract_functions_c_cpp as _extract_functions_c_cpp
from redup.core.ts_extractor.extractors.shell import extract_functions_bash as _extract_functions_bash

# Backward compatibility aliases
_LANGUAGE_MAPPING = LANGUAGE_MAPPING
_language_registry = language_registry
_extract_functions_lua = _extract_functions_bash  # Alias for test compatibility

__all__ = [
    # Main API
    "extract_functions_treesitter",
    "get_supported_languages",
    "is_language_supported",
    # Config
    "LANGUAGE_MAPPING",
    "_LANGUAGE_MAPPING",
    "language_registry",
    "_language_registry",
    # Internal extractors (for tests)
    "_extract_blocks_html_xml",
    "_extract_blocks_css",
    "_extract_blocks_sql",
    "_extract_functions_c_cpp",
    "_extract_functions_lua",
]
