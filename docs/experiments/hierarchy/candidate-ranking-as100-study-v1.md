# Candidate selection on the current fifty-note build

**Result:** keeping original root comparisons and combining the original and
meaning-based selection for children reproduces all 124 saved construction
entries. It preserves the final graph, immutable meanings, evidence supports,
equivalences and holds. The known API-equivalent cost projection is **5.997% lower**:
**$7.296504 → $6.858958**. Production selection was not changed, no new hierarchy
was generated, and no teacher/provider calls or UI refresh occurred.

This uses the [current ASv6.100 regression suite](selection-regressions-v2.md),
`selection-as100-fifty-v2`: 120 comparison-bearing placements across the same
50 source posts, Bootstrap-v96 / Compare-v48. It is separate from the deprecated
ASv6.48 study. Reproducing saved teacher decisions is not human semantic gold;
the original construction's semantic and menu qualifications still apply.

## The tested selection

For one incoming local node, start with the existing production nomination pool
of at most sixteen eligible canonical nodes. These were selected using heading
SSE, text matching and original local ancestor headings. Retain its mapped
canonical parent under the existing rule. Never compare canonical nodes with
each other.

1. **Original local root:** keep its whole original nomination pool.
2. **Local child:** keep the first twelve nodes in that original ordering. Also
   take the first eight from the same pool ranked by cosine between the local
   explicit meaning and each canonical node's fixed explicit meaning. Combine
   the lists and remove duplicate IDs. There are at most sixteen unique nodes;
   smaller source pools stay smaller. Do not pad the result to sixteen.
3. Apply the original placement, settled-answer contradiction and complete
   implication checks. Any extra verification requests still count toward cost.

The rule reads local numbering, meanings and nomination scores; it does not read
saved pair labels, expected placements or case-specific review flags. Research
method `root_baseline_meaning_union-16` implements this rule. Root/child status
comes from the original local numbering: a root has no dot, while a child has
one or more ancestry levels. Roots therefore retain broad-placement evidence;
child selection combines two signals without fitting a prediction model.

Both fixed meanings are encoded alone and their entire text is pooled by SSE.
The original post and canonical graph are still supplied to the unchanged
comparison workflow where required; they are not encoded into these standalone
meaning vectors. Similarity only selects comparisons, never decides containment.

## What the simpler alternatives lost

The initial controlled screen retested five twelve-comparison methods. A learned
method used only current-ASv6.100 labels, with forty development notes and ten
notes excluded from fitting. Development predictions excluded their own note
fold. No historical ASv6.48 weights were transferred. All methods stayed inside
the same original sixteen-node pool.

| Selection | Matched cases | Missed relationships | Unresolved cases |
|---|---:|---:|---:|
| Original first twelve | 117 | 2 | 1 |
| Meaning cosine, twelve | 113 | 2 | 5 |
| Heading encoded beside meaning, twelve | 116 | 1 | 3 |
| Meaning encoded beside heading, twelve | 112 | 3 | 5 |
| Learned score without canonical graph features, twelve | 113 | 4 | 3 |
| Original roots + combined child selection | 119 native + 1 source review | 0 | 0 |

Unresolved is distinct from a wrong relationship. All five smaller fixed-cap
methods omitted evidence from the explicit source review at entry 20; ordered
replay stops there. Some additionally proposed placements requiring comparisons
the original run never made. A known verification contradiction can establish
a hold while other proposed verification requests remain unpriced. Unknowns
were not assigned `neither` or zero cost.

Concrete misses illustrate why a single ranking signal was insufficient:

- Original first twelve lost Dinner C019 as a parent of the local
  **Enjoyment of the proper food the author cooked tonight** (entry 79).
- Meaning cosine lost Food C001 as a parent of local **Dinners** (58), and
  Cuisine C016 as a parent of local **Cheesesteaks** (65).
- The learned score lost four saved relationships, including Meat C033 above
  local **Cheesesteaks** and local **Bread** above Pizza C054.

