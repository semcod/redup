# Ticket 018: Wire unused performance and reporter parameters across redup core, CLI, and benchmarks

- **ID**: ticket-018
- **Owner**: gemini
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-17
- **Authorization**: SESSION_EXECUTION_AUTHORIZATION

## Goal and scope

Wire previously ignored optional parameters across reDUP scanner utilities, semantic intent profile duplicate detection, code2llm reporter functions, CLI compare path formatting, refactoring advisor match list building, and library benchmark project generation, and record Wellmanifest standard pack adoption evidence.

## Acceptance criteria

- [x] AC-01: `_preload_files` in `src/redup/core/scanner_utils.py` enforces `max_cache_mb` byte budget (`max_bytes = int(max_cache_mb * 1024 * 1024)` when `max_cache_mb and max_cache_mb > 0`).
- [x] AC-02: `_find_intent_profile_duplicates` in `src/redup/core/semantic.py` bounds returned matches to `[:top_k]` when `top_k and top_k > 0`.
- [x] AC-03: `to_code2llm_toon` and `to_code2llm_context` in `src/redup/reporters/code2llm_reporter.py` wire `classes_count`, `files_scanned`, and `total_lines`.
- [x] AC-04: `_short_path` in `src/redup/cli_app/compare_command.py`, `_build_match_list` in `src/redup/core/refactor_advisor.py`, and `generate_test_project` in `benchmarks/bench_libraries.py` wire their optional parameters (`max_parts`, `limit`, `lines_per_file`).
- [x] AC-05: `audit_repository` reports 0 `PERF-AUDIT-*` findings, `standard_pack_check.py` reports `findings=0`, pytest passes, and `governance-check.sh` reports `GOV-PASS`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
