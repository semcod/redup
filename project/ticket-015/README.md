# Ticket 015: Native Rust excludes and MinHash in scan hot paths

- **ID**: ticket-015
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-12

## Goal and scope

Optimize scanning performance in reDUP by eliminating quadratic `fnmatch` pattern matching overhead during file exclusion checks, and leveraging the native PyO3 Rust extension (`redup_fast_hash`) for MinHash signature computation in LSH near-duplicate matching.

## Acceptance criteria

- [x] AC-01: Replace repetitive `fnmatch.fnmatch` lookups in `_should_exclude` with a single compiled regex alternation and larger LRU cache.
- [x] AC-02: Use native `redup_fast_hash.compute_minhash_signature` in `lsh_matcher` for high-throughput MinHash signature generation with safe Datasketch fallback.
- [x] AC-03: Full test suite passes and governance checks pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
