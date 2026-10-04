# ASv6.100 generalization validation v1

Status: authorized, preparing; no validation teacher calls yet.

The user accepts the observed returned-relationship error rates for
[ASv6.100](../asv6.100/ASv6.100.md) and authorizes testing its consistency on
fresh, diverse inputs. This does not adopt the prompt into production or establish
that it outperforms ASv6.101. ASv6.101 has only the small
[ASv6.99-controlled comparison](../asv6.99/README.md#completed-comparison), with
promising source formation and unresolved original-post coverage.

## Frozen experiment

Keep ASv6.100 unchanged: source SHA-256
`76aa2c831ab6d65802de4c76a960f8618c7ec7ee4cd62e619621ec8a453b095d`,
template SHA-256
`0e3fdfb713128233ba65070c0092914a38b0059a2eb5e873c0d828add1c5d52f`.
Use [the native specification](../../experiment_specs/asv6.100-generalization-v1.json), the existing subject schema and
subscription `openai-codex/gpt-6.1-sol/medium`, WebSocket, 1,800-second timeout,
no output cap or paid fallback. Three independent trials each contain the same
60 complete inputs: 40 fresh real Nostr posts and 20 authored stress cases.
Eight authored cases are the previously unused P201–P208; twelve are newly
authored H009–H020. Report these source kinds separately.

The real posts come from the saved 51,200-row public Nostr sample at
`target/crec-113-formal-v1/sample/sample.jsonl`. Source SHA-256 is
`8edb8a51246201100e6ba7cf7bf1bbf9cd501881d7c70b8a9cfc7a380d1b168e`.
Select exact original posts across ten broad topics after reviewing their full
text and excluding identified earlier teacher, development, candidate and
inspection inputs. The lexical retrieval pool is not a semantic topic label or
a representative probability sample. Preserve exact source IDs, author/row
provenance, selection policy and exclusions in the ignored source artifacts.

Native preparation reads referenced original JSONL/posts files, selects supplied
IDs, hashes all sources and keeps review criteria out of POST. No corpus copying
or experiment-specific execution driver is needed. Preparation reads the bounded
21.8 MB source once; inherited trials reuse frozen cases. Per-request prompt work
remains one unchanged ASv6.100 prompt plus one complete post. This evaluation does
not add a production grading pass or change corpus-scale inference architecture.

Use ignored artifacts under
`experiments/sp-autonomous-v1/asv6.100-generalization-v1/`, with the existing
`experiments/sp-autonomous-v1` history root. Freeze all three plans with `--repeat`
before inference. Each runner has concurrency one; three independent runners
allow three simultaneous requests. Bound T1/T2/T3 at 67/67/66 new attempts,
respectively: 180 intentional first calls and at most 200 total attempts.
Only existing provider-transient retries qualify, with at most two attempts per
case. No quality retry or prompt editing during the test.

The unchanged shared counter begins at 1,604/2,000. Three complete first-call
trials would reach 1,784; this task's 200-attempt maximum reaches 1,804. Failed
attempts remain charged. Existing subscription use adds no incremental cash;
quota consumption remains unmeasured. Every run uses
`target/sp-autonomous-v1/attempt-budget.json` and preserves native receipts.

## Preregistered review

Before inference, independently review concise required source meanings and
definite semantic refinement pairs for every input. Keep inventories, original
texts and hashes as ignored experimental artifacts. Equivalent faithful wording,
language, numbering and intervening headings are accepted; no exact tree or
optional taxonomy is required. Criteria are agent judgments, not human gold.
The user's Food/nonfood-use calibration applies. Qualified vegetable placement
beneath Mothers or Ten-year-old children is not required. Do not infer a universal
requirement or prohibition from that particular withdrawal.

Report separate denominators:

- Returned relationships: every immediate numbered child-parent edge classified
  correct, clearly incorrect or uncertain; roots are excluded.
- Source coverage: each preregistered required source meaning represented,
  omitted or uncertain. Events do not replace their participant subjects.
- Fixed relationship coverage: each preregistered semantic refinement pair
  satisfied, missing despite both endpoints being represented, blocked by a
  source omission or uncertain. An omitted source is not also charged as an
  absent copy. These bounded targets are not an exhaustive taxonomy.
- Additional copy coverage: evaluate compatible actual returned occurrences
  separately, with an output-dependent denominator. Mere mentioned participants
  do not establish compatibility. Optional absent headings are not errors.
- Unsupported subject assertions: separate source grounding from correctness
  of relationships between returned headings.

Record exact numbered witnesses in native agent reviews. Show pooled and
per-post rates, real/authored and topic breakdowns, and the number of independent
trials demonstrating each input's bounded criteria. Keep ambiguous cases visible.
Sampled fresh inputs and three repeats support a bounded consistency assessment,
not population accuracy, identical-output requirements or causal prompt progress.
No comparison with ASv6.48 or ASv6.101 is authorized by this validation alone.

## Offline verification

The two source-loading CLI tests first failed because the existing posts adapter
required a notes array. They now pass through native prepare/show without model
calls, preserving exact original text, source hashes and row/author evidence and
rejecting unknown selections and duplicate identities across files.
Of 210 workflow/runner/revision/title tests, 209 passed initially; the remaining
test needed `tiktoken` and passed with the cached dependency. Forty prompt
consolidation checks also pass. The prompt bytes remain unchanged.
