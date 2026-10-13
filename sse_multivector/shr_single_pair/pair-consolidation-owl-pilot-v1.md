# Pair-consolidation-owl v5: first pilot

The user authorized the proposed twelve-case GPT-6.1 Sol medium pilot and four
conditional follow-up cases only if the initial screen passes. This record
freezes the initial selection and assessment method before inference. It does
not activate the prompt in hierarchy construction or authorize paid fallback.

## Frozen inputs and expectations

The [case source](pair-consolidation-owl-pilot-source-v1.json) contains one exact
prompt-example input, used only to check the output format, and eleven unseen
agent-designed controls. The controls are authored synthetic definitions, not
AS outputs or independently validated human gold. Two reuse exact subjects and
meanings from the existing authored completed-painting control; the other
controls exercise discussed failure mechanisms without claiming historical
input identity. No original posts or model answers are copied into this source.

Expected restrictions are stored in each case's `evidence`, outside `INPUT_JSON`.
The generic adapter renders only `INPUT_JSON`. No unique consolidated title is
predetermined, and no old model label is used as semantic gold.

| Case | Purpose |
|---|---|
| 00 | Prompt example: structure and vocabulary only |
| 01 | Finished painting beneath a finished-work parent |
| 02 | Preserve the distinction between a plan and completed work |
| 03 | `SOME` light emission does not forbid other colours |
| 04 | `ONLY` contents does not require contents to exist |
| 05 | Preserve alternatives and which object a condition qualifies |
| 06 | Preserve an explicitly stated absence under open-world interpretation |
| 07 | Keep rosemary's culinary and cultivated-plant roles distinct |
| 08 | Cover a material and a product through their stated relationships |
| 09 | Equivalent input meanings beneath an equally restrictive parent |
| 10 | Preserve design purpose and the shelf-to-cup-to-coffee relationship |
| 11 | Do not transfer a human-consumer condition to evening meals |

## Execution and assessment

The [native spec](pair-consolidation-owl-v5-pilot-v1.spec.json) selects the exact
approved v5 prompt, the existing generic adapter, `openai-codex`,
`gpt-6.1-sol`, medium reasoning and SSE through the shared stable launcher.
The existing pair adapter requires a natural-language parent, so it is not used
for this different experimental input contract. The shared runner owns request
admission and provider retries. No concurrency override is supplied.

No strict output schema is supplied: class and glossary keys are generated
dynamically. This initial trial tests the prompt's requested JSON structure.
Native generic transport validity is not structural or semantic approval; every
output is independently checked for JSON shape, references, copied definitions
and its meanings. The full saved answer remains authoritative evidence.

Assess five questions separately:

1. Is the output well formed, with complete vocabulary and fixed reused names?
2. Does each formal translation preserve its input's complete conditions?
3. Does the consolidation cover both translated inputs and fit within the
   supplied parent? Do not silently add axioms from plausible class names.
4. Does its natural-language meaning express the same scope as its logic?
5. Is the resulting browsing topic coherent and informative?

Record failures separately from unresolved interpretations. Use concrete
counterexamples where possible. This pilot uses agent review; it does not claim
automated OWL-reasoner verification or turn these expectations into human gold.
Only if this screen passes should the four follow-ups be prepared. A failing
screen ends this authorized trial before prompt editing or more inference.

## Accounting and evidence

The ignored native directory is `target/pair-consolidation-owl-v5-pilot-v1` in
the task worktree. The preparation reports twelve unrun cases and zero exact
baseline matches or reusable answers. No additional baseline calls are planned;
no measured v6 accuracy or cost improvement can be claimed from this pilot.

Subscription requests have no incremental cash charge in this workflow.
Report native fresh attempts, retries, reuses and all observable API-equivalent
token costs separately from subscription billing. No caching warmup is requested
for this initial screen; ordinary server-reported caching, if any, remains in
the native receipts. No paid provider, rental or monetary commitment is added.
