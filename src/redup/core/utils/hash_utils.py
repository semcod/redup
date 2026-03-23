"""Consolidated hashing utilities to eliminate thin wrapper duplication."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..hasher import _hash_text, _normalize_text, _normalize_ast_text


def create_hash_function(normalizer: Callable[[str], str]) -> Callable[[str], str]:
    """
    Factory function to create hash functions with different normalizers.
    
    Args:
        normalizer: Function to normalize text before hashing
        
    Returns:
        Function that hashes normalized text
    """
    def hash_function(text: str) -> str:
        """SHA-256 hash of normalized text."""
        from ..hasher import _hash_text
        return _hash_text(text, normalizer)
    
    # Set appropriate docstring based on normalizer
    from ..hasher import _normalize_text, _normalize_ast_text
    if normalizer == _normalize_text:
        hash_function.__doc__ = "SHA-256 hash of normalized text."
    elif normalizer == _normalize_ast_text:
        hash_function.__doc__ = "SHA-256 hash of deeply normalized text (variable names replaced)."
    
    return hash_function


# Pre-configured hash functions for backward compatibility
from ..hasher import _normalize_text, _normalize_ast_text
hash_block = create_hash_function(_normalize_text)
hash_block_structural = create_hash_function(_normalize_ast_text)
