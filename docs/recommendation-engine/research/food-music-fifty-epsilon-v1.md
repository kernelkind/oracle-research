# Food/Music 50-note fixed-group epsilon review

Status: completed numerical grouping probe; candidate rule remains experimental.
No production HiGen policy, prompt or canonical hierarchy was changed.

## Inputs and method

Select the first 25 notes in HR21's saved Food order and the first 25 notes in
the saved Music probe's order. These 50 distinct notes retain their ASv6.100
local hierarchies and Bootstrap-v133 titles/meanings. All original L1 entries
are eligible; no prominence selection or deeper local entries are introduced.

Food source:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr21-v41/target/hierarchy-hr21-v41-fifty-note-v1/HR21/state.json`.

Music source:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-music-fifty-epsilon-v1/target/music-fifty-epsilon-v1/numeric-source/state.json`.

The reusable offline review CLI validates both native states, producer and
encoder receipts, exact prompt wording and matching teacher/SSE settings.
It selects original vectors by note, preserving source associations and
preventing collisions between identical local IDs in different sources.
All 355 combined normalized vectors were independently compared with the
original saved HDBSCAN requests and were exactly equal.

Run one new HDBSCAN clustering on the combined original vectors. Prior Food
and Music group memberships are not imported. Settings remain HR21's angular
distance, `min_samples=3`, `min_cluster_size=2`, excess-of-mass selection, and
the same retained production executable. Apply the unchanged
[10%-trimmed bend rule](hr21-epsilon-selection-v1.md) to the resulting fixed
groups' original ancestor tree. No six-section cap or corpus-specific epsilon
adjustment is applied. Section naming and containment judgments are not run.

No new model calls or encodings were required. Existing producer costs are
not claimed as new savings. Incremental paid charges were zero.

## Result

| Measure | Result |
|---|---:|
| Food notes selected | 25 |
| Music notes selected | 25 |
| Original L1 entries: Food / Music | 156 / 201 |
| Existing null Bootstrap meanings | 2 |
| Reused original vectors | 355 |
| Selected HDBSCAN groups | 29 |
| Assigned entries | 147 |
| Unassigned encoded entries | 208 |
| Notes represented | 48 / 50 |
| Automatic epsilon | 0.9575326870058704 |
| Colored sections | 18 |

The selected interval is between angular distances `0.9785585154034873` and
`0.9365068586082534`. Epsilon is their midpoint. Every selected group appears
in exactly one section; the cut discards no groups or represented notes.

Three sections combine multiple fixed groups; the other 15 are singletons:

| Section | Groups | Contents | Distinct notes |
|---|---|---|---:|
| S02 | G02, G03, G04, G09, G14, G17 | Songs/lyrics/identification, music/search/playlists, musicians, live music/concerts, Nostr and GrowNostr | 23 |
| S03 | G08, G11, G16, G24, G29 | Chicken stock, lunches/lunch boxes, Food/preparation/meals, Foodstr, cooking/cookware | 19 |
| S08 | G06, G15, G21 | Personal interests/success/significance, enjoyment/anticipation/satisfaction, praise/appreciation | 14 |

Note sets may overlap between sections. These labels describe numerical
contents, not approved synthetic parent names or semantic containment.
In particular, Nostr/GrowNostr joining the Music section merits review.

The two entirely ungrouped notes are both Food-source notes:

- `4646bba688b309931c1f026b8dd3f9deb1ade8b515b7dd2c90e172a340066e69`:
  "How to spend some moments: Preparing sourdough bread."
- `c78ee86d3d31ff731203406db3ac159ffabe1aecd3a99587411e55d21c6a5c3d`:
  "okay, ngl... the raw milk slush is soooo good."

Their original entries and vectors remain saved, but HDBSCAN assigns none to
a selected group. This loss occurs before the epsilon cut. The two null
meanings, Songstr and zapagirl, belong to Music notes still represented by
other entries; they are not the reason these Food notes are absent.

## Verification and artifacts

Native-source tests exercise real preparation, receipt collection and SSE
worker paths with controlled external producers. They check note selection,
source ID collisions, exact vector reuse and rejection of unfinished inputs.
The new behavior was first demonstrated by failing tests. Numerical replay
produced identical groups, partition and epsilon. All 29 SVG labels have
section colors; cutoff arrows remain outside the tree. The PNG was visually
inspected. The prior Food and Music controls independently reproduce their
original 25/15 and 40/30 group/section counts and exact epsilons.

After synchronization with current main, 158 relevant tests ran. One existing
node-input test fails for two malformed-input subcases (`null` and integer
`42`): it receives an iteration error instead of the expected "must be an
object" message. Both failures were independently reproduced on unchanged
main before integration; this task changes none of that input-validation
code. All grouping/reuse tests pass, and a current-main numerical replay
preserves every mixed-corpus group, section and epsilon. The unrelated
error-reporting defect was left outside this task's scope.

Task worktree, retained for frozen source references and ignored evidence:
`/home/dev/src/notedeck_worktrees/algos/oracle-mvp-food-music-fifty-epsilon-v1`.

Primary ignored output:
`target/food-music-fifty-epsilon-v1/review-v2/`.
It contains `sources.json`, native HDBSCAN `request.json`/`result.json`,
`analysis.json`, `groups.md`, `groups.svg` and `groups.png`.
The initial numerical replay and individual corpus controls remain alongside
it. All source paths and hashes and the exact selected note IDs are preserved.
No hierarchy review UI was refreshed.

To reproduce from a task worktree, using a fresh output directory:

```bash
python3 -m sse_multivector.hdbscan_epsilon_review \
  /home/dev/src/notedeck_worktrees/algos/oracle-mvp-hierarchy-hr21-v41/target/hierarchy-hr21-v41-fifty-note-v1/HR21/state.json \
  /home/dev/src/notedeck_worktrees/algos/oracle-mvp-music-fifty-epsilon-v1/target/music-fifty-epsilon-v1/numeric-source/state.json \
  --notes-per-source 25 \
  --output target/food-music-epsilon-replay-v1 \
  --title 'Food + Music · 25 notes each · automatic epsilon candidate'
```

Review the three combined sections' contents before drawing a semantic-quality
conclusion or adopting the numerical rule in construction.
