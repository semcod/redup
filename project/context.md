# System Architecture Analysis

## Overview

- **Project**: redup
- **Language**: python
- **Files**: 10
- **Lines**: 2574
- **Functions**: 52
- **Classes**: 15
- **Avg CC**: 4.1
- **Critical (CC≥10)**: 2

## Architecture

### root/ (1 files, 17L, 0 functions)

- `project.sh` — 17L, 0 methods, CC↑0

### src/ (1 files, 4L, 0 functions)

- `sitecustomize.py` — 4L, 0 methods, CC↑0

### src/redup/ (2 files, 30L, 0 functions)

- `__init__.py` — 25L, 0 methods, CC↑0
- `__main__.py` — 5L, 0 methods, CC↑0

### src/redup/cli_app/ (2 files, 170L, 3 functions)

- `main.py` — 169L, 3 methods, CC↑9
- `__init__.py` — 1L, 0 methods, CC↑0

### src/redup/core/ (7 files, 1054L, 44 functions)

- `hasher.py` — 235L, 15 methods, CC↑14
- `pipeline.py` — 256L, 12 methods, CC↑9
- `scanner.py` — 193L, 6 methods, CC↑9
- `matcher.py` — 107L, 5 methods, CC↑7
- `planner.py` — 110L, 5 methods, CC↑7
- _2 more files_

### src/redup/reporters/ (4 files, 176L, 5 functions)

- `toon_reporter.py` — 75L, 1 methods, CC↑12
- `yaml_reporter.py` — 34L, 1 methods, CC↑4
- `json_reporter.py` — 66L, 3 methods, CC↑3
- `__init__.py` — 1L, 0 methods, CC↑0

## Key Exports


## Hotspots (High Fan-Out)

- **scan** — fan-out=18: Scan a project for code duplicates and generate a refactoring map.
- **scan_project** — fan-out=15: Scan a project and return files with their code blocks.

Returns:
    Tuple of (
- **_find_structural_groups** — fan-out=11: Find structural duplicate groups.

## Refactoring Priorities

| # | Action | Impact | Effort |
|---|--------|--------|--------|
| 1 | Reduce scan fan-out (currently 18) | medium | medium |
| 2 | Reduce scan_project fan-out (currently 15) | medium | medium |

## Context for LLM

When suggesting changes:
1. Start from hotspots and high-CC functions
2. Follow refactoring priorities above
3. Maintain public API surface — keep backward compatibility
4. Prefer minimal, incremental changes

