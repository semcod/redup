"""Project scanner — walks directories, reads files, produces code blocks."""

from __future__ import annotations

import fnmatch
import functools
import mmap
import os
import time
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from redup.core.models import ScanConfig, ScanStats


@dataclass
class CodeBlock:
    """A contiguous block of source code lines."""

    file: str
    line_start: int
    line_end: int
    text: str
    function_name: str | None = None
    class_name: str | None = None

    @property
    def line_count(self) -> int:
        return self.line_end - self.line_start + 1


@dataclass
class ScannedFile:
    """A file that has been read and split into blocks."""

    path: str
    lines: list[str] = field(default_factory=list)
    blocks: list[CodeBlock] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)


@dataclass
class ScanStrategy:
    """Configuration for HOW to scan — not WHAT to scan."""
    parallel: bool = False
    max_workers: int = 4
    memory_cache: bool = False
    max_cache_mb: int = 256
    preload_to_ram: bool = False


class MemoryFileCache:
    """Cache file contents in RAM for faster access during scanning."""
    
    def __init__(self, max_memory_mb: int = 512):
        """Initialize cache with memory limit."""
        self.max_memory_mb = max_memory_mb
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: dict[Path, bytes] = {}
        self.current_memory = 0
    
    def _estimate_size(self, content: bytes) -> int:
        """Estimate memory usage of cached content."""
        return len(content) + 100  # Add overhead for dict entry
    
    def get_file_content(self, file_path: Path) -> bytes:
        """Get file content from cache or load from disk."""
        if file_path in self.cache:
            return self.cache[file_path]
        
        # Check file size before loading
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_memory_bytes // 2:  # Don't cache huge files
                return file_path.read_bytes()
            
            content = file_path.read_bytes()
            content_size = self._estimate_size(content)
            
            # Check if we have enough memory
            if self.current_memory + content_size <= self.max_memory_bytes:
                self.cache[file_path] = content
                self.current_memory += content_size
            else:
                # Cache is full, clear oldest entries
                self._evict_oldest(content_size)
                if content_size <= self.max_memory_bytes // 2:
                    self.cache[file_path] = content
                    self.current_memory += content_size
            
            return content
        except (OSError, UnicodeDecodeError):
            return b""
    
    def _evict_oldest(self, needed_size: int) -> None:
        """Evict oldest entries to make room."""
        # Simple LRU: clear half the cache
        items_to_remove = len(self.cache) // 2
        for _ in range(items_to_remove):
            if self.cache:
                oldest_path = next(iter(self.cache))
                oldest_content = self.cache.pop(oldest_path)
                self.current_memory -= self._estimate_size(oldest_content)


@functools.lru_cache(maxsize=1000)
def _should_exclude(path: Path, patterns: tuple[str, ...]) -> bool:
    """Check if a path matches any exclusion pattern."""
    name = path.name
    str_path = str(path)
    
    # Check against patterns
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(str_path, pattern):
            return True
    
    return False


def _collect_files(config: ScanConfig) -> list[Path]:
    """Collect all files to scan based on configuration."""
    files = []
    
    for file_path in config.root.rglob("*"):
        if file_path.is_file():
            # Check extension
            if file_path.suffix not in config.extensions:
                continue
            
            # Check exclusions
            if _should_exclude(file_path, tuple(config.exclude_patterns)):
                continue
            
            # Check if test file
            if not config.include_tests and _is_test_file(file_path):
                continue
            
            # Check file size
            try:
                if file_path.stat().st_size > config.max_file_size:
                    continue
            except OSError:
                continue
            
            files.append(file_path)
    
    return files


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    name = path.name.lower()
    dir_parts = [part.lower() for part in path.parts]
    
    # Check filename patterns
    test_patterns = [
        "test_", "_test.", "tests.", "spec_", "_spec."
    ]
    
    if any(pattern in name for pattern in test_patterns):
        return True
    
    # Check directory patterns
    if any("test" in part for part in dir_parts):
        return True
    
    return False


