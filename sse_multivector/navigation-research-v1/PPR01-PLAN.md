# Grounded subject descriptions in a phrase-trained representation

## Decision being tested

CAP04's word patterns miss a shared rosemary/bread relationship and split
morning greetings by wording. Its coffee/experience pattern also ignores what
is being experienced. Before building more candidates from words, test whether
encoding the **complete existing subject descriptions** supplies useful local
semantic neighborhoods. This is not another parent classifier, a replacement
SSE experiment, or an equivalence decision rule.

Freeze CAP04's 945 records, including every subject, source mask, alias and full
original. Encode the `subject` field, not the original post or concatenated mask.
These descriptions are existing generated interpretations, not certified facts.
Their median length is nine whitespace-separated words, maximum 37. Retain
duplicate descriptions and masks as evidence; cache identical input strings for
inference only. Never let several records from one note fill a neighborhood.

## Model fit and limits

Phrase-BERT uses mean-pooled BERT embeddings and a Euclidean triplet loss.
Training pairs phrases with generated paraphrases and with masked surrounding
contexts; negatives use corrupted phrases or random contexts. Its native inputs
therefore include both short phrases and longer contextual text. The strongest
paraphrase accuracy figures require an additional trained classifier, which is
not part of this test. Its published neighbors also include associated actions,
not just equivalent meanings. These facts justify testing topical affinity, not
calling distance equivalence or containment.[^1]

Compare the author's released Phrase-BERT with its documented Sentence-BERT
starting model. Both checkpoints specify mean pooling, 128-token inputs and no
normalization layer. The official example provides three phrases and expected
cosines as an implementation control.[^2] This compares released checkpoints;
it does not reproduce training or isolate each training objective.

## Hypothesis and competing explanations

Hypothesis: with complete descriptions, Phrase-BERT can make source-supported
shared subjects accessible despite different wording or dispersed source masks,
without the specific false attachments produced by CAP04. Its starting model
may already supply this capability; that would argue against adding a specialist.

Competing explanations: apparent gains may come from shared words, shared
reporting style, a broader associated topic, or a meaning supplied incorrectly
by the saved subject. A low score may reflect input mismatch or sparse subject
coverage, rather than proving an impossible relationship. Preserve full source
evidence so these explanations can be checked.

Before any scores, select these four diagnostics:

| Query record | Existing subject | Evidence to inspect |
|---|---|---|
| 258 / N017 | The author wishes readers a good morning. | All ten known morning-greeting notes, including the three omitted by the literal `morning greeting` pattern. |
| 669 / N037 | Rosemary in sourdough bread. | N072's explicit addition of rosemary to Irish soda bread; other bread and rosemary evidence. Different bread types need not be equivalent to share a valid parent. |
| 572 / N094 | Decaffeinated-coffee drinkers drink coffee for the experience of drinking coffee. | N086's coffee-taste experience versus N065's coffee-shop operators experiencing loss of internet. Coffee shops may share a broader topic without describing the same experience. |
| 484 / N100 | Food preservation. | N022's beet freezing and N013's stock canning, plus any other returned preservation evidence. Affinity alone does not establish broader/narrower direction. |

Record every score. For each query and metric, inspect the nearest ten distinct
other notes under **both** models, retaining the exact record that supplies each
score. Inspect the fixed evidence above even if it falls outside those ten.
Unknown neighbors are not automatic negatives. Classify the actual common
meaning before judging usefulness; do not demand identical claims, attitudes,
ingredients or actions. Do not infer a precision/recall estimate from four
diagnostics or select a cutoff after seeing their scores.

Euclidean distance on unnormalized output is primary because it matches the
training loss. Save cosine as a prespecified metric sensitivity control, not a
second chance to choose whichever metric produces a preferred result. Lower
Euclidean distance and higher cosine indicate nearer representations.

Would either outcome change the next decision? Yes: useful neighborhoods across
the harder gap/attachment examples would justify investigating bounded semantic
candidate proposals with explicit source witnesses. If the base matches them,
prefer it for that role. If both still mainly follow incidental association or
reporting words, do not feed these neighborhoods into hierarchy construction or
try a score cutoff to fix the ordering. Reassess the representation requirement.
Greeting recovery alone repeats earlier evidence and is insufficient justification.

## Complete-method dependency

A possible construction method would propose shared descriptions from semantic
neighbors, retain their source witnesses, establish which descriptions actually
narrow others, recover note membership, and select useful navigation choices.
This experiment tests only whether the first stage has better evidence than
word co-occurrence. It does not test description generation, equivalence,
parent relations or a complete browser. No GDC09 artifact or TUI will change.

## Execution and preservation

- Run ID: PPR01; separate `base` and `phrase` artifacts. Refuse existing outputs.
- Phrase checkpoint: `whaleloops/phrase-bert`, revision
  `6f68f4dc2d28aadefa038c79023dc7dfd51f6495`.
- Base checkpoint: `sentence-transformers/bert-base-nli-stsb-mean-tokens`, revision
  `c1e99553cc170c78b16717e93e8042552f5bef20`.
- Author training source: `sf-wa-326/phrase-bert-topic-model`, revision
  `fad93c62dfb20b6f567ff8d6c6fb6272d5801323`.
- Public model downloads, about 876 MB of weights total; no paid inference,
  frontier prompts or new generated subjects. CPU only, two threads, batch four,
  one model at a time. No training. Preserve raw vectors and package versions.
- Enforce the checkpoint's 128-token limit without silently truncating inputs.
  Verify mean pooling and the official example before interpreting results.
- Write production-path tests first; verify the expected initial failure. Test
  input fidelity, distance calculation, note-balanced selection and invalid data.
- Save frozen inputs, scores, model hashes, source snapshots and the semantic
  audit. Keep this pre-run plan unchanged; put deviations in the result report.

## Sources

[^1]: Wang, Thompson and Iyyer (2021), [Phrase-BERT: Improved Phrase Embeddings from BERT with an Application to Corpus Exploration](https://aclanthology.org/2021.emnlp-main.846.pdf), sections 3–5 and Tables 1–3. These sections were read; this is not a reproduction of the topic-model case study.
[^2]: [Official checkpoint and executable example](https://huggingface.co/whaleloops/phrase-bert/tree/6f68f4dc2d28aadefa038c79023dc7dfd51f6495), [author training code](https://github.com/sf-wa-326/phrase-bert-topic-model/blob/fad93c62dfb20b6f567ff8d6c6fb6272d5801323/phrase-bert/phrase_bert_finetune.py), and [base checkpoint](https://huggingface.co/sentence-transformers/bert-base-nli-stsb-mean-tokens/tree/c1e99553cc170c78b16717e93e8042552f5bef20).
