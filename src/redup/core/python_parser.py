"""Unified Python parser — libcst (fast) with ast (fallback)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from redup.core.scanner import CodeBlock


@dataclass
class ParsedFunction:
    """A parsed Python function with metadata."""
    name: str
    start_line: int
    end_line: int
    text: str
    class_name: str | None = None
    arg_count: int = 0
    has_return: bool = False
    decorators: list[str] | None = None


def _parse_with_libcst(source: str, filepath: str) -> list[ParsedFunction]:
    """Fast path — libcst CST parsing."""
    try:
        import libcst as cst
    except ImportError:
        return []

    functions: list[ParsedFunction] = []
    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError:
        return []

    class FunctionCollector(cst.CSTVisitor):
        """Collect function definitions with line numbers."""
        
        def __init__(self):
            self._class_stack: list[str] = []

        def visit_ClassDef(self, node: cst.ClassDef) -> bool:
            self._class_stack.append(node.name.value)
            return True

        def leave_ClassDef(self, node: cst.ClassDef) -> None:
            self._class_stack.pop()

        def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
            # Get line numbers from position
            start_line = node.position.start.line if hasattr(node, 'position') else 0
            
            # Extract function text (approximate)
            func_text = cst.Module([node]).code
            
            # Count arguments
            arg_count = len(node.params.params)
            
            # Check for return statements (simplified)
            has_return = 'return' in func_text
            
            # Extract decorators
            decorators = []
            for decorator in node.decorators:
                if hasattr(decorator, 'decorator') and hasattr(decorator.decorator, 'value'):
                    decorators.append(decorator.decorator.value)
            
            functions.append(ParsedFunction(
                name=node.name.value,
                start_line=start_line,
                end_line=start_line + func_text.count('\n'),
                text=func_text,
                class_name=self._class_stack[-1] if self._class_stack else None,
                arg_count=arg_count,
                has_return=has_return,
                decorators=decorators if decorators else None,
            ))
            return False  # Don't visit nested functions

        def visit_AsyncFunctionDef(self, node: cst.AsyncFunctionDef) -> bool:
            # Handle async functions the same way
            return self.visit_FunctionDef(node.function)

    try:
        tree.visit(FunctionCollector())
    except Exception:
        return []

    return functions


def _parse_with_ast(source: str, filepath: str) -> list[ParsedFunction]:
    """Fallback — stdlib ast parsing."""
    import ast
    functions: list[ParsedFunction] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    parent_map: dict[int, ast.ClassDef] = {}
    
    # Build parent map for class context
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in ast.walk(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    parent_map[id(child)] = node

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno or start
            text = "\n".join(lines[start - 1:end])
            class_node = parent_map.get(id(node))
            
            # Count arguments
            arg_count = len(node.args.args)
            
            # Check for return statements
            has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
            
            # Extract decorators
            decorators = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name):
                    decorators.append(decorator.id)
                elif isinstance(decorator, ast.Attribute):
                    decorators.append(ast.unparse(decorator))
            
            functions.append(ParsedFunction(
                name=node.name,
                start_line=start,
                end_line=end,
                text=text,
                class_name=class_node.name if class_node else None,
                arg_count=arg_count,
                has_return=has_return,
                decorators=decorators if decorators else None,
            ))

    return functions


def parse_python_functions(source: str, filepath: str) -> list[ParsedFunction]:
    """Parse Python source — uses libcst if available, falls back to ast."""
    try:
        result = _parse_with_libcst(source, filepath)
        if result:
            return result
    except ImportError:
        pass
    return _parse_with_ast(source, filepath)


def parsed_to_code_blocks(parsed: list[ParsedFunction], filepath: str) -> list[CodeBlock]:
    """Convert ParsedFunction list to CodeBlock list for pipeline compatibility."""
    return [
        CodeBlock(
            file=filepath,
            line_start=f.start_line,
            line_end=f.end_line,
            text=f.text,
            function_name=f.name,
            class_name=f.class_name,
        )
        for f in parsed
    ]
