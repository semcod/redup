"""Project scanner — walks directories, reads files, produces code blocks."""

from __future__ import annotations

import fnmatch
import functools
import mmap
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

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


@functools.lru_cache(maxsize=1000)
def _should_exclude(path: Path, patterns: tuple[str, ...]) -> bool:
    """Check if a path matches any exclusion pattern."""
    name = path.name
    str_path = str(path)
    parts = path.parts
    for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
        # Check if any path component matches the pattern
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
        if fnmatch.fnmatch(str_path, f"*/{pattern}/*"):
            return True
        if fnmatch.fnmatch(str_path, f"*/{pattern}"):
            return True
    return False


def _collect_files(config: ScanConfig) -> Iterator[Path]:
    """Yield all files matching the scan configuration."""
    root = Path(config.root).resolve() if isinstance(config.root, str) else config.root.resolve()
    for ext in config.extensions:
        for path in root.rglob(f"*{ext}"):
            if _should_exclude(path, tuple(config.exclude_patterns)):
                continue
            if not config.include_tests and _is_test_file(path):
                continue
            # Defer stat() to read phase - avoid double syscalls
            yield path


def _is_test_file(path: Path) -> bool:
    """Heuristic: is this a test file?"""
    name = path.name.lower()
    parts = [p.lower() for p in path.parts]
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or "tests" in parts
        or "test" in parts
    )


