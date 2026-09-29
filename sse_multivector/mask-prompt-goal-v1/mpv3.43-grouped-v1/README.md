# MPv3.43-G1

Status: draft; not model-tested, frozen or adopted. Intended experiment model:
Astra low. Inference and runner changes are not part of this draft.

Based on frozen MPv3.43, SHA-256
`75cf99011d0b35e4f62f5157834cc953cfd11bba913b9a4db602e8c151af8c03`.
The new input supplies all subjects for one post as a JSON array of `id` and
`subject` entries in `{SUBJECTS}`. The output retains a separate assessment and
mask for every subject, including empty masks, in a `results` array. Different
subjects may select overlapping text. Existing semantic rules and all example
subjects, explanations and selections are preserved; example envelopes change
to demonstrate the grouped input/output contract.

Created through `experiment.py revise`; the generated revision receipt is an
ignored artifact. Frozen MPv3.43 and its results remain unchanged. This draft
does not establish that grouped generation improves cost or preserves quality.
