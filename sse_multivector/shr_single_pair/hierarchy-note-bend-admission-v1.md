# Reference-note bend admission v1 — experimental result

This particular relaxation is too conservative to replace the baseline. On the
matched primary samples, useful omitted notes fall from 37 to 14 under original
meaning scores, while wrong root placements fall from 27 to 1. Two of the three
user-approved Food notes are rejected. Lower noise alone does not establish
successful recovery of notes that fit existing roots.

This does not prove that requiring every reference note to pass is necessary,
or that every alternative without that constraint fails. It rejects one frozen
replacement: choosing the existing positive log-support bend among reference
notes' best relative scores instead of their minimum.

No existing membership, hierarchy, prompt, encoder or query score changed.
There were no LLM calls, new encodings, training or paid resources. The new
function is experimental and is not activated in HiGen.

## Exact change

Keep the original accepted-only fusion groups and full-meaning scores. For
each group, retain its minimum member score and median of each source note's
strongest member score. All those scores already exclude the entry's entire
source note.

For each accepted note, divide its strongest score in each of its groups by
that group's median, then take its best ratio across groups. Each distinct
note contributes once. The old rule uses the **minimum** of those note ratios
as a shared multiplier for the root, guaranteeing a surviving self-recovery
route for every eligible reference note.

The new rule applies the existing log-support bend calculation to those same
note ratios. Normalize them by their maximum to reuse its [0,1] input contract;
the logarithmic gaps and geometric midpoint retain their scale. Undo that
normalization to obtain the root multiplier. No reviewed label, outsider,
fixed semantic cutoff, quantile search, trimming change or new score determines
the bend.

As before, each group threshold is the larger of its original member minimum
and the multiplier times its median. A missing bend retains the exact original
multiplier. All 28 tested root/view combinations have a positive bend, so that
fallback is unused in the actual replay. Thresholds never decrease.

Accepted notes whose self-recovery score falls below the new boundary remain
members of the root. The experiment removes the constraint linking admission
standards to preserving every existing note's self-recovery; it does not delete
the notes or their references.

Implementation: [fixed_reference_note_bend.py](../fixed_reference_note_bend.py),
reusing the unchanged
[member-distribution bend](../fixed_reference_member_distribution.py) and
[note-preservation calculation](../fixed_reference_note_coverage.py).
The new computation is O(N log N) in accepted notes per root, with no extra
pairwise vector work. Outsider comparisons remain independent.

## Matched whole-note results

Use the original frozen 24-note primary sample for each corpus. Centered scores
are a separately declared transfer check with the **same** boundary rule.
Keep supplements outside the primary table. Preserve original assessments;
when the old useful witness disappears but other selected entries remain,
review those actual entries separately after scoring.

| Measure | HR36 original score | HR37 original score | HR36 centered score | HR37 centered score |
|---|---:|---:|---:|---:|
| Useful notes, old → bend | 19 → 7 | 18 → 7 | 19 → 9 | 20 → 9 |
| Supported root placements, old → bend | 26 → 10 | 40 → 12 | 26 → 10 | 43 → 11 |
| Wrong root placements, old → bend | 5 → 0 | 22 → 1 | 10 → 0 | 19 → 2 |
| Previously useful notes now entirely unproposed | 12 | 10 | 10 | 11 |

For original HR37 scores, another formerly useful note retains only an
unresolved route. Thus losing a valid heading is not automatically counted as
losing a note, and mere reachability does not establish a useful replacement
route. All three supplemental HR36 notes retain a supported route; these
root-coverage supplements are not extra random primary successes.

The two centered wrong placements are Clothing needs in the publication/data
root, and Speakers (people) in the technical/language-learning root. The latter
root was previously useful through **Verification**. Once that witness is
removed, general speaking supplies no technical or language-learning role.
A subset of selected headings can therefore leave a formerly useful root
placement with only wrong evidence, despite introducing no new heading.

Alternate-witness checks preserve useful routes through explicit software form
handling, produced audiovisual material, sports predictions, code publication,
contact information and content creators. These are provisional agent reviews,
not new human gold. In particular, digital-publication extensions do not imply
that every computing process belongs in the content root. All prior exact
entry/root rejections remain unchanged.

### Human Food controls

