# Reference-note bend admission v1 — experimental result

Status: retained as a **conservative admission candidate**, following the user's
clarification that lower coverage can be an acceptable tradeoff. No production
admission behavior is activated. The unchanged
[HR38 transfer](hierarchy-hr38-conservative-admission-v1.md) finds 27 useful
notes among 32 sampled proposals, but 15 wrong root placements remain, 11 through
one People group. Uniform low-error generalization remains open.

On the matched primary samples, useful omitted notes fall from 37 to 14 under
original meaning scores, while wrong root placements fall from 27 to 1. Among
the 16 notes it still proposes, 14 are useful, one has only wrong routes and one
is unresolved. Two of the three user-approved Food notes are omitted. These
are measured coverage costs, not new judgments that those notes do not fit.

This does not prove that requiring every reference note to pass is necessary,
or that every alternative without that constraint fails. The frozen candidate
chooses the existing positive log-support bend among reference notes' best
relative scores instead of their minimum. It has not established itself as a
general replacement for the broader baseline; it remains worth validating as
a stricter option.

No existing membership, hierarchy, prompt, encoder or query score changed.
There were no LLM calls, new encodings, training or paid resources. The new
function is experimental and is not activated in HiGen.

## Current practical assessment across corpora

The unchanged full-meaning conservative rule has enough demonstrated coverage
value to justify a saved-hierarchy trial. This is a recommendation, not approval
to activate it or evidence that every added placement is correct. The user
rejected manually selecting definition words such as people; that proposal is
closed without preparation or encoding. The objective remains automatic
recovery of omitted entries into suitable existing roots, accepting a measured
coverage/quality tradeoff rather than perfect separation of one People case.

| Corpus | All additional-note proposals | Reviewed conservative proposals with a useful route | Wrong reviewed root placements |
|---|---:|---:|---:|
| HR36 | 75 | 7 / 7 | 0 / 10 |
| HR37 | 92 | 7 / 9 | 1 / 14 |
| HR38 | 384 | 27 / 32 | 15 / 56 |

Proposal totals are distinct omitted notes, not verified correct additions.
HR36/HR37 retain seven and nine proposals from the original 24-note samples;
HR38 independently samples 32 of the conservative rule's proposals. Supplements
are excluded. These different, small agent-reviewed samples must not be pooled
into a claimed general accuracy rate. HR37 has one wrong-only and one unresolved
proposed note; HR38 has four wrong-only and one unresolved. Wrong extra roots
remain errors even when another route makes the note useful.

The coverage cost is substantial: on the matched HR36/HR37 samples, useful
notes drop from 37 to 14 while wrong root placements drop from 27 to one.
Two of three human-approved Food notes remain omitted. HR38's separate omission
screen also identifies six useful notes among 12 proposals lost to tightening.
This rule is a conservative addition pass, not a recovery guarantee.

HR38's 11 wrong People-group placements account for 11 of its 15 wrong
placements. The other sampled roots have 30 supported, four wrong and four
unresolved placements. This identifies concentration; it does not authorize
blacklisting that root/group or fitting a new threshold from these judgments.

Centered conservative scores are an alternative, not an established successor:
the same HR36/HR37 primary samples have 18 useful notes versus 14, but two wrong
root placements versus one. No matched centered-conservative HR38 transfer is
saved. The full-meaning rule remains the candidate tested unchanged across all
three corpora; the evidence does not establish a universal best score.

The user authorized applying the **already computed conservative additions to
a separate copy of HR38**. That preview is now generated; human hierarchy review
is pending. No new HiGen version or production policy is activated. The copy
retains all saved proposals, including known wrong placements, so its review
can assess actual usefulness and browsing noise without selective filtering.

All counts were independently recounted from saved query decisions and frozen
note/root judgments. Evidence:
`target/food-halves-v1/conservative-admission-reassessment-v1/summary.json`,
SHA256 `39e88afad480e2ea22c0a534f81a58d6e6a5abec584ff5e86aeb7fa04069f7b0`.
Independent joins verify all 80 primary note states and all 55 supported
witnesses against the actual own-corpus query decisions. There are no new
scores, semantic labels, admissions, encodings or model calls.

