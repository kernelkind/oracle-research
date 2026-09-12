# Source meanings and paired refinements

USC01 automatically constructs a useful local Cooking → Cooking with meat
destination. It also exposes an incorrect construction assumption: requiring
two different word occurrences can remove notes without adding a different
subject. The comparison supports keeping semantic combinations under
investigation, not adopting this hierarchy or requiring distinct word matches.

## What changed

The inputs are all fifteen frozen descriptions from thirteen notes, with all
USM02 assignments retained: 134 word occurrences, 128 nonempty highest matches.
No masks, descriptions, senses, or dictionary entries were hand-corrected.

The baseline constructs each assigned meaning and its WordNet ancestors. The
changed condition additionally combines two differently assigned word occurrences
from the same description, then broadens either meaning using that same order.
It does not combine separate descriptions, even when they belong to one note.
A pair asserts co-presence, not an ingredient, causal, or action-object relation.

The [pre-run plan](./USC01-PLAN.md) records the hypothesis, alternatives, method
fit, and decision. [Complete notes with their original inline masks and all word
assignments](./USM02/SOURCE-RESULTS.md) supply the source evidence. Exact candidate
memberships, source witnesses and links are in [the construction result](./USC01/construction/result.json).

| Construction | Single concepts only | With pairs |
| --- | ---: | ---: |
| Literal patterns | 102 | 625 |
| Literal recurring note sets | 11 | 11 |
| Generalized patterns | 301 | 10,283 |
| Generalized recurring note sets | 45 | 132 |

These are inventory counts, not useful-category or accuracy counts. The changed
condition has 592 source pairs and 1,229 new generalized patterns containing
at least two notes. Of those, 202 have no further same-note-set refinement in
the constructed graph. Those 202 are the complete generalized semantic-audit
scope, not a hand-selected list of successful categories.

Two independent review partitions cover every one of those 202 patterns and
all 2,504 saved witnesses: [first half](./USC01/semantic-audit-a.json),
[second half](./USC01/semantic-audit-b.json). Their judgments were reviewed
against the source records. Broad, unexpected and same-note-set meanings are
not automatically failures; unsupported witnesses and missing notes are kept
separate from whether the resulting category could be useful.

## A useful new distinction

Cooking, `G151a03e04828a39d19ef`, contains N039, N047, N085 and N096. Cooking
with meat, `Gf87b69658e35b3a3755b`, contains N085 and N096. That two-note set
does not exist in the singleton baseline.

N085's original selected text is ⟦Brisket on the smoker⟧. Its unchanged
description is “Cooking brisket on a smoker.” The automatic cooking and brisket
meanings support the pair; brisket reaches meat through the dictionary order.
The wrong tobacco-user meaning assigned to smoker does not supply this witness.

N096's original recipe includes ⟦Gently fry beef⟧. Its description contains
“gently frying beef”; the assigned frying and beef meanings independently reach
cooking and meat. The broader Cooking destination also contains bread baking
and storm-threatened grilling, whose masks do not establish a meat restriction.

This is a supported local narrowing, not proof of complete meat-cooking coverage.
For example, N026's source includes preparing tomatoes and making chicken stock,
but its operation is assigned a verb whose lexical ancestry does not reach the
Cooking noun. Its absence starts before pair construction. No event-role
recognition is demonstrated merely because these two retained examples really
do involve cooking meat.

A second, weaker positive is `Gb9630c1a640a2fa769fc`, Change plus Flavoring,
containing N089 and N096. Its witnesses combine salt with mixing and basil or
sauce with frying. Both masks support food transformation alongside seasoning,
and this is a new subset of the broader Change destination. It does not prove
that a particular seasoning is itself fried, or recover every seasoning-related
activity expressed with another grammatical form. Cooking with meat remains
the cleaner demonstration.

## A smaller set that is not a narrower subject

Cooking → Act plus Cooking, `G43e4038818dfd62d5bc8`, keeps only N039 and N047.
The frozen dictionary already makes Act an ancestor of Cooking. Therefore the
additional Act label supplies no independent topical condition.

The actual source matches explain the smaller membership:

| Note | Cooking evidence | Separate Act evidence required by the constructor | Result |
| --- | --- | --- | --- |
| N039 | grilling | parade | Kept |
| N047 | baking, word 10 | baking, word 0 | Kept |
| N085 | cooking | None | Lost |
| N096 | frying | None | Lost |

N047 qualifies by describing baking twice. N085's cooking and N096's frying
already supply Act through their own ancestry, but the constructor refuses to
reuse those occurrences. This is an occurrence-count restriction, not a useful
distinction in what the notes discuss. It also explains why merely checking
child-note containment would wrongly approve the transition.

Among the 202 audited generalized pairs, 42 have identical endpoints or one
endpoint already entailed by the other under the frozen order. Six have identical
endpoints. Nineteen of the 42 return fewer notes than the narrower endpoint's
singleton. These counts isolate a structural mechanism; they do not classify
all broad or surprising categories as invalid.

