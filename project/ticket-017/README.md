# Ticket 017: Pipeline optimization for parallel scanning, cache lookups, and AST block extraction

- **ID**: ticket-017
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-13

## Goal and scope

Optimize reDUP scan and duplicate finding bottlenecks:
1. Enable parallel scanning by default in `scan_command` and `analyze_optimized` across CPU cores.
2. Optimize AST function block extraction using a single-pass `ast.NodeVisitor` instead of multiple full tree traversals.
3. Cache SQLite block hashes at the file level in `build_hash_index_with_cache` to eliminate redundant queries and SHA256 hashes per block.
4. Skip redundant cache re-writes for unchanged files in `find_duplicates_phase_lazy`.
5. Fix UTF-8 multi-byte operator boundary slicing panic in `redup_fast_hash::extract_fuzzy_tokens`.

## Acceptance criteria

- [x] AC-01: Default `parallel` to True in CLI scan command and auto-parallelize in `analyze_optimized`.
- [x] AC-02: Single-pass AST extraction for Python function blocks without repeated whole-tree traversals.
- [x] AC-03: File-level hash cache lookup in `build_hash_index_with_cache` avoiding per-block DB round-trips.
- [x] AC-04: Skip re-storing unchanged file hashes into SQLite in `find_duplicates_phase_lazy`.
- [x] AC-05: Fix UTF-8 multi-byte operator slicing in `redup_fast_hash` to prevent thread panics on unicode.
- [x] AC-06: Pass test suite and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent.
