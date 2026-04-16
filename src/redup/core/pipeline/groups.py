"""Group creation, deduplication, and matching utilities."""

from __future__ import annotations

from redup.core.hasher import HashedBlock
from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType
from redup.core.matcher import MatchResult


def blocks_to_group(
    group_id: str,
    blocks: list[HashedBlock],
    dup_type: DuplicateType,
    similarity: float = 1.0,
    normalized_hash: str = "",
) -> DuplicateGroup:
    """Convert a list of hashed blocks into a DuplicateGroup."""
    seen: set[tuple[str, int]] = set()
    fragments: list[DuplicateFragment] = []

    for hb in blocks:
        block = hb.block
        key = (block.file, block.line_start)
        if key in seen:
            continue
        seen.add(key)
        fragments.append(
            DuplicateFragment(
                file=block.file,
                line_start=block.line_start,
                line_end=block.line_end,
                text=block.text,
                function_name=block.function_name,
                class_name=block.class_name,
            )
        )

    if len(fragments) < 2:
        return DuplicateGroup(id=group_id, duplicate_type=dup_type)

    name = fragments[0].function_name if fragments[0].function_name else None

    return DuplicateGroup(
        id=group_id,
        duplicate_type=dup_type,
        fragments=fragments,
        similarity_score=similarity,
        normalized_hash=normalized_hash,
        normalized_name=name,
    )


def deduplicate_groups(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
    """Remove groups that are subsets of larger groups."""
    if not groups:
        return groups

    # Sort by impact (largest first)
    sorted_groups = sorted(groups, key=lambda g: g.impact_score, reverse=True)
    kept: list[DuplicateGroup] = []
    seen_locations: set[tuple[str, int, int]] = set()

    for group in sorted_groups:
        if group.occurrences < 2:
            continue

        # Check if this group's fragments are already covered
        locations = {
            (f.file, f.line_start, f.line_end)
            for f in group.fragments
        }
        new_locations = locations - seen_locations

        if len(new_locations) >= 2:
            kept.append(group)
            seen_locations.update(locations)

    return kept


def match_results_to_blocks(matches: list[MatchResult]) -> list[HashedBlock]:
    """Flatten a list of pairwise matches into unique hashed blocks."""
    seen: set[tuple[str, int]] = set()
    blocks: list[HashedBlock] = []

    for match in matches:
        for candidate in (match.block_a, match.block_b):
            key = (candidate.block.file, candidate.block.line_start)
            if key in seen:
                continue
            seen.add(key)
            blocks.append(candidate)

    return blocks


def calculate_similarity(matches: list[MatchResult]) -> float:
    """Calculate similarity score for a group of pairwise matches."""
    if not matches:
        return 1.0

    return sum(match.similarity for match in matches) / len(matches)
