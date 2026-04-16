"""JavaScript/TypeScript extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block, get_node_text


def _extract_function_declaration(node: Any, source_lines: list[str], file_path: str) -> CodeBlock | None:
    """Extract a function declaration."""
    name_node = node.child_by_field_name("name")
    function_name = get_node_text(name_node) if name_node else "anonymous"
    return create_code_block(node, source_lines, file_path, function_name)


def _extract_method_definition(node: Any, source_lines: list[str], file_path: str) -> CodeBlock | None:
    """Extract a method definition."""
    name_node = node.child_by_field_name("name")
    method_name = get_node_text(name_node) if name_node else "anonymous"
    return create_code_block(node, source_lines, file_path, method_name)


def _extract_arrow_function(node: Any, source_lines: list[str], file_path: str) -> CodeBlock | None:
    """Extract an arrow function if it spans multiple lines."""
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    
    # Only include multi-line arrow functions
    if end_line - start_line < 3:
        return None
    
    return create_code_block(node, source_lines, file_path, "arrow_function")


def extract_functions_javascript(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from JavaScript/TypeScript using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        if node_type in ("function_declaration", "function_definition"):
            block = _extract_function_declaration(node, source_lines, file_path)
            if block:
                blocks.append(block)
        elif node_type == "method_definition":
            block = _extract_method_definition(node, source_lines, file_path)
            if block:
                blocks.append(block)
        elif node_type == "arrow_function":
            block = _extract_arrow_function(node, source_lines, file_path)
            if block:
                blocks.append(block)
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
