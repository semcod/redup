# Ticket 009: Defer LSH imports from SDK and CLI startup

- **ID**: ticket-009
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-09-28

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: the user requested implementing, publishing and testing
Koru dependencies that delay task execution, then continued that request.
Prerequisite ticket-008 merged through protected PR #13 at `1f81dee2b4600c36452555ad37ad11aa6327b07f`.
Change only matcher/pipeline LSH imports and focused startup regression tests.
Load the existing LSH implementation only for eligible work or explicit compatibility
export access. Preserve native callable identity/signature, discovery, monkeypatch
points, thresholds, installed-backend behavior and missing-package fallback.
No dependency changes or LSH algorithm repair. Unknown primary workflow and old
Koru benchmark branches remain preserved outside this admitted scope.

## Acceptance criteria

- [x] AC-01: Fresh SDK import and CLI help do not load datasketch/SciPy; disabled
  or below-threshold LSH work does not load the backend.
- [x] AC-02: Explicit exports keep native identity/signature/discovery, eligible
  work keeps arguments and groups, and missing-package fallback remains usable.
- [x] AC-03: Existing duplicate detection and full tests pass; paired fresh-process
  measurements and the actual Koru changed-scan wrapper show output parity.
- [ ] AC-04: Publish through independent exact-head validation and activate the
  trusted merged revision; retain four separate delivery states.

## Validation

Nine fresh-process regressions: 8 failed/1 passed before the change, all 9 pass
afterward. Full suite: 221 passed, 13 skipped (36.10s); governed checks,
Ruff and whitespace checks pass. Five alternating baseline/candidate startup
pairs: SDK median 1.1654s -> 0.1620s, CLI help 1.3594s -> 0.4001s.
Three pairs using actual Koru `changed-scan` at merged revision
`a30898695eb07212808318ccc9c072190c500e86`: 2.0511s -> 0.6256s;
one changed short Python file scanned, stable semantic report in both revisions.
These are local process measurements, not claims about total task completion time.
Pending: protected CI/review/merge and activation of the resulting exact revision. The pre-existing native LSH string-key bug is separately
recorded; matching its empty result is not evidence of positive LSH correctness.
