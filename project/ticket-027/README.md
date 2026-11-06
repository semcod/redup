# Ticket 027: Index fallback MinHash candidates without losing duplicate matches

- **ID**: ticket-027
- **Owner**: tom (session request); implementation agent: codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-11-06

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requested compact, complete project analysis and repeatedly instructed “kontynuuj, scalaj”. This ticket implements the upstream reDUP performance repair tracked by PLF-19981 under coordination PLF-19979.

Without datasketch, every query currently compares all signatures, causing quadratic work across workspace inventories. Index disjoint signature bands to retain every result accepted by the existing floating-point threshold comparison. Keep original scoring, equal-score occurrence ordering and duplicate grouping. Rebuild after additions or a threshold change; preserve exhaustive behavior for unsupported thresholds or native scoring. The source scope is exactly lsh_matcher.py and its existing regression tests; dependency/backend selection is unchanged.

## Acceptance criteria

- [x] AC-01: Record existing user execution/publication authorization and exact native allocation.
- [x] AC-02: Match exhaustive fallback results, scores, ordering and groups, including floating-point boundaries and index additions.
- [x] AC-03: Demonstrate bounded candidate comparison reduction on an unrelated-signature inventory without capping results.
- [x] AC-04: Pass native affected tests, supported-version tests and governance checks.
- [ ] AC-05: Independent protected Validator approval and merge of the exact frozen PR head.

## Delivery evidence

Host evidence: tellmesh/.planfile/evidence/project-analysis-remaining-20261106. Native lease ticket-027--fallback-minhash-index, revision 1, fencing token 1. Preserve all other leases, branches and worktrees.

Validation: 294 passed / 14 optional-backend skips on each Python 3.10 and 3.13 (locked dev dependencies); 63 passed / 10 skips in affected tests with the existing native extension environment. Ruff and the native governance gate pass. The new comparison-budget regression failed before implementation (1000 scores versus 1 required) and passes afterward. The bounded 1000-vector / 1000-query benchmark retained every ordered result: 1,000,000 to 1,000 Jaccard calls, 15.346 s to 0.463 s on this host. Dense candidate sets may still require exhaustive scoring. Independent approval/merge remains pending.
