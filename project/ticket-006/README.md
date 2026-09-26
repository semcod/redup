# ticket-006: Atomize sequence similarity and accelerate with native Rust engine

- **Status**: IN_PROGRESS
- **Workflow state**: EDIT

SESSION_EXECUTION_AUTHORIZATION: on 2026-09-26 the user requested sequential execution of performance atomization and Rust acceleration for `redup`.

## Acceptance Criteria
- AC-01: Implement fast sequence / Levenshtein similarity ratio algorithm in `packages/redup-fast-hash` with zero external dependencies.
- AC-02: Support pairwise string similarity comparison via CLI (`--similarity-ratio <a> <b>` or stdin lines) and library API.
- AC-03: Integrate native acceleration into `src/redup/core/matcher.py` (`sequence_similarity`, `fuzzy_similarity`) with transparent fallback to `rapidfuzz` / `difflib`.
- AC-04: Preserve 100% backward compatibility with all existing consumers.
- AC-05: Unit and contract tests in `tests/test_similarity_rust.py` and existing `tests/test_matcher.py`.
- AC-06: Full test suite passes without regressions.
