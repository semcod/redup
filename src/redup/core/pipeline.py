"""Pipeline — orchestrates scan → hash → match → group → plan."""

from __future__ import annotations

from redup.core.hasher import (
    HashedBlock,
    build_hash_index,
    find_exact_duplicates,
    find_structural_duplicates,
)
from redup.core.matcher import refine_structural_matches
from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    ScanConfig,
)
from redup.core.planner import generate_suggestions
from redup.core.scanner import CodeBlock, scan_project


def _blocks_to_group(
    group_id: str,
    blocks: list[HashedBlock],
    dup_type: DuplicateType,
    similarity: float = 1.0,
    normalized_hash: str = "",
) -> DuplicateGroup:
    """Convert a list of hashed blocks into a DuplicateGroup."""
    # Deduplicate by file+line
    seen: set[tuple[str, int]] = set()
    fragments: list[DuplicateFragment] = []

    for hb in blocks:
        key = (hb.block.file, hb.block.line_start)
        if key in seen:
            continue
        seen.add(key)
        fragments.append(
            DuplicateFragment(
                file=hb.block.file,
                line_start=hb.block.line_start,
                line_end=hb.block.line_end,
                text=hb.block.text,
                function_name=hb.block.function_name,
                class_name=hb.block.class_name,
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


def _deduplicate_groups(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
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


def analyze(
    config: ScanConfig | None = None,
    function_level_only: bool = False,
) -> DuplicationMap:
    """Run the full reDUP analysis pipeline.

    Args:
        config: Scan configuration. Defaults to current directory, .py files.
        function_level_only: If True, only analyze function-level blocks
            (skip sliding-window line blocks). Faster but misses inline duplicates.

    Returns:
        A DuplicationMap with all duplicate groups and refactoring suggestions.
    """
    if config is None:
        config = ScanConfig()

    # Phase 1: Scan
    scanned_files, stats = scan_project(config)

    # Collect blocks
    all_blocks: list[CodeBlock] = []
    for sf in scanned_files:
        for block in sf.blocks:
            if function_level_only and block.function_name is None:
                continue
            all_blocks.append(block)

    # Phase 2: Hash
    index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Phase 3: Find candidates
    groups: list[DuplicateGroup] = []
    group_counter = 0

    # 3a: Exact duplicates
    exact_groups = find_exact_duplicates(index)
    for h, blocks in exact_groups.items():
        # Only keep function-level exact matches (skip noisy line blocks)
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            group_counter += 1
            g = _blocks_to_group(
                group_id=f"E{group_counter:04d}",
                blocks=func_blocks,
                dup_type=DuplicateType.EXACT,
                normalized_hash=h,
            )
            if g.occurrences >= 2:
                groups.append(g)

    # 3b: Structural duplicates (not already found as exact)
    exact_hashes = set(exact_groups.keys())
    structural_groups = find_structural_duplicates(index)
    for h, blocks in structural_groups.items():
        # Skip if all blocks are already in an exact group
        if all(b.exact_hash in exact_hashes for b in blocks):
            continue

        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            matches = refine_structural_matches(func_blocks, config.min_similarity)
            if matches:
                group_counter += 1
                avg_sim = sum(m.similarity for m in matches) / len(matches)
                g = _blocks_to_group(
                    group_id=f"S{group_counter:04d}",
                    blocks=func_blocks,
                    dup_type=DuplicateType.STRUCTURAL,
                    similarity=avg_sim,
                    normalized_hash=h,
                )
                if g.occurrences >= 2:
                    groups.append(g)

    # Phase 4: Deduplicate overlapping groups
    groups = _deduplicate_groups(groups)

    # Phase 5: Build map and plan
    dup_map = DuplicationMap(
        project_path=str(config.root.resolve()),
        config=config,
        groups=groups,
        stats=stats,
    )

    # Phase 6: Generate suggestions
    dup_map.suggestions = generate_suggestions(dup_map)

    return dup_map
