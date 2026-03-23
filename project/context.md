# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 21
- **Lines**: 5344
- **Functions**: 147
- **Classes**: 20
- **Avg CC**: 3.9
- **Critical (CC≥10)**: 10

## Architecture

### root/ (2 files, 128L, 2 functions)

- `benchmark.py` — 111L, 2 methods, CC↑3
- `project.sh` — 17L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 423L, 11 functions)

- `main.py` — 422L, 11 methods, CC↑12
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (12 files, 2836L, 99 functions)

- `ts_extractor.py` — 767L, 23 methods, CC↑24
- `differ.py` — 246L, 5 methods, CC↑18
- `parallel_scanner.py` — 234L, 6 methods, CC↑11
- `pipeline.py` — 409L, 15 methods, CC↑11
- `lsh_matcher.py` — 217L, 12 methods, CC↑10
- _7 more files_

### src/redup/core/utils/ (4 files, 222L, 7 functions)

- `function_extractor.py` — 148L, 5 methods, CC↑5
- `duplicate_finders.py` — 36L, 1 methods, CC↑3
- `hash_utils.py` — 37L, 1 methods, CC↑3
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/reporters/ (6 files, 578L, 28 functions)

- `markdown_reporter.py` — 90L, 1 methods, CC↑12
- `enhanced_reporter.py` — 274L, 17 methods, CC↑8
- `toon_reporter.py` — 106L, 6 methods, CC↑8
- `json_reporter.py` — 73L, 3 methods, CC↑5
- `yaml_reporter.py` — 34L, 1 methods, CC↑4
- _1 more files_

## Key Exports

- **extract_functions_treesitter** (function, CC=24) ⚠ split
- **compare_scans** (function, CC=18) ⚠ split
- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **extract_functions_treesitter** — fan-out=25: Extract functions using tree-sitter for multi-language support.
- **scan_project** — fan-out=17: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **scan_project_parallel** — fan-out=13: Scan project files in parallel for better performance on large projects.
- **compare_scans** — fan-out=13: Compare two reDUP scan results and return the differences.
- **_write_results** — fan-out=13: Write scan results to output files.
- **_find_structural_groups** — fan-out=11: Find structural duplicate groups.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split god module src/redup/core/ts_extractor.py (767L, 1 classes) | high | high |
| 2 | Split extract_functions_treesitter (CC=24 → target CC<10) | medium | low |
| 3 | Split compare_scans (CC=18 → target CC<10) | medium | low |
| 4 | Reduce extract_functions_treesitter fan-out (currently 25) | medium | medium |
| 5 | Reduce scan_project fan-out (currently 17) | medium | medium |
| 6 | Reduce _load_duplication_map fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

