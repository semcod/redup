"""PHP extractor using tree-sitter."""

from __future__ import annotations

from typing import Any

from redup.core.scanner import CodeBlock
from redup.core.ts_extractor.extractors.base import (
    create_code_block,
    get_ancestor_name,
    get_node_text,
)


def extract_functions_php(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from PHP using tree-sitter."""
    blocks: list[CodeBlock] = []

    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return

        node_type = node.type

        # Function definitions, method declarations
        if node_type in ("function_definition", "method_declaration"):
            name_node = node.child_by_field_name("name")
            function_name = get_node_text(name_node) if name_node else "anonymous"
            class_name = (
                get_ancestor_name(node, "class_declaration")
                if node_type == "method_declaration"
                else None
            )

            blocks.append(
                create_code_block(node, source_lines, file_path, function_name, class_name)
            )

        # Anonymous functions/closures
        elif node_type == "closure_expression":
            blocks.append(create_code_block(node, source_lines, file_path, "anonymous_closure"))

        for child in node.children:
            traverse(child, depth + 1)

    traverse(node)
    return blocks
