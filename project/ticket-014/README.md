# Ticket 014: Enforce reDUP CLI duplicate budgets

- **ID**: ticket-014
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-11

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requests continuation of standard refactoring, verification and Issue/PR maintenance. Parent wellmanifest/PLF-002; bounded follow-up [reDUP #20](https://github.com/semcod/redup/issues/20), Planfile PLF-022. Application preflight admits a disjoint scope; Docs229 remains frozen.

Fix the CLI check command's successful exit despite exceeded duplication budgets. Preserve scanner behavior and MCP contracts. Canonical cross-repository result remains [harmonization v13](https://github.com/subactor/docs/blob/b80c27e6d4c8caa0c6db389eddb4377d9f86cd8a/architecture/analysis/wellmanifest-standards-harmonization.md); new evidence awaits protected report recovery.

## Acceptance criteria

- [x] AC-01: CLI enforces both configured/default and explicit budgets, with equality passing and invalid budgets rejected.
- [x] AC-02: Actual CLI duplicate and empty fixtures plus configuration/override regression tests pass; managed governance passes.
- [ ] AC-03: Material change published and independently reviewed through the declared protected route.

## Tracking boundary

Verification: 16 new CLI cases; full suite 256 passed / 13 existing skips, zero failures. Three negative CLI cases fail against the unchanged baseline. Exact Metafile source canary exits1 with groups94/lines1152 instead of the baseline's misleading exit0. Ruff lint/format and scoped governance pass. No protected approval or merge is inferred from these local checks.

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
