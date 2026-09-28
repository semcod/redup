# Ticket 008: Adopt delivery prerequisites for dependency remediation

- **ID**: ticket-008
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-28

## Goal and authority

SESSION_EXECUTION_AUTHORIZATION: implement and test dependencies delaying Koru; explicit user handoff of .gitignore, AGENTS.md, CLAUDE.md, GEMINI.md, .aider.conf.yml, .cursor/rules/new-project-standard.mdc and .github/copilot-instructions.md. Install the immutable published new-project 0.20.54 package needed by those host entries, preserving independent protected delivery and private operational state.

The managed allocator reserved ticket-008 and created this canonical checkout, then stopped because the pre-adoption base lacks ticket_storage.py. Restore the verified package and finish that same allocation; no replacement identity, source changes or publication from the preparation branch. The handed-off originals are secured externally and in stash 34420a73a21e1e7441cd34c1fd6d0c6d8191316e.

## Acceptance criteria

- [x] AC-01: Immutable published source and managed hashes verify; allocator and host activation work.
- [x] AC-02: Governance and existing reDUP checks pass without disabling checks.
- [ ] AC-03: Protected review and merge bind the exact head; primary unknown files remain intact.

## Limits

No reDUP source or dependency changes in this prerequisite ticket. No reviewer rotation, admin bypass or self approval.

Validation: pinned adoption is up-to-date; pytest lifecycle governance passes; 212 tests passed and 13 skipped in 43.78s (Python 3.13). No algorithm edits. Bootstrap estimate corrected before first commit: immutable first adoption needs eight target-owned files, complexity M budget nine.

CI compatibility repair: preserve published new-project v0.20.54; adopt independently merged docs checker 0714f714 (0.6.0, not a published release) and its policy digest. Required Python 3.10/3.13 jobs acquire standard-copy hashes from independently pinned source, never candidate metadata. Legacy ticket-007 status reflects already merged PR #12 and grants no approval. This necessary compatibility adds two target-owned paths; complexity revised to L, ten implementation files before the repair commit. Original configuration handoffs remain restorable.

Repaired validation: 212 passed, 13 skipped in 18.35s; current all-path CI governance has no findings; docs check verifies three independently hashed manuals and rejects an incorrect digest. Immutable adoption remains v0.20.54 with no drift.
