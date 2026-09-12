# CPC02 — word-form control for the observed gains

CPC01's development condition recovers Chicken/N080 and Chicken/N100 from the
literal baseline. Both notes already have saved descriptions explicitly saying
`chickens`. This leaves a competing explanation: ordinary inflection handling,
not learned semantic generalization, is sufficient for the observed gains.

Before retaining the classifier as necessary for this construction family,
test that explanation directly. Keep CPC01's 12 candidate strings, IDs, source
records and both relation rules unchanged. Use NLTK 3.9.2's cached
`EnglishStemmer` to normalize each CAP04 token and each candidate token solely
for matching. A candidate matches when its normalized token sequence occurs
contiguously in a description. Note membership is still any matching description.
Preserve the actual source positions; do not claim normalized matches were
literal occurrences or rename the categories using stemmed words.

Hypothesis: this fixed normalization recovers both observed Chicken notes,
without adding unsupported notes to the six complete categories or losing
their literal supported memberships, and preserves the three clear existing
refinements. Evaluate all 100 notes and all 12 candidates, not only those two
positive examples. Keep CPC01's frozen source judgments, unresolved boundaries,
duplicates and incomplete-category limitations. No learned score or cutoff is
used in this control. There is no classifier retraining, download or new model.

Competing explanations:

- If the same gains follow from generic normalization and other memberships
  remain appropriate, the observed gains do not establish a need for the learned
  matcher in this family. Use the simpler control as the reference for future
  semantic-recovery claims rather than crediting elementary inflection again.
- If normalization fails to recover them or introduces other unsupported
  memberships, inspect those exact source matches. The classifier may provide
  a useful distinction here, but this does not establish broad transfer.
- Either method can leave missing broader knowledge: `bagels`, `tomato tortilla`
  and `Lacha Paratha` need not normalize to `bread`. Do not interpret their
  continued absence as failure of an inflection control or as solved membership.

Would either outcome change the next decision? Yes: it determines whether the
only demonstrated gains require the expensive component, or whether subsequent
work should start from a simpler reference. It does not decide category quality
or semantic parenthood, which remain separate unresolved construction needs.

This is a post-CPC01, pre-control hypothesis, not a predeclared CPC01 condition.
No hand-written suffix rule, exception for these notes, or canonical taxonomy.

The [native NLTK documentation](https://www.nltk.org/api/nltk.stem.snowball.html)
describes English Snowball stemming and its rule-based suffix processing.
This is word-form normalization, not a learned sentence classifier or a
guarantee of word-sense identity. Woods' [Conceptual Indexing](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf)
keeps morphology, semantic generality and phrase relationships distinct; this
control deliberately tests only the first, without adopting that full system.

Write minimal failing production-path tests, then run the fixed control once.
Save source matches, changed memberships, both complete relation outputs,
package/source hashes, and an exact offline replay. Preserve CPC01 and GDC09.
