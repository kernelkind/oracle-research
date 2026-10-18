# Hierarchy parameters and review commands

Open a run with its command below in an interactive terminal. Press `N` for
original notes. Parameters describe the settings actually used.

## Inputs and prompts

| Run | Notes | Subjects | Generator | Bootstrap | Consolidation | Compare |
| --- | ---: | --- | --- | --- | --- | --- |
| HR03 | 50 | ASv6.100 | Staged / guarded16 | bootstrap-v96 | — | compare-v48 |
| HR04 | 12 | ASv6.100 | traversal-v24 | bootstrap-v109 | consolidation-v4 | compare-v179 |
| HR05 | 24 | ASv6.100 | traversal-v24 | bootstrap-v109 | consolidation-v4 | compare-v179 |
| HR06 | 8 | ASv6.48 | Staged / guarded16 | bootstrap-v88 | — | compare-v36 |
| HR07 | 50 | ASv6.48 | Staged / guarded16 | bootstrap-v96 | — | compare-v48 |
| HR08 | 24 | ASv6.100 | V2 | bootstrap-v109 | consolidation-v4 | compare-v179 |
| HR09 | 24 | ASv6.100 | V2 | bootstrap-v122 | consolidation-v18 | compare-v192 |
| HR10 | 50 | ASv6.100 | V2 | bootstrap-v122 | consolidation-v18 | compare-v192 |
| HR11 | 6 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v6 | — |
| HR12 | 12 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v6 | — |
| HR13 | 24 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v6 | — |
| HR14 | 50 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v6 | — |
| HR15 | 24 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v7 | — |
| HR16 | 50 | ASv6.100 | V3 | bootstrap-v129 | pair-consolidation-v7 | — |
| HR17 | 24 | ASv6.100 | V3.1 | bootstrap-v129 | pair-consolidation-v7 | — |
| HR18 | 24 | ASv6.100 | V3.2 | bootstrap-v133 | pair-consolidation-v11 | — |
| HR19 | 50 | ASv6.100 | V3.1 | bootstrap-v129 | pair-consolidation-v7 | — |
| HR20 | 50 | ASv6.100 | V3.2 | bootstrap-v133 | pair-consolidation-v11 | — |
| HR21 | 50 | ASv6.100 | V4.1 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR22 | 100 | ASv6.100 | V4.1 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR23 | 100 | ASv6.100 | V4.2 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR24 | 100 | ASv6.100 | V4.3 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR25 | 100 | ASv6.100 | V4.4 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR26 | 200 | ASv6.100 | V4.1 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR27 | 50 | ASv6.100 | V5 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR28 | 100 | ASv6.100 | V5 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR29 | 200 | ASv6.100 | V5 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR30 | 1,000 | ASv6.100 | V5 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR31 | 100 | ASv6.100 | V5.1 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR32 | 200 | ASv6.100 | V5.1 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR33 | 200 | ASv6.100 | V5.2 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR34 | 200 | ASv6.100 | V5.3 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR35 | 1,000 | ASv6.100 | V5.3 | bootstrap-v133 | consolidated-grouped-v1 | — |
| HR36 | 1,000 | ASv6.100 | V5.3 | bootstrap-v133 | consolidated-grouped-v1 | — |

**Same notes:** HR03/HR10/HR14/HR16/HR19/HR20/HR21/HR27 use the same ordered 50-note selection.
HR05/HR08/HR09/HR13/HR15/HR17/HR18 use its same ordered first 24 notes. HR04 uses
its first 12; HR11 and HR12 use selected 6- and 12-note subsets of the 24,
so HR12's set differs from HR04's. HR06/HR07 use older ASv6.48 inputs and are
**deprecated historical runs**.

HR22 keeps that same 50-note set first and appends the remaining 50 frozen
collection notes. All 326 original Bootstrap titles and meanings match HR20.
HR23 uses HR22’s exact ordered 100 notes, all 733 saved Bootstrap answers and
original vectors. HR24 and HR25 reuse that same frozen corpus, all Bootstrap
answers and vectors, changing only their two explicitly recorded HDBSCAN
parameters.

HR33 uses HR32's exact ordered 200-note corpus, saved Bootstrap meanings and
vectors, changing section ranking to V5.2 at every level. HR34 reuses that
same corpus and saved meanings/vectors with V5.3 membership expansion.

