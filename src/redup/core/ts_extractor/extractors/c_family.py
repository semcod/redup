"""C/C++ extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block


def extract_functions_c_cpp(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from C/C++ using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        if node_type in ("function_definition", "function_declarator"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("declarator")
            if name_node:
                # Try to get the actual function name from the declarator
                while name_node and name_node.type not in ("identifier", "scoped_identifier"):
                    name_node = name_node.child_by_field_name("declarator") or (
                        name_node.children[0] if name_node.children else None
                    )
            
            function_name = name_node.text.decode() if name_node and hasattr(name_node, 'text') else "anonymous"
            
            blocks.append(create_code_block(node, source_lines, file_path, function_name))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
