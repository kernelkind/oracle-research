# ASv6.100 generalization validation v1

Status: validation running; preregistration frozen at `050267d5` before calls.

The user accepts the observed returned-relationship error rates for
[ASv6.100](../asv6.100/ASv6.100.md) and authorizes testing its consistency on
fresh, diverse inputs. This does not adopt the prompt into production or establish
that it outperforms ASv6.101 generally. The six saved ASv6.101 answers from the
[ASv6.99-controlled comparison](../asv6.99/README.md#completed-comparison)
have now been scored across all 501 returned immediate relationships: 459 correct,
36 incorrect and six uncertain. On the shared N096 input, three ASv6.101 answers
have 246 correct, 22 incorrect and three uncertain relationships out of 271;
three ASv6.100 answers have 257 correct, two incorrect and nine uncertain out of
268. These agent assessments favor ASv6.100's returned-link correctness on this
small shared sample; they do not measure overall missing-relationship rates or
establish a causal prompt effect. The user approves resuming the unchanged
ASv6.100 diverse-input test before further prompt revision.

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
before inference. Initially each runner had concurrency one, allowing three
simultaneous requests. Bound T1/T2/T3 at 67/67/66 new attempts,
respectively: 180 intentional first calls and at most 200 total attempts.
Only existing provider-transient retries qualify, with at most two attempts per
case. No quality retry or prompt editing during the test.

The unchanged shared counter begins at 1,604/2,000. Three complete first-call
trials would reach 1,784; this task's 200-attempt maximum reaches 1,804. Failed
attempts remain charged. Existing subscription use adds no incremental cash;
quota consumption remains unmeasured. Every run uses
`target/sp-autonomous-v1/attempt-budget.json` and preserves native receipts.

The user subsequently requested higher concurrency. The original three
schedulers were interrupted with SIGINT; their executor contexts waited for
active calls to finish and persist receipts before exiting. T1/T2/T3 retain
20/20/21 valid answers, with no failed calls. Native `prepare --from --only
CASE_ID --repeat --concurrency 8` created `T1-concurrency8`, `T2-concurrency8`
and `T3-concurrency8` for only the remaining 40/40/39 untouched cases. The
continuations allow **24 simultaneous model calls**; no completed answer is
rerun and the immutable original plans remain intact. Their new-attempt
allowances are 47/47/45, preserving the original combined 200-attempt maximum
and shared counter. Report each logical trial across its two disjoint native
plans. Prompt bytes, inputs, model settings and frozen rubrics are unchanged.

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

## Preregistration checkpoint

The 40 real inputs retain their original complete texts, with four posts in each
of ten broad topics, 40 authors and an equal short/long split. The source-only
rubrics cover 329 required source meanings and 85 fixed refinement targets per
real-post trial; the 20 authored inputs add 209 meanings and 43 targets. Across
three complete trials the planned denominators are **1,614 source checks and
384 fixed targets**. These are bounded agent judgments, not an exhaustive
inventory or a required tree. Missing-placement rates use only clear targets
with both endpoints represented; source-blocked and uncertain targets remain
separate.

Frozen rubric artifacts under the ignored experiment root:

| Rubric | Source meanings | Fixed targets | SHA-256 |
| --- | ---: | ---: | --- |
| `real-selection/rubric-a.md` | 153 | 49 | `610288bbca1a6db9e36e184a548e6829f444280bb565e5d33ce49f27b2ee8005` |
| `real-selection/rubric-b.md` | 176 | 36 | `f9845a4e5fdb18e38b9671c5800112135db7c189b639533f5f4f272b512a5468` |
| `prospective-audit/rubric.md` | 76 | 14 | `d5f492cb978c2e4a48a0d1b24f6fd8e9dfa58c4b96ae5050c12fe252be95980f` |
| `authored-new/rubric.md` | 133 | 29 | `c72956f484154380f2e1ec46b8360178d85a987396165f64dfdfb3697da918b2` |

Before inference, independent source review corrected missing standalone named
participants, clarified unresolved reference attachment and collapsed an
equal-meaning tennis target that would have required an identical descendant.
No source post, prompt or runner setting changes. All T1/T2/T3 cases remain
unrun at this checkpoint.

### Review calibration during validation

Review retains the frozen item IDs, counts and rubric hashes. An entity heading
that explicitly states the complete action can retain both meanings, as in
"Article written by the author"; an action-only heading does not replace its
participant entity. Clear loss of a required complete meaning counts as source
omission even when a broader partial topic remains.

Some fixed pairs concern scalar properties of one event or a qualified entity
and its description. When one faithful entry explicitly retains both source
facts, the frozen strict-descendant target's applicability is uncertain: the
prompt does not require every possible broader intermediate heading or an
identical descendant. Record these as requirement uncertainty, without removing
targets or counting an optional absent heading as missing placement. This does
not exempt distinct individual/shared action sources or missing descendants at
actual compatible broader occurrences. The resulting rate describes clear
applicable bounded targets, with uncertain and source-blocked shares alongside.
