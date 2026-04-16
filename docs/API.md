## Overview

reDUP provides a clean, well-documented API for programmatic code duplication analysis.

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

The TOON format includes actionable sections for refactoring:

- **HOTSPOTS** — Top 7 files with most duplicated lines (where to focus effort)
- **DUPLICATES** — All duplicate groups ranked by impact score
- **REFACTOR** — Prioritized refactoring suggestions with risk assessment
- **QUICK_WINS** — Low-risk, high-savings suggestions (do first)
- **DEPENDENCY_RISK** — Duplicates spanning multiple packages (cross-module risk)
- **EFFORT_ESTIMATE** — Time estimates per task with difficulty (easy/medium/hard)
- **METRICS-TARGET** — Current state vs zero-duplication goal

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

## Cross-Project Comparison

Compare two projects to detect shared code and receive refactoring recommendations (merge projects vs extract shared library).

### `compare_projects()`

```python
from pathlib import Path
from redup.core.comparator import compare_projects

comparison = compare_projects(
    project_a=Path("./project-a"),
    project_b=Path("./project-b"),
    similarity_threshold=0.75,
    use_semantic=False,
    extensions=[".py", ".js"],
    min_lines=3,
)

print(f"Found {comparison.total_matches} cross-project matches")
print(f"Shared LOC potential: {comparison.shared_loc_potential}")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_a` | `Path` | Required | Root of first project |
| `project_b` | `Path` | Required | Root of second project |
| `similarity_threshold` | `float` | `0.75` | Minimum similarity for matches |
| `use_semantic` | `bool` | `False` | Enable semantic similarity (slow) |
| `extensions` | `list[str]` | `[".py"]` | File extensions to scan |
| `min_lines` | `int` | `3` | Minimum block line count |

### `CrossProjectComparison`

```python
@dataclass
class CrossProjectComparison:
    project_a: Path
    project_b: Path
    matches: list[CrossProjectMatch]
    stats_a: dict  # {"files": N, "lines": N}
    stats_b: dict

    @property
    def total_matches(self) -> int
    @property
    def shared_loc_potential(self) -> int
```

### `CrossProjectMatch`

```python
@dataclass
class CrossProjectMatch:
    project_a: str
    project_b: str
    file_a: str
    file_b: str
    function_a: str
    function_b: str
    similarity: float        # 0.0-1.0
    similarity_type: str     # "exact" | "structural" | "lsh" | "semantic"
    lines_a: tuple[int, int]
    lines_b: tuple[int, int]
```

### Community Detection

```python
from redup.core.community import detect_communities, CodeCommunity

communities = detect_communities(comparison, min_similarity=0.70)

for c in communities[:5]:
    print(f"{c.extraction_candidate_name}: {c.avg_similarity:.2f} similarity, {c.total_loc} LOC")
```

### Decision Engine

```python
from redup.core.decision import recommend, RefactorDecision

rec = recommend(comparison, communities)

print(f"Decision: {rec.decision}")  # merge_projects | extract_shared_lib | keep_separate
print(f"Rationale: {rec.rationale}")
print(f"Confidence: {rec.confidence:.0%}")
```

### Complete Cross-Project Example

```python
from pathlib import Path
from redup.core.comparator import compare_projects
from redup.core.community import detect_communities
from redup.core.decision import recommend

# Compare two projects
comparison = compare_projects(
    Path("./legacy-service"),
    Path("./new-service"),
    similarity_threshold=0.70,
    extensions=[".py"],
)

# Detect communities (requires networkx)
try:
    communities = detect_communities(comparison, min_similarity=0.70)
    rec = recommend(comparison, communities)

    print(f"\nRecommendation: {rec.decision.value}")
    print(f"Overlap: {rec.overlap_percent:.1%}")
    print(f"Shared LOC: {rec.shared_loc}")
    print(f"\nTop extraction candidates:")
    for c in communities[:3]:
        print(f"  - {c.extraction_candidate_name}: {c.total_loc} LOC")
except ImportError:
    print("Install redup[compare] for community detection")
```

