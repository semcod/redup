"""HTML/XML extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block


def extract_blocks_html_xml(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract meaningful blocks from HTML/XML using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Extract elements (tags) as blocks
        if node_type in ("element", "self_closing_tag", "start_tag", "tag"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Only include multi-line elements or elements with content
            if end_line - start_line >= 1:
                # Try to get tag name
                tag_name = node_type
                for child in node.children:
                    if child.type == "tag_name":
                        tag_name = child.text.decode() if child.text else node_type
                        break
                
                blocks.append(create_code_block(node, source_lines, file_path, f"<{tag_name}>"))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
