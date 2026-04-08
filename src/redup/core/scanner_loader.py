"""File loading and preload helpers for scanner operations."""
from __future__ import annotations

import mmap
import time
from pathlib import Path


def _preload_files(files: list[Path], max_cache_mb: int = 256) -> dict[Path, str]:
    """Load ALL files into RAM at once for maximum speed."""
    if not files:
        return {}
    start_time = time.time()
    total_size = 0
    files.sort(key=lambda f: f.stat().st_size if f.exists() else 0)
    if len(files) > 50:
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            with Progress(SpinnerColumn(), TextColumn('[progress.description]{task.description}'), BarColumn(), transient=True) as progress:
                task = progress.add_task(f'Loading {len(files)} files to RAM...', total=len(files))
                sources = {}
                for file_path in files:
                    try:
                        file_size = file_path.stat().st_size
                        if file_size > 64 * 1024:
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
                progress.console.print(f'✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s')
        except ImportError:
            sources = {}
            for file_path in files:
                try:
                    content = file_path.read_text('utf-8', errors='replace')
                    sources[file_path] = content
                    total_size += len(content)
                except (OSError, UnicodeDecodeError):
                    continue
            load_time = time.time() - start_time
            print(f'✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s')
    else:
        sources = {}
        for file_path in files:
            try:
                content = file_path.read_text('utf-8', errors='replace')
                sources[file_path] = content
                total_size += len(content)
            except (OSError, UnicodeDecodeError):
                continue
        load_time = time.time() - start_time
        print(f'✅ Loaded {len(sources)} files ({total_size // 1024 // 1024}MB) in {load_time:.2f}s')
    return sources
