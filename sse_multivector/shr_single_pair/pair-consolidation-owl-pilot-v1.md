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

## Completed results — 2026-10-13

All twelve initial cases completed and passed the targeted agent screen, so the
four authorized follow-ups were run. Two intentionally repeated cases 04 and
08; two reversed only the node order in cases 02 and 11, using the
[reversal source](pair-consolidation-owl-reversal-source-v1.json) and
[native spec](pair-consolidation-owl-v5-reversal-v1.spec.json). Exact repeats were
prepared with native `prepare --from ... --repeat`, bypassing answer reuse.
Their prompt, inputs and settings match the first draw, and their upstream
response identities differ. Each request has one user message and no
`previous_response_id` or earlier model output in its input. Reversals preserve
the original meanings, optional
parent and teacher settings. All sixteen receipts report GPT-6.1 Sol and HTTP
200; native preparation pins medium reasoning.

All sixteen outputs pass the independent JSON layout, expression formatting,
vocabulary-reference and unchanged-definition checks. Every returned name is
resolved by a formal class or English glossary definition, without duplicate
formal/glossary definitions or changed reused names. Native generic `valid`
alone does not establish these results.

| Control | Targeted result under agent review |
|---|---|
| 00: known prompt example | Requested layout and copied vocabulary pass; format evidence only |
| 01: completed work | Both translations and consolidation retain finished painting within the parent |
| 02 + reversed | Finished work remains finished; plans require neither execution nor completion |
| 03: `SOME` | Emission requires the stated colour without forbidding other colours |
| 04 + repeat | `ONLY` restricts contents without requiring any; empty containers remain admitted |
| 05: alternatives | Lamp emission and sign backgrounds remain separate alternatives |
| 06: explicit absence | `NOT` preserves stated never-painted status rather than inferring it from silence |
| 07: rosemary roles | Culinary leaves and cultivated plants retain their different roles |
| 08 + repeat | Material designation and made-from product relationships remain distinct |
| 09: identical meanings | Both inputs and consolidation retain reached-boiling state within the fixed parent |
| 10: coffee equipment | Design purpose and the shelf-to-cup-to-coffee relationship are preserved |
| 11 + reversed | Human consumer/purpose conditions do not transfer to evening meals; representation detail varies |

Manual review found the proposed consolidations cover both returned translations
and fit each supplied parent using their printed definitions. Their English
meanings preserve the proposed formal scope. This is not an automated
entailment, satisfiability or complete translation-fidelity proof. Some headings
remain partly enumerative, such as cups and their storage; the trial measures
neither hierarchy shape nor browsing decisions.

Native attributed reviews contain fifteen agent accepts and one agent
uncertain, with no user judgments assigned. The uncertain review concerns formal
representation sufficiency in reversed case 11, not demonstrated incorrect
containment. Those counts are not an accuracy estimate.

### Formal representation question exposed by the reversal

The forward human-food translation represents the consumer and purpose
separately:

```text
Substance AND (intendedFor SOME (EatingOrDrinking AND (hasConsumer SOME Person) AND (hasPurpose SOME Nourishment)))
```

The reversed translation instead uses:

```text
Substance AND (intendedFor SOME HumanNourishingConsumption)
```

Its English glossary defines `HumanNourishingConsumption` as "Eating or drinking
by people for nourishment." Thus the condition is preserved in English, but an
OWL reasoner treating the name as an atomic class could not inspect its internal
consumer or purpose restrictions. The reversed `Meal` glossary likewise contains
occasion-or-food alternatives, whereas the forward answer chooses food/drink
provision. This is variation in formal detail and lexical interpretation, not
proof that either consolidation violates its returned input expressions. The
prompt does not yet give a precise boundary between basic English-defined terms
and conditions that must be decomposed formally.

Other lexical qualifications remain unresolved: the first bead definition adds
a threading hole while its exact repeat uses an unexpanded bead category; Garden
and the supplied Material definition also need interpretation. They are recorded
as qualifications, not new human gold or automatically counted failures.

The recommended next step is to settle which explicit input conditions must
appear as formal structure, then test a new prompt version on these matched
controls. No prompt revision, further inference or hierarchy activation was
performed as part of this trial. V5 and every original receipt remain unchanged.

### Native accounting and retained evidence

The native `summarize-experiments` report verifies all three completed experiments
and deduplicates their original generation receipts. All usage and catalogue
estimates are present; it reports no accounting warnings.

| Batch | Fresh attempts | Input tokens | Output tokens | API-equivalent cost |
|---|---:|---:|---:|---:|
| Initial screen | 12 | 37,313 | 8,737 | $0.161996 |
| Exact repeats | 2 | 6,246 | 1,373 | $0.026222 |
| Reversed order | 2 | 6,204 | 1,610 | $0.028508 |
| **Total** | **16** | **49,763** | **11,720** | **$0.216726** |

The 4,992 reasoning tokens are already included in output tokens and output
cost. There are zero failed attempts, retries, answer reuses, warmups, cached
input tokens or reported cache-write tokens. API-equivalent cost is a saved
catalogue estimate, not a subscription invoice. No v6 baseline was run, so this
is not an improvement or savings comparison.

The task worktree is retained because validated native plans, source bindings,
receipts and attributed reviews refer to its absolute paths:

```text
/home/dev/src/notedeck_worktrees/algos/oracle-mvp-pair-consolidation-owl-v5-pilot-v1
```

Its ignored evidence comprises:

- `target/pair-consolidation-owl-v5-pilot-v1`
- `target/pair-consolidation-owl-v5-repeat-v1`
- `target/pair-consolidation-owl-v5-reversal-v1`
- `target/pair-consolidation-owl-v5-structural-checks-v1.json`
- `target/pair-consolidation-owl-v5-usage-source-v1.json`
- `target/pair-consolidation-owl-v5-usage-summary-v1.json`

Reusable prompt and case definitions and these maintained findings are tracked;
rendered prompts, model outputs and native reports remain ignored artifacts.
