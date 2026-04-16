"""SQL extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import create_code_block


def extract_blocks_sql(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract SQL statements and clauses as blocks using tree-sitter."""
    blocks: list[CodeBlock] = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Extract SQL statements
        if node_type in (
            "select_statement", "insert_statement", "update_statement", 
            "delete_statement", "create_statement", "alter_statement",
            "drop_statement", "function_definition", "procedure_definition"
        ):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Only include statements with content
            if end_line - start_line >= 1:
                blocks.append(create_code_block(
                    node, source_lines, file_path, node_type.replace("_", " ")
                ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    traverse(node)
    return blocks
