# 📚 API Documentation

## Overview

reDUP provides a clean, well-documented API for programmatic code duplication analysis.

## Core API

### `ScanConfig`

Configuration object for scanning projects.

```python
from redup import ScanConfig
from pathlib import Path

config = ScanConfig(
    root=Path("./my_project"),
    extensions=[".py", ".js", ".ts"],
    min_block_lines=3,
    min_similarity=0.85,
    include_tests=False,
    parallel=True,
    max_workers=4
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | `Path` | Required | Project root directory |
| `extensions` | `list[str]` | `[".py"]` | File extensions to scan |
| `min_block_lines` | `int` | `3` | Minimum lines for duplicate detection |
| `min_similarity` | `float` | `0.85` | Similarity threshold (0.0-1.0) |
| `include_tests` | `bool` | `False` | Include test files in scan |
| `parallel` | `bool` | `False` | Enable parallel processing |
| `max_workers` | `int` | `None` | Max parallel workers (auto if None) |

### `analyze()`

Main entry point for duplication analysis.

```python
from redup import analyze, ScanConfig
from pathlib import Path

config = ScanConfig(root=Path("."), extensions=[".py"])
result = analyze(config=config)
```

#### Returns

`DuplicationMap` object containing:
- `groups`: List of duplicate groups
- `suggestions`: Refactoring suggestions
- `stats`: Scan statistics

### `scan_project()`

Lower-level function for just scanning (no analysis).

```python
from redup.core.scanner import scan_project
from redup import ScanConfig

config = ScanConfig(root=Path("."), extensions=[".py"])
blocks = scan_project(config)
```

#### Returns

`list[CodeBlock]` - Raw code blocks from scanning.

## Data Models

### `DuplicationMap`

```python
@dataclass
class DuplicationMap:
    groups: list[DuplicateGroup]
    suggestions: list[RefactorSuggestion]
    stats: ScanStats
    project_path: Path
```

### `DuplicateGroup`

```python
@dataclass
class DuplicateGroup:
    id: str
    duplicate_type: DuplicateType
    fragments: list[DuplicateFragment]
    similarity_score: float
    impact_score: int
    saved_lines_potential: int
    saved_lines: int
```

### `DuplicateFragment`

```python
@dataclass
class DuplicateFragment:
    file: str
    line_start: int
    line_end: int
    text: str
    function_name: str | None
    class_name: str | None
    line_count: int
```

### `RefactorSuggestion`

```python
@dataclass
class RefactorSuggestion:
    group_id: str
    action: RefactorAction
    new_module: str
    function_name: str | None
    class_name: str | None
    original_files: list[str]
    risk_level: RiskLevel
    priority: int
    rationale: str
```

## Reporters

### JSON Reporter

```python
from redup.reporters.json_reporter import to_json

json_output = to_json(duplication_map)
# Save to file
Path("duplicates.json").write_text(json_output)
```

### TOON Reporter (LLM-optimized)

```python
from redup.reporters.toon_reporter import to_toon

toon_output = to_toon(duplication_map)
print(toon_output)  # Compact format for LLMs
```

### Enhanced Reporter

```python
from redup.reporters.enhanced_reporter import EnhancedReporter

reporter = EnhancedReporter(duplication_map)
metrics = reporter.generate_metrics_report()
viz_data = reporter.generate_visualization_data()

# Save comprehensive report
reporter.save_enhanced_report(Path("enhanced_report.json"))
```

### YAML Reporter

```python
from redup.reporters.yaml_reporter import to_yaml

yaml_output = to_yaml(duplication_map)
Path("duplicates.yaml").write_text(yaml_output)
```

## Examples

### Basic Usage

```python
from pathlib import Path
from redup import analyze, ScanConfig

# Scan current directory for Python duplicates
config = ScanConfig(
    root=Path("."),
    extensions=[".py"],
    min_block_lines=5
)

result = analyze(config)
print(f"Found {len(result.groups)} duplicate groups")
print(f"Can save {result.total_saved_lines} lines")
```

### Advanced Analysis

```python
from pathlib import Path
from redup import analyze, ScanConfig
from redup.reporters.enhanced_reporter import EnhancedReporter

# Comprehensive analysis with multiple languages
config = ScanConfig(
    root=Path("./large_project"),
    extensions=[".py", ".js", ".ts", ".go"],
    min_block_lines=3,
    min_similarity=0.9,
    parallel=True,
    max_workers=8
)

result = analyze(config)

# Generate detailed metrics
reporter = EnhancedReporter(result)
metrics = reporter.generate_metrics_report()

print(f"Scan metrics: {metrics['scan_metrics']}")
print(f"Language breakdown: {metrics['language_metrics']}")
print(f"Refactoring opportunities: {metrics['refactoring_metrics']}")
```

### Custom Processing

```python
from pathlib import Path
from redup import ScanConfig
from redup.core.pipeline import analyze
from redup.core.hasher import build_hash_index
from redup.core.matcher import refine_candidates

# Custom pipeline with fine-grained control
config = ScanConfig(root=Path("."), extensions=[".py"])

# Step 1: Scan
blocks = scan_project(config)

# Step 2: Hash
hash_index = build_hash_index(blocks)

# Step 3: Find candidates
exact_candidates = find_exact_duplicates(hash_index)
structural_candidates = find_structural_duplicates(hash_index)

# Step 4: Refine with similarity matching
refined_groups = refine_candidates(exact_candidates + structural_candidates)

print(f"Found {len(refined_groups)} refined duplicate groups")
```

## Error Handling

```python
from pathlib import Path
from redup import analyze, ScanConfig
import logging

logging.basicConfig(level=logging.INFO)

try:
    config = ScanConfig(root=Path("./project"))
    result = analyze(config)
except Exception as e:
    logging.error(f"Analysis failed: {e}")
    raise
```

## Performance Tips

1. **Use parallel scanning** for large projects
2. **Set appropriate `min_block_lines`** to reduce noise
3. **Filter extensions** to avoid scanning irrelevant files
4. **Consider function-level only** for faster initial scans

```python
# Fast scan for large projects
config = ScanConfig(
    root=Path("./huge_project"),
    extensions=[".py"],
    min_block_lines=10,  # Higher threshold
    parallel=True,
    max_workers=16
)

result = analyze(config, function_level_only=True)
```
