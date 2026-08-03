# Direct Note-to-Mask Extractor

## Status

This note records research into replacing corpus-wide frontier-model takeaway
and mask calls with one trained local extractor. It is a plausible scaling
path, not an approved implementation or a measured Nostr result.

## Required Transformation

The production component would perform:

```text
canonical note
  -> set of grouped source-token masks
  -> Sub-Sentence Encoder vectors
```

One mask represents one meaning. A mask may contain separated source
fragments, and masks from the same note may overlap. The extractor must also
decide how many masks the note needs.

SSE does not consume a natural-language takeaway. Takeaways are currently an
intermediate aid for generating and auditing masks with general-purpose
models. A specialist extractor does not need to generate them at inference.

## Direct Precedent

PropSegmEnt defines almost exactly this task as extractive proposition
segmentation. Given one sentence, a model predicts an unordered set of
propositions. Each proposition is represented as a possibly discontinuous
subset of source tokens. Different propositions may share tokens.

Its strongest direct baseline fine-tuned T5 to emit one marked copy of the
source per proposition:

- `[M]...[/M]` encloses selected source fragments;
- `[TARGET]` separates proposition masks;
- the marked copies are converted directly into binary masks.

The T5-large baseline reached 55.50 fuzzy set F1. Estimated human performance
was 67.07. A simpler BERT encoder with 20 independent mask heads reached 34.17
F1 and emitted redundant propositions for more than 20% of sentences. The
T5 formulation is therefore the strongest demonstrated starting point, while
also showing that the task is not solved.

Cross-domain T5-large performance fell to approximately 44--50 F1. The
published data consists of factual Wikipedia and news sentences. It does not
establish quality on informal Nostr notes containing opinions, questions,
requests, humor, or multiple sentences.

Source: [PropSegmEnt](https://aclanthology.org/2023.findings-acl.565.pdf).

## Relationship to the SSE Paper

SSE only embeds masks supplied by another process. It encodes the complete
text once, pools the contextual token embeddings selected by each mask, and
projects each pooled result into one vector.

The SSE paper did not train SSE to discover masks. Its corpus pipeline instead:

1. used GPT-3.5 to generate natural-language propositions for about 45,000
   sentences;
2. fine-tuned T5-large to generate propositions for the remaining corpus;
3. heuristically aligned words from each generated proposition back to source
   tokens using lexical matching and Hungarian assignment.

The released `SegmenT5-large` therefore generates rewritten propositions, not
direct source masks. It is not itself the desired replacement.

Sources: [Sub-Sentence Encoder paper](https://aclanthology.org/2024.naacl-long.89.pdf)
and [released SegmenT5-large model](https://huggingface.co/sihaochen/SegmenT5-large).

## Proposed Training Role

The existing two-stage process can create supervision without becoming part of
production:

```text
training-data creation
  note -> TPv3.81 takeaway -> MPv3.3 mask -> reviewed training record

production inference
  note -> trained mask extractor -> SSE vectors
```

The extractor's training target is only the final grouped mask set. Takeaways
may remain in the preserved training artifacts for diagnosis, but are not an
inference output.

The frozen teacher prompts are preserved in:

- `sse_multivector/takeaway-prompt-versions.json`;
- `sse_multivector/mask-prompt-versions.json`.

Teacher-to-student proposition segmentation has also been demonstrated at
larger scale. One study used 226,000 teacher-generated text/proposition pairs
to train 2B and 7B students with results comparable to their teachers. That
study generated rewritten propositions rather than masks, so it supports the
distillation strategy but not direct mask quality.

Source: [Scalable and Domain-General Abstractive Proposition Segmentation](https://aclanthology.org/2024.findings-emnlp.517.pdf).

## Training-Data Estimate

The current center estimate is **10,000 diverse English Nostr notes**, with a
plausible range of **5,000--25,000**.

The estimate is based on supervision density rather than note count alone:

- TEv4.1 produced 194 masks from 50 notes, or about 3.9 masks per note;
- 10,000 similar notes would therefore yield about 39,000 mask examples;
- PropSegmEnt trained on 9,913 sentences containing 38,206 propositions.

Pretraining on the public PropSegmEnt masks and then adapting to Nostr could
put the Nostr-specific requirement nearer 5,000--10,000 notes. Starting only
from generic T5 weights would likely require more. Neither estimate has yet
been measured on Nostr.

Do not purchase all labels up front. Measure a learning curve:

1. 1,000 notes: verify that the model learns the output structure and measure
   annotation and training cost;
2. 3,000 notes: measure whether held-out quality is still improving;
3. 10,000 notes: first credible domain model;
4. expand toward 25,000 only if additional data still produces material gains.

All label generation and training must remain inside the Oracle MVP's lifetime
paid-compute ceiling. The complete cost of TPv3.81 plus one MPv3.3 call per
takeaway must be calibrated before approving even the first stage.

## Evaluation Requirements

Exact token agreement is insufficient because several source-token selections
can preserve the same meaning. PropSegmEnt itself measured only moderate human
agreement on complete proposition sets.

A credible test must separately measure:

1. mask-set coverage, duplication, and unsupported selections on a held-out
   Nostr set;
2. fuzzy token overlap after matching predicted and reference masks as
   unordered sets;
3. whether predicted masks produce the same useful SSE neighborhood behavior
   as the reviewed teacher masks.

The third measurement is decisive for this architecture: mask wording matters
only insofar as it preserves the semantic vectors needed downstream.

## Current Conclusion

Direct `note -> grouped masks` extraction is feasible and has strong published
precedent. The simplest evidence-backed first implementation is the T5
marked-copy formulation, adapted with Nostr-specific supervision. A new custom
parallel mask architecture is not necessary for the first experiment.

The unresolved question is data efficiency: how many Nostr-specific examples
are required before direct masks preserve the downstream SSE geometry well
enough. The staged learning curve above is how that should be measured.
