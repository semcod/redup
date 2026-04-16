"""Base utilities for tree-sitter extractors."""

from __future__ import annotations

from typing import Any, Callable

from redup.core.scanner import CodeBlock


def traverse_tree(
    node: Any,
    source_lines: list[str],
    file_path: str,
    matchers: dict[str, Callable[[Any, list[str], str], CodeBlock | None]],
    depth: int = 0,
    max_depth: int = 50,
) -> list[CodeBlock]:
    """Generic tree traversal with pluggable matchers.
    
    Args:
        node: Current tree-sitter node
        source_lines: Source code split by lines
        file_path: Path to the source file
        matchers: Dict mapping node types to extractor functions
        depth: Current recursion depth
        max_depth: Maximum recursion depth to prevent infinite loops
        
    Returns:
        List of extracted code blocks
    """
    if depth > max_depth:
        return []
    
    blocks: list[CodeBlock] = []
    node_type = node.type
    
    # Try to match this node
    if node_type in matchers:
        block = matchers[node_type](node, source_lines, file_path)
        if block:
            blocks.append(block)
    
    # Recursively traverse children
    for child in node.children:
        blocks.extend(traverse_tree(child, source_lines, file_path, matchers, depth + 1, max_depth))
    
    return blocks


def get_node_text(node: Any) -> str:
    """Safely get decoded text from a node."""
    if hasattr(node, 'text') and node.text:
        return node.text.decode()
    return ""


def create_code_block(
    node: Any,
    source_lines: list[str],
    file_path: str,
    function_name: str,
    class_name: str | None = None,
) -> CodeBlock:
    """Create a CodeBlock from a tree-sitter node."""
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    
    return CodeBlock(
        file=file_path,
        line_start=start_line,
        line_end=end_line,
        text="\n".join(source_lines[start_line - 1:end_line]),
        function_name=function_name,
        class_name=class_name,
    )
