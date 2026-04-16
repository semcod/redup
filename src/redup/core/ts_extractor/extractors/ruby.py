"""Ruby extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block, get_node_text


def extract_functions_ruby(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Ruby using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Method definitions, singleton methods, class methods
        if node_type in ("method", "singleton_method", "class_method"):
            name_node = node.child_by_field_name("name")
            function_name = get_node_text(name_node) if name_node else "anonymous"
            
            # Add prefix for different method types
            if node_type == "singleton_method":
                function_name = "singleton_" + function_name
            elif node_type == "class_method":
                function_name = "class_" + function_name
            
            blocks.append(create_code_block(node, source_lines, file_path, function_name))
        
        # Class and module definitions
        elif node_type in ("class", "module"):
            name_node = node.child_by_field_name("name")
            function_name = get_node_text(name_node) if name_node else "anonymous"
            function_name = f"{node_type}_{function_name}"
            
            blocks.append(create_code_block(node, source_lines, file_path, function_name))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
