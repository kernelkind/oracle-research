# Shared hierarchy-encoder geometry

SRR01–SRR03 found false parents from independent relation classification.
HIT01 tests a different representation: entity embeddings trained jointly for
parent proximity and broader-to-narrower radial ordering. No group or hierarchy
is changed, and no classification threshold is fitted to these notes.

**Hypothesis:** hierarchy training produces useful direction and parent preference
on the fixed meanings, rather than merely keeping associated words close.
Compare `sentence-transformers/all-MiniLM-L12-v2` revision
`a50ef00143b4d5391434df20ae11632588ac25be` with its WordNet-trained HiT version,
`Hierarchy-Transformers/HiT-MiniLM-L12-WordNetNoun` revision
`d6389aa835ddae03cc88809bb8a0255da4ab454c`. Choose the released hard-negative
variant before seeing results because related-but-not-parent cases matter here.
MiniLM-L12 is the architecture used in the paper's cross-ontology transfer test.

Freeze all 842 subject pairs and 56 manual-description pairs from SRR01, all
56 definition pairs from SRR02 and all 56 name/definition pairs from SRR03.
Add all 12 ordered pairs of the author's four example names: computer, personal
computer, fruit and berry. These familiar native controls are not a holdout
generalization benchmark. Total: 1,022 ordered pairs for each encoder.

Use the author's Transformer + attention-mask mean pooling, including special
tokens, without the base model's final unit normalization. Both encoders receive
the exact same strings. No instructions or generated new descriptions. Refuse
truncation beyond the HiT checkpoint's 128-token limit. Preserve every raw vector,
token count, model/input hash and ordered pair. CPU only, two threads, batch four;
load models sequentially. The two public checkpoints total about 267MB.

The published score is `-distance + weight * (child_radius - parent_radius)`.
It requires validation-set calibration, which is not supplied by these frozen
notes. Instead, inspect its two ingredients without fitting a weight:

- For a defensible strict refinement, does the narrower meaning lie farther
  from the origin? This determines preference between the two input directions
  for every positive weight, but is not sufficient for a semantic edge.
- For the same child, is an incorrect parent both closer and nearer the origin
  than a valid parent? If so, it outranks the valid parent for every positive
  weight. This cannot be repaired merely by calibrating that weight or a cutoff.
- Preserve all distances/radii to inspect other candidate relationships and
  compare with the unchanged base encoder. Do not invent one gold taxonomy.

Use the author's Geoopt geometry and check it against the closed-form distance.
No arbitrary default weight is a production decision. Radius ordering alone
cannot establish equivalence, transitivity of selected edges, meaningful
note membership, faithful whole-group descriptions or complete browsing paths.

Primary sources: [HiT paper](https://arxiv.org/html/2401.11374v3), §§3–4 and
appendix B; [pinned source](https://github.com/KRR-Oxford/HierarchyTransformers/tree/1b68f00ec52ee5923cec907582a007810b28d4d8),
especially `models/hierarchy_transformer/hit.py` and `evaluation/hit_eval.py`;
[released hard-negative checkpoint](https://huggingface.co/Hierarchy-Transformers/HiT-MiniLM-L12-WordNetNoun/tree/d6389aa835ddae03cc88809bb8a0255da4ab454c).
