# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 31
- **Lines**: 8616
- **Functions**: 245
- **Classes**: 33
- **Avg CC**: 3.4
- **Critical (CC≥10)**: 13

## Architecture

### root/ (2 files, 132L, 2 functions)

- `benchmark.py` — 111L, 2 methods, CC↑3
- `project.sh` — 21L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (6 files, 655L, 24 functions)

- `output_writer.py` — 78L, 2 methods, CC↑15
- `scan_commands.py` — 163L, 5 methods, CC↑7
- `fuzzy_similarity.py` — 160L, 9 methods, CC↑5
- `main.py` — 219L, 5 methods, CC↑1
- `scan_helpers.py` — 34L, 3 methods, CC↑1
- _1 more files_

### src/redup/core/ (16 files, 4707L, 173 functions)

- `differ.py` — 209L, 5 methods, CC↑14
- `scanner.py` — 642L, 20 methods, CC↑12
- `pipeline.py` — 660L, 17 methods, CC↑11
- `universal_fuzzy.py` — 454L, 16 methods, CC↑11
- `fuzzy_similarity.py` — 408L, 20 methods, CC↑10
- _11 more files_

### src/redup/core/utils/ (5 files, 294L, 12 functions)

- `function_extractor.py` — 148L, 5 methods, CC↑5
- `language_dispatcher.py` — 72L, 5 methods, CC↑4
- `duplicate_finders.py` — 36L, 1 methods, CC↑3
- `hash_utils.py` — 37L, 1 methods, CC↑3
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/reporters/ (7 files, 787L, 34 functions)

- `markdown_reporter.py` — 90L, 1 methods, CC↑12
- `code2llm_reporter.py` — 209L, 6 methods, CC↑11
- `enhanced_reporter.py` — 274L, 17 methods, CC↑8
- `toon_reporter.py` — 106L, 6 methods, CC↑8
- `json_reporter.py` — 73L, 3 methods, CC↑5
- _2 more files_

## Key Exports

- **write_results** (function, CC=15) ⚠ split
- **UniversalFuzzyDetector** (class, CC̄=5.6)
- **FuzzySimilarityDetector** (class, CC̄=5.3)
- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **_preload_files** — fan-out=20: Load ALL files into RAM at once for maximum speed.
- **_scan_sequential** — fan-out=16: Scan files sequentially.
- **scan_project** — fan-out=16: UNIFIED entry point for project scanning.

Args:
    config: Scan configuration

- **_find_duplicates_phase_lazy** — fan-out=15: Phase 3: Hash and find duplicates with caching and lazy evaluation.
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **_scan_parallel** — fan-out=14: Scan files in parallel using ProcessPoolExecutor.
- **write_results** — fan-out=14: Write analysis results in specified format.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split god module src/redup/core/scanner.py (642L, 4 classes) | high | high |
| 2 | Split god module src/redup/core/pipeline.py (660L, 0 classes) | high | high |
| 3 | Split god module src/redup/core/ts_extractor.py (765L, 1 classes) | high | high |
| 4 | Split write_results (CC=15 → target CC<10) | medium | low |
| 5 | Reduce _preload_files fan-out (currently 20) | medium | medium |
| 6 | Reduce _scan_sequential fan-out (currently 16) | medium | medium |
| 7 | Reduce scan_project fan-out (currently 16) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

