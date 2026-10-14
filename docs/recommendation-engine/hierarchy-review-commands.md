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
| HR19 | 50 | ASv6.100 | V3.1 | bootstrap-v129 | pair-consolidation-v7 | — |

**Same notes:** HR03/HR10/HR14/HR16/HR19 use the same ordered 50-note selection.
HR05/HR08/HR09/HR13/HR15/HR17 use its same ordered first 24 notes. HR04 uses
its first 12; HR11 and HR12 use selected 6- and 12-note subsets of the 24,
so HR12's set differs from HR04's. HR06/HR07 use older ASv6.48 inputs and are
**deprecated historical runs**.

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
- HR14/HR16 omit two null Bootstrap meanings. HR17 had none. Answers and receipts
  remain saved; the original selected note set is preserved as input evidence.

## Model, limits and code

**Model:** all listed runs use **openai-codex / gpt-6.1-sol / medium / SSE**.
**Timeouts:** Bootstrap 600s; consolidation 1,800s. Compare uses 600s for
HR03/HR06/HR07 and 1,800s for traversal/V2. V2 prominence uses 600s.

**Encoder:** V3/V3.1 use the same SSE checkpoint as HR15, sentence-T5-base,
CPU, 768 dimensions, batch 8, **512-token maximum**. Pool the original AS
subject with its Bootstrap meaning as unselected context. HR03/HR06/HR07 used
standalone subject vectors, also with a 512-token maximum. Traversal/V2 did not
use SSE for hierarchy construction.

**Execution:** HR11–HR17 use prefix caching, automatic warming and exact-request
answer reuse. Seed/temperature are unspecified; no explicit output-token cap.
Normally at most two provider attempts per case across resumes, temporary
provider errors only; HR14 had an approved recovery exception.

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
| HR19 | None | 5446454d | 9d956b3a |

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
| HR19 | 54 | 432 | 95,792 | $0.2132 | 0 |

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
