# Ticket 025: Source-bound cross-project comparison candidates for PLF-20326

- **ID**: ticket-025
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-27

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requested the cross-project intent plan
and then explicitly said "wykonaj" on 2026-10-27. Implement RED, Planfile
PLF-20326 / semcod/redup#32. The exact Heyasa campaign was paused with no jobs
or ticket reservations before native allocation; its autonomy label is held
while this single writer works. Other ticket worktrees remain untouched.

Extend the existing comparator and shared CLI/MCP report with a versioned,
source-bound advisory projection. Reuse scanner blocks and existing matching;
do not add another intent parser, ticket exporter or quality-ranking engine.
Capture scan content, observed Git revision, freshness and explicit source
origins. Missing optional semantic evidence and behavioral verification stay
unknown. Existing Intract integration remains the owner of declared contracts.

## Acceptance criteria

- [x] AC-01: Comparison output binds candidates to full source revision where
  available, file/content hashes, exact spans, analyzer and scan coverage.
- [x] AC-02: Stable candidate identities survive identical reruns; changed or
  missing source and non-Git input are represented explicitly.
- [x] AC-03: Exact, structural and inferred semantic evidence remain distinct;
  generated/deployment origins require explicit declarations, not LOC guesses.
- [x] AC-04: Recommendations remain advisory and cannot establish a superior
  implementation, compatible effects/license, or behavioral verification.
- [x] AC-05: Regression fixtures cover identical, renamed, unrelated,
  generated/deployment, stale and missing optional evidence; existing APIs and
  Intract tests remain compatible. No Planfile writes from comparison.
- [ ] AC-06: Managed governance and affected tests pass; publish through the
  protected OneDev/Validator path with exact HEAD evidence.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.

## Validation and publication

- 45 affected tests passed on Python 3.11.15, including the real sibling
  Intract integration, comparator, shared reporter, MCP and CLI import checks.
- The missing-extras run passed 39 tests with 3 optional skips before the last
  two regressions were added; explicit missing-engine fixtures remain in the
  final passing run. Ruff and diff whitespace checks passed.
- Scanner-relative paths are qualified per project before matching, preventing
  equal filenames from collapsing across repository identities.
- Observed Git HEAD is explicitly separate from the hash of possibly dirty
  source. Local checkout URI is the available identity; canonical remote
  identity enrichment belongs to Diagit/consumers. Inline declarations use the
  existing optional Intract matcher; manifests remain the Intract artifact
  pipeline's responsibility. Similarity and intent matches cannot prove
  behavioral equivalence.
- Native continuity capture currently requires delivery.targetBranch even for
  allocator-generated compact intents. A bounded external checkpoint preserves
  exact branch/base, source snapshot and allocator lease 1/1; no lease or
  managed file was rewritten to hide this tool incompatibility.
- Publication preflight resolved the protected registry and requires hosted
  test (3.10) / test (3.13). Deployed OneDev has no redup profile. Protected
  review/merge and any missing-profile reconciliation remain outstanding.
