# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 30
- **Lines**: 9097
- **Functions**: 245
- **Classes**: 32
- **Avg CC**: 3.9
- **Critical (CC≥10)**: 23

## Architecture

### root/ (2 files, 131L, 2 functions)

- `benchmark.py` — 111L, 2 methods, CC↑3
- `project.sh` — 20L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 601L, 12 functions)

- `main.py` — 600L, 12 methods, CC↑19
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (19 files, 5319L, 185 functions)

- `differ.py` — 209L, 5 methods, CC↑14
- `ultra_fast_scanner.py` — 358L, 8 methods, CC↑14
- `memory_scanner.py` — 285L, 8 methods, CC↑13
- `scanner.py` — 373L, 10 methods, CC↑13
- `parallel_scanner.py` — 234L, 6 methods, CC↑11
- _14 more files_

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

- **UniversalFuzzyDetector** (class, CC̄=5.6)
- **FuzzySimilarityDetector** (class, CC̄=5.3)
- **LSHIndex** (class, CC̄=5.6)

## Hotspots (High Fan-Out)

- **scan_project_parallel_memory_optimized** — fan-out=32: Parallel scan with memory optimization.
- **scan_project_memory_optimized** — fan-out=27: Scan project with memory optimization for faster processing.

Loads files into R
- **preload_to_ram** — fan-out=22: Load ALL files into RAM at once for maximum speed.

Returns:
    Dict mapping fi
- **scan_project_ultra_fast** — fan-out=21: Ultra-fast scanner with RAM preload and smart hashing.

Performance optimization
- **scan_project** — fan-out=19: Scan a project and return files with their code blocks.

Args:
    config: Scan 
- **_find_duplicates_phase_lazy** — fan-out=15: Phase 3: Hash and find duplicates with caching and lazy evaluation.
- **_load_duplication_map** — fan-out=15: Load a DuplicationMap from a JSON file.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split god module src/redup/cli_app/main.py (600L, 0 classes) | high | high |
| 2 | Split god module src/redup/core/pipeline.py (664L, 0 classes) | high | high |
| 3 | Split god module src/redup/core/ts_extractor.py (765L, 1 classes) | high | high |
| 4 | Split _apply_fuzzy_similarity (CC=19 → target CC<10) | medium | low |
| 5 | Reduce scan_project_parallel_memory_optimized fan-out (currently 32) | medium | medium |
| 6 | Reduce scan_project_memory_optimized fan-out (currently 27) | medium | medium |
| 7 | Reduce preload_to_ram fan-out (currently 22) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

