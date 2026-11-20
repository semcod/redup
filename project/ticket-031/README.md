# Ticket 031: Refresh internal-dependencies documentation review date to resolve DOCS_REVIEW_DUE

- **ID**: ticket-031
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-20
- **Authorization**: SESSION_EXECUTION_AUTHORIZATION (user requested finishing unmerged PRs across organizations including unblocking semcod/redup#39)

## Goal and scope

Refresh the overdue `review_after` metadata (`2026-09-13` -> `2026-12-20`), increment document `version` (`1` -> `2`), and update `updated` (`2026-11-20`) and `source_revision` (`6de6209ea434c60645c891bee1e08ad2bfebc950`) in `docs/information/internal-dependencies.md` to resolve `DOCS_REVIEW_DUE` blocking `test (3.10)` and `test (3.13)` CI workflows.

## Acceptance criteria

- [x] AC-01: `wellmanifest/docs` `check.py` passes with zero errors (`ok: true`, no `DOCS_REVIEW_DUE`).
- [x] AC-02: `./project/governance-check.sh --base origin/main --head HEAD` passes (`GOV-PASS`, 0 errors, 0 warnings) and `wellman check --root .` passes.
- [x] AC-03: Locked test suite passes under `pytest`.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
