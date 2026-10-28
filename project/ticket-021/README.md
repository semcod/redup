# ticket-021: Fix issue #29 by preserving UTF-8 during native SimHash normalization and proving Unicode parity against Python using freshly built Rust source.

- **ID**: ticket-021
- **Owner**: agent:coding-agent
- **Status**: IN_PROGRESS
- **Workflow state**: PUBLICATION

## Goal and scope

Deliver and protectively merge the bounded issue #29 Unicode SimHash correction with source-bound regression evidence, subject to existing controller admission and exact-head review. This planning turn performs no allocation, editing, commit or publication.

SESSION_EXECUTION_AUTHORIZATION: validated native ticket PLF-19944; Willman request a0c469a6-5a7c-4359-9153-7ecd62f0295a; protected publication only.

## Acceptance criteria

- [x] AC-01: AC-01: Native normalization preserves unmatched Unicode scalar values and valid UTF-8 boundaries. Candidate normalization, tokenization and SimHash complete without panics on valid Unicode fixtures.
- [x] AC-02: AC-02: Candidate Rust matches the Python reference for these exact vectors: ASCII add function = 1999307407177186558; ą = 2684146023269591358; zażółć gęślą jaźń = 3173260504582634983; 😀value = 17867692854670522352; const źródło = `żółć`; = 16890555981135166839; fn 変数() {return 1;} = 8428574849076232171.
- [x] AC-03: AC-03: Preserve existing ASCII fingerprints, ASCII identifier normalization, keyword handling, comments, strings, numbers and hashing rules. Qualify Unicode behavior against Python's actual token sequence; do not normalize entire Unicode identifiers as ASCII identifiers.
- [x] AC-04: AC-04: Add Rust regression vectors asserting cleaned text, tokens and fixed fingerprints, including multi-byte letters, emoji, mixed identifiers and ASCII controls. Add one focused Python conformance test that builds and directly invokes the candidate Rust binary and compares with prefer_rust=False; missing or failed candidate execution must fail this required check rather than pass through fallback.
- [x] AC-05: AC-05: Crate native tests, focused Python hashing and pipeline regressions, full Python tests and applicable governance/stack gates pass. Keep installed-extension failures separate from candidate-source results and record candidate source/artifact identity.
- [x] AC-06: AC-06: Before implementation, reconcile accepted base, existing issue #29 intake, overlapping ticket scopes, current ownership, publication receipts and fenced leases through the managed controller. Reuse matching authorized work; do not infer ownership transfer from expired leases or start a competing writer.
- [x] AC-07: AC-07: Require OneDev verification of the exact candidate HEAD against current main and independent Validator approval bound to repository, PR, HEAD, ticket and actor before protected-controller merge. Report completed, locally committed, pushed/PR-open and merged/deployed states separately; no PyPI publication or shared-environment deployment.

## Implementation evidence — 2026-10-24

PLF-19944 / semcod/redup#29 remains the admitted request. Complexity is S,
estimated 20 minutes. The immutable intent was not edited; its file SHA-256 is
`d4c95c69352e46daec0dc331252803cfd4094034d371475e761f9a5a62d76850`.
The latest session instruction authorizes scoped editing and focused checks only;
commits, branch changes, remote effects and authoritative gates belong to the runner.

- `clean_code_for_fuzzy` now copies each unmatched non-ASCII scalar intact and
  advances by its UTF-8 length. Existing ASCII scanner branches remain intact.
  Python's ASCII identifier regex is unchanged: mixed identifiers split into
  ASCII `ID` tokens and individual lowercased Unicode tokens. Backticks remain
  ordinary tokens. This is not a general tokenizer redesign.
- Embedded Rust tests assert cleaned text, exact tokens and golden fingerprints
  for all six admitted vectors plus seven controls covering comments, quotes,
  escaped emoji, numbers, operators, mixed identifiers and Unicode lowercasing.
  Six incomplete comment/string inputs also exercise UTF-8 end boundaries.
- One required Python conformance test builds this checkout with Cargo `--locked`
  in a fresh target directory and directly invokes that release binary for all
  13 vectors. Missing Cargo, build errors or execution errors fail the test;
  installed bindings, discovery and fallback cannot satisfy it. Successful builds
  attach source/binary digests, binary path and build exit code as test properties.

### Focused validation

- PASS: `rustc --edition=2021 --test /tmp/redup-ticket-021-simhash-tests.rs -o
  /tmp/redup-ticket-021-simhash-tests`, then `/tmp/redup-ticket-021-simhash-tests`:
  **6 passed**. The temporary harness imports this worktree's actual `simhash.rs`
  and `blake2b.rs` by absolute path; no copied candidate or installed extension.
  This is supplemental source validation, not a successful full-crate build.