| Previously reviewed note | Expected | Original and centered bend result |
|---|---|---|
| L00101 · Eggs as food | Accept | Rejected |
| L00440 · Egg yolks | Accept | Note accepted through L00438; yolk heading itself rejected |
| L02984 · Eggs | Accept | Rejected |
| L02222 · Easter broadcast | Reject | Rejected |

These are note-level controls; another valid heading can preserve the Egg
yolks note. Both score variants match only two of the four decisions.

## Frozen heading panels and proposal counts

Useful and unwanted selections remain separate; unresolved judgments are not
converted to negatives. These panels overlap and are not independent accuracy
estimates.

| Panel | Useful selected: original boundary → bend | Unwanted selected: original boundary → bend |
|---|---:|---:|
| HR35 Food, original scores | 14/30 → 5/30 | 3/51 → 0/51 |
| HR35 Arts, original scores | 52/63 → 8/63 | 4/30 → 0/30 |
| HR36 own-root audit, original scores | 36/36 → 8/36 | 12/14 → 0/14 |
| HR37 own-root audit, original scores | 30/36 → 5/36 | 9/21 → 0/21 |
| HR36 own-root audit, centered scores | 34/36 → 10/36 | 9/14 → 1/14 |
| HR37 own-root audit, centered scores | 23/36 → 4/36 | 6/21 → 0/21 |

All-own-root potential omitted-note proposals change from 239 to 75 in HR36 and
261 to 92 in HR37 with original scores; centered scores change from 242 to 91
and 288 to 89. Those counts are proposals, not verified correct recoveries.

## Mechanism and interpretation

All 28 bends raise the multiplier. For original HR36 C00001, it rises from
0.035599 to 0.736715. Photography's boundary jumps from 0.006853 to 0.141833,
above the valid Al Jazeera match at 0.012133 as well as the wrong Basketball
match at 0.009052. The method has stopped the weak reference from dictating
the boundary, but the new boundary also blocks useful semantic extensions.

Reference self-recovery remains much higher than useful outsider recovery:
1,507 of 1,759 eligible reference note/root pairs still pass with original
scores, and 1,468 with centered scores. **All reference memberships remain
intact**, including those not passing this diagnostic. Their failed self-test
is not the reason for rejecting the variant; the lost reviewed omitted notes
and user controls are the material coverage loss.

These observations are consistent with a mismatch between the two populations:
accepted members often closely resemble other definitions of the same topic,
whereas useful omitted entries can extend a root through a different entity,
activity or topic. A bend in existing-member scores is not automatically a
boundary separating useful new topics from wrong ones. The experiment does
not establish duplication as the sole cause or identify a proven replacement.

A useful next probe is to withhold repeated definitions together and inspect
recovery from the remaining references. That would check whether the reference
test can better represent a genuinely new topic, before choosing another
admission boundary. It is unrun and not authorized by this write-up itself.
Historical membership must not silently become new semantic gold.

## Evidence and verification

Ignored evidence in the retained research worktree:
`target/food-halves-v1/note-bend-admission-v1/`, through its external-storage
symlink. The worktree remains necessary for frozen source and artifact paths.

- Plan SHA256:
  `9f8ff1144e6e4e5b5671ac4daa1ae582f67502b7f62ac10cc9cef17216f6ea51`.
  It pins 67 sources and the rule before new boundaries or outcomes.
- `reference-calibrations.json` retains both old and new thresholds and every
  note curve; `reference-self-recovery.json` lists every failed reference route
  without changing membership. The existing source code remains byte-for-byte
  unchanged; the experimental helper is separate.
- `query-root-results.json`, `panel-results.json`, `human-controls.json` and
  `all-own-root-note-proposals.json` retain complete automatic outcomes.
  `whole-note-reviewed-results.json` records the separate alternate-witness
  reviews, with original assessments preserved.
- All 44,196 old query/root decisions replay exactly. Every candidate decision
  is a subset of its matching original decision, across 992,454 query/group
  score cells, 14 reference collections and two score views.
- An independent scalar reconstruction checks all 28 bends and 654 group
  thresholds; maximum boundary error is `1.11e-16`. All pinned sources remain
  unchanged. Five new failing-first helper tests and the relevant numerical
  regressions pass: 90 tests total.
- No production admission or official hierarchy experiment was run, so no
  hierarchy UI or official-run spreadsheet changed.