### Saved HR38 preview

Artifact: `target/food-halves-v1/hr38-conservative-preview-v1/` in the
`oracle-mvp-hierarchy-food-halves-v1` worktree. `hierarchy.json` and `notes.json`
use the existing review UI format; `root-admissions.json` retains every selected
entry and source binding, and `verification.json` independently checks the copy
against HR38's original verified review export.

| Measure | Original HR38 | Saved-addition preview |
|---|---:|---:|
| Distinct notes beneath roots | 1,328 / 2,000 | 1,712 / 2,000 |
| Coverage | 66.4% | 85.6% |
| Canonical nodes / roots | 133 / 6 | 133 / 6 |

The 384 additional distinct notes create 592 note/root placements because some
notes qualify for multiple roots. They are attached directly to existing roots;
children, headings, meanings, original memberships, short IDs and full posts
are preserved. The display container remains empty. No child construction is
rerun, so this preview does not measure how added entries would affect later
grouping or depth. The original constructor state and review bundle are intact.

The exporter verifies the saved decision hashes and exact original-entry
identities. It reuses HR38's verified export after checking its state, corpus and
exported-file hashes, avoiding historical clustering recomputation. The existing
UI parser accepts the output. Independent checks retain all 15 reviewed wrong
placements rather than silently removing them. There are no new scores,
encodings, LLM calls or training; this is a mechanical preview, not semantic
certification. The live review UI has not been refreshed.

### Supplemental review of the actual preview

The user authorized inspecting the added notes before deciding whether to
adopt the pass. A frozen supplemental selection inspects eight previously
unreviewed proposed note/root placements per root, or all available when fewer
remain. Selection is by SHA256 of a fixed prefix, root ID and note ID, before
judgments. This yields 33 placements across 32 distinct notes, with no overlap
with the prior 53 reviewed notes. It is root-stratified, not a population error
estimate, and is not pooled with the earlier sample.

Review uses each full post, the selected entries and actual accepted references,
including relevant families outside the winning fusion group. Synthetic root
names do not establish scope. Unselected headings cannot rescue a proposal.
Broad accepted Life meanings are not silently restricted to positive feelings;
unclear activity/goal, depiction and communication-purpose relationships remain
unresolved. These are provisional agent judgments, not new human gold.

| Root | Supported | Wrong | Unresolved |
|---|---:|---:|---:|
| C00001 · General knowledge | 6 | 1 | 1 |
| C00002 · Life and activity | 4 | 0 | 4 |
| C00003 · Daily life | 1 | 0 | 0 |
| C00004 · United Kingdom | No additions | — | — |
| C00005 · Society and technology | 1 | 4 | 3 |
| C00006 · Humanity and humaneness | 2 | 6 | 0 |

Useful additions include Books through accepted Publications, Health through
Well-being, and Voice actors and Actors through People. The root placement can
be useful even when an unrelated winning group is not a defensible semantic
explanation: radio-spectrum measurements fit accepted Data, for example.

Two repeated mismatches matter to adoption:

- C00006 admits Amazon Mechanical Turk (L07047), Mockery (L09290),
  Transmissions (L09404), Summaries/Invitations, Pretending/Deception and Nostr
  relays (L09342) through its People group. Services, messages and conduct do
  not become human beings because people use, send or perform them.
- C00005 admits Self-portraits (L09409), conventional graphics tools and icons,
  interactive telescope-image viewing (L01781), and Builds (L00622) through an
  AI-specific group without an established AI role. Ordinary art or software
  can fit C00001 while remaining a wrong extra route in C00005.

The assessment is to retain the candidate and preview but **not recommend
adopting the unchanged rule yet**. The concern is repeated broadening of People
and AI-specific topics, rather than a requirement for perfect precision. No
group is blacklisted, threshold retuned, reviewed label used in scoring, or
saved proposal removed. The coverage count remains 85.6%; it does not measure
useful coverage or establish acceptable browsing noise.

