# Verification

## Tests first

- The new fresh-process candidate test first failed because `source_note_ids` was not accepted by the production CLI.
- The numerical test first failed because the supplied-core-distance production API did not exist.
- The new Python package tests first rejected the trial identity and demonstrated that the old package path accepted spliced cross-note metadata. New runner tests first failed because the flag did not exist.
- The preservation/comparison tests first failed because the comparison module did not exist. An independent code audit then identified a missing binding between packaged memberships and the replayed result; the added test first failed for the missing check, then passed after the comparison verified exact memberships against the replayed candidate output.

Existing approved tests were not edited. No test-only production APIs or `cfg(test)` code were introduced.

## Passing checks

62 Rust tests passed across ten suites: candidate (5), candidate artifact (4), artifact adapter (1), HDBSCAN (9), supplied core distances (7), partition geometry (10), candidate CLI (4), cross-note candidate (7), review persistence/contract (10), and masks-only multi-note review (5).

The cross-note tests cover every alias's source note, exact-vector groups spanning notes, overlapping source-note sets, unchanged same-source alias weighting, invalid/incomplete/extra note maps, unsupported `min_samples`, source-map digest changes, forged results, input ordering, and unchanged ordinary candidate behavior.

Python checks passed: 21 package/adapter checks; all five runner tests with the newly frozen binary, none skipped; and five preservation/comparison tests. The Python implementation agent also ran 25 existing scaled-vector/post-hoc-review checks successfully. Rustfmt, targeted Ruff, and scoped whitespace checks passed.

The complete staged whitespace check flags copied original-note whitespace in the two generated `unassigned.txt` evidence files. Those source-text exports are intentionally preserved, not reformatted; code and authored documentation pass the scoped check.

Known unrelated limitations remain: three historical runner tests pin an old executable SHA that was already absent before this change; three historical full-note reviewer assertions conflict with the previously approved masks-only UI. Neither old test set was weakened or rewritten. The corresponding current production paths were tested above; this is not a claim that every repository test passes.

## Full data checks

Both complete trial executions returned identical parsed responses. The trial and baseline retain the same 916 unique-vector ordinals and the same aliases representing all 945 original vectors.

An independent calculation used the saved baseline angular-distance matrix to calculate each nearest-different-note core distance. All 916 matched the trial exactly. All 838,140 off-diagonal mutual-reachability entries matched `max(original angular distance, first core distance, second core distance)` exactly. Of the core distances, 747 increased, 169 stayed equal, and none decreased. This collection has no exact-vector alias group spanning different notes; that edge case is covered by synthetic production-path tests.

The original baseline request was also executed twice using the new frozen binary. Its entire retained result, canonical inputs, and selected output equal the saved baseline. Only `adapter_implementation_source_sha256` and `algorithm_implementation_source_sha256` changed in the artifact manifest, as expected after editing those source files.

The comparison verifies that both packaged partitions match their retained candidate outputs and that every vector's complete note and mask evidence remains identical. All 65 pretrial files match their saved byte counts and SHA-256 hashes after the trial and terminal smoke test.

## Actual terminal

The existing reviewer opened the 41-segment artifact as `Segment 1 of 41`, showing six exact masks in one scrollable list. Ctrl-D scrolled the list, Right moved to segment 2, and Ctrl-C saved and exited successfully. No verdict or comment was entered. Smoke state is isolated under `smoke/`; no user session was created or modified.

## Resources and identities

No subject or mask generation, SSE encoding, or rented compute was used. Cargo ran sequentially with two jobs, an 8 GiB memory limit, no swap, and two CPUs' quota. The largest build reached its 8 GiB cgroup limit and completed successfully; this includes file cache and is not a measured 8 GiB process heap. Host available memory remained approximately 103 GiB at the recorded check.

The complete trial plus replay and packaging took 9.249 seconds, peaking at 321.6 MiB in its cgroup with no swap. Baseline recheck took 8.952 seconds, peaking at 289.9 MiB. Both used a 4 GiB memory limit and two CPUs' quota.

Frozen candidate SHA-256:

```text
d2c0cf7266ad46a09882c395c20e393c08eff1ab27780538219184d96df4a7d9
```

Its pinned local copy is `target/frozen-binaries/d2c0cf7266ad46a09882c395c20e393c08eff1ab27780538219184d96df4a7d9/fine-segmentation-candidate`. Exact commands, request hashes, timestamps, and return codes are in both `replay-proof.json` files.

The terminal-tested review binary SHA-256 is `de45d01a6bf7b436f324d4d3d160d1d41845f374471d9ec0709b7cf0deb9788b`. The new review set is `RN30ea35e75a20`.
