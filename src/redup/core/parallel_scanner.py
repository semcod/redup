"""Parallel scanning for large projects."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
import time
from functools import lru_cache

from redup.core.scanner import CodeBlock, ScannedFile, scan_project
from redup.core.ts_extractor import extract_functions_treesitter
from redup.core.hasher import hash_block, hash_block_structural


def _scan_file_worker(args: tuple[Path, str, list[str], bool, bool, int]) -> ScannedFile:
    """Worker function for parallel file scanning."""
    file_path, project_root, extensions, include_tests, function_level_only, max_file_size = args
    
    # Check if file should be processed
    if not _should_process_file(file_path, project_root, extensions, include_tests, max_file_size):
        return ScannedFile(path=str(file_path), blocks=[])
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract code blocks
        blocks = []
        
        if function_level_only:
            # Extract function-level blocks only
            if file_path.suffix == '.py':
                from redup.core.scanner import _extract_function_blocks_python
                blocks = _extract_function_blocks_python(content, str(file_path))
            else:
                # Try tree-sitter for other languages
                blocks = extract_functions_treesitter(content, str(file_path))
        else:
            # Extract all blocks (functions + sliding window)
            if file_path.suffix == '.py':
                from redup.core.scanner import _extract_function_blocks_python, _extract_sliding_blocks
                blocks = _extract_function_blocks_python(content, str(file_path))
                blocks.extend(_extract_sliding_blocks(content, str(file_path)))
            else:
                # For non-Python files, just extract functions
                blocks = extract_functions_treesitter(content, str(file_path))
        
        return ScannedFile(path=str(file_path), blocks=blocks)
    
    except Exception:
        # Return empty file if processing fails
        return ScannedFile(path=str(file_path), blocks=[])


def _should_process_file(
    file_path: Path,
    project_root: Path,
    extensions: list[str],
    include_tests: bool,
    max_file_size: int
) -> bool:
    """Check if file should be processed."""
    # Check extension
    if file_path.suffix not in extensions:
        return False
    
    # Check file size
    try:
        if file_path.stat().st_size > max_file_size * 1024:
            return False
    except OSError:
        return False
    
    # Check if test file (and whether to include)
    if not include_tests:
        relative_path = file_path.relative_to(project_root)
        test_parts = frozenset(('test', 'tests', 'testing'))
        if _is_test_file_cached(str(relative_path), test_parts):
            return False
    
    return True


def _is_test_file(file_path: Path, project_root: Path) -> bool:
    """Check if file is a test file."""
    relative_path = file_path.relative_to(project_root)
    
    # Check if in test directory
    parts = relative_path.parts
    for part in parts:
        if part in ('test', 'tests', 'testing'):
            return True
    
    # Check filename patterns
    filename = file_path.name
    if filename.startswith('test_') or filename.endswith('_test.py'):
        return True
    
    return False


def scan_project_parallel(
    root: Path,
    extensions: list[str],
    exclude_patterns: list[str] | None = None,
    include_tests: bool = False,
    function_level_only: bool = False,
    max_file_size: int = 1024,
    max_workers: int | None = None,
    min_files_for_parallel: int = 10,
    use_threading: bool = False
) -> tuple[list[ScannedFile], Any]:
    """Scan project files in parallel for better performance on large projects."""
    from redup.core.models import ScanStats
    
    if max_workers is None:
        max_workers = min(os.cpu_count() or 4, 8)  # Cap at 8 workers
    
    # Find all files to scan (optimized)
    all_files = _find_files_optimized(root, extensions, exclude_patterns or [])
    
    # Use parallel scanning only if we have enough files
    if len(all_files) < min_files_for_parallel:
        # Fall back to sequential scanning
        return scan_project(root, extensions, exclude_patterns, include_tests, function_level_only, max_file_size)
    
    # Prepare work items
    work_items = [
        (file_path, root, extensions, include_tests, function_level_only, max_file_size)
        for file_path in all_files
    ]
    
    # Scan files in parallel
    start_time = time.time()
    scanned_files = []
    total_blocks = 0
    total_lines = 0
    
    executor_class = ThreadPoolExecutor if use_threading else ProcessPoolExecutor
    
    with executor_class(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_file = {
            executor.submit(_scan_file_worker, work_item): work_item[0]
            for work_item in work_items
        }
        
        # Collect results
        for future in as_completed(future_to_file):
            try:
                scanned_file = future.result()
                scanned_files.append(scanned_file)
                
                # Update statistics
                for block in scanned_file.blocks:
                    total_blocks += 1
                    total_lines += block.line_count
                
            except Exception:
                # Log error but continue processing other files
                file_path = future_to_file[future]
                print(f"Warning: Failed to scan {file_path}")
    
    scan_time = (time.time() - start_time) * 1000
    
    # Create stats
    stats = ScanStats(
        files_scanned=len(scanned_files),
        total_lines=total_lines,
        total_blocks=total_blocks,
        scan_time_ms=scan_time,
    )
    
    return scanned_files, stats


def _find_files_optimized(
    root: Path,
    extensions: set[str],
    exclude_patterns: list[str]
) -> list[Path]:
    """Optimized file discovery using set lookups and compiled patterns."""
    extensions_set = set(extensions) if not isinstance(extensions, set) else extensions
    
    # Pre-compile exclude patterns for better performance
    import fnmatch
    compiled_patterns = [fnmatch.translate(pattern) for pattern in exclude_patterns]
    import re
    regex_patterns = [re.compile(pattern) for pattern in compiled_patterns]
    
    all_files = []
    
    for file_path in root.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Fast extension check using set
        if file_path.suffix not in extensions_set:
            continue
        
        # Check exclude patterns
        relative_path = file_path.relative_to(root)
        should_exclude = False
        
        for regex_pattern in regex_patterns:
            if regex_pattern.match(str(relative_path)):
                should_exclude = True
                break
        
        if not should_exclude:
            all_files.append(file_path)
    
    return all_files


@lru_cache(maxsize=1024)
def _is_test_file_cached(relative_path: str, test_parts: frozenset) -> bool:
    """Cached version of test file detection."""
    parts = Path(relative_path).parts
    
    # Check if in test directory
    for part in parts:
        if part in test_parts:
            return True
    
    # Check filename patterns
    filename = Path(relative_path).name
    if filename.startswith('test_') or filename.endswith('_test.py'):
        return True
    
    return False