- PASS: negative control compiled the frozen-base production implementation with
  the new regression tests. The golden-vector test rejected `ą` because the old
  cleaner returned `Ä\u{85}`. This is an expected assertion failure, separate
  from the historical installed-extension panic reported in the issue.
- PASS: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -o addopts= -q
  tests/test_tokens_hasher.py tests/test_pipeline.py`: **25 passed** (Python 3.13.7).
- Auxiliary: the same pytest flags with `tests/test_tokens_hasher_rust.py -k
  'missing_binary or pyo3'` reported **4 passed, 3 deselected**. The installed
  extension is absent here, so the three existing PyO3 tests return early; they
  provide no candidate-native validation. The missing-binary test did execute.
- BLOCKED: `cargo test --locked --offline --manifest-path
  packages/redup-fast-hash/Cargo.toml --target-dir /tmp/redup-ticket-021-native`
  exited 101: cached `crossbeam-deque v0.8.8` is unavailable.
- BLOCKED: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -o addopts= -q
  tests/test_tokens_hasher_rust.py -k unicode_candidate_conformance
  --junitxml=/tmp/redup-ticket-021-conformance.xml -o junit_family=legacy`
  reported **1 failed, 6 deselected**. Cargo exited 101 while downloading locked
  dependencies because `static.crates.io` DNS is unavailable. No full-crate
  candidate artifact was produced. AC-04 execution and AC-05 remain pending.
- PASS: file-scoped `rustfmt --check`, Python syntax parsing and `git diff --check`.
  Ruff is unavailable. The initial system pytest startup also encountered a
  globally installed plugin missing `aiohttp.test_utils`; disabling unrelated
  plugin autoload avoids that environment failure without environment mutation.
- No full repository verification, governance gate or todo2code comparison ran.
  The explicit pytest `addopts` override prevents the automatic broad governance
  bridge during this model turn, as requested. Runner-owned authoritative checks,
  full-crate/release build and Python 3.10 coverage are still required.

Candidate `simhash.rs` SHA-256:
`fa203840c19fdc156d6652df576ec2ab12bbf4aa1cf4da1b688cb0b4a0748ac2`.
Candidate Python test SHA-256:
`43acd1415635d08e7072bfe9809e789446d6393201b551a2a7d701fbcf6f26e8`.
Supplemental test executable `/tmp/redup-ticket-021-simhash-tests` SHA-256:
`ddbc8c87d912e7cbd12948ee079ea0fcc4d00c5c988b0a90f7c9c2eb474241b6`.
Toolchain: rustc 1.97.1, Cargo 1.97.1. No dependencies or shared environments changed.

### Bounded checkpoint / runner handoff

- Ticket/slice: ticket-021, PLF-19944, issue #29; immutable `intent.json` above.
- Worktree: `.worktrees/ticket-021--project-job-a0c469a6`.
- Branch: `ticket/021-project-job-a0c469a6`.
- HEAD and accepted base: `0cbd10d40d367ddbc25d745b3643461e5708f8b4`;
  local main and already-fetched origin/main match. No fetch or account switch.
- Managed work-start check returned `REUSE_EXISTING`, no blockers, one active
  ticket. Runner overlap receipt under its PLF-19944 session artifacts passed.
  Unintegrated legacy branches were observed and left untouched.
- Lease: `allocation-ticket-021-project-job-a0c469a6`, owner `agent:coding-agent`,
  session `allocation-ticket-021-2026-10-24T17:51:51Z`, revision 1, fencing token 1,
  claimed; expiry `2026-10-24T19:51:51Z`; `pullRequest: null` at observation.
  No renewal, takeover or lease modification occurred.
- No prior ticket-021 continuity checkpoint was found. This bounded handoff is
  stored only in the authorized README. Runner must persist the content-addressed,
  secret-scanned dirty snapshot and managed v2/external continuity receipt; no
  snapshot or external receipt is claimed by this model turn.
- Next action: runner revalidates lease/base and makes locked crate dependencies
  available in its permitted build environment, runs required candidate
  conformance/full-crate checks and authoritative gates once, then freezes the
  resulting HEAD for OneDev current-base verification and independent Validator.
  Only the protected runner may commit, publish or merge after those gates.

### Delivery ledger

- Completed: scoped UTF-8 correction and regression implementation; supplemental
  native and focused Python evidence above. Overall validation remains incomplete.
- Locally committed: **no**; source edits remain in this authorized worktree.
- Pushed / PR-open: **no effect performed**; runner lease has no PR binding.
- Merged / deployed: **no**; independent approval and protected merge pending;
  deployment and PyPI publication are outside this slice.

Status remains **IN_PROGRESS / PUBLICATION** for runner-owned validation/delivery.