### Compare Report JSON Format

The `--output` flag exports a simplified, human-readable JSON report:

```json
{
  "project_a": "/path/to/project-a",
  "project_b": "/path/to/project-b",
  "stats": {
    "a": {"files": 551, "lines": 70758},
    "b": {"files": 99, "lines": 14849}
  },
  "total_matches": 35,
  "shared_loc_potential": 430,
  "recommendation": {
    "decision": "keep_separate",
    "rationale": "Projects are 1.0% similar — distinct concerns, no refactoring needed.",
    "overlap_pct": 0.0096,
    "shared_loc": 822,
    "confidence": 0.9
  },
  "communities": [
    {
      "name": "create_nfo_setup",
      "similarity": 1.0,
      "loc": 95,
      "members": [
        {"project": "A", "file": "shared/nfo_config_factory.py", "function": "create_nfo_setup"},
        {"project": "B", "file": "oqlos/shared/config_factory.py", "function": "create_nfo_setup"}
      ]
    }
  ],
  "matches": [
    {
      "type": "structural",
      "similarity": 1.0,
      "func_a": "create_nfo_setup",
      "func_b": "create_nfo_setup",
      "file_a": "shared/nfo_config_factory.py",
      "file_b": "oqlos/shared/config_factory.py",
      "loc": 95
    }
  ],
  "refactor_plan": {
    "summary": "...",
    "tasks": [...],
    "model": "openrouter/x-ai/grok-code-fast-1",
    "prompt_tokens": 2190,
    "completion_tokens": 1442,
    "duration_ms": 7025
  }
}
```

**Report Optimizations:**
- Relative file paths (strips project root prefix)
- Matches deduplicated by function pair (keeps highest similarity)
- Communities: compact member dicts instead of raw node keys
- Filtered trivial entries (matches >2 LOC, communities ≥8 LOC, cap 20)
- `refactor_plan` field added when using `--refactor-plan`

### LLM-Powered Refactoring Plan

Generate an AI-assisted refactoring TODO list from cross-project comparison data using `litellm`.

```python
from pathlib import Path
from redup.core.comparator import compare_projects
from redup.core.community import detect_communities
from redup.core.decision import recommend
from redup.core.refactor_advisor import (
    generate_refactor_plan,
    format_plan_markdown,
    format_plan_json,
)

# Compare projects and build report
comparison = compare_projects(
    Path("./project-a"),
    Path("./project-b"),
    similarity_threshold=0.75,
    extensions=[".py"],
)

communities = detect_communities(comparison, min_similarity=0.75)
rec = recommend(comparison, communities)

# Build compact report (compare_command._build_json_report format)
report = {
    "project_a": str(comparison.project_a),
    "project_b": str(comparison.project_b),
    "stats_a": comparison.stats_a,
    "stats_b": comparison.stats_b,
    "total_matches": comparison.total_matches,
    "shared_loc_potential": comparison.shared_loc_potential,
    "recommendation": {
        "decision": rec.decision.value,
        "rationale": rec.rationale,
        "overlap_percent": rec.overlap_percent,
        "shared_loc": rec.shared_loc,
        "confidence": rec.confidence,
    },
    "communities": [
        {
            "name": c.extraction_candidate_name,
            "similarity": c.avg_similarity,
            "loc": c.total_loc,
            "members": c.members,
        }
        for c in communities
    ],
    "matches": [
        {
            "similarity_type": m.similarity_type,
            "similarity": m.similarity,
            "function_a": m.function_a,
            "function_b": m.function_b,
            "file_a": m.file_a,
            "file_b": m.file_b,
            "lines_a": list(m.lines_a),
            "lines_b": list(m.lines_b),
        }
        for m in comparison.matches
    ],
}

# Generate LLM refactoring plan (requires litellm + .env with API keys)
try:
    plan = generate_refactor_plan(
        report,
        env_path=Path(".env"),  # Path to .env with OPENROUTER_API_KEY, LLM_MODEL
        model=None,  # Optional: override default model
    )

    # Display in console
    print(format_plan_markdown(plan))

    # Export to JSON
    plan_json = format_plan_json(plan)
    Path("refactor_plan.json").write_text(plan_json)

except ImportError:
    print("Install redup[llm] for LLM refactoring plans")
except RuntimeError as e:
    print(f"LLM error: {e}")
```

