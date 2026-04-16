"""CSS extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block


def extract_blocks_css(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract CSS rules and declarations as blocks using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Extract CSS rules (selector + declaration block)
        if node_type in ("rule_set", "at_rule"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Only include multi-line rules
            if end_line - start_line >= 1:
                # Try to get selector name
                selector_name = node_type
                for child in node.children:
                    if child.type in ("selector", "tag_name", "class_name", "identifier"):
                        selector_name = child.text.decode() if child.text else node_type
                        break
                    elif child.type == "at_keyword":
                        selector_name = child.text.decode() if child.text else node_type
                        break
                
                blocks.append(create_code_block(
                    node, source_lines, file_path, selector_name[:50]  # Limit length
                ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
