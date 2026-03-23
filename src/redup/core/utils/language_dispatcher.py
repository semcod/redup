"""Language dispatcher for tree-sitter function extraction."""

from typing import Any, Callable, Dict, List, Optional
from ..scanner import CodeBlock


class LanguageDispatcher:
    """Dispatches function extraction to appropriate language-specific extractors."""
    
    def __init__(self):
        """Initialize the dispatcher with language mappings."""
        self._extractors: Dict[str, Callable] = {}
        self._group_mappings: Dict[str, List[str]] = {}
    
    def register_extractor(self, language: str, extractor: Callable) -> None:
        """Register a language-specific extractor function.
        
        Args:
            language: Language name (e.g., "go", "rust", "java")
            extractor: Function that extracts CodeBlocks from AST
        """
        self._extractors[language] = extractor
    
    def register_group(self, group_name: str, languages: List[str]) -> None:
        """Register a group of languages that share the same extractor.
        
        Args:
            group_name: Name for the group (e.g., "web_languages")
            languages: List of language names in the group
        """
        self._group_mappings[group_name] = languages
    
    def get_extractor(self, language: str) -> Optional[Callable]:
        """Get the appropriate extractor for a language.
        
        Args:
            language: Language name
            
        Returns:
            Extractor function or None if not found
        """
        # Direct lookup first
        if language in self._extractors:
            return self._extractors[language]
        
        # Check group mappings
        for group_name, languages in self._group_mappings.items():
            if language in languages:
                return self._extractors.get(group_name)
        
        return None
    
    def extract_functions(self, language: str, node: Any, source_lines: List[str], file_path: str) -> List[CodeBlock]:
        """Extract functions using the appropriate language-specific extractor.
        
        Args:
            language: Language name
            node: Tree-sitter AST node
            source_lines: Source code lines
            file_path: File path for context
            
        Returns:
            List of extracted CodeBlocks
        """
        extractor = self.get_extractor(language)
        if extractor:
            return extractor(node, source_lines, file_path)
        return []


# Create global dispatcher instance
language_dispatcher = LanguageDispatcher()
