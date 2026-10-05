# SHR student preparation while the prompt is unfinished

The user authorized three preparation tasks: GB10 feasibility checks, evaluation
design, and an audit of the existing 1,300-note corpus. Work lives on
`research/shr-student-prep-v1`, in `oracle-mvp-shr-student-prep-v1`.
SHR-single-v26 remains the user-approved prompt reference. No final student,
new prompt, SHR teacher labels, paid run, or release-plan decision is approved
by these preparation results. See [model research](SHR-FINETUNING-MODEL-RESEARCH.md).

## Dataset audit

The documented bundle is at
`oracle-mvp/target/distillation-pilot-v1/pilot-data-asv6.100-20261004/`.
The requested source-review handoff
has been queued; confirmation of provenance and reuse constraints is pending.
The following findings independently use the documented files read-only.

```bash
python3 -m sse_multivector.distillation_audit \
  --source ../oracle-mvp/target/distillation-pilot-v1/pilot-data-asv6.100-20261004/sample-final/notes.json \
  --prepared ../oracle-mvp/target/distillation-pilot-v1/pilot-data-asv6.100-20261004/prepared \
  --output target/shr-student-prep-v1/data-audit.json
```

The audit validates posts through the shared input adapter and training answers
through the production subject parser. It checks source/output hashes, frozen
membership and order, complete instruction/post preservation, author separation
and duplicate content. It opens only source notes, the prepared manifest,
training answers, and input-only validation/test files. It does not open
`references.jsonl`, the combined teacher-label file, or any student outputs.

| Split | Notes | Authors | Median post characters | Maximum post characters |
| --- | ---: | ---: | ---: | ---: |
| Training | 1,000 | 458 | 261 | 1,707 |
| Validation | 100 | 78 | 191 | 1,605 |
| Reserved test | 200 | 150 | 265 | 1,107 |

There is no author overlap or exact whitespace-normalized content duplication.
A bounded inverted-index search examined 3,934 nominated pairs and found no
word-5-shingle Jaccard similarity of at least 0.8. Five overly common shingles
were skipped; this heuristic is not an exhaustive near-duplicate or pretraining
contamination check.

The **training** partition supplies 33,234 SP subject/context entries:

| Inventory | Result | What it can establish |
| --- | ---: | --- |
| Entries per note | median 28; p95 76; maximum 145 | Several scope levels are available within many posts. |
| Parent/child candidates from SP numbering | 26,465 | Places to seek SHR comparisons; SP numbering is not an SHR answer. |
| Casefolded subject strings recurring across notes | 991 groups | Cross-post equivalence/polysemy candidates, requiring semantic review. |
| Exactly repeated subject/context across notes | 42 groups | Candidate duplication; text identity alone does not establish node membership. |
| Entry JSON characters, subject and context only | median 175; p95 320; maximum 559 | Capacity can be tested with complete entries; these are not model token counts. |
| SHR relation labels | 0 | This corpus cannot currently measure five-way SHR accuracy. |

The five relation frequencies, multi-entry group lengths, aliases, conflicting
meanings and false-parent difficulty are **unknown**. They cannot be inferred
from SP answer counts. English, short, natural notes limit language/length
coverage; this corpus does not establish multilingual or long-input quality.
The final SP test partition must stay reserved. Dataset-derived development
pairs can initially use only training notes. Validation-derived SHR pairs need
an explicit selection protocol that preserves the existing SP holdout.

Artifact identity:

- Source SHA-256: `0ed88bec41a69b367be8e7eed65d94047b30291558825ff5799bc5742d53df38`.
- Prepared manifest SHA-256 and each opened file hash are recorded in the audit
  artifact, along with the exact source paths.
- Training SHA-256: `f166371c5051b2ea95eb9591510544ade59ef8b1ef3b94826ed4baab92d1e681`.

## Evaluation design

This is a proposed protocol, not a frozen test set or accepted numerical gate.
The purpose is to test whether relation-only inference builds useful hierarchy
nodes, and whether a cheaper student can replace a larger one without damaging
that behavior. SP's full-hierarchy JSON generation is a different output task;
its student winner need not win these comparisons.

Keep two collections distinct. Prompt-development examples, including the v26
examples and any cases already used to revise prompts, are regression cases.
They are useful for diagnosing errors but cannot provide a clean final accuracy
claim. An independent corpus-derived collection measures generalization after
the prompt's rules stabilize. Preserve source-note IDs, author IDs, complete
subject/context entries, nomination method, and prompt/label revision for every
case using `experiment.py prepare` and its shared adapters. Add missing reusable
preparation support there; do not hand-build rendered experiment batches.

Split source families before generating comparisons. Every original comparison,
its A/B reversal, context controls, paraphrases, duplicated entries and all
multi-entry variants belong to one partition. Keep connected source notes and
authors together. Record repeated subject strings across partitions rather than
declaring all shared words leakage: common topics need to generalize. Also keep
an unseen-topic-family slice to test reliance on memorized entities. Never move
cases between partitions because a student gets them wrong.

