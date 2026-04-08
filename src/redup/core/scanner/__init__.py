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


def scan_project(
    config: ScanConfig | None = None,
    strategy: ScanStrategy | bool | None = None,
    function_level_only: bool | None = None,
) -> tuple[list[ScannedFile], ScanStats]:
    """Scan a project and return files with their extracted code blocks."""
    if isinstance(strategy, bool):
        if function_level_only is None:
            function_level_only = strategy
        strategy = None

    if config is None:
        from redup.core.config import config_to_scan_config, load_config

        config = config_to_scan_config(load_config(), Path.cwd())

    config = _normalize_scan_config(config)

    if strategy is None:
        strategy = ScanStrategy()
    if function_level_only is None:
        function_level_only = False

    files = sorted(_collect_files(config))
    if not files:
        return [], ScanStats()

    preloaded_sources: dict[Path, str] | None = None
    file_cache: MemoryFileCache | None = None

    if strategy.preload_to_ram:
        preloaded_sources = _preload_files(files, strategy.max_cache_mb)
    elif strategy.memory_cache:
        file_cache = MemoryFileCache(strategy.max_cache_mb)

    start_time = time.monotonic()
    scanned_files: list[ScannedFile] = []
    total_lines = 0
    total_blocks = 0

    for file_path in files:
        if preloaded_sources is not None:
            source = preloaded_sources.get(file_path)
            if source is None:
                continue
        else:
            source = _read_source_text(file_path, file_cache)
            if source is None:
                continue

        lines = source.splitlines()
        relative_path = str(_project_relative_path(file_path, config.root))

        if file_path.suffix == ".py":
            blocks = _extract_function_blocks_python(source, relative_path)
        else:
            blocks = []
            try:
                from redup.core.ts_extractor import extract_functions_treesitter
            except ImportError:
                extract_functions_treesitter = None

            if extract_functions_treesitter is not None:
                blocks = extract_functions_treesitter(source, relative_path)

        if not function_level_only:
            blocks.extend(_extract_sliding_blocks(source, relative_path, config.min_block_lines))

        scanned_files.append(
            ScannedFile(
                path=relative_path,
                lines=lines,
                blocks=blocks,
            )
        )
        total_lines += len(lines)
        total_blocks += len(blocks)

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
