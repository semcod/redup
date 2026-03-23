"""Multi-language function extraction using tree-sitter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tree_sitter
except ImportError:
    tree_sitter = None

from redup.core.scanner import CodeBlock


# Language mappings for tree-sitter
_LANGUAGE_MAPPING = {
    # Web/JavaScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".mts": "typescript",
    # HTML/XML
    ".html": "html",
    ".htm": "html",
    ".xhtml": "html",
    ".xml": "xml",
    ".svg": "xml",
    # CSS
    ".css": "css",
    ".scss": "css",
    ".sass": "css",
    ".less": "css",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Java/C-family
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    ".scala": "scala",
    ".kt": "kotlin",
    # Swift/Objective-C
    ".swift": "swift",
    ".m": "objc",
    ".mm": "objc",
    # Python (fallback to AST)
    ".py": "python",
    ".pyw": "python",
    # Ruby
    ".rb": "ruby",
    ".rbw": "ruby",
    ".rake": "ruby",
    ".gemspec": "ruby",
    # PHP
    ".php": "php",
    ".phtml": "php",
    ".php3": "php",
    ".php4": "php",
    ".php5": "php",
    ".phps": "php",
    # SQL
    ".sql": "sql",
    ".ddl": "sql",
    ".dml": "sql",
    # Data formats
    ".json": "json",
    ".json5": "json",
    ".jsonl": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    # Markdown
    ".md": "markdown",
    ".markdown": "markdown",
    ".mdown": "markdown",
    ".mkd": "markdown",
    ".mkdown": "markdown",
    # Shell
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".fish": "bash",
    # Templates
    ".erb": "embedded_template",
    ".ejs": "embedded_template",
    ".hbs": "embedded_template",
    ".handlebars": "embedded_template",
    # Regex
    ".regex": "regex",
}


def _get_tree_sitter_language(language_name: str) -> Any:
    """Get tree-sitter language parser."""
    if tree_sitter is None:
        return None
    
    try:
        if language_name == "javascript":
            import tree_sitter_javascript
            return tree_sitter.Language(tree_sitter_javascript.language())
        elif language_name == "typescript":
            import tree_sitter_typescript
            return tree_sitter.Language(tree_sitter_typescript.language_typescript())
        elif language_name == "html":
            import tree_sitter_html
            return tree_sitter.Language(tree_sitter_html.language())
        elif language_name == "xml":
            import tree_sitter_xml
            return tree_sitter.Language(tree_sitter_xml.language())
        elif language_name == "css":
            import tree_sitter_css
            return tree_sitter.Language(tree_sitter_css.language())
        elif language_name == "go":
            import tree_sitter_go
            return tree_sitter.Language(tree_sitter_go.language())
        elif language_name == "rust":
            import tree_sitter_rust
            return tree_sitter.Language(tree_sitter_rust.language())
        elif language_name == "java":
            import tree_sitter_java
            return tree_sitter.Language(tree_sitter_java.language())
        elif language_name == "c":
            import tree_sitter_c
            return tree_sitter.Language(tree_sitter_c.language())
        elif language_name == "cpp":
            import tree_sitter_cpp
            return tree_sitter.Language(tree_sitter_cpp.language())
        elif language_name == "c_sharp":
            import tree_sitter_c_sharp
            return tree_sitter.Language(tree_sitter_c_sharp.language())
        elif language_name == "scala":
            import tree_sitter_scala
            return tree_sitter.Language(tree_sitter_scala.language())
        elif language_name == "kotlin":
            import tree_sitter_kotlin
            return tree_sitter.Language(tree_sitter_kotlin.language())
        elif language_name == "swift":
            import tree_sitter_swift
            return tree_sitter.Language(tree_sitter_swift.language())
        elif language_name == "objc":
            import tree_sitter_objc
            return tree_sitter.Language(tree_sitter_objc.language())
        elif language_name == "ruby":
            import tree_sitter_ruby
            return tree_sitter.Language(tree_sitter_ruby.language())
        elif language_name == "php":
            import tree_sitter_php
            return tree_sitter.Language(tree_sitter_php.language())
        elif language_name == "sql":
            import tree_sitter_sql
            return tree_sitter.Language(tree_sitter_sql.language())
        elif language_name == "json":
            import tree_sitter_json
            return tree_sitter.Language(tree_sitter_json.language())
        elif language_name == "yaml":
            import tree_sitter_yaml
            return tree_sitter.Language(tree_sitter_yaml.language())
        elif language_name == "toml":
            import tree_sitter_toml
            return tree_sitter.Language(tree_sitter_toml.language())
        elif language_name == "markdown":
            import tree_sitter_markdown
            return tree_sitter.Language(tree_sitter_markdown.language())
        elif language_name == "bash":
            import tree_sitter_bash
            return tree_sitter.Language(tree_sitter_bash.language())
        elif language_name == "embedded_template":
            import tree_sitter_embedded_template
            return tree_sitter.Language(tree_sitter_embedded_template.language())
        elif language_name == "regex":
            import tree_sitter_regex
            return tree_sitter.Language(tree_sitter_regex.language())
        else:
            return None
    except ImportError:
        return None


def _extract_functions_javascript(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from JavaScript/TypeScript using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:  # Prevent infinite recursion
            return
            
        node_type = node.type
        
        # Function declarations
        if node_type in ("function_declaration", "function_definition"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract function name
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        # Method definitions in classes
        elif node_type == "method_definition":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract method name
            name_node = node.child_by_field_name("name")
            method_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=method_name,
                class_name=None,  # Could be extracted from parent class node
            ))
        
        # Arrow functions (if they span multiple lines)
        elif node_type == "arrow_function":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            if end_line - start_line >= 3:  # Only include multi-line arrow functions
                blocks.append(CodeBlock(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text="\n".join(source_lines[start_line-1:end_line]),
                    function_name="arrow_function",
                    class_name=None,
                ))
        
        # Recursively traverse children
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_go(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Go using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
            
        node_type = node.type
        
        # Function declarations
        if node_type == "function_declaration":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract function name
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        # Method declarations
        elif node_type == "method_declaration":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract method name
            name_node = node.child_by_field_name("name")
            method_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=method_name,
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_rust(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Rust using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
            
        node_type = node.type
        
        # Function definitions
        if node_type == "function_item":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract function name
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        # Method definitions in impl blocks
        elif node_type == "method_declaration":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract method name
            name_node = node.child_by_field_name("name")
            method_name = name_node.text.decode() if name_node else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=method_name,
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_java(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Java using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
            
        node_type = node.type
        
        # Method declarations
        if node_type == "method_declaration":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            # Extract method name
            name_node = node.child_by_field_name("name")
            method_name = name_node.text.decode() if name_node else "anonymous"
            
            # Try to get class name from parent
            class_name = None
            parent = node.parent
            while parent and parent.type != "class_declaration":
                parent = parent.parent
            if parent:
                class_name_node = parent.child_by_field_name("name")
                class_name = class_name_node.text.decode() if class_name_node else None
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=method_name,
                class_name=class_name,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def extract_functions_treesitter(source: str, file_path: str) -> list[CodeBlock]:
    """Extract functions using tree-sitter for multi-language support."""
    if tree_sitter is None:
        return []
    
    # Determine language from file extension
    file_ext = Path(file_path).suffix.lower()
    language_name = _LANGUAGE_MAPPING.get(file_ext)
    
    if not language_name:
        return []
    
    # Skip Python - use existing AST extractor
    if language_name == "python":
        return []
    
    # Get language parser
    language = _get_tree_sitter_language(language_name)
    if language is None:
        return []
    
    # Parse the source code
    parser = tree_sitter.Parser(language)
    
    try:
        tree = parser.parse(bytes(source, "utf8"))
    except Exception:
        return []
    
    source_lines = source.splitlines()
    
    # Extract functions based on language
    if language_name in ("javascript", "typescript"):
        return _extract_functions_javascript(tree.root_node, source_lines, file_path)
    elif language_name == "go":
        return _extract_functions_go(tree.root_node, source_lines, file_path)
    elif language_name == "rust":
        return _extract_functions_rust(tree.root_node, source_lines, file_path)
    elif language_name == "java":
        return _extract_functions_java(tree.root_node, source_lines, file_path)
    elif language_name == "c_sharp":
        return _extract_functions_c_sharp(tree.root_node, source_lines, file_path)
    elif language_name == "scala":
        return _extract_functions_scala(tree.root_node, source_lines, file_path)
    elif language_name == "kotlin":
        return _extract_functions_kotlin(tree.root_node, source_lines, file_path)
    elif language_name == "swift":
        return _extract_functions_swift(tree.root_node, source_lines, file_path)
    elif language_name == "objc":
        return _extract_functions_objc(tree.root_node, source_lines, file_path)
    elif language_name == "ruby":
        return _extract_functions_ruby(tree.root_node, source_lines, file_path)
    elif language_name == "php":
        return _extract_functions_php(tree.root_node, source_lines, file_path)
    elif language_name == "bash":
        return _extract_functions_bash(tree.root_node, source_lines, file_path)
    elif language_name in ("c", "cpp"):
        # C/C++ function extraction would be more complex
        # For now, return empty list
        return []
    elif language_name in ("html", "xml", "css", "json", "yaml", "toml", "markdown", "embedded_template", "regex", "sql"):
        # Data formats and markup languages don't have functions in the traditional sense
        return []
    
    return []


def get_supported_languages() -> list[str]:
    """Get list of supported languages for tree-sitter extraction."""
    if tree_sitter is None:
        return []
    
    supported = []
    for ext, lang in _LANGUAGE_MAPPING.items():
        if _get_tree_sitter_language(lang) is not None:
            supported.append(ext)
    
    return supported


def is_language_supported(file_path: str) -> bool:
    """Check if a file extension is supported by tree-sitter extraction."""
    file_ext = Path(file_path).suffix.lower()
    language_name = _LANGUAGE_MAPPING.get(file_ext)
    
    if not language_name or language_name == "python":
        return False
    
    return _get_tree_sitter_language(language_name) is not None
