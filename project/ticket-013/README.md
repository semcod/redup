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
- [x] AC-03: Ensure all existing cache tests pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
