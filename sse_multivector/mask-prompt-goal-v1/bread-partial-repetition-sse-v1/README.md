# BPRv1 — bread partial-repetition result

Completed 2026-09-20. The additions moved this representation toward general
bread and reduced its similarity to all three target paraphrases. They also
reduced all three matched success-versus-failure margins. The distinctions did
not disappear: every success paraphrase still ranked above every failed-recipe
paraphrase in all five variants. No hierarchy or clustering was run.

## Fixed subject and actual masks

Subject: **The author was very pleased that the recently tried Irish soda bread
recipe turned out great.** This is saved ASv6.23 subject N072-S006; the mask is the
actual MPv3.34 F05 output, not a regenerated or manually improved baseline.

Original selected fragments:

> An Irish soda bread recipe I tried out recently,
>
> I was very pleased to see this recipe turned out great!

Every variant retains those exact two spans and the complete unchanged source
note. The only additions are:

- `tags`: `bread` in `#bread`, and `sodabread` in `#sodabread`.
- `generic`: `Soda bread` in `Soda bread usually has currants but recipes vary`.
- `tags_generic`: both additions above.
- `all_bread`: both above, plus `soda bread` in `The soda bread I usually made
  doesn't work at the high altitude I live at now`.

These are controlled interventions, not newly approved masks. Exact UTF-8 spans,
the complete post, source hashes and every comparison text are in
run/inputs.json (`run/inputs.json`).

## Measurements

Each column averages cosine similarities to three fixed, independently encoded
comparison texts. Higher means more similar, not probability or membership.
General comparison texts are `Soda bread.`, `Irish soda bread.`, and
`Soda bread recipes.` The other families are full-sentence paraphrases, not
length-matched general-category controls. Absolute family ordering alone is
therefore not a correctness test.

| Mask | Selected tokens | Successful-recipe reaction | Failed-recipe reaction | General bread | Happy about finding a baking website |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 22 | 0.887 | 0.612 | 0.617 | 0.560 |
| + hashtags | 28 | 0.838 | 0.628 | 0.743 | 0.508 |
| + generic sentence's bread phrase | 26 | 0.832 | 0.637 | 0.774 | 0.489 |
| + hashtags and generic phrase | 32 | 0.766 | 0.619 | 0.828 | 0.436 |
| + those and old recipe's bread phrase | 34 | 0.724 | 0.615 | 0.860 | 0.396 |

The original's three closest anchors are all target paraphrases. With all bread
additions, the three closest are all general-bread texts. Each addition variant
lowers every target-paraphrase similarity and raises every general-bread
similarity relative to the original. This is consistent across these wordings,
not only an average effect.

More importantly, the average target-minus-failed-recipe margin falls from
0.275 to 0.210 / 0.195 / 0.146 / 0.109. This gives evidence of weakened separation
from a meaningfully different reaction, beyond movement toward a legitimate
broader subject. No comparison crosses from success to failure. The target-minus-
website margin stays approximately 0.327–0.343: not every distinction worsens,
and the experiment does not establish confusion about which event caused joy.

All 60 individual scores, rankings, margins and deltas were calculated by
study.py and are retained in run/comparison.json (`run/comparison.json`).

## Interpretation and limits

This supports reconsidering the assumption that every repeated partial meaning
is a harmless or beneficial addition to a detailed mask. It does not establish
that all repetition is harmful, that the original mask is uniquely optimal, or
that HDBSCAN would misplace any of these vectors. Similarity changes are not a
validated measure of exact semantic equivalence. The general anchors are not
gold parents and synthetic paraphrases are not independent corpus samples.

The experiment does not separate repetition count, source context and which
token pieces are selected. Both hashtags and ordinary prose had the same
direction of effect, so a hashtag-only explanation is insufficient here; a
universal policy still needs evidence beyond this one note and historical
detailed subject.

The prior F05 claim that omitted bread hashtags were necessarily a masking
failure is not justified. That historical assessment is preserved, not silently
rewritten. MPv3.34 and all other prompts remain unchanged.

Suggested next test, NOT executed: use a different note with a broad subject and
its detailed child to compare partial repetition at both levels. This would
check whether it helps represent the broad heading while weakening the detailed
one, rather than jumping to a blanket anti-repetition rule.

## Execution and verification