**Selection and stopping:**

- Traversal-v24: stop at individual note access, single-note leaves and strictly
  narrowing edges; six siblings is a consolidation trigger.
- V2: uses **PPv35-post-meaning-v1**; original L1 guarantee threshold 50,
  falling back to the highest valid score per note. No deeper prominence cutoff;
  six browsing choices is a soft target.
- V3: Bootstrap all original L1s; descending cosine pairs within each family,
  with no cutoff. Carry odd leftovers. Restart children from their parent's
  original L1s. Hard maximum six siblings; stop expansion at two distinct notes.
- V3.1: same family construction, with cutoff **0.66 → 0.53 → 0.465 → … toward
  0.40**, reset per family. Discard both entries in rejected pairs; retain odd
  leftovers. Notes can disappear. **HR17 retains 19/24 notes in 25 nodes.**
- V3.2: same cutoff and construction as V3.1; use Bootstrap-v133's generated
  titles in SSE, consolidation inputs and browsing. Preserve original AS subjects
  separately. **HR18 retains 19/24 notes in 20 nodes.**
- V4.1: one HDBSCAN tree, **min_samples=3, min_cluster_size=2, excess-of-mass**,
  angular distance and no cosine cutoff. Cut selected-group ancestors into at
  most six choices per level. Name groups and broader sections bottom-up;
  generated meanings are never reclustered. Stop at original groups, exposing
  notes directly. **HR21: 31 nodes, 46/50 notes. HR22: 80 nodes, 94/100 notes.
  Both have six roots.**
- V4.2: same construction as V4.1, with **min_cluster_size=4**.
  **HR23: 53 nodes, six roots and 93/100 notes.**
- V4.3: same construction, **min_samples=4, min_cluster_size=2**.
  **HR24: 60 nodes, six roots and 94/100 notes.**
- V4.4: same construction, **min_samples=4, min_cluster_size=4**.
  **HR25: 52 nodes, six roots and 90/100 notes.**
- V5: same original HDBSCAN parameters as V4.1. Choose a positive bend among
  the middle 80% of merge distances, select the largest sections by distinct
  notes, generate group definitions before section definitions, and recluster
  synthetic representatives. Amend existing nodes; build fresh trees for their
  children. Stop at groups; retain unclaimed eligible notes directly on the
  parent. Originally unassigned entries remain excluded.
  **HR27: 22 nodes, 46/50 notes; HR28: 52 nodes, 94/100 notes; HR29: 66 nodes,
  198/200 notes.** Reachability includes direct top-level notes.
- V5.1: V5's construction with all non-null original entries retained for
  subsequent root rounds, including those initially left unassigned. It was the
  default for new definitions until V5.2. Roots-only chat iterations on the HR27 and
  HR28 corpora covered 50/50 and 100/100 notes under actual roots, respectively;
  they are not new official HR runs or semantic approval. Full construction
  remains recursive. HR31 completed with 72 nodes and 100/100 notes beneath
  its six actual roots. HR32 completed with 70 nodes; its original export
  exposed 200 notes. New exports show only the 176 beneath roots, hiding 24
  unclaimed top-only notes. Top-container access does not establish root coverage.
- V5.2: V5.1's construction, ranking sections at every level by distinct notes
  not already covered by existing siblings in that lineup. Saved section order
  breaks ties. This was the default for new definitions until V5.3. HR33 completed with
  67 nodes and 189/200 notes beneath roots; 15 gained placement and two lost it
  compared with HR32. Native validation and the review UI check passed.
- V5.3: V5.2 plus an additional HDBSCAN membership pass after each completed
  sibling lineup, including non-roots. Each sibling's original entries are
  clustered with the same frozen global untracked pool. Shared groups add
  untracked entries to that sibling; existing memberships, meanings and native
  producer evidence stay unchanged. New definitions default to V5.3. HR34
  completed with 68 nodes and 199/200 notes beneath roots, versus HR33's 189.
  A new Beverages and drinking membership has a scope mismatch; coverage does
  not establish semantic quality.
- HR14/HR16 omit two null Bootstrap meanings. HR17 had none. Answers and receipts
  remain saved; the original selected note set is preserved as input evidence.

## Model, limits and code