#### `RefactorPlan` Structure

```python
@dataclass
class RefactorPlan:
    summary: str                    # AI-generated overview
    tasks: list[RefactorTask]       # Prioritized refactoring tasks
    model: str                      # LLM model used
    prompt_tokens: int              # Input token count
    completion_tokens: int          # Output token count
    duration_ms: float              # Generation time

@dataclass
class RefactorTask:
    priority: str                   # "high" | "medium" | "low"
    action: str                     # Short action title
    description: str                # Detailed steps
    files: list[str]                # Files to modify
    loc_saved: int                  # Estimated LOC saved
    difficulty: str                 # "easy" | "medium" | "hard"
```

**Environment Variables (for litellm):**

- `OPENROUTER_API_KEY` — API key for LLM provider
- `LLM_MODEL` — Model name (default: `openrouter/x-ai/grok-code-fast-1`)

## CLI Command Architecture

### `compare_command` Module Structure

The `redup compare` CLI command is implemented with a clean, modular architecture following single-responsibility principle. Each phase of the comparison is handled by a dedicated helper function.

```
compare_command()
├── _parse_extensions()           # Parse --ext flag
├── _print_summary_table()        # Display project stats
├── _detect_communities()         # Run community detection
├── _print_recommendation()       # Show decision + rationale
│   └── _print_communities_table()  # Communities breakdown
├── _print_match_details()        # Top matches table
├── _generate_llm_plan()          # LLM refactoring plan (optional)
└── _export_json()                # Save report to file
```

### Internal Helper Functions

#### `_parse_extensions(extensions: str | None) -> list[str] | None`

Parse comma-separated file extensions from CLI argument.

```python
# Example: "--ext .py,.js,.ts" → [".py", ".js", ".ts"]
ext_list = _parse_extensions(".py,.js,.ts")
```

#### `_detect_communities(comparison, threshold, no_community) -> list[CodeCommunity]`

Conditionally run community detection with graceful fallback if `networkx` is not installed.

**Behavior:**
- Returns `[]` if `--no-community` flag set or no matches found
- Prints yellow warning if `networkx` not installed
- Requires `redup[compare]` extra dependency

#### `_build_json_report(comparison, communities) -> dict`

Build compact JSON report with deduplication and filtering.

**Pipeline:**
1. `_make_relative_path()` — Strip project prefixes from paths
2. `_deduplicate_matches()` — Group by (func_a, func_b, file_a, file_b), keep highest similarity
3. `_filter_significant_communities()` — Filter LOC ≥ 8, cap at 20
4. `_build_recommendation_dict()` — Generate recommendation or `None`

**Output format:**
```json
{
  "project_a": "./project-a",
  "project_b": "./project-b",
  "stats": {"a": {...}, "b": {...}},
  "total_matches": 42,
  "shared_loc_potential": 1200,
  "recommendation": {
    "decision": "extract_shared_lib",
    "rationale": "25% overlap (1200 shared lines, 5 clusters)...",
    "overlap_pct": 0.2534,
    "shared_loc": 1200,
    "confidence": 0.8
  },
  "communities": [...],
  "matches": [...]
}
```

#### `_generate_llm_plan(report, refactor_plan, env_file, llm_model, comparison) -> RefactorPlan | None`

Generate LLM-powered refactoring plan using `litellm`.

**Requirements:**
- `--refactor-plan` flag must be set
- `comparison.total_matches > 0`
- `.env` file with `OPENROUTER_API_KEY`

