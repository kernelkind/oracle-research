# 100-note fine-segmentation development

Goal: `/home/dev/.codex/memories/oracle-mvp-100-note-fine-segmentation-goal.md`.

Started 2026-09-08 UTC from commit `18637cbed7ba45716bc81afd8d4a195e99844b51` on main. Existing unrelated working-tree changes are preserved. Tracking: CREC-118. This experiment has not produced results yet.

## Current checkpoint

Saved-example integration passed: see `smoke-test/integration-gate.json`, `technical-smoke-check.json`, and `interactive-check.md`. Five saved notes and ten reviewed masks passed through the unchanged SSE worker (768 dimensions), baseline HDBSCAN, and the actual unnamed full-note review tool. The four smoke segments are technical outputs, not evidence of semantic success.

The 100-note food/drink collection is frozen in `corpus-selection-v1/notes.json` (SHA-256 `581e465d9a4c3ac5e6e2067a2edb9e9711acb3fd68982909394c9c704151dbf3`). The primary assistant read all 100 original notes. The initial-ten checkpoint passed: `initial-ten-checkpoint.json`. All ten AS calls and 77 MP calls succeeded and were reviewed; one subject and one mask were corrected separately from raw output, and three ambiguous source placements were explicitly resolved. No vectors or segments from the new collection have been inspected.

All 100 subject lists and all 945 masks are reviewed. The consolidated `reviewed-input.json` has SHA-256 `9de47b1a66867e612aaf706da5002d4b04b4e9d8192e3782330a693dd1dea019`. The 946 generated subjects yielded 945 accepted subjects and one unresolved interpretation (N028-S002); eleven subjects and seventeen masks received separately recorded corrections. Eighty-three source placements were explicitly chosen. All original note texts, IDs and authors still equal the frozen collection. See `all-inputs-reviewed-checkpoint.json` and the per-range decision files. Do not rerun completed generation calls.

The unchanged SSE encoding finished successfully in 67.70 seconds. `vectors/` freezes all 945 vectors from all 100 notes; only N028-S002 is excluded. Each vector has 768 dimensions and unit norm within floating-point precision. The normalized vector bytes have SHA-256 `fd545835af8c28c9e11a56286af7b19d343c3adf968070d42268ea2277e3138d`. The baseline HDBSCAN run is in progress; no new-collection groupings have been assessed yet. Exact SSE execution and cgroup samples are under `encoder-run/`.

Reviewed initial inputs remain in `masks-001-010-reviewed/reviewed-input.json`; its `review.txt` shows the chosen masks over complete originals. Independent assistant reviewers covered disjoint later-note ranges, and the primary assistant adjudicated surfaced uncertainties. Each decision file names its actual reviewer; this is not a claim that the primary assistant independently reread every delegated subject.

## Verified inputs and integration gaps

- ASv6.23 and MPv3.5 are frozen, both `gpt-6-astra` / low. Their package manifests are the source of truth; no prompt or model changes.
- The pinned SSE CPU container is present locally. Existing Sentence-T5-base checkpoint and worker remain the encoding path.
- Saved mask-review ranges use UTF-16 offsets; SSE uses UTF-8 bytes. Repeated fragments require explicit placement choices.
- Existing scaled-vector orchestration assumes older takeaway/prominence records; the worker itself accepts original notes plus source ranges without those fields.
- The candidate CLI now accepts an optional explicit HDBSCAN configuration; absent that field, historical baseline behavior is unchanged. Non-HDBSCAN requests cannot silently accept that field.
- The existing review tool now also accepts variable-size v3 real-note artifacts, full-note inline masks, comments, skips, partial responses, and resume. All ten existing v2 tests and a copied historical review still pass unchanged.
- Verification: 34 relevant Python tests and 51 Rust tests across eight suites passed. New behavior was tested failing before implementation. Final stable-binary baseline replay matched the earlier baseline result exactly.

## Work accounting

