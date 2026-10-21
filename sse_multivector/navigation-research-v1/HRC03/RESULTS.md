# HRC03 — Transfer exists, but parent choice is wording-sensitive

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../../docs/experiments/README.md#reading-the-research-records).

HierarCaps recognized many relationships outside food. However, changing how a category was described could change where the model placed it. These results do not support using its angle score as a dependable standalone parent selector yet.

## What was tested

Thirty manually constructed category relationships: six each in software, economics, political ideas, interpersonal relationships, and food. Each had two wordings, giving sixty matched comparisons. The model received only the category description strings—no notes, masks, instructions, examples, or intended answers.

For example, given the narrower description `A central bank raising interest rates`, we compared `Monetary policy` with `Fiscal policy` as possible broader categories. Judgments and inputs were reviewed before scoring. No input or expected answer was changed after seeing scores.

Same released checkpoint and score as HRC01/HRC02; no training. These are constructed descriptions, not a representative sample of generated corpus labels. The two wordings are paired observations of each case, not independent cases.

## Results by subject area

“Intended” means the parent selected in the pre-score review. Counts describe this fixture; they are not population accuracy. Some alternative-category judgments have qualifications below.

| Area | Angle chose intended parent | Cosine chose intended parent | Cases where angle chose intended in both wordings |
|---|---:|---:|---:|
| Software | 6/12 | 10/12 | 1/6 |
| Economics | 12/12 | 9/12 | 6/6 |
| Political ideas | 11/12 | 12/12 | 5/6 |
| Interpersonal relationships | 10/12 | 9/12 | 4/6 |
| Food control | 10/12 | 10/12 | 5/6 |

The angle selected the intended parent in 49/60 comparisons, versus 50/60 for ordinary cosine from the same embeddings. It corrected five choices cosine got wrong, but changed six of cosine's intended choices to the alternative. This does not demonstrate an advantage over cosine for this task; neither is thereby established as a hierarchy-construction method.

The broader→narrower direction check favored the declared direction in 59/60 comparisons. That check is mathematically tied to which vector lies closer to the empty-string root. It is not independent confirmation that the model picked a relevant parent.

Simple shortcuts did not explain all the intended choices: always choosing the parent closer to the root favored the intended parent in 29/60 comparisons; choosing the shorter tokenized parent favored it in 20, the alternative in 17, and tied in 23. These baselines do not isolate the cause of any particular error.

## A clear successful relationship

Narrower category: `Tariffs on imported goods`.

| Candidate parent | Angle, lower preferred | Cosine, higher more similar |
|---|---:|---:|
| International trade | 88.0047° | 0.889494 |
| Domestic sales taxation | 118.6420° | 0.851557 |

This preference survived all eight combinations of the two wordings for child and both parents. It is useful evidence that the model can recognize a nonvisual economic relationship. It does not establish economics-wide reliability.

## A clear wrong parent choice

Narrower category: `Blocking cross-site tracking`.

| Candidate parent | Angle, lower preferred | Cosine, higher more similar |
|---|---:|---:|
| Web browser privacy | 114.6285° | 0.860399 |
| Web browser appearance | 110.3737° | 0.851995 |

Blocking tracking is a privacy subject; it is not a refinement of browser appearance. Cosine favored privacy, but the angle favored appearance. This is not simply evidence that the encoder has no notion of the relevant software meaning.

## Rewording only the parent can reverse the choice

Keep these two inputs fixed:

- Narrower category: `A central bank raising interest rates`.
- Alternative parent: `Fiscal policy`, angle 93.3048° and cosine 0.848944.

Change only the intended parent's wording:

| Intended parent text | Angle | Cosine | Parent selected by angle |
|---|---:|---:|---|
| Monetary policy | 84.8441° | 0.898768 | Intended |
| Central-bank management of money and borrowing conditions | 116.0265° | 0.871342 | Alternative: Fiscal policy |

Both intended descriptions reasonably cover central-bank interest-rate increases. Cosine still favors the intended parent in both versions, but the angle reverses its choice. This is a controlled wording change using the saved embeddings, not another model run.

The same effect appears in software licensing. Hold the narrower input `Programs released under the GNU General Public License` and alternative `Closed-source software` fixed. The alternative's angle is 94.3780°.

| Intended parent text | Angle | Parent selected by angle |
|---|---:|---|
| Open-source software | 87.9191° | Intended |
| Software whose source code users may inspect, modify, and redistribute | 108.0246° | Alternative: Closed-source software |

The short intended parent wins all four combinations of child and alternative wording; the expanded intended parent loses all four. These observations demonstrate wording sensitivity. They do not isolate whether length, particular words, or the way the learned geometry represents explanatory detail causes it.

