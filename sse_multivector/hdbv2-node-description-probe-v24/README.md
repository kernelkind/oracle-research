# Category-title prompt v24

Status: proposed draft, not approved or inference-tested. Base: v21, the prompt
used by HRv1. This draft does not activate a new prompt, change saved titles,
consolidate groups, or resume TRUE. v22 and v23 are not its baseline.

The sole change replaces v21's instruction to clarify term meanings from the
title alone with subject identification without definitions and an explicit
requirement that every instance express any aspect named in the title.
The hypothesis is that definition-style elaboration can imply unsupported
category scope. This is not an instruction to omit supported specificity.

The unchanged input and output contracts allow comparison against saved v21
results. Model evaluation remains pending user approval; no improvement is
claimed from reviewing the wording alone.

Official OpenAI prompting guidance informed the explicit wording and scoped
change; it does not validate this task-specific hypothesis:

- https://developers.openai.com/api/docs/guides/prompt-engineering
- https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md#prompting-best-practices
