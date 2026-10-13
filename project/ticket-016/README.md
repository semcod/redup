# Ticket 016: Native Rust MinHash scheme compatibility and batch Rayon signatures

- **ID**: ticket-016
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-13

## Goal and scope

Resolve Datasketch >=2.0 scheme compatibility for native Rust MinHash signature instantiation, introduce multi-threaded batch MinHash signatures via Rayon in `redup_fast_hash`, vectorize LSH block indexing in `LSHIndex.add_blocks`, and eliminate redundant pairwise similarity re-computations in `find_fuzzy_groups`.

## Acceptance criteria

- [x] AC-01: Support datasketch >=2.0 scheme specification (`scheme='legacy'`) and fallback assignment for native Rust MinHash signature instantiation.
- [x] AC-02: Implement `batch_minhash_signature` in `redup-fast-hash` with Rayon parallelization and GIL release.
- [x] AC-03: Implement batch indexing in `LSHIndex.add_blocks` for high-throughput parallel signature generation.
- [x] AC-04: Cache pairwise similarity in `find_fuzzy_groups` to eliminate duplicate `sequence_similarity` re-computation.
- [x] AC-05: Pass test suite and governance checks.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
