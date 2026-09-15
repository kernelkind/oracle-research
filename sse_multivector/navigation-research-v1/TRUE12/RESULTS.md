# TRUE12 — Can independent membership recover missing notes?

The old score cutoff recovers all nine clear missing notes, but also adds one unwanted note and five uncertain notes. TRUE's own Yes/No answers recover only one of the nine.

This is evidence that checking membership separately from HDBSCAN can recover useful content. It is not evidence that this TRUE configuration is a reliable final membership system. The existing hierarchy has not been changed.

## What was tested

Every original mask in the 100-note corpus was checked independently against two existing categories: **Coffee** and **Tea as a beverage**. The 945 masks produce 1,890 decisions. Identical model inputs were computed once, leaving 1,796 actual inputs; every original mask and source note remains represented.

TRUE received exactly this format:

```text
premise: {original mask fragments joined with spaces} hypothesis: This text is about {category title}.
```

No brackets or quotes were added. Original punctuation and whitespace were preserved. The model did not receive the full note, generated subject, HDBSCAN assignment, or expected answer.

Before inference, the primary assistant read every mask and saved the expected memberships. Those judgments identify 16 clear Coffee notes and four clear Tea notes. Coffee already contained nine of those notes through its existing hierarchy; Tea already contained two. Five other Coffee notes and one other Tea note were reserved as uncertain. These are recorded interpretations, not a uniquely correct ontology or new user approvals.

The primary test uses TRUE's complete generated Yes/No answer. After observing obvious misses, a separate diagnostic applied the **previously used strict score > 0.142 rule** to the same saved outputs. That cutoff was not fitted here, but its validity does not automatically transfer from category containment to mask membership.

## Missing notes recovered

| Decision rule | Coffee: seven missing clear notes | Tea: two missing clear notes | Unwanted new notes | Uncertain new notes |
| --- | ---: | ---: | ---: | ---: |
| TRUE's own Yes/No answer | 1 / 7 | 0 / 2 | 0 | 0 |
| Historical score cutoff | 7 / 7 | 2 / 2 | 1 | 5 |

The recovered Coffee notes are N018, N041, N043, N045, N058, N060 and N071. The recovered Tea notes are N072 and N073. Native answers recover only N060.

These are **additions**, not replacements for existing memberships. If applied additively, native answers would expand Coffee from nine notes to ten and leave Tea at two. The cutoff would expand Coffee to 22 notes: 16 clear matches, one unwanted match and five uncertain matches. Tea would contain all four clear notes because its original memberships remain preserved.

The distinction matters: using the classifier alone would retain only four of the 16 clear Coffee notes and none of the four Tea notes under native answers. The cutoff alone accepts all 16 Coffee notes but only three Tea notes; it misses the already-present N080. No existing note has actually been removed or added.

## N060: an unassigned mask recovers a coffee note

Complete original note, with V504 overlaid:

> ⟦Made⟧ my ⟦coffee with raw cream⟧ and a raw egg yolk ⟦today⟧ #coffeechain

Exact model input:

```text
premise: Made coffee with raw cream today hypothesis: This text is about Coffee.
```

Native answer: **Yes**. Score: **0.505581**.

HDBv2 left V504 unassigned. It put two other masks from this note in the Eggs group. TRUE12 therefore recovers the note for Coffee without incorrectly placing the entire Eggs category beneath Coffee.

This recovery is inconsistent across the note's coffee masks:

| Mask | Plain mask text | Native answer | Score |
| --- | --- | --- | ---: |
| V503 | Made coffee today | No | 0.364204 |
| V504 | Made coffee with raw cream today | Yes | 0.505581 |
| V505 | Made coffee with raw egg yolk today | No | 0.321178 |
| V506 | Made my coffee raw cream raw egg yolk today | No | 0.343970 |

All four pass the historical cutoff. A note belongs if at least one mask is accepted, so the native result is still a valid recovery through V504—not evidence that all its masks were classified correctly.

## N073: a mask in another coherent group recovers a tea note

Complete original note, with V672 overlaid:

