"""Project scanner public API compatibility layer."""
from __future__ import annotations

import time
from pathlib import Path

from redup.core.models import ScanConfig, ScanStats
from redup.core.scanner_cache import MemoryFileCache
from redup.core.scanner_filters import (
    _collect_files,
    _is_test_file,
    _project_relative_path,
    _should_exclude,
)
from redup.core.scanner_loader import _preload_files
from redup.core.scanner_types import CodeBlock, ScanStrategy, ScannedFile


def _normalize_scan_config(config: ScanConfig) -> ScanConfig:
    """Coerce the scan root into an absolute path."""
    if not isinstance(config.root, Path):
        config.root = Path(config.root)
    config.root = config.root.expanduser().resolve()
    return config


def _extract_function_blocks_python(source: str, filepath: str) -> list[CodeBlock]:
    """Extract Python function and method blocks."""
    import ast

    blocks: list[CodeBlock] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return blocks

    lines = source.splitlines()
    parent_map: dict[int, ast.ClassDef] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    parent_map[id(child)] = node

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno or start
            class_node = parent_map.get(id(node))
            blocks.append(
                CodeBlock(
                    file=filepath,
                    line_start=start,
                    line_end=end,
                    text="\n".join(lines[start - 1 : end]),
                    function_name=node.name,
                    class_name=class_node.name if class_node else None,
                )
            )

    return blocks


def _extract_sliding_blocks(source: str, filepath: str, min_lines: int) -> list[CodeBlock]:
    """Extract simple sliding-window blocks for non-function-level scans."""
    if min_lines <= 0:
        return []

    lines = source.splitlines()
    if len(lines) < min_lines:
        return []

    blocks: list[CodeBlock] = []
    for start in range(0, len(lines) - min_lines + 1):
        end = start + min_lines
        block_lines = lines[start:end]
        if not any(line.strip() for line in block_lines):
            continue
        blocks.append(
            CodeBlock(
                file=filepath,
                line_start=start + 1,
                line_end=end,
                text="\n".join(block_lines),
            )
        )

    return blocks


def _read_source_text(file_path: Path, cache: MemoryFileCache | None = None) -> str | None:
    """Read a file as text, optionally via the in-memory cache."""
    try:
        if cache is not None:
            content = cache.get_file_content(file_path)
            if not content:
                try:
                    if file_path.stat().st_size > 0:
                        return None
                except OSError:
                    return None
            return content.decode("utf-8", errors="replace")

        return file_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None


def _get_source_for_file(
    file_path: Path,
    preloaded_sources: dict[Path, str] | None,
    file_cache: MemoryFileCache | None,
) -> str | None:
    """Get source text for a file from preloaded sources or cache."""
    if preloaded_sources is not None:
        return preloaded_sources.get(file_path)
    return _read_source_text(file_path, file_cache)


def _extract_blocks_for_file(
    source: str,
    relative_path: str,
    file_ext: str,
    function_level_only: bool,
    min_block_lines: int,
) -> list[CodeBlock]:
    """Extract code blocks from a file based on its type."""
    blocks: list[CodeBlock] = []

    # Extract function-level blocks
    if file_ext == ".py":
        blocks = _extract_function_blocks_python(source, relative_path)
    else:
        try:
            from redup.core.ts_extractor import extract_functions_treesitter
            blocks = extract_functions_treesitter(source, relative_path)
        except ImportError:
            pass

    # Add sliding window blocks if not function-only mode
    if not function_level_only:
        blocks.extend(_extract_sliding_blocks(source, relative_path, min_block_lines))

    return blocks


def _process_single_file(
    file_path: Path,
    config: ScanConfig,
    preloaded_sources: dict[Path, str] | None,
    file_cache: MemoryFileCache | None,
    function_level_only: bool,
) -> ScannedFile | None:
    """Process a single file and return ScannedFile or None if skipped."""
    source = _get_source_for_file(file_path, preloaded_sources, file_cache)
    if source is None:
        return None

    lines = source.splitlines()
    relative_path = str(_project_relative_path(file_path, config.root))

    blocks = _extract_blocks_for_file(
        source, relative_path, file_path.suffix,
        function_level_only, config.min_block_lines
    )

    return ScannedFile(
        path=relative_path,
        lines=lines,
        blocks=blocks,
    )


