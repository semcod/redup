"""Tree-sitter multi-language extraction package."""

# Re-export from ts_extractor.py module (which provides the actual implementations)
import sys
from pathlib import Path

# Add parent directory to path temporarily to import the .py module
_ts_extractor_py = Path(__file__).parent.parent / "ts_extractor.py"
if _ts_extractor_py.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_ts_extractor_module", _ts_extractor_py)
    _ts_module = importlib.util.module_from_spec(spec)
    sys.modules["_ts_extractor_module"] = _ts_module
    spec.loader.exec_module(_ts_module)
    
    # Export main functions
    extract_functions_treesitter = _ts_module.extract_functions_treesitter
    get_supported_languages = _ts_module.get_supported_languages
    is_language_supported = _ts_module.is_language_supported
    
    # Export language mapping with underscore aliases for backward compatibility
    _LANGUAGE_MAPPING = _ts_module._LANGUAGE_MAPPING
    LANGUAGE_MAPPING = _ts_module._LANGUAGE_MAPPING
    
    # Internal extractor functions (needed by tests)
    _extract_blocks_html_xml = _ts_module._extract_blocks_html_xml
    _extract_blocks_css = _ts_module._extract_blocks_css
    _extract_blocks_sql = _ts_module._extract_blocks_sql
    _extract_functions_c_cpp = _ts_module._extract_functions_c_cpp
    _extract_functions_lua = _ts_module._extract_functions_lua
    
    # Registry wrapper for backward compatibility
    class _RegistryWrapper:
        """Wrapper that provides _languages attribute for test compatibility.
        
        Combines both direct extractors and languages from groups.
        """
        def __init__(self, dispatcher):
            self._dispatcher = dispatcher
            # Build combined language mapping from extractors and groups
            self._languages = self._build_languages_dict()
        
        def _build_languages_dict(self):
            """Build combined dict of all supported languages."""
            langs = dict(self._dispatcher._extractors)
            # Expand group mappings into individual language entries
            for group_name, languages in self._dispatcher._group_mappings.items():
                extractor = self._dispatcher._extractors.get(group_name)
                if extractor:
                    for lang in languages:
                        langs[lang] = extractor
            return langs
        
        def __getattr__(self, name):
            return getattr(self._dispatcher, name)
    
    # Trigger lazy initialization of the dispatcher
    if not _ts_module.language_dispatcher._extractors:
        _ts_module._initialize_language_dispatcher()
    
    _language_registry = _RegistryWrapper(_ts_module.language_dispatcher)
    language_registry = _language_registry
else:
    # Fallback if ts_extractor.py doesn't exist
    def extract_functions_treesitter(source: str, file_path: str):
        return []
    def get_supported_languages():
        return []
    def is_language_supported(file_path: str):
        return False
    def _extract_blocks_html_xml(node, source_lines, file_path):
        return []
    def _extract_blocks_css(node, source_lines, file_path):
        return []
    def _extract_blocks_sql(node, source_lines, file_path):
        return []
    def _extract_functions_c_cpp(node, source_lines, file_path):
        return []
    def _extract_functions_lua(node, source_lines, file_path):
        return []
    _LANGUAGE_MAPPING = {}
    LANGUAGE_MAPPING = {}
    _language_registry = None
    language_registry = None

__all__ = [
    "extract_functions_treesitter",
    "get_supported_languages",
    "is_language_supported",
    "LANGUAGE_MAPPING",
    "_LANGUAGE_MAPPING",
    "language_registry",
    "_language_registry",
    "_extract_blocks_html_xml",
    "_extract_blocks_css",
    "_extract_blocks_sql",
    "_extract_functions_c_cpp",
    "_extract_functions_lua",
]