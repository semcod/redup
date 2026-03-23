# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 27
- **Lines**: 6543
- **Functions**: 195
- **Classes**: 26
- **Avg CC**: 3.5
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

### src/redup/cli_app/ (2 files, 441L, 11 functions)

- `main.py` — 440L, 11 methods, CC↑14
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (15 files, 3414L, 128 functions)

- `differ.py` — 209L, 5 methods, CC↑14
- `parallel_scanner.py` — 234L, 6 methods, CC↑11
- `pipeline.py` — 411L, 15 methods, CC↑11
- `lsh_matcher.py` — 217L, 12 methods, CC↑10
- `scanner.py` — 249L, 7 methods, CC↑10
- _10 more files_

### src/redup/core/utils/ (6 files, 391L, 20 functions)

- `diff_helpers.py` — 97L, 8 methods, CC↑7
- `function_extractor.py` — 148L, 5 methods, CC↑5
- `language_dispatcher.py` — 72L, 5 methods, CC↑4
- `duplicate_finders.py` — 36L, 1 methods, CC↑3
- `hash_utils.py` — 37L, 1 methods, CC↑3
- _1 more files_

### src/redup/reporters/ (7 files, 787L, 34 functions)

- `markdown_reporter.py` — 90L, 1 methods, CC↑12
- `code2llm_reporter.py` — 209L, 6 methods, CC↑11
- `enhanced_reporter.py` — 274L, 17 methods, CC↑8
- `toon_reporter.py` — 106L, 6 methods, CC↑8
- `json_reporter.py` — 73L, 3 methods, CC↑5
- _2 more files_

## Key Exports

- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **scan_project** — fan-out=18: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **_write_results** — fan-out=15: Write scan results to output files.
- **scan_project_parallel** — fan-out=13: Scan project files in parallel for better performance on large projects.
- **_find_structural_groups** — fan-out=11: Find structural duplicate groups.
- **_normalize_text** — fan-out=11: Normalize code text for comparison.

Strips comments, normalizes whitespace, low
- **check** — fan-out=11: Check project for duplicates and exit with non-zero code if thresholds exceeded.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split god module src/redup/core/ts_extractor.py (765L, 1 classes) | high | high |
| 2 | Reduce scan_project fan-out (currently 18) | medium | medium |
| 3 | Reduce _load_duplication_map fan-out (currently 15) | medium | medium |
| 4 | Reduce _write_results fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

