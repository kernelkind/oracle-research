# GPRv1 — repetition at two subject levels

Completed 2026-09-20. **Mixed result, not a clean confirmation that repetition
helps broad subjects and hurts detailed ones.** Broad-target similarity changed
little. Detailed-target similarity increased slightly on average, while
separation from a different retuning condition decreased.

## Inputs and intervention

One unchanged real post, previously used in masking diagnostics:

> I have a guitar question. Is it normal to have to retune your guitar every
> time you put a capo on and take it off?
>
> I'm not talking like the 8th fret, I'm talking like the 3rd fret.
>
> Does this mean my guitar needs to be set up or is that just how it goes? The
> electric guitar I play now, which I love, has this behavior, and I don't
> remember experiencing it before with other guitars.
>
> (Jimmy) Paging [encoded Nostr identifier]
>
> #guitar

The identifier is abbreviated only in this report; the encoder receives the
complete byte-identical post. Targets are **Guitars** and **Guitar retuning when
putting on or taking off a capo**, previously fixed diagnostic subjects, not
newly generated ASv6.48 outputs.

The broad core selects only `guitar` in the retuning question. The detailed core
selects `retune` + `guitar every time you put a capo on and take it` + `off`.
At both levels the same additions are tested: the hashtag's guitar, the other
four prose mentions, and all five extra mentions. Every detailed mask retains
the condition `every time` and both capo actions.

All-mentions variants exactly reproduce the saved MPv3.32 T03/T04 masks. Core
variants are diagnostic removals from those masks, not original model outputs
or newly approved replacements. MPv3.32 was chosen because its condition was
retained and previously accepted; using MPv3.34's unresolved condition omission
would combine two questions. No prompt was rerun or changed.

Each of the six guitar mentions was also encoded alone to test dependence on
the initial occurrence. Thirteen masks and fifteen independently encoded,
hand-authored comparison texts were fixed before inference. Those texts cover
general guitars, matched violin subjects, capo-triggered retuning, retuning
after string replacement, and capo use without retuning. They are not corpus
notes, gold hierarchy nodes, or independent statistical replicates.

## Measurements

Average cosine similarity to three comparison texts per family; not accuracy,
membership probability or subsumption scores. All individual scores, rankings
and margins are in [run/comparison.json](run/comparison.json).

### Broad target: Guitars

| Mask | Selected tokens | General guitars | Violins | Capo-triggered retuning |
| --- | ---: | ---: | ---: | ---: |
| Core mention | 1 | 0.865 | 0.481 | 0.467 |
| + hashtag | 3 | 0.825 | 0.430 | 0.414 |
| + other prose mentions | 6 | 0.874 | 0.485 | 0.454 |
| + all five extra mentions | 8 | 0.870 | 0.474 | 0.445 |

All-mentions changes target similarity by only +0.0045 versus the chosen core;
two target wordings improve and one declines. Its guitar-minus-violin margin
rises from 0.384 to 0.395, with all matched distinctions retained. This is not
evidence of a practically important improvement in broad-subject grouping.

The six single-mention target averages are 0.859, 0.865, 0.861, 0.852, 0.876 and
0.759 in source order. All-mentions is not better than the strongest single
mention (`guitars` in the comparison with other instruments of that type).
That mention was not selected after results as a replacement mask. These
differences show sensitivity to source position/word form/tokenization; the
experiment does not isolate those factors. Six lexical mentions pool eight
tokens because the plural and hashtag each select two token pieces.

### Detailed target: capo-triggered guitar retuning

| Mask | Selected tokens | Intended retuning | String-replacement retuning | Capo use without retuning | General guitars |
| --- | ---: | ---: | ---: | ---: | ---: |
| Core fragments | 18 | 0.870 | 0.655 | 0.805 | 0.367 |
| + hashtag | 20 | 0.890 | 0.683 | 0.825 | 0.458 |
| + other prose mentions | 23 | 0.895 | 0.733 | 0.842 | 0.618 |
| + all five extra mentions | 25 | 0.882 | 0.729 | 0.830 | 0.667 |

Unlike the bread test, all-mentions increases average target similarity
(+0.0114); two paraphrases improve and one declines. It also increases all
three general-guitar similarities, and increases all three alternative-trigger
similarities more than their matched target similarities.

The target-minus-alternative-trigger margin decreases from 0.215 to 0.152.
Every matched comparison shows that decrease. The average margin against capo
use without retuning decreases from 0.066 to 0.052, but that pattern is not
universal: two matched margins decline and one improves. **Every target anchor
still outranks every anchor in both of these contrast families for all four
detailed variants.** No wrong ranking was introduced by this test.

The gap to general-guitar anchors decreases from 0.504 to 0.215. That indicates
a change in emphasis; proximity to a legitimate broader subject is not itself
incorrect. Neither these cosine gaps nor their changes are calibrated to
HDBSCAN behavior or an exact level of abstraction.

## Conclusion and recommended decision

This does not establish either a universal advantage of exhaustive repetition
or a universal benefit of removing it. It does corroborate that additional
mentions of a component can substantially reweight a detailed representation.
Target resemblance alone would miss the reduced distinction from a different
retuning trigger. The near-unchanged broad result does not establish that
covering all six mentions is necessary for a useful general-guitar vector.

Together with BPRv1, this is reason to question treating every omitted,
already-covered partial meaning as an automatic mask failure. It is not a
reason to ban repetitions or to claim either hierarchy would fail.

Recommended next step, not executed: prepare a narrow experimental prompt
delta removing mandatory accumulation of already-covered partial meanings,
while preserving the complete target meaning and coverage of repetitions
expressing the whole supplied subject. Do not silently convert that proposal
into a frozen policy or relabel old assessments. MPv3.34 remains unchanged.

## Execution and verification

One offline CPU FP32 invocation, 28 vectors, unchanged production worker,
checkpoint and model artifacts. Python 3.13.12, torch 2.13.0+cpu, transformers
4.57.1 and tokenizers 0.22.2 match the BPRv1 runtime whose seven saved-vector
parity checks passed. Those controls were reused as evidence, not rerun.
Collection verifies matching runtime/model identities, source hashes and
request/output binding. The required historical `container_image` field is
configuration provenance only; actual execution was local, not Docker.

The input test first failed because the study implementation was absent, then
passed. Five existing worker tests also passed; actual inference exercises the
production encoder and selection code. No new model/dependency downloads,
paid resources, frontier calls, baseline prompt reruns, clustering, UI edits or
production changes. All prior artifacts are preserved.

- [PLAN.md](PLAN.md): prospective hypotheses, controls and interpretation limits.
- [run/inputs.json](run/inputs.json): full note, exact spans and all anchor texts.
- [run/comparison.json](run/comparison.json): mechanically collected measurements.
- [run/result/worker-receipt.json](run/result/worker-receipt.json): encoder output provenance.
- [study.py](study.py) and [run-local.sh](run-local.sh): reproducible experiment code.