Cooking plus Food is less clean evidence of the same issue. It drops N039,
whose dinner was assigned a gathering sense. Its Food endpoint specifically
means solid food, and the dictionary does not encode cooking's food relationship
as an is-a ancestor. Source interpretation and missing semantic relations are
additional explanations. It should not replace the cleaner Act/Cooking control.

## Other complete paths and unresolved errors

The following paths are present in the automatic graph. Titles here explain
dictionary meanings for analysis; they are not generated or approved UI labels.
Their exact node IDs and source witnesses are retained in the result.

| Path | Notes returned at successive levels | Interpretation |
| --- | --- | --- |
| Solid food → Produce → Vegetables → Solanaceous vegetables → Tomatoes | 8 → 3 → 3 → 2 → 2 | Useful material narrowing already exists in the singleton baseline. Pairs receive no credit for it. Repeated note sets still create low-value levels. |
| Cooking → Cooking with meat | 4 → 2 | Supported new local distinction, with incomplete broader coverage described above. |
| Solid food → Cooking plus solid food → Cooking with meat | 8 → 3 → 2 | Contains valid examples, but the middle choice's loss of storm-grilling is not established as meaningful narrowing. |
| Preservation → Solid food plus preservation | 2 → 1 | Loses the beet note; not a demonstrated useful narrowing. |
| Meat → Commercial enterprise plus meat | 6 → 2 | The two retained source derivations are wrong. |

Preservation contains N013's chicken stock and N022's beets. N022's preservation
description assigns beets the plant sense rather than the edible-root sense.
The root sense occurs in a different description, which pairing intentionally
does not cross. Changing the distinct-word requirement alone cannot repair this
missing food/preservation membership.

The commercial-meat pair, `G16ac554cb25e5199674f`, combines N013's pantry
storage, wrongly interpreted as commercial storage, with N022's harvested crop
and side dishes. The crop reaches commercial industry through the lexical
order, while side becomes half an animal carcass. Neither personal food note
supports that commercial-meat category. This separates source-selection errors
from a broader-order problem: even a plausible crop meaning can have an
inappropriate industrial ancestor for the original garden context.

The meat-cut singleton likewise wrongly contains N022 alongside genuine steak
and brisket notes. The older bread/steak preparation activity grouping is lost
because preparation means a formulated substance in those descriptions. These
are retained input errors, not failures introduced by pairing.

The three literal recurring pairs are fully accounted for: chicken/broth and
cooking-verb/tomato are source-supported but repeat singleton note sets;
dishware/professional-writer relies on unsupported paid-writer meanings and a
wrong dishware interpretation of beet sides. Different descriptions can be
valid while returning the same notes; equal sets do not prove synonymy.

## What the evidence changes

There is a reason to keep combinations: cooking and meat create a useful local
choice without hand-filtering outputs. There is also a reason to change what a
combination means. A subject already entailed by an occurrence should not need
an additional word merely to count as present. RHOG explicitly distinguishes
subsumption with and without a distinct-object constraint; that constraint is
an extra modeling choice, not a requirement of broader/narrower reasoning.[^1]

The next justified question is whether same-description semantic conjunction,
allowing one occurrence to support both concepts, removes the artificial
restrictions while retaining genuinely distinct refinements. It must preserve
source assignments and test changed memberships and incorrect additions, not
only reduce node counts. Redundant ancestor combinations can be identified
from semantic entailment, not from coincidentally equal note sets. This remains
a proposed controlled comparison, not an implemented repair.

Even success there would leave source errors, incomplete lexical relationships,
description coverage and category selection unresolved. Fifteen targeted
descriptions cannot establish a complete hierarchy for all 100 notes. Neither
this graph nor hand-edited labels have been installed in the browser.

## Reproducibility

All 102 literal and 301 generalized baseline singleton patterns and witnesses
remain unchanged. Both constructed conditions are acyclic; every link has
contained source-row and note support. A separate production-CLI run reproduced
`result.json`, `inputs.json`, `graphs.json` and `lexicon.json` byte-for-byte.
The original executed source and plan remain snapshotted with the run.

Construction took about 2.9 seconds after setup. The replay's own process
high-water memory was 504,244 KiB, about 492 MiB. The original recorded
`ru_maxrss` value includes inherited pre-exec high-water history on this launcher
and is not an isolated measurement of the Python process. Historical files are
preserved; current runners measure `/proc/self/status` `VmHWM` instead. Neither
run encoded text, downloaded a model, or used paid resources.

[Verification records](./USC01/verification.json) preserve exact hashes, the
42 overlapping-endpoint cases, source witnesses, replay checks and audit
coverage. Twelve LMMS tests, three occurrence-construction tests and 61 existing
semantic-construction tests pass. This verifies the implementation and saved
evidence, not the correctness of every proposed category.

[^1]: Santiago Ontañón, [RHOG: A Refinement-Operator Library for Directed Labeled Graphs](https://arxiv.org/pdf/1604.06954), section 1.3.1 and Figure 3, arXiv v2. It formalizes graph mappings under a supplied label order; it does not validate the source meanings or our browsing objective.
