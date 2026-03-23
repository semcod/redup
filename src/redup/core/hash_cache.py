"""Hash cache for incremental reDUP scans.

Stores SHA-256 hashes of files to skip unchanged files in subsequent scans.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class HashCache:
    """Cache for file hashes to enable incremental scanning."""
    
    def __init__(self, cache_path: Path | None = None):
        if cache_path is None:
            cache_path = Path(".redup_cache.json")
        self.cache_path = cache_path
        self._cache: dict[str, dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load cache from disk."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {}
    
    def save(self) -> None:
        """Save cache to disk."""
        try:
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except IOError:
            pass  # Cache save is best-effort
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        except (IOError, OSError):
            return ""
    
    def is_unchanged(self, file_path: Path, config_hash: str = "") -> bool:
        """Check if file is unchanged since last scan."""
        path_str = str(file_path)
        
        if path_str not in self._cache:
            return False
        
        entry = self._cache[path_str]
        current_hash = self.get_file_hash(file_path)
        
        # Check content hash and config
        return (
            entry.get("content_hash") == current_hash and
            entry.get("config_hash") == config_hash
        )
    
    def update(self, file_path: Path, file_results: dict[str, Any], config_hash: str = "") -> None:
        """Update cache entry for a file."""
        path_str = str(file_path)
        content_hash = self.get_file_hash(file_path)
        
        self._cache[path_str] = {
            "content_hash": content_hash,
            "config_hash": config_hash,
            "mtime": file_path.stat().st_mtime if file_path.exists() else 0,
            "results": file_results,
        }
    
    def invalidate(self, file_path: Path | None = None) -> None:
        """Invalidate cache for a file or entire cache."""
        if file_path is None:
            self._cache = {}
        else:
            path_str = str(file_path)
            self._cache.pop(path_str, None)
    
    def get_cached_results(self, file_path: Path) -> dict[str, Any] | None:
        """Get cached results for unchanged file."""
        path_str = str(file_path)
        
        if path_str in self._cache:
            return self._cache[path_str].get("results")
        return None
    
    def clear(self) -> None:
        """Clear entire cache."""
        self._cache = {}
        if self.cache_path.exists():
            self.cache_path.unlink()


def _config_to_hash(config: Any) -> str:
    """Convert config to a hash string for cache validation."""
    import json
    config_str = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(config_str.encode()).hexdigest()[:8]
