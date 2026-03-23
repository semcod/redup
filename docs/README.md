<!-- code2docs:start --># redup

![version](https://img.shields.io/badge/version-0.1.0-blue) ![python](https://img.shields.io/badge/python-%3E%3D3.10-blue) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey) ![functions](https://img.shields.io/badge/functions-148-green)
> **148** functions | **20** classes | **30** files | CC̄ = 3.9

> Auto-generated project documentation from source code analysis.

**Author:** Tom Sapletta  
**License:** Apache-2.0[(LICENSE)](./LICENSE)  
**Repository:** [https://github.com/semcod/redup](https://github.com/semcod/redup)

## Installation

### From PyPI

```bash
pip install redup
```

### From Source

```bash
git clone https://github.com/semcod/redup
cd redup
pip install -e .
```

### Optional Extras

```bash
pip install redup[all]    # all optional features
pip install redup[fuzzy]    # fuzzy features
pip install redup[ast]    # ast features
pip install redup[lsh]    # lsh features
pip install redup[dev]    # development tools
```

## Quick Start

### CLI Usage

```bash
# Generate full documentation for your project
redup ./my-project

# Only regenerate README
redup ./my-project --readme-only

# Preview what would be generated (no file writes)
redup ./my-project --dry-run

# Check documentation health
redup check ./my-project

# Sync — regenerate only changed modules
redup sync ./my-project
```

### Python API

```python
from redup import generate_readme, generate_docs, Code2DocsConfig

# Quick: generate README
generate_readme("./my-project")

# Full: generate all documentation
config = Code2DocsConfig(project_name="mylib", verbose=True)
docs = generate_docs("./my-project", config=config)
```

## Generated Output

When you run `redup`, the following files are produced:

```
<project>/
├── README.md                 # Main project README (auto-generated sections)
├── docs/
│   ├── api.md               # Consolidated API reference
│   ├── modules.md           # Module documentation with metrics
│   ├── architecture.md      # Architecture overview with diagrams
│   ├── dependency-graph.md  # Module dependency graphs
│   ├── coverage.md          # Docstring coverage report
│   ├── getting-started.md   # Getting started guide
│   ├── configuration.md    # Configuration reference
│   └── api-changelog.md    # API change tracking
├── examples/
│   ├── quickstart.py       # Basic usage examples
│   └── advanced_usage.py   # Advanced usage examples
├── CONTRIBUTING.md         # Contribution guidelines
└── mkdocs.yml             # MkDocs site configuration
```

## Configuration

Create `redup.yaml` in your project root (or run `redup init`):

```yaml
project:
  name: my-project
  source: ./
  output: ./docs/

readme:
  sections:
    - overview
    - install
    - quickstart
    - api
    - structure
  badges:
    - version
    - python
    - coverage
  sync_markers: true

docs:
  api_reference: true
  module_docs: true
  architecture: true
  changelog: true

examples:
  auto_generate: true
  from_entry_points: true

sync:
  strategy: markers    # markers | full | git-diff
  watch: false
  ignore:
    - "tests/"
    - "__pycache__"
```

## Sync Markers

redup can update only specific sections of an existing README using HTML comment markers:

```markdown
<!-- redup:start -->
# Project Title
... auto-generated content ...
<!-- redup:end -->
```

Content outside the markers is preserved when regenerating. Enable this with `sync_markers: true` in your configuration.

## Architecture

```
redup/
    ├── 01_basic_usage        ├── __main__    ├── redup/            ├── config        ├── core/├── benchmark            ├── planner            ├── scanner            ├── parallel_scanner            ├── models            ├── pipeline    ├── sitecustomize            ├── hasher            ├── matcher            ├── markdown_reporter            ├── lsh_matcher        ├── reporters/            ├── json_reporter            ├── differ            ├── yaml_reporter        ├── cli_app/            ├── toon_reporter            ├── enhanced_reporter            ├── utils/                ├── function_extractor                ├── duplicate_finders├── project                ├── hash_utils            ├── ts_extractor            ├── main```

## API Overview

### Classes

- **`CodeBlock`** — A contiguous block of source code lines.
- **`ScannedFile`** — A file that has been read and split into blocks.
- **`DuplicateType`** — How the duplicate was detected.
- **`RefactorAction`** — Proposed refactoring action.
- **`RiskLevel`** — Risk of the proposed refactoring.
- **`ScanConfig`** — Configuration for project scanning.
- **`DuplicateFragment`** — A single occurrence of a duplicated code fragment.
- **`DuplicateGroup`** — A cluster of duplicated code fragments.
- **`RefactorSuggestion`** — A concrete refactoring proposal for a duplicate group.
- **`ScanStats`** — Statistics from the scanning phase.
- **`DuplicationMap`** — Complete result of a reDUP analysis run.
- **`HashedBlock`** — A code block with its computed fingerprints.
- **`HashIndex`** — Index mapping hashes to blocks for fast lookup.
- **`MatchResult`** — Result of comparing two code blocks.
- **`LSHIndex`** — LSH index for efficient near-duplicate detection.
- **`DiffResult`** — Result of comparing two reDUP scans.
- **`EnhancedReporter`** — Enhanced reporter with detailed metrics and visualizations.
- **`FunctionExtractor`** — Generic function extractor that can be configured for different languages.

### Functions

- `main()` — —
- `load_config()` — Load reDUP configuration from available sources.
- `config_to_scan_config(config, path)` — Convert configuration dict to ScanConfig object.
- `create_sample_redup_toml()` — Create a sample redup.toml configuration file content.
- `benchmark_sequential_vs_parallel()` — Compare sequential vs parallel scanning performance.
- `benchmark_feature_performance()` — Test performance of different features.
- `generate_suggestions(dup_map)` — Generate prioritized refactoring suggestions for all duplicate groups.
- `scan_project(config)` — Scan a project and return files with their code blocks.
- `scan_project_parallel(root, extensions, exclude_patterns, include_tests)` — Scan project files in parallel for better performance on large projects.
- `analyze(config, function_level_only)` — Run the full reDUP analysis pipeline.
- `analyze_parallel(config, function_level_only, max_workers)` — Run reDUP analysis with parallel scanning for large projects.
- `hash_block(text)` — SHA-256 hash of normalized text.
- `hash_block_structural(text)` — SHA-256 hash of deeply normalized text (variable names replaced).
- `find_exact_duplicates(index)` — Find groups of blocks with identical normalized text.
- `find_structural_duplicates(index)` — Find groups of blocks with identical structure (names may differ).
- `build_hash_index(blocks, min_lines)` — Build a hash index from a list of code blocks.
- `sequence_similarity(text_a, text_b)` — SequenceMatcher ratio between two normalized texts.
- `fuzzy_similarity(text_a, text_b)` — Fuzzy similarity using rapidfuzz if available, fallback to SequenceMatcher.
- `match_candidates(candidates, min_similarity)` — Compare all pairs in a candidate group and return matches above threshold.
- `refine_structural_matches(candidates, min_similarity)` — For structural hash collisions, verify with text similarity.
- `to_markdown(dup_map)` — Serialize a DuplicationMap to Markdown format.
- `build_lsh_index(blocks, threshold, min_lines)` — Build LSH index from code blocks.
- `find_near_duplicates(blocks, threshold, min_lines)` — Find near-duplicate code blocks using LSH.
- `to_json(dup_map, indent, include_snippets)` — Serialize a DuplicationMap to JSON string.
- `compare_scans(before_file, after_file)` — Compare two reDUP scan results and return the differences.
- `format_diff_result(diff)` — Format a DiffResult as a human-readable string.
- `to_yaml(dup_map)` — Serialize a DuplicationMap to YAML string.
- `to_toon(dup_map)` — Serialize a DuplicationMap to TOON format.
- `create_duplicate_finder(hash_type)` — Factory function to create duplicate finders for different hash types.
- `create_hash_function(normalizer)` — Factory function to create hash functions with different normalizers.
- `extract_functions_treesitter(source, file_path)` — Extract functions using tree-sitter for multi-language support.
- `get_supported_languages()` — Get list of supported languages for tree-sitter extraction.
- `is_language_supported(file_path)` — Check if a file extension is supported by tree-sitter extraction.
- `scan(path, format, output, extensions)` — Scan a project for code duplicates and generate a refactoring map.
- `diff(before, after)` — Compare two reDUP scans and show the differences.
- `check(path, max_groups, max_saved_lines, extensions)` — Check project for duplicates and exit with non-zero code if thresholds exceeded.
- `config(init, show)` — Manage reDUP configuration.
- `info()` — Show reDUP version and configuration info.


## Project Structure

📄 `benchmark` (2 functions)
📄 `examples.01_basic_usage` (1 functions)
📄 `project`
📦 `src.redup`
📄 `src.redup.__main__`
📦 `src.redup.cli_app`
📄 `src.redup.cli_app.main` (11 functions)
📦 `src.redup.core`
📄 `src.redup.core.config` (6 functions)
📄 `src.redup.core.differ` (5 functions, 1 classes)
📄 `src.redup.core.hasher` (15 functions, 2 classes)
📄 `src.redup.core.lsh_matcher` (12 functions, 2 classes)
📄 `src.redup.core.matcher` (5 functions, 1 classes)
📄 `src.redup.core.models` (1 functions, 9 classes)
📄 `src.redup.core.parallel_scanner` (6 functions)
📄 `src.redup.core.pipeline` (15 functions)
📄 `src.redup.core.planner` (5 functions)
📄 `src.redup.core.scanner` (6 functions, 2 classes)
📄 `src.redup.core.ts_extractor` (23 functions, 1 classes)
📦 `src.redup.core.utils`
📄 `src.redup.core.utils.duplicate_finders` (1 functions)
📄 `src.redup.core.utils.function_extractor` (5 functions, 1 classes)
📄 `src.redup.core.utils.hash_utils` (1 functions)
📦 `src.redup.reporters`
📄 `src.redup.reporters.enhanced_reporter` (17 functions, 1 classes)
📄 `src.redup.reporters.json_reporter` (3 functions)
📄 `src.redup.reporters.markdown_reporter` (1 functions)
📄 `src.redup.reporters.toon_reporter` (6 functions)
📄 `src.redup.reporters.yaml_reporter` (1 functions)
📄 `src.sitecustomize`

## Requirements

- Python >= >=3.10
- pyyaml >=6.0- typer >=0.12.0- rich >=13.0- pydantic >=2.0

## Contributing

**Contributors:**
- Tom Softreck <tom@sapletta.com>
- Tom Sapletta <tom-sapletta-com@users.noreply.github.com>

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/semcod/redup
cd redup

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Documentation

- 📖 [Full Documentation](https://github.com/semcod/redup/tree/main/docs) — API reference, module docs, architecture
- 🚀 [Getting Started](https://github.com/semcod/redup/blob/main/docs/getting-started.md) — Quick start guide
- 📚 [API Reference](https://github.com/semcod/redup/blob/main/docs/api.md) — Complete API documentation
- 🔧 [Configuration](https://github.com/semcod/redup/blob/main/docs/configuration.md) — Configuration options
- 💡 [Examples](./examples) — Usage examples and code samples

### Generated Files

| Output | Description | Link |
|--------|-------------|------|
| `README.md` | Project overview (this file) | — |
| `docs/api.md` | Consolidated API reference | [View](./docs/api.md) |
| `docs/modules.md` | Module reference with metrics | [View](./docs/modules.md) |
| `docs/architecture.md` | Architecture with diagrams | [View](./docs/architecture.md) |
| `docs/dependency-graph.md` | Dependency graphs | [View](./docs/dependency-graph.md) |
| `docs/coverage.md` | Docstring coverage report | [View](./docs/coverage.md) |
| `docs/getting-started.md` | Getting started guide | [View](./docs/getting-started.md) |
| `docs/configuration.md` | Configuration reference | [View](./docs/configuration.md) |
| `docs/api-changelog.md` | API change tracking | [View](./docs/api-changelog.md) |
| `CONTRIBUTING.md` | Contribution guidelines | [View](./CONTRIBUTING.md) |
| `examples/` | Usage examples | [Browse](./examples) |
| `mkdocs.yml` | MkDocs configuration | — |

<!-- code2docs:end -->