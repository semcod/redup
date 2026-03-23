"""Fuzzy similarity detection for HTML/CSS components.

This module provides fuzzy matching capabilities for HTML/CSS code,
enabling detection of similar functionality despite different implementations.
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

# Fast fuzzy matching with fallback
try:
    from rapidfuzz import fuzz as _rfuzz
    def _text_ratio(a: str, b: str) -> float:
        return _rfuzz.ratio(a, b) / 100.0
    def _partial_ratio(a: str, b: str) -> float:
        return _rfuzz.partial_ratio(a, b) / 100.0
    def _token_sort_ratio(a: str, b: str) -> float:
        return _rfuzz.token_sort_ratio(a, b) / 100.0
except ImportError:
    from difflib import SequenceMatcher
    def _text_ratio(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()
    _partial_ratio = _text_ratio
    _token_sort_ratio = _text_ratio

from redup.core.scanner import CodeBlock


@dataclass
class ComponentSignature:
    """Semantic signature of a component for fuzzy matching."""
    
    component_type: str  # 'form', 'button', 'card', 'navigation', etc.
    structure_hash: str  # Normalized structure fingerprint
    attributes: dict[str, str]  # Key attributes (type, class patterns)
    text_content: str  # Normalized text content
    css_properties: dict[str, str]  # For CSS components


class HTMLComponentExtractor:
    """Extract HTML components with semantic normalization for fuzzy matching."""
    
    # Component type patterns
    COMPONENT_PATTERNS = {
        'form': r'form.*?(?:input|button|textarea|select)',
        'button': r'button|input.*type.*=.*["\']submit["\']|input.*type.*=.*["\']button["\']',
        'card': r'(?:(?:card|panel|tile|section).*?(?:header|body|footer)|div.*class.*(?:card|panel|tile))',
        'navigation': r'nav|navigation|navbar|menu.*?(?:ul|li|a)',
        'table': r'table.*?(?:tr|td|th|thead|tbody)',
        'list': r'ul|ol.*li',
        'modal': r'modal|dialog|popup.*?(?:overlay|backdrop)',
        'header': r'header|head.*?(?:nav|logo|menu)',
        'footer': r'footer.*?(?:link|copyright|contact)',
    }
    
    def __init__(self):
        self.compiled_patterns = {
            comp_type: re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for comp_type, pattern in self.COMPONENT_PATTERNS.items()
        }
    
    def extract_component_signature(self, code_block: CodeBlock) -> ComponentSignature | None:
        """Extract semantic signature from HTML code block."""
        text = code_block.text
        
        # Normalize HTML: remove IDs, normalize classes, extract structure
        normalized = self._normalize_html(text)
        
        # Detect component type
        component_type = self._detect_component_type(text)
        if not component_type:
            return None
        
        # Extract key attributes
        attributes = self._extract_attributes(text)
        
        # Extract text content (normalized)
        text_content = self._extract_text_content(text)
        
        return ComponentSignature(
            component_type=component_type,
            structure_hash=self._compute_structure_hash(normalized),
            attributes=attributes,
            text_content=text_content,
            css_properties={}  # HTML blocks don't have CSS properties
        )
    
    def _normalize_html(self, html: str) -> str:
        """Normalize HTML for structure comparison."""
        # Remove specific IDs
        html = re.sub(r'id\s*=\s*["\'][^"\']+["\']', '', html)
        
        # Normalize class names to patterns (btn-primary -> btn-*)
        html = re.sub(r'class\s*=\s*["\']([^"\']+)["\']', 
                     lambda m: f'class="{self._normalize_class_name(m.group(1))}"', html)
        
        # Remove whitespace between tags
        html = re.sub(r'>\s+<', '><', html)
        
        # Normalize attribute order
        html = re.sub(r'(\w+)\s*=\s*["\']([^"\']*)["\']', r'\1="\2"', html)
        
        return html.strip()
    
    def _normalize_class_name(self, class_str: str) -> str:
        """Normalize class names to patterns."""
        classes = class_str.split()
        normalized = []
        
        for cls in classes:
            # Convert specific variants to patterns
            if cls.startswith('btn-'):
                normalized.append('btn-*')
            elif cls.startswith('form-'):
                normalized.append('form-*')
            elif cls.startswith('card-'):
                normalized.append('card-*')
            elif cls.startswith('nav-'):
                normalized.append('nav-*')
            elif cls in ['primary', 'secondary', 'success', 'danger', 'warning', 'info']:
                normalized.append('*-variant')
            else:
                normalized.append(cls)
        
        return ' '.join(normalized)
    
    def _detect_component_type(self, html: str) -> str | None:
        """Detect the semantic type of HTML component."""
        for comp_type, pattern in self.compiled_patterns.items():
            if pattern.search(html):
                return comp_type
        return None
    
    def _extract_attributes(self, html: str) -> dict[str, str]:
        """Extract key attributes for comparison."""
        attributes = {}
        
        # Extract input types
        input_types = re.findall(r'input[^>]*type\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if input_types:
            attributes['input_types'] = ','.join(sorted(set(input_types)))
        
        # Extract form methods
        form_method = re.search(r'form[^>]*method\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if form_method:
            attributes['form_method'] = form_method.group(1).lower()
        
        # Extract button types
        button_types = re.findall(r'(?:button|input)[^>]*type\s*=\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if button_types:
            attributes['button_types'] = ','.join(sorted(set(button_types)))
        
        return attributes
    
    def _extract_text_content(self, html: str) -> str:
        """Extract and normalize text content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Convert to lowercase for comparison
        return text.lower()
    
    def _compute_structure_hash(self, normalized_html: str) -> str:
        """Compute structure hash for normalized HTML."""
        # Simple hash based on tag sequence
        tags = re.findall(r'<(/?)(\w+)', normalized_html)
        tag_sequence = ''.join(f"{open_tag}{tag}" for open_tag, tag in tags)
        return str(hash(tag_sequence))


