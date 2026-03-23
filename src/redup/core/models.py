"""Data models for reDUP analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class DuplicateType(str, Enum):
    """How the duplicate was detected."""

    EXACT = "exact"
    STRUCTURAL = "structural"
    FUZZY = "fuzzy"
    NEAR_DUPLICATE = "near_duplicate"


class RefactorAction(str, Enum):
    """Proposed refactoring action."""

    EXTRACT_FUNCTION = "extract_function"
    EXTRACT_CLASS = "extract_class"
    EXTRACT_MODULE = "extract_module"
    INLINE = "inline"


class RiskLevel(str, Enum):
    """Risk of the proposed refactoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ScanConfig:
    """Configuration for project scanning."""

    root: Path = field(default_factory=lambda: Path("."))
    extensions: list[str] = field(default_factory=lambda: [".py"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            # Universal system files (but not normal code files)
            ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", ".tox", ".nox", ".coverage", "htmlcov", ".DS_Store",
            "Thumbs.db", "*.swp", "*.swo", "*~", ".vscode", ".idea",
            
            # Python specific
            "*.pyc", "*.pyo", "*.pyd", "$py.class",
            "python*", "python3*", "Python*",
            "venv*", "env*", ".venv*", ".env*",
            "*.egg-info", "*.egg", "build", "dist",
            ".installer", ".eggs", "lib", "lib64", "parts", "sdist", "var", "wheels",
            
            # Node.js/JavaScript
            "node_modules", "npm-debug.log*", "yarn-debug.log*", "yarn-error.log*",
            "pnpm-debug.log*", ".npm", ".yarn-integrity", ".eslintcache", ".stylelintcache",
            ".next", ".nuxt", ".vuepress/dist",
            
            # Java/Maven/Gradle
            "target", "build", "out", ".classpath", ".project", ".settings",
            ".mvn", "gradle", ".gradle", "*.class", "*.jar", "*.war", "*.ear", "*.aar",
            
            # Rust
            "target", "Cargo.lock", "**/*.rs.bk",
            
            # Go
            "vendor", "*.exe", "*.exe~", "*.dll", "*.so", "*.dylib", "*.test", "*.out",
            
            # Docker
            ".dockerignore", ".docker",
            
            # Mobile
            "android/app/build", "ios/build", "*.apk", "*.ipa", "*.xcarchive",
            
            # Database
            "*.db", "*.sqlite", "*.sqlite3", "data", "logs",
            
            # Cloud/DevOps
            ".terraform", ".terraform.lock.hcl", "*.tfstate", "*.tfstate.*", ".ansible", ".kube",
            
            # General build/cache
            "cache", ".cache", "tmp", ".tmp", "*.tmp", "*.temp", "*.bak", "*.backup",
            
            # Package managers
            "composer.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
            "poetry.lock", "Pipfile.lock", "Gemfile.lock",
            
            # Logs
            "*.log", "logs",
        ]
    )
    min_block_lines: int = 3
    min_similarity: float = 0.85
    max_file_size_kb: int = 1024
    include_tests: bool = False
    enable_cache: bool = False
    parallel_workers: int = 1
    _parallel_enabled: bool = False
    _memory_cache: bool = True
    _max_cache_mb: int = 512
    functions_only: bool = True
    fuzzy_enabled: bool = False
    fuzzy_threshold: float = 0.8
    # LSH configuration
    lsh_enabled: bool = True
    lsh_min_lines: int = 50
    lsh_threshold: float = 0.8
    # Performance configuration
    parallel_workers: int | None = None  # None = auto-detect CPU count
    cache_dir: Path = field(default_factory=lambda: Path(".redup/cache"))
    use_ultra_fast_scanner: bool = True


@dataclass
class DuplicateFragment:
    """A single occurrence of a duplicated code fragment."""

    file: str
    line_start: int
    line_end: int
    text: str = ""
    function_name: str | None = None
    class_name: str | None = None

    @property
    def line_count(self) -> int:
        return self.line_end - self.line_start + 1


@dataclass
class DuplicateGroup:
    """A cluster of duplicated code fragments."""

    id: str
    duplicate_type: DuplicateType
    fragments: list[DuplicateFragment] = field(default_factory=list)
    similarity_score: float = 1.0
    normalized_hash: str = ""
    normalized_name: str | None = None

    @property
    def occurrences(self) -> int:
        return len(self.fragments)

    @property
    def total_lines(self) -> int:
        if not self.fragments:
            return 0
        return self.fragments[0].line_count

    @property
    def saved_lines_potential(self) -> int:
        """Lines saved if extracted: L * (N - 1)."""
        if self.occurrences <= 1:
            return 0
        return self.total_lines * (self.occurrences - 1)

    @property
    def impact_score(self) -> float:
        return float(self.saved_lines_potential) * self.similarity_score


@dataclass
class RefactorSuggestion:
    """A concrete refactoring proposal for a duplicate group."""

    group_id: str
    action: RefactorAction
    new_module: str
    function_name: str | None = None
    class_name: str | None = None
    original_files: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    priority: int = 0
    rationale: str = ""


@dataclass
class ScanStats:
    """Statistics from the scanning phase."""

    files_scanned: int = 0
    files_skipped: int = 0
    total_lines: int = 0
    total_blocks: int = 0
    scan_time_ms: float = 0.0


@dataclass
class DuplicationMap:
    """Complete result of a reDUP analysis run."""

    project_path: str = ""
    config: ScanConfig | None = None
    groups: list[DuplicateGroup] = field(default_factory=list)
    suggestions: list[RefactorSuggestion] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_fragments(self) -> int:
        return sum(g.occurrences for g in self.groups)

    @property
    def total_saved_lines(self) -> int:
        return sum(g.saved_lines_potential for g in self.groups)

    def sorted_by_impact(self) -> list[DuplicateGroup]:
        """Return groups sorted by refactoring impact (highest first)."""
        return sorted(self.groups, key=lambda g: g.impact_score, reverse=True)