Evidence: `target/food-halves-v1/hr38-preview-quality-review-v1/`. Frozen input
SHA256: `3878c21faf4440e32430f771fb4b3d8a35b0a06aa9c62fb127fdf62eb1311c6c`.
`review.json` preserves all 33 rationales and accepted-reference witnesses;
`verification.json` checks source hashes, exact selected entries in the actual
preview, witness membership, sample disjointness and unchanged preview files.
No scores, vectors, hierarchy files, prompts or model-call allowances changed.
No new encodings, model calls, training or UI refresh occurred. Human review and
any subsequent implementation or full-run decision remain open.

### Title/meaning agreement diagnostic

The user authorized testing whether disagreement inside accepted reference
groups identifies unreliable admission groups automatically. It highlights the
People problem but **does not establish a general group-rejection rule**. The
AI-specific group is less extreme than several groups providing reviewed useful
routes. No group eligibility rule is adopted or added to HiGen.

The calculation is frozen before joining existing semantic judgments: normalize
each saved vector, take the median title cosine and median full-meaning cosine
over pairs from different source notes, then subtract the second from the first.
Exclude self-pairs and every same-note pair. A larger positive gap means titles
agree more strongly than meanings; it is not itself a semantic error label.
The reusable calculation is [reference_view_agreement.py](../reference_view_agreement.py).

All 628 fixed groups are measured: 157 in HR36, 130 in HR37, 301 in HR38, plus
40 existing HR35 Food/Arts controls. Each group has a cross-note comparison.
Group membership, meanings, admission scores and thresholds remain unchanged;
no outsider enters the measurement. Existing review outcomes are joined only
after the metrics are written and hashed. A supported root placement can be
triggered by a numerically unrelated group, so those associations do not label
an entire group as semantically correct or incorrect.

| Group | Title median | Meaning median | Gap | Existing reviewed witness |
|---|---:|---:|---:|---|
| HR38 C00006 fused-002 · People/Individuals | 0.9873 | 0.2839 | 0.7035 | Both valid people and wrong services/conduct |
| HR38 C00005 fused-009 · AI-specific topics | 0.7797 | 0.5533 | 0.2264 | Codex is valid; conventional graphics are not |
| HR36 C00001 fused-092 · Software features/functions/use | 0.9573 | 0.5802 | 0.3771 | Form submission |
| HR37 C00002 fused-034 · Notes/Notedeck/note-taking | 0.8979 | 0.3801 | 0.5178 | Nostr client releases; Unifans |

People's gap ranks fourth among HR38's 301 groups; the AI-specific group ranks
92nd. Other large gaps occur in Songs, Food, Meals, news destinations and software
groups. The larger-gap ordering would reject the useful software and content
routes above before rejecting the AI group. More generally, disabling the AI
group disables its valid Codex route as well as its wrong non-AI image routes;
group diagnostics cannot replace assessing an outsider's relation to that group.

Two **diagnostic counterfactuals**, not proposed cutoffs, quantify the cost:
disable all groups whose gap is at least the already-observed People gap, or
at least the already-observed AI-group gap. These values come from the failure
witnesses and must not be presented as reference-only calibrated rules.

| Original new-note proposals → remaining | People-gap diagnostic | AI-gap diagnostic |
|---|---:|---:|
| HR36 | 75 → 75 | 75 → 39 |
| HR37 | 92 → 92 | 92 → 45 |
| HR38 | 384 → 287 | 384 → 113 |

These are distinct proposed-note totals, not useful-coverage estimates. At the
AI-gap diagnostic, nine of 13 reviewed supported HR36 root placements and seven
of 12 in HR37 lose every passing group. The HR38 historical review loses 23
supported placements outright; six more lose their supported witness while
other, unreviewed selected entries remain. Its separate supplemental preview
review loses seven supported placements outright, with three more needing
alternate-witness review. Do not pool these differently selected cohorts or
count a surviving arbitrary heading as a verified useful route.

The narrower People-gap diagnostic removes 14 wrong historical HR38 placements
and six wrong supplemental placements, but also removes five and two supported
placements respectively. It remains a possible warning signal with a measured
tradeoff; this test supplies no automatic way to select that boundary. The AI
errors remain. No labels determine a new score, threshold or gate.

