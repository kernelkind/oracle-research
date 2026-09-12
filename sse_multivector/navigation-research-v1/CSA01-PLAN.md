# Contextual sense attributes: construction-fit audit

## Question

Would replacing CAP02's word features with correctly chosen contextual word
senses and their dictionary ancestors supply the missing construction capability?
This is an audit of that representation before selecting or running a model.
It is not an evaluation of automatic word-sense disambiguation.

The proposed full route is: interpret mask-supported words in their original
contexts; attach their sense IDs and broader dictionary concepts to each mask;
construct recurring shared attributes and inclusion relations; then select
useful note-navigation choices. Per-occurrence interpretation and dictionary
lookup are not intrinsically unscalable. Whether this route retains phrase
meaning and supplies useful topical parents remains unproven.

## Evidence and controls

Keep GDC09 and CAP02 unchanged. Use the existing pinned WordNet 3.0 archive and
the production lookup in `mask_group_lexical_relations.py`. Save every queried
sense and ancestor, not only a preferred answer. Inspect complete source notes
and their exact masks. Human interpretation identifies plausible senses for
this diagnostic only; it must not become repaired corpus annotations.

Inspect these already documented mechanisms, selected before new lookup:

1. N007/V052 and N039/V304: the two uses of `hit`. Query both the word and
   `hit the spot`; check whether the required distinction exists in the inventory.
2. N065/V561 and N094/V852: `experience` in the cafe-retaliation and decaf
   masks. Check whether part of speech alone already separates the uses.
3. N013/V097, N026/V205 and N080/V733: chicken stock and egg-laying chickens.
   Check normalization separately from the meat/bird distinction and inspect
   whether dictionary ancestry actually supports a shared topical destination.
4. N015's sourdough-bread mask, N037/V290 and N072/V665: inspect the paths
   from bread types and culinary rosemary to food. Distinguish broader lexical
   concepts from the relationship that rosemary is added to bread.
5. Retain the established LGR01 missing greeting sense for GM as an inventory
   control. Do not rerun that lookup as though it were a new discovery.

## Hypothesis and competing explanations

The hypothesis is that contextual senses plus their ancestors can supply
meaningful new abstractions while resolving CAP02's observed word ambiguity.
Competing explanations are that grammatical tagging already explains an apparent
gain; the needed sense is absent; or correct word senses still omit the relation
required to describe a group. A dictionary animal/meat split might also remove
a legitimate cross-sense topic rather than improve discovery.

For each example, record what literal features preserve, what sense IDs could
add, and what neither represents. An ancestor path establishes a dictionary
relation only, not correct membership of every original mask in a browsing
category. A missing path is not a judgment that two notes are unrelated.

## Decision consequences

Would either outcome change the next decision? Yes. If the inventory supplies
the needed distinctions and abstractions without losing the established topical
links, a small native-context WSD test becomes justified. If it cannot, do not
spend a model run testing a representation that already lacks the needed output.
Instead identify whether senses should be optional attributes, whether a
compositional representation is necessary, or whether this route should stop.

This audit cannot establish extraction accuracy, end-to-end category quality,
coverage over all notes, or a preferred taxonomy. Do not package a browser from
it. The decision concerns the role and adequacy of the proposed representation,
not whether a particular checkpoint is competent.