**Model:** all listed runs use **openai-codex / gpt-6.1-sol / medium / SSE**.
**Timeouts:** Bootstrap 600s; consolidation 1,800s. Compare uses 600s for
HR03/HR06/HR07 and 1,800s for traversal/V2. V2 prominence uses 600s.

**Encoder:** V3/V3.1 use the same SSE checkpoint as HR15, sentence-T5-base,
CPU, 768 dimensions, batch 8, **512-token maximum**. Pool the original AS
subject with its Bootstrap meaning as unselected context. V3.2/V4.1–V4.4 use the same
encoder and limits, pooling the generated title instead. V4.1–V4.4 encode only
original Bootstrap entries. V5 also encodes newly generated representatives
using the same title-only pooling with their meaning as context. HR03/HR06/HR07 used
standalone subject vectors, also with a 512-token maximum. Traversal/V2 did not
use SSE for hierarchy construction.

**Execution:** HR11–HR32 use prefix caching, automatic warming and exact-request
answer reuse. Seed/temperature are unspecified; no explicit output-token cap.
The earlier runs used at most two provider attempts per case across resumes;
HR14 and HR30 had approved recovery exceptions. The autonomous HR30 continuation
has no attempt cap and uses one-hour Bootstrap/consolidation deadlines. HR31
and HR32 also use one-hour new-request deadlines without a per-case attempt
maximum override; copied Bootstrap receipts retain their original settings. HR22 used a
scoped replacement checkpoint for one invalid evidence quote, preserving the
strict validator and original prompts.

Call caps include warmups, retries and resumes. Older caps below are historical;
HR15 onward have no cap. Git arrows show initial → continuation commits.
Unknown means the execution commit was not recorded.

| Run | Call cap | Generator Git | Runner Git |
| --- | ---: | --- | --- |
| HR03 | Unknown | Unknown | Unknown |
| HR04 | 500 | 17ea0b74 | e19592f9 |
| HR05 | 500 | 251cf0ed | e19592f9 |
| HR06 | 20,000 shared | Unknown | Unknown |
| HR07 | 20,000 shared | Unknown | Unknown |
| HR08 | 3,000 | 1a7f68a3 → 542d5697 | e19592f9 |
| HR09 | 3,000 | 1a7f68a3 → 542d5697 | e19592f9 |
| HR10 | 10,000 | 1a7f68a3 → 542d5697 | e19592f9 |
| HR11 | 1,000 | d4c55c13 | b03251cc |
| HR12 | 3,000 | d4c55c13 | b03251cc |
| HR13 | 5,000 | d4c55c13 | b03251cc |
| HR14 | 10,000 | d4c55c13 → c607d6fb | b03251cc → ef3e6828 |
| HR15 | None | dbd03c02 | 9d956b3a |
| HR16 | None | dbd03c02 → fb6f6154 | 9d956b3a |
| HR17 | None | bdc22432 | 9d956b3a |
| HR18 | None | 48e71c71 | 9d956b3a |
| HR19 | None | 5446454d | 9d956b3a |
| HR20 | None | 48e71c71 → 273e16e1 | 9d956b3a |
| HR21 | None | f5500b02 | e7dd09fa |
| HR22 | None | 581132e9 | e7dd09fa |
| HR23 | None | df96b21c | e7dd09fa |

## Calls, tokens and API cost

These are **new-call** totals for hierarchy construction, including warmups and
retries. Reused answers are counted separately. Tokens = uncached input + cached
input + output; reasoning is already included in output. API cost is the saved
API-equivalent estimate, rather than a subscription invoice. With missing usage,
tokens and cost are known subtotals; the complete totals remain unknown.

