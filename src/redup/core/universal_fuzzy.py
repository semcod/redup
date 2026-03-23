"""Universal fuzzy similarity detection for all supported languages and DSLs.

This module extends fuzzy similarity detection to work across all programming
languages, configuration files, and domain-specific languages (DSLs) supported
by reDUP's tree-sitter integration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from datasketch import MinHash, MinHashLSH
except ImportError:
    MinHash = None
    MinHashLSH = None

try:
    from rapidfuzz import fuzz, ratio
except ImportError:
    fuzz = None
    ratio = None

from redup.core.scanner import CodeBlock


@dataclass
class UniversalSignature:
    """Universal semantic signature for any code block."""
    
    language_family: str  # 'programming', 'config', 'data', 'template', 'dsl'
    component_type: str  # 'function', 'class', 'config_section', 'api_endpoint', etc.
    structure_hash: str  # Normalized structure fingerprint
    semantic_patterns: list[str]  # Key semantic patterns
    metadata: dict[str, str]  # Language-specific metadata
    complexity_score: float  # Estimated complexity (0.0-1.0)


class UniversalFuzzyExtractor:
    """Universal fuzzy extractor for all supported languages and DSLs."""
    
    # Language family classification
    LANGUAGE_FAMILIES = {
        # Programming languages
        'javascript': 'programming',
        'typescript': 'programming',
        'python': 'programming',
        'java': 'programming',
        'c': 'programming',
        'cpp': 'programming',
        'c_sharp': 'programming',
        'go': 'programming',
        'rust': 'programming',
        'scala': 'programming',
        'kotlin': 'programming',
        'swift': 'programming',
        'objc': 'programming',
        'ruby': 'programming',
        'php': 'programming',
        'lua': 'programming',
        'bash': 'programming',
        
        # Web technologies
        'html': 'template',
        'css': 'styling',
        'xml': 'data',
        'svelte': 'template',
        'vue': 'template',
        'embedded_template': 'template',
        
        # Data formats
        'json': 'data',
        'yaml': 'data',
        'toml': 'data',
        'markdown': 'documentation',
        
        # Configuration/DSL
        'sql': 'query',
        'graphql': 'query',
        'dockerfile': 'infrastructure',
        'make': 'build',
        'nginx': 'infrastructure',
        'vim': 'configuration',
        'regex': 'pattern',
    }
    
    # Universal component patterns across languages
    UNIVERSAL_PATTERNS = {
        'programming': {
            'function': r'(function|def|func|fn|method|sub)\s+\w+',
            'class': r'(class|struct|interface|trait|type)\s+\w+',
            'api_endpoint': r'(get|post|put|delete|patch)\s*[\(\/]',
            'database_query': r'(select|insert|update|delete|create|drop)\s+',
            'validation': r'(validate|check|verify|ensure|assert)',
            'error_handling': r'(try|catch|except|error|throw|raise)',
            'authentication': r'(auth|login|signin|logout|signout|token|jwt)',
            'logging': r'(log|print|debug|info|warn|error)',
        },
        'template': {
            'form': r'form.*?(?:input|button|textarea|select)',
            'table': r'table.*?(?:tr|td|th|thead|tbody)',
            'navigation': r'nav|menu|header.*?(?:ul|li|a)',
            'card': r'(?:card|panel|tile|section)',
            'modal': r'modal|dialog|popup',
        },
        'styling': {
            'button': r'(?:btn|button).*\{',
            'form': r'(?:form|input|field).*\{',
            'layout': r'(?:flex|grid|display).*\{',
            'animation': r'(?:animation|transition|transform).*\{',
        },
        'data': {
            'schema': r'(?:schema|model|type).*\{',
            'config': r'(?:config|settings|options).*\{',
            'metadata': r'(?:meta|info|description).*\{',
        },
        'query': {
            'select_query': r'select.*from',
            'insert_query': r'insert.*into',
            'update_query': r'update.*set',
            'delete_query': r'delete.*from',
        },
        'infrastructure': {
            'service': r'(?:service|container|server)',
            'network': r'(?:network|port|expose)',
            'volume': r'(?:volume|mount|path)',
            'environment': r'(?:env|environment|arg)',
        },
        'build': {
            'target': r'(?:target|build|compile)',
            'dependency': r'(?:require|import|include)',
            'rule': r'(?:rule|recipe|command)',
        },
        'configuration': {
            'setting': r'(?:set|let|option|config)',
            'mapping': r'(?:map|keybind|shortcut)',
            'plugin': r'(?:plugin|extension|package)',
        },
        'pattern': {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'url': r'https?://[^\s]+',
            'phone': r'\+?[\d\s\-\(\)]+',
            'date': r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}',
        },
        'documentation': {
            'heading': r'^#+\s+',
            'code_block': r'```',
            'list': r'^\s*[-*+]\s+',
            'link': r'\[.*?\]\(.*?\)',
        }
    }
    
    def __init__(self):
        self.compiled_patterns = {}
        for family, patterns in self.UNIVERSAL_PATTERNS.items():
            self.compiled_patterns[family] = {
                comp_type: re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for comp_type, pattern in patterns.items()
            }
    
    def extract_universal_signature(self, code_block: CodeBlock) -> UniversalSignature | None:
        """Extract universal signature from any code block."""
        text = code_block.text
        language = self._detect_language(code_block.file)
        language_family = self.LANGUAGE_FAMILIES.get(language, 'programming')
        
        # Normalize code for structure comparison
        normalized = self._normalize_code(text, language)
        
        # Detect component type
        component_type = self._detect_component_type(text, language_family)
        
        # Extract semantic patterns
        semantic_patterns = self._extract_semantic_patterns(text, language_family)
        
        # Extract language-specific metadata
        metadata = self._extract_metadata(text, language)
        
        # Compute complexity score
        complexity_score = self._compute_complexity(text, language)
        
        return UniversalSignature(
            language_family=language_family,
            component_type=component_type,
            structure_hash=self._compute_structure_hash(normalized),
            semantic_patterns=semantic_patterns,
            metadata=metadata,
            complexity_score=complexity_score
        )
    
    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        from redup.core.ts_extractor import _LANGUAGE_MAPPING
        
        file_ext = Path(file_path).suffix.lower()
        return _LANGUAGE_MAPPING.get(file_ext, 'unknown')
    
    def _normalize_code(self, code: str, language: str) -> str:
        """Normalize code for structure comparison."""
        # Remove comments
        code = self._remove_comments(code, language)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code).strip()
        
        # Normalize string literals
        code = re.sub(r'["\'][^"\']*["\']', 'STRING_LITERAL', code)
        
        # Normalize numbers
        code = re.sub(r'\b\d+\.?\d*\b', 'NUMBER', code)
        
        # Normalize identifiers (language-specific)
        code = self._normalize_identifiers(code, language)
        
        return code
    
    def _remove_comments(self, code: str, language: str) -> str:
        """Remove comments based on language."""
        comment_patterns = {
            'javascript': r'//.*?$|/\*.*?\*/',
            'typescript': r'//.*?$|/\*.*?\*/',
            'python': r'#.*?$|""".*?"""',
            'java': r'//.*?$|/\*.*?\*/',
            'c': r'//.*?$|/\*.*?\*/',
            'cpp': r'//.*?$|/\*.*?\*/',
            'c_sharp': r'//.*?$|/\*.*?\*/',
            'rust': r'//.*?$|/\*.*?\*/',
            'go': r'//.*?$|/\*.*?\*/',
            'ruby': r'#.*?$',
            'php': r'//.*?$|/\*.*?\*/|#.*?$',
            'bash': r'#.*?$',
            'lua': r'--.*?$|--\[\[.*?\]\]',
            'sql': r'--.*?$|/\*.*?\*/',
            'html': r'<!--.*?-->',
            'css': r'/\*.*?\*/',
            'yaml': r'#.*?$',
            'dockerfile': r'#.*?$',
            'make': r'#.*?$',
            'nginx': r'#.*?$',
            'vim': r'".*?$',
        }
        
        pattern = comment_patterns.get(language, r'#.*?$|//.*?$|/\*.*?\*/')
        return re.sub(pattern, '', code, flags=re.MULTILINE | re.DOTALL)
    
    def _normalize_identifiers(self, code: str, language: str) -> str:
        """Normalize identifiers based on language conventions."""
        if language in ['javascript', 'typescript', 'java', 'c', 'cpp', 'c_sharp']:
            # CamelCase and snake_case normalization
            code = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', 'IDENTIFIER', code)
        elif language == 'python':
            # snake_case normalization
            code = re.sub(r'\b[a-z_][a-z0-9_]*\b', 'IDENTIFIER', code)
            # CamelCase for classes
            code = re.sub(r'\b[A-Z][a-zA-Z0-9]*\b', 'CLASS_IDENTIFIER', code)
        elif language in ['html', 'xml']:
            # Tag normalization
            code = re.sub(r'<(/?)(\w+)', r'<\1TAG', code)
        elif language == 'css':
            # Selector normalization
            code = re.sub(r'[.#]?[\w-]+', 'SELECTOR', code)
        
        return code
    
    def _detect_component_type(self, code: str, language_family: str) -> str:
        """Detect component type using universal patterns."""
        patterns = self.compiled_patterns.get(language_family, {})
        
        for comp_type, pattern in patterns.items():
            if pattern.search(code):
                return comp_type
        
        return 'unknown'
    
    def _extract_semantic_patterns(self, code: str, language_family: str) -> list[str]:
        """Extract semantic patterns from code."""
        patterns = self.compiled_patterns.get(language_family, {})
        found_patterns = []
        
        for comp_type, pattern in patterns.items():
            matches = pattern.findall(code)
            if matches:
                found_patterns.append(comp_type)
        
        return found_patterns
    
    def _extract_metadata(self, code: str, language: str) -> dict[str, str]:
        """Extract language-specific metadata."""
        metadata = {}
        
        # Extract function names for programming languages
        if language in ['javascript', 'typescript', 'python', 'java', 'c', 'cpp', 'c_sharp', 'rust', 'go']:
            func_matches = re.findall(r'(?:function|def|func|fn)\s+(\w+)', code, re.IGNORECASE)
            if func_matches:
                metadata['functions'] = ','.join(func_matches[:5])  # Limit to first 5
        
        # Extract class names
        if language in ['javascript', 'typescript', 'python', 'java', 'c', 'cpp', 'c_sharp', 'rust']:
            class_matches = re.findall(r'(?:class|struct|interface|trait)\s+(\w+)', code, re.IGNORECASE)
            if class_matches:
                metadata['classes'] = ','.join(class_matches[:5])
        
        # Extract selectors for CSS
        if language == 'css':
            selector_matches = re.findall(r'([.#]?[\w-]+)\s*{', code)
            if selector_matches:
                metadata['selectors'] = ','.join(selector_matches[:5])
        
        # Extract tags for HTML
        if language in ['html', 'xml']:
            tag_matches = re.findall(r'<(\w+)', code)
            if tag_matches:
                metadata['tags'] = ','.join(set(tag_matches[:10]))
        
        # Extract keys for data formats
        if language in ['json', 'yaml', 'toml']:
            key_matches = re.findall(r'["\']?(\w+)["\']?\s*:', code)
            if key_matches:
                metadata['keys'] = ','.join(key_matches[:5])
        
        return metadata
    
    def _compute_complexity(self, code: str, language: str) -> float:
        """Compute complexity score for the code block."""
        # Simple complexity metrics
        lines = len(code.splitlines())
        chars = len(code)
        
        # Count control structures
        control_patterns = r'\b(if|else|for|while|switch|case|try|catch|except|return)\b'
        control_count = len(re.findall(control_patterns, code, re.IGNORECASE))
        
        # Count nested structures (approximation)
        nesting = code.count('{') + code.count('(') + code.count('[')
        
        # Normalize complexity (0.0 to 1.0)
        complexity = min(1.0, (lines / 100.0 + control_count / 20.0 + nesting / 50.0) / 3.0)
        
        return complexity
    
    def _compute_structure_hash(self, normalized_code: str) -> str:
        """Compute structure hash for normalized code."""
        return str(hash(normalized_code))


class UniversalFuzzyDetector:
    """Universal fuzzy similarity detector for all languages and DSLs."""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.extractor = UniversalFuzzyExtractor()
        
        # Initialize LSH for efficient similarity search
        if MinHash is not None:
            self.lsh = MinHashLSH(threshold=similarity_threshold)
        else:
            self.lsh = None
    
    def find_similar_components(self, code_blocks: list[CodeBlock]) -> list[tuple[CodeBlock, CodeBlock, float]]:
        """Find similar components across all languages and DSLs."""
        # Extract signatures for all blocks
        signatures = []
        for block in code_blocks:
            signature = self.extractor.extract_universal_signature(block)
            if signature:
                signatures.append((block, signature))
        
        # Find similar pairs
        similar_pairs = []
        for i, (block1, sig1) in enumerate(signatures):
            for block2, sig2 in signatures[i+1:]:
                similarity = self._compute_universal_similarity(sig1, sig2)
                if similarity >= self.similarity_threshold:
                    similar_pairs.append((block1, block2, similarity))
        
        return similar_pairs
    
    def _compute_universal_similarity(self, sig1: UniversalSignature, sig2: UniversalSignature) -> float:
        """Compute similarity between two universal signatures."""
        # Start with base similarity
        similarity = 0.0
        
        # Same component type gives base similarity
        if sig1.component_type == sig2.component_type:
            similarity += 0.3
        
        # Same language family gives additional similarity
        if sig1.language_family == sig2.language_family:
            similarity += 0.2
        
        # Structure similarity
        if sig1.structure_hash == sig2.structure_hash:
            similarity += 0.3
        
        # Semantic pattern similarity
        pattern_similarity = self._compute_pattern_similarity(sig1.semantic_patterns, sig2.semantic_patterns)
        similarity += 0.1 * pattern_similarity
        
        # Metadata similarity
        metadata_similarity = self._compute_metadata_similarity(sig1.metadata, sig2.metadata)
        similarity += 0.1 * metadata_similarity
        
        return min(similarity, 1.0)
    
    def _compute_pattern_similarity(self, patterns1: list[str], patterns2: list[str]) -> float:
        """Compute similarity between semantic patterns."""
        if not patterns1 and not patterns2:
            return 1.0
        if not patterns1 or not patterns2:
            return 0.0
        
        # Jaccard similarity
        set1, set2 = set(patterns1), set(patterns2)
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _compute_metadata_similarity(self, meta1: dict[str, str], meta2: dict[str, str]) -> float:
        """Compute similarity between metadata dictionaries."""
        if not meta1 and not meta2:
            return 1.0
        if not meta1 or not meta2:
            return 0.0
        
        # Jaccard similarity on keys
        keys1, keys2 = set(meta1.keys()), set(meta2.keys())
        intersection = keys1 & keys2
        union = keys1 | keys2
        
        if not union:
            return 1.0
        
        key_similarity = len(intersection) / len(union)
        
        # Value similarity for matching keys
        value_similarities = []
        for key in intersection:
            val1, val2 = meta1[key], meta2[key]
            if val1 == val2:
                value_similarities.append(1.0)
            elif fuzz is not None:
                value_similarities.append(fuzz.ratio(val1, val2) / 100.0)
            else:
                value_similarities.append(0.0)
        
        if value_similarities:
            value_similarity = sum(value_similarities) / len(value_similarities)
            return (key_similarity + value_similarity) / 2.0
        
        return key_similarity
