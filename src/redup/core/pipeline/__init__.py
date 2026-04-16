"""Pipeline — orchestrates scan → hash → match → group → plan."""

from __future__ import annotations

import time
import signal
from typing import TYPE_CHECKING

from redup.core.models import DuplicationMap, ScanConfig, ScanStats
from redup.core.planner import generate_suggestions
from redup.core.scanner import ScanStrategy, scan_project

if TYPE_CHECKING:
    from redup.core.cache import HashCache

# Import from submodules
from redup.core.pipeline.phases import ensure_config, scan_phase, scan_phase_parallel, process_blocks
from redup.core.pipeline.duplicate_finder import (
    find_duplicates_phase_optimized,
    find_duplicates_phase_lazy,
    find_exact_groups,
    find_structural_groups,
    find_near_duplicate_groups,
    find_semantic_groups,
)
from redup.core.pipeline.groups import (
    blocks_to_group,
    deduplicate_groups,
    match_results_to_blocks,
    calculate_similarity,
)

# Backward compatibility aliases
_ensure_config = ensure_config
_scan_phase = scan_phase
_scan_phase_parallel = scan_phase_parallel
_process_blocks = process_blocks
_find_duplicates_phase_optimized = find_duplicates_phase_optimized
_find_duplicates_phase_lazy = find_duplicates_phase_lazy
_find_exact_groups = find_exact_groups
_find_structural_groups = find_structural_groups
_deduplicate_phase = deduplicate_groups
_match_results_to_blocks = match_results_to_blocks
_calculate_similarity = calculate_similarity
_find_near_duplicate_groups = find_near_duplicate_groups
_find_semantic_groups = find_semantic_groups
_blocks_to_group = blocks_to_group


def analyze(
    config: ScanConfig | None = None,
    function_level_only: bool | None = None,
) -> DuplicationMap:
    """Run the full reDUP analysis pipeline.

    Args:
        config: Scan configuration. Defaults to current directory, .py files.
        function_level_only: If True, only analyze function-level blocks
            (skip sliding-window line blocks). Faster but misses inline duplicates.
            If None, uses config.functions_only.

    Returns:
        A DuplicationMap with all duplicate groups and refactoring suggestions.
    """
    config = ensure_config(config)

    # Use config.functions_only if function_level_only is not explicitly provided
    if function_level_only is None:
        function_level_only = config.functions_only

    # Phase 1: Scan with function_level_only optimization
    scanned_files, stats = scan_phase(config, function_level_only=function_level_only)

    # Phase 2: Process blocks
    all_blocks = process_blocks(scanned_files, function_level_only)

    # Phase 3: Hash and find duplicates with optimizations
    groups = find_duplicates_phase_optimized(all_blocks, config)

    # Phase 4: Deduplicate and suggest
    final_groups = deduplicate_groups(groups)

    dup_map = DuplicationMap(
        project_path=config.root.as_posix(),
        config=config,
        stats=stats,
        groups=final_groups,
    )
    dup_map.suggestions = generate_suggestions(dup_map)

    return dup_map


