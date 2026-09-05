# Proposed mask prompt: subject-to-source mapping

Tested with user approval in the [Sol-low development run](../mask-prompt-subject-source-sol-low-v1/README.md). Not frozen, registered, or selected as a default. The prompt itself is unchanged from the reviewed entry-definition fix.

The baseline is `../mask-prompt-probe-v4/mask-prompt.md`, without worked examples. Only its final output requirement changes. All mask-scope instructions and the original `{POST}` and `{SUBJECT}` placeholders are unchanged.

The current output is a list of source fragments. The proposed output is a list of objects pairing an exact excerpt from the fixed subject (`subject_text`) with the source fragments that express it (`source_fragments`). This remains one call for one already-supplied subject. The excerpts do not become new subjects. All returned source fragments form one mask.

The entry rule now specifies each person or thing identified in the subject, each relationship or assertion about them, and each qualification of that meaning. Entries retain enough subject wording to preserve the meaning being matched. This replaces the undefined “each distinct part” wording without requiring a fixed number of entries or splitting the subject word by word. All other prompt text is unchanged from the first draft.

The hypothesis is that making the correspondence explicit will help the model include the source text needed for the whole subject while excluding separate meanings. The 36-call development test produced mixed results and did not reliably solve that problem. The mapping is evidence for inspection, not a self-verification result: both the associations and the resulting mask can still be wrong. No confidence field or automatic approval is added.

Overlapping subject excerpts are allowed so that identifying a referent separately does not prevent also representing its relationship to something else. Source order applies within each `source_fragments` array. The object array is a mapping, not a claim that concatenating its arrays preserves global source order. Repeated source strings remain ambiguous when the post contains several possible occurrences; this proposal does not resolve that existing issue.

This draft adds no examples, runner/parser changes, review-tool changes, model changes, subject regeneration, or SSE work. The approved test used the existing raw prompt interface and saved the object-shaped outputs, their combined masks, and assistant assessments in its own result directory. No user review decisions were changed.

Static checks confirm that replacing the new output block with the original sentence reconstructs the baseline byte-for-byte; both input placeholders occur exactly once. These checks establish the draft's construction, not its effectiveness.

The [official GPT-5.6 guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6) informed the limited change: retain the existing goal and constraints, make the required output explicit, and avoid adding a prescribed internal reasoning process. The specific subject-to-source mapping is our experimental hypothesis, not a method established by that guidance.