One CPU FP32 SSE invocation produced 24 vectors: five treatments, twelve
synthetic comparison texts, and seven intentional saved-vector parity checks.
No frontier calls, baseline prompt reruns, model downloads or paid services.
The original checkpoint, model artifacts and production worker are unchanged;
the worker verifies their recorded hashes. Preparation and collection bind
source files, plan, request and outputs through hashes. Seven local tests passed
(two study checks and five existing worker tests), and actual inference used
the production worker codepath.

The Docker socket was inaccessible. Local execution used Python 3.13.12,
torch 2.13.0+cpu, transformers 4.57.1 and tokenizers 0.22.2. The saved reference
runtime used Python 3.12.3, torch 2.12.1+cu130, transformers 4.41.2 and tokenizers
0.19.1, also with CPU inference. The local environment reused cached packages
and downloaded a 15.9 MiB numpy dependency, not model weights.

All seven parity checks passed the prospective tolerances with identical
tokenization. Minimum cosine to saved output: 0.9999999999999157. Maximum
component difference: 1.7881393432617188e-7. This is a measured runtime parity
check, not a claim that the environments are identical. The worker's required
`container_image` field retains the historical configured reference; it does
not mean a container ran. Actual local execution is in
run-local.sh (`03bd9e45:sse_multivector/mask-prompt-goal-v1/bread-partial-repetition-sse-v1/run-local.sh`), with worker stdout/stderr and the worker's own
receipt retained under `run/`.

The result preserves all earlier artifacts. No prompt policy, UI, membership or
production behavior was changed.

## BPRv1 study design

Prospective plan, written before inference. One saved real note, five masks,
twelve hand-authored diagnostic anchors, seven intentional saved-vector parity
checks. No prompt generation, prompt revisions, HDBSCAN, or hierarchy changes.

### Question and competing explanations

Does adding repeated bread references to the saved MPv3.34 mask improve its
representation of the author's pleasure at the recently tried Irish soda bread
recipe's success, or emphasize the general bread topic at that meaning's expense?

Possibilities: partial repetition improves target representation; it favors the
shared broad topic and weakens distinctions; it has little effect; or this SSE
configuration cannot resolve the close contrasts even before additions. These
are not necessarily exclusive: target similarity can rise while discrimination
falls. Do not infer hierarchy quality from vector movement alone.

### Fixed inputs and intervention

Use F05's complete byte-identical note and actual saved two-span mask. The subject
is historical ASv6.23, not newly generated ASv6.48. Keep all punctuation and URLs
in the note; select only declared spans. The five variants are baseline, plus
`bread`/`sodabread` from hashtags, plus `Soda bread` from the generic currants
sentence, plus both, and plus those and `soda bread` from the old failed recipe.
Never modify the baseline in light of output. These added spans are experimental
interventions, not newly approved semantic masks.

Twelve independent, fully selected anchor texts are fixed in study.py before
inference: three target paraphrases, three corresponding failed-recipe reactions,
three general soda-bread subjects, and three happy reactions to finding a baking
website. The latter distinguishes the event causing the reaction. They are
synthetic diagnostics, not corpus notes or independent statistical samples.

### Execution constraints and checks

Use existing worker.py, the saved checkpoint, tokenizer artifacts, projection,
CPU FP32 and batch size 8. No paid services or new model downloads. Docker is
inaccessible in this session, so use a local dependency environment. Record its
versions and execution separately. The worker schema requires the historical
container reference: that configured field does NOT establish that Docker ran.

Before interpreting the bread comparison, all seven parity vectors must have
identical tokenization, cosine >= 1 - 1e-9 and max component error <= 1e-6 against
the saved coffee-shop outputs. If not, report the discrepancy and withhold a
semantic conclusion; do not quietly change tolerances. The worker itself checks
checkpoint/model/request hashes. Keep experiment source hashes unchanged.

### Analysis and next decision

Report every anchor score, family mean, target-minus-contrast margins, rankings,
and selected token counts. Compare each variant to the same baseline. Target vs
failed-recipe and wrong-event contrasts test distinctions; relative movement
toward the broad subject is diagnostic, not intrinsically a correctness failure.
No cosine threshold means category membership. Do not call a small movement an
established downstream loss or claim that paraphrase replicates estimate corpus
accuracy. If the baseline already fails, do not attribute that failure to added
repetition. Inspect whether the effects agree across anchor wordings.

Either result informs whether to keep enforcing blanket partial-repetition
coverage. If it helps here, preserve it pending wider evidence; if it hurts,
recommend reconsideration with a confirming case; if mixed/inconclusive, do not
rewrite the prompt or declare omitted tags incorrect from this example. This
probe cannot validate an entire hierarchy or resolve all mask semantics.
