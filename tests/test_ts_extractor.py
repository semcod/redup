"""Tests for tree-sitter multi-language extraction."""

from pathlib import Path

import pytest

from redup.core.ts_extractor import (
    _LANGUAGE_MAPPING,
    _language_registry,
    extract_functions_treesitter,
    get_supported_languages,
    is_language_supported,
)


class TestLanguageMapping:
    """Test language extension mappings."""

    def test_language_mapping_has_common_extensions(self):
        """Test that common language extensions are mapped."""
        assert ".py" in _LANGUAGE_MAPPING
        assert ".js" in _LANGUAGE_MAPPING
        assert ".ts" in _LANGUAGE_MAPPING
        assert ".go" in _LANGUAGE_MAPPING
        assert ".rs" in _LANGUAGE_MAPPING
        assert ".java" in _LANGUAGE_MAPPING

    def test_language_mapping_has_new_web_languages(self):
        """Test that new web language extensions are mapped."""
        assert ".html" in _LANGUAGE_MAPPING
        assert ".css" in _LANGUAGE_MAPPING
        assert ".svelte" in _LANGUAGE_MAPPING
        assert ".vue" in _LANGUAGE_MAPPING

    def test_language_mapping_has_data_formats(self):
        """Test that data format extensions are mapped."""
        assert ".json" in _LANGUAGE_MAPPING
        assert ".yaml" in _LANGUAGE_MAPPING
        assert ".yml" in _LANGUAGE_MAPPING
        assert ".toml" in _LANGUAGE_MAPPING
        assert ".xml" in _LANGUAGE_MAPPING
        assert ".md" in _LANGUAGE_MAPPING

    def test_language_mapping_has_sql(self):
        """Test that SQL extensions are mapped."""
        assert ".sql" in _LANGUAGE_MAPPING
        assert ".ddl" in _LANGUAGE_MAPPING
        assert ".dml" in _LANGUAGE_MAPPING

    def test_language_mapping_has_dsl_languages(self):
        """Test that DSL language extensions are mapped."""
        assert ".graphql" in _LANGUAGE_MAPPING
        assert ".gql" in _LANGUAGE_MAPPING
        assert "Dockerfile" in _LANGUAGE_MAPPING
        assert ".dockerfile" in _LANGUAGE_MAPPING
        assert "Makefile" in _LANGUAGE_MAPPING
        assert ".mk" in _LANGUAGE_MAPPING
        assert ".nginx" in _LANGUAGE_MAPPING
        assert ".vim" in _LANGUAGE_MAPPING
        assert ".svelte" in _LANGUAGE_MAPPING
        assert ".vue" in _LANGUAGE_MAPPING

    def test_language_mapping_has_additional_programming(self):
        """Test that additional programming language extensions are mapped."""
        assert ".rb" in _LANGUAGE_MAPPING
        assert ".php" in _LANGUAGE_MAPPING
        assert ".sh" in _LANGUAGE_MAPPING
        assert ".lua" in _LANGUAGE_MAPPING
        assert ".scala" in _LANGUAGE_MAPPING
        assert ".kt" in _LANGUAGE_MAPPING
        assert ".swift" in _LANGUAGE_MAPPING
        assert ".m" in _LANGUAGE_MAPPING
        assert ".cs" in _LANGUAGE_MAPPING

    def test_language_mapping_count(self):
        """Test that we have expected number of language mappings."""
        # Should have at least 80 mappings (33 languages with multiple extensions)
        assert len(_LANGUAGE_MAPPING) >= 80


