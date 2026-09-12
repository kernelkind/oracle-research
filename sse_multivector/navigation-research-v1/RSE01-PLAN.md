# RSE01 — General-category transfer using released RSE

Authorized September 12, 2026. This plan is recorded before model scoring.

Question: does the released RSE entailment score distinguish plausible broader categories from the fixed alternatives more reliably than HierarCaps did on HRC03?

Use the exact frozen HRC03 fixture: 30 cases, two wordings each, five domains, 180 description occurrences. Preserve its original judgments and later qualifications. Fixture SHA256: `d3efece72ebf6f03e4c0b5fe9b1c588fbece361b00599b34389c242a699c2c35`. No new generated text, masks, notes, labels, or hierarchy changes.

Model: `binwang/RSE-RoBERTa-large-10-relations`, revision `b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5`. Weights SHA256: `76ae8a51d65f60b70b526954ad047bc72398d80681ba5b80a8c8dcfa39b87e39`. Author code revision: `2fc202227bf95bd12ce3b41acbbfefb1a45c983f`.

Encode plain descriptions independently. Use the final first-token representation, trained linear layer and tanh. Score `cosine(z(child) + relation[0], z(parent))`; add before normalization. Relation 0 is entailment. Keep plain same-model cosine as a baseline. Do not use the SentEval helper that maximizes the two directions. No training, relation selection, fitted cutoff, or prompt changes.

Check token counts before inference. Use the author's 32-token limit with truncation forbidden; if an input exceeds it, stop and record the issue rather than silently shorten it.

Compare all 60 matched parent choices and the 30 families' stability across all eight combinations of wording. Report direction separately; preferring forward over reverse does not itself establish parent membership. Compare RSE's native score against its own cosine and saved HRC03 results; record both improvements and regressions. No absolute acceptance threshold or universal accuracy claim follows from this constructed fixture.

Verify scoring and projection with test-first checks. Save complete inputs, raw vectors, the learned relation, all ordered pair scores, derived comparisons, model/input/source hashes, runtime and memory. Independently check the implementation against author code and reproduce saved calculations. Present concrete text and both scores for questionable placements; preserve ambiguous cases without silently changing their expected labels.

Resource scope: local CPU only, batch 4, two CPU threads, 6 GiB process/cgroup memory bound, no swap, one model process at a time. One public 1.42 GB weight download; no paid resources. Prior runs remain unchanged. This is a model-transfer diagnostic, not model adoption or construction of a hierarchy.