| Run | New calls | Reused answers | Known tokens | API-equivalent cost | Calls missing usage/cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| HR03 | 2,183 | 538 | 5,279,012 | $6.2906 | 12 |
| HR04 | 153 | 0 | 445,965 | $0.7431 | 1 |
| HR05 | 459 | 0 | 1,226,176 | $2.1243 | 3 |
| HR06 | 153 | 7 | 374,939 | $0.9077 | 0 |
| HR07 | 3,085 | 201 | 7,523,324 | $9.1301 | 7 |
| HR08 | 2,603 | 1 | 6,537,102 | $12.8365 | 28 |
| HR09 | 2,646 | 0 | 7,170,506 | $14.1764 | 10 |
| HR10 | 4,088 | 762 | 10,824,142 | $21.0439 | 45 |
| HR11 | 67 | 0 | 241,959 | $0.4186 | 0 |
| HR12 | 152 | 40 | 435,478 | $0.8358 | 0 |
| HR13 | 421 | 86 | 1,073,429 | $2.0719 | 0 |
| HR14 | 1,030 | 181 | 2,507,864 | $5.2233 | 6 |
| HR15 | 334 | 169 | 611,130 | $1.3505 | 1 |
| HR16 | 864 | 417 | 1,538,725 | $3.3941 | 51 |
| HR17 | 25 | 193 | 43,585 | $0.0856 | 0 |
| HR18 | 218 | 0 | 1,050,026 | $1.4479 | 3 |
| HR19 | 54 | 432 | 95,792 | $0.2132 | 0 |
| HR20 | 327 | 167 | 1,355,596 | $1.8697 | 5 |
| HR21 | 10 | 25 + 326 Bootstrap | 20,183 | $0.0450 | 0 |
| HR22 | 512 | 1,050 events across checkpoints | 2,760,036 | $3.8414 | 4 |
| HR23 | 20 | 39 + 733 Bootstrap | 44,303 | $0.1147 | 0 |

HR18's tokens and cost are known subtotals: three recovered provider attempts
lack reported usage. HR20 has five recovered attempts without reported usage.
Both rows are known subtotals; complete tokens and API-equivalent costs remain
unknown. HR20's final row includes Bootstrap and consolidation across its resume.

HR17's new calls took **1m 45s**. Including the saved original producers behind
its reused answers, its construction used **226 calls, 1,039,228 tokens and
$1.4236 API-equivalent cost**. Shared producers must be deduplicated when adding
costs across runs.

## Review commands

## HR03 — 50 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr14-v3/target/hr14-review-ui-v2/sse-subject-navigation \
  --categories ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/review-ui-v1/hierarchy.json \
  ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-as100-b96-c48-fifty-note-v1/review-ui-v1/notes.json
```

## HR04 — 12 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr14-v3/target/hr14-review-ui-v2/sse-subject-navigation \
  --categories ./oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hr04-review-ui-v1/hierarchy.json \
  ./oracle-mvp-hierarchy-hr04-twelve-note-v1/target/hr04-review-ui-v1/notes.json
```

## HR05 — 24 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr05-twenty-four-note-v1/target/hr05-review-ui-v1/launch.sh
```

## HR06 — 8 notes · historical, deprecated ASv6.48

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr14-v3/target/hr14-review-ui-v2/sse-subject-navigation \
  --categories ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-v88-eight-note-review-v1/hierarchy.json \
  ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-v88-eight-note-review-v1/notes.json
```

## HR07 — 50 notes · historical, deprecated ASv6.48

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr14-v3/target/hr14-review-ui-v2/sse-subject-navigation \
  --categories ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-b96-c48-fifty-note-v1/review-ui-v1/hierarchy.json \
  ./oracle-mvp-hierarchy-bootstrap-v88-three-note-v1/target/hierarchy-b96-c48-fifty-note-v1/review-ui-v1/notes.json
```

## HR08 — 24 notes · partial

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr08-v2/target/hr08-review-ui-v1/launch.sh
```

## HR09 — 24 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr09-v2/target/hr09-review-ui-v1/launch.sh
```

## HR10 — 50 notes · stopped

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr10-v2/target/hr10-resumed-review-ui-v1/launch.sh
```

## HR11 — 6 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr11-v3/target/hr11-review-ui-v1/launch.sh
```

## HR12 — 12 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr12-v3/target/hr12-review-ui-v1/launch.sh
```

## HR13 — 24 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr13-v3/target/hr13-review-ui-v1/launch.sh
```

## HR14 — 50 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr14-v3/target/hr14-review-ui-v2/launch.sh
```

## HR15 — 24 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr15-v3/target/hr15-review-ui-v1/launch.sh
```

## HR16 — 50 notes

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr16-v3/target/hr16-review-ui-v1/launch.sh
```

## HR17 — 24 input notes · 19 retained

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr17-v31/target/hr17-review-ui-v1/launch.sh
```

## HR19 — 50 input notes · 35 retained

Same controls and generator Python sources as HR17, with the original 50-note
selection. Complete: **63 nodes, three roots, 35/50 notes**, in **9m 45s**.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr19-v31/target/hr19-review-ui-v1/launch.sh
```

