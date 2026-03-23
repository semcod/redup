"""Project scanner — walks directories, reads files, produces code blocks."""

from __future__ import annotations

import fnmatch
import functools
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
    root = config.root.resolve()
    for ext in config.extensions:
        for path in root.rglob(f"*{ext}"):
            if _should_exclude(path, tuple(config.exclude_patterns)):
                continue
            if not config.include_tests and _is_test_file(path):
                continue
            if path.stat().st_size > config.max_file_size_kb * 1024:
                continue
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


def _extract_blocks_sliding(lines: list[str], min_lines: int) -> list[tuple[int, int, str]]:
    """Extract overlapping blocks using a sliding window.

    Returns list of (start_line, end_line, normalized_text).
    Lines are 1-indexed.
    """
    blocks: list[tuple[int, int, str]] = []
    non_empty = [(i, line) for i, line in enumerate(lines) if line.strip()]
    if len(non_empty) < min_lines:
        return blocks

    for window_size in range(min_lines, min(len(non_empty), 50) + 1):
        for start_idx in range(len(non_empty) - window_size + 1):
            chunk = non_empty[start_idx : start_idx + window_size]
            first_line = chunk[0][0] + 1
            last_line = chunk[-1][0] + 1
            # Optimized: reduce string operations
            lines = [line.strip() for _, line in chunk]
            text = "\n".join(lines)
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

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno
            end = node.end_lineno or start
            lines = source.splitlines()
            text = "\n".join(lines[start - 1 : end])

            # Get method names for context
            method_names = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

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

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = node.end_lineno or start
            lines = source.splitlines()
            text = "\n".join(lines[start - 1 : end])

            class_name = None
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef):
                    for child in ast.walk(parent):
                        if child is node:
                            class_name = parent.name
                            break

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


def scan_project(config: ScanConfig | None = None) -> tuple[list[ScannedFile], ScanStats]:
    """Scan a project and return files with their code blocks.

    Returns:
        Tuple of (scanned_files, scan_stats).
    """
    if config is None:
        config = ScanConfig()

    t0 = time.monotonic()
    stats = ScanStats()
    scanned: list[ScannedFile] = []

    for filepath in _collect_files(config):
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            stats.files_skipped += 1
            continue

        lines = source.splitlines()
        rel_path = str(filepath.relative_to(config.root.resolve()))

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

        # Also extract sliding-window blocks for line-level matching
        sliding = _extract_blocks_sliding(lines, config.min_block_lines)
        line_blocks = [
            CodeBlock(file=rel_path, line_start=s, line_end=e, text=t)
            for s, e, t in sliding
        ]

        all_blocks = func_blocks + class_blocks + line_blocks

        sf = ScannedFile(path=rel_path, lines=lines, blocks=all_blocks)
        scanned.append(sf)
        stats.files_scanned += 1
        stats.total_lines += len(lines)
        stats.total_blocks += len(all_blocks)

    stats.scan_time_ms = (time.monotonic() - t0) * 1000
    return scanned, stats
