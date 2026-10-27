# Ticket 024: Fallback community detection without networkx and preserve shared LOC in decision engine

- **ID**: ticket-024
- **Owner**: agent:gemini
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-10-27

SESSION_EXECUTION_AUTHORIZATION: user requested cross-project standardization duplication audit and fix of `semcod/redup` cross-project comparison and decision engine.

## Goal and scope

Provide a pure-Python connected-components fallback in `detect_communities()` when `networkx` is not installed, and fall back to deduplicated matched-block LOC in `recommend()` when `communities` is empty (`--no-community`).

## Acceptance criteria

- [x] AC-01: `detect_communities()` returns connected-component `CodeCommunity` clusters when `networkx` is absent instead of raising `ImportError`.
- [x] AC-02: `recommend()` computes non-zero `shared_loc` and `overlap_percent` from `comparison.matches` when `communities` is empty.
- [x] AC-03: Unit tests in `tests/test_compare.py` and `./project/governance-check.sh` pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
