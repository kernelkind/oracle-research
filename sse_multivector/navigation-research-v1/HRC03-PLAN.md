# HRC03 — Transfer of category-description relationships

## Question

Does the released HierarCaps encoder recognize broader–narrower relationships in clear software, economics, political-idea, and interpersonal-relationship descriptions, alongside food as a control?

This is the user's requested transfer diagnostic, not construction of a hierarchy. HDBSCAN, SSE, subject extraction, masking, and category naming are bypassed. Inputs are manually constructed English category descriptions. No canonical hierarchy is prescribed, and an alternative being related to a child is not itself an error.

## Fixed inputs and checks

Thirty cases, six per domain, with two wordings per case. Each wording has an intended broader category, a narrower category, and a related alternative category that is not an appropriate broader description of that narrower category. The broader relationship is topical refinement, not entailment between complete claims. Parent candidates should have comparable breadth; choosing the shortest description alone should not solve the test.

Before scoring, the primary agent reads every case and a separate clean-context agent reviews the judgments and wording equivalence. Preserve the first draft and the review changes. Freeze the reviewed fixture before loading the model. Metadata and judgments are not part of model input.

Primary checks, reported separately:

- Direction: is the angle for broader → narrower smaller than for narrower → broader?
- Parent choice: is the angle for broader → narrower smaller than for alternative → narrower?
- Wording stability: does each result hold for both wordings of the same case?

Lower angle supports the proposed broader category; it is not a calibrated probability. Direction is mathematically tied to distance from the empty-string root, so it is not an independent measure of semantic parent selection. Save symmetric cosine for comparison, not as another asymmetric relationship score.

Predeclared diagnostics using the same embeddings:

- Cross the two wordings of each role independently (eight combinations per case). Report a case's stability across these combinations, not 240 independent observations.
- Compare the geometric parent choice with same-model cosine, choosing the shorter tokenized parent, and choosing the parent closer to the root. Root distance alone cannot check relevance to this particular child.
- Examine token counts and all unexpected results. Keep ambiguous semantic judgments visible instead of silently repairing labels after seeing scores.

There are thirty constructed case families, not sixty independent random samples. Report each domain separately; no population accuracy, p-values, universal threshold, post-score prompt edits, or hyperparameter search. These examples cannot prove transfer to all domains, fragmented masks, generated labels, or complete navigation paths. Visual concreteness, relation type, wording length, and domain are not fully disentangled.

## Model and execution

Use `malper/hierarcaps-clip-l`, revision `e3aa199d94c438f98628c9697a0b64ef5760b03c`, unchanged from HRC01/HRC02. Use the cached text encoder with projection, normalized 768-dimensional embeddings, and the authors' empty-string root. The angle between A−root and B−A is the same score used in HRC02.

No training, model download, external API, or paid compute. One CPU inference process, two threads, batch size four, float32 eager attention; systemd limits of 6 GiB RAM, no swap, and two CPU cores. Reject token truncation. Output goes to a new exclusive HRC03 directory; preserve all earlier results. Save exact inputs, embeddings, all ordered pair scores, checkpoint hashes, code snapshots, package versions, timings, memory, and the execution command.

Run the production preparation/scoring tests, then independently recompute saved scores and inspect checkpoint loading. Present concise findings with concrete complete input descriptions and scores; no new review UI or hierarchy construction is authorized by this run.

## Why these subject areas

Saved corpus notes establish that these areas occur; they do not make the constructed descriptions a representative corpus sample or direct extraction from these notes:

- Software: note `709b25103a422d0bbaaad8fa9a8247930cd763dc1cf248ee90b083ce3f728f32` says Doom is licensed under the GPL. Source: `sse_multivector/context-counterfactual-source-notes-v1.json`.
- Economics: note `8adc047bd3030501802d8afc9b950466c66853f3e9ceaafb5f3c17ae76292b5d` discusses competition and product prices. Source: `reference_map/crec-115-note-proposal-v2.json`.
- Political ideas: note `c36ed58c0f533ce9840a7cabe2a425b8d1f5b84f137b360bf58cfd270e6df268` discusses government restrictions, financial control, and independence. Source: `sse_multivector/context-counterfactual-source-notes-v1.json`.
- Relationships: note `b843720355752d704f1a167b7b0625d4d28833461c5c6d27c76e8e5b0648aca6` describes keeping roses for a spouse despite different tastes. Source: `reference_map/crec-115-note-proposal-v2.json`.
- Food control: note `ab52ebc67eed9ae6d8e8bd327073ff0ed4e80e267f2b76dfcb8a4468d136c895` describes sourdough bread. Its original text is preserved in `sse_multivector/navigation-research-v1/HRC02/inputs.json`.

Method source: [HierarCaps paper](https://arxiv.org/html/2407.08521v2). Existing implementation and loading checks were previously verified in HRC02.