## HR18 — 24 input notes · 19 retained

HiGen V3.2 with Bootstrap-v133 titles and Pair-consolidation-v11. Complete:
**20 nodes, four roots, 19/24 notes**, in **10m 06s**.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr18-v32/target/hr18-review-ui-v1/launch.sh
```

## HR20 — 50 input notes · 30 retained

Same controls as HR18, with the approved Bootstrap quote-space validation fix.
Complete: **58 nodes, three roots, 30/50 notes**. **8m 59s active execution**;
29m 06s elapsed including the validation stop. Four null Bootstrap meanings
were skipped with evidence retained. Revalidation used saved answers unchanged.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr20-v32/target/hr20-review-ui-v1/launch.sh
```

## HR21 — 50 notes · HiGen V4.1

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr21-v41/target/hr21-review-ui-v1/launch.sh
```

Completed in **8m 39s**. Ten new calls comprise six section answers and four
warmups; all 25 original group answers and 326 Bootstrap answers were reused.
New usage is 6,928 uncached input, 10,240 cached input and 3,015 output tokens
(including 1,849 reasoning). Historical producer-inclusive cost is a known
subtotal of **$2.6688**, with four historical calls missing usage; the complete
producer-inclusive total remains unknown. Null meanings and 183 unassigned
entries remain recorded as evidence; four selected notes are absent.

## HR22 — 100 notes · HiGen V4.1

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr22-v41/target/hr22-review-ui-v1/launch.sh
```

Completed in **1h 31m 53s**, including subject generation and recovery.
Construction used **512 new calls** and **729 final Bootstrap reuses**; the
initial generation also recorded 321 reuses. The 1,050 reuse events count both
checkpoints, rather than distinct original producers. All 80 section answers
are valid. Five null meanings and 361 unassigned entries remain as evidence.

The additional 50 ASv6.100 notes required **52 new calls**, 547,933 known tokens
and **$1.0014** known API-equivalent cost. Including those calls and every
recovery attempt, HR22 used **564 new calls, 3,307,969 known tokens and $4.8428**
known API-equivalent cost. Five provider attempts lack usage; complete totals
remain unknown. Historical Bootstrap producers are separate: the native
producer-inclusive known subtotal is **$7.3450**, excluding original 50-note
AS generation, with nine calls missing usage.

Recovery preserved all 326 HR20 Bootstrap answers after five were initially
regenerated. One malformed evidence quote was replaced using the same prompt;
three other additional-note answers were regenerated after cache misses.
Every initial response and extra call is retained and included in accounting.
Prompts, model, encoder, clustering and stopping settings were unchanged.

## HR23 — 100 notes · HiGen V4.2

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr23-v42/target/hr23-review-ui-v1/launch.sh
```

Completed in **7m 55s**: 53 nodes, six roots, 42 original groups and 93/100 notes.
Same controls and exact Bootstrap answers/vectors as HR22; HDBSCAN minimum
cluster size changes from two to four. Bootstrap-v133, Consolidated-grouped-v1,
GPT-6.1 Sol medium, 600s/1,800s teacher timeouts, 512-token encoder limit,
no cosine cutoff and no call cap.

**20 new calls** comprise 14 section answers and six warmups; 39 group answers
and all 733 Bootstrap answers were reused. No new AS, Bootstrap or encoder work.
New usage: 17,279 uncached input, 19,200 cached input and 7,824 output tokens
(including 5,060 reasoning), with complete usage and no failures/retries.
New API-equivalent cost: **$0.114718**. Historical hierarchy producers have a
known subtotal of **$6.0894**, with four historical attempts missing usage;
original subject generation is excluded.

Saved-input reuse now accepts validated V4.1/V4.2 checkpoints with matching
inputs and controls. HR22’s frozen runner was retained for the comparison.
Five null meanings and 393 unassigned entries remain recorded as evidence;
seven input notes are absent. Structural validation and the review UI check
passed; human semantic review is pending.

## HR24 — 100 notes · HiGen V4.3

Completed: 60 nodes, 46 original groups,
six roots and 94/100 represented notes. Recorded run interval:
504.5 seconds. Maximum leaf depth is
7 category selections, with at most six choices per section.
The exact ordered HR23 corpus, all 733 Bootstrap answers, original vectors,
prompts, teacher settings, encoder controls and frozen shared runner e7dd09fa
are unchanged. HDBSCAN uses min_samples=4 and min_cluster_size=2.
The generation source is e498cda9. No new AS, Bootstrap or encoder calls occurred.

Native accounting: **32 new attempts**, comprising 25 definitions
and 7 warmups; **35 exact definition answers reused**.
No failures, retries or missing usage. New API-equivalent catalog cost:
**$0.1738776**; subscription incremental cash charge is zero.
Accounting includes all input/cache/output token types and includes reasoning
within output. Reuse is not a matched policy-savings claim.

Native receipt/state validation passed. The browsing hierarchy has not received
human semantic approval. The review UI passed its checks from `/tmp`, preserving
60 canonical nodes, six roots and 94 represented original notes. Its checked
viewer, export provenance and launcher are saved together.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr24-v43/target/hr24-review-ui-v1/launch.sh
```

