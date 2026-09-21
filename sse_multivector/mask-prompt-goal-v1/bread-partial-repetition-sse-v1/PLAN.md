# BPRv1 — partial repetition and SSE

Prospective plan, written before inference. One saved real note, five masks,
twelve hand-authored diagnostic anchors, seven intentional saved-vector parity
checks. No prompt generation, prompt revisions, HDBSCAN, or hierarchy changes.

## Question and competing explanations

Does adding repeated bread references to the saved MPv3.34 mask improve its
representation of the author's pleasure at the recently tried Irish soda bread
recipe's success, or emphasize the general bread topic at that meaning's expense?

Possibilities: partial repetition improves target representation; it favors the
shared broad topic and weakens distinctions; it has little effect; or this SSE
configuration cannot resolve the close contrasts even before additions. These
are not necessarily exclusive: target similarity can rise while discrimination
falls. Do not infer hierarchy quality from vector movement alone.

## Fixed inputs and intervention

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

## Execution and checks

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

## Analysis and next decision

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
