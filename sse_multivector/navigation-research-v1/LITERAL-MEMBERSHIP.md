# Explicit mask evidence and missing notes

NMR03 finds four notes outside the existing broad Coffee destination and two
outside Bitcoin, using only subjects already written in their masks. It does not
change the hierarchy. Literal matching remains a diagnostic, not an adopted
semantic membership rule.

## Question and mechanism

The previous membership rules could miss explicit coffee evidence because its
nearest vectors expressed other relationships. This experiment asks whether
separating a category's stated subject from its original tree membership exposes
concrete omissions. Original membership is neither a complete answer nor a set
of negative labels for everything outside it.

Formal concept analysis pairs shared attributes with **all** objects possessing
those attributes. Its subset ordering is useful only to the extent that the
attributes represent meaningful distinctions.[^1] Cimiano, Hotho and Staab apply
this to corpus-derived syntactic dependencies, not literal keyword navigation.
They explicitly warn about accidental corpus associations. Their attribute
propagation between similar terms worsened the reported hierarchy F-measure in
both domains for all four tested similarity measures. Consequently this test
does not assume that spreading attributes to nearest neighbors is a repair.[^2]

**Hypothesis:** If several masks identify exactly the same explicit subject,
other masks containing that subject can recover relevant notes outside the
original groups without requiring another geometric merge. Shared wording alone
may still be ambiguous; every proposed addition needs inspection.

The seeds are generated, not handpicked:

1. Take an existing GDC09 category with at least two distinct source notes.
2. Require every canonical mask in it to have exactly the same nonempty set of
   words. A shared intersection of otherwise different masks is insufficient.
3. Combine seed categories with the same word set.
4. Find every canonical mask anywhere in the frozen corpus containing all those
   words. Other masks from the same note do not automatically join.

Words are casefolded Unicode words. Function words and numbers remain. There is
no stemming, stoplist, synonym expansion, full-note keyword search, generated
label, or embedding change. Word order, punctuation and symbols are not modeled.
`coffee` does not match `coffeechain` or `coffeehouse`. Seed discovery never
repeats using newly admitted members. An inverted word index implements matching;
the method does not enumerate an exponential concept lattice.

This is an exploratory test, not a blind holdout. The corpus and some failures
were already inspected. The code has no topic, note-ID or category-ID exceptions.

## Complete counts

| Seed words | Seed categories | Seed notes → matched notes | Seed masks → matched masks |
| --- | --- | ---: | ---: |
| bitcoin | 949, 961, 970, 988 | 5 → 8 | 5 → 18 |
| coffee | 956, 966 | 4 → 19 | 4 → 75 |
| coffeechain | 983 | 2 → 10 | 2 → 10 |
| gm | 1006 | 2 → 6 | 2 → 6 |
| grownostr | 1004, 1032, 1043, 1101, 1133 | 7 → 7 | 7 → 7 |
| nostr | 1019 | 2 → 11 | 2 → 19 |
| plebchain | 1100 | 2 → 3 | 2 → 3 |

These are 138 family–mask memberships: 24 seed memberships and 114 additions.
Some masks match multiple families, so there are 134 distinct canonical masks
and 36 distinct notes overall. There are 40 added family–note memberships, not
40 different newly discovered notes. All seven seeds are single words; this real
corpus run does not test multiword subject matching.

The complete row IDs, source-note IDs and seed IDs are in
[results.json](./NMR03/results.json). [review.json](./NMR03/review.json) preserves
every matching original note, every exact fragment, byte ranges, generated
subject and vector alias. Nothing is replaced with a summary.

## Additions versus existing broad destinations

Growing the seed union is not the same as recovering notes absent from every
existing broad destination. That distinction materially changes the result:

| Existing destination | Notes newly found outside it | Existing notes not matched |
| --- | --- | --- |
| Coffee [1539], 19 notes | N018, N041, N058, N065 | N005, N017, N024, N034 |
| Coffee/tea [1598], 22 notes | N018, N041, N058, N065 | N005, N017, N024, N034, N042, N072, N080 |
| Bitcoin [1284], 6 notes | N050, N074 | None |