class CSSComponentExtractor:
    """Extract CSS components with semantic normalization for fuzzy matching."""
    
    # CSS property normalization patterns
    PROPERTY_PATTERNS = {
        'colors': r'(?:color|background-color|border-color)\s*:\s*([^;]+)',
        'spacing': r'(?:margin|padding)\s*:\s*([^;]+)',
        'sizes': r'(?:width|height|font-size)\s*:\s*([^;]+)',
        'positioning': r'(?:position|display|float|clear)\s*:\s*([^;]+)',
        'borders': r'border\s*:\s*([^;]+)',
    }
    
    def __init__(self):
        self.compiled_patterns = {
            prop_type: re.compile(pattern, re.IGNORECASE)
            for prop_type, pattern in self.PROPERTY_PATTERNS.items()
        }
    
    def extract_component_signature(self, code_block: CodeBlock) -> ComponentSignature | None:
        """Extract semantic signature from CSS code block."""
        text = code_block.text
        
        # Extract CSS properties
        css_properties = self._extract_css_properties(text)
        
        # Detect component type from selector
        component_type = self._detect_css_component_type(text)
        if not component_type:
            component_type = 'style_rule'
        
        return ComponentSignature(
            component_type=component_type,
            structure_hash=self._compute_css_hash(css_properties),
            attributes={},  # CSS rules don't have HTML attributes
            text_content='',  # CSS rules don't have text content
            css_properties=css_properties
        )
    
    def _extract_css_properties(self, css: str) -> dict[str, str]:
        """Extract and normalize CSS properties."""
        properties = {}
        
        for prop_type, pattern in self.compiled_patterns.items():
            matches = pattern.findall(css)
            if matches:
                # Normalize property values
                normalized_values = [self._normalize_css_value(val) for val in matches]
                properties[prop_type] = ','.join(normalized_values)
        
        return properties
    
    def _normalize_css_value(self, value: str) -> str:
        """Normalize CSS property values for fuzzy comparison."""
        value = value.strip().lower()
        
        # Normalize colors (hex to rgb approximation)
        hex_color = re.search(r'#([0-9a-f]{6}|[0-9a-f]{3})', value)
        if hex_color:
            # For fuzzy matching, we could group similar colors
            value = re.sub(r'#[0-9a-f]{6}', 'color-hex', value)
            value = re.sub(r'#[0-9a-f]{3}', 'color-hex', value)
        
        # Normalize sizes (group similar values)
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(px|em|rem|%|pt)', value)
        if size_match:
            size, unit = size_match.groups()
            size_float = float(size)
            
            # Group sizes into ranges for fuzzy matching
            if unit == 'px':
                if size_float < 5:
                    value = re.sub(r'\d+px', 'size-xs', value)
                elif size_float < 10:
                    value = re.sub(r'\d+px', 'size-sm', value)
                elif size_float < 20:
                    value = re.sub(r'\d+px', 'size-md', value)
                elif size_float < 50:
                    value = re.sub(r'\d+px', 'size-lg', value)
                else:
                    value = re.sub(r'\d+px', 'size-xl', value)
        
        return value
    
    def _detect_css_component_type(self, css: str) -> str | None:
        """Detect component type from CSS selector and properties."""
        selector_match = re.search(r'([^{]+)', css)
        if selector_match:
            selector = selector_match.group(1).strip()
            
            # Common component patterns in CSS
            if any(pattern in selector.lower() for pattern in ['btn', 'button']):
                return 'button'
            elif any(pattern in selector.lower() for pattern in ['form', 'input', 'field']):
                return 'form'
            elif any(pattern in selector.lower() for pattern in ['card', 'panel', 'tile']):
                return 'card'
            elif any(pattern in selector.lower() for pattern in ['nav', 'menu']):
                return 'navigation'
        
        return None
    
    def _compute_css_hash(self, properties: dict[str, str]) -> str:
        """Compute hash for CSS properties."""
        prop_string = '|'.join(f"{k}:{v}" for k, v in sorted(properties.items()))
        return str(hash(prop_string))


