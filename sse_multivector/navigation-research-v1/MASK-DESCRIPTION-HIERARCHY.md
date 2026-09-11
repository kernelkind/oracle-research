# Hierarchies from explicit mask descriptions

MDH02 produces one ordinary broad-to-narrow relationship, Bread → Sourdough
bread, and two audience-related refinements, GM → GM Nostr and Nostr → GM Nostr.
It does not produce a useful complete hierarchy. Literal matching also admits
clear errors: art matches state-of-the-art, and getting up matches rising prices.

These experiments remove dependence on the old tree for both candidate discovery
and membership. They do not modify GDC09 or the browsing candidate ND02-NP01.
The result is evidence about one construction mechanism, not a replacement
hierarchy or a verdict against SSE. No vectors were recomputed or used here.

## Question

NMR03 recovered explicitly supported notes missing from old destinations, but
used old categories to obtain its seven subject candidates. Could complete masks
themselves supply broader and narrower destinations, with their memberships
established independently of the old tree?

Two relations are compared with identical candidates and memberships:

1. **Note inclusion:** B is placed under A when every note in B also occurs in A,
   and A contains at least one additional note.
2. **Description extension:** require that same note inclusion and additionally
   require B's descriptor to contain every feature of A plus additional features.

This is exploratory work on an already inspected corpus. A synthetic production
test demonstrates how independent coffee and bread masks in the same notes can
create Coffee → Bread under the first rule. That test establishes a possible
mechanism, not an observed error in the real corpus.

## Literature and its limits

Lingo separates finding descriptions from assigning documents. It extracts
frequent phrases, uses SVD to propose latent concepts, matches phrases to them,
and then assigns documents. Crucially, its final section explicitly does not
provide hierarchy induction. This supports separating the two jobs; it does not
establish that a concise phrase names a valid parent.[^1]

Suffix Tree Clustering also begins with shared phrases. Its later overlap-based
merging takes connected components. Applying that entire procedure here would
reintroduce the possibility that a connecting group joins otherwise distinct
collections. The useful ingredient for this investigation is source-phrase
proposals, not an assumption that its merging solves parent meaning.[^2]

Li and Wu's phrase-based hierarchy groups phrases by average document proximity
and uses the phrase covering the most documents as the parent label. Their
evaluation measures document clustering against ODP classes. Neither the label
choice nor that evaluation proves that every descendant refines its ancestor.
This is a relevant alternative, but not a repair for the already observed
problem of naming a mixed union after only part of it.[^3]

Sanderson and Croft derive relations from document inclusion, relaxing complete
inclusion to 0.8. They work with query-retrieved documents and assume this reduces
word ambiguity. Their small user study evaluates displayed term relations,
without showing the underlying documents. It is therefore not evidence of
complete root-to-document fidelity on mixed short posts. They also permit
aspect relations and explicitly decline to require all relations to be
transitive. MDH tests strict inclusion as a diagnostic, not a reproduction of
their term extraction, query expansion or hierarchy evaluation.[^4]

## Inputs and procedure

Both runs use the same 916 canonical mask records from GDC09, covering 100 notes.
Every original note, exact fragment, byte range, generated subject and vector
alias remains available. Generated subjects and old category names do not decide
either candidate membership or parentage.

For each complete mask, collect its casefolded words. Keep function words and
numbers; do not stem or add a stoplist. Each distinct nonempty feature set becomes
a candidate if masks containing all its features occur in at least two different
notes. The candidate's members are all such masks, wherever the old tree placed
them. Other masks from the same note do not join automatically.

Apply both relations above, then remove direct edges already represented by a
path through another candidate. Multiple parents are retained. Equal note sets
never create a parent–child transition. No artificial root, final labels or
browser export is introduced.

MDH01 uses words only. MDH02 changes only feature extraction by also retaining
characters in Unicode symbol categories. This is a deliberately limited control,
not full emoji interpretation, phrase parsing, word-sense resolution or an
endorsed production representation.

## Complete results

| Run | Candidates | Notes reached | Distinct matching masks | Note-inclusion edges | Description-extension edges |
| --- | ---: | ---: | ---: | ---: | ---: |
| MDH01, words | 23 | 65 | 341 | 4 | 3 |
| MDH02, words and symbols | 22 | 53 | 246 | 3 | 3 |

