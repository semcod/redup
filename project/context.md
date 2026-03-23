# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 16
- **Lines**: 4230
- **Functions**: 104
- **Classes**: 17
- **Avg CC**: 4.2
- **Critical (CC≥10)**: 8

## Architecture

### root/ (1 files, 17L, 0 functions)

- `project.sh` — 17L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 400L, 11 functions)

- `main.py` — 399L, 11 methods, CC↑9
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (12 files, 2352L, 82 functions)

- `differ.py` — 246L, 5 methods, CC↑18
- `parallel_scanner.py` — 185L, 4 methods, CC↑16
- `pipeline.py` — 392L, 15 methods, CC↑11
- `ts_extractor.py` — 353L, 8 methods, CC↑11
- `lsh_matcher.py` — 217L, 12 methods, CC↑10
- _7 more files_

### src/redup/reporters/ (5 files, 304L, 11 functions)

- `markdown_reporter.py` — 90L, 1 methods, CC↑12
- `toon_reporter.py` — 106L, 6 methods, CC↑8
- `json_reporter.py` — 73L, 3 methods, CC↑5
- `yaml_reporter.py` — 34L, 1 methods, CC↑4
- `__init__.py` — 1L, 0 methods, CC↑0

## Key Exports

- **compare_scans** (function, CC=18) ⚠ split
- **scan_project_parallel** (function, CC=16) ⚠ split
- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **scan_project** — fan-out=17: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **scan_project_parallel** — fan-out=17: Scan project files in parallel for better performance on large projects.
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **extract_functions_treesitter** — fan-out=13: Extract functions using tree-sitter for multi-language support.
- **compare_scans** — fan-out=13: Compare two reDUP scan results and return the differences.
- **_find_structural_groups** — fan-out=11: Find structural duplicate groups.
- **_write_results** — fan-out=11: Write scan results to output files.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split scan_project_parallel (CC=16 → target CC<10) | medium | low |
| 2 | Split compare_scans (CC=18 → target CC<10) | medium | low |
| 3 | Reduce scan_project fan-out (currently 17) | medium | medium |
| 4 | Reduce scan_project_parallel fan-out (currently 17) | medium | medium |
| 5 | Reduce _load_duplication_map fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