def _preload_files(files: list[Path], max_cache_mb: int = 256) -> dict[Path, str]:
    """Load ALL files into RAM at once for maximum speed."""
    if not files:
        return {}
    
    start_time = time.time()
    total_size = 0
    
    # Sort by size for better memory access patterns
    files.sort(key=lambda f: f.stat().st_size if f.exists() else 0)
    
    # Show progress for large projects
    if len(files) > 50:
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), 
                         BarColumn(), transient=True) as progress:
                task = progress.add_task(f"Loading {len(files)} files to RAM...", total=len(files))
                
                # Batch load all files into RAM with optimized I/O
                sources = {}
                for file_path in files:
                    try:
                        # Use memory mapping for larger files (>64KB) to reduce memory copies
                        file_size = file_path.stat().st_size
                        if file_size > 64 * 1024:  # 64KB threshold for mmap
                            with open(file_path, 'rb') as f:
                                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                                    content = mm.read().decode('utf-8', errors='replace')
                        else:
                            content = file_path.read_text('utf-8', errors='replace')
                        
                        sources[file_path] = content
                        total_size += len(content)
                        progress.advance(task)
                    except (OSError, UnicodeDecodeError):
                        continue
                
                load_time = time.time() - start_time
                progress.console.print(f"✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s")
                
        except ImportError:
            # Fallback without rich
            sources = {}
            for file_path in files:
                try:
                    content = file_path.read_text('utf-8', errors='replace')
                    sources[file_path] = content
                    total_size += len(content)
                except (OSError, UnicodeDecodeError):
                    continue
            
            load_time = time.time() - start_time
            print(f"✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s")
    else:
        # Small project, load directly
        sources = {}
        for file_path in files:
            try:
                content = file_path.read_text('utf-8', errors='replace')
                sources[file_path] = content
                total_size += len(content)
            except (OSError, UnicodeDecodeError):
                continue
        
        load_time = time.time() - start_time
        print(f"✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s")
    
    return sources


def _lazy_read_files(files: list[Path]) -> dict[Path, str]:
    """Create lazy file reader that reads on demand."""
    class LazyFileReader:
        def __init__(self, files: list[Path]):
            self.files = files
            self._cache: dict[Path, str] = {}
        
        def get(self, file_path: Path) -> str:
            if file_path not in self._cache:
                try:
                    self._cache[file_path] = file_path.read_text('utf-8', errors='replace')
                except (OSError, UnicodeDecodeError):
                    self._cache[file_path] = ""
            return self._cache[file_path]
        
        def __getitem__(self, file_path: Path) -> str:
            return self.get(file_path)
    
    return LazyFileReader(files)


def _scan_sequential(
    sources: dict[Path, str] | Any, 
    config: ScanConfig,
    function_level_only: bool = False
) -> tuple[list[ScannedFile], ScanStats]:
    """Scan files sequentially."""
    from redup.core.ts_extractor import extract_functions_treesitter
    
    start_time = time.time()
    scanned_files = []
    total_lines = 0
    
    for file_path in sources.keys() if hasattr(sources, 'keys') else []:
        try:
            content = sources[file_path] if hasattr(sources, '__getitem__') else file_path.read_text('utf-8', errors='replace')
            
            if not content.strip():
                continue
            
            lines = content.splitlines()
            total_lines += len(lines)
            
            blocks = []
            
            if function_level_only:
                # Extract function-level blocks only
                if file_path.suffix == '.py':
                    blocks = _extract_function_blocks_python(content, str(file_path))
                else:
                    blocks = extract_functions_treesitter(content, str(file_path))
            else:
                # Extract all blocks (functions + sliding window)
                if file_path.suffix == '.py':
                    blocks = _extract_function_blocks_python(content, str(file_path))
                    blocks.extend(_extract_sliding_blocks(content, str(file_path)))
                else:
                    # For non-Python files, just extract functions
                    blocks = extract_functions_treesitter(content, str(file_path))
            
            scanned_file = ScannedFile(
                path=str(file_path),
                lines=lines,
                blocks=blocks
            )
            scanned_files.append(scanned_file)
            
        except (OSError, UnicodeDecodeError):
            continue
    
    scan_time = time.time() - start_time
    stats = ScanStats(
        files_scanned=len(scanned_files),
        total_lines=total_lines,
        scan_time_ms=int(scan_time * 1000)
    )
    
    return scanned_files, stats


