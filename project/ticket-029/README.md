# Ticket 029: Align redup __version__ with VERSION 0.4.49

- **ID**: ticket-029
- **Owner**: unresolved:human
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-18

## Goal and scope

Fixes semcod/redup#37. `src/redup/__init__.py` declared `__version__ = "0.4.48"` while the authoritative
`VERSION` is `0.4.49`, so the new-project 0.20.162 gate reports GOV-VERSION-001 and the fleet standard
adoption cannot land. Align `__version__` with `VERSION` and add a regression test for the parity.

## Acceptance criteria

- [ ] AC-01: `__version__` equals `VERSION` (0.4.49) and `tests/test_version_parity.py` passes.
- [ ] AC-02: `project/governance-check.sh` passes.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
