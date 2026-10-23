# Ticket 020: Repair dependency freshness and public docs verification

- **ID**: ticket-020
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

SESSION_EXECUTION_AUTHORIZATION: user requested continued backlog repair, tests and merges. Parent Planfile PLF-17346. Complete the dependency intent of existing PR27 through governed delivery.

## Scope and acceptance

- [x] AC-01: Published stable dependency lock targets are current; only uv.lock and the locked test workflow change materially.
- [x] AC-02: Both immutable public standard checkouts work with contents-read github.token, while action/standard pins, credential persistence controls and every check remain intact.
- [x] AC-03: Required Python3.10/3.13 tests, pinned docs verification and managed governance pass.
- [ ] AC-04: Independent exact-head Validator and protected merge deliver this repair; reconcile PR27 only after coverage proof, preserving its unmerged branch.

Native allocator owns the relative linked worktree and exact scoped lease. No human-owned files, algorithm, runtime installation or protected policy changes are included.

Session bound: maxActiveMinutes=90, within the manifest120-minute ceiling.

## Validation evidence

Python3.10 and3.13 each:251passed,15skipped. Managed worktree governance:0errors,0warnings. Pinned docs0714f71 with managed-copy digests derived from pinned new-projectfa7972d:PASS. Dependency freshness:PASS. Operational receipts remain private; trusted review and merge are still pending.