def _scan_parallel(
    sources: dict[Path, str] | Any,
    config: ScanConfig,
    max_workers: int = 4,
    function_level_only: bool = False
) -> tuple[list[ScannedFile], ScanStats]:
    """Scan files in parallel using ProcessPoolExecutor."""
    from redup.core.ts_extractor import extract_functions_treesitter
    
    start_time = time.time()
    scanned_files = []
    total_lines = 0
    
    # Prepare work items
    files = list(sources.keys()) if hasattr(sources, 'keys') else []
    work_items = [
        (file_path, str(config.root), list(config.extensions), config.include_tests, 
         function_level_only, config.max_file_size)
        for file_path in files
    ]
    
    if len(work_items) < 4:  # Not worth parallelizing for small projects
        return _scan_sequential(sources, config, function_level_only)
    
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit all work items
            future_to_file = {
                executor.submit(_scan_file_worker, item): item[0] 
                for item in work_items
            }
            
            # Collect results
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    scanned_file = future.result()
                    if scanned_file.blocks:  # Only include files with blocks
                        scanned_files.append(scanned_file)
                        total_lines += scanned_file.line_count
                except Exception:
                    continue  # Skip failed files
    
    except (OSError, ImportError):
        # Fallback to sequential if parallel execution fails
        return _scan_sequential(sources, config, function_level_only)
    
    scan_time = time.time() - start_time
    stats = ScanStats(
        files_scanned=len(scanned_files),
        total_lines=total_lines,
        scan_time_ms=int(scan_time * 1000)
    )
    
    return scanned_files, stats


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
                blocks = _extract_function_blocks_python(content, str(file_path))
            else:
                # Try tree-sitter for other languages
                from redup.core.ts_extractor import extract_functions_treesitter
                blocks = extract_functions_treesitter(content, str(file_path))
        else:
            # Extract all blocks (functions + sliding window)
            if file_path.suffix == '.py':
                blocks = _extract_function_blocks_python(content, str(file_path))
                blocks.extend(_extract_sliding_blocks(content, str(file_path)))
            else:
                # For non-Python files, just extract functions
                from redup.core.ts_extractor import extract_functions_treesitter
                blocks = extract_functions_treesitter(content, str(file_path))
        
        lines = content.splitlines()
        return ScannedFile(path=str(file_path), lines=lines, blocks=blocks)
        
    except (OSError, UnicodeDecodeError):
        return ScannedFile(path=str(file_path), blocks=[])


def _should_process_file(
    file_path: Path, 
    project_root: str, 
    extensions: list[str], 
    include_tests: bool,
    max_file_size: int
) -> bool:
    """Check if file should be processed in parallel scan."""
    # Check extension
    if file_path.suffix not in extensions:
        return False
    
    # Check exclusions
    if _should_exclude(file_path, tuple()):
        return False
    
    # Check if test file
    if not include_tests and _is_test_file(file_path):
        return False
    
    # Check file size
    try:
        if file_path.stat().st_size > max_file_size:
            return False
    except OSError:
        return False
    
    return True


def _extract_function_blocks_python(content: str, file_path: str) -> list[CodeBlock]:
    """Extract function blocks from Python code using AST."""
    import ast
    
    blocks = []
    lines = content.splitlines()
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get function boundaries
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                
                # Extract function text
                func_lines = lines[start_line - 1:end_line]
                func_text = '\\n'.join(func_lines)
                
                # Get class name if inside a class
                class_name = None
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        if (parent.lineno <= start_line <= 
                            (parent.end_lineno if hasattr(parent, 'end_lineno') else float('inf'))):
                            class_name = parent.name
                            break
                
                block = CodeBlock(
                    file=file_path,
                    line_start=start_line,
                    line_end=end_line,
                    text=func_text,
                    function_name=node.name,
                    class_name=class_name
                )
                blocks.append(block)
    
    except SyntaxError:
        # Fallback to simple regex-based extraction for invalid Python
        import re
        
        func_pattern = r'^(def|async\\s+def)\\s+(\\w+)\\s*\\('
        for i, line in enumerate(lines):
            if re.match(func_pattern, line.strip()):
                # Simple heuristic: take 10-50 lines as function
                end_line = min(i + 50, len(lines))
                if i + 10 < end_line:
                    end_line = i + 10
                
                func_text = '\\n'.join(lines[i:end_line])
                func_name = re.match(func_pattern, line.strip()).group(2)
                
                block = CodeBlock(
                    file=file_path,
                    line_start=i + 1,
                    line_end=end_line,
                    text=func_text,
                    function_name=func_name
                )
                blocks.append(block)
    
    return blocks


