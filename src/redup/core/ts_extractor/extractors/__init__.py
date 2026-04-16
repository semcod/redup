"""Language-specific tree-sitter extractors."""

from redup.core.ts_extractor.extractors.web import extract_functions_javascript
from redup.core.ts_extractor.extractors.c_family import extract_functions_c_cpp
from redup.core.ts_extractor.extractors.markup import extract_blocks_html_xml
from redup.core.ts_extractor.extractors.stylesheet import extract_blocks_css
from redup.core.ts_extractor.extractors.query import extract_blocks_sql
from redup.core.ts_extractor.extractors.dotnet import extract_functions_c_sharp
from redup.core.ts_extractor.extractors.ruby import extract_functions_ruby
from redup.core.ts_extractor.extractors.php import extract_functions_php
from redup.core.ts_extractor.extractors.shell import extract_functions_bash

__all__ = [
    "extract_functions_javascript",
    "extract_functions_c_cpp",
    "extract_blocks_html_xml",
    "extract_blocks_css",
    "extract_blocks_sql",
    "extract_functions_c_sharp",
    "extract_functions_ruby",
    "extract_functions_php",
    "extract_functions_bash",
]
