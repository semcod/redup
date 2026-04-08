"""Scanner data models and strategy configuration."""
from __future__ import annotations

from dataclasses import dataclass, field


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