class FuzzySimilarityDetector:
    """Detect fuzzy similarity between HTML/CSS components."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.html_extractor = HTMLComponentExtractor()
        self.css_extractor = CSSComponentExtractor()
        
        # Initialize LSH for efficient similarity search
        if MinHash is not None:
            self.lsh = MinHashLSH(threshold=similarity_threshold)
        else:
            self.lsh = None
    
    def find_similar_components(self, code_blocks: list[CodeBlock]) -> list[tuple[CodeBlock, CodeBlock, float]]:
        """Find similar components among code blocks."""
        # Extract signatures for all blocks
        signatures = []
        for block in code_blocks:
            signature = self._extract_signature(block)
            if signature:
                signatures.append((block, signature))
        
        # Find similar pairs
        similar_pairs = []
        for i, (block1, sig1) in enumerate(signatures):
            for block2, sig2 in signatures[i+1:]:
                similarity = self._compute_similarity(sig1, sig2)
                if similarity >= self.similarity_threshold:
                    similar_pairs.append((block1, block2, similarity))
        
        return similar_pairs
    
    def _extract_signature(self, block: CodeBlock) -> ComponentSignature | None:
        """Extract component signature based on file type."""
        file_ext = Path(block.file).suffix.lower()
        
        if file_ext in ['.html', '.htm', '.xhtml']:
            return self.html_extractor.extract_component_signature(block)
        elif file_ext in ['.css', '.scss', '.sass', '.less']:
            return self.css_extractor.extract_component_signature(block)
        else:
            # Try universal fuzzy extractor for other languages
            try:
                from redup.core.universal_fuzzy import UniversalFuzzyExtractor
                universal_extractor = UniversalFuzzyExtractor()
                universal_sig = universal_extractor.extract_universal_signature(block)
                if universal_sig:
                    # Convert universal signature to component signature for compatibility
                    return ComponentSignature(
                        component_type=universal_sig.component_type,
                        structure_hash=universal_sig.structure_hash,
                        attributes=universal_sig.metadata,
                        text_content='',
                        css_properties={}
                    )
            except ImportError:
                pass
        
        return None
    
    def _compute_similarity(self, sig1: ComponentSignature, sig2: ComponentSignature) -> float:
        """Compute similarity between two component signatures."""
        # Different component types can't be similar
        if sig1.component_type != sig2.component_type:
            return 0.0
        
        # Start with base similarity for same component type
        similarity = 0.5
        
        # Structure similarity
        if sig1.structure_hash == sig2.structure_hash:
            similarity += 0.3
        
        # Attribute similarity
        attr_similarity = self._compute_attribute_similarity(sig1.attributes, sig2.attributes)
        similarity += 0.1 * attr_similarity
        
        # Text content similarity (for HTML)
        if sig1.text_content and sig2.text_content:
            text_similarity = _text_ratio(sig1.text_content, sig2.text_content)
            similarity += 0.1 * text_similarity
        
        # CSS properties similarity (for CSS)
        if sig1.css_properties and sig2.css_properties:
            css_similarity = self._compute_css_similarity(sig1.css_properties, sig2.css_properties)
            similarity += 0.1 * css_similarity
        
        return min(similarity, 1.0)
    
    def _compute_attribute_similarity(self, attrs1: dict[str, str], attrs2: dict[str, str]) -> float:
        """Compute similarity between attribute dictionaries."""
        if not attrs1 and not attrs2:
            return 1.0
        if not attrs1 or not attrs2:
            return 0.0
        
        # Jaccard similarity on attribute keys
        keys1 = set(attrs1.keys())
        keys2 = set(attrs2.keys())
        intersection = keys1 & keys2
        union = keys1 | keys2
        
        if not union:
            return 1.0
        
        key_similarity = len(intersection) / len(union)
        
        # Value similarity for matching keys
        value_similarities = []
        for key in intersection:
            val1, val2 = attrs1[key], attrs2[key]
            if val1 == val2:
                value_similarities.append(1.0)
            else:
                value_similarities.append(_text_ratio(val1, val2))
        
        if value_similarities:
            value_similarity = sum(value_similarities) / len(value_similarities)
            return (key_similarity + value_similarity) / 2.0
        
        return key_similarity
    
    def _compute_css_similarity(self, css1: dict[str, str], css2: dict[str, str]) -> float:
        """Compute similarity between CSS property dictionaries."""
        return self._compute_attribute_similarity(css1, css2)
