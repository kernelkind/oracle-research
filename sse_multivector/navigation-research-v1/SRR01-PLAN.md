# Task-trained sense relations

GDR03 exposed association errors in generic topic classification. SRR01 tests
a different learned task: predicting the relationship between two meanings.
It does not change the existing groups or build a hierarchy from the predictions.

Use `ChangeIsKey/change-type-classifier`, revision
`5c833b8a1f6e1f6fc3e27c533ce16e21949c931e`. It is a 355M-parameter RoBERTa-large
cross-encoder with five outputs, trained on WordNet definition pairs. The labels
in the released checkpoint are homonym, hyponym, hypernym, co-hyponym and antonym.
The author's test records establish orientation: hyponym means the first input
is narrower than the second. No equality/identity class exists.

**Hypothesis:** explicitly training the relation type can retain the bread
narrowing while avoiding Coffee/greeting and human-diet/Dog containment errors
seen with the topic classifier. Existing subjects may be inadequate inputs:
they often name a concept or report an event rather than define a sense.

Freeze two input conditions before scoring:

- All 842 cross-group subject-candidate pairs from GDR02, directly as two texts.
  No aboutness wrapper, shortening, candidate selection or new generation.
- All 56 ordered pairs of GDR01's eight manually clarified descriptions. Reuse
  them exactly; these remain diagnostic manual inputs, not an automatic method.

Also run the first two records of each of the five classes in the author's
pinned WordNet test file. These ten examples check implementation and label
orientation, not performance on Nostr data. Preserve their source and exact text.
Keep all logits and normalized scores, not merely the winning class.

Use two CPU threads, batch size four, deterministic evaluation and no silent
truncation. No fitting, score-threshold sweep, paid inference or GPU rental.

Read directional predictions against the unchanged source masks and notes.
Keep related-but-not-broader cases and description-scope issues separate. The
model cannot validate equality; forcing its greeting-equivalence pairs into one
of five classes is a documented limitation, not proof of a new strict parent.
No majority of easy negatives or native benchmark examples can certify a useful
hierarchy. If the available descriptions fail while native definitions work,
investigate that input mismatch rather than simply declaring the model useless.

Sources: [paper](https://aclanthology.org/2024.acl-long.249.pdf),
[model](https://huggingface.co/ChangeIsKey/change-type-classifier/tree/5c833b8a1f6e1f6fc3e27c533ce16e21949c931e),
[author data and code](https://github.com/ChangeIsKey/change-type-classification/tree/71ceac95188eb41eaed4ba831c1c2a212c004a76).
