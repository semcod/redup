# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 12
- **Lines**: 3350
- **Functions**: 76
- **Classes**: 16
- **Avg CC**: 4.0
- **Critical (CC≥10)**: 4

## Architecture

### root/ (1 files, 17L, 0 functions)

- `project.sh` — 17L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 313L, 9 functions)

- `main.py` — 312L, 9 methods, CC↑7
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (9 files, 1656L, 57 functions)

- `differ.py` — 246L, 5 methods, CC↑18
- `ts_extractor.py` — 353L, 8 methods, CC↑11
- `pipeline.py` — 257L, 12 methods, CC↑9
- `scanner.py` — 201L, 6 methods, CC↑9
- `matcher.py` — 107L, 5 methods, CC↑7
- _4 more files_

### src/redup/reporters/ (4 files, 207L, 10 functions)

- `toon_reporter.py` — 106L, 6 methods, CC↑8
- `yaml_reporter.py` — 34L, 1 methods, CC↑4
- `json_reporter.py` — 66L, 3 methods, CC↑3
- `__init__.py` — 1L, 0 methods, CC↑0

## Key Exports

- **compare_scans** (function, CC=18) ⚠ split

## Hotspots (High Fan-Out)

- **scan_project** — fan-out=17: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **extract_functions_treesitter** — fan-out=13: Extract functions using tree-sitter for multi-language support.
- **compare_scans** — fan-out=13: Compare two reDUP scan results and return the differences.
- **_find_structural_groups** — fan-out=11: Find structural duplicate groups.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split compare_scans (CC=18 → target CC<10) | medium | low |
| 2 | Reduce scan_project fan-out (currently 17) | medium | medium |
| 3 | Reduce _load_duplication_map fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