def analyze_optimized(
    config: ScanConfig | None = None,
    function_level_only: bool = False,
    use_memory_cache: bool = True,
    max_cache_mb: int = 512,
) -> DuplicationMap:
    """Run reDUP analysis with all performance optimizations enabled.

    Uses parallel scanning, hash caching, lazy grouping, and memory optimization for maximum speed.

    Args:
        config: Scan configuration. Defaults to current directory, .py files.
        function_level_only: If True, only analyze function-level blocks.
        use_memory_cache: If True, load files into RAM for faster access.
        max_cache_mb: Maximum memory to use for file caching.

    Returns:
        A DuplicationMap with all duplicate groups and refactoring suggestions.
    """
    config = ensure_config(config)

    # Initialize cache if enabled
    cache = None
    if config.enable_cache:
        from redup.core.cache import HashCache
        cache = HashCache(config.cache_dir)

    start_time = time.time()

    def handle_interrupt(signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n⚠️  Scan interrupted by user")
        raise KeyboardInterrupt()

    # Set up signal handler for graceful interruption
    old_handler = signal.signal(signal.SIGINT, handle_interrupt)

    try:
        # Phase 1: Optimized scanning with memory cache
        if config.parallel_workers and config.parallel_workers > 1:
            # Explicit worker count specified
            strategy = ScanStrategy(
                parallel=True,
                max_workers=config.parallel_workers,
                memory_cache=use_memory_cache,
                max_cache_mb=max_cache_mb if use_memory_cache else 256
            )
            scanned_files, stats = scan_project(config, strategy, function_level_only=True)
        elif config.parallel_workers is None and (getattr(config, '_parallel_enabled', False) or config.parallel_workers is None):
            # Auto-detect CPU count when parallel_workers is None (default behavior)
            import multiprocessing as mp
            auto_workers = mp.cpu_count()
            strategy = ScanStrategy(
                parallel=True,
                max_workers=auto_workers,
                memory_cache=use_memory_cache,
                max_cache_mb=max_cache_mb if use_memory_cache else 256
            )
            scanned_files, stats = scan_project(config, strategy, function_level_only=True)
        elif use_memory_cache:
            strategy = ScanStrategy(memory_cache=True, max_cache_mb=max_cache_mb)
            scanned_files, stats = scan_project(config, strategy, function_level_only=True)
        else:
            scanned_files, stats = scan_project(config, function_level_only=True)

        # Phase 2: Process blocks
        all_blocks = process_blocks(scanned_files, function_level_only)

        # Phase 3: Hash and find duplicates with caching and lazy grouping
        groups = find_duplicates_phase_lazy(all_blocks, config, cache)

        # Phase 4: Deduplicate and suggest
        final_groups = deduplicate_groups(groups)

        # Update scan time
        stats.scan_time_ms = (time.time() - start_time) * 1000

        dup_map = DuplicationMap(
            project_path=config.root.as_posix(),
            config=config,
            stats=stats,
            groups=final_groups,
        )
        dup_map.suggestions = generate_suggestions(dup_map)

        # Store cache data if caching is enabled
        if cache is not None:
            try:
                cache.cleanup_old_entries()
            except Exception:
                pass  # Ignore cache cleanup errors

        return dup_map
    except KeyboardInterrupt:
        print("\n⚠️  Scan cancelled by user")
        # Return empty results
        return DuplicationMap(
            project_path=config.root.as_posix() if config else ".",
            config=config,
            stats=ScanStats(scan_time_ms=(time.time() - start_time) * 1000),
            groups=[],
        )
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, old_handler)


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
    start_time = time.time()

    config = ensure_config(config)

    def handle_interrupt(signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n⚠️  Scan interrupted by user")
        raise KeyboardInterrupt()

    # Set up signal handler for graceful interruption
    old_handler = signal.signal(signal.SIGINT, handle_interrupt)

    try:
        # Phase 1: Parallel Scan
        scanned_files, stats = scan_phase_parallel(config, max_workers)

        # Phase 2: Process blocks
        all_blocks = process_blocks(scanned_files, function_level_only)

        # Phase 3: Hash and find duplicates
        groups = find_duplicates_phase_optimized(all_blocks, config)

        # Phase 4: Deduplicate and suggest
        final_groups = deduplicate_groups(groups)

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
    except KeyboardInterrupt:
        print("\n⚠️  Scan cancelled by user")
        # Return empty results
        return DuplicationMap(
            project_path=config.root.as_posix() if config else ".",
            config=config,
            stats=ScanStats(scan_time_ms=(time.time() - start_time) * 1000),
            groups=[],
        )
    finally:
        # Restore original signal handler
        signal.signal(signal.SIGINT, old_handler)


__all__ = [
    # Main entry points
    "analyze",
    "analyze_optimized",
    "analyze_parallel",
    # Phases
    "ensure_config",
    "scan_phase",
    "scan_phase_parallel",
    "process_blocks",
    # Duplicate finding
    "find_duplicates_phase_optimized",
    "find_duplicates_phase_lazy",
    "find_exact_groups",
    "find_structural_groups",
    "find_near_duplicate_groups",
    "find_semantic_groups",
    # Groups
    "blocks_to_group",
    "deduplicate_groups",
    "match_results_to_blocks",
    "calculate_similarity",
    # Backward compatibility
    "_ensure_config",
    "_scan_phase",
    "_scan_phase_parallel",
    "_process_blocks",
    "_find_duplicates_phase_optimized",
    "_find_duplicates_phase_lazy",
    "_find_exact_groups",
    "_find_structural_groups",
    "_deduplicate_phase",
    "_match_results_to_blocks",
    "_calculate_similarity",
    "_find_near_duplicate_groups",
    "_find_semantic_groups",
    "_blocks_to_group",
]