These are immediate edges. MDH02 has twenty roots and at most one edge in a
path: its three edges reach only two distinct child candidates. Most candidates
remain disconnected. Counts of reached notes are not recall or quality scores.

Every immediate relation is enumerated here:

| Parent features | Child features | Notes in parent → child | Observed in | Judgment from masks and originals |
| --- | --- | --- | --- | --- |
| bread | bread, sourdough | 8 → 2: N015, N037 | Both rules, both runs | Clear narrowing to a kind of bread. |
| gm | gm, nostr | 6 → 2: N058, N089 | Both rules, both runs | A greeting restricted to its addressed community. |
| nostr | gm, nostr | 11 → 2: N058, N089 | Both rules, both runs | Community greetings are an aspect, not a type of platform; plausible browsing refinement. |
| i | homesteading | 27 → 3: N013, N092, N100 | MDH01 note inclusion only | Artifact of our feature extraction; not valid evidence about semantic parent selection. |

### Why the `i` result is invalid evidence

The candidate originated from N034, V275. Its complete original is:

> I've had a stupid amount of caffeine today and ⟦I⟧ still feel so tired. 4 more hours of work. ⟦😴⟧

The actual mask is `I` plus the sleep emoji. MDH01 erased the emoji and matched
every mask containing `I`, reaching 27 notes. MDH02 preserves the symbol; that
complete feature set no longer has support from two notes and is not proposed.
This is not a failure of the source mask or SSE, nor evidence that first-person
text is inherently an invalid mask. The preprocessing changed its meaning.

After correcting this representation error, the two relation rules produce
exactly the same real edges. There is **no observed superiority** of description
extension over note inclusion in MDH02. The synthetic counterexample remains a
reason not to equate observed note inclusion with semantic containment.

### What the bread path actually does

The broader candidate contains N011, N015, N023, N037, N047, N072, N075 and N089.
Their masks concern mochi bread, sourdough preparation, bread in meals, flavored
sourdough, baking bread, soda bread, sandwich bread, and mixing bread ingredients.
The child retains only N015 and N037, whose masks explicitly say sourdough bread.
This offers both a recognizable narrowing and a strict reduction of notes.

It does not claim these are every bread note in the corpus. No paraphrase or
implicit-subject recall denominator was established. Nor does a successful
two-category path demonstrate useful organization above Bread.

### Where literal matching loses meaning

For `art`, N048 supplies the mask `⟦art⟧` from a long hashtag list. N027 matches
through `⟦CombiCookTop V4000 I804⟧ ⟦one of V-Zug's most state-of-the-art products⟧`.
Its original describes a technologically advanced induction hob. It does not
use *art* in the sense supplied by the tag. Token overlap alone admitted it.

For `rise`, N052 supplies `⟦Rise⟧` in “Rise and grind coffee beans.” N062 matches
through `⟦Aussies' Christmas lunch costs rise⟧`. Getting up and price increases
are different senses. No suitable subject follows merely from spelling equality.

For `ice`, the matches include both ice serving a drink and ice cream. There may
be a reasonable broader cold-food connection, but the mechanism neither finds
nor establishes that description. Its output must not be declared correct merely
because an evaluator can invent a broader name afterward.

## Audit of every MDH02 candidate

The following descriptions are audit shorthand for exact feature sets, not
generated or approved category labels. The complete matching originals and masks
are in [MDH02/review.json](./MDH02/review.json); stable descriptor IDs, all rows
and note memberships are in [MDH02/descriptions.json](./MDH02/descriptions.json).