**Error handling:**
- `ImportError` → prints yellow warning (litellm not installed)
- `RuntimeError` → prints red error (LLM API failure)

### Report Deduplication Logic

The `_deduplicate_matches()` function handles a common edge case: when the same function pair is detected by multiple similarity tiers (hash, LSH, semantic), only the highest similarity score is retained.

```python
key = (m.function_a, m.function_b, m.file_a, m.file_b)
if key not in deduped or m.similarity > deduped[key]["similarity"]:
    deduped[key] = {...}  # Keep best match only
```

## Modular Architecture (v0.5.0+)

### MCP Server Package

The MCP server has been refactored into a modular package for better maintainability:

```
redup/mcp/
├── __init__.py      # Public API exports
├── handlers.py      # Tool handlers (8 tools)
├── schemas.py       # JSON-RPC schemas
├── server.py        # JSON-RPC server core
└── utils.py         # Shared utilities
```

#### Direct MCP Package Usage

```python
from redup.mcp import (
    TOOL_HANDLERS,
    TOOL_SCHEMA_REDUP,
    handle_analyze_project,
    handle_compare_scans,
    run_server,
)

# Run specific handler directly
result = handle_analyze_project({
    "path": "./my_project",
    "format": "json",
    "mode": "optimized"
})

# Or start the full MCP server
run_server()  # Reads/writes JSON-RPC from stdin/stdout
```

### Pipeline Package

The analysis pipeline has been split into focused modules:

```
redup/core/pipeline/
├── __init__.py          # Main entry points (analyze, analyze_optimized, analyze_parallel)
├── phases.py            # Scan and process phases
├── duplicate_finder.py  # Exact, structural, near-duplicate, semantic finding
└── groups.py            # Group creation, deduplication, matching
```

#### Using Individual Pipeline Phases

For fine-grained control over the analysis pipeline:

```python
from redup import ScanConfig
from redup.core.pipeline.phases import scan_phase, process_blocks
from redup.core.pipeline.duplicate_finder import (
    find_duplicates_phase_optimized,
    find_exact_groups,
    find_structural_groups,
)
from redup.core.pipeline.groups import deduplicate_groups, blocks_to_group

# Phase 1: Scan
config = ScanConfig(root=Path("./src"), extensions=[".py"])
scanned_files, stats = scan_phase(config, function_level_only=True)

# Phase 2: Process blocks
all_blocks = process_blocks(scanned_files, function_level_only=True)

# Phase 3: Find duplicates with custom logic
from redup.core.hasher import build_hash_index
index = build_hash_index(all_blocks)

# Get exact duplicates only
exact_groups = find_exact_groups(index)

# Or get structural duplicates
structural_groups = find_structural_groups(index, exact_groups)

# Phase 4: Deduplicate
final_groups = deduplicate_groups(exact_groups + structural_groups)
```

#### Advanced: Custom Group Processing

```python
from redup.core.pipeline.groups import blocks_to_group, calculate_similarity
from redup.core.hasher import HashedBlock
from redup.core.models import DuplicateType

# Create custom group from hashed blocks
custom_group = blocks_to_group(
    group_id="CUSTOM001",
    blocks=hashed_blocks_list,  # list[HashedBlock]
    dup_type=DuplicateType.STRUCTURAL,
    similarity=0.92,
    normalized_hash="structural_hash_abc123"
)

# Calculate similarity for match results
from redup.core.matcher import MatchResult
similarity = calculate_similarity(match_results_list)
```

### Scanner Module Improvements

The scanner has been refactored with extracted helper functions for better testability:

```python
from redup.core.scanner import (
    scan_project,
    # New internal helpers (for advanced use/testing)
    _get_source_for_file,
    _extract_blocks_for_file,
    _process_single_file,
    _init_strategy,
    _init_file_loading,
)

# Process single file with custom logic
from pathlib import Path
from redup.core.models import ScanConfig

config = ScanConfig(root=Path("./src"))
scanned = _process_single_file(
    file_path=Path("./src/my_module.py"),
    config=config,
    preloaded_sources=None,
    file_cache=None,
    function_level_only=True
)
```

