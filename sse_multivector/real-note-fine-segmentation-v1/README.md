# 100-note fine-segmentation development

Goal: `/home/dev/.codex/memories/oracle-mvp-100-note-fine-segmentation-goal.md`.

Started 2026-09-08 UTC from commit `18637cbed7ba45716bc81afd8d4a195e99844b51` on main. Existing unrelated working-tree changes are preserved. Tracking: CREC-118. The 100-note experiment is complete and ready for user review; the larger 500–1,000-note roadmap is not complete.

[Results](results.md) · [Full-note evidence](evidence.md) · [Run the unnamed review tool](review-handoff/README.md)

## Current checkpoint

Saved-example integration passed: see [the gate](smoke-test/integration-gate.json), [technical checks](smoke-test/technical-smoke-check.json), and [interactive checks](smoke-test/interactive-check.md). Five saved notes and ten reviewed masks passed through the unchanged SSE worker (768 dimensions), baseline HDBSCAN, and the actual unnamed full-note review tool. The four smoke segments are technical outputs, not evidence of semantic success.

The 100-note food/drink collection is frozen in `corpus-selection-v1/notes.json` (SHA-256 `581e465d9a4c3ac5e6e2067a2edb9e9711acb3fd68982909394c9c704151dbf3`). The primary assistant read all 100 original notes. The initial-ten checkpoint passed before expansion: `initial-ten-checkpoint.json`. All ten AS calls and 77 MP calls succeeded and were reviewed; one subject and one mask were corrected separately from raw output, and three ambiguous source placements were explicitly resolved. No new-collection vectors were inspected before all subjects and masks were reviewed.

All 100 subject lists and all 945 masks are reviewed. The consolidated `reviewed-input.json` has SHA-256 `9de47b1a66867e612aaf706da5002d4b04b4e9d8192e3782330a693dd1dea019`. The 946 generated subjects yielded 945 accepted subjects and one unresolved interpretation (N028-S002); eleven subjects and seventeen masks received separately recorded corrections. Eighty-three source placements were explicitly chosen. All original note texts, IDs and authors still equal the frozen collection. See `all-inputs-reviewed-checkpoint.json` and the per-range decision files. Do not rerun completed generation calls.

The unchanged SSE encoding finished successfully in 67.70 seconds. `vectors/` freezes all 945 vectors from all 100 notes; only N028-S002 is excluded. Each vector has 768 dimensions and unit norm within floating-point precision. The normalized vector bytes have SHA-256 `fd545835af8c28c9e11a56286af7b19d343c3adf968070d42268ea2277e3138d`. Exact SSE execution and cgroup samples are under `encoder-run/`.

Three HDBSCAN configurations are complete, each verified by two actual pinned-binary executions with equal full parsed responses: baseline (2/2/EOM), leaf (2/2/leaf), and density (3/2/EOM). They produced 252, 260 and 119 segments respectively. Their configuration plans and complete outputs are preserved. The alternatives recover some relationships and lose others; neither is selected as the final algorithm. Configuration exploration stops at this documented tradeoff rather than continuing a blind parameter search.

Every baseline segment and all 82 newly appearing alternative segments have separate assistant assessments. Exact unchanged membership and evidence are reused. The unchanged handoff artifacts contain 252 baseline segments, 15 leaf changes and 67 density changes. The reviewer now displays only their multi-note segments: 43 baseline, 3 leaf changes and 23 density changes. All masks in each displayed segment appear together without surrounding note text. Full original partitions and all ungrouped masks remain accessible; saved decisions are preserved. Assistant assessments and technical smoke sessions are separate. The earlier full-note CLI checks are recorded in `handoff-smoke/interactive-check.md` and `handoff-smoke/integrity-result.json`.

Masks-only UI verification: six new production-path tests pass, covering all masks together, distinct-note filtering, navigation, scrolling, and historical-session preservation. The actual terminal shows all four masks of the first baseline segment together and a total of 43 segments. Across the relevant Rust suites, 54 tests pass; three unchanged historical tests still require full-note display or Tab note cycling and conflict with the approved replacement. Updating those existing assertions awaits explicit permission. The experiment inputs and the user's session/response files were not modified.

Reviewed initial inputs remain in `masks-001-010-reviewed/reviewed-input.json`; its `review.txt` shows the chosen masks over complete originals. Independent assistant reviewers covered disjoint later-note ranges, and the primary assistant adjudicated surfaced uncertainties. Each decision file names its actual reviewer; this is not a claim that the primary assistant independently reread every delegated subject.

## Verified inputs and integration gaps

- ASv6.23 and MPv3.5 are frozen, both `gpt-6-astra` / low. Their package manifests are the source of truth; no prompt or model changes.
- The pinned SSE CPU container is present locally. Existing Sentence-T5-base checkpoint and worker remain the encoding path.
- Saved mask-review ranges use UTF-16 offsets; SSE uses UTF-8 bytes. Repeated fragments require explicit placement choices.
- Existing scaled-vector orchestration assumes older takeaway/prominence records; the worker itself accepts original notes plus source ranges without those fields.
- The candidate CLI now accepts an optional explicit HDBSCAN configuration; absent that field, historical baseline behavior is unchanged. Non-HDBSCAN requests cannot silently accept that field.
- The existing review tool accepts variable-size v3 artifacts containing full original notes and exact mask ranges. It displays all masks together for segments containing at least two distinct notes, with comments, skips, partial responses, and resume. Full source evidence and saved reviews remain unchanged. Legacy v2 review is unchanged.
- Verification: the final 32 relevant Python tests and 51 Rust tests across eight suites passed. New behavior was tested failing before implementation. Final stable-binary baseline replay matched the earlier baseline result exactly.

