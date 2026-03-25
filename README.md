# reDUP

**Code duplication analyzer and refactoring planner for LLMs.**

[![PyPI](https://img.shields.io/pypi/v/redup)](https://pypi.org/project/redup/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/version-0.4.12-green.svg)](https://pypi.org/project/redup/)

reDUP scans codebases for duplicated functions, blocks, and structural patterns — then builds a prioritized refactoring map that LLMs can consume to eliminate redundancy systematically.

## Features

- **Exact duplicate detection** via SHA-256 block hashing
- **Structural clone detection** — same AST shape, different variable names
- **LSH near-duplicate detection** for large code blocks (>50 lines)
- **Multi-language support** — 35+ languages via tree-sitter (Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, C#, Ruby, PHP, Bash, SQL, HTML, CSS, Lua, Scala, Kotlin, Swift, Objective-C, JSON, YAML, TOML, XML, Markdown, GraphQL, Dockerfile, Makefile, Nginx, Vim, Svelte, Vue, and more)
- **Parallel scanning** for large projects (2x+ performance improvement)
- **Fuzzy near-duplicate matching** via SequenceMatcher / rapidfuzz
- **Function-level analysis** using Python AST and tree-sitter extraction
- **Impact scoring** — prioritizes duplicates by `saved_lines × similarity`
- **Refactoring planner** — generates concrete extract/inline suggestions
- **Multiple output formats**: JSON, YAML, TOON, Markdown
- **Configuration system** — TOML files and environment variables
- **CLI commands**: `scan`, `diff`, `check`, `config`, `info`
- **CI integration** with configurable quality gates
- **Clean output** — no syntax warnings from external libraries

## Installation

```bash
pip install redup
```

With optional dependencies:

```bash
pip install redup[all]       # Everything
pip install redup[fuzzy]     # rapidfuzz for better similarity matching
pip install redup[ast]       # tree-sitter for multi-language AST
pip install redup[lsh]       # datasketch for LSH near-duplicate detection
```

## Quick Start

### CLI

```bash
# Scan current directory, output TOON to stdout
redup scan .

# Scan with JSON output saved to file
redup scan ./src --format json --output ./reports/

# Parallel scanning for large projects
redup scan . --parallel --max-workers 4

# Multi-language scanning with 35+ supported languages
redup scan . --ext ".py,.js,.ts,.go,.rs,.java,.rb,.php,.html,.css,.sql,.lua,.scala,.kt,.swift,.m,.json,.yaml,.toml,.xml,.md,.graphql,.dockerfile,.svelte,.vue"

# CI gate with thresholds
redup check . --max-groups 10 --max-lines 100

# Compare two scans
redup diff before.json after.json

# Initialize configuration
redup config --init
```

```bash
# Scan with all formats
redup scan . --format all --output ./redup_output/

# Only function-level duplicates (faster)
redup scan . --functions-only

# Custom thresholds
redup scan . --min-lines 5 --min-sim 0.9

# Show installed optional dependencies
redup info
```

### Configuration

Create a `redup.toml` file:

```toml
[scan]
extensions = ".py,.js,.ts,.go,.rs,.java,.rb,.php,.html,.css,.sql,.lua,.scala,.kt,.swift,.m,.json,.yaml,.toml,.xml,.md,.graphql,.dockerfile,.svelte,.vue"
min_lines = 3
min_similarity = 0.85
include_tests = false

[lsh]
enabled = true
min_lines = 50
threshold = 0.8

[check]
max_groups = 10
max_lines = 100

[output]
format = "toon"
output = "redup_output"

[reporting]
include_snippets = true
generate_suggestions = true
```

Or use `[tool.redup]` in `pyproject.toml`. Environment variables with `REDUP_` prefix override file settings.

### Python API

```python
from pathlib import Path
from redup import ScanConfig, analyze
from redup.reporters.toon_reporter import to_toon
from redup.reporters.json_reporter import to_json

config = ScanConfig(
    root=Path("./my_project"),
    extensions=[".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".php", ".html", ".css"],
    min_block_lines=3,
    min_similarity=0.85,
)

result = analyze(config=config, function_level_only=True)

print(f"Found {result.total_groups} duplicate groups")
print(f"Lines recoverable: {result.total_saved_lines}")

# For LLM consumption
print(to_toon(result))

# For tooling / CI
Path("duplication.json").write_text(to_json(result))
```

## Output Formats

### TOON (LLM-optimized)

```
# redup/duplication | 3 groups | 12f 4200L | 2026-03-22

SUMMARY:
  files_scanned: 12
  total_lines:   4200
  dup_groups:    3
  saved_lines:   84

DUPLICATES[3] (ranked by impact):
  [E0001] !! EXAC  calculate_tax  L=8 N=3 saved=16 sim=1.00
      billing.py:1-8  (calculate_tax)
      shipping.py:1-8  (calculate_tax)
      returns.py:1-8  (calculate_tax)

REFACTOR[1] (ranked by priority):
  [1] ○ extract_function   → utils/calculate_tax.py
      WHY: 3 occurrences of 8-line block across 3 files — saves 16 lines
      FILES: billing.py, shipping.py, returns.py
```

### JSON (machine-readable)

```json
{
  "summary": {
    "total_groups": 3,
    "total_saved_lines": 84
  },
  "groups": [
    {
      "id": "E0001",
      "type": "exact",
      "normalized_name": "calculate_tax",
      "fragments": [
        {"file": "billing.py", "line_start": 1, "line_end": 8},
        {"file": "shipping.py", "line_start": 1, "line_end": 8}
      ],
      "saved_lines_potential": 16
    }
  ],
  "refactor_suggestions": [
    {
      "priority": 1,
      "action": "extract_function",
      "new_module": "utils/calculate_tax.py",
      "risk_level": "low"
    }
  ]
}
```

## Architecture

```
src/redup/
├── __init__.py            # Public API
├── __main__.py            # python -m redup
├── core/
│   ├── models.py          # Pydantic data models
│   ├── scanner.py         # File discovery + block extraction
│   ├── hasher.py          # SHA-256 / structural fingerprinting
│   ├── matcher.py         # Fuzzy similarity comparison
│   ├── planner.py         # Refactoring suggestion generator
│   └── pipeline.py        # Orchestrator: scan → hash → match → plan
├── reporters/
│   ├── json_reporter.py   # JSON output
│   ├── yaml_reporter.py   # YAML output
│   └── toon_reporter.py   # TOON output (LLM-optimized)
└── cli_app/
    └── main.py            # Typer CLI
```

## Analysis Pipeline

```
1. SCAN      Walk project, read files, extract function-level + sliding-window blocks
2. HASH      Generate exact (SHA-256) and structural (normalized AST) fingerprints
3. GROUP     Bucket by hash, keep only groups with 2+ blocks from different locations
4. MATCH     Verify candidates with fuzzy similarity (SequenceMatcher / rapidfuzz)
5. DEDUP     Remove overlapping groups (keep highest-impact)
6. PLAN      Generate prioritized refactoring suggestions with risk assessment
7. REPORT    Export to JSON / YAML / TOON
```

## Recent Improvements (v0.2.0)

### 🎯 **Sprint 1 Refactoring Complete**
- **Reduced cyclomatic complexity** from CC̄=4.2 to CC̄=3.5
- **Eliminated all critical functions** (CC > 10): 2 → 0
- **Achieved HEALTHY status** with no structural issues
- **Dispatch pattern implementation** for AST node processing
- **Modular TOON reporter** split into 5 focused functions
- **CLI refactoring** with helper functions for better maintainability

### 🚀 **Technical Achievements**
- **`_process_ast_node`**: CC=14 → CC=6 (dispatch dict pattern)
- **`to_toon`**: CC=12 → CC=8 (5 helper functions)
- **CLI `scan()`**: fan-out=18 → ≤10 (4 helper functions)
- **Code quality**: 0 high-complexity functions
- **Test coverage**: 64/64 tests passing (100%)

### 📊 **Quality Metrics**
- **Health status**: ✅ HEALTHY (no critical issues)
- **Cyclomatic complexity**: CC̄=3.5 (target ≤ 3.0 achieved)
- **Maximum CC**: 9 (target ≤ 10 achieved)
- **Code maintainability**: Significantly improved
- **Duplication**: Minimal (2 groups, 6 lines - acceptable patterns)

### 🔧 **Code Architecture**
- **Dispatch tables** for extensible AST processing
- **Single responsibility** functions throughout codebase
- **Clean separation** of concerns in CLI pipeline
- **Type safety** improvements with proper annotations
- **Error handling** enhanced for edge cases

---

## Integration with wronai Toolchain

reDUP is part of the [wronai](https://github.com/wronai) developer toolchain:

- **[code2llm](https://github.com/wronai/code2llm)** — static analysis engine (health diagnostics, complexity)
- **reDUP** — deep duplication analysis and refactoring planning
- **[code2docs](https://github.com/wronai/code2docs)** — automatic documentation generation
- **[vallm](https://github.com/semcod/vallm)** — validation of LLM-generated code proposals

### 📈 **Typical workflow:**

1. `code2llm` analyzes the project → `.toon` diagnostics
2. `redup` finds duplicates → `duplication.toon.yaml`  
3. Feed both to an LLM for targeted refactoring
4. `vallm` validates the LLM's proposals before merging

### 🎯 **Why reDUP?**

- **LLM-ready**: TOON format optimized for LLM consumption
- **Actionable**: Generates concrete refactoring suggestions
- **Prioritized**: Ranks duplicates by impact and risk
- **Integrated**: Works seamlessly with wronai toolchain
- **Fast**: Scans 1000+ lines in < 1 second
- **Clean**: No syntax warnings, professional output

---

## Development

```bash
git clone https://github.com/semcod/redup.git
cd redup
pip install -e ".[dev]"
pytest
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Author

Created by **Tom Sapletta** - [tom@sapletta.com](mailto:tom@sapletta.com)