Saved state: `/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr24-v43/target/hierarchy-hr24-v43-hundred-note-v1/HR24/state.json`.
Measured structure and controls: `structural-measurements.json` and
`baseline-control-validation.json` in the same artifact root. Native
`usage-new.json` and `execution-provenance.json` preserve usage and timing.
Reusable definition: `sse_multivector/hierarchy-runs/hr24/hierarchy.spec.json`.
Retain the isolated run worktree for its frozen source bindings and evidence.

## HR25 — 100 notes · HiGen V4.4

Completed: 52 nodes, 39 original groups,
six roots and 90/100 represented notes. Recorded run interval:
461.9 seconds. Maximum leaf depth is
6 category selections, with at most six choices per section.
The exact ordered HR23 corpus, all 733 Bootstrap answers, original vectors,
prompts, teacher settings, encoder controls and frozen shared runner e7dd09fa
are unchanged. HDBSCAN uses min_samples=4 and min_cluster_size=4.
The generation source is e498cda9. No new AS, Bootstrap or encoder calls occurred.

Native accounting: **17 new attempts**, comprising 11 definitions
and 6 warmups; **41 exact definition answers reused**.
No failures, retries or missing usage. New API-equivalent catalog cost:
**$0.0913840**; subscription incremental cash charge is zero.
Accounting includes all input/cache/output token types and includes reasoning
within output. Reuse is not a matched policy-savings claim.

Native receipt/state validation passed. The browsing hierarchy has not received
human semantic approval. The review UI passed its checks from `/tmp`, preserving
52 canonical nodes, six roots and 90 represented original notes. Its checked
viewer, export provenance and launcher are saved together.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr25-v44/target/hr25-review-ui-v1/launch.sh
```

Saved state: `/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr25-v44/target/hierarchy-hr25-v44-hundred-note-v1/HR25/state.json`.
Measured structure and controls: `structural-measurements.json` and
`baseline-control-validation.json` in the same artifact root. Native
`usage-new.json` and `execution-provenance.json` preserve usage and timing.
Reusable definition: `sse_multivector/hierarchy-runs/hr25/hierarchy.spec.json`.
Retain the isolated run worktree for its frozen source bindings and evidence.

## HR26 — 200 notes · HiGen V4.1

Completed: **192 nodes, 151 original groups, six roots and 198/200 notes**.
Maximum leaf depth is 16 category selections, with at most six choices per
section. Native state/receipt validation and the standalone review UI check
passed. Human semantic review is pending.

Exact historical raw input: HR25’s ordered 100 food/drink notes followed by
100 frozen music notes. All 100 food ASv6.100 subject trees and 733
Bootstrap-v133 answers reused. Music uses 100 fresh ASv6.100 subject trees.
The combined corpus has 1,527 original L1s; seven null meanings are preserved
and omitted. All 1,516 unique original title/meaning vectors were encoded once.

Bootstrap-v133 and consolidated-grouped-v1; HDBSCAN min_samples=3,
min_cluster_size=2, excess_of_mass and angular distance. No cosine cutoff,
local L2 refinement or encoding/reclustering generated section meanings.
Original HDBSCAN groups expose notes directly.

Recovery preserves the original Songs answer, flagging its invalid diagnostic
quote without blocking its meaning/title. The overloaded provider case
recovered on attempt three. The user approved temporary-provider retries until
recovery without the initial two-attempt limit. Original settings, answers and
receipts remain preserved; source/limit changes are audited separately.

Native accounting: **1,102 new attempts**, including warmups and failed calls;
740 exact reuses (733 Bootstrap and seven grouped consolidation).
Four failed attempts lack usage. Known API-equivalent cost: **$9.8172116**;
complete cost is unknown. Known token subtotals: 789,037 input; 4,891,776 cached
input; 774,996 output, including 201,379 reasoning. Incremental subscription
cash charge is zero. Original food subject-generation costs are excluded.

The resumed constructor interval was 1169.0 seconds. The full recorded interval
includes the initial AS/Bootstrap pass, the blocked interval and code recovery;
use the saved phase timestamps when comparing runtimes.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr26-v41/target/hr26-review-ui-v1/launch.sh
```

