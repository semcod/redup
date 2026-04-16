"""Language dispatcher initialization for tree-sitter extractors."""

from __future__ import annotations

from redup.core.utils.language_dispatcher import language_dispatcher

# Import extractors from function_extractor module (core utils)
from redup.core.utils.function_extractor import (
    GO_EXTRACTOR,
    RUST_EXTRACTOR,
    JAVA_EXTRACTOR,
    SCALA_EXTRACTOR,
    KOTLIN_EXTRACTOR,
    SWIFT_EXTRACTOR,
    OBJC_EXTRACTOR,
    LUA_EXTRACTOR,
)

# Import local extractors directly (avoid circular import through __init__)
from redup.core.ts_extractor.extractors.web import extract_functions_javascript
from redup.core.ts_extractor.extractors.c_family import extract_functions_c_cpp
from redup.core.ts_extractor.extractors.markup import extract_blocks_html_xml
from redup.core.ts_extractor.extractors.stylesheet import extract_blocks_css
from redup.core.ts_extractor.extractors.query import extract_blocks_sql
from redup.core.ts_extractor.extractors.dotnet import extract_functions_c_sharp
from redup.core.ts_extractor.extractors.ruby import extract_functions_ruby
from redup.core.ts_extractor.extractors.php import extract_functions_php
from redup.core.ts_extractor.extractors.shell import extract_functions_bash


def initialize_language_dispatcher() -> None:
    """Initialize the language dispatcher with all supported extractors."""
    # Skip if already initialized
    if language_dispatcher._extractors:
        return
    
    # Register individual language extractors (from function_extractor module)
    language_dispatcher.register_extractor("go", GO_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("rust", RUST_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("java", JAVA_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("scala", SCALA_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("kotlin", KOTLIN_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("swift", SWIFT_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("objc", OBJC_EXTRACTOR.extract_functions)
    language_dispatcher.register_extractor("lua", LUA_EXTRACTOR.extract_functions)
    
    # Register groups of languages
    language_dispatcher.register_group("web_languages", ["javascript", "typescript"])
    language_dispatcher.register_group("c_cpp", ["c", "cpp"])
    language_dispatcher.register_extractor("web_languages", extract_functions_javascript)
    language_dispatcher.register_extractor("c_cpp", extract_functions_c_cpp)
    
    # Register other languages (local extractors)
    language_dispatcher.register_extractor("c_sharp", extract_functions_c_sharp)
    language_dispatcher.register_extractor("ruby", extract_functions_ruby)
    language_dispatcher.register_extractor("php", extract_functions_php)
    language_dispatcher.register_extractor("bash", extract_functions_bash)
    language_dispatcher.register_extractor("html", extract_blocks_html_xml)
    language_dispatcher.register_extractor("xml", extract_blocks_html_xml)
    language_dispatcher.register_extractor("css", extract_blocks_css)
    language_dispatcher.register_extractor("sql", extract_blocks_sql)
    
    # Register web framework languages
    language_dispatcher.register_extractor("svelte", extract_blocks_html_xml)
    language_dispatcher.register_extractor("vue", extract_blocks_html_xml)
    
    # Register data formats (use HTML/XML extractor for structure)
    language_dispatcher.register_extractor("json", extract_blocks_html_xml)
    language_dispatcher.register_extractor("yaml", extract_blocks_html_xml)
    language_dispatcher.register_extractor("toml", extract_blocks_html_xml)
    language_dispatcher.register_extractor("markdown", extract_blocks_html_xml)
    
    # Register DSL languages
    language_dispatcher.register_extractor("graphql", extract_blocks_sql)
    language_dispatcher.register_extractor("dockerfile", extract_blocks_sql)
    language_dispatcher.register_extractor("make", extract_blocks_sql)
    language_dispatcher.register_extractor("nginx", extract_blocks_sql)
    language_dispatcher.register_extractor("vim", extract_blocks_sql)


# Auto-initialize on import
initialize_language_dispatcher()
