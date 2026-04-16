from __future__ import annotations
from typing import Any
try:
    import tree_sitter
except ImportError:
    tree_sitter = None

LANGUAGE_MAPPING = {
    ".js": "javascript", ".jsx": "javascript", ".ts": "typescript", ".tsx": "typescript", ".mjs": "javascript", ".cjs": "javascript", ".mts": "typescript",
    ".html": "html", ".htm": "html", ".xhtml": "html", ".xml": "xml", ".svg": "xml",
    ".css": "css", ".scss": "css", ".sass": "css", ".less": "css",
    ".go": "go", ".rs": "rust", ".java": "java", ".c": "c", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "c_sharp", ".scala": "scala", ".kt": "kotlin",
    ".swift": "swift", ".m": "objc", ".mm": "objc", ".py": "python", ".pyw": "python", ".lua": "lua",
    ".rb": "ruby", ".rbw": "ruby", ".rake": "ruby", ".gemspec": "ruby",
    ".php": "php", ".phtml": "php", ".php3": "php", ".php4": "php", ".php5": "php", ".phps": "php",
    ".sql": "sql", ".ddl": "sql", ".dml": "sql",
    ".json": "json", ".json5": "json", ".jsonl": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".md": "markdown", ".markdown": "markdown", ".mdown": "markdown", ".mkd": "markdown", ".mkdown": "markdown",
    ".sh": "bash", ".bash": "bash", ".zsh": "bash", ".fish": "bash",
    ".erb": "embedded_template", ".ejs": "embedded_template", ".hbs": "embedded_template", ".handlebars": "embedded_template",
    ".regex": "regex", ".graphql": "graphql", ".gql": "graphql",
    "Dockerfile": "dockerfile", ".dockerfile": "dockerfile",
    "Makefile": "make", ".mk": "make", ".mak": "make",
    ".vim": "vim", ".vimrc": "vim", ".nginx": "nginx", "nginx.conf": "nginx",
    ".svelte": "svelte", ".vue": "vue"
}

class LanguageRegistry:
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
        if tree_sitter is None or language_name not in self._languages:
            return None
        module_name, function_name = self._languages[language_name]
        try:
            module = __import__(module_name)
            return tree_sitter.Language(getattr(module, function_name)())
        except (ImportError, AttributeError):
            return None

language_registry = LanguageRegistry()