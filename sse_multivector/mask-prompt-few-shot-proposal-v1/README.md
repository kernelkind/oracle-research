# Proposed mask prompt with worked examples

Tested on Sol low in [the worked-example comparison](../mask-prompt-few-shot-sol-low-v1/README.md). The examples did not produce a reliable improvement on the four development notes. Not frozen, registered, or selected as a default.

`mask-prompt.md` preserves the instructions and input placeholders from `../mask-prompt-probe-v4/mask-prompt.md` exactly. The only addition is six worked examples, arranged as three pairs using the same post with different fixed subjects.

The posts and masks are synthetic teaching examples written for this proposal, not generated model outputs or real Nostr notes:

- Rescue boat: select an identifying noun without its surrounding claim; retain that claim when it is the supplied subject.
- Ceramics studio: omit or include a modifier according to the supplied subject, including a longer mask when needed.
- Theater: distinguish the event and its consequence from the author's sarcastic praise of the same performers. Both masks omit the announcement setup; the rhetoric mask also omits the separate rehearsal-delay claim.

The hypothesis is that examples make the existing scope requirement easier to apply consistently. These examples use different content from the four notes in the saved Sol-medium/Astra-low comparison. They are not evidence that the prompt works, and must not be counted as independent test notes.

Drafting the examples involved no inference calls. The subsequent user-approved test made 36 Sol-low calls, recorded separately in the linked result. No subject changes, production changes, registry changes, or new user review decisions were made.

Static checks: all six responses are JSON arrays of exact source fragments in source order; removing the examples block reproduces the baseline prompt exactly; each input placeholder still occurs once. The existing Git-to-delta review command rendered the addition successfully. These checks validate the draft's construction, not model behavior.

The proposal follows the [official guidance on diverse input/output examples](https://developers.openai.com/api/docs/guides/prompt-engineering#few-shot-learning). Keeping the existing instructions unchanged isolates the proposed addition, consistent with [GPT-5.6 guidance on controlled prompt changes](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6#prompt-migration-workflow).
