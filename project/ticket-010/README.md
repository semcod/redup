# Ticket 010: Restore LSH near-duplicate results for real code blocks

- **ID**: ticket-010
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT

## Session authorization

SESSION_EXECUTION_AUTHORIZATION: the user requested implementation, tests and
deployment of Koru dependency repairs, then accepted the listed followups with
“tak”. This ticket delivers the separate reDUP LSH correctness observation.

## Goal and scope

The installed datasketch backend returns string keys; comparing these to an
integer hides valid matches. Group construction hashes mutable CodeBlock
instances and fails before returning any group. Restore native and fallback
results, omit self-only groups and repeated members, and retain lazy startup.
Only lsh_matcher.py and its focused tests change. No timeout, routing,
governance, dependency, threshold or clustering-policy overhaul.

## Acceptance criteria

- [x] AC-01: Native string-key candidates return threshold-qualified matches;
  unavailable or failing LSH candidate selection retains hash comparison.
- [x] AC-02: Real mutable CodeBlock instances form groups without hashing,
  self duplication, singleton groups or repeated already-grouped members.
- [x] AC-03: Native and fallback pipeline regressions, existing startup tests,
  full test suite and governance pass.
- [ ] AC-04: Protected exact-head review/merge and local runtime verification.

## Delivery

Publish through the independent protected controller, then activate the
merged code in the existing local editable runtime. No public package release.

Validation: 12 focused LSH cases (11 failed before the fix); 233 passed,
13 skipped in the full suite; Ruff and governance pass.