Across the full experiment, only 8/30 cases retained the intended parent across all eight combinations of the three descriptions' wordings. These are not 240 independent trials. Some paraphrases have scope issues; the monetary-policy and GPL examples provide concrete evidence that the instability is not solely a label-ambiguity problem.

## All unexpected matched choices

Every exact input and score, including successful cases, is in [CASES.md](CASES.md). The frozen fixture and its counts remain unchanged after review.

| Case | What the angle selected instead | Interpretation |
|---|---|---|
| S01 wording 1 | Browser appearance instead of privacy for blocking tracking | Clear mismatch; detailed above. |
| S02 wording 2 | Ease of use instead of security for checking software signatures | Clear mismatch. The wording supplies verification, not usability. |
| S03 wording 2 | Withheld source code instead of inspect/modify/redistribute rights for GPL software | Clear mismatch. It also reverses the expected broader–narrower direction. |
| S04 wording 1 | File organization instead of preventing data loss for backups | Weaker diagnostic: file organization can include managing backups. Its second wording, arranging and categorizing files, is more specific. |
| S06 wording 1 | Application software instead of operating systems for Linux distributions | Defensible mismatch: distributions contain applications, but are not therefore a refinement of application software. |
| S06 wording 2 | Programs carrying out tasks for users instead of system software managing hardware/programs | Ambiguous alternative: this supposed paraphrase of application software can also describe system software. Do not treat it as a clean model failure. |
| P03 wording 1 | Electoral representation instead of decentralization for transferring power to local councils | Defensible mismatch: the supplied description concerns distribution of authority, not elections. Margin is only 0.9074°. |
| R02 wording 1 | Giving advice instead of respecting boundaries for accepting a friend's refusal | Clear mismatch: the description contains no advice-giving. |
| R05 wording 1 | Persuasion instead of consideration for accommodating a spouse's different preferences | Defensible mismatch: accommodation does not state an attempt to change the spouse's preferences. Margin is only 0.8393°. |
| F03 wording 1 | Growing food instead of preservation for freezing homegrown vegetables | Preservation is the direct intended parent, but handling a harvest can also belong in a broader food-growing workflow. Less decisive than the privacy example. |
| F03 wording 2 | Cultivating plants instead of preventing spoilage for garden vegetables in a freezer | The direct action is storage, though garden produce contributes real growing-related meaning. Same case as the previous row, not independent confirmation. |

Small positive margins should not be overinterpreted either: R03 wording 1 favors emotional over financial support by only 0.0101°. No cutoff was fitted to convert these margins into confidence.

## What this establishes—and what it does not

There is useful transfer to clear categories outside the model's original image-caption setting. A blanket claim that abstract or nonfood categories cannot work is contradicted by these examples. But stronger performance in one small constructed domain does not establish general domain competence; relation type, wording, and explanatory detail are not fully controlled across domains.

More importantly for the proposed system, semantically reasonable alternative descriptions of the same category can receive different parent placements. That matters if another model will generate the category descriptions. This experiment does not validate that label generator, actual HDBSCAN node descriptions, parent–child paths, corpus coverage, or note discovery.

The justified next decision is to keep the HierarCaps angle unvalidated as a standalone placement rule. These results warrant investigating the demonstrated wording-sensitive geometry before adopting it, not declaring the whole architecture impossible or changing more components at once. No subsequent experiment or hierarchy construction was run here.

## Artifacts and verification

