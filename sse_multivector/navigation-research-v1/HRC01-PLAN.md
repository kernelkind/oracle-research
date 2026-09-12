# HRC01 — HierarCaps on existing mask text

Test the released HierarCaps text encoder as a possible source of broader–narrower relationships. Do not train anything, construct a hierarchy, change masks, or modify the browser.

## What changes

The source masks stay fixed. This run encodes their exact text with HierarCaps rather than SSE. It is a standalone capability check, not a controlled claim that HierarCaps improves upon SSE: no corresponding SSE score comparison is being run.

Use `malper/hierarcaps-clip-l` at revision `e3aa199d94c438f98628c9697a0b64ef5760b03c`. This is the larger released HierarCaps text encoder, approximately 123 million parameters. Choosing it does not imply it outperforms the base variant. Its image-caption training may transfer poorly to technical and abstract masks; those appear in the selected inputs.

The user authorized an already-trained model only. Inference is local CPU, two threads, batches of four, within a systemd scope capped at 6 GiB RAM with no swap and two CPU equivalents. No paid resources or new model training.

## Inputs and hypothesis

Twenty original masks were selected before any model scores by an independently spawned, clean-context reader. The main agent reviewed the selections before inference. Exact IDs, comparisons, limitations, checkpoint, and original-artifact hash are frozen in [hrc01-fixture.json](hrc01-fixture.json).

**Hypothesis:** The released geometry distinguishes supported broad-to-narrow directions and separates those relationships from obvious cross-topic alternatives on these exact masks.

The fixed directions are bread → sourdough bread → cinnamon sourdough bread; coffee → iced coffee; Bitcoin → Bitcoin workshop; and music → playing music in a coffee shop. The three bread comparisons reuse one nested trio, not three independent examples. Four additional comparisons ask whether a suitable broader mask scores better than a clearly cross-topic alternative for the same specific mask.

Remaining inputs cover ingredients, technical names, knowledge-sharing, advice, and two different activities in a coffee-shop setting. These are inspected without requiring a unique parent. In particular, ice → iced coffee and timing speech → leaving things unsaid are not hard negative examples. Additional detail does not automatically require another navigation level.

The original masks come from `real-note-fine-segmentation-v1/vectors/vector-map.json`. Source notes come from `geometric-hierarchy-v1/GDC09/evidence.json`; each chosen record must match the original vector identity, source-note identity, fragments, and UTF-8 byte ranges. Model input is only the fragments joined with a space, in source order. No generated descriptions, full notes, semantic templates, dictionary lookups, or rewritten text enter the model. Full notes are saved separately for interpretation.

## Calculation and limits

Encode each mask and the empty string, normalizing each output vector to length one. The empty string supplies the author's geometric origin, not a semantic instruction. For proposed broader mask A and narrower mask B, calculate the angle between `A − origin` and `B − A`. Smaller angles support the proposed direction more strongly; they are not probabilities and have no calibrated acceptance threshold here.

This is the paper-defined exterior-angle measure, verified against the [paper, sections 3–4 and 6.1](https://arxiv.org/html/2407.08521v2) and [author code at c8ddc41](https://github.com/TAU-VAILab/hierarcaps/blob/c8ddc41cdb0fcdf39f711875c9c72c14bbbbb0dc/code/train.py#L143). The published HyperLex test adds an image-style prompt; this run deliberately does not because our required input is exact mask text. It is not a reproduction of that benchmark or of the image-retrieval demo.

Save both directions, ordinary cosine, and distance from the origin. Directional angle ordering and distance ordering are mathematically dependent; they must not be counted as independent evidence. Comparisons against other subjects are necessary to inspect whether the direction is semantically useful. Equal embeddings have no defined directional angle.

Preserve all 400 ordered pair scores, embeddings, original source notes, exact masks, loading diagnostics, input/checkpoint hashes, package versions, and the executed runner. Never truncate an input silently or accept randomly initialized text parameters. Do not fit a threshold after seeing results.

This small, selected pilot can expose concrete capability or counterexamples. It cannot establish corpus-wide accuracy, generate missing broader categories, or validate parent–child construction. A failure is specific to this checkpoint, mask-only input, and score—not every broader–narrower embedding model.
