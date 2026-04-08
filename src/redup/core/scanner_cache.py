"""Scanner caching and path-filtering helpers."""
import fnmatch
import functools
from pathlib import Path


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
        return len(content) + 100

    def get_file_content(self, file_path: Path) -> bytes:
        """Get file content from cache or load from disk."""
        if file_path in self.cache:
            return self.cache[file_path]
        try:
            file_size = file_path.stat().st_size
            if file_size > self.max_memory_bytes // 2:
                return file_path.read_bytes()
            content = file_path.read_bytes()
            content_size = self._estimate_size(content)
            if self.current_memory + content_size <= self.max_memory_bytes:
                self.cache[file_path] = content
                self.current_memory += content_size
            else:
                self._evict_oldest(content_size)
                if content_size <= self.max_memory_bytes // 2:
                    self.cache[file_path] = content
                    self.current_memory += content_size
            return content
        except (OSError, UnicodeDecodeError):
            return b''

    def _evict_oldest(self, needed_size: int) -> None:
        """Evict oldest entries to make room."""
        items_to_remove = len(self.cache) // 2
        for _ in range(items_to_remove):
            if self.cache:
                oldest_path = next(iter(self.cache))
                oldest_content = self.cache.pop(oldest_path)
                self.current_memory -= self._estimate_size(oldest_content)


@functools.lru_cache(maxsize=1000)
def _should_exclude(path: Path, patterns: tuple[str, ...]) -> bool:
    """Check if a path matches any exclusion pattern with support for negation."""
    name = path.name
    str_path = str(path)
    for pattern in patterns:
        if not pattern.startswith('!'):
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(str_path, pattern):
                return True
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
    for pattern in patterns:
        if pattern.startswith('!'):
            include_pattern = pattern[1:]
            if fnmatch.fnmatch(name, include_pattern) or fnmatch.fnmatch(str_path, include_pattern):
                return False
            for part in path.parts:
                if fnmatch.fnmatch(part, include_pattern):
                    return False
    return False
