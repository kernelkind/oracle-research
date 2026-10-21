# Construction from existing subject descriptions

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

CAP03 shows that the saved subject text contains useful semantic information,
but turning it into unordered word sets does not produce a dependable hierarchy.
It also identifies a separate construction limitation: some clear multiword
subjects are present in the inputs but excluded by the candidate seed rule.

No new model was run. The baseline, source masks, SSE vectors and browser remain
unchanged. This is not a candidate ready for browsing.

## Controlled comparison

The [pre-run plan](SUBJECT-DESCRIPTION-CONSTRUCTION.md#cap03-study-design) changes only the text from which features are
extracted. Every distinct saved subject attached to a canonical mask remains a
separate input; no alternative is selected for favorable results. The 916 masks
produce 945 such records. Both runs use those same records and note owners.

The control extracts words and symbols from the original fragments. The changed
run extracts them from each saved subject. Both then use complete-input seeds,
single-feature closures, support from at least two distinct notes, the same
descriptor-extension/note-subset relation, and the same transitive reduction.

Mapping control rows back to canonical masks reproduces all CAP02 descriptions,
memberships and relations exactly. Alternative subjects do not inflate the number
of independent notes or get concatenated into invented compound meanings.

| Output | Mask text | Saved subject text |
|---|---:|---:|
| Candidates | 336 | 556 |
| Immediate links | 43 | 359 |
| Roots | 304 | 312 |
| Longest path, in links | 1 | 3 |

These are structural counts, not quality scores. Most added links involve
reporting language such as `the author` or individual function words.

## Useful semantic information is already available

The dinner/storm confusion disappears from the shared-word candidates:

- V052: ⟦dinner⟧ ⟦Lamb with steamed seasoned broccoli and baby potatoes really hit the spot⟧
  becomes “The author found the dinner of lamb, steamed seasoned broccoli, and
  baby potatoes particularly satisfying.”
- V304: ⟦Next⟧ ⟦storms look like they will hit⟧ ⟦grilling out dinner⟧
  becomes “Upcoming storms threaten to interfere with grilling dinner outdoors.”

The original `dinner + hit` candidate is absent. Dinner remains a reasonable
shared broader topic; removal of the accidental `hit` conjunction is not proof
that the two notes must be separated under every possible category.

Food coverage grows from 15 to 28 notes. All 26 newly matched subject records
were checked against their masks and full originals. Concrete additions include:

- N019 / V133: ⟦brisket⟧ → “Brisket as food.”
- N067 / V579: ⟦cheesecake⟧ → “Food.”
- N013 / V100: ⟦stock pots rolling⟧ ⟦chicken stock⟧ ⟦pressure can⟧ ⟦store in the pantry⟧
  → “Pressure-canning homemade chicken stock for pantry storage is a form of food preservation.”

These additions are not explainable by literal occurrence of the word `food` in
the masks. They illustrate useful existing abstraction, not exhaustive Food
membership or verified generalization to new data. Some inputs also carry other
subjects, and bare hashtags remain an inherited scope issue.

Two new local refinements are supported by their child evidence:

| Parent → child | Child notes | Evidence |
|---|---|---|
| Food → Food preservation | N013, N100 | Chicken-stock canning/storage; a vacuum sealer and food-preservation hashtag. |
| Food → Concerns about harmful food | N031, N032 | Pesticides/chemicals in supermarket food; processed food being bad for the author. |

These readable descriptions explain the feature sets; they were not supplied
to the construction algorithm. They do not certify the whole parent membership
or establish that this is the only valid organization.

## Better text can still lose its meaning during construction

### A shared word need not describe the same thing

The new `coffee + more` child contains N035 and N065:

- N035 / V277: ⟦More coffee⟧ → “More coffee.”
- N065 / V564: ⟦Coffee shop⟧ ⟦“No laptops or tablets” rule on weekends⟧
  ⟦changing their router/ap passwords so they could experience the true freedom from internet⟧
  → “The author contrasts the coffee shop's weekend ban on laptops and tablets
  with the more complete disconnection that losing internet access would impose
  on the people running it.”

In the second subject, `more` qualifies internet disconnection, not coffee.
That relationship is explicit in the subject text and discarded by the word-set
representation. Interpreting the child as wanting or having more coffee would
therefore be incorrect. This diagnoses a loss after generation, not an extractor
failure and not proof that the notes share no conceivable broader theme.

The coffee-experience concern also remains unresolved. A new seven-word
conjunction is seeded by `change`: V561 changes router passwords; V858 challenges
others to change an opinion about decaf drinkers. More shared words do not
establish the same narrower coffee experience. The audit leaves alternative
coarse interpretations open rather than declaring this an unconditional error.

### Clear combinations may never become candidates

Ten notes have generated subjects containing both `good` and `morning`:

N005, N017, N040, N058, N064, N071, N089, N092, N095, N099.

Examples include:

- V310: ⟦GM⟧ ⟦siamstr⟧ → “A good-morning greeting to the Siamstr community.”
- V120: ⟦Good morning⟧ → “The author wishes readers a good morning.”
- V824: ⟦Good morning nostr⟧ → “Wishing the Nostr community a good morning.”

The shared-feature closure of `good + morning` is `a + good + morning` and
contains all ten notes. But the algorithm never seeds this pair. Neither an
individual word's closure nor a complete saved subject supplies that candidate.
Its existing `greeting` seed instead produces seven notes and omits N017, N092
and N095, whose descriptions use “wishes” or “wishing.”

This is not missing model knowledge about greetings. The relevant common words
already exist in the inputs. It is a demonstrated limitation of the bounded
candidate family. The ten-note combination is a diagnostic, not an inserted node.

Two old useful candidates disappear for the same identifiable reason:

| Missing combination | Still-supported notes | Why individual seeds no longer recover it |
|---|---|---|
| Processed food | N032, N069 | `processed` now also occurs in N100's description of processing beef; its closure is no longer `food + processed`. |
| Sea salt | N046, N063 | `sea` also occurs in a separate sea-and-land interpretation of N054; no complete subject is just the sea-salt combination. |

Computing the conjunction supports directly still recovers those note pairs.
This does not validate every possible word conjunction or mandate these exact
categories. It shows why a correct and useful combination can be absent without
its meaning being missing from the input.

### More depth can be only wording differences

The three-link Nostr path successively adds `growing`, `community`, then
`network` and `and`. Its narrowed masks are versions of the same `#grownostr`
evidence. The additional words do not establish progressively narrower subjects.

Two Carnivore-diet children differ by the article `a` and contain exactly the
same three notes. Two social-media siblings likewise have identical note sets.
These would need deduplication in navigation; they are not useful distinctions
merely because the formal descriptors differ.

The Food-preservation child omits N022 even though its source says:

> This year’s beets. Vac sealed and ready for the freezer. Not too bad for a 4x4 raised bed. 5 meals of sides in a pinch. I am looking forward to having more garden space but this is good while we are still in a half acre lot in town.

V149's subject correctly describes preserving garden-grown beets by freezing,
but lacks the word `food`. The parent `preservation` includes it; its child
`food + preservation` does not. Calling that a useful narrowing would hide a
membership omission. Bread notes without a generated Food description are
similarly not automatically connected to Food.

## Audit scope

The complete edge inventory and assessments (`./CAP03/edge-audit.json`) preserve
all 359 links. For 308, the parent descriptor itself supplies no browsing subject
beyond function words or generic reporting language. That is a descriptor
inspection, not a semantic verdict on every child.

For the other 51 links, every child input was inspected with its exact fragments
and full original: 132 subject records from 41 notes. Additional inspection
covered all new Food and Coffee matches and the diagnostics above. Twenty-two
links have plausible local refinements, including old successes and overlapping
alternatives; that is not 22 new or complete successful browsing paths. Remaining
links include unresolved scope, different word attachments, and wording-only
narrowing. No overall accuracy or exhaustive category-coverage rate is reported.

All originals and fragments are stored in the result's input records (`./CAP03/result.json`).
The same file contains every candidate, membership, seed and relation for both
runs. Audit annotations never alter those machine outputs. Root-only candidates
and every parent-only member have not been exhaustively semantically certified.

## Decision

The follow-up [CAP04 order/adjacency diagnostic](./ORDERED-PHRASE-CANDIDATES.md)
recovers the omitted combinations and establishes a limit: adjacency removes
some false combinations but also loses valid dispersed subjects. Its complete
inventory and source review refine the candidate-construction question below.

Do not add another context-extraction model merely to repair meanings already
expressed correctly in the saved subjects. Do not adopt subject-word closure as
the browser either. It provides useful broad abstractions in some cases, retains
attachment problems, and exposes a separate candidate-coverage limit.

Before selecting a parser, investigate candidate construction that can retain
explicit shared multiword descriptions without manufacturing hundreds of
grammatical distinctions. Use the demonstrated omitted combinations as diagnostic
witnesses, not as a hand-specified taxonomy. Check new false combinations and
omissions across the collection. A more complete candidate family cannot by
itself fix the `more coffee` attachment problem; that requires retaining meaning
or rejecting unsupported descriptions at a separate stage.

LLooM's distinction between per-example summaries and synthesized shared concepts
is relevant here, but its LLM membership scoring is not implemented or validated
by this run. Its optional synthesis/generalization pipeline is not evidence that
our current word-set hierarchy is semantically valid.[^1]

## Reproduction

From the repository root, choose an output directory that does not exist:

```sh
python3 sse_multivector/subject_description_construction.py \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --baseline sse_multivector/navigation-research-v1/CAP02-result.json \
  --output /tmp/cap03-replay-new
```

Both runs completed locally with standard-library Python and no model inference.
A second production run reproduced `result.json` byte-for-byte. The record pins
input/code hashes and Unicode version; its `source/` directory preserves the
runner and construction helpers. Thirty-five relevant tests pass, including
control equivalence, separate alternatives, same-note support and previous
construction regressions. The new test first failed because the comparison
module did not exist. No approved test was weakened or replaced.

## Sources

[^1]: Lam et al. (2024), [Concept Induction: Analyzing Unstructured Text with
High-Level Concepts Using LLooM](https://arxiv.org/html/2404.12259v1), sections
3.1.1–3.1.4. Method fit and limitations are discussed in the pre-run plan.

## CAP03 study design

### Question

Can the already-generated description of each mask improve category construction
without adding a parser, another generation step, or a category-relation model?
CAP02 used literal mask words as attributes. CSA01 established that word senses
alone would not supply all the missing phrase meanings. Before adding a new
component, test the semantic descriptions already present in the frozen evidence.

This is a representation control, not permission to replace source evidence with
generated prose. Category judgments still require the masks and complete notes.
GDR02 used a seed subject as a description of an entire group. Here each subject
describes only its own mask; shared descriptions are constructed mechanically.

### Fixed and changed inputs

Use all GDC09 evidence, with no hand-selected subjects or manual corrections.
Each distinct saved subject for a canonical mask becomes a separate input record.
Keep its canonical row, note, aliases, exact subject, fragments and full original.
Do not concatenate alternative subjects into a new compound description.

Run the same CAP02 construction twice on these identical records:

- Control: features extracted from the original mask fragments.
- Changed input: features extracted from the corresponding saved subject string.

Keep word/symbol extraction, recurrence in at least two distinct notes, complete
input seeds, single-feature closures, descriptor extension, strict note narrowing,
and transitive reduction unchanged. Repeated aliases do not provide extra notes.
Verify that mapping control memberships back to canonical rows reproduces CAP02
exactly. No stemming, stopword list, score cutoff, learned classifier or manual
category is added. Record every subject alternative rather than choosing a best one.

### Hypothesis and competing explanations

The subject representation removes some misleading shared-word descriptions and
creates source-supported parent/child paths or restores relevant memberships that
the mask-word control misses. The existing dinner/storm, coffee-experience, bread
and greeting examples are diagnostics, not an exhaustive or uniquely correct taxonomy.

Competing explanations: apparent gains come from unsupported generated meaning;
generic summary wording creates spurious commonalities; useful distinctions are
still lost when prose is reduced to unordered words; paraphrases create new lexical
omissions; the bounded candidate family misses useful combinations in either input.

Inspect all proposed links and every source mask/full note supporting links judged
potentially substantive. Record excluded relevant examples where evidence exists.
Classify grammatical constraints separately, without using that classification to
silently modify the output. Preserve ambiguous cases instead of forcing pass/fail.
Formal containment and additional depth are not semantic evidence by themselves.

Could success occur without the needed capability? Yes: a generated term might
describe the note but not its mask, or repeated reporting language might create an
apparently narrower group. Audit source grounding and scope before counting gains.
Could failure be unrelated to the representation? Yes: closure limits and literal
matching remain. Confirm the unchanged control and inspect which stage loses a
meaning instead of declaring the subject model or whole architecture invalid.

Would either outcome change the next decision? If this removes meaningful errors
or supplies defensible new paths, reuse existing descriptions for further structure
tests rather than assume another context extractor is required. If a meaning is
present in the subject but lost by word features, test structured features next.
If it is absent or unsupported in the saved subject, attribute that limitation to
the representation input and do not ask a parser to repair it. More than one
outcome may occur. Do not adopt a browser on the strength of a few examples.

### Literature fit

LLooM separates short textual summaries, clustered examples, synthesized concepts,
and membership scoring. Its synthesis may identify a subset of a cluster rather
than invent a description covering every item. This supports keeping per-example
descriptions separate from group descriptions. Its explicit full-data scoring
remains a different, costly operation; it does not validate our inclusion rule.
The paper also notes that its implementation does not verify summary fidelity.
This experiment reuses existing descriptions and deterministic construction; it
does not reproduce LLooM or establish its model performance here.[^cap03-study-design-1]

### Evidence and decision criteria

Save exact inputs, both outputs, differences, code/input hashes, complete link
inventory and semantic assessment under CAP03. Keep GDC09, previous experiments,
prompts, masks, SSE vectors and the browser unchanged. No new model calls, model
downloads or paid compute are required. No TUI packaging before goal wrap-up.

[^cap03-study-design-1]: Lam et al. (2024), [Concept Induction: Analyzing Unstructured Text with
High-Level Concepts Using LLooM](https://arxiv.org/html/2404.12259v1), sections
3.1.1–3.1.4. These method and limitation sections were read; this experiment does
not borrow a quantitative performance claim from the paper.