[Plan](RESULTS.md#hrc03-study-design) · [Pre-score review](../HRC03-PRESCORE-REVIEW.md) · [Frozen inputs](fixture.json) · [Every case in readable form](CASES.md) · All analysis (`analysis.json`) · All 32,400 scores (`scores.json`) · Embeddings (`embeddings.json`) · [Execution](RESULTS.md#hrc03-runtime-and-verification) · Verification (`verification.json`).

Eight new preparation/scoring tests and nine unchanged mask tests pass. Independent verification rebuilt all 180 input records, recomputed all 32,400 scores and 120 matched checks, and reproduced all 181 embeddings bit-for-bit through the full CLIP model. No truncation: the longest input used 16 of 77 allowed tokens.

The main runner took 10.189 seconds including loading/hashing/scoring; embedding inference itself took 1.543 seconds. Peak process memory was about 724 MiB, and independent verification about 757 MiB. Both model invocations used offline CPU scopes bounded to 6 GiB RAM, no swap, and two CPUs. No training or paid compute; earlier artifacts were preserved.

**Selected data:** Compact pair-score results, inputs and parameters for `HRC03` are selected for release as `numerical/pair-scores-9c5f98ada943ce6b` in the [publication catalog](../../../docs/experiments/publications.csv). These compact exports use a different format. Other cited artifacts remain separate originals.

## HRC03 study design

### Question

Does the released HierarCaps encoder recognize broader–narrower relationships in clear software, economics, political-idea, and interpersonal-relationship descriptions, alongside food as a control?

This is the user's requested transfer diagnostic, not construction of a hierarchy. HDBSCAN, SSE, subject extraction, masking, and category naming are bypassed. Inputs are manually constructed English category descriptions. No canonical hierarchy is prescribed, and an alternative being related to a child is not itself an error.

### Fixed inputs and checks

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

### Model and execution

Use `malper/hierarcaps-clip-l`, revision `e3aa199d94c438f98628c9697a0b64ef5760b03c`, unchanged from HRC01/HRC02. Use the cached text encoder with projection, normalized 768-dimensional embeddings, and the authors' empty-string root. The angle between A−root and B−A is the same score used in HRC02.

No training, model download, external API, or paid compute. One CPU inference process, two threads, batch size four, float32 eager attention; systemd limits of 6 GiB RAM, no swap, and two CPU cores. Reject token truncation. Output goes to a new exclusive HRC03 directory; preserve all earlier results. Save exact inputs, embeddings, all ordered pair scores, checkpoint hashes, code snapshots, package versions, timings, memory, and the execution command.

Run the production preparation/scoring tests, then independently recompute saved scores and inspect checkpoint loading. Present concise findings with concrete complete input descriptions and scores; no new review UI or hierarchy construction is authorized by this run.

### Why these subject areas

Saved corpus notes establish that these areas occur; they do not make the constructed descriptions a representative corpus sample or direct extraction from these notes:

- Software: note `709b25103a422d0bbaaad8fa9a8247930cd763dc1cf248ee90b083ce3f728f32` says Doom is licensed under the GPL. Source: `sse_multivector/context-counterfactual-source-notes-v1.json`.
- Economics: note `8adc047bd3030501802d8afc9b950466c66853f3e9ceaafb5f3c17ae76292b5d` discusses competition and product prices. Source: `reference_map/crec-115-note-proposal-v2.json`.
- Political ideas: note `c36ed58c0f533ce9840a7cabe2a425b8d1f5b84f137b360bf58cfd270e6df268` discusses government restrictions, financial control, and independence. Source: `sse_multivector/context-counterfactual-source-notes-v1.json`.
- Relationships: note `b843720355752d704f1a167b7b0625d4d28833461c5c6d27c76e8e5b0648aca6` describes keeping roses for a spouse despite different tastes. Source: `reference_map/crec-115-note-proposal-v2.json`.
- Food control: note `ab52ebc67eed9ae6d8e8bd327073ff0ed4e80e267f2b76dfcb8a4468d136c895` describes sourdough bread. Its original text is preserved in `sse_multivector/navigation-research-v1/HRC02/inputs.json`.

Method source: [HierarCaps paper](https://arxiv.org/html/2407.08521v2). Existing implementation and loading checks were previously verified in HRC02.

## HRC03 runtime and verification

Pre-score hashes:

- Fixture: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`
- Plan: `f871a4bf1712f24b74a970267d1bd400e0bace12817bc6359b14ab42a999b442`
- Pre-score review: `f05dfec76955fb88779c12aa399b40d652933fd467fa44873c4b5e7360014c28`

No network access was needed: the exact checkpoint was already cached. 180 input records plus the empty-string root were encoded. All 32,400 ordered description pairs were saved. Encoding took 1.543 seconds; total runner time, including checkpoint hashing/loading and all-pair scoring, was 10.189 seconds. The process's `/proc/self/status` high-water memory was 741,348 KiB (about 724 MiB). These numbers exclude planning and semantic review. No training, external API inference, or paid compute.

The analysis used only saved embeddings and pair scores. `analysis.json` contains every matched and crossed-wording check with a key explaining each field. For each case, independently varying the broader, narrower, and alternative wording gives 2×2×2 combinations. A positive alternative-minus-intended angle favors the intended parent; a positive intended-minus-alternative cosine favors it by symmetric similarity. Baselines use only token count or distance from the empty-string root. Exact ties are reported separately (numerical comparison tolerance 1e-8); none of the model parent-angle or direction checks were near that tolerance. These diagnostics and their scope were stated in the pre-score plan.

Independent verification is recorded in `verify.py` and `verification.json`; it reconstructs the inputs and numerical results rather than reusing either runner's scoring functions.
