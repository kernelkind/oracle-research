# CPC01 — category membership and actual paths

## Question

Can the useful but imperfect membership mechanism from TCC03/TCC04 improve
access through existing source-derived category candidates when it is connected
to the existing relation rules? This is a construction-compatibility experiment,
not another search for a score cutoff and not a complete hierarchy solution.

The original GDC09 hierarchy, masks, descriptions and all previous experiments
remain unchanged. No browser is packaged during this investigation.

## Frozen candidate family

Use the three existing TCC04 source words `bread`, `chicken` and `salt`, plus
**every** CAP04 adjacent two-word pattern containing any of those words:

| Source word | All adjacent patterns |
| --- | --- |
| bread | bread in; sourdough bread |
| chicken | a chicken; chicken stock; make chicken; making chicken; of chicken |
| salt | salt and; sea salt |

These are 12 candidate strings, not 12 approved subjects. CAP04's saved token
positions establish their order. Verify that every recorded occurrence's
casefolded source span exactly equals the space-joined string. Preserve the
source rows and positions; do not fix grammar, choose more favorable wording,
or turn CAP02's unordered feature sets into invented phrases.

This is an intentionally bounded family around the preceding three membership
categories, not a representative estimate of all possible categories. It
contains recognizable refinements, incomplete phrases, and possible duplicates.
It excludes valid possibilities such as rosemary used in bread, which is not a
recurrent adjacent phrase. No membership score can recover an absent candidate.

## Inputs and conditions

Copy all 945 CAP04 input records, unchanged, covering all 100 GDC09 notes.
The native pinned GLiClass runner scores each saved subject description against
each of the 12 strings **separately**: 11,340 requests. The model sees neither
the whole original note nor other descriptions. Originals, masks and alias
identifiers remain in the evidence for evaluation.

For each note/category, retain the maximum over all its saved descriptions,
including every tied attaining row. Compare three conditions:

1. **Literal:** the source word or adjacent phrase occurs in a saved description.
2. **Native:** the complete-note maximum is at least 0.5.
3. **Development:** that maximum is at least 0.9481359422711596, the retrospective
   shared operating point in the frozen TCC03+TCC04 tradeoff record.

Both score cutoffs are fixed before this run. Do not choose a new cutoff,
category-specific cutoff, or accepted-note quota after seeing the results.
The native condition is important: unlike the higher operating point, it
retained the previously tested Bagel/Salt assignment. Both conditions reuse
development evidence and are not clean holdout estimates. The full 100-note
memberships and the new compound-category scores have not been measured by
this experiment before.

For every condition reuse `mask_description_hierarchy.description_relations`
unchanged. It returns both existing rules:

- `note_subset`: child notes are a proper subset of parent notes.
- `descriptor_extension`: the same note condition, plus the parent's token
  set is a proper subset of the child's token set.

Both rules remove transitive edges. Neither establishes semantic parenthood.
Preserve all candidates, roots, edges, empty and one-note destinations, and
equal-note-set groups in the output. Do not silently reapply recurrence after
scoring, discard awkward candidates, merge equivalent-looking labels, or add
child notes to parents. Equal note sets remove an edge under these rules; they
do **not** remove the category or its duplicate siblings.

## Hypothesis and predictions before scores

Hypothesis: replacing literal membership with one of these fixed semantic
conditions produces at least one additional source-supported reachable
destination or valid relation in this bounded family. Record every regression
and incorrect addition alongside that improvement. A component improvement
does not make the complete output a useful browser.

Positive opportunities include Bread notes expressed as bagels, tortillas or
paratha, and Chicken notes expressed as chickens or chicks. The three complete
child phrases already have literal support for their two known relevant notes;
do not portray retaining those notes as new recovery.

Three existing relations have a clear source-supported interpretation:
Bread → sourdough bread; Chicken → chicken stock; Salt → sea salt. They are
examples, not an exhaustive prescribed taxonomy. Accept other coherent
relations if their actual evidence supports the complete path.

One regression is already predicted for the development condition. Salt's
saved score for N046 is 0.761453772, below the fixed cutoff. N046 explicitly
lists sea-salt bagel toppings. If `sea salt` accepts that note, strict note
containment blocks Salt → sea salt. If it does not, the child loses relevant
content too. No new child score can preserve that route with N046 in this
condition. Its reappearance is not a novel finding.