def _init_strategy(strategy: ScanStrategy | bool | None, function_level_only: bool | None) -> tuple[ScanStrategy, bool]:
    """Initialize scan strategy and function-level flag."""
    if isinstance(strategy, bool):
        if function_level_only is None:
            function_level_only = strategy
        strategy = None
    if strategy is None:
        strategy = ScanStrategy()
    if function_level_only is None:
        function_level_only = False
    return strategy, function_level_only


def _init_file_loading(
    files: list[Path],
    strategy: ScanStrategy,
) -> tuple[dict[Path, str] | None, MemoryFileCache | None]:
    """Initialize file loading based on strategy."""
    if strategy.preload_to_ram:
        return _preload_files(files, strategy.max_cache_mb), None
    elif strategy.memory_cache:
        return None, MemoryFileCache(strategy.max_cache_mb)
    return None, None


def scan_project(
    config: ScanConfig | None = None,
    strategy: ScanStrategy | bool | None = None,
    function_level_only: bool | None = None,
) -> tuple[list[ScannedFile], ScanStats]:
    """Scan a project and return files with their extracted code blocks."""
    # Load config if not provided
    if config is None:
        from redup.core.config import config_to_scan_config, load_config
        config = config_to_scan_config(load_config(), Path.cwd())

    config = _normalize_scan_config(config)
    strategy, function_level_only = _init_strategy(strategy, function_level_only)

    files = sorted(_collect_files(config))
    if not files:
        return [], ScanStats()

    preloaded_sources, file_cache = _init_file_loading(files, strategy)

    start_time = time.monotonic()
    scanned_files: list[ScannedFile] = []
    total_lines = 0
    total_blocks = 0

    for file_path in files:
        scanned = _process_single_file(
            file_path, config, preloaded_sources, file_cache, function_level_only
        )
        if scanned is not None:
            scanned_files.append(scanned)
            total_lines += len(scanned.lines)
            total_blocks += len(scanned.blocks)

    stats = ScanStats(
        files_scanned=len(scanned_files),
        files_skipped=max(0, len(files) - len(scanned_files)),
        total_lines=total_lines,
        total_blocks=total_blocks,
        scan_time_ms=(time.monotonic() - start_time) * 1000,
    )
    return scanned_files, stats


def scan_project_ultra_fast(config: ScanConfig | None = None) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility wrapper for preload-to-RAM scanning."""
    strategy = ScanStrategy(preload_to_ram=True)
    return scan_project(config, strategy)


def scan_project_memory_optimized(
    config: ScanConfig | None = None,
    max_cache_mb: int = 512,
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility wrapper for memory-cache scanning."""
    strategy = ScanStrategy(memory_cache=True, max_cache_mb=max_cache_mb)
    return scan_project(config, strategy)


def scan_project_parallel(
    config: ScanConfig | None = None,
    max_workers: int = 4,
    function_level_only: bool = False,
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility wrapper for parallel scanning."""
    strategy = ScanStrategy(parallel=True, max_workers=max_workers)
    return scan_project(config, strategy, function_level_only)


def scan_project_parallel_memory_optimized(
    config: ScanConfig | None = None,
    max_workers: int = 4,
    max_cache_mb: int = 512,
    function_level_only: bool = False,
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility wrapper for combined parallel and cached scanning."""
    strategy = ScanStrategy(
        parallel=True,
        max_workers=max_workers,
        memory_cache=True,
        max_cache_mb=max_cache_mb,
    )
    return scan_project(config, strategy, function_level_only)


__all__ = [
    'CodeBlock',
    'ScannedFile',
    'ScanStrategy',
    'MemoryFileCache',
    'ScanConfig',
    'ScanStats',
    '_should_exclude',
    '_project_relative_path',
    '_collect_files',
    '_is_test_file',
    '_preload_files',
    '_extract_function_blocks_python',
    'scan_project',
    'scan_project_ultra_fast',
    'scan_project_memory_optimized',
    'scan_project_parallel',
    'scan_project_parallel_memory_optimized',
]
