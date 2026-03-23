"""Generic function extraction framework for tree-sitter based languages."""

from typing import Any, Callable, List, Optional
from ..scanner import CodeBlock


class FunctionExtractor:
    """Generic function extractor that can be configured for different languages."""
    
    def __init__(self, 
                 function_node_types: List[str],
                 method_node_types: List[str],
                 extract_class_name: Optional[Callable[[Any], Optional[str]]] = None):
        """
        Initialize extractor for a specific language.
        
        Args:
            function_node_types: Tree-sitter node types that represent functions
            method_node_types: Tree-sitter node types that represent methods  
            extract_class_name: Optional function to extract class name from method nodes
        """
        self.function_node_types = function_node_types
        self.method_node_types = method_node_types
        self.extract_class_name = extract_class_name
    
    def extract_functions(self, node: Any, source_lines: List[str], file_path: str) -> List[CodeBlock]:
        """Extract functions from AST using the configured node types."""
        blocks = []
        
        def traverse(node: Any, depth: int = 0) -> None:
            if depth > 50:
                return
                
            node_type = node.type
            
            # Handle function declarations
            if node_type in self.function_node_types:
                block = self._create_function_block(node, source_lines, file_path)
                if block:
                    blocks.append(block)
            
            # Handle method declarations
            elif node_type in self.method_node_types:
                class_name = None
                if self.extract_class_name:
                    class_name = self.extract_class_name(node)
                    
                block = self._create_method_block(node, source_lines, file_path, class_name)
                if block:
                    blocks.append(block)
            
            # Recursively traverse children
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(node)
        return blocks
    
    def _create_function_block(self, node: Any, source_lines: List[str], file_path: str) -> Optional[CodeBlock]:
        """Create a CodeBlock for a function node."""
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # Extract function name
        name_node = node.child_by_field_name("name")
        function_name = name_node.text.decode() if name_node else "anonymous"
        
        return CodeBlock(
            file=file_path,
            line_start=start_line,
            line_end=end_line,
            text="\n".join(source_lines[start_line-1:end_line]),
            function_name=function_name,
            class_name=None,
        )
    
    def _create_method_block(self, node: Any, source_lines: List[str], file_path: str, class_name: Optional[str]) -> Optional[CodeBlock]:
        """Create a CodeBlock for a method node."""
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        
        # Extract method name
        name_node = node.child_by_field_name("name")
        method_name = name_node.text.decode() if name_node else "anonymous"
        
        return CodeBlock(
            file=file_path,
            line_start=start_line,
            line_end=end_line,
            text="\n".join(source_lines[start_line-1:end_line]),
            function_name=method_name,
            class_name=class_name,
        )


# Language-specific configurations
def _extract_java_class_name(node: Any) -> Optional[str]:
    """Extract class name from Java method node."""
    parent = node.parent
    while parent and parent.type != "class_declaration":
        parent = parent.parent
    if parent:
        class_name_node = parent.child_by_field_name("name")
        return class_name_node.text.decode() if class_name_node else None
    return None


# Pre-configured extractors for each language
GO_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_declaration"],
    method_node_types=[]
)

RUST_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_item"],
    method_node_types=["method_declaration"]
)

JAVA_EXTRACTOR = FunctionExtractor(
    function_node_types=[],
    method_node_types=["method_declaration"],
    extract_class_name=_extract_java_class_name
)

SCALA_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_definition"],
    method_node_types=["method_definition"]
)

KOTLIN_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_declaration"],
    method_node_types=["function_declaration"]
)

SWIFT_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_declaration"],
    method_node_types=["method_declaration"]
)

OBJC_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_definition"],
    method_node_types=["method_declaration"]
)

LUA_EXTRACTOR = FunctionExtractor(
    function_node_types=["function_declaration", "local_function"],
    method_node_types=[]
)