Initial generator: `b1b1118e0be6a01b0c621206a398b5308879e92a`;
recovery constructor: `e66eb182832ec689e13f6f79c95aec4ae9a8017f`;
shared runner: `1cfdd6a76a9910b2c9dea0ca395f825b90485f7e`.
The viewer exporter uses `eb30aa68`; its source is retained with the review UI.
Saved state: `oracle-mvp-hierarchy-hr26-v41/target/hierarchy-hr26-v41-two-hundred-note-v1/HR26/state.json`.
Native accounting: `usage-new-complete.json`; structure and timing:
`structural-measurements.json` and `execution-provenance.json` in the same
artifact root. The blocked snapshot and recovery authorization remain saved.
Reusable definition: `sse_multivector/hierarchy-runs/hr26/hierarchy.spec.json`.
Retain the original run, recovery-source and shared-runner worktrees for frozen
bindings, artifacts and reproducibility.

## HR27 — 50 notes · HiGen V5

HR21's exact corpus, original Bootstrap-v133 answers, encoder receipts and
teacher settings; only generation policy changed. Complete in 3m 19s: 22 nodes,
four roots and 46/50 reachable notes, including three available only directly
at the top. Structural validation passed; semantic quality remains for review.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr27-v5/target/hr27-review-ui-v1/launch.sh
```

## HR28 — 100 notes · HiGen V5

HR22's exact ordered corpus, original meanings/vectors and teacher controls.
Complete in 19m 26s: 52 canonical nodes, six roots and 94/100 reachable notes,
including seven available only directly at the top. Native validation passed.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr28-v5/target/hr28-review-ui-v1/launch.sh
```

