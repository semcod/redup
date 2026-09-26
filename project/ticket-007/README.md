# ticket-007: Atomize AST normalizer and exact/structural matcher

- **Status**: IN_PROGRESS / PUBLICATION
- **Workflow state**: VERIFIED

SESSION_EXECUTION_AUTHORIZATION: on 2026-09-26 the user requested sequential execution of performance atomization for `redup` (Atom 2: Exact & Structural Block Matcher).

## Acceptance Criteria
- [x] AC-01: Extract AST structure tokenization and normalized text generation into `src/redup/core/ast_normalizer.py`.
- [x] AC-02: Extract block collision indexing, different location filtering, and exact/structural collision grouping into `src/redup/core/exact_matcher.py`.
- [x] AC-03: `src/redup/core/hasher.py` delegates to `ast_normalizer` and `exact_matcher` maintaining 100% backward compatibility.
- [x] AC-04: Full contract tests in `tests/test_exact_matcher.py` verifying grouping and collision filtering.
- [x] AC-05: Existing test suite passes with zero regressions (212 passed, 13 skipped).
