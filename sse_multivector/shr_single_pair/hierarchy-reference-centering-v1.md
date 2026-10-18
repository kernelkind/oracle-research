# Accepted-reference mean-centering v1 — experimental findings

Mean-centering is a tradeoff, not a consistent improvement over the unchanged
full-meaning admission experiment. It preserves all 37 previously useful notes
in the two primary whole-note samples, and rescues two additional HR37 notes.
However, unwanted root placements double in HR36. Keep the original score as
the reference; this does not qualify centering for automatic admission.

No hierarchy, prompt, encoder, group membership or production policy changed.
No LLM calls, new encodings, training or paid resources were used. Semantic
assessments remain provisional agent judgments except the four existing user
Food controls. Perfection is not the criterion: useful recovery and unwanted
extra root placements are assessed separately.

## Single change tested

Use the same frozen full-meaning SSE vectors as the prior experiments. For
each reference corpus, collect the unique original entries in **all six roots'
initial memberships**, including entries not assigned to a fusion group.
Normalize their vectors, calculate their shared average, subtract it from both
incoming and reference vectors, renormalize and calculate cosine similarity.
The incoming entry never enters this average or the fusion networks.

For member calibration, and any incoming entry whose source note occurs in the
bank, exclude that entire note from the average. The same note is also excluded
from group scoring. Apply exactly that row's average to both sides. This avoids
a calibration member or an old overlapping query supplying its own background.
Do not average each root separately: that would deliberately remove its topic.

| Reference bank | Original entries | Distinct notes | Norm of shared average |
|---|---:|---:|---:|
| HR35 | 1,289 | 663 | 0.4494 |
| HR36 | 1,390 | 623 | 0.4672 |
| HR37 | 1,103 | 569 | 0.4701 |

The average can contain real topics as well as general embedding structure.
Its norm does not establish that it represents grammatical or definition-writing
style. HR36's largest initial root contributes 904 of its 1,390 bank entries;
this is an intentionally unchanged entry-weighted experiment, not a balanced
or topic-free background estimate.

Leave all other choices unchanged: original accepted-only fusion memberships,
the `exp(-5.5 * (1 - cosine))` conversion, per-entry group mean, independent
outsiders, and whole-source-note exclusion. Recompute both original member
minimum and reference-note-coverage boundaries from centered member scores.
Never reuse old thresholds on the new scale. Centered note coverage is the
primary comparison; the minimum rule is a separate boundary diagnostic.

No component-count search, principal-component removal, whitening, learned
projection, constant cutoff or label-based transformation selection was added.
Zero residual vectors or an unavailable bank stop calculation without a
fallback. The reusable calculation is in
[fixed_reference_centering.py](../fixed_reference_centering.py).