Coffee therefore remains 19 notes, but it is a **different set of 19**. The
three Coffeechain-only contexts and unspecified caffeine source omitted by
literal Coffee are boundary cases, not automatically irrelevant. Tea was never
the subject of the literal Coffee query. N055's Bitcoin workshop is new to the
five-note seed union but was already in broad Bitcoin [1284].

Concrete supporting masks:

- N018, V130: `⟦Off⟧ ⟦running⟧ ⟦errands⟧ ⟦on those days I enjoyed⟧ ⟦morning coffee⟧`.
- N041, V321: `⟦I don't feel I need⟧ ⟦coffee to start living today⟧`.
- N058, V494: `⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧`.
- N065, V554: `⟦Coffee shop I liked⟧ ⟦now⟧ ⟦No laptops or tablets⟧ ⟦weekends⟧`.
- N050, V402: `⟦goals⟧ ⟦pizza restaurant⟧ ⟦St Michel de L'Attalaye⟧ ⟦accept Bitcoin⟧ ⟦haiti⟧`.
- N074, V683: `⟦bitcoin carnivore narrative⟧`.

The broad interpretation includes coffee venues and Bitcoin community matters,
not just beverage preparation or Bitcoin implementation. A negative statement
about needing coffee or disliking a Bitcoin narrative still concerns that
subject. These interpretations are judgments grounded in the originals, not
implied by a generated category name.

## Semantic audit of every addition

The main review inspected all 134 matching canonical masks and full source notes.
A separate clean-context agent independently inspected all 18 new Coffee and
Bitcoin notes and every admitted mask from those notes. No clearly unrelated
new note was found under a broad, mention-supported interpretation. That is
**not** a measured precision score or approval of every destination's scope.

| New Coffee note | What its masks support; qualification |
| --- | --- |
| N004 | A rave at a coffee shop; venue context, not coffee preparation. |
| N018 | Morning coffee during errands; masks also retain errand context. |
| N036 | Iced coffee served in ice. |
| N038 | Music playing in a coffee shop; venue context. |
| N041 | Not needing coffee after improved sleep; a relevant negative statement. |
| N043 | Fetching coffee as a movement ritual; V351 also contains stretching and bowing. |
| N045 | Half-and-half ruining coffee. |
| N052 | Grinding coffee beans. |
| N058 | Hot morning coffee, including V494 missed by NMR02. |
| N060 | Coffee with raw cream and egg yolk. |
| N065 | Coffee-shop laptop rules and switching shops; many masks also select retaliation or personal growth. |
| N071 | Coffee with breakfast; V652 additionally selects breakfast ingredients. |
| N086 | Roasting beans and personal coffee flavor. |
| N094 | Decaf, flavor and caffeine motivation. |
| N095 | Having coffee and wanting another. |

| New Bitcoin note | What its masks support; qualification |
| --- | --- |
| N050 | Pizza day and planned Bitcoin acceptance at a restaurant. |
| N055 | A Bitcoin workshop; V454 also selects the subsequent pig slaughter/meal. |
| N074 | Criticism of a Bitcoin-community carnivore narrative, not technical Bitcoin content. |

The remaining added family–note memberships were all inspected:

- Coffeechain: N004, N017, N018, N029, N038, N071, N086, N095. All masks name
  the community/tag; this does not establish coffee drinking in every note.
- GM: N005, N040, N058, N089. Their originals use GM as a greeting. No different
  sense was observed here, but the rule has no word-sense disambiguation.
- Nostr: N018, N026, N028, N048, N058, N074, N077, N089, N092. Evidence ranges
  from community greetings and bare tags to recipes, selling salsa, desired
  platform content and diet controversy. These are not equivalent technical subjects.
- Plebchain: N048. The mask names Nostr/Plebchain amid an otherwise unrelated
  tag-heavy post. This is literal community reference, not proof of substantive discussion.
- GrowNostr has no added note or mask beyond its consolidated seed groups.

Scope is an important limitation even before addition. Coffee's original seed
N048 is a Tolstoy quotation with a long tag list. Bitcoin's original seed N012
discusses Cheese Doodle Day with a Bitcoin tag. The diagnostic preserves these
inputs; it does not certify their relevance or repair extraction. Likewise, a
compound mask containing coffee-shop retaliation does not become a pure coffee
mask. Note admission and whether every part of a mask expresses the destination
are separate questions.

## Hierarchy and recall limitations

The smallest original category containing **all** 19 literal Coffee notes is
the 100-note root [1753]. For Bitcoin's eight notes it is [1653], with 87 notes.
In ND02-NP01 the corresponding covering categories are the root and [1701], with
98 notes. Shortening paths cannot supply the missing destination memberships.
These counts describe set coverage, not the semantic quality of those ancestors.

Literal matching also misses meaningful wording. GM does not match `Good morning`.
Coffee does not match N052/V412's `Rise` + `grind` or N086/V797's `Sipping` +
`#coffeechain`, though their originals clarify coffee. Both source notes are
retrieved through other masks. Bitcoin does not match `satoshi`/`Satoshis` in
N024/N054; those notes are likewise reached through other masks. Missing a mask
is not necessarily missing a note. No exhaustive recall denominator was established.

The strict seed requirement also leaves exercise, sleep and equipment untested.
Failure to derive a seed is abstention, not evidence that a subject is absent.
Using the original hierarchy for seeds remains an unnecessary potential source
of omissions; this experiment has not escaped that dependency.

## Consequence and next question

The concrete gain is recovering some explicit subject-supported note memberships
without depending on where diffusion placed them. The experiment does not justify
replacing semantic vectors with keywords, adding members to every old ancestor,
or claiming a better broad-to-narrow hierarchy.

A read-only feasibility check removed only the existing-category requirement:
use complete word sets already supplied by individual masks, and retain those
whose words appear in masks from at least two notes. This yields 23 candidates:
19 single-word, three two-word, and one three-word. Alongside the seven subjects
above it finds bread (8 notes), sourdough bread (2), beef (4), brisket (2), and
`good morning` (4). But it also proposes `I` (27 notes) and ambiguous `rise` and
`freedom` (2 each). These are exploratory counts, not another accepted run.

The next useful test is whether source-supported descriptions can generate
meaningful broad and narrow destinations independently of old ancestry. It
must examine why a candidate is a subject rather than merely shared wording,
and whether adding a qualifier actually narrows the meaning and notes. Do not
silently remove `I` with a one-off exception or advertise the 23 candidates as
a solution. This is the unresolved description-quality problem, not a reason
to tune another geometric distance cutoff.

## Reproduction and verification

From the repository root, with ordinary Python and a nonexistent output path:

```sh
python3 sse_multivector/navigation-research-v1/NMR03/source/literal_category_membership.py \
  sse_multivector/geometric-hierarchy-v1/GDC09/categories.json \
  --hierarchy sse_multivector/geometric-hierarchy-v1/GDC09/hierarchy.json \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --output /tmp/nmr03-reproduction --run-id NMR03
```

The three source snapshots are self-contained. [config.json](./NMR03/config.json)
records every input and source hash. All six declared files reproduced
byte-for-byte in a fresh temporary directory. An initial verification command
also enumerated Python's incidental `__pycache__` and failed on that non-artifact;
the corrected check compares the six declared artifacts, not interpreter caches.
No experimental output was changed to make reproduction pass.

An independent exhaustive word scan reproduced all matches. All 219 original
category note-mask projections agree exactly with native vector evidence. Every
review record equals its original source record. The new tests first failed
because the implementation did not exist; the final 52-test suite passes.
It includes the production CLI, complete multiword matching, no same-note mask
spillover, source consistency, and refusal to overwrite previous results.

No subject, mask, vector, label or browsing artifact was regenerated. Baseline
GDC09 and the optional ND02-NP01 browser remain unchanged. No paid compute/API
run was introduced. The broader research goal remains open.

## Sources

[^1]: A. Buzmakov, S. O. Kuznetsov and A. Napoli, [Concept Stability as a Tool for Pattern Selection](https://ceur-ws.org/Vol-1257/paper6.pdf), 2014, §2.1. Formal contexts and closure; not evidence that literal words capture semantic identity.
[^2]: P. Cimiano, A. Hotho and S. Staab, [Learning Concept Hierarchies from Text Corpora using Formal Concept Analysis](https://arxiv.org/pdf/1109.2140), JAIR 24, 2005, §§3–4 and 6.3, Table 7. Read these relevant sections, not claimed as a complete reading of the 35-page paper. The later arXiv upload date is not its publication year.