Evidence: `target/food-halves-v1/reference-view-agreement-v1/`. The frozen plan
pins 36 source files; `group-metrics.json` retains all measurements,
`reviewed-group-links.json` the exact saved judgments and passing groups, and
`monotone-gap-capacity.json` both counterfactuals with cohorts kept separate.
`final-verification.json` checks all source hashes, unchanged preview files,
and independent scalar arithmetic for both failure groups and useful controls.
Maximum target-check error is `4.45e-16`; nine relevant tests pass after the
initial missing-module failure. The prior 20-group scalar checks also pass.
All code and artifacts remain experimental. No new vectors, semantic judgments,
LLM calls, training, hierarchy changes or UI refresh occurred.

### Within-group admission score tradeoff

The user authorized comparing correct and wrong matches within the same group
to distinguish boundary problems from score-ordering problems. This descriptive
HR38 sweep keeps every other group's threshold fixed. It changes no actual
admission or hierarchy and does not select a threshold for deployment.

Freeze the earlier judgments before inspecting the scores: 12 AI-group entries
(one supported, ten wrong, one unresolved) and 39 People-group entries (nine
supported, 22 wrong, eight unresolved). Reuse the original review and supplemental
preview review, plus the earlier fixed People controls; deduplicate repeated
entry IDs and retain every judgment's provenance. Supported entries are the
reviewed useful witnesses; other headings in a useful note are not automatically
positive. Wrong root placements provide their selected wrong entries. No new
semantic labels are introduced, and unresolved cases remain separate.

People's nine supported witnesses include Patient advocacy through the root's
humane-treatment scope; it is not relabeled as a class of people. Four of the
nine already fail the original threshold, including Astronauts and Racing
drivers. Retaining currently passing witnesses must not hide those misses.

These are full-meaning group mean-support scores, not raw cosine similarities.
The existing thresholds are 0.065366 for the AI group and 0.011525 for People.

| Group | Entry | Existing assessment | Score |
|---|---|---|---:|
| AI | L04959 · Software icons | Wrong | 0.143399 |
| AI | L04960 · Figma | Wrong | 0.104740 |
| AI | L01833 · OpenAI Codex | Supported | 0.095769 |
| AI | L09409 · Self-portraits | Wrong | 0.083418 |
| People | L04535 · Audience reactions | Wrong | 0.027289 |
| People | L03937 · Spectators | Supported | 0.020622 |
| People | L07047 · Amazon Mechanical Turk | Wrong | 0.011799 |
| People | L03676 · Actors | Supported | 0.011669 |
| People | L04484 · Voice actors | Supported | 0.011617 |
| People | L03337 · Astronauts | Supported, already missed | 0.004233 |

Enumerate the current threshold and values immediately above every distinct
currently passing outsider score: 37 AI-group states and 315 People-group
states. Recompute group matches, note/root placements and distinct-note proposals
across all roots. Other entries, groups and roots can retain a placement even
when its match to this group disappears. Existing accepted memberships remain
fixed. These curves use labels to describe achievable tradeoffs only; they do
not calibrate an automatic boundary.

| Diagnostic point | Wrong entry/group matches removed | Currently passing useful group witnesses kept | Reviewed wrong root placements removed | Reviewed useful root placements kept |
|---|---:|---:|---:|---:|
| AI · retain Codex's group match | 8 / 10 | 1 / 1 | 6 / 7 | 3 / 3 |
| AI · remove all reviewed wrong group matches | 10 / 10 | 0 / 1 | 7 / 7 | 3 / 3 |
| People · retain all currently passing useful witnesses | 1 / 22 | 5 / 5 | 0 / 18 | 5 / 5 |
| People · intermediate tradeoff | 13 / 22 | 3 / 5 | 10 / 18 | 3 / 5 |
| People · remove all reviewed wrong group matches | 22 / 22 | 0 / 5 | 18 / 18 | 0 / 5 |