def _extract_sliding_blocks(content: str, file_path: str) -> list[CodeBlock]:
    """Extract blocks using sliding window approach."""
    lines = content.splitlines()
    blocks = []
    
    min_block_size = 3
    max_block_size = 50
    
    for start in range(0, len(lines) - min_block_size + 1):
        for size in range(min_block_size, min(max_block_size, len(lines) - start + 1)):
            end = start + size - 1
            block_lines = lines[start:end + 1]
            block_text = '\\n'.join(block_lines)
            
            # Skip blocks that are too short or mostly empty
            non_empty_lines = [line for line in block_lines if line.strip()]
            if len(non_empty_lines) < min_block_size:
                continue
            
            block = CodeBlock(
                file=file_path,
                line_start=start + 1,
                line_end=end + 1,
                text=block_text
            )
            blocks.append(block)
    
    return blocks


def scan_project(
    config: ScanConfig | None = None,
    strategy: ScanStrategy | None = None,
    function_level_only: bool = False
) -> tuple[list[ScannedFile], ScanStats]:
    """UNIFIED entry point for project scanning.
    
    Args:
        config: Scan configuration
        strategy: Scanning strategy (parallel, memory cache, etc.)
        function_level_only: Only analyze function-level blocks
        
    Returns:
        Tuple of (scanned_files, scan_stats)
    """
    if config is None:
        from redup.core.config import load_config, config_to_scan_config
        file_config = load_config()
        config = config_to_scan_config(file_config, Path.cwd())
    
    if strategy is None:
        strategy = ScanStrategy()
    
    # Collect files
    files = _collect_files(config)
    
    if not files:
        return [], ScanStats(files_scanned=0, total_lines=0, scan_time_ms=0)
    
    # Choose file reading strategy
    if strategy.preload_to_ram:
        sources = _preload_files(files, strategy.max_cache_mb)
    elif strategy.memory_cache:
        cache = MemoryFileCache(strategy.max_cache_mb)
        # Wrap cache to provide dict-like interface
        class CachedSource:
            def __init__(self, cache: MemoryFileCache):
                self.cache = cache
            
            def keys(self):
                return [f for f in files if f in self.cache.cache or f.exists()]
            
            def __getitem__(self, file_path: Path) -> str:
                content = self.cache.get_file_content(file_path)
                return content.decode('utf-8', errors='replace')
        
        sources = CachedSource(cache)
    else:
        sources = _lazy_read_files(files)
    
    # Choose scanning strategy
    if strategy.parallel and len(files) > 10:
        return _scan_parallel(sources, config, strategy.max_workers, function_level_only)
    else:
        return _scan_sequential(sources, config, function_level_only)


# Legacy compatibility functions
def scan_project_ultra_fast(config: ScanConfig | None = None) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility - use scan_project with ScanStrategy(preload_to_ram=True)."""
    strategy = ScanStrategy(preload_to_ram=True)
    return scan_project(config, strategy)


def scan_project_memory_optimized(
    config: ScanConfig | None = None, 
    max_cache_mb: int = 512
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility - use scan_project with ScanStrategy(memory_cache=True)."""
    strategy = ScanStrategy(memory_cache=True, max_cache_mb=max_cache_mb)
    return scan_project(config, strategy)


def scan_project_parallel(
    config: ScanConfig | None = None,
    max_workers: int = 4,
    function_level_only: bool = False
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility - use scan_project with ScanStrategy(parallel=True)."""
    strategy = ScanStrategy(parallel=True, max_workers=max_workers)
    return scan_project(config, strategy, function_level_only)


def scan_project_parallel_memory_optimized(
    config: ScanConfig | None = None,
    max_workers: int = 4,
    max_cache_mb: int = 512,
    function_level_only: bool = False
) -> tuple[list[ScannedFile], ScanStats]:
    """Legacy compatibility - use scan_project with combined strategy."""
    strategy = ScanStrategy(
        parallel=True, 
        max_workers=max_workers,
        memory_cache=True,
        max_cache_mb=max_cache_mb
    )
    return scan_project(config, strategy, function_level_only)
