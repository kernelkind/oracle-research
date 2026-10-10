# Repeatable candidate-selection tests

The completed ASv6.100 build is now a separate [current-source suite](selection-regressions-v2.md),
with another 120 placement cases. Use that suite for current-pipeline selection
work; retain this one as clearly labeled historical evidence.

**Prepared:** `selection-historical-fifty-v1`, 177 comparison-bearing placement
cases across 50 notes. The source construction has 181 local entries; its initial
bootstrap and three producer-review holds require no selection and remain fixed.
The cases include 145 additions, sixteen equivalences and sixteen holds.

**Status:** historical ASv6.48 evidence, deprecated for current-pipeline validation.
Expected relationships come from validated native saved construction, **not
human semantic gold**. None of these 177 expectations is labeled human-reviewed.
The user authorized preparing repeatable tests; that does not approve every old
model answer. No teacher/provider calls or new encodings were made.

## What stays fixed

Each case identifies the incoming **local node**, its established meaning and
original post/ancestor evidence, the existing **canonical hierarchy**, and the
saved comparison answers. These remain in their original native sources, linked
by absolute paths, SHA-256 hashes and the original step index. The suite stores
expected outcomes separately from ranking inputs. Changing a protected source
refuses evaluation; old receipts are never edited.

Do not train or tune against a supposedly held-out test's answers. This first
suite is visible development data; it is not an independent final test. Unknown
comparisons remain unresolved and cannot be filled with `neither` or guessed
costs. More cases can be frozen through the same code when qualifying current
ASv6.100 constructions become available.

## What the tests measure

1. **Each case separately:** run the native placement and implication checks
   against that case's original graph and history. Check whether the resulting
   graph preserves the old local node's relationships to existing nodes, including
   equivalence, parent and child relationships. Ancestor routes count: placing
   Breakfast beneath Meals can retain its Food relationship without a direct
   Food edge. Extra relationships or different redundant edges do not by
   themselves fail this measurement. This is historical relationship preservation,
   not a claim that all old relationships are needed for a good final hierarchy.
2. **Construction in order:** retain only answers the selection actually requested
   or verified. Run the native checks again in construction order. This catches
   loss of an earlier negative answer needed to reject a later contradiction.
   Stop at the first graph difference or unavailable required answer; later
   saved model inputs would no longer describe the same construction.
3. **API-equivalent cost:** use native receipt accounting for every retained
   comparison and verification. Keep original meaning-generation and warmup
   costs. Include priced cached/uncached input and output; reasoning is already
   included in output. Preserve failed-attempt/missing-usage counts. These are
   conditional saved-token projections, not freshly measured build savings.

An original hold that becomes an addition is reported as `missed_hold`. An
original addition/equivalence that becomes a hold is `unexpected_hold`: returning
uncertain everywhere cannot pass. Missing historical relationships are reported
with the canonical IDs, so the full node descriptions can be inspected. Different
graphs and unknown answers are reported separately from relationship preservation.

## Focused cases

These are original zero-based construction indices, not new pair IDs. They are
included within the full 177 cases rather than duplicated to increase counts.

| Index | Incoming local node | What it exercises |
|---:|---|---|
| 18 | #coffeechain | Preserving an uncertain comparison hold |
| 49 | Food preparation | Multiple possible equivalences requiring review |
| 65 | Yogurt making | Finding broader preparation topics |
| 66 | Processing rotisserie chickens | Losing Food, its only historical parent |
| 75 | Bread | Finding equivalence while retaining ancestor routes |
| 77 | Meals | Contradiction found during implication verification |
| 81 | Breakfast | Meals provides a route to Food |
| 137 | Eating practices | An earlier negative matters at a later step |
| 159 | Wine in cooking | Original mapped parent and multiple ancestors |
| 180 | Meat eating | Earlier Eating practices / Gamey meat negative prevents admission |

## Native offline checks

| Selection | Cases separately | Construction in order | Projected known total |
|---|---|---|---|
| Original sixteen | 177 matched | All 181 entries match | $9.1301216 |
| Meaning-only twelve | 174 matched, three missed relationships | Stops at entry index 66 | $7.5270844; 17.56% lower |
| Earlier learned twelve, with graph features | 177 matched | Misses the hold at index 180 | $7.5456264; 17.35% lower |
| Learned twelve, graph features removed | 177 matched | All 181 entries match | $7.5400580; 17.42% lower |

Thus a perfect result on isolated cases alone is insufficient. These saved
learned selections are exploratory results from the same historical corpus,
not independent validation or an adopted production policy. Seven original
failed attempts lack usage, so full totals remain unknown. Retrieval/encoding
infrastructure cost and changed future cache behavior are outside these projections.

## Use

[selection_regressions.py](selection_regressions.py) supplies `freeze` and
`evaluate`. It uses the production native readers, placement, contradiction,
implication and cost functions from the frozen reference project; it does not
replace the experiment runner or execute model requests.

Built-in selection accepts `--method meaning --limit 12` (or baseline, heading
and other existing study scores). A new selection implementation can instead
supply `--selection-report FILE`: `state_sha256` plus `steps` containing each
case's `index` and ordered `queried` canonical IDs. Every case must be present
exactly once; IDs must be unique and eligible. Existing study reports are
accepted with `--selection-report FILE --profile NAME`, without rewriting them.
The existing mapped-parent rule is preserved.

Frozen suite and result artifacts are ignored under
`target/selection-regressions-v1/` in
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1`.
They include `suite.json`, `baseline-16.json`, `meaning-12.json`, `learned-12.json`
and `no-graph-12.json`. The task worktree remains because original experiment and
vector provenance uses its absolute paths.

For this historical source, another task has changed its heading-vector reader.
Use the existing read-only archived-reader mount to preserve the frozen source;
do not edit that task's worktree. Example repeated evaluation:

```bash
cd /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-candidate-rankings-v1
env LD_LIBRARY_PATH=/nix/store/1xw5xccqqh1xw3mvd70hyil6x418wxcm-gcc-14.3.0-lib/lib:/nix/store/ri9paa3mri4kqakljak8ldvbcp7lpmif-zlib-1.3.1/lib OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 bwrap \
  --ro-bind / / --dev-bind /dev /dev --proc /proc \
  --bind "$PWD/target" "$PWD/target" \
  --ro-bind "$PWD/target/candidate-ranking-study-v1/frozen-source/subject_matching_probe.py" \
  /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/sse_multivector/subject_matching_probe.py \
  ../oracle-mvp-scalable-hierarchy-v12/target/sh3-worker-env/bin/python \
  sse_multivector/selection_regressions.py evaluate \
  --suite target/selection-regressions-v1/suite.json \
  --method meaning --limit 12 \
  --output target/selection-regressions-v1/meaning-12-repeat.json
```

Outputs are immutable: choose a new path for a repeat. The suite validates its
original sources before every evaluation. Review expected relationships before
promoting any case to semantic gold or claiming end-hierarchy quality.
