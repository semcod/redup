"""Multi-language function extraction using tree-sitter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import tree_sitter
except ImportError:
    tree_sitter = None

from redup.core.scanner import CodeBlock
from redup.core.utils.function_extractor import (
    GO_EXTRACTOR, RUST_EXTRACTOR, JAVA_EXTRACTOR, 
    SCALA_EXTRACTOR, KOTLIN_EXTRACTOR, SWIFT_EXTRACTOR, OBJC_EXTRACTOR,
    LUA_EXTRACTOR
)


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
    # Lua
    ".lua": "lua",
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
    # Lua
    ".lua": "lua",
    # GraphQL
    ".graphql": "graphql",
    ".gql": "graphql",
    # Dockerfile
    "Dockerfile": "dockerfile",
    ".dockerfile": "dockerfile",
    # Makefile
    "Makefile": "make",
    ".mk": "make",
    ".mak": "make",
    # Vim
    ".vim": "vim",
    ".vimrc": "vim",
    # Nginx
    ".nginx": "nginx",
    "nginx.conf": "nginx",
    # Svelte
    ".svelte": "svelte",
    # Vue
    ".vue": "vue",
}


# Language registry for tree-sitter parsers
class _LanguageRegistry:
    """Registry for tree-sitter language parsers."""
    
    def __init__(self):
        self._languages = {
            "javascript": ("tree_sitter_javascript", "language"),
            "typescript": ("tree_sitter_typescript", "language_typescript"),
            "html": ("tree_sitter_html", "language"),
            "xml": ("tree_sitter_xml", "language"),
            "css": ("tree_sitter_css", "language"),
            "go": ("tree_sitter_go", "language"),
            "rust": ("tree_sitter_rust", "language"),
            "java": ("tree_sitter_java", "language"),
            "c": ("tree_sitter_c", "language"),
            "cpp": ("tree_sitter_cpp", "language"),
            "c_sharp": ("tree_sitter_c_sharp", "language"),
            "scala": ("tree_sitter_scala", "language"),
            "kotlin": ("tree_sitter_kotlin", "language"),
            "swift": ("tree_sitter_swift", "language"),
            "objc": ("tree_sitter_objc", "language"),
            "ruby": ("tree_sitter_ruby", "language"),
            "php": ("tree_sitter_php", "language"),
            "sql": ("tree_sitter_sql", "language"),
            "json": ("tree_sitter_json", "language"),
            "yaml": ("tree_sitter_yaml", "language"),
            "toml": ("tree_sitter_toml", "language"),
            "markdown": ("tree_sitter_markdown", "language"),
            "bash": ("tree_sitter_bash", "language"),
            "embedded_template": ("tree_sitter_embedded_template", "language"),
            "regex": ("tree_sitter_regex", "language"),
            "lua": ("tree_sitter_lua", "language"),
            "graphql": ("tree_sitter_graphql", "language"),
            "dockerfile": ("tree_sitter_dockerfile", "language"),
            "make": ("tree_sitter_make", "language"),
            "vim": ("tree_sitter_vim", "language"),
            "nginx": ("tree_sitter_nginx", "language"),
            "svelte": ("tree_sitter_svelte", "language"),
            "vue": ("tree_sitter_vue", "language"),
        }
    
    def get_language(self, language_name: str) -> Any:
        """Get tree-sitter language parser."""
        if tree_sitter is None:
            return None
        
        if language_name not in self._languages:
            return None
        
        module_name, function_name = self._languages[language_name]
        
        try:
            module = __import__(module_name)
            language_func = getattr(module, function_name)
            return tree_sitter.Language(language_func())
        except ImportError:
            return None
        except AttributeError:
            return None


# Global registry instance
_language_registry = _LanguageRegistry()


def _get_tree_sitter_language(language_name: str) -> Any:
    """Get tree-sitter language parser."""
    return _language_registry.get_language(language_name)


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
    return GO_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_rust(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Rust using tree-sitter."""
    return RUST_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_java(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Java using tree-sitter."""
    return JAVA_EXTRACTOR.extract_functions(node, source_lines, file_path)


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
    elif language_name == "lua":
        return _extract_functions_lua(tree.root_node, source_lines, file_path)
    elif language_name in ("c", "cpp"):
        return _extract_functions_c_cpp(tree.root_node, source_lines, file_path)
    elif language_name in ("html", "xml"):
        return _extract_blocks_html_xml(tree.root_node, source_lines, file_path)
    elif language_name == "css":
        return _extract_blocks_css(tree.root_node, source_lines, file_path)
    elif language_name == "sql":
        return _extract_blocks_sql(tree.root_node, source_lines, file_path)
    elif language_name in ("json", "yaml", "toml", "markdown", "embedded_template", "regex", "graphql", "dockerfile", "make", "vim", "nginx", "svelte", "vue"):
        # Data formats, markup languages, config files, and template languages don't have functions in the traditional sense
        return []
    
    return []



def _extract_functions_c_cpp(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from C/C++ using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        if node_type in ("function_definition", "function_declarator"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("declarator")
            if name_node:
                # Try to get the actual function name from the declarator
                while name_node and name_node.type not in ("identifier", "scoped_identifier"):
                    name_node = name_node.child_by_field_name("declarator") or (
                        name_node.children[0] if name_node.children else None
                    )
            
            function_name = name_node.text.decode() if name_node and hasattr(name_node, 'text') else "anonymous"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_blocks_html_xml(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract meaningful blocks from HTML/XML using tree-sitter."""
    blocks = []
    
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
                
                blocks.append(CodeBlock(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text="\n".join(source_lines[start_line-1:end_line]),
                    function_name=f"<{tag_name}>",
                    class_name=None,
                ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_blocks_css(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract CSS rules and declarations as blocks using tree-sitter."""
    blocks = []
    
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
                
                blocks.append(CodeBlock(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text="\n".join(source_lines[start_line-1:end_line]),
                    function_name=selector_name[:50],  # Limit length
                    class_name=None,
                ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_blocks_sql(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract SQL statements and clauses as blocks using tree-sitter."""
    blocks = []
    
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
                blocks.append(CodeBlock(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text="\n".join(source_lines[start_line-1:end_line]),
                    function_name=node_type.replace("_", " "),
                    class_name=None,
                ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_lua(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Lua using tree-sitter."""
    return LUA_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_c_sharp(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from C# using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Method declarations, constructors, destructors
        if node_type in ("method_declaration", "constructor_declaration", "destructor_declaration"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            # Extract class name for methods
            class_name = None
            if node_type == "method_declaration":
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
                function_name=function_name,
                class_name=class_name,
            ))
        
        # Property getters and setters
        elif node_type == "property_declaration":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("name")
            function_name = (name_node.text.decode() if name_node else "anonymous") + "_property"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_scala(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Scala using tree-sitter."""
    return SCALA_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_kotlin(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Kotlin using tree-sitter."""
    return KOTLIN_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_swift(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Swift using tree-sitter."""
    return SWIFT_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_objc(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Objective-C using tree-sitter."""
    return OBJC_EXTRACTOR.extract_functions(node, source_lines, file_path)


def _extract_functions_ruby(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Ruby using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Method definitions, singleton methods, class methods
        if node_type in ("method", "singleton_method", "class_method"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            # Add prefix for different method types
            if node_type == "singleton_method":
                function_name = "singleton_" + function_name
            elif node_type == "class_method":
                function_name = "class_" + function_name
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        # Class and module definitions (for completeness)
        elif node_type in ("class", "module"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            function_name = f"{node_type}_{function_name}"
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name=function_name,
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_php(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from PHP using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        # Function definitions, method declarations
        if node_type in ("function_definition", "method_declaration"):
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            name_node = node.child_by_field_name("name")
            function_name = name_node.text.decode() if name_node else "anonymous"
            
            # Extract class name for methods
            class_name = None
            if node_type == "method_declaration":
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
                function_name=function_name,
                class_name=class_name,
            ))
        
        # Anonymous functions/closures
        elif node_type == "closure_expression":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
            blocks.append(CodeBlock(
                file=file_path,
                line_start=start_line,
                line_end=end_line,
                text="\n".join(source_lines[start_line-1:end_line]),
                function_name="anonymous_closure",
                class_name=None,
            ))
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


def _extract_functions_bash(node: Any, source_lines: list[str], file_path: str) -> list[CodeBlock]:
    """Extract functions from Bash using tree-sitter."""
    blocks = []
    
    def traverse(node: Any, depth: int = 0) -> None:
        if depth > 50:
            return
        
        node_type = node.type
        
        if node_type == "function_definition":
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1
            
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
        
        for child in node.children:
            traverse(child, depth + 1)
    
    return blocks


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