| Features | Notes | Evidence and qualification |
| --- | ---: | --- |
| art | 2 | Clear sense error: art tag versus state-of-the-art appliance. |
| beef | 4 | Beef stew, a beef meal, recipe ground beef and steak processing. |
| bitcoin | 8 | Existing NMR03 broad Bitcoin evidence; includes community references and weak tags. |
| bread | 8 | Bread preparation, ingredients and meals; detailed path above. |
| bread, sourdough | 2 | Explicit sourdough preparation and flavored sourdough. |
| brisket | 2 | Both originals explicitly discuss smoking brisket. |
| carnivore | 3 | Diet reference, non-carnivore recipe and criticism of the diet narrative; disagreement does not make them unrelated. |
| coffee | 19 | Same broad explicit Coffee membership as NMR03, including venues. |
| coffeechain | 10 | Explicit tag/community reference, not proof of drinking coffee. |
| day, happy, pizza | 2 | Pizza-day greetings, one explicitly Bitcoin Pizza Day; dropped qualifier limits the descriptor's specificity. |
| dog | 2 | Bare dog tag versus feeding meat to a dog; weak first note, no word-sense mismatch observed. |
| freedom | 2 | Bare Freedom tag versus sarcastic freedom from internet; a shared broad reading is possible, not established by matching. |
| gm | 6 | Greeting use in these originals; no paraphrase matching. |
| gm, nostr | 2 | Explicit community-addressed greetings. |
| good, morning | 4 | Morning greetings; separate from GM despite equivalent wording in context. |
| grownostr | 7 | Explicit community/tag evidence, unchanged from NMR03. |
| homesteading | 3 | Stock preservation, meal/chicken care and household food processing; one mask is only the tag. |
| ice | 3 | Ice serving a drink and ice-cream compounds; literal component matching does not establish subject identity. |
| music | 2 | A song playing in a coffee shop versus a bare Music tag. |
| nostr | 11 | Platform/community references across different activities, unchanged from NMR03. |
| plebchain | 3 | Explicit community/tag evidence, unchanged from NMR03. |
| rise | 2 | Clear sense error: getting up versus prices increasing. |

All candidates were inspected through full originals and matching masks. The
seven unchanged NMR03 families retain that prior complete audit. This is one
researcher's semantic audit, not a blind user study or a measured precision score.
An independent agent could not be launched because the thread limit was reached;
the mechanical reproduction below was performed locally.

## Consequence for the next experiment

Removing dependence on the old tree can recover candidate destinations and a few
valid relations. However, complete literal feature sets are too restrictive for
unstated broader subjects and too permissive across senses and compounds.
GM and Good morning remain disconnected; the method has no way to propose an
unwritten shared description. Adjusting inclusion thresholds cannot supply that
missing semantic understanding.

The next mechanism to investigate is source-grounded semantic generalization:
can an explicit description identify the relevant meaning across differently
worded masks and distinguish refinement from mere association? Published
conceptual indexing and contextual entailment methods are leads, not approved
solutions. A new test must separately establish description meaning, membership
and ancestor fit; it must not silently turn a conventional noun taxonomy or a
claim-entailment score into the definition of note browsing.

## Reproduction and preservation

From the repository root, choose a nonexistent output directory:

```sh
python3 sse_multivector/navigation-research-v1/MDH02/source/mask_description_hierarchy.py \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --output /tmp/mdh02-reproduction --run-id MDH02 --features words-and-symbols
```

For MDH01, use its own source directory, run ID and `--features words`.
Each run has four JSON files and three self-contained source snapshots. Configs
pin the input hash, all source hashes, Unicode version, feature mode and counts.
Both runs reproduce all seven declared files byte-for-byte. Interpreter caches
are not experiment artifacts.

An independent exhaustive scan reproduced every candidate and membership, both
complete and immediate edge sets, and every saved original review record. Every
source fragment was checked against its UTF-8 byte ranges. Seven new tests and
52 existing tests pass, including the production CLI, rejection of inconsistent
aliases, equal-note-set exclusion and refusal to overwrite existing output.
The initial five tests failed before implementation existed; two further checks
were added during the audit without changing production behavior.

No browser default, category label, subject, source mask or vector changed.
The current optional browser remains ND02-NP01. These sparse diagnostic outputs
are not packaged as a better hierarchy. No paid model or compute job was started.

## Sources

[^1]: S. Osiński, J. Stefanowski and D. Weiss, [Lingo: Search Results Clustering Algorithm Based on Singular Value Decomposition](https://www.cs.put.poznan.pl/jstefanowski/pub/lingo.pdf), 2004, especially §3.5. Full paper read.
[^2]: O. Zamir and O. Etzioni, [Web Document Clustering: A Feasibility Demonstration](https://www.cs.ucr.edu/~vagelis/classes/CS242/publications/webClustering.pdf), 1998, §§3.1–3.3. Relevant method sections read; not claimed as a full-paper review.
[^3]: Z. Li and X. Wu, [A Phrase-Based Method for Hierarchical Clustering of Web Snippets](https://ojs.aaai.org/index.php/AAAI/article/download/7773/7633), 2010. Full two-page paper read.
[^4]: M. Sanderson and W. B. Croft, [Deriving Concept Hierarchies from Text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), 1999, §§2–4. Full paper read; publication year is not the search engine's recent crawl date.
