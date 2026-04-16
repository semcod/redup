"""Bash/Shell extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block, get_node_text


def extract_functions_bash(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Bash using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        if node_type == "function_definition":
            name_node = node.child_by_field_name("name")
            function_name = get_node_text(name_node) if name_node else "anonymous"
            
            blocks.append(create_code_block(node, source_lines, file_path, function_name))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