| Case family | Concrete change to test | What to report |
| --- | --- | --- |
| Both parent directions | Books/Bookshops; reverse A and B | Directional confusion and reversal agreement. |
| Equivalent wording | Different names for the same meaning, versus the same name for different meanings | Equivalence precision and recall. |
| Context-only restriction | Steel context mentions a fork; subject still names Steel | False parent/equivalence decisions after context changes. |
| Explicit subject limits | Add/remove an author, purpose, exclusion or relationship in the subject | Accuracy on the contrast and its unchanged companion. |
| Whole-field scope | Literature versus Artistic creation | False containment caused by comparing only the shared activity. |
| Activities and products | Making sound effects versus Sound effects | Preserve the named activity/product distinction. |
| Multiple entries | Consistent synonyms versus Bread baking combined with Loaves of bread | `uncertain` recall for actual conflicts; entry-order agreement. |
| Missing meaning | An unresolved hashtag versus an identified name | Semantic `uncertain` accuracy, separately from low confidence. |
| Related neighbours | Shared materials, places or purposes without containment | False positive rates for equivalence and each parent direction. |
| Input robustness | Duplicate/reorder entries; quoted instructions in context; complete long groups | Agreement, invalid outputs and rejected/overlength inputs. |

Nominate pairs from SP edges, recurring subjects, shared siblings, local
hierarchy mistakes and unrelated controls. Report accuracy separately by
nomination source. A balanced diagnostic panel reveals rare-label errors;
a held-out sample from the actual nomination distribution estimates deployment
behavior. Do not confuse either with all possible pairs. No corpus-wide
quadratic pair enumeration is needed.

After rules stabilize, teachers may supply relation labels and diagnostic
reasons. Independently review a stratified sample and disagreements to detect
teacher mistakes. Store provisional/accepted/disputed status separately from
the relation. A disputed example is not automatically an `uncertain` example.
Preserve teacher probabilities only when the provider actually supplies them;
do not invent soft targets from reasons or disagreement counts.

Compare students on the same accepted cases and training budget. Start with
relation-only targets. Add diagnostic-reason supervision as an ablation only
if it improves held-out relations enough to justify the extra training or
inference cost. Encoder NLI labels and confidence cannot be mapped directly to
SHR's five relations. A fixed-task encoder may take complete A/B entries alone;
an LM may use the instruction prompt and direct label scoring. Report these
input contracts explicitly, plus full-token coverage and overlength exclusions.

Measure per-label precision/recall, macro-F1, deployment-weighted accuracy,
parent-direction confusion, reversal/order agreement, and calibration of
confidence separately from semantic `uncertain`. Use paired resampling over
source families for model differences, not independent resampling of variants.
Record inference batch size, complete input-token distribution, examples/sec,
latency and peak memory. An inference implementation that scores one token is
already one forward pass; adding a classifier head alone does not prove a
large speed advantage.

Finally, replay the same bounded hierarchy construction with each candidate's
relations: inspect incorrect merges, incorrect parent placements, incompatible
ancestry and reader-visible topic scope. Good pair scores alone do not accept
a student. Numerical tolerances and final model choice remain user decisions.

## GB10 feasibility checks

The GB10 test system runs Ubuntu 24.04.4,
ARM64, Python 3.12.3 and NVIDIA driver 580.173.02. On initial inspection its
Qwen3.8 Flash Next serving process occupied 95,896 MiB, while system available
memory was about 22 GiB. NVIDIA's unified-memory GPU reports total/used GPU
memory as unavailable; record system availability as well as PyTorch peaks.

Preparation
and appropriately bounded small-model checks can proceed without a pause.

Use an isolated environment and ignored artifacts within the owned checkout;
do not change the serving container, global Python or authentication. First
verify CUDA matmul/backward on the actual ARM64 wheel. Then measure model load,
a short optimization, checkpoint save/reload agreement and batched inference.
Synthetic token workloads can measure capacity before labels are ready; they
must be labelled as hardware checks, with no SHR quality or convergence claim.
Installation/download/first-kernel times and steady optimization times are
separate measurements. Co-resident serving means throughput is not an idle
machine estimate. No projected full-training time should be reported without
stating its dataset size, input lengths, batch and measured step count.

The compact feasibility order is Ettin-400M for the environment smoke check,
Ettin-1B and the DeBERTa NLI warm start for encoder comparisons, then a 9B
language-model path when memory permits. The 400M check does not replace the
1B quality candidate. Kev's custom head needs its own validated training path;
a Qwen backbone timing cannot be reported as a tested Kev implementation.
Larger quality controls remain candidates regardless of a 96 GB threshold.

The reusable capacity command is:

```bash
python3 -m sse_multivector.distillation_benchmark \
  --config sse_multivector/distillation/benchmark-ettin400m.json \
  --output target/shr-student-prep-v1/ettin400m
```

Pinned configurations also cover Ettin-1B full/LoRA, the DeBERTa warm start,
and Qwen3.5-9B-Base LoRA. The benchmark admits runs only when available system
memory exceeds its declared budget plus reserve, caps this process's CUDA
allocator, and checks the reserve between workloads. Encoder full training uses
FP32 parameters/AdamW states with BF16 autocast; these numbers must not be
described as a BF16-parameter or quantized training run. LoRA uses rank 16.
The five-column DeBERTa output replaces its original NLI head, as SHR requires
five relations. Causal-LM loading and LoRA reuse `distillation_run`; it needs
the existing FLA CUDA dependency before a Qwen training check can run.

Every accepted run requires finite nonzero gradients, checkpoint hash recording,
reload-logit agreement and finite five-column batched outputs. Failed admission
does not download or load model weights. Benchmark output includes cold-load,
warmup/steady optimization, save/reload and inference timings separately.
Initial GPU validation remains in progress; source/config availability does
not establish that a model has passed these checks.
