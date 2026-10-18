# HR38 conservative admission transfer v1 — experimental findings

The unchanged conservative candidate finds a useful route for **27 of 32**
newly sampled proposed notes. Four have only wrong proposed routes and one is
unresolved. However, those same notes have **15 wrong extra/root placements**
among 56 proposed placements; eight other placements remain unresolved. The
very low wrong-placement count seen on HR36/HR37 does not transfer uniformly.
This remains a conservative research candidate, not an activated HiGen policy
or a requirement to achieve perfection.

Most wrong placements concentrate in one accepted People group. The same root
also misses clear people topics such as racing drivers and astronauts. This is
useful evidence for a focused representation/boundary diagnosis, rather than
choosing another cutoff from the new judgments.

## Frozen test

Apply [reference-note bend admission v1](hierarchy-note-bend-admission-v1.md)
without changing its scoring, fusion groups, bend calculation, fallback or
parameters. HR38 contains **2,000 notes**, not 1,000. Its completed hierarchy
covers 1,328 distinct notes; 672 are outside its six roots. Excluding all prior
HR35/HR36/HR37 note IDs and exact full-post text matches leaves 670 fresh omitted
notes. Of these, 499 have usable supplied meanings, comprising 2,127 entries;
171 lack a usable meaning and are outside this scoring test. No AS version
older than ASv6.100 enters these inputs.

Use 2,451 original reference entries from the six roots' initial versions.
Amendments, descendants, synthetic definitions and outsiders do not form the
reference networks. All reference meanings, including fusion-unassigned ones,
remain available when reviewing root scope. Synthetic root names identify
roots; they do not define admission scope or make every topic eligible.

Reuse exact encoded contexts where available. Encode missing views locally
with the same frozen SSE checkpoint, base artifact, 768 dimensions, contextual
pooling and 512-token maximum. Each input is `title + "\n\n" + meaning`:
one view pools the title, the other the complete explicit meaning. There are
4,427 new unique contexts and nine exact replay contexts, producing 8,872 rows;
134 required entries reuse existing exact-context vectors. These are local SSE
encodings, not LLM calls or training.

Accepted-only fusion remains K=20, sigma=0.5, 20 iterations; HDBSCAN remains
min_samples=3 (including self), min_cluster_size=2, EOM. Score each outsider
independently with full-meaning support `exp(-5.5 * (1-cosine))`, averaged within
a fixed group, excluding its whole source note. Apply the unchanged broader
note-preserving baseline and the unchanged stricter reference-note bend.
Neither outsiders nor reviewed judgments choose groups or thresholds.

## Actual proposals

Counts are distinct fresh omitted notes proposed to each root, before semantic
review. Overlap between roots means these rows must not be summed as distinct
new notes.

| Root, for identification | Broader baseline | Conservative bend |
|---|---:|---:|
| C00001 · General knowledge | 476 | 318 |
| C00002 · Life and activity | 76 | 17 |
| C00003 · Daily life | 294 | 3 |
| C00004 · United Kingdom | 3 | 0 |
| C00005 · Society and technology | 410 | 51 |
| C00006 · Humanity and humaneness | 283 | 203 |
| Any root, deduplicated | 492 | 384 |

The candidate removes 108 of 492 note proposals (22.0%). Proposed note/root
placements fall from 1,542 to 592 (61.6%). These are automatic proposal counts,
not verified correct additions or actual hierarchy membership changes.

## Whole-note review

Freeze the hash-selected sample before judgments: 32 proposed notes, root
supplements sufficient to review two available proposals per root, 12 notes
proposed only by the broader baseline, and eight neither-policy notes if
available. Only seven neither-policy notes exist, so inspect all seven. This
produces 53 reviews. The United Kingdom root has no candidate proposals and
therefore supplies no positive review case; do not manufacture one.

Review the complete original post, all supplied query meanings and actual
accepted reference families. Assess every proposed root separately. A useful
note needs a supported **selected heading**; an unselected good heading cannot
rescue a bad proposal. Keep wrong extra roots, legitimate omissions and
uncertainty separate. All new judgments are provisional agent assessments,
not new human gold or trained labels. No reviewed label changes the method.

| Cohort | Useful notes | Wrong-only notes | Unresolved notes |
|---|---:|---:|---:|
| Primary proposed sample, 32 notes | 27 | 4 | 1 |
| Root supplements, 2 notes | 2 | 0 | 0 |

The primary notes have 56 proposed root placements: 33 supported, 15 wrong and
eight unresolved. Supplements have five supported, two wrong and one unresolved
placement; keep those out of the primary sample.

| Root | Supported primary placements | Wrong | Unresolved |
|---|---:|---:|---:|
| C00001 | 24 | 2 | 2 |
| C00002 | 4 | 0 | 1 |
| C00003 | 0 | 0 | 0 |
| C00004 | 0 | 0 | 0 |
| C00005 | 2 | 2 | 1 |
| C00006 | 3 | 11 | 4 |