The source audit also already establishes that `bread in`, `of chicken` and
`salt and` are incomplete expressions, not independently defined narrower
topics. Their scores cannot prove that a category generator understood them.
`a chicken` occurs inside descriptions of a chicken dish or chicken tractor,
not evidence for a whole-bird-only category. `make chicken` and `making chicken`
may describe a recognizable preparation activity; their source occurrences
continue with `stock`. Preserve possible useful interpretations rather than
predeclaring every non-noun phrase invalid.

## Competing explanations and discriminating observations

- **Useful membership transfers into useful access:** previously absent notes
  enter appropriate destinations through genuine source witnesses, and those
  destinations retain valid narrower choices. This warrants work on candidate
  selection and semantic relation evidence with membership as a component.
- **Literal grammatical distinctions were incidental:** complete note sets
  become equal or near-equal. Report the actual remaining roots and siblings;
  edge disappearance alone is not removal of low-value navigation choices.
- **Strict containment magnifies membership errors:** a supported child loses
  its appropriate parent because of one missing parent note or erroneous child
  addition. Identify that exact note and winning description/mask. Do not call
  the broken edge evidence that the subjects lack a broader/narrower relation.
- **Finite co-occurrence mimics semantic refinement:** a new strict subset link
  is not a recognizable narrowing when its complete masks and notes are read.
  This limits the relation rule, even if individual memberships are acceptable.
- **The category input is not a defined meaning:** an incomplete source fragment
  yields a score or note set. Keep this separate from failure to recognize a
  complete category. Do not repair the phrase after scoring.
- **The available evidence is defective:** the winning saved description adds
  meaning or the mask omits it. Distinguish original-note validity, description
  validity, and attaining-mask support rather than blaming the relation rule.

Would either outcome change the next decision? Yes. Source-supported access
improvements with retained paths justify testing a repeatable candidate-selection
step. If new memberships mainly cause broken paths, extra roots or unsupported
distinctions, revise the way semantic relation evidence and note membership are
combined; do not automatically fit another cutoff. Neither outcome establishes
all category generation, equivalent-category handling or parenthood solved.

## Evaluation and evidence

The main and independent reviewer have read all 100 original notes before this
run. The independent reviewer also inspected all 945 saved subject/mask records.
`CPC01-JUDGMENTS.json` freezes supported and unresolved note IDs for the six
complete topical categories. Other notes are unsupported by the readable text,
not proof that a food contains none of a particular ingredient. Unresolved
bread-family and unspecified-egg boundaries stay outside binary error counts.

After scoring inspect all admitted notes for the six complete categories, all
attaining source witnesses for additions/misses, every edge under both rules,
and the entire root menu. Audit the other six strings as possible meanings or
incomplete inputs; do not manufacture binary truth labels for undefined scopes.
Keep all raw scores, maxima, source texts, inline masks, decisions and source
hashes. Report selection, membership and relation failures separately.

## Literature and task fit

Sanderson and Croft construct browsing menus from terms and document inclusion,
allowing topical aspects as well as type relations. Their conditional-frequency
rule was relaxed to 0.8 through informal analysis; query-focused retrieved
collections helped limit ambiguity. That motivates testing extensional evidence,
not adopting their threshold or treating inclusion as semantic proof.[^1]

AutoPhrase explicitly separates candidate sequences from phrase quality. It
requires interpretable semantic units rather than assuming recurrence suffices.
Its distant training, statistical features and POS-guided segmentation were
evaluated on much larger corpora than these saved descriptions. It supports
keeping category validity separate here; it does not justify deploying a new
phrase model without checking its fit.[^2]

GLiClass's exact native inputs, training streams, model loading and transfer
limits are recorded in TCC01–TCC04. No new model-transfer claim is introduced.
Here the new assumption is compositional: that imperfect independent category
memberships remain useful when supplied to the existing relation rules.

## Resources and verification

Use only the already cached native checkpoint, CPU, one process and two Torch
threads. Prior peak RSS was about 4.91 GiB; no parallel model processes, GPU,
paid service or new download. Expect minutes rather than a long sweep.

Implement minimal production-path tests first for source-preserving preparation,
complete score-matrix validation, maxima, fixed thresholds, equality/empty cases
and unchanged relation construction. Independently audit the assembled artifact.
Replay the deterministic preparation/analysis and verify reused TCC04 scores
against their unchanged description/category requests. Keep all frozen prior
artifacts and the unrelated pending HiT files untouched.

[^1]: Sanderson and Croft (1999), [Deriving concept hierarchies from text](https://ciir.cs.umass.edu/pubfiles/ir-156.pdf), sections 2–4.
[^2]: Shang et al. (2017), [Automated Phrase Mining from Massive Text Corpora](https://arxiv.org/html/1702.04457), sections 2–4.
