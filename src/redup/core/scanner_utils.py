"""Scanner file-collection and file-loading utilities."""

import mmap
import time
from pathlib import Path

from redup.core.scanner_filters import _collect_files, _is_test_file, _project_relative_path

__all__ = [
    "_collect_files",
    "_is_test_file",
    "_preload_files",
    "_project_relative_path",
]


def _read_file_with_mmap(file_path: Path) -> str:
    """Read file content using mmap for large files (>64KB)."""
    with open(file_path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        return mm.read().decode("utf-8", errors="replace")


def _read_file_safe(file_path: Path) -> str | None:
    """Safely read file content, using mmap for large files."""
    try:
        file_size = file_path.stat().st_size
        if file_size > 64 * 1024:
            return _read_file_with_mmap(file_path)
        return file_path.read_text("utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return None


def _load_files_simple(files: list[Path]) -> tuple[dict[Path, str], int]:
    """Load files without progress bar."""
    sources: dict[Path, str] = {}
    total_size = 0
    for file_path in files:
        content = _read_file_safe(file_path)
        if content is not None:
            sources[file_path] = content
            total_size += len(content)
    return sources, total_size


def _load_files_with_progress(files: list[Path]) -> tuple[dict[Path, str], int]:
    """Load files with rich progress bar."""
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    sources: dict[Path, str] = {}
    total_size = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task(f"Loading {len(files)} files to RAM...", total=len(files))
        for file_path in files:
            content = _read_file_safe(file_path)
            if content is not None:
                sources[file_path] = content
                total_size += len(content)
                progress.advance(task)

    return sources, total_size


def _load_all_files(files: list[Path]) -> tuple[dict[Path, str], int]:
    """Load all files with progress bar if available."""
    try:
        return _load_files_with_progress(files)
    except ImportError:
        return _load_files_simple(files)


def _print_load_result(sources: dict[Path, str], total_size: int, load_time: float) -> None:
    """Print load completion message."""
    size_mb = total_size // 1024 // 1024
    print(f"✅ Loaded {len(sources)} files ({size_mb}MB) in {load_time:.2f}s")


def _preload_files(files: list[Path], max_cache_mb: int = 256) -> dict[Path, str]:
    """Load ALL files into RAM at once for maximum speed."""
    if not files:
        return {}

    start_time = time.time()
    files.sort(key=lambda f: f.stat().st_size if f.exists() else 0)

    use_progress = len(files) > 50
    if use_progress:
        sources, total_size = _load_all_files(files)
    else:
        sources, total_size = _load_files_simple(files)

    _print_load_result(sources, total_size, time.time() - start_time)
    return sources