These are failures to preserve saved outcomes, not independently adjudicated
semantic errors. The combined rule was designed after seeing this screen, so
its successful result is exploratory development evidence, not an untouched
test or an approved deployment policy.

## Full replay and API-equivalent cost

The combined selection passes every original snapshot and the complete ordered
replay. Earlier history retains only answers that this selection actually
requests or verifies. All 124 entries match; 119 placement cases pass native
checks and one retains its explicit agent-review hold with its full original
evidence. Bootstrap and three producer-review holds remain fixed.

| Measurement | Original | Combined selection |
|---|---:|---:|
| Shortlist comparisons | 1,791 | 1,607 |
| Verification comparisons | 5 | 6 |
| Total comparison cases | 1,796 | 1,613 |
| Original comparison attempts, including failures | 1,807 | 1,623 |
| Known comparison API-equivalent subtotal | $4.8477276 | $4.4101816 |
| Other original work, kept fixed | $2.4487764 | $2.4487764 |
| Known total | $7.2965040 | $6.8589580 |

This is **10.19% fewer comparison cases**, **9.03% lower known comparison cost**
and **6.00% lower known total cost**. Uncached comparison input falls 8.92%,
cached input 10.36%, and output 9.01%. Reasoning remains included in output and
is not charged twice. Reported cache-write tokens are zero.

The accounting follows exact reuse references through the native generation
report, unions original file/line identities, retains source retries, and uses
native token/cost functions. Reuse markers are neither paid attempts nor free
original generations. A bug in the earlier helper omitted 190 reused originals'
costs and misclassified them as fixed overhead. Correcting their attribution
adds $0.508978 to both comparison subtotals and subtracts the same amount from
fixed overhead. The total saving happens to remain unchanged because this rule
retains all of those reused originals. Earlier reports are preserved separately.

Every original warmup stays in fixed overhead, including warmups attached to
reused sources. The denominator also retains the original AS/meaning generation
and archived/replayed work. Fourteen original failed attempts lack usage; the
combined selection retains thirteen, so complete totals remain unknown. These
are saved-token projections, not cash subscription charges or measured fresh
build savings. Encoding/infrastructure costs and future cache behavior are not
measured by this projection.

## Reproduction and limits

The 48 targeted ranking, selection, vector/worker and native cost checks pass.
A broadened 59-test run has one existing error in
`test_generation_costs_keep_zero_normalized_failure_usage_unknown`: it expects
a complete $0.10 estimate where the runner now returns an unknown total after
a failed attempt with missing usage. The same error reproduces on unchanged
canonical main. No runner code or that test was changed.

The existing local CPU SSE worker encoded 124 unique current heading/meaning
pairs into 376 rows, including four standalone-heading controls. All controls
match the current native vectors to cosine greater than 0.9999999999999 and
maximum normalized error below 0.000000041. Checkpoint/model identity, source
hashes and worker request/receipt bindings pass. These are auxiliary encodings,
not source-post masks or newly generated subjects.

Ignored artifacts are in the retained research worktree
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1`,
under `target/candidate-ranking-as100-v1/`. They include `meaning-vectors`,
`screen-v1.json`, `root-child-union-v1.json` and `regressions/`. Hash-exact source
snapshots preserve the two earlier research versions. Final accounting is in
`regressions/root-child-union-final.json`; earlier cost reports are superseded.

Repeat the passing selection with a fresh output path:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  ../oracle-mvp-scalable-hierarchy-v12/target/sh3-worker-env/bin/python \
  sse_multivector/selection_regressions.py evaluate \
  --suite target/selection-regressions-v2/as100-fifty/suite-v2.json \
  --selection-report target/candidate-ranking-as100-v1/root-child-union-v1.json \
  --profile root_baseline_meaning_union-16 \
  --output target/candidate-ranking-as100-v1/regressions/root-child-union-repeat.json
```

This tests removal within the original nomination pool; it cannot establish
recovery of useful nodes outside that pool. All cases are visible development
data. The next useful check is this same fixed rule on another independently
generated, current-ASv6.100 construction before production adoption.