The AI result offers room for a more selective boundary without demanding
perfect score ordering: Codex outranks eight of ten wrong entries, but not
Software icons or Figma. Codex also passes **fused-004**, the AI-assistant group,
so removing its fused-009 match does not remove its valid root placement. At
the all-reviewed-wrong diagnostic, C00005 proposals fall from 51 to 26 notes;
the union across all roots remains 384 because the affected notes have other
root routes. These proposal counts do not certify all remaining routes.

People has a substantially worse tradeoff. The one wrong entry that can be
removed while keeping all five currently passing useful witnesses is Summaries;
Invitations from that same note still passes, so no reviewed wrong root placement
is fixed. The intermediate point removes ten wrong placements but loses the
Actors and Voice actors placements. Four previously missed positive controls
remain missed under every tightening. This identifies a score-ordering problem
in addition to any boundary choice; it is not a requirement for perfect precision.

Root-placement counts span the existing historical primary, historical root
supplement and supplemental preview cohorts. The evidence retains those cohorts
separately. These overlapping, selected agent judgments are not new human gold,
independent accuracy samples, or proof of reliability on unreviewed additions.
No numerical value in the table is proposed as an operational cutoff.

Evidence: `target/food-halves-v1/same-group-score-tradeoff-v1/`. Plan SHA256:
`67170c7dd7003faa080c1b9d419527cd36bde767eb284930867c46e5e2358d29`.
`panel-scores.json` preserves all 51 entries; both `*-threshold-sweep.json`
files retain every state and cohort outcome. `summary.json` records the full
tradeoffs, and `final-verification.json` checks independent note-membership
reconstruction, monotone sweeps and unchanged input/preview hashes. All 51
scores replay through the existing mean-support implementation and independent
scalar arithmetic within `5.56e-17`; 39 relevant scoring/boundary tests pass.
No new encodings, LLM calls, training, production code changes, thresholds,
semantic judgments, hierarchy changes or UI refresh occurred.

### Uniform combination of note and member bends

The user authorized combining the current boundary with the existing per-group
member-distribution bend, taking the stricter value everywhere, then replaying
HR36–38. This reproduces the desirable AI tightening automatically but does
not establish a generally preferable replacement for the current conservative
candidate. It loses known useful routes elsewhere and does not resolve People.
The combination remains experimental and is not activated in HiGen.

Implementation: [fixed_reference_combined_bend.py](../fixed_reference_combined_bend.py).
It calls the unchanged reference-note bend and unchanged group-member bend;
each group's threshold is their maximum. An unavailable current threshold stays
unavailable, and a missing group bend retains the current threshold. No new
constant, outsider score, semantic label or root-specific exception determines
the boundary. Existing accepted memberships, member statistics, meanings,
fusion groups, score kernel and source-note exclusion remain fixed.

All 18 own-root collections / 588 groups use the same rule. Exactly 374 group
boundaries rise. Current calibrations and query decisions replay exactly before
the change; every new proposal is a subset of the corresponding old proposal.
All boundaries are written and hashed before query outcomes or review labels
are evaluated. The test uses the original full-meaning score only.

| Corpus | Additional-note proposals: current → combined | Projected coverage: current → combined |
|---|---:|---:|
| HR36 · 1,000 notes | 75 → 58 | 75.8% → 74.1% |
| HR37 · 1,000 notes | 92 → 75 | 71.4% → 69.7% |
| HR38 · 2,000 notes | 384 → 340 | 85.6% → 83.4% |

Projected coverage means the original saved hierarchy's covered-note union plus
new proposals, deduplicated. Native hierarchies cover 683, 622 and 1,328 notes
respectively. Unclaimed notes above roots are excluded, as in the existing
viewer. These are hypothetical proposal totals, not certified useful coverage
or newly generated hierarchies. The saved HR38 preview remains unchanged.

The matched historical primary samples retain the earlier note/root judgments:

| Corpus | Previously useful sampled notes | Known useful route retained | No proposal remains | Alternate-witness review required |
|---|---:|---:|---:|---:|
| HR36 | 7 | 6 | 1 | 0 |
| HR37 | 7 | 7 | 0 | 0 |
| HR38 | 27 | 22 | 2 | 3 |