## MCP Server API

reDUP provides an MCP (Model Context Protocol) server for integration with AI assistants and IDE plugins.

### Starting the MCP Server

```python
from redup.mcp import run_server

# Run the MCP server (stdio or HTTP mode)
run_server(transport="stdio")  # or "http" with --port
```

### Available Tools

The MCP server exposes these tools for AI consumption:

| Tool | Description |
|------|-------------|
| `analyze_project` | Full duplication analysis with configurable parameters |
| `find_duplicates` | Quick duplicate detection for specific files |
| `check_project` | Quality gate check with pass/fail result |
| `compare_scans` | Compare two scan results for differences |
| `compare_projects` | Cross-project duplicate detection |
| `suggest_refactoring` | Generate prioritized refactoring suggestions |
| `project_info` | Get project metadata and statistics |

### Tool Schemas

```python
from redup.mcp import TOOL_SCHEMA_REDUP

# Get JSON schema for all tools
print(TOOL_SCHEMA_REDUP)
```

### Example: analyze_project Tool

```python
{
  "path": "./my_project",
  "extensions": [".py", ".js"],
  "min_lines": 3,
  "min_similarity": 0.85,
  "include_tests": False,
  "parallel": True
}
```

### Response Format

```python
{
  "summary": {
    "total_groups": 15,
    "total_saved_lines": 217,
    "files_scanned": 86,
    "total_lines": 10453
  },
  "hotspots": [...],  # Top files with most duplication
  "groups": [...],    # Duplicate groups with fragments
  "suggestions": [...] # Prioritized refactoring suggestions
}
```

### Running via CLI

```bash
# Start MCP server on stdio (default)
redup-mcp

# Start HTTP server
redup-mcp --transport http --port 8000
```

## Universal Fuzzy Similarity Detection

Cross-language fuzzy similarity detection works across all 35+ supported languages.

### UniversalFuzzyExtractor

```python
from redup.core.universal_fuzzy import UniversalFuzzyExtractor

extractor = UniversalFuzzyExtractor()

# Extract semantic signatures from any language
signatures = extractor.extract_signatures(
    source_code,
    language="python",  # or any supported language
    file_path="example.py"
)
```

### UniversalFuzzyDetector

```python
from redup.core.universal_fuzzy import UniversalFuzzyDetector

detector = UniversalFuzzyDetector(threshold=0.65)

# Find similar components across different languages
similar_pairs = detector.find_similar_pairs(signatures)

# Example: JavaScript ↔ Python function similarity
# Returns: [(sig1, sig2, 0.70), ...]  # 70% similarity
```

### UniversalSignature

```python
from redup.core.universal_fuzzy import UniversalSignature

# Semantic signature for cross-language comparison
signature = UniversalSignature(
    component_type="function",      # function, class, api_endpoint, etc.
    normalized_structure="...",   # Language-agnostic structure
    complexity_score=0.5,           # 0.0-1.0
    semantic_tokens=["auth", "validate"]
)
```

### Supported Pattern Types

Universal detection works for:

- **Functions**: Across all programming languages
- **Classes/OOP**: Object-oriented patterns
- **API Endpoints**: REST/graphql route handlers
- **Database Queries**: SQL patterns across dialects
- **Web Components**: Forms, cards, buttons, navigation
- **Auth/Validation**: Security patterns
- **Error Handling**: Exception handling patterns
- **Logging**: Logging framework patterns
- **Configuration**: Config file patterns
- **Infrastructure**: Docker, Nginx, Makefile patterns

### Cross-Language Similarity Examples

```python
# JavaScript function ↔ Python function: 65% similarity
# Docker config ↔ YAML config: 40% similarity
# JS auth pattern ↔ Python auth pattern: 70% similarity
```

## Tree-Sitter Multi-Language Extractor

