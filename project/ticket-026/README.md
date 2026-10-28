# Ticket 026: Document dev test installation in README

- **ID**: ticket-026
- **Owner**: antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION
- **Created**: 2026-10-28

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requested autonomous completion of remaining backlog tasks (`kontynuuj, testuj, scalaj, wykonuj zalegle`) for `semcod/redup#30`.
Document the `[dev]` optional dependencies installation (`pip install -e ".[dev]"`) and test command (`pytest -q`) in `README.md` so contributors and fleet verifiers install `pytest` before running the test suite.

## Acceptance criteria

- [x] AC-01: `README.md` documents `pip install -e ".[dev]"` and `pytest -q` under Installation.
- [x] AC-02: `./project/governance-check.sh --base origin/main` and `pytest -q` pass.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
