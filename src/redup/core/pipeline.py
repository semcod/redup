"""Pipeline — orchestrates scan → hash → match → group → plan."""

from __future__ import annotations

from redup.core.hasher import (
    HashedBlock,
    HashIndex,
    build_hash_index,
    find_exact_duplicates,
    find_structural_duplicates,
)
from redup.core.lsh_matcher import find_near_duplicates
from redup.core.matcher import MatchResult, refine_structural_matches
from redup.core.parallel_scanner import scan_project_parallel
from redup.core.models import (
    DuplicateFragment,
    DuplicateGroup,
    DuplicateType,
    DuplicationMap,
    ScanConfig,
    ScanStats,
)
from redup.core.planner import generate_suggestions
from redup.core.scanner import CodeBlock, ScannedFile, scan_project


def _blocks_to_group(
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
    config = _ensure_config(config)

    # Phase 1: Scan
    scanned_files, stats = _scan_phase(config)

    # Phase 2: Process blocks
    all_blocks = _process_blocks(scanned_files, function_level_only)

    # Phase 3: Hash and find duplicates
    groups = _find_duplicates_phase(all_blocks, config)

    # Phase 4: Deduplicate and suggest
    final_groups = _deduplicate_phase(groups)

    dup_map = DuplicationMap(
        project_path=config.root.as_posix(),
        config=config,
        stats=stats,
        groups=final_groups,
    )
    dup_map.suggestions = generate_suggestions(dup_map)

    return dup_map


def _ensure_config(config: ScanConfig | None) -> ScanConfig:
    """Ensure we have a valid configuration."""
    return config or ScanConfig()


def _scan_phase(config: ScanConfig) -> tuple[list[ScannedFile], ScanStats]:
    """Phase 1: Scan project files."""
    return scan_project(config)


def _scan_phase_parallel(config: ScanConfig, max_workers: int | None = None) -> tuple[list[ScannedFile], ScanStats]:
    """Phase 1: Scan project files in parallel."""
    return scan_project_parallel(
        root=config.root,
        extensions=config.extensions,
        exclude_patterns=config.exclude_patterns,
        include_tests=config.include_tests,
        function_level_only=True,  # Always function-level for parallel
        max_file_size=config.max_file_size_kb,
        max_workers=max_workers,
    )


def _process_blocks(
    scanned_files: list[ScannedFile],
    function_level_only: bool
) -> list[CodeBlock]:
    """Phase 2: Extract and filter code blocks."""
    all_blocks: list[CodeBlock] = []
    for sf in scanned_files:
        for block in sf.blocks:
            if function_level_only and block.function_name is None:
                continue
            all_blocks.append(block)
    return all_blocks


def _find_duplicates_phase(
    all_blocks: list[CodeBlock],
    config: ScanConfig
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicate groups."""
    index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Find exact duplicates
    exact_groups = _find_exact_groups(index)

    # Find structural duplicates
    structural_groups = _find_structural_groups(index, exact_groups)
    
    # Find near-duplicates using LSH (for larger blocks)
    near_duplicate_groups = _find_near_duplicate_groups(all_blocks, config)

    return exact_groups + structural_groups + near_duplicate_groups


def _find_exact_groups(index: HashIndex) -> list[DuplicateGroup]:
    """Find exact duplicate groups."""
    groups: list[DuplicateGroup] = []
    exact_groups = find_exact_duplicates(index)

    for i, (h, blocks) in enumerate(exact_groups.items(), 1):
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            g = _blocks_to_group(
                group_id=f"E{i:04d}",
                blocks=func_blocks,
                dup_type=DuplicateType.EXACT,
                normalized_hash=h,
            )
            if g.occurrences >= 2:
                groups.append(g)

    return groups


def _find_structural_groups(
    index: HashIndex,
    exact_groups_list: list[DuplicateGroup]
) -> list[DuplicateGroup]:
    """Find structural duplicate groups."""
    groups: list[DuplicateGroup] = []
    exact_hashes: set[str] = set()
    for group in exact_groups_list:
        exact_hashes.add(group.normalized_hash)

    structural_groups = find_structural_duplicates(index)

    for i, (h, blocks) in enumerate(structural_groups.items(), 1):
        if h in exact_hashes:
            continue

        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            refined = refine_structural_matches(func_blocks)
            refined_blocks = _match_results_to_blocks(refined)
            if len(refined_blocks) >= 2:
                g = _blocks_to_group(
                    group_id=f"S{i:04d}",
                    blocks=refined_blocks,
                    dup_type=DuplicateType.STRUCTURAL,
                    normalized_hash=h,
                    similarity=_calculate_similarity(refined),
                )
                if g.occurrences >= 2:
                    groups.append(g)

    return groups


def _deduplicate_phase(groups: list[DuplicateGroup]) -> list[DuplicateGroup]:
    """Phase 4: Remove overlapping groups."""
    return _deduplicate_groups(groups)


def _match_results_to_blocks(matches: list[MatchResult]) -> list[HashedBlock]:
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


def _calculate_similarity(matches: list[MatchResult]) -> float:
    """Calculate similarity score for a group of pairwise matches."""
    if not matches:
        return 1.0

    return sum(match.similarity for match in matches) / len(matches)


def _find_near_duplicate_groups(
    all_blocks: list[CodeBlock],
    config: ScanConfig
) -> list[DuplicateGroup]:
    """Find near-duplicate groups using LSH."""
    groups: list[DuplicateGroup] = []
    
    # Check if LSH is enabled
    if not getattr(config, 'lsh_enabled', True):
        return groups
    
    # Only use LSH for blocks larger than configured threshold
    lsh_min_lines = getattr(config, 'lsh_min_lines', 50)
    lsh_threshold = getattr(config, 'lsh_threshold', 0.8)
    
    # Filter blocks for LSH
    lsh_blocks = [b for b in all_blocks if b.line_count >= lsh_min_lines]
    
    if not lsh_blocks:
        return groups
    
    try:
        # Find near-duplicates
        near_dup_groups = find_near_duplicates(
            lsh_blocks, 
            threshold=lsh_threshold, 
            min_lines=lsh_min_lines
        )
        
        for i, (group_id, block_similarities) in enumerate(near_dup_groups.items(), 1):
            if len(block_similarities) < 2:
                continue
            
            # Convert to DuplicateGroup format
            fragments = []
            avg_similarity = 0.0
            
            for block, similarity in block_similarities:
                fragments.append(DuplicateFragment(
                    file=block.file,
                    line_start=block.line_start,
                    line_end=block.line_end,
                    text=block.text,
                    function_name=block.function_name,
                    class_name=block.class_name,
                ))
                avg_similarity += similarity
            
            if len(fragments) >= 2:
                avg_similarity /= len(fragments)
                
                # Use function name if available
                name = fragments[0].function_name if fragments[0].function_name else None
                
                group = DuplicateGroup(
                    id=f"L{i:04d}",
                    duplicate_type=DuplicateType.NEAR_DUPLICATE,
                    fragments=fragments,
                    similarity_score=avg_similarity,
                    normalized_hash=f"lsh_{group_id}",
                    normalized_name=name,
                )
                groups.append(group)
    
    except Exception:
        # Silently fail if LSH is not available or has issues
        pass
    
    return groups


def analyze_parallel(
    config: ScanConfig | None = None,
    function_level_only: bool = False,
    max_workers: int | None = None,
) -> DuplicationMap:
    """Run reDUP analysis with parallel scanning for large projects.

    Args:
        config: Scan configuration. Defaults to current directory, .py files.
        function_level_only: If True, only analyze function-level blocks.
        max_workers: Number of parallel workers. Defaults to CPU count.

    Returns:
        A DuplicationMap with all duplicate groups and refactoring suggestions.
    """
    import time
    start_time = time.time()
    
    config = _ensure_config(config)

    # Phase 1: Parallel Scan
    scanned_files, stats = _scan_phase_parallel(config, max_workers)

    # Phase 2: Process blocks
    all_blocks = _process_blocks(scanned_files, function_level_only)

    # Phase 3: Hash and find duplicates
    groups = _find_duplicates_phase(all_blocks, config)

    # Phase 4: Deduplicate and suggest
    final_groups = _deduplicate_phase(groups)

    # Update scan time
    stats.scan_time_ms = (time.time() - start_time) * 1000

    dup_map = DuplicationMap(
        project_path=config.root.as_posix(),
        config=config,
        stats=stats,
        groups=final_groups,
    )
    dup_map.suggestions = generate_suggestions(dup_map)

    return dup_map


