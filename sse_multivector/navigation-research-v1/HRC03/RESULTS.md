# HRC03 — Transfer exists, but parent choice is wording-sensitive

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

[Plan](../HRC03-PLAN.md) · [Pre-score review](../HRC03-PRESCORE-REVIEW.md) · [Frozen inputs](fixture.json) · [Every case in readable form](CASES.md) · [All analysis](analysis.json) · [All 32,400 scores](scores.json) · [Embeddings](embeddings.json) · [Execution](EXECUTION.md) · [Verification](verification.json).

Eight new preparation/scoring tests and nine unchanged mask tests pass. Independent verification rebuilt all 180 input records, recomputed all 32,400 scores and 120 matched checks, and reproduced all 181 embeddings bit-for-bit through the full CLIP model. No truncation: the longest input used 16 of 77 allowed tokens.

The main runner took 10.189 seconds including loading/hashing/scoring; embedding inference itself took 1.543 seconds. Peak process memory was about 724 MiB, and independent verification about 757 MiB. Both model invocations used offline CPU scopes bounded to 6 GiB RAM, no swap, and two CPUs. No training or paid compute; earlier artifacts were preserved.
