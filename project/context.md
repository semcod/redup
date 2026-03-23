# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 12
- **Lines**: 2895
- **Functions**: 56
- **Classes**: 15
- **Avg CC**: 4.8
- **Critical (CC≥10)**: 6

## Architecture

### root/ (3 files, 505L, 18 functions)

- `cli_utilities_demo.py` — 231L, 7 methods, CC↑12
- `refactored_frontend_demo.py` — 258L, 11 methods, CC↑4
- `project.sh` — 16L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 166L, 3 functions)

- `main.py` — 165L, 3 methods, CC↑9
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (7 files, 941L, 30 functions)

- `pipeline.py` — 183L, 3 methods, CC↑20
- `hasher.py` — 204L, 11 methods, CC↑17
- `scanner.py` — 193L, 6 methods, CC↑9
- `planner.py` — 117L, 5 methods, CC↑7
- `matcher.py` — 91L, 4 methods, CC↑6
- _2 more files_

### src/redup/reporters/ (4 files, 176L, 5 functions)

- `toon_reporter.py` — 75L, 1 methods, CC↑12
- `yaml_reporter.py` — 34L, 1 methods, CC↑4
- `json_reporter.py` — 66L, 3 methods, CC↑3
- `__init__.py` — 1L, 0 methods, CC↑0

## Key Exports

- **analyze** (function, CC=20) ⚠ split

## Hotspots (High Fan-Out)

- **analyze** — fan-out=21: Analysis pipeline, 21 stages
- **scan** — fan-out=18: Scan a project for code duplicates and generate a refactoring map.
- **scan_project** — fan-out=15: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **format_output** — fan-out=11: 11-way dispatch
- **format_table** — fan-out=10: 10-way dispatch

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Split analyze (CC=20 → target CC<10) | medium | low |
| 2 | Split _ast_to_normalized_string (CC=17 → target CC<10) | medium | low |
| 3 | Reduce analyze fan-out (currently 21) | medium | medium |
| 4 | Reduce scan fan-out (currently 18) | medium | medium |
| 5 | Reduce scan_project fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