> I just realized ⟦I've drank over a gallon of hot tea in less than 24 hours⟧. I wonder if that's bad for me 🤔

Exact model input:

```text
premise: I've drank over a gallon of hot tea in less than 24 hours hypothesis: This text is about Tea as a beverage.
```

Native answer: **No**. Score: **0.148712**, which passes the historical cutoff.

HDBv2 placed this note's three masks in the large-consumption group alongside chocolate consumption. Checking the tea masks individually can add N073 to Tea without bringing the chocolate note N016 with it. All N016 masks were rejected for Tea by both decision rules.

V673 also passes the cutoff at 0.168723. V674 narrowly misses it at 0.141385. Native answers reject all three. N072 is separately recovered through its sweet-tea-preparation mask V670, which HDBv2 left unassigned.

## Incorrect and uncertain additions

The unwanted note is **N065**, about a coffee shop's laptop restrictions, contemplated router-password changes, and changing venues. The pre-inference review applied the previously agreed distinction between coffee and unrelated activities at coffee shops.

The five uncertain notes are **N004, N005, N017, N024 and N038**. Each enters through coffeechain-tag evidence. N004 additionally has an incorrectly accepted rave-at-a-coffee-shop mask. The uncertain notes are not silently counted as correct or incorrect.

[All six notes, complete original text, inline highlights, individual masks, scores and reasoning](./ADDITIONS-TO-REVIEW.md).

There is an actual ordering problem, not just a high cutoff:

```text
premise: coffee hypothesis: This text is about Coffee.
```

V244 is a clear match. Native answer No; score **0.243593**.

```text
premise: Coffee shop “No laptops or tablets” on weekends what happens if you let hipsters get too successful hypothesis: This text is about Coffee.
```

V559 is outside Coffee under the above boundary. Native answer No; score **0.373953**. Any score cutoff admitting V244 also admits V559. Raising a single cutoff cannot perfectly repair Coffee membership in these outputs.

Tea's clearly relevant masks all score above its clearly irrelevant masks in this collection. That is a different result from Coffee; it does not establish a transferable Tea cutoff. The matcha-pie cases remain explicitly uncertain and were rejected by both tested rules.

## What this establishes—and what it does not

- Membership can recover notes that HDBSCAN left out of a destination, including both unassigned masks and masks assigned elsewhere. Neither example requires moving a whole HDBSCAN group.
- Native answers in this raw-mask format miss ordinary, explicit meanings. This is a failure of the tested membership configuration, not evidence that TRUE lacks the concept of coffee or tea.
- The old cutoff is much more useful here, but it introduces unwanted and uncertain evidence. Across all masks it accepts nine clearly wrong Coffee masks from two notes; counting only additional notes would hide some of those errors.
- The result does not establish transfer to other categories, especially categories whose names are not explicitly present in their masks. Two common beverage categories are a limited pilot.
- No prompt, cutoff, title, group or hierarchy was changed during the run. No new threshold was optimized from these judgments.

The next useful step is to review the six questionable additions before changing the classifier. Their exact evidence is now available; that review can distinguish genuine model mistakes from unsettled category boundaries. No further inference or hierarchy update has been started.

## Records

- [Judgments frozen before inference](./semantic-review-before-inference.json)
- [Primary native-answer analysis](./analysis.json) and [note memberships with evidence quality](./memberships.json)
- [Historical-cutoff diagnostic](./cutoff-diagnostic.json); reproducible by running `cutoff_diagnostic.py` from the repository root
- [Every mask decision with complete source note and exact model input](./comparison-details.json)
- [Frozen inputs](./inputs.json), [raw model outputs](./scores.jsonl), [execution](./execution.json), [model configuration](./config.json) and [completion hashes](./completion.json)
- [Verification](./verification.json)

The cached TRUE checkpoint ran locally on CPU, float32, four threads, batch size four. Inference took 41.4 minutes; the complete run took 42.0 minutes including loading and verification. Peak process RSS was 46.3 GiB, with a 60 GiB limit and swap disabled for the process. No paid compute or training was used. All 110 TRUE tests pass. Raw logits remain local; their hash is recorded rather than committing the large array.
