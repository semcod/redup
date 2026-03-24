# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 36
- **Lines**: 10318
- **Functions**: 288
- **Classes**: 40
- **Avg CC**: 3.7
- **Critical (CC≥10)**: 17

## Architecture

### benchmarks/ (1 files, 160L, 4 functions)

- `bench_libraries.py` — 160L, 4 methods, CC↑10

### root/ (2 files, 132L, 2 functions)

- `benchmark.py` — 111L, 2 methods, CC↑3
- `project.sh` — 21L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (3 files, 705L, 16 functions)

- `mcp_server.py` — 675L, 16 methods, CC↑12
- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (6 files, 655L, 24 functions)

- `output_writer.py` — 78L, 2 methods, CC↑15
- `scan_commands.py` — 163L, 5 methods, CC↑7
- `fuzzy_similarity.py` — 160L, 9 methods, CC↑5
- `main.py` — 219L, 5 methods, CC↑1
- `scan_helpers.py` — 34L, 3 methods, CC↑1
- _1 more files_

### src/redup/core/ (18 files, 5213L, 187 functions)

- `python_parser.py` — 170L, 4 methods, CC↑15
- `differ.py` — 209L, 5 methods, CC↑14
- `scanner.py` — 633L, 21 methods, CC↑13
- `pipeline.py` — 714L, 18 methods, CC↑11
- `universal_fuzzy.py` — 449L, 16 methods, CC↑11
- _13 more files_

### src/redup/core/utils/ (6 files, 456L, 21 functions)

- `diff_helpers.py` — 162L, 9 methods, CC↑15
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

- **write_results** (function, CC=15) ⚠ split
- **GroupMatcher** (class, CC̄=5.8)
  - `_ensure_matches` CC=15 ⚠ split
- **UniversalFuzzyDetector** (class, CC̄=5.4)
- **FuzzySimilarityDetector** (class, CC̄=5.0)
- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **_handle_analyze_project** — fan-out=23: Analysis pipeline, 23 stages
- **_preload_files** — fan-out=20: Load ALL files into RAM at once for maximum speed.
- **_scan_sequential** — fan-out=16: Scan files sequentially.
- **scan_project** — fan-out=16: UNIFIED entry point for project scanning.

Args:
    config: Scan configuration

- **_find_duplicates_phase_lazy** — fan-out=15: Phase 3: Hash and find duplicates with caching and lazy evaluation.
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.
- **_scan_parallel** — fan-out=14: Scan files in parallel using ProcessPoolExecutor.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split god module src/redup/core/scanner.py (633L, 4 classes) | high | high |
| 2 | Split god module src/redup/mcp_server.py (675L, 0 classes) | high | high |
| 3 | Split god module src/redup/core/pipeline.py (714L, 0 classes) | high | high |
| 4 | Split god module src/redup/core/ts_extractor.py (765L, 1 classes) | high | high |
| 5 | Split _parse_with_ast (CC=15 → target CC<10) | medium | low |
| 6 | Split write_results (CC=15 → target CC<10) | medium | low |
| 7 | Split GroupMatcher._ensure_matches (CC=15 → target CC<10) | medium | low |
| 8 | Break circular dependency: src.redup.mcp_server._json_safe | medium | low |
| 9 | Reduce _handle_analyze_project fan-out (currently 23) | medium | medium |
| 10 | Reduce _preload_files fan-out (currently 20) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

