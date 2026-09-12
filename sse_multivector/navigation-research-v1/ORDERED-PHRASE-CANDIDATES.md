# Word order and adjacency in category candidates

CAP04 recovers useful categories omitted by CAP03 and removes one demonstrated
false word attachment. It also shows why neither word order nor adjacency is a
sufficient replacement for understanding a shared subject.

The practical result is a separation of responsibilities: phrase recurrence can
propose candidates, but does not establish that a phrase is a complete subject,
that differently worded phrases are different subjects, or that all relevant
notes have been included. No new hierarchy or browser is adopted.

## Experiment

The [pre-run plan](./CAP04-PLAN.md) fixes all 945 saved subject records and their
original notes/masks. Every candidate requires at least two distinct notes;
repeated aliases or subjects from one note cannot supply that support.

For each pair of distinct tokens, the control accepts their co-occurrence
anywhere in one subject. The second version also requires their order. The third
requires adjacency. All three use the same case-folded word/symbol features as
CAP03, now retaining token positions. Punctuation remains ignored: this is not
syntactic parsing. No phrase is formed across separate subject records.

| Candidate family | Recurrent patterns |
|---|---:|
| Unordered pairs | 2,647 |
| Ordered pairs, any gap | 2,725 |
| Adjacent pairs | 362 |

The ordered count can be larger because the two orders are separate candidates.
For each fixed order its support is contained in the unordered support; adjacent
support is contained in ordered support. These invariants were checked on every
pattern before filtering by distinct-note support. Counts are not quality scores.

## Useful categories become available

All three families recover the same source-supported memberships for:

| Shared expression | Notes | CAP03 candidate with this note set? |
|---|---|---|
| Good morning | N005, N017, N040, N058, N064, N071, N089, N092, N095, N099 | No |
| Processed food | N032, N069 | No |
| Sea salt | N046, N063 | No |

This confirms CAP03's candidate-family limitation. It is not new evidence that
these words or meanings were understood: they were already in the saved inputs.
The old seed rule did not offer their combinations.

The wider source review found other useful candidates absent as note sets in
CAP03: coffee beans (grinding and roasting), hot tea (wanting and consuming it),
ice cream (a joke and a discussion of eating it), and being very tired. These
are compatible subjects despite differing actions, attitudes or claims. They
are not required parts of a uniquely correct taxonomy.

Other plausible groups, such as smoking brisket and the circumstances upon
waking, already had equivalent CAP03 memberships. They are retained evidence,
not newly discovered improvements. Tag-derived coffee/social-media groups also
remain; their recurrence does not establish deeper semantic grouping.

## Order removes one false connection, not every attachment problem

N035's original is:

> More coffee in cool places https://image.nostr.build/f09d0a87aad1f999f48a1c3ff1ce4ea08db05749888f258359c12719943797ad.jpg

V277 selects ⟦More coffee⟧ and its saved subject is “More coffee.” Two overlapping
masks from this same note also put `more` before `coffee`.

N065's original is:

> Coffee shop I liked now has a “No laptops or tablets” rule on weekends. This is what happens if you let hipsters get too successful. Felt like changing their router/ap passwords so they could experience the true freedom from internet, but I simply went to another coffee shop and will remove this one from rotation. Personal growth on display.

V564 selects ⟦Coffee shop⟧ ⟦“No laptops or tablets” rule on weekends⟧
⟦changing their router/ap passwords so they could experience the true freedom from internet⟧.
Its saved subject correctly contrasts the ban with **more complete disconnection**.
Here `coffee` precedes `more`, and `more` does not modify coffee.

Unordered matching joins the two notes. Ordered matching separates them, leaving
neither orientation supported by two notes. This specific error disappears.

But N065/V561 and N094's decaf masks retain `coffee` before `experience` in all
six saved subjects. N094 describes experiencing coffee's flavour; N065 describes
making coffee-shop operators experience losing internet access. Order alone
does not identify what is being experienced. Adjacency removes that pattern, but
this is not proof that all broader connections between the notes are invalid.

## Adjacency also discards a valid shared subject

N037 explicitly lists rosemary among the ingredients of sourdough bread.
V290 selects ⟦rosemary⟧ ⟦sourdough bread⟧. Its subject is:

> Rosemary in sourdough bread.

N072 describes making Irish soda bread and adding rosemary and cranberries.
V665 selects ⟦Irish soda bread⟧ ⟦I added fresh rosemary and cranberries⟧.
Its subject is:

> The author added fresh rosemary and cranberries to the Irish soda bread.

Both originals support bread containing rosemary. Unordered matching and
forward order preserve both notes. Adjacency supplies no recurrent rosemary/bread
pattern in either order. The words are separated even though the relationship
is explicit. A longer strictly contiguous phrase cannot recover this common
combination either: there is no shared intervening phrase.

