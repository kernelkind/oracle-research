# Integration test evidence

Technical integration checks only; these results are not semantic judgments or algorithm qualification. No new model-generation calls were used.

## Fail before implementation

- The first complete-note review test failed at the production reviewer decoder: `unknown field byte_spans, expected instance or fragments`.
- Both new candidate CLI tests failed before its change: the decoder rejected `hdbscan_configuration`, including the SNN case that now reports the explicit candidate/configuration mismatch.
- Three additional production-path save/resume tests failed before their fixes: Ctrl-C discarded a comment being edited; cancelling a verdict after resuming a skipped segment restored `pending`; supplying a missing session path allowed an existing response to be overwritten.
- Existing approved tests were not changed. New tests exercise the real artifact loader, review state persistence, terminal model, candidate CLI, and production algorithms. No test-only production APIs or `cfg(test)` code were added.

## Final regression command

Run from `/home/dev/src/notedeck_worktrees/algos/oracle-mvp`:

```sh
PATH=/nix/store/w9rw92p5izknryxzvyb5gws1faqa6vz7-cargo-1.95.0/bin:/nix/store/skkini2rsbwv5zgg52z9asps90xsfvsq-rustc-1.95.0/bin:/nix/store/kilyfvfmh9x9rlaj47ph1916lbc1pnsr-gcc-wrapper-14.3.0/bin:/nix/store/3zcs23yc1wbjkmd7s1fp7dncvy17dhr3-gnumake-4.4.1/bin:$PATH \
CARGO_BUILD_JOBS=2 cargo test --offline \
  --test fine_segmentation_review_notes \
  --test fine_segmentation_review \
  --test fine_segmentation_candidate_cli \
  --test fine_region_candidate \
  --test fine_region_candidate_artifact \
  --test fine_region_candidate_artifact_adapter \
  --test fine_region_hdbscan \
  --test fine_region_partition
```

Result: **51 passed, 0 failed**, across eight suites (8 + 10 + 4 + 5 + 4 + 1 + 9 + 10). Cargo completed in 52.69 seconds; Cargo invocations were sequential with two build jobs. The eight new complete-note tests cover exact UTF-8 occurrence selection after non-ASCII text and a tab, full-note scrolling/cycling, comments/skipping/partial response recovery, empty segment output, invalid ranges/conflicting evidence, and the three persistence fixes above. Formatting and targeted `git diff --check` also passed.

## Actual terminal replay

The final binary was tested with copies of sessions; original sessions and responses were not modified.

- Legacy v2: replayed `target/fine-segmentation-hdbscan-review-v2/review-artifact/review.json` with a copy of its historical session and response. The CLI exited successfully with **9 valid, 0 invalid, 0 uncertain**. `cmp` verified both copied files remained byte-identical to the originals.
- Complete-note v3: in a 110-column, 34-row terminal, resumed `sse_multivector/real-note-fine-segmentation-v1/smoke-test/review/review.json` with copies of `manual-session.json` and `manual-response.json`. The first segment displayed the full original Bitcoin Block Art note, its inline mask, the saved skipped state, and `Integration smoke only; not a semantic judgment.` outside the source-note box. Ctrl-C exited successfully; `cmp` verified both saved files were unchanged. The response still contained no judgments.

Replay copies were retained at `/dev/shm/fine-segmentation-v2-replay.uHxvUF/` (`session.json`, `response.json`, `v3-session.json`, `v3-response.json`); this temporary path is evidence location, not a required experiment input. The earlier complete interactive browsing/scrolling check is recorded in `smoke-test/interactive-check.md`.

Final tested executable SHA-256:

```text
e0b54d50ea9c7cdd45a596a81707299c1a9e0fbdf25545fb426e78a92153e001  target/debug/fine-segmentation-review
1d9a45211d8af49c1357509c748331b393bba4280db3cb2391d9e1a75f733a6d  target/debug/fine-segmentation-candidate
```

These hashes identify the tested local builds. Later rebuilds require their own identities; the historical and new user-review sessions must remain separate from this technical smoke review.

## Declared-file integrity fix and candidate-result limitation

The adapter audit demonstrated two distinct integrity gaps with in-memory probes that intercepted output writes:

- Packaging accepted a vector artifact whose declared `worker-receipt.json` was unavailable, because it read only the vector map, reviewed input, and normalized vectors.
- Packaging accepted a changed selected partition after its selected-output hash was updated, even though the retained algorithm still contained four clusters and `result_sha256` was unchanged. The probe would have published one all-vector segment. This was not an observed corruption of the saved experiment artifacts.

The declared-file gap is fixed: packaging reads and checks the size/SHA-256 of **every file declared in the vector manifest**, and rejects missing, unreadable, or changed files before creating output. Two new tests first failed because a missing worker receipt and changed encoder descriptor were accepted; both now pass. A third new test first failed because the candidate-result limitation was absent from metadata; it now passes. Existing approved tests and fixtures were preserved.

The candidate-result gap is handled by an explicit experiment replay requirement, not a new serializer or CLI protocol. Rust's `result_sha256` hashes typed-struct JSON field order and `serde_json` floating-point formatting; the CLI emits that result through `serde_json::Value`, which sorts object keys, while Python also formats some floats differently. Consequently, `package_review` **does not independently validate `result_sha256` or prove that the selected output equals the retained algorithm output**. Its metadata now says `candidate_result_verification.result_sha256_checked: false` and records the required external check: freshly replay each saved request with the pinned unchanged candidate binary and compare the **full parsed response** before packaging. Source bindings and the selected-output hash remain checked. The experiment checkpoint owns the replay evidence and admission decision.

Regression command:

```sh
python3 -m unittest sse_multivector.test_real_note_segmentation sse_multivector.test_fine_segmentation_candidate_runs
```

Result: **16 passed**, in 0.527 seconds. No Cargo, SSE, or model-generation calls were made for this fix.

Saved-smoke packaging replay (uses the existing saved baseline response; does not rerun HDBSCAN):

```sh
python3 -m sse_multivector.real_note_segmentation package-review \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/vectors \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/candidate-response.json \
  sse_multivector/real-note-fine-segmentation-v1/smoke-test/review-declared-files-verified
```

Result: four segments, ten assigned vectors, no noise. `cmp` verified the new `review.json` and `unassigned.json` are byte-identical to those in `smoke-test/review/`; only the packaging metadata/manifest gain the explicit verification limitation. `git diff --check` passed.