def _read_file_optimized(filepath: Path, max_size_kb: int = 1024) -> str | None:
    """Read file using mmap for large files to avoid heap allocation.
    
    Uses regular read for small files (<64KB) and mmap for larger files.
    Returns None on error.
    """
    try:
        size = filepath.stat().st_size
        
        # Small files: regular read (faster due to less overhead)
        if size < 64 * 1024:  # 64KB threshold
            return filepath.read_text(encoding="utf-8", errors="replace")
        
        # Large files: memory-mapped read (avoids loading to heap)
        if size > max_size_kb * 1024:
            return None  # Skip files exceeding limit
            
        with open(filepath, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                return mm.read(size).decode("utf-8", errors="replace")
                
    except (OSError, PermissionError, UnicodeDecodeError):
        return None


def _extract_blocks_sliding(lines: list[str], min_lines: int) -> list[tuple[int, int, str]]:
    """Extract overlapping blocks using a sliding window.

    Returns list of (start_line, end_line, normalized_text).
    Lines are 1-indexed.
    
    Optimized: O(n) complexity with step > 1, adaptive window sizes,
    and early exit for uniform blocks (auto-generated code).
    """
    blocks: list[tuple[int, int, str]] = []
    non_empty = [(i, line) for i, line in enumerate(lines) if line.strip()]
    if len(non_empty) < min_lines:
        return blocks

    n = len(non_empty)
    # Adaptive max window: smaller for large files to avoid explosion
    max_window = min(n, 20 if n > 100 else 50)
    
    # Use step > 1 to reduce overlap (O(n) instead of O(n²))
    step = max(1, n // 100)  # Adaptive step based on file size
    
    # Limit total blocks per file to prevent memory explosion
    max_blocks = 500
    
    # Pre-compute line hashes for fast duplicate detection
    line_hashes = [hash(line.strip()) for line in lines]
    
    for window_size in range(min_lines, max_window + 1, step):
        for start_idx in range(0, n - window_size + 1, step):
            if len(blocks) >= max_blocks:
                return blocks
            chunk = non_empty[start_idx : start_idx + window_size]
            indices = [i for i, _ in chunk]
            
            # Early exit: skip if all lines identical (likely auto-generated)
            if len(set(line_hashes[i] for i in indices)) == 1:
                continue
            
            first_line = chunk[0][0] + 1
            last_line = chunk[-1][0] + 1
            # Optimized: reduce string operations
            chunk_lines = [line.strip() for _, line in chunk]
            text = "\n".join(chunk_lines)
            blocks.append((first_line, last_line, text))

    return blocks


def _extract_class_blocks_python(source: str, filepath: str) -> list[CodeBlock]:
    """Extract class-level blocks from Python source using ast.
    
    This enables detection of duplicate classes across files.
    """
    import ast

    blocks: list[CodeBlock] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return blocks

    # Cache splitlines - call once instead of for every class
    lines = source.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno or start
            text = "\n".join(lines[start - 1 : end])

            blocks.append(
                CodeBlock(
                    file=filepath,
                    line_start=start,
                    line_end=end,
                    text=text,
                    function_name=None,  # It's a class, not a function
                    class_name=node.name,
                )
            )

    return blocks


def _extract_function_blocks_python(source: str, filepath: str) -> list[CodeBlock]:
    """Extract function/method-level blocks from Python source using ast."""
    import ast

    blocks: list[CodeBlock] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return blocks

    # Cache splitlines - single call for all functions
    lines = source.splitlines()
    
    # Single-pass AST walk - O(n) instead of O(2n)
    node_to_parent: dict[ast.AST, ast.ClassDef] = {}
    function_nodes: list[tuple[ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef | None]] = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    node_to_parent[child] = node
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = node_to_parent.get(node)
            function_nodes.append((node, parent))

    # Process all function nodes
    for node, class_node in function_nodes:
        start = node.lineno
        end = node.end_lineno or start
        text = "\n".join(lines[start - 1 : end])

        class_name = class_node.name if class_node else None

        blocks.append(
            CodeBlock(
                file=filepath,
                line_start=start,
                line_end=end,
                text=text,
                function_name=node.name,
                class_name=class_name,
            )
        )

    return blocks


def _preload_files_to_ram(config: ScanConfig) -> list[tuple[Path, str]]:
    """Preload all matching files to RAM for faster processing.
    
    Returns list of (path, content) tuples. Filters out files exceeding size limit.
    """
    files_content: list[tuple[Path, str]] = []
    
    for filepath in _collect_files(config):
        # Check size first to avoid loading huge files
        try:
            size = filepath.stat().st_size
            if size > config.max_file_size_kb * 1024:
                continue
        except OSError:
            continue
            
        source = _read_file_optimized(filepath, config.max_file_size_kb)
        if source is not None:
            files_content.append((filepath, source))
    
    return files_content


def scan_project(config: ScanConfig | None = None, function_level_only: bool = False) -> tuple[list[ScannedFile], ScanStats]:
    """Scan a project and return files with their code blocks.
    
    Args:
        config: Scan configuration
        function_level_only: If True, skip sliding-window blocks (faster)

    Returns:
        Tuple of (scanned_files, scan_stats).
    """
    import sys
    
    if config is None:
        config = ScanConfig()

    t0 = time.monotonic()
    stats = ScanStats()
    scanned: list[ScannedFile] = []
    
    # Phase 1: RAM preload - all files to memory at once
    files_content = _preload_files_to_ram(config)
    stats.files_scanned = len(files_content)
    
    # Progress indicator for large projects
    total_files = len(files_content)
    if total_files > 100:
        print(f"  Scanning {total_files} files...", file=sys.stderr, flush=True)
    
    # Phase 2: Process all files from RAM
    for i, (filepath, source) in enumerate(files_content):
        # Progress indicator for large projects
        if total_files > 100 and (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{total_files} files...", file=sys.stderr, flush=True)
        
        lines = source.splitlines()
        rel_path = str(filepath.relative_to(config.root.resolve()))
        stats.total_lines += len(lines)

        # Extract function-level blocks for Python and other supported languages
        if filepath.suffix == ".py":
            func_blocks = _extract_function_blocks_python(source, rel_path)
            class_blocks = _extract_class_blocks_python(source, rel_path)
        else:
            # Try tree-sitter extraction for other languages
            try:
                from redup.core.ts_extractor import extract_functions_treesitter, is_language_supported
                if is_language_supported(rel_path):
                    func_blocks = extract_functions_treesitter(source, rel_path)
                else:
                    func_blocks = []
            except ImportError:
                func_blocks = []
            class_blocks = []

        # Early skip: sliding-window blocks only when not functions-only
        if function_level_only:
            line_blocks = []
        else:
            sliding = _extract_blocks_sliding(lines, config.min_block_lines)
            line_blocks = [
                CodeBlock(file=rel_path, line_start=s, line_end=e, text=t)
                for s, e, t in sliding
            ]

        all_blocks = func_blocks + class_blocks + line_blocks

        sf = ScannedFile(path=rel_path, lines=lines, blocks=all_blocks)
        scanned.append(sf)
        stats.total_blocks += len(all_blocks)
    
    if total_files > 100:
        print(f"  Scanned {stats.total_blocks} blocks from {stats.files_scanned} files", file=sys.stderr, flush=True)

    stats.scan_time_ms = (time.monotonic() - t0) * 1000
    return scanned, stats
