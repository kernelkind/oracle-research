# Mask recognition test — approved proposal

The user approved this prompt and test. All 18 planned calls have now run; see the [results](../mask-prompt-recognition-sol-low-v1/README.md) and [full-context judgments](../mask-prompt-recognition-sol-low-v1/judgments.md). The prompt, cases, expected judgments, and original plan in this proposal remain unchanged.

The proposed test uses **six existing masks**, for **three fixed subjects across two original notes**: understanding life, cryptocurrency insurance, and Bitcoin's value under restrictions. Each subject has an acceptable mask and an incorrect mask. Five selections have direct user review decisions; the clean insurance mask is an existing generated selection checked by the assistant, not a fabricated user approval.

Each call receives **one mask**, highlighted inside the complete note, and the fixed subject. It reports missing meaning and additional meaning separately. It does not generate a replacement or choose from alternatives. The expected judgments and their provenance are kept in a separate file and never sent to the model.

The plan was three fresh Sol-low calls per mask: 18 calls total, sequential and isolated. Call order changes between trials. Because every call has a clean context and sees only one mask, this is not a multiple-choice or candidate-position test.

The prompt uses the scope and completeness requirements from the original fragment-only mask prompt. Changes adapt generation instructions into assessment criteria, explain the inline input, and request issue descriptions instead of fragments. No examples, case-specific hints, new scope policy, internal reasoning procedure, or confidence score are added.

The [GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6) informed that limited change: preserve the evidence and success criteria while stating the new task and required output directly. It does not establish that recognition will work.

Files:

- [Recognition prompt](./recognition-prompt.md).
- [Complete posts and fixed masks](./cases.json).
- [Expected judgments and review provenance](./expected-judgments.json), excluded from model inputs.
- [Test plan](./plan.json).

The meditation selection uses the exact highlighted ranges the user approved, not the earlier generator's out-of-order fragment array. The Bitcoin masks retain occurrence 1 from the existing review display. These are fixed recognition inputs; no old generated response or ambiguity record is rewritten.

Even correct judgments on all six masks would establish only a small development result, not a reliable general-purpose reviewer. False alarms on the acceptable masks matter as much as detecting the known errors. ASv6.8, SSE, segmentation, generated data, user decisions, and prompt defaults stay unchanged.
