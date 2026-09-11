# LGR01: lexical relations between frozen mask groups

Question: can explicit lexical relations supply useful broader or equivalent
group proposals that the literal MDH02 rule missed?

The input is all 22 MDH02 groups, with unchanged members, seeds and source masks.
Each complete seed mask is looked up in WordNet, retaining its source order.
The algorithm records every matching word sense; it does not choose the first
sense, strip a phrase to its head, or interpret a generated subject/title.
For all ordered group pairs, an explicit hypernym path proposes a broader group;
a shared word sense proposes equivalence. A common ancestor alone proposes neither.
Unknown phrases and missing relations remain unknown, not rejected meanings.
Instance-of and part-whole relations are not used. These are lexical proposals,
not accepted browsing edges. All proposed links must be inspected against every
member mask and its original note before drawing conclusions.

Hypothesis: this supplies at least one defensible additional relation beyond
MDH02's three literal edges. Strong counterevidence is a proposed relation that
uses a word sense incompatible with the groups' actual masks. Coverage failures
are recorded separately from incorrect proposals. No threshold is tuned.

Diagnostic expectations, recorded before executing the lookup:

- Sourdough bread should narrow Bread, reproducing an existing relation.
- Brisket under Beef is a plausible additional relation to investigate, not a
  universal lexical truth presumed for every kind of brisket.
- GM and Good morning are candidates for an equivalent greeting meaning. GM
  may instead be absent or have an irrelevant dictionary expansion.
- Coffee and Music must not acquire parentage merely through association.
- Art and Rise already have mixed-sense members; a word-level relationship must
  not be promoted to a claim about those complete groups without examination.

Run once with the pinned WordNet archive. Save its hash, selected senses and
paths, every ordered pair, complete unchanged group evidence and runner source.
Reproduce the relation calculation offline from the saved lexical records.
This tests a lexical proposal component, not a finished hierarchy or universal
word-sense disambiguation. Original browser artifacts remain unchanged.
