# Ticket 013: optimize sqlite cache with wal mode and batch commits

- **ID**: ticket-013
- **Owner**: Antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-10

## Goal and scope

Optimize SQLite `hash_cache.db` performance and reduce disk I/O load during incremental scans.
By enabling WAL mode (`PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;`) and batching commits instead of committing on every file, we eliminate heavy fsync loops (`jbd2_log_wait_commit`) that cause disk freezes on large repositories.

## Acceptance criteria

- [x] AC-01: Enable WAL journal mode and normal synchronous mode on SQLite connection in `HashCache`.
- [x] AC-02: Batch commits during `store_file_hashes` and provide `flush()` / `close()` methods.
- [x] AC-03: Eliminate IPC subprocess overhead via in-process PyO3 + Rayon Rust extension (`redup-fast-hash`).
- [x] AC-04: Implement native parallel LSH band candidates and MinHash signature computation in Rust.
- [x] AC-05: Benchmark scan on large repository (5,761 files, 1.13M lines) drops from 50 minutes to ~1 minute 9 seconds.
- [x] AC-06: Ensure all existing and new unit tests pass (238 unit tests + 11 cargo tests).

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