Mean removal has published precedent, but the word-vector results in
[All-but-the-Top](https://arxiv.org/abs/1702.01417) do not establish that it helps
these SSE meanings. That paper also removes principal components; this test
isolates mean removal alone.

## Frozen heading panels

Compare actual selections using the unchanged and centered note-coverage rules.
Useful and unwanted counts are separate. Panels overlap and have different
selection processes; do not pool them into one accuracy estimate.

| Frozen panel | Reviewed useful / unwanted | Useful: original → centered | Unwanted: original → centered |
|---|---:|---:|---:|
| HR35 Food | 30 / 51 | 14 → 12 | 3 → 0 |
| HR35 Arts | 63 / 30 | 52 → 53 | 4 → 4 |
| HR36 against old Food | 19 / 62 | 15 → 16 | 1 → 1 |
| HR36 against old Arts | 18 / 57 | 5 → 8 | 0 → 1 |
| HR37 against old Food | 12 / 50 | 11 → 11 | 0 → 0 |
| HR37 against old Arts | 29 / 33 | 13 → 16 | 0 → 0 |
| HR36 own-root heading audit | 36 / 14 | 36 → 34 | 12 → 9 |
| HR37 own-root heading audit | 36 / 21 | 30 → 23 | 9 → 6 |

All four existing user Food note decisions still pass. The post-result Japanese
CPI observation remains missed by the note-coverage rule. Reference self-coverage
is preserved, but is not evidence of held-out admission accuracy.

## Matched whole-note review

Reuse the frozen 24 proposed-note samples per corpus from
[whole-note admission audit v1](hierarchy-whole-note-admission-audit-v1.md).
Retain old judgments and review changed routes separately after scoring.
A lost heading is not a lost note when another **actually selected** heading
provides a valid route. Root names do not define scope; use actual accepted
topic families. Valid membership does not depend on the triggering numerical
group being the only possible semantic family in the root.

| Primary sample measure | HR36 original → centered | HR37 original → centered |
|---|---:|---:|
| Notes with a supported route, out of 24 | 19 → 19 | 18 → 20 |
| Notes with only wrong routes | 2 → 2 | 5 → 3 |
| Unresolved notes | 3 → 3 | 1 → 1 |
| Supported root placements | 26 → 26 | 40 → 43 |
| Unsupported root placements | 5 → 10 | 22 → 19 |
| Unresolved root placements | 7 → 7 | 10 → 7 |
| Useful notes also placed under an unsupported extra root | 3 → 7 | 8 → 8 |

All 37 originally useful primary-sample notes retain at least one supported
route. All three supplemental HR36 notes also retain a valid route; report
those separately from the primary sample. Some individual valid root placements
are still lost, including the amateur-radio convention's technical route and
the opinion request's emotional/evaluative route in HR37.

Examples explaining the tradeoff:

- The HR36 TV-series heading drops, but a selected **Sex scenes** meaning
  explicitly describes film/television narrative content. The note remains
  useful under the content root.
- The HR37 student-protest note gains a **Pennsylvania → United States** route.
  This rescues the note without changing the prior **Students → technical**
  rejection. Other unwanted extra placements remain.
- The hallucinogen note gains a provisional scientific-explanation route through
  **Biological evolution** and the post's adaptive-mechanism discussion. This
  does not vindicate its old technical or emotional placements.
- HR36 newly admits **Product testing** and **Sex scenes** under the game/sport
  collection, and general **Al Jazeera** news under the finance/music/art/event
  collection. Their fixed meanings lack the required roles.

In the separately frozen unproposed-note screens, centering recovers useful
routes for four of eight HR36 notes, including two Japanese relay-measurement
websites, Japanese Books and the public-protest note. The earlier relay headings
themselves remain missed. One additional note has only an unsupported route and
three remain unproposed.

For HR37's eight screened unproposed notes, only the football note obtains a
supported route; four have only unsupported routes and three remain unresolved.
For example, **Dogs** is admitted to publication/commerce/science without that
role, while the plausible **Chicago → United States** route remains missed.
The opaque build and Pollerama identities remain unresolved. The earlier exact
**Daylight saving time → technical/mining** rejection is preserved: an initial
post-result review mistakenly reopened it as unresolved; a separate v2
assessment corrects that without overwriting either historical record.

These matched samples were selected from the original method's output, not
centering's full output. They cannot estimate the accuracy of new proposals
outside those samples. Across all available omitted meanings, proposed distinct
notes change from 239 to 242 in HR36 and 261 to 288 in HR37. Those are proposal
counts, not verified useful recoveries.

## Evidence and checks

Ignored evidence directory in the retained research worktree:
`target/food-halves-v1/reference-centering-admission-v1/`.
It follows the established external-storage symlink.

- Frozen plan SHA256:
  `eef0a83f17dbb8b35057fd072c2b35668493adecf779e020b6d66f6d0fdd2f84`.
- `plan.json` pins 64 input/code hashes, accepted-bank entry IDs and the single
  transformation before centered calibration or query outcomes.
- `reference-models.json`, `reference-coverage.json`, `centering-bank-summary.json`
  and all centered query/group score arrays retain the complete calculation.
- `query-root-results.json`, `panel-results.json`, `human-controls.json` and
  `all-own-root-note-proposals.json` retain automatic selections without review
  labels determining scores or thresholds.
- `whole-note-route-deltas.json` preserves all changes for the original 67-note
  audit; `post-result-whole-note-assessments-v2.json` and its summary retain the
  corrected provisional route review. The superseded initial review is kept.
- `verification.json` confirms exact original decisions across all 14 reference
  collections / 327 groups and 992,454 query/group cells across both views.
  Original-score replay error is at most `2.78e-16`; independent centered scalar
  checks differ by at most `1.11e-16`. All pinned sources remain unchanged.
- The helper first failed to import in its new test, then passed all four
  centering tests and the relevant regression suites: 85 tests total. Checks
  cover direct cosines, whole-note exclusion, query independence, permutation,
  input normalization, immutability and explicit degeneracy rejection.

This trial does not separate a shared stylistic component from a shared topic,
or show that another background estimate would help. The practical conclusion
is narrower: this particular mean removal has useful local gains but does not
consistently reduce unwanted root placements. It remains experimental and is
not activated in HiGen.

The subsequent [boundary provenance audit](hierarchy-admission-boundary-provenance-v1.md)
traces all wrong primary-sample routes under both views to their exact accepted
members and root-wide limiting notes. It also records score-order conflicts
that prevent threshold tightening from preserving every known useful route.