Modular tree-sitter extraction for 35+ languages with a clean, extensible architecture.

### Architecture

```
ts_extractor/
├── __init__.py          # Public API exports
├── main.py              # Core extraction API
├── config.py            # Language mappings & registry
├── dispatcher.py        # Language routing
└── extractors/          # Modular extractor implementations
    ├── c_family.py      # C, C++, C#, Objective-C
    ├── go.py            # Go language
    ├── java.py          # Java, Scala, Kotlin
    ├── markup.py        # HTML, XML, Svelte, Vue
    ├── query.py         # SQL, GraphQL
    ├── scripting.py     # Python, Ruby, PHP, Lua
    ├── shell.py         # Bash, Zsh, Fish
    ├── stylesheet.py    # CSS, SCSS, Sass, Less
    └── web.py           # JavaScript, TypeScript
```

### Main API Functions

```python
from redup.core.ts_extractor import (
    extract_functions_treesitter,
    get_supported_languages,
    is_language_supported,
)

# Extract functions from any supported language
blocks = extract_functions_treesitter(source_code, file_path="example.go")

# Check language support
print(is_language_supported("example.rs"))  # True for Rust
print(get_supported_languages())  # List of 35+ languages
```

### Language Registry

```python
from redup.core.ts_extractor import language_registry, LANGUAGE_MAPPING

# Access language configuration
print(LANGUAGE_MAPPING[".rs"])  # "rust"
print(LANGUAGE_MAPPING["Dockerfile"])  # "dockerfile"

# Registry provides parser access
parser = language_registry.get_language("go")
```

### Dispatcher System

```python
from redup.core.ts_extractor.dispatcher import (
    language_dispatcher,
    initialize_language_dispatcher,
)

# Initialize all language extractors
initialize_language_dispatcher()

# Route to appropriate extractor
extractor = language_dispatcher.get_extractor("rust")
blocks = extractor(node, source_lines, file_path)
```

### Supported Languages (35+)

**Programming:** Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, C#, Scala, Kotlin, Swift, Objective-C, Ruby, PHP, Lua, Bash

**Web:** HTML, XML, Svelte, Vue, Embedded Templates (ERB, EJS, Handlebars)

**Styling:** CSS, SCSS, Sass, Less

**Data:** JSON, YAML, TOML, XML, Markdown

**Query:** SQL, GraphQL

**Infrastructure:** Dockerfile, Makefile, Nginx

**Configuration:** Vim, Regex

## Universal Fuzzy Similarity Detection

Cross-language fuzzy similarity detection for identifying similar code patterns across different programming languages and DSLs.

### `UniversalFuzzyExtractor`

Extracts semantic patterns from any supported language:

```python
from redup.core.universal_fuzzy import UniversalFuzzyExtractor

extractor = UniversalFuzzyExtractor()

# Extract from any language
patterns = extractor.extract_patterns(source_code, language="javascript")
for pattern in patterns:
    print(f"{pattern.pattern_type}: {pattern.name} (confidence: {pattern.confidence:.2f})")
```

**Supported Language Families:**
- **Programming**: Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Scala, Kotlin, Swift, Objective-C, Ruby, PHP, Lua, Bash
- **Web**: HTML, XML, Svelte, Vue
- **Styling**: CSS, SCSS, Sass, Less
- **Data**: JSON, YAML, TOML, Markdown
- **Query**: SQL, GraphQL
- **Infrastructure**: Dockerfile, Nginx, Make

### `UniversalFuzzyDetector`

Detects similarities between code blocks from different languages:

```python
from redup.core.universal_fuzzy import UniversalFuzzyDetector

detector = UniversalFuzzyDetector(similarity_threshold=0.6)

# Compare blocks from different languages
similarity = detector.compute_similarity(
    block_a=js_function,
    block_b=py_function,
    language_a="javascript",
    language_b="python"
)

print(f"Cross-language similarity: {similarity:.2%}")
```