- Corpus audit: compared food/drink, Bitcoin, and AI using a 21 MB existing tmpfs materialization. Food/drink chosen; 194 manually eligible notes from 176 authors. No new database scan, vectors, or expected fine segments.
- Saved-example integration: passed; no generation calls.
- 100-note selection: frozen after text, copy, author, and actual local-tokenizer checks. The 100 notes contain 95 authors, with at most two notes per author; all fit the unchanged encoder's 512-token limit.
- First ten subjects: ten successful calls, 77 generated subjects reviewed and retained. One correction resolves “coffee chain” as a coffee-themed social-media post rather than a business chain; raw output remains unchanged.
- First ten masks: 77 successful calls, no retries, no JSON parse errors, fresh isolated call contexts verified. All 77 accepted after one correction; three repeated-text placements explicitly resolved. Adapter input preparation passes; no experiment encoding yet.
- Remaining 90 subjects: 90 successful calls; all 869 generated subjects reviewed. Ten wording corrections, one unresolved interpretation, no rejected subjects. Original note IDs, text, and authors in the consolidated artifact exactly match the frozen 100-note collection.
- Remaining masks: all 868 calls completed in 73 sequential batches, at most 12 workers at once. Every call succeeded exactly once with a distinct isolated thread; no parse errors, retries or resource stops. All masks were explicitly reviewed; sixteen were corrected separately from raw output. N028-S002 remains excluded with its reason in input accounting.
- Experiment SSE artifact: complete and frozen after source/range/token, finite-vector, dimension and normalization checks. Baseline HDBSCAN is running through two actual pinned-binary invocations before review admission; configuration comparisons have not started.
- Assistant assessment and final user review handoff: not started.

## Resources

Initial host check: approximately 103 GiB MemAvailable. Existing guarded model runner and disk-pressure guidance will be retained. Cargo is serialized with two build jobs. No new billable resources are authorized or used. The monetary ledger has unresolved reserved values, so it cannot admit new paid work; this goal uses existing local resources and the authorized subscription only.

Initial ten AS calls used 25,976 input tokens (1,920 cached) and 3,663 output tokens (1,051 reasoning). Their 77 MP calls used 186,418 input tokens (50,304 cached) and 7,997 output tokens (6,318 reasoning). Batches ran sequentially with at most 12 isolated workers at once. No generation resource interruptions occurred.

The other 90 AS calls used 236,204 input tokens (57,984 cached) and 34,276 output tokens (8,711 reasoning). All eight batches succeeded without retries or pressure stops. Their 160 guard samples recorded at least 111,561,285,632 bytes available memory and zero sampled memory/I/O pressure.

The remaining 868 MP calls used 2,156,129 input tokens (1,416,576 cached) and 87,272 output tokens (70,247 reasoning). The guarded sequential-batch run took 19m01s. Its 1,208 resource samples recorded at least 111,303,327,744 bytes available memory; peak sampled memory/I/O avg10 pressure was 0.90/1.46. No guard stop or retry occurred. These are generation-run diagnostics, not measurements of SSE quality.

SSE ran with four CPUs and an 8 GiB/no-swap container limit. Its 269 workload-cgroup samples recorded a peak 1,318,621,184 bytes of memory and 8.26% rolling two-second I/O pressure, below the documented 20% backoff threshold. No OOM event occurred and no additional workload was admitted during encoding. See `encoder-run/resource-summary.json`.

Implementation checkpoints: `2971e86` adds the real-note adapter/review integration; `d708b10` verifies every declared vector-evidence file and records the candidate replay requirement. Six mask-range helper tests pass, including ambiguous occurrence refusal and preservation of raw masks after explicit correction. Candidate requests must still be freshly executed twice and their complete parsed responses compared before review packaging; the adapter does not claim to validate Rust's full-result serialization digest independently.

Resume from this checkpoint and the goal document; do not restart completed stages. Concrete replay commands will be recorded beside each artifact as the integration is established.