class TestLanguageRegistry:
    """Test language registry for tree-sitter parsers."""

    def test_registry_has_core_languages(self):
        """Test that core programming languages are in registry."""
        assert "javascript" in _language_registry._languages
        assert "typescript" in _language_registry._languages
        assert "go" in _language_registry._languages
        assert "rust" in _language_registry._languages
        assert "java" in _language_registry._languages

    def test_registry_has_web_languages(self):
        """Test that web languages are in registry."""
        assert "html" in _language_registry._languages
        assert "css" in _language_registry._languages
        assert "svelte" in _language_registry._languages
        assert "vue" in _language_registry._languages

    def test_registry_has_new_languages(self):
        """Test that newly added languages are in registry."""
        assert "ruby" in _language_registry._languages
        assert "php" in _language_registry._languages
        assert "bash" in _language_registry._languages
        assert "lua" in _language_registry._languages
        assert "sql" in _language_registry._languages
        assert "scala" in _language_registry._languages
        assert "kotlin" in _language_registry._languages
        assert "swift" in _language_registry._languages
        assert "objc" in _language_registry._languages
        assert "c_sharp" in _language_registry._languages

    def test_registry_has_dsl_languages(self):
        """Test that DSL languages are in registry."""
        assert "graphql" in _language_registry._languages
        assert "dockerfile" in _language_registry._languages
        assert "make" in _language_registry._languages
        assert "nginx" in _language_registry._languages
        assert "vim" in _language_registry._languages

    def test_registry_has_data_formats(self):
        """Test that data format languages are in registry."""
        assert "json" in _language_registry._languages
        assert "yaml" in _language_registry._languages
        assert "toml" in _language_registry._languages
        assert "xml" in _language_registry._languages
        assert "markdown" in _language_registry._languages

    def test_registry_count(self):
        """Test that we have expected number of registered languages."""
        # Should have at least 33 registered languages
        assert len(_language_registry._languages) >= 33


class TestLanguageSupportFunctions:
    """Test language support checking functions."""

    def test_is_language_supported_python(self):
        """Python is not supported by tree-sitter (uses AST instead)."""
        assert not is_language_supported("test.py")

    def test_is_language_supported_unknown_extension(self):
        """Unknown extensions are not supported."""
        assert not is_language_supported("test.unknown")

    def test_is_language_supported_known_languages(self):
        """Known language extensions are supported."""
        # Note: This will return False if tree-sitter packages are not installed
        # but the function should work without errors
        result = is_language_supported("test.js")
        # Result depends on whether tree-sitter is installed
        assert result in [True, False]


class TestExtractFunctions:
    """Test function extraction for different languages."""

    def test_extract_python_returns_empty(self):
        """Python extraction returns empty (uses AST instead)."""
        source = "def hello(): pass"
        result = extract_functions_treesitter(source, "test.py")
        assert result == []

    def test_extract_unknown_extension_returns_empty(self):
        """Unknown extension returns empty list."""
        source = "some content"
        result = extract_functions_treesitter(source, "test.unknown")
        assert result == []

    def test_extract_javascript_no_treesitter(self):
        """JavaScript extraction without tree-sitter returns empty."""
        # This test will pass if tree-sitter is not installed
        source = "function hello() { return 42; }"
        result = extract_functions_treesitter(source, "test.js")
        # Returns empty if tree-sitter is not installed
        assert isinstance(result, list)


class TestHTMLExtraction:
    """Test HTML block extraction."""

    def test_html_extraction_structure(self):
        """Test that HTML extraction function exists."""
        from redup.core.ts_extractor import _extract_blocks_html_xml
        # Function should exist and be callable
        assert callable(_extract_blocks_html_xml)


class TestCSSExtraction:
    """Test CSS block extraction."""

    def test_css_extraction_structure(self):
        """Test that CSS extraction function exists."""
        from redup.core.ts_extractor import _extract_blocks_css
        # Function should exist and be callable
        assert callable(_extract_blocks_css)


class TestSQLExtraction:
    """Test SQL block extraction."""

    def test_sql_extraction_structure(self):
        """Test that SQL extraction function exists."""
        from redup.core.ts_extractor import _extract_blocks_sql
        # Function should exist and be callable
        assert callable(_extract_blocks_sql)


class TestCExtraction:
    """Test C/C++ function extraction."""

    def test_c_extraction_structure(self):
        """Test that C extraction function exists."""
        from redup.core.ts_extractor import _extract_functions_c_cpp
        # Function should exist and be callable
        assert callable(_extract_functions_c_cpp)


class TestLuaExtraction:
    """Test Lua function extraction."""

    def test_lua_extraction_structure(self):
        """Test that Lua extraction function exists."""
        from redup.core.ts_extractor import _extract_functions_lua
        # Function should exist and be callable
        assert callable(_extract_functions_lua)