**Pattern Types Detected:**
- Functions, classes, methods
- API endpoints, database queries
- Authentication, validation, error handling, logging
- Web components (forms, tables, navigation, cards, modals)
- Configuration schemas, metadata
- Infrastructure services, networks, volumes

### Universal Signature

Creates language-agnostic signatures for comparison:

```python
from redup.core.universal_fuzzy import UniversalSignature

sig = UniversalSignature.from_code(
    code=source,
    language="javascript",
    normalize_identifiers=True,
    remove_comments=True
)

print(f"Complexity score: {sig.complexity_score:.2f}")
print(f"Structural hash: {sig.structural_hash}")
```

### CLI Usage with `--fuzzy`

```bash
# Enable universal fuzzy matching for all file types
redup scan . --fuzzy --ext .py,.js,.ts,.go

# Cross-project fuzzy comparison
redup compare ./project-a ./project-b --fuzzy --threshold 0.65
```

## ts_extractor Modular Architecture

The tree-sitter extractor has been refactored from a 782-line god module into a clean, maintainable package structure:

```
redup/core/ts_extractor/
├── __init__.py          # Public API exports
├── config.py            # LanguageRegistry, LANGUAGE_MAPPING
├── dispatcher.py        # Language dispatcher initialization
├── main.py              # Main extraction API (extract_functions_treesitter)
└── extractors/
    ├── __init__.py      # Aggregates all extractors
    ├── base.py          # Shared utilities (traverse_tree, create_code_block)
    ├── web.py           # JavaScript/TypeScript
    ├── c_family.py      # C/C++
    ├── markup.py        # HTML/XML
    ├── stylesheet.py    # CSS
    ├── query.py         # SQL
    ├── dotnet.py        # C#
    ├── ruby.py          # Ruby
    ├── php.py           # PHP
    └── shell.py         # Bash
```

### Using Individual Extractors

```python
from redup.core.ts_extractor.extractors.web import extract_functions_javascript
from redup.core.ts_extractor.extractors.c_family import extract_functions_c_cpp
from redup.core.ts_extractor.extractors.markup import extract_blocks_html_xml

# Extract JavaScript functions
js_blocks = extract_functions_javascript(tree.root_node, source_lines, file_path)

# Extract C++ functions
cpp_blocks = extract_functions_c_cpp(tree.root_node, source_lines, file_path)

# Extract HTML blocks
html_blocks = extract_blocks_html_xml(tree.root_node, source_lines, file_path)
```

### Base Utilities for Custom Extractors

```python
from redup.core.ts_extractor.extractors.base import (
    traverse_tree,
    create_code_block,
    get_node_text,
)

# Build custom extractor
def my_custom_extractor(node, source_lines, file_path):
    matchers = {
        "function_definition": lambda n, lines, path: create_code_block(
            n, lines, path, "function"
        ),
        "class_declaration": lambda n, lines, path: create_code_block(
            n, lines, path, "class"
        ),
    }
    return traverse_tree(node, source_lines, file_path, matchers)
```

### Backward Compatibility

All existing imports continue to work:

```python
# These still work (backward compatible)
from redup.core.ts_extractor import (
    extract_functions_treesitter,
    get_supported_languages,
    is_language_supported,
    _extract_blocks_html_xml,  # For tests
    _extract_functions_c_cpp,     # For tests
)
```

## Performance Tips

1. **Use parallel scanning** for large projects
2. **Set appropriate `min_block_lines`** to reduce noise
3. **Filter extensions** to avoid scanning irrelevant files
4. **Consider function-level only** for faster initial scans
5. **Skip semantic tier** unless needed — it's 10x slower
6. **Use pipeline phases directly** for custom analysis workflows
7. **Use fuzzy detection sparingly** — it's powerful but slower than exact matching

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

# Fast cross-project comparison
comparison = compare_projects(
    Path("./project-a"),
    Path("./project-b"),
    similarity_threshold=0.80,  # Higher = fewer candidates
    use_semantic=False,  # Skip slow semantic tier
)
```