[Full result and evidence](hierarchy-runs.md#hr28--hr22-controls-with-higen-v5).

## HR29 — 200 notes · HiGen V5

HR26's exact ordered corpus, original meanings/vectors and teacher controls;
ordinary two-attempt provider limit. Complete in 24m 32s: 66 canonical nodes,
six roots and 198/200 reachable notes, including 21 available only directly
at the top. Native validation passed.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr29-v5/target/hr29-review-ui-v1/launch.sh
```

[Full result and evidence](hierarchy-runs.md#hr29--hr26-controls-with-higen-v5).

## HR30 — 1,000 notes · HiGen V5

Running after user-authorized recovery of one local 600-second timeout.
All 7,036 Bootstrap answers are available and valid; native V5 construction
has resumed from the completed producer, with the original failed receipt
preserved. New request deadlines are one hour. The valid unresolved topic in
the `#2100Rocks` post is skipped and its note omission is reported.
There is no review UI yet.

[Current state and evidence](hierarchy-runs.md#hr30--approved-1000-note-higen-v5-experiment).

## HR31 — 100 notes · HiGen V5.1

HR28's exact ordered corpus and saved Bootstrap-v133 meanings; unchanged
Consolidated-grouped-v1 and encoder controls. Complete in 10m 54s of native
execution: 72 canonical nodes, six roots, at most six children per node and four
canonical levels. All 100 notes occur beneath actual roots; none relies only on
the top container. Full recursive construction and the offline UI check passed.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr31-v51/target/hr31-review-ui-v1/launch.sh
```

Press L on a leaf to show its notes.
[Full result and evidence](hierarchy-runs.md#hr31--hr28-corpus-with-higen-v51).

## HR32 — 200 notes · HiGen V5.1

HR29's exact ordered corpus and saved Bootstrap-v133 meanings/vectors; unchanged
Consolidated-grouped-v1 and numerical controls. Complete in 15m 24s: 70 canonical
nodes, six roots, at most six canonical children and five canonical levels.
The current review export shows the 176 notes beneath roots. The 24 top-only
notes remain in saved construction evidence and are hidden by the review UI.
All 70 canonical nodes, meanings and memberships match the original export.
Native validation and the updated UI check passed. Root placement and semantic
quality remain for review.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-root-container-notes-v1/target/hr32-root-container-review-v1/launch.sh
```

Press L on a leaf to show its notes.
[Full result and evidence](hierarchy-runs.md#hr32--hr29-corpus-with-higen-v51).

## HR33 — 200 notes · HiGen V5.2

HR32's exact ordered corpus, prompts, Bootstrap meanings and saved vectors.
Sections rank by notes not already covered by existing siblings at every level.
Complete: 67 canonical nodes, six roots, at most six children and five levels.
The UI shows 189 notes beneath roots; 11 unclaimed notes stay in saved evidence.
Compared with HR32, 15 gained root placement and two lost it. All 14 lineups
finished, all 61 edges strictly narrow note sets, and native/UI checks passed.
Semantic quality remains for review.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr33-v52/target/hr33-review-ui-v1/launch.sh
```

Press L on a leaf to show its notes.
[Full result and evidence](hierarchy-runs.md#hr33--hr32-corpus-with-higen-v52).

## HR34 — 200 notes · HiGen V5.3

Complete on HR33's exact corpus and saved Bootstrap meanings/vectors: 68 nodes,
six roots, at most six children and five levels. All 62 edges narrow observed
note sets. Root coverage is 199/200, gaining ten notes and losing none against
HR33. Fourteen completed lineups each received the new global-untracked
membership pass. Native validation passed after a checkpoint validator fix.
Bodily reduction of consumed substances joined Beverages and drinking;
this agent-assessed scope mismatch remains for review. No manual repair.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr34-v53/target/hr34-review-ui-v1/launch.sh
```

Press L on a leaf to show its notes. The offline viewer check passed: 68
canonical nodes plus the display container, 199 notes, and no direct notes
above the roots.
[Full result and evidence](hierarchy-runs.md#hr34--hr33-corpus-with-higen-v53).

## HR35 — 1,000 notes · HiGen V5.3

Construction completed on HR30's exact corpus using its saved Bootstrap
meanings and vectors: 169 nodes, six roots, at most six children and four levels.
All 163 edges narrow observed note sets. Root coverage is 718/1,000, gaining
148 notes and losing 12 against HR30; semantic review remains pending.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr35-v53/target/hr35-review-ui-v1/launch.sh
```

Press L on a leaf to show its notes. The review contains 169 canonical nodes
plus the display container and 718 original notes, with no direct notes above
the roots. The offline viewer check passed; all 128 leaves have notes. The saved
hierarchy and its meanings remain unchanged.
[Current state and controls](hierarchy-runs.md#hr35--hr30-thousand-note-corpus-with-higen-v53).

## HR36 — 1,000 automatically sampled notes · HiGen V5.3

Complete: **71 nodes, six roots and 683/1,000 notes beneath roots**; 317
inputs remain outside them. The input inventory includes 61 posts with empty
ASv6.100 subject lists. All 65 edges narrow observed note sets; every sibling
lineup finishes within six choices. The offline review-UI check passed.

The corpus is a fixed-seed automatic sample (`hr36-corpus-v1`) from the frozen
English-eligible pool, without manual reviews, topic quotas or author balancing.
Bootstrap-v133 and Consolidated-grouped-v1 are fixed. Semantic review is pending.

```bash
cd /home/dev/src/notedeck_worktrees/algos
./oracle-mvp-hierarchy-hr36-v53-auto/target/hr36-review-ui-v1/launch.sh
```

[Input, code and accounting record](hierarchy-runs.md#hr36--automatically-sampled-1000-note-higen-v53).

## HR37 — 1,000 automatically sampled notes · HiGen V5.3

ASv6.100 complete; Bootstrap and construction running. ASv6.100, Bootstrap-v133 and Consolidated-grouped-v1. Review command unavailable until the hierarchy completes.

## HR38 — 2,000 automatically sampled notes · HiGen V5.3

ASv6.100 complete; Bootstrap and construction running. ASv6.100, Bootstrap-v133 and Consolidated-grouped-v1. Review command unavailable until the hierarchy completes.
