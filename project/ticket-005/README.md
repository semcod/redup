# ticket-005: Atomize tokenization, SimHash, MinHash and normalization into pure tokens_hasher module

- **Status**: IN_PROGRESS
- **Workflow state**: EDIT

SESSION_EXECUTION_AUTHORIZATION: on 2026-09-26 the user requested investigation and execution of option A: refactoring and atomizing `redup` before Rust migration.

## Acceptance Criteria
- AC-01: Extract `_fuzzy_simhash`, `_fuzzy_candidate_indices`, `_normalize_text`, and pure MinHash generation into a dedicated pure module `redup.core.tokens_hasher`.
- AC-02: `duplicate_finder.py`, `hasher.py`, and `lsh_matcher.py` import and delegate to `tokens_hasher` maintaining 100% backward compatibility.
- AC-03: Zero coupling to file I/O or `DuplicateGroup` models in `tokens_hasher`.
- AC-04: Full contract tests in `tests/test_tokens_hasher.py` covering golden vectors (hashes, tokens, similarity) to enable subsequent 1:1 Rust implementation verification.
- AC-05: Existing test suite passes with zero regressions.
- AC-06: Create native Rust prototype engine in `packages/redup-fast-hash` computing fuzzy SimHash with zero external dependencies.
- AC-07: Integrate optional Rust accelerator in `tokens_hasher.py` with fallback to Python and benchmark speedup.
