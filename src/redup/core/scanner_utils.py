"""Scanner file-collection and file-loading utilities."""
import mmap
import time
from pathlib import Path

from redup.core.models import ScanConfig
from redup.core.scanner_cache import _should_exclude


def _project_relative_path(file_path: Path, project_root: Path) -> Path:
    """Return a path relative to the project root when possible."""
    try:
        return file_path.relative_to(project_root)
    except ValueError:
        return file_path


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    name = path.name.lower()
    dir_parts = [part.lower() for part in path.parts]
    if any(('pytest-' in part for part in dir_parts)):
        return False
    test_patterns = ['test_', '_test.', 'tests.', 'spec_', '_spec.']
    if any((pattern in name for pattern in test_patterns)):
        return True
    if any(('test' in part and 'pytest-' not in part for part in dir_parts)):
        return True
    return False


def _collect_files(config: ScanConfig) -> list[Path]:
    """Collect all files to scan based on configuration."""
    files: list[Path] = []
    for file_path in config.root.rglob('*'):
        if file_path.is_file():
            relative_path = _project_relative_path(file_path, config.root)
            if file_path.suffix not in config.extensions:
                continue
            if _should_exclude(relative_path, tuple(config.exclude_patterns)):
                continue
            if not config.include_tests and _is_test_file(relative_path):
                continue
            try:
                if file_path.stat().st_size > config.max_file_size_kb * 1024:
                    continue
            except OSError:
                continue
            files.append(file_path)
    return files


def _read_file_with_mmap(file_path: Path) -> str:
    """Read file content using mmap for large files (>64KB)."""
    with open(file_path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return mm.read().decode('utf-8', errors='replace')


def _read_file_safe(file_path: Path) -> str | None:
    """Safely read file content, using mmap for large files."""
    try:
        file_size = file_path.stat().st_size
        if file_size > 64 * 1024:
            return _read_file_with_mmap(file_path)
        return file_path.read_text('utf-8', errors='replace')
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
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    sources: dict[Path, str] = {}
    total_size = 0

    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        transient=True
    ) as progress:
        task = progress.add_task(f'Loading {len(files)} files to RAM...', total=len(files))
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
    print(f'✅ Loaded {len(sources)} files ({size_mb}MB) in {load_time:.2f}s')


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