Ordering loses one reordered N037 subject record, but other records preserve
that note's membership. That row-level change is **not** counted as missing note
discovery. Adjacency, in contrast, loses the shared candidate entirely.

## Remaining construction problems

**Repetition does not identify a subject.** The largest adjacent pattern is
`the author`, with 254 records from 36 notes. Other frequent patterns include
`of the` and `in the`. `themed social` cuts across a longer expression instead
of providing a complete description. No frequency cutoff or semantic accuracy
claim was made from this inventory.

**Different note sets need not mean different subjects.** `good morning` selects
ten notes while `morning greeting` selects seven of the same notes. The other
three say “wishes” or “wishing” rather than “greeting” in their saved subjects.
Their original masks still greet in the morning. The seven-note set is not
therefore a meaningfully narrower category. Removing only identical note sets
would leave this distinction unresolved.

**Exact matching still misses relevant notes.** `food preservation` retains
N013 and N100 but not N022's beet freezing. That saved subject describes
preservation without the literal word `food`. CAP04 does not repair this earlier
membership omission, nor connect every food to Food.

## What changes next

Do not extend pair enumeration or tune a recurrence threshold as if either would
solve semantic construction. The stronger hypothesis—that adjacency removes
false connections while retaining the demonstrated shared meanings—is contradicted
by the rosemary/bread example. The narrower claim that it supplies useful local
candidate evidence is supported.

The next investigation needs to address **complete, context-grounded subject
expressions**, including relationships across gaps and equivalent descriptions
with different wording. Those are different requirements: syntax might preserve
an attachment without recognizing two paraphrases. A parser or learned model
should only be selected after its native inputs and objective are checked against
the particular requirement being tested. The follow-up
[PPR01 description-embedding comparison](./PHRASE-DESCRIPTION-NEIGHBORHOODS.md)
finds useful gap/attachment evidence in the base model, but does not establish
equivalence, containment or a reliable membership rule.

A plausible complete method would propose grounded descriptions, reconcile
equivalent meanings, establish broader/narrower relations, recover membership,
and then select useful navigation choices. CAP04 supplies evidence for only the
first component and a boundary on its sufficiency. The relations and membership
steps remain unproven; writing that pipeline is not evidence that it works.
The earlier classifier failures still apply to their tested configurations.

## Literature implications

AutoPhrase explicitly separates raw n-gram candidates from a learned quality
estimate. Its Wikipedia-derived training and large-corpus statistics make it
relevant to candidate quality, but its experiments do not validate transfer to
this small set of generated subjects. We did not run it.[^1]

TopMine's contiguous phrase construction is pertinent to the order/adjacency
control. Its corpus-association score and subsequent topic model do not establish
semantic equivalence or broader/narrower relationships for our notes.[^2]

Béchet et al. use gap constraints and closed patterns, followed by expert
validation for their linguistic-pattern task. Their result supports keeping
pattern generation separate from validation, not assuming closure eliminates
non-semantic candidates. Our comparison is not a reproduction of their
French-language extraction experiment.[^3]

## Evidence and verification

[The complete result](./CAP04/result.json) contains every pattern, membership,
token position, saved subject, exact source mask and full original note.
[The audit](./CAP04/audit.json) inventories all 362 adjacent patterns and records
full-source review of 29 adjacent patterns plus the three attachment/gap
diagnostics: 154 distinct subject records from 47 notes. The remaining patterns
are not certified; no overall precision, recall or full-hierarchy score is claimed.

The three new tests failed before implementation because the construction module
did not exist. All 38 relevant tests now pass. Production runs to two independent
directories produced byte-identical results. Token features equal CAP03's for
every input, and all input records remain identical. Code snapshots and hashes
are saved under `CAP04/source/`. No new model, download or paid compute was used.

Reproduce from the repository root using an unused output path:

```sh
python3 sse_multivector/subject_pattern_candidates.py \
  --input sse_multivector/navigation-research-v1/CAP03/result.json \
  --output /tmp/cap04-replay-new
```

## Sources

[^1]: Shang et al. (2017), [Automated Phrase Mining from Massive Text Corpora](https://arxiv.org/html/1702.04457), sections 3–5.3.
[^2]: El-Kishky et al. (2014), [Scalable Topical Phrase Mining from Text Corpora](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/vldb15ToPMine.pdf), sections 2–5.
[^3]: Béchet et al. (2012), [Discovering Linguistic Patterns Using Sequence Mining](https://cremilleux.users.greyc.fr/papers/CICLing12final.pdf), sections 1–3.4.