For HR36's separate three-note root supplement, only one of three useful notes
retains a route; two become unproposed. HR38's two supplemental notes both
retain a useful route despite losing some valid extra placements. Do not pool
these cohorts into a claimed accuracy rate.

| Historical primary root placements | Supported: retained / removed / alternate review | Wrong: before → after |
|---|---|---:|
| HR36 | 7 / 2 / 1, out of 10 | 0 → 0 |
| HR37 | 9 / 3 / 0, out of 12 | 1 → 0 |
| HR38 | 24 / 4 / 5, out of 33 | 15 → 13 |

Here removed means that root no longer receives the note at all; losing a
particular root does not necessarily lose the whole note's useful access.
Alternate review means the old useful witness no longer passes but other
selected entries remain; those entries are not silently promoted to positives.
Examples of definitely removed supported routes include Al Jazeera, Canada,
large language models, Nostr client releases, Hoses and Approval.

HR38's separately selected 33-placement preview inspection changes from 14
supported / 11 wrong / eight unresolved placements to ten supported / eight
wrong / six unresolved. Four supported placements disappear. These judgments
are provisional, and the supplement is not an independent accuracy estimate.

The target groups explain why the result is mixed:

- The AI-group boundary rises from **0.0653655 to 0.0843310** using only its
  accepted members. It retains Codex and rejects eight of ten reviewed wrong
  entry matches, removing six of seven reviewed wrong C00005 placements.
  Software icons and Figma still pass. The uniform rule also tightens other
  groups in C00005: it loses the legitimate Audience reactions communication
  route. The single-group sweep held those other groups fixed and therefore
  did not reveal this additional cost.
- The People-group boundary rises from **0.0115250 to 0.0117640**. Actors
  (0.0116690) and Voice actors (0.0116172) now fail, while Amazon Mechanical
  Turk (0.0117990) still passes. Summaries is rejected, but Invitations from
  that note still passes. Across the reviewed root placements, all 18 wrong
  C00006 routes remain and only three of five useful ones survive. Four useful
  fixed controls were already missed and remain missed.

This is not a requirement to eliminate every error. It shows a concrete
coverage/quality cost outside the successful AI example, with no reviewed
People-placement improvement. The assessment is to retain the existing
conservative candidate rather than replace it uniformly on this evidence.
No exception or hand-selected threshold is introduced to rescue the test.

Evidence: `target/food-halves-v1/combined-member-note-bend-v1/`. Frozen plan
SHA256: `081755b9345d20372efbe7c6f1cfe2fc030db37328942f6df5c0e102768efe3b`.
`calibrations.json` retains every old/new threshold and complete group bend;
`query-decisions.json` retains originally proposed entries and their surviving
groups. Coverage, root outcomes, whole-note cohorts, heading controls and fixed
AI/People controls remain separate files. Existing judgments are not changed.
Independent verification reconstructs all **588 thresholds** with exact rational
note masses and all **982,494 query/group comparisons**; maximum scalar threshold
error is `1.12e-16`. All input and preview hashes remain unchanged. The helper
first failed its missing-module test, then **50 relevant tests passed**.
No new encodings, LLM calls, training, semantic judgments, actual memberships,
hierarchy files or UI updates occurred.

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
is not a failure criterion for this variant. The lost reviewed omitted notes
and user controls quantify its material coverage tradeoff.

These observations are consistent with a mismatch between the two populations:
accepted members often closely resemble other definitions of the same topic,
whereas useful omitted entries can extend a root through a different entity,
activity or topic. A bend in existing-member scores is not automatically a
boundary separating useful new topics from wrong ones. The experiment does
not establish duplication as the sole cause or identify a proven replacement.

The approved fresh-data investigation is now complete on
[HR38](hierarchy-hr38-conservative-admission-v1.md), with admitted-note quality
and missed useful notes reported separately. No rule was tuned on that corpus.
Joint holdouts of repeated definitions remain a separate, unrun possible
diagnostic. Neither the findings nor that proposal activate an admission policy;
historical membership must not silently become new semantic gold.

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
