# Admission boundary provenance v1 — experimental findings

The weakest accepted members usually still set the admission boundary. A few
mixed or weakly connected groups admit most of the studied wrong matches, and
one weak reference note limits tightening across its whole root. However,
useful outsiders also depend on weak routes and sometimes score below wrong
outsiders. Neither raising boundaries indiscriminately nor dropping those
groups establishes a quality-preserving fix.

This is a read-only diagnosis of the unchanged and centered full-meaning
experiments. No admission rule, boundary, score, membership, encoder or prompt
changed. No LLM calls, new encodings, training or paid resources occurred.
All semantic judgments were previously saved provisional agent assessments;
none became human gold through this audit.

## Inputs and question

Use only the frozen primary whole-note samples: 24 notes from HR36 and 24 from
HR37. Keep supplemental notes and omission screens outside these main tables.
Trace every selected heading in a reviewed wrong root through **every** group
that admitted it. Separately trace the selected witnesses establishing useful
root routes. Reuse the corrected changed-route review for centered scores.

The root scope comes from all its accepted topical families, not its synthetic
name. A witness need not semantically belong to the particular numerical group
that triggered root admission. This distinction matters below: a correct root
placement can come through an unrelated permissive group.

## What currently determines the boundary

The existing member-minimum rule calculates each member's mean similarity to
the other notes in its group. Its lowest member score is the group boundary.

The reference-note-preservation rule can raise that boundary. It compares each
accepted note's strongest member score with the median of its group, finds the
note's best such route, and uses the weakest note's best relative score as one
shared multiplier across the root. The final boundary is the larger of the
old minimum and that multiplier times the group's median. Preserving every
eligible accepted note can therefore limit tightening in unrelated groups.

| View | HR36 boundaries still at member minimum | HR37 boundaries still at member minimum | Total |
|---|---:|---:|---:|
| Original meanings | 155/157 | 123/130 | 278/287 |
| Centered meanings | 155/157 | 122/130 | 277/287 |

Across the original sample, 55 of 61 wrong heading/group routes pass boundaries
that remain at the member minimum. For centered scores, 64 of 68 do. Routes
overlap: one wrong root placement can have several headings and admitting
groups. These counts are not independent semantic errors or population rates.

## Groups admitting the wrong matches

The original calculation has wrong matches in only four of HR36's 157 groups
and ten of HR37's 130 groups on this sample. Some of those groups also provide
many useful root routes.

| Original group | Reference setting its minimum | Boundary | Wrong note/root placements passing this group | Useful witness notes passing this group |
|---|---|---:|---:|---:|
| HR36 C00001 Photography, fused-020 | IRIB broadcasting organization | 0.006853 | 3 | 14 |
| HR36 C00001 Technology, fused-071 | Technology as a named posting destination | 0.010120 minimum; 0.010378 final | 2 | 9 |
| HR36 C00005 Games, fused-001 | Roleplaying-game character backgrounds | 0.029628 | 2 | 0 |
| HR37 C00005 Language, fused-019 | English language | 0.012975 | 10 | 6 |
| HR37 C00005 Viewing/testing, fused-009 | Viewing presented content | 0.021189 | 5 | 1 |
| HR37 C00005 Game creation/play, fused-022 | Game developers | 0.020666 | 5 | 2 |
| HR37 C00004 Games/events, fused-002 | General organized Events | 0.017413 | 5 | 5 |
| HR37 C00002 Data, fused-006 | Data availability for one reporting interval | 0.011311 minimum; 0.013241 final | 2 | 12 |

Rows overlap and show selected witnesses, not all possible useful headings.
The zero in the Games row does not establish that the group is useless:
the sample contains no selected positive witness through it. Labels such as
Photography and Language summarize saved member titles; they are not new
canonical definitions.

Concrete mechanisms:

- **IRIB is explicitly a broadcasting organization**, while most peers describe
  cameras, photographs or photography. Its low score both sets Photography's
  minimum and limits the root-wide multiplier to 0.035599. Basketball scores
  0.009052 and Leisure escapes 0.009021, so both clear 0.006853. But Al Jazeera
  also uses this group at 0.012133 and is a valid news-provider root match.
  Its usefulness does not mean the group reliably distinguishes new news topics
  from unrelated topics.
- **Technology as a posting destination** has a different meaning from the
  technological field named by most peers. Its fixed meaning is retained;
  this audit does not silently interpret it as the broad field. Its weak
  within-group score makes the final bar low enough for Political parties.
- **English language** is the weakest member among language practice, learning
  apps, vocabulary, wordplay and language models. Requests for opinions scores
  0.042225, well above the 0.012975 boundary. The useful Nostr client releases
  witness scores only 0.017117 in the same group. Raising that group's bar above
  the wrong request would also remove this useful route.
- **Mining projects** explicitly means developing or operating mines extracting
  mineral resources. Its group otherwise describes cryptocurrency mining.
  At 0.019954, this member limits the original HR37 C00005 root multiplier to
  0.127170. All 22 groups in that root retain their member minima. Digestion
  clears the mining group's boundary at 0.020440. This is the mechanism under
  the saved fixed meanings, not a claim that mining is absent from the root or
  that the Bootstrap prompt must change.

