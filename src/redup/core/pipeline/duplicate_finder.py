"""Duplicate finding phases: exact, structural, near-duplicate, semantic."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from redup.core.cache import HashCache, build_hash_index_with_cache
from redup.core.hasher import HashIndex, build_hash_index, find_exact_duplicates, find_structural_duplicates
from redup.core.lsh_matcher import find_near_duplicates
from redup.core.matcher import refine_structural_matches
from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType, ScanConfig
from redup.core.scanner_types import CodeBlock

if TYPE_CHECKING:
    from redup.core.pipeline.groups import calculate_similarity, blocks_to_group, match_results_to_blocks


def find_exact_groups(index: HashIndex) -> list[DuplicateGroup]:
    """Find exact duplicate groups."""
    from redup.core.pipeline.groups import blocks_to_group
    
    groups: list[DuplicateGroup] = []
    exact_groups = find_exact_duplicates(index)

    for i, (h, blocks) in enumerate(exact_groups.items(), 1):
        func_blocks = [b for b in blocks if b.block.function_name]
        if len(func_blocks) >= 2:
            g = blocks_to_group(
                group_id=f"E{i:04d}",
                blocks=func_blocks,
                dup_type=DuplicateType.EXACT,
                normalized_hash=h,
            )
            if g.occurrences >= 2:
                groups.append(g)

    return groups


def find_structural_groups(
    index: HashIndex, exact_groups_list: list[DuplicateGroup]
) -> list[DuplicateGroup]:
    """Find structural duplicate groups."""
    from redup.core.pipeline.groups import blocks_to_group, calculate_similarity, match_results_to_blocks
    
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
            refined_blocks = match_results_to_blocks(refined)
            if len(refined_blocks) >= 2:
                g = blocks_to_group(
                    group_id=f"S{i:04d}",
                    blocks=refined_blocks,
                    dup_type=DuplicateType.STRUCTURAL,
                    normalized_hash=h,
                    similarity=calculate_similarity(refined),
                )
                if g.occurrences >= 2:
                    groups.append(g)

    return groups


def find_near_duplicate_groups(
    all_blocks: list[CodeBlock], config: ScanConfig
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


def find_semantic_groups(
    blocks: list[CodeBlock], threshold: float = 0.80
) -> list[DuplicateGroup]:
    """Tier 4: Semantic duplicate detection via embeddings."""
    try:
        from redup.core.semantic import SemanticDetector
    except ImportError:
        return []

    detector = SemanticDetector(threshold=threshold)

    # Only function-level blocks (skip sliding window noise)
    func_blocks = [b for b in blocks if b.function_name]
    if len(func_blocks) < 2:
        return []

    matches = detector.find_semantic_duplicates_fast(func_blocks)

    groups: list[DuplicateGroup] = []
    for i, match in enumerate(matches):
        groups.append(DuplicateGroup(
            id=f"M{i+1:04d}",
            duplicate_type=DuplicateType.SEMANTIC,
            fragments=[
                DuplicateFragment(
                    file=match.block_a.file,
                    line_start=match.block_a.line_start,
                    line_end=match.block_a.line_end,
                    text=match.block_a.text,
                    function_name=match.block_a.function_name,
                ),
                DuplicateFragment(
                    file=match.block_b.file,
                    line_start=match.block_b.line_start,
                    line_end=match.block_b.line_end,
                    text=match.block_b.text,
                    function_name=match.block_b.function_name,
                ),
            ],
            similarity_score=match.similarity,
        ))

    return groups


def find_duplicates_phase_optimized(
    all_blocks: list[CodeBlock], config: ScanConfig
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicate groups with performance optimizations."""
    from redup.core.lazy_grouper import find_all_duplicates_lazy
    from redup.core.pipeline.groups import deduplicate_groups
    
    start_time = time.time()

    # Build hash index with progress tracking
    index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Find duplicates using lazy evaluation for better performance
    groups = list(find_all_duplicates_lazy(index, min_lines=config.min_block_lines))

    # Add near-duplicates if LSH is enabled
    near_duplicate_groups = find_near_duplicate_groups(all_blocks, config)
    groups.extend(near_duplicate_groups)

    # Sort by impact
    groups.sort(key=lambda g: g.impact_score, reverse=True)

    processing_time = (time.time() - start_time) * 1000
    print(f"Duplicate finding completed in {processing_time:.1f}ms")

    return groups


def find_duplicates_phase_lazy(
    all_blocks: list[CodeBlock], config: ScanConfig, cache: HashCache | None = None
) -> list[DuplicateGroup]:
    """Phase 3: Hash and find duplicates with caching and lazy evaluation."""
    from redup.core.lazy_grouper import find_all_duplicates_lazy
    from redup.core.pipeline.groups import deduplicate_groups
    
    start_time = time.time()

    # Build hash index with optional caching
    if cache is not None:
        index, block_hash_cache = build_hash_index_with_cache(
            all_blocks, min_lines=config.min_block_lines, cache=cache
        )

        # Store cache data for incremental scans
        for file_path, hashes in block_hash_cache.items():
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    cache.store_file_hashes(file_path, content, hashes)
                except OSError:
                    pass
    else:
        index = build_hash_index(all_blocks, min_lines=config.min_block_lines)

    # Use lazy grouping with early exit
    groups = list(find_all_duplicates_lazy(index, min_lines=config.min_block_lines))

    # Add near-duplicates if LSH is enabled
    near_duplicate_groups = find_near_duplicate_groups(all_blocks, config)
    groups.extend(near_duplicate_groups)

    # Sort by impact
    groups.sort(key=lambda g: g.impact_score, reverse=True)

    processing_time = (time.time() - start_time) * 1000
    if cache is not None:
        cache_stats = cache.get_stats()
        print(f"Duplicate finding completed in {processing_time:.1f}ms (cache: {cache_stats.get('cached_files', 0)} files)")
    else:
        print(f"Duplicate finding completed in {processing_time:.1f}ms")

    return groups
