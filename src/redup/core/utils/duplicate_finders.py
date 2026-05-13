"""Consolidated duplicate finding utilities to eliminate thin wrapper duplication."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..hasher import HashedBlock, HashIndex


def create_duplicate_finder(
    hash_type: str,
) -> Callable[["HashIndex"], "dict[str, list[HashedBlock]]"]:
    """
    Factory function to create duplicate finders for different hash types.

    Args:
        hash_type: Either 'exact' or 'structural'

    Returns:
        Function that finds duplicates of the specified type
    """

    def find_duplicates(index: "HashIndex") -> "dict[str, list[HashedBlock]]":
        """Find groups of blocks with identical {hash_type} text."""
        from ..hasher import _find_duplicates

        hash_dict = getattr(index, hash_type)
        return _find_duplicates(hash_dict)

    # Set appropriate docstring based on hash type
    if hash_type == "exact":
        find_duplicates.__doc__ = "Find groups of blocks with identical normalized text."
    elif hash_type == "structural":
        find_duplicates.__doc__ = (
            "Find groups of blocks with identical structure (names may differ)."
        )

    return find_duplicates


# Pre-configured finders for backward compatibility
find_exact_duplicates = create_duplicate_finder("exact")
find_structural_duplicates = create_duplicate_finder("structural")