Examples of useful routes include Nostr beneath the accepted social-networking
protocol family, music beneath accepted Art, student aid beneath Financial
support, Codex beneath AI assistants, and spectators beneath People. Physical
hoses are not rejected merely because many references are digital: accepted
Technology explicitly includes practical physical tools. Likewise, accepted
Life is not silently restricted to positive feelings.

Wrong-only examples include Bread in C00001, which has no accepted Food family,
and Undesired behavior in the People-dominated C00006 root. Wrong extras include
App login options in C00006 and ordinary, non-AI music in C00005 through its
AI-art group. Unresolved cases include fictional ordinary people, body versus
person scope, a Reddit forum versus a collective of people, and general civic
participation versus humane concern. These qualifications are retained rather
than converted to positives or new human rejections.

### Missed useful notes, assessed separately

| Omission screen | Clear useful missing route | No demonstrated fitting family | Unresolved |
|---|---:|---:|---:|
| Broader baseline proposes, conservative omits: 12 | 6 | 2 | 4 |
| Neither method proposes: all 7 | 4 | 1 | 2 |

The first screen misses a software library, privacy technology, activity
logging, star ratings, racing drivers and a hotel industry note. The second
misses celebrity, astronaut, Australian-athlete and telecommunications-outage
notes. Clear witnesses are actual accepted Software, Technology, Data,
Assessments, People and Business-sector meanings. These are coverage costs,
not new judgments that those notes do not belong. The samples do not estimate
population recall. No demonstrated fit is limited to supplied evidence, not a
proof that no future hierarchy could admit the note.

## Why the People root remains permissive

All 11 wrong primary placements in C00006 pass **fused-002**, containing 15
People entries and one Individuals entry. Their meanings denote human beings;
several add optional examples such as protocol arguers, athletes, lawyers or
people addressed in requests. They do not thereby denote the activities or
software options associated with those people.

This group's median member support is 0.033348. Its original threshold is
0.009354; the frozen root bend raises it only to 0.011525. Undesired behavior
scores 0.024002, audience reactions 0.027289 and inquiries 0.014026, so they
still pass. No score or threshold is changed by this diagnosis.

The 120 distinct within-group entry pairs have median cosine **0.9873 in the
contextual-title view**, but **0.2839 in the full-meaning view**. For example,
“People are individual human beings” and “People are human beings, including
but not limited to those who argue about protocols and those whose
understanding the author doubts” have full-meaning cosine 0.3520. Identical
short definitions replay at cosine 1.0. Thus semantically consistent People
references can have weak numerical support. Optional example wording is a
concrete representation hypothesis, not an established sole cause or authority
to rewrite meanings, drop references, change pooling or add an arbitrary cutoff.

## Evidence and checks

Ignored evidence remains in the retained research worktree at
`target/food-halves-v1/hr38-conservative-transfer-v1/`, through its external
storage symlink. The worktree is retained for frozen source/artifact paths.

- Frozen plan SHA256:
  `b270a115291cc76d8d72dec5cea4feb13c5e1b5df40ac9b172766cd74a83b66c`.
- Frozen review-selection SHA256:
  `e08f2453610b2b4a9d6afaab101782dbaf8eb3b5f6780f9bcb84d29136171b04`.
- `plan.json`, `worker-request.json`, `worker-config.json` and the native
  `worker-result/` retain all input bindings, spans, hashes and raw vectors.
  The initial encoder attempt failed before inference on missing libstdc++;
  its log and the environment-only recovery record are preserved. The existing
  Python/model/package versions did not change.
- `reference-models.json`, `root-references.json`, `group-composition.json`,
  all six query/group NPZ files and `query-root-results.json` retain all
  640,227 score cells and 301 groups, not only selected matches.
- `review-input.json` retains full original posts and all supplied meanings;
  `whole-note-reviewed-results.json` retains every selected root, witness,
  explanation and unresolved case. An explicit reconsideration preserves the
  initial quality-assessment judgment instead of silently replacing it.
  `people-group-diagnostic.json` retains all wrong People routes and numbers.
- All 39 pinned inputs remain unchanged. All required title views match native
  HR38 vectors within `3.98e-13` cosine error, and all 18 exact replay views
  pass. Sampled independent scalar group scores differ by at most `3.47e-17`.
  Independent scalar reconstruction matches all six bends and 301 thresholds
  exactly. Candidate proposals remain a subset of the corresponding baseline.
- The relevant numerical regression suites pass **90 tests**. No LLM calls,
  training, paid resources, hierarchy changes, prompt changes or UI updates.

The experiment supports retaining a useful conservative option, while exposing
a concentrated admission problem before adoption. It does not establish a
uniform low wrong-placement rate, compare root-quality rates from a large
human-labeled sample, or justify rejecting the entire approach because it
misses useful notes. A focused test of optional-example effects is a possible
next diagnostic; it has not been run or activated here.