Centering changes which weak member controls some groups, without removing
the mechanism. In HR36's Bitcoin initiative/media group, **Hope With Bitcoin**
sets the centered boundary at 0.008995. General Al Jazeera news (0.010694),
Hopelessness (0.010032) and Apologies (0.009521) all pass despite lacking the
required financial/art/music/event roles. No primary useful witness uses this
group. Again, that limited observation does not certify deleting it.

## Why a higher bar alone is insufficient

Every studied wrong heading/group route falls below its group's median of the
best member score per source note. But so do nearly all useful outsider routes.
Only 1/19 reviewed useful HR36 notes and 2/18 HR37 notes have any recorded
useful route reaching that median under the original score. Centering gives
1/19 and 3/20. These are checks on known witnesses, not proof that every other
heading on those notes fails. A median boundary is not recommended.

There are exact score-ordering conflicts as well. In HR37's original Games/
events group, Baseball scores 0.018458 while the wrong Asynchronous operations
scores 0.030179. No threshold on that one score can keep the lower Baseball
route and reject the higher software-operations route.

Use the union of previously reviewed exact wrong entry/root pairs for both
views, with no unresolved case treated as wrong. Inspect every currently
qualifying route for the union of known useful witnesses. A route is separable
by tightening only if its score is **strictly greater** than every known wrong
entry's score in that group. No replacement thresholds are fitted or applied.

| Ordering diagnostic | HR36 original | HR37 original | HR36 centered | HR37 centered |
|---|---:|---:|---:|---:|
| Reviewed useful notes | 19 | 18 | 19 | 20 |
| Useful notes with no known current route above all reviewed wrong entries | 2 | 7 | 0 | 4 |
| Eligible accepted note/root pairs | 809 | 777 | 809 | 777 |
| Accepted note/root pairs with no existing member route above all reviewed wrong entries | 1 | 16 | 2 | 18 |

The original nine blocked useful notes include Dietary advice, the nostube
software project, Football, Baseball, Genetics, the theatre-production note,
the Google advertising agency, the amateur-radio convention and Recipes.
Other unreviewed headings could rescue some notes; these are obstructions for
the **known current routes**, not permanent whole-note impossibility results.
Nor do they demand perfect classification. They show why eliminating all known
wrong matches by threshold adjustment has a measurable cost on current evidence.

## Implication for the next experiment

Preserving accepted memberships does not logically require every accepted
member to pass a new-outsider admission test. The current preservation rule
couples those two requirements and allows one weak note to constrain the root.
That coupling deserves an explicit test before another score transformation.
Do not simply replace it with a median or delete weak groups: this audit shows
that either shortcut can remove useful routes too.

Earlier [within-group meaning-clustering experiments](hierarchy-v53-coverage-investigation-v1.md)
already failed to distinguish weak references from valid rare topics and AI
agents. That rejected filter is not revived here. No new admission method is
specified, approved or activated by these findings.

## Evidence and verification

Ignored evidence remains in the research worktree under
`target/food-halves-v1/boundary-provenance-audit-v1/` through the external-storage
symlink.

- Frozen plan SHA256:
  `2e24f997f0bac09cfde5a3edadf2e0e6d477d728614b9ef831279612a7cbdc32`.
- `group-provenance.json` records every member's original ID, title, meaning,
  source note, member score, active threshold, weakest member and useful/wrong
  selected routes. `root-provenance.json` identifies the exact limiting notes,
  their best groups and the members establishing their relative scores.
- `wrong-entry-group-traces.json` retains all 129 wrong routes across both
  views; `useful-witness-group-traces.json` retains 248 useful witness routes.
  `exact-semantic-controls.json` freezes the same positive/negative meanings
  for score-order comparisons; it changes no old label.
- `useful-witness-ordering.json`, `accepted-note-ordering.json`,
  `note-ordering-summary.json` and `summary.json` retain all comparisons behind
  the ordering tables, including identities of outranking wrong entries.
- `trace.py` is a data-bound inspection script, not a provider experiment or
  replacement admission implementation. The first attempt stopped on a
  difference between the two saved review schemas; its error log is retained.
  The corrected inspection completed without changing source artifacts.
- Independent reconstruction checks 586 minimum-setting members and all 377
  selected wrong/useful query/group routes against the saved full vectors.
  Maximum score difference is `2.11e-15`. All 24 existing root boundary
  calculations replay exactly through `derive_boundaries`. All pinned inputs
  remain unchanged. No production code or test seam was added.

The subsequent [reference-note bend test](hierarchy-note-bend-admission-v1.md)
relaxes the self-recovery constraint without changing memberships. Its frozen
bend variant removes most wrong matches but loses most reviewed useful omitted
notes and two human Food acceptances. Following the user's clarification, it
remains a conservative candidate with an explicit coverage tradeoff; it is not
activated in HiGen. The result does not establish that every reference must
pass an admission test. The subsequent unchanged-rule
[HR38 transfer](hierarchy-hr38-conservative-admission-v1.md) finds useful routes
for 27 of 32 sampled proposals, but 15 wrong root placements
remain; 11 pass a single People group with weak full-meaning support. The
conservative candidate remains unactivated, with fresh precision and coverage
limits recorded separately.