## Work accounting

- Corpus audit: compared food/drink, Bitcoin, and AI using a 21 MB existing tmpfs materialization. Food/drink chosen; 194 manually eligible notes from 176 authors. No new database scan, vectors, or expected fine segments.
- Saved-example integration: passed; no generation calls.
- 100-note selection: frozen after text, copy, author, and actual local-tokenizer checks. The 100 notes contain 95 authors, with at most two notes per author; all fit the unchanged encoder's 512-token limit.
- First ten subjects: ten successful calls, 77 generated subjects reviewed and retained. One correction resolves “coffee chain” as a coffee-themed social-media post rather than a business chain; raw output remains unchanged.
- First ten masks: 77 successful calls, no retries, no JSON parse errors, fresh isolated call contexts verified. All 77 accepted after one correction; three repeated-text placements explicitly resolved. Adapter input preparation passed before remaining generation.
- Remaining 90 subjects: 90 successful calls; all 869 generated subjects reviewed. Ten wording corrections, one unresolved interpretation, no rejected subjects. Original note IDs, text, and authors in the consolidated artifact exactly match the frozen 100-note collection.
- Remaining masks: all 868 calls completed in 73 sequential batches, at most 12 workers at once. Every call succeeded exactly once with a distinct isolated thread; no parse errors, retries or resource stops. All masks were explicitly reviewed; sixteen were corrected separately from raw output. N028-S002 remains excluded with its reason in input accounting.
- Experiment SSE artifact: complete and frozen after source/range/token, finite-vector, dimension and normalization checks. All three HDBSCAN runs passed their complete replay checks before review admission.
- Assistant assessment and final user review handoff: complete. Interpretations remain provisional, and no favorable outcome or user-completed review is claimed.

## Resources

Initial host check: approximately 103 GiB MemAvailable. Existing guarded model runner and disk-pressure guidance will be retained. Cargo is serialized with two build jobs. No new billable resources are authorized or used. The monetary ledger has unresolved reserved values, so it cannot admit new paid work; this goal uses existing local resources and the authorized subscription only.

Initial ten AS calls used 25,976 input tokens (1,920 cached) and 3,663 output tokens (1,051 reasoning). Their 77 MP calls used 186,418 input tokens (50,304 cached) and 7,997 output tokens (6,318 reasoning). Batches ran sequentially with at most 12 isolated workers at once. No generation resource interruptions occurred.

The other 90 AS calls used 236,204 input tokens (57,984 cached) and 34,276 output tokens (8,711 reasoning). All eight batches succeeded without retries or pressure stops. Their 160 guard samples recorded at least 111,561,285,632 bytes available memory and zero sampled memory/I/O pressure.

The remaining 868 MP calls used 2,156,129 input tokens (1,416,576 cached) and 87,272 output tokens (70,247 reasoning). The guarded sequential-batch run took 19m01s. Its 1,208 resource samples recorded at least 111,303,327,744 bytes available memory; peak sampled memory/I/O avg10 pressure was 0.90/1.46. No guard stop or retry occurred. These are generation-run diagnostics, not measurements of SSE quality.

SSE ran with four CPUs and an 8 GiB/no-swap container limit. Its 269 workload-cgroup samples recorded a peak 1,318,621,184 bytes of memory and 8.26% rolling two-second I/O pressure, below the documented 20% backoff threshold. No OOM event occurred and no additional workload was admitted during encoding. See `encoder-run/resource-summary.json`.

Implementation checkpoints: `2971e86` adds the real-note adapter/review integration; `d708b10` verifies every declared vector-evidence file and records the candidate replay requirement. Six mask-range helper tests pass, including ambiguous occurrence refusal and preservation of raw masks after explicit correction. Candidate requests must still be freshly executed twice and their complete parsed responses compared before review packaging; the adapter does not claim to validate Rust's full-result serialization digest independently.

Final regression: all 51 prebuilt Rust production-path tests and 32 relevant Python tests passed again, with unchanged tested binary hashes and no Cargo rebuild. See `handoff-smoke/regression-result.json`.

Resume by opening the review tool, not by rerunning generation or encoding:

```sh
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp
E=sse_multivector/real-note-fine-segmentation-v1
./target/debug/fine-segmentation-review \
  "$E/review-handoff/baseline/review.json" \
  "$E/review-handoff/baseline/user-session.json" \
  "$E/review-handoff/baseline/user-response.json"
```

The same command restores partial progress. `review-handoff/README.md` explains how to inspect the alternatives without repeating identical groups. `package_handoff.py` records the mechanical packaging operation and refuses to overwrite an existing handoff. Each `hdbscan-*/replay-proof.json` records the exact request, configuration, executable identity and invocation arguments. The frozen vector artifact never needs regeneration to compare these saved results.
