# SHR student model research

Research dates: October 5–6, 2026. **Recommendations for evaluation, not an
approved model choice or SHR training plan.** The initial literature phase
performed no runs. Subsequent user-authorized capacity checks and provisional
v26/v79 comparisons are recorded in [student preparation](SHR-STUDENT-PREPARATION.md).
Those synthetic optimization checks do not train an SHR student. No paid
resources were used.

## Recommendation

**Keep a larger quality reference in matched SHR training.** Qwen3.8-27B and
Kev-27B are strongest on the current v79 panel; the standard LM is at least
as competitive as the pointer checkpoint. Kev-9B remains a useful compact
comparison alongside its actual Qwen3.5-9B-Base control, and Ettin-1B is the
cheap training arm. Gemma 4 12B-it retains the independent-foundation role:
it handles the clear original cases well but misses inconsistent groups.
Nimble and Decider have no current diagnostic quality advantage. These are
priorities for evaluation, not an approved student or post-finetuning ranking.

SHR should have a separate student decision from SP. It jointly compares two
supplied topics and returns one of five relations; SP generates a variable
subject hierarchy from a whole post. A relation-only SHR student can therefore
use a decision checkpoint or encoder even if it cannot produce SP's output.
Sharing a foundation remains useful only if its quality and whole-process
cost justify doing so.

The completed seven-model NF4 comparison uses the same 70 v26 development inputs,
including 35 exact A/B reversal pairs. The two scored orders change the mapping
between answer codes and relations. Agreement is with saved teacher decisions,
**not semantic gold or held-out accuracy**. Twelve related Culture judgments
are a substantial correlated cluster. Chat models receive a checked
`Answer: (` prefix so that punctuation before an answer code does not distort
the readout. All scored outputs below were valid in one HTTP attempt.

| Published checkpoint, NF4 direct readout | Teacher agreement, two code orders | Reversal consistency, two orders | Decisions unchanged by code rotation | Provisional role |
| --- | --- | --- | --- | --- |
| Kev-9B, native pointer | 61/70; 60/70 | 31/35; 31/35 | 66/70 | Leading compact decision warm start |
| Kev-27B, learned full backbone and native pointer | 51/70; 51/70 | 32/35; 30/35 | 66/70 | Larger decision reference; no demonstrated quality gain |
| Nimble-9B v3-12026, native schema and LM scores | 56/70; 51/70 | 29/35; 24/35 | 61/70 | Standard LM adapter alternative; continued-adapter optimization unmeasured |
| Gemma 4 12B-it, checked chat answer prefix | 49/70; 54/70 | 33/35; 31/35 | 65/70 | Independent foundation; scope and activity/product errors remain |
| Qwen3.8-27B, checked chat answer prefix | 53/70; 52/70 | 28/35; 27/35 | 59/70 | Larger quality reference; no demonstrated advantage over the compact decision warm starts |
| Mapika decider-4b v2.1, native plain layout | 45/70; 42/70 | 28/35; 30/35 | 58/70 | Cheaper compression comparison |
| Qwen3.5-9B instruct, checked chat answer prefix | 35/70; 39/70 | 20/35; 28/35 | 47/70 | Instruct control; no current diagnostic advantage |

These checkpoints have different prior supervision and native input layouts.
Kev-9B's stronger results support trying its decision specialization, but do not
isolate its head architecture or show superiority after matched SHR training.
Kev-27B's additional size does not improve this developmental comparison. BF16
scores 49/70 in both orders, with 32/35 reversal consistency in each and 68/70
decisions unchanged by rotation. Higher precision therefore has not rescued
its quality result. Its native local capacity path also passes. The two Kev
releases differ in foundation and published training history, so they do not
isolate a model-size effect or resolve a post-finetuning capacity plateau.
Nimble currently uses the 12,026-row, 8,192-token release, rather than its
original 2,676-row release. Qwen3.5-9B instruct is also distinct from Kev's
Base foundation; the latter remains the corresponding matched-training control.

Correcting the chat answer position matters. Gemma's initial bare-code
rotation preserved only 38/70 decisions; its checked prefix preserves 65/70.
Its generated v26 answers were all Markdown-fenced and failed strict JSON
validation. Those failures remain preserved, not repaired targets. Qwen-9B's
unmodified greedy-JSON path agreed with 36/70 decisions; correcting its scored
answer position does not close the current gap to Kev. Reasons are diagnostic,
so the student need not reproduce this generation contract.

The separately authorized v79 TRAIN-panel comparison is complete: 840 valid
single-attempt answers on the exact 60 teacher cases, in two option orders.

| Published checkpoint, NF4 | v79 teacher agreement, two orders /60 | Original orientations /40 | A/B reversals /30 |
| --- | --- | --- | --- |
| Qwen3.8-27B | 53; 53 | 37; 38 | 27; 28 |
| Kev-27B | 53; 51 | 37; 36 | 29; 27 |
| Kev-9B | 44; 40 | 27; 26 | 18; 14 |
| Gemma 4 12B-it | 42; 40 | 30; 28 | 25; 27 |
| Nimble-9B | 36; 37 | 25; 25 | 23; 22 |
| Decider-4B | 36; 34 | 24; 23 | 23; 22 |
| Qwen3.5-9B instruct | 33; 39 | 21; 27 | 17; 23 |

Both 27B checkpoints match all 36 non-uncertain answers in each order. Their
remaining disagreements largely concern unresolved meanings and inconsistent
multi-entry groups. The Kev-9B lead on v26 does not transfer, while Gemma has
stronger original-case and reversal behavior than Kev-9B but misses most
constructed conflicts. Nimble/Decider each match 4/24 uncertain answers in the
first order. Qwen-9B is most sensitive to option rotation: only 38/60 decisions
remain unchanged. These error profiles support a larger reference and diverse
supervision rather than a uniform compact-model winner.

This changes both prompt **and** case panel; its provisional TRAIN teachers
and 20 families do not establish an isolated prompt/size effect, held-out
accuracy or a finetuning plateau. The current real-data trainer supports SP/MP
only. Building reusable SHR relation-only training support is therefore a useful
next preparation while the prompt remains unfinished, before matched supervised
fits and separately reviewed evaluation. Final selection remains open. See
[the complete v79 evidence](SHR-STUDENT-PREPARATION.md#provisional-shr-single-v79-published-checkpoint-comparison).

GB10 measurements establish usable local training paths, independently of
semantic quality. They use synthetic token tensors, finite gradients,
checkpoint save and a separate process checking reload logits. They do not
fit any SHR labels or estimate convergence. Sequence lengths, trained weights,
precision and service contention differ; these are capacity observations,
not a controlled architecture speed ranking.

| Verified training path | Seconds/update at 512 tokens | Seconds/update at 2,048 tokens | What was updated |
| --- | ---: | ---: | --- |
| Ettin-1B full, service stopped | 0.628 | 1.055 | All 1.031 billion FP32 parameters; 32 GiB allocator budget |
| Decider-4b NF4, service stopped | 0.613 | 2.241 | 32.46 million FP32 LoRA parameters over the merged decision checkpoint |
| Kev-9B native NF4, service resident | 1.467 | 4.774 | Published LoRA plus pointer head, 45.38 million parameters |
| Kev-27B native NF4, service stopped | 4.134 | 13.750 | Fresh LoRA over the learned full backbone plus pointer head, 119.35 million parameters |
| Gemma 4 12B-it NF4, service stopped | 1.566 | 6.332 | 65.57 million FP32 LoRA parameters |
| Qwen3.8-27B NF4, service stopped | 3.150 | 9.985 | 116.73 million FP32 LoRA parameters |

Ettin's speed makes it worth training once suitable labels exist. It currently
has no meaningful untuned five-relation quality score: a new random SHR head
cannot answer the task. DeBERTa's adversarial-NLI warm start remains secondary
because its 512-position limit constrains complete merged pairs; NLI labels
cannot be mapped directly to SHR. Ettin-400M also has a verified cheap full
training path if compression becomes necessary.

Qwen3.8-27B's completed direct readout gives 53/70 and 52/70 agreement,
with 28/35 and 27/35 reversals. Rotation preserves 59/70 decisions. It fixes
simple directional errors but changes which direction recognizes Culture
containment. Its unmodified greedy-JSON run gave 42 agreements among 69 valid
answers; one of 70 attempts hit the 512-token limit during a repetitive
Nature/Cats explanation. The full scored inputs are 2,638–2,724 tokens and median
reported inference time is 2.980 seconds in each code order. This confirms a
local relation-only path, without a v26 quality advantage over Kev-9B.
Its native LoRA path also passes training, save, fresh-process reload and all
four inference shapes on GB10. It peaks at 20.07 GiB allocated during the
2,048-token updates; batch-eight inference at that length gives 0.388 examples
per second. Load/reload take 412/327 seconds in this stack. These observations
retain it as a local escalation candidate, without a demonstrated v26 reason to
prefer it over the compact decision warm starts; the v79 panel now supports
retaining it as a serious larger quality reference. Bounded internal reasoning
and matched SHR finetuning remain untested.

Kev-27B likewise passes native NF4 LoRA/head training, save, fresh-process
reload and six inference shapes. At 3,072 tokens, above the current complete
v26 inputs, updates take 19.954 seconds and peak at 23.77 GiB allocated;
batch-eight inference gives 0.177 examples/second and peaks at 26.36 GiB.
Load/reload take 332/405 seconds. These measurements use the correct reference
causal convolution and FP32 k-bit preparation with BF16 autocast, rather than
an optimized throughput ceiling. Kev-9B's earlier measurement had the separate
service resident, so the roughly threefold update-time difference is an
observation across those runs. Local hardware can handle the larger pointer
warm start; its extra iteration cost has no demonstrated v26 quality return.

Kev-27B v2 is now a tested larger decision reference. The literature below
retains Gemma 4 31B/26B-A4B and larger sparse foundations as possible escalation
candidates. A 96GB ceiling is not a requirement. Published general benchmarks
alone are insufficient reason to expand the local comparison before matched
SHR training resolves the compact models' scope errors. No final student,
real SHR fit, paid run or
release-plan decision is made here. Exact experiment identities, failures,
case reviews, test results and capacity hashes are in
[student preparation](SHR-STUDENT-PREPARATION.md).

## Project constraints and task meaning

The project needs useful automatically constructed subject hierarchies for
readers. Pair accuracy matters through its effects on combining equivalent
topics and placing broader/narrower hierarchy nodes. SHR training remains
conditional on a useful SHR-built hierarchy; this research does not authorize
training or change the release plan. See
[release decisions](../docs/planning/release-decisions.md) and the
[existing SP pilot](EXTRACTOR-FINETUNING-PILOT-PLAN.md).

The user's correction identified **SHR-single-v26** as the approved reference
for the earlier model investigation. The user subsequently selected
**SHR-single-v79** for the current provisional teacher-labeling pilot; that
choice does not select a release prompt or final training corpus. Later tested
revisions are evaluated from their evidence, not their version numbers.
The prompt is still being developed. The v26
source inspected was `sse_multivector/shr_single_pair/SHR-single-v26.md` in the
SHR worktree at commit `672aff1339f9c213a7ac205af557a552883a56d5`; that branch's
prompt sources are not present in this research worktree's base commit.

SHR's input is two lists of `{subject, context}` entries, each representing
one consistent topic. Its output relation is one of `equivalent`,
`a_parent_of_b`, `b_parent_of_a`, `neither`, or `uncertain`.

| Concrete input or change | Required distinction | Model capability implicated |
| --- | --- | --- |
| `Books` versus `Bookshops` | Books is broader although a shop is not a kind of book. | Knowledge plus the supplied containment rule, beyond ordinary noun hypernymy. |
| `Cutlery` versus `Steel`, with a steel fork in context | Neither contains the other; the example fork must not narrow either subject. | Separate reference resolution from importing context restrictions. |
| `Literature` versus `Artistic creation` | Neither: literature includes works, reading and study as well as creation. | Preserve the whole field rather than select one overlapping activity. |
| `Rhea Stone's gardening advice` versus `Mulching garden beds` | Neither, even with the same advice in both contexts. | Preserve the explicit author/advice restriction and both directions. |
| One side combines `Bread baking` and `Loaves of bread` | Uncertain because the entries establish conflicting topics. | Integrate all entries without converting related meanings into one meaning. |
| Reverse A and B | Reverse the two parent labels; preserve the other labels. | Directional consistency. |

General knowledge is allowed to identify names. Therefore a model trained only
to derive facts from a supplied passage can have an unhelpful prior. Conversely,
a model that freely uses associations can invent containment. Both tendencies
must be measured.

The user only needs the relation at inference; reasons are mostly diagnostic.
The existing v26 prompt still requests `relation` and `reason`: no prompt or
runtime contract was changed here. Also, **`uncertain` has a semantic meaning**
in SHR. Low classifier confidence must not automatically be relabeled as
`uncertain`. An NLI checkpoint is a warm start for a newly trained five-way
decision; its entailment/neutral/contradiction labels cannot be mapped directly
to SHR's relations.

## What the closest studies establish

### Taxonomy and lexical containment

[TaxoLLaMA's extended study](https://www.inf.uni-hamburg.de/en/inst/ab/lt/publications/2026-moskvoretskiietal-swj.pdf)
is unusually relevant: it fine-tunes language models on WordNet noun relations
and evaluates lexical entailment, taxonomy construction and insertion. It
supports learning semantic relations from focused supervision, including
definitions. It does **not** establish the best SHR checkpoint: its relation
is chiefly noun IS-A, whereas SHR includes devoted businesses and activities.
Its taxonomy results also include tuned edge thresholds and graph processing,
so they are not evidence of naturally consistent raw pair decisions.

[TaxoInstruct](https://aclanthology.org/2025.findings-acl.167/)
shows that jointly learning parents and siblings improves Llama-2-based
taxonomy expansion and related tasks. However, generating a parent within an
existing taxonomy differs from judging two independently established topics.
Its tree-oriented construction experiments also leave the project's
multi-parent setting unresolved. These papers favor considering a language
model with relation supervision; they do not justify importing their taxonomy
rules or selecting an old specialized checkpoint over a newer foundation.

### Hard semantic inference versus ordinary classification

[Pushing the boundary on Natural Language Inference](https://arxiv.org/html/2504.18376v1)
trains Qwen2.5 models on hard ANLI cases using reasoning and reinforcement
learning. Its 7B/14B/32B trained models score 61.83/63.58/71.75 on ANLI round 3.
This is evidence that difficult semantic decisions can benefit from capacity
and inference-time reasoning, even when the answer has only three classes.
The comparisons do not control for all pretraining differences, and generated
reasoning is part of the procedure. These scores cannot be assigned to an
SHR label head, or used to declare today's encoders inferior.

[Ettin](https://arxiv.org/html/2507.11412v1)
provides the cleaner architecture comparison: matched encoder/decoder models
from 17M to 1B parameters, with encoders stronger on classification. Its 400M
and 1B encoders obtain 91.3 and 91.8 MNLI accuracy. This supports an encoder
experiment, but it does not compare them with modern 4–31B instruction or
decision models on SHR-like scope rules. The 1B encoder received 667B training
tokens, rather than the 400M model's 2T; size alone does not summarize their
training. [Released checkpoints](https://huggingface.co/jhu-clsp/ettin-encoder-1b)
use the ModernBERT architecture and are practical classifier foundations.

NLI tuning is not uniformly beneficial. The
[ModernCE author's comparison](https://huggingface.co/dleemiller/ModernCE-large-nli)
reports ANLI round 3 accuracy of 49.25% for tasksource ModernBERT-large-nli,
44.08% after ModernCE's further AllNLI tuning, and 64.0% for the named Laurer
DeBERTa checkpoint. Those are developer-reported results, not SHR measurements,
but they are a concrete reason to retain the older adversarial-NLI warm start
and avoid selecting ModernCE merely because its name or ordinary MNLI score
looks stronger. The
[tasksource checkpoint](https://huggingface.co/tasksource/ModernBERT-large-nli/blob/main/config.json)
has a 2,048-position configuration; it should not inherit the base model's
advertised context limit without checking.

## Decision-trained students: promising, with different evidence

| Checkpoint | Training and output | Implication for SHR |
| --- | --- | --- |
| [Kev-9B](https://huggingface.co/jaredpalmer/kev-9b) | Qwen3.5-9B-Base plus LoRA and option-scoring heads; public task labels and generated policy, rule and missing-evidence cases. | Best initial compact decision hypothesis. Supplied option descriptions suit five relations; policy scope is relevant. Continued task training is supported. |
| [Kev-27B v2](https://huggingface.co/jaredpalmer/kev-27b) | Full-weight tuning of Qwen3.8-27B, followed by blending with v1; 145,840 records and a pointer head. | Tested larger warm start; below Kev-9B's v26 teacher agreement at NF4 and BF16. Corpus disclosure is partial; post-SHR-finetuning quality remains unknown. |
| [Bespoke-Nimble-9B](https://huggingface.co/bespokelabs/Bespoke-Nimble-9B) | Current v3-12026: Qwen3.5-9B instruct plus LoRA; 12,026 training rows, including contrastive/long-form decisions and public task data; scores answer-letter logits. | Relevant restrictions without a separate head. Its [pinned training contract](https://huggingface.co/bespokelabs/Bespoke-Nimble-9B/resolve/bd792f44ec8e265be861bfcdf4e05967ffe0e858/schema_config.json) is 8,192 tokens, with reconstructed training inputs up to 6,231. |
| [Mapika decider-4b](https://huggingface.co/Mapika/decider-4b) | Qwen3.5-4B-Base; broad decision training followed by hard-case LoRA; answer-letter scoring. | Plausible cheap student. v2.1 improves some hard families but does not dominate earlier versions on every held-out panel. |
| [AutoTrust JEV-9B](https://huggingface.co/autotrust/JEV-9B) | Qwen3.5-9B instruct, LoRA and a decision head distilled from closed Jev probabilities. | Useful alternative; fidelity to Jev is not evidence of correctness under SHR. It can preserve teacher errors. |
| [GEV-26B-Decide](https://huggingface.co/autotrust/GEV-26B-Decide) | Gemma 4 26B-A4B-it plus a decision adapter/head; previously JEV-Gemma4-26B-A4B, with the same weights. | A relevant Gemma warm start. Its headline 62.48 Decision Index mixes direct decisions and adaptive reasoning; do not treat it as a one-pass score. |

Kev-9B's hard-policy gains coexist with essentially unchanged broad transfer
between its releases. Kev-27B v2 improves its trained skill families markedly,
but its locked out-of-domain comparison with v1 is slightly lower and its
all-14-dataset breadth gain has a confidence interval spanning zero. Relevant
specialization is a reason to test, not an assurance of universal improvement.

The [Qwen3.5-9B-Base release](https://huggingface.co/Qwen/Qwen3.5-9B-Base)
is a pretraining checkpoint, distinct from Qwen3.5-9B instruct. Kev uses the
former; Nimble uses the latter. A matched warm-start comparison must preserve
that difference. An untuned Base model's failure to follow the full prompt
would not establish its quality after supervised SHR training.

Nimble's earlier synthetic holdout scores 90.12% versus its untuned 9B foundation's
66.36%, but spans just six source families. More usefully, its
[separate human-labeled public suite](https://github.com/bespokelabsai/nimble/blob/main/docs/PUBLIC_BENCHMARKS.md)
reports 85.3% on a 299-item MultiNLI subset, 82.8% on PAWS and 76.6% on
VitaminC. Candidate-order sensitivity remains unmeasured there. This is credible
semantic-decision evidence, but not a matched SHR-tuning comparison with Kev
or Qwen.

[AlexWortega/openjev](https://huggingface.co/AlexWortega/openjev)
is another NLI-based Qwen warm start. Its v5 disclosure explicitly includes
both train and test portions of several popular benchmarks. Their reported
scores therefore cannot establish generalization for that checkpoint. Its
generic decision interface also evaluates options separately, which would
repeat input work for SHR's five labels. Neither property prevents future
SHR-specific tuning, but both lower its priority.

## Foundations: quality, knowledge and the cost of reasoning

[Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)
and the larger Gemma 4 models are quality references because SHR combines
language, factual identification and explicit rule application. Qwen's broad
instruction benchmark is encouraging, but much of its release evidence concerns
coding and agents. This is a suitability inference, not direct evidence that it
is the best containment model. The repository already has a fine-tuning path
and SP preparation evidence for the three larger pilot foundations.

The [Gemma 4 study](https://arxiv.org/html/2607.02770v1)
reports MMLU-Pro scores of 77.2/82.6/85.2 for 12B/26B-A4B/31B, and BBEH
53.0/64.8/74.4. These support a capacity prior within the family; reasoning-mode
scores do not predict direct label accuracy. The 26B model retains all experts
in memory despite lower active computation. E4B likewise has more total
parameters than its effective-size name suggests, so it is not a straightforward
4B memory comparison.

[gpt-oss-20b](https://developers.openai.com/api/docs/models/gpt-oss-20b)
has 21B total/3.6B active parameters;
[gpt-oss-120b](https://developers.openai.com/api/docs/models/gpt-oss-120b)
has 117B total/5.1B active. Both are fine-tunable open-weight reasoning models.
They deserve consideration for knowledge and rule-heavy failures. The
[official 20B fine-tuning example](https://developers.openai.com/cookbook/articles/gpt-oss/fine-tune-transfomers)
uses LoRA on an H100 and dequantizes the base. That recipe alone proves neither
120B fit nor fast training on GB10. Their reasoning strengths also must not be
credited to an untested no-reasoning head.

Models screened but given lower initial priority:

| Family | Reason to consider later |
| --- | --- |
| [Ministral 3 14B](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512) | Independent compact foundation with instruction/reasoning variants. Its published comparisons emphasize broad chat, knowledge and reasoning rather than pair containment. Useful if Qwen/Gemma share systematic failures. |
| [Mistral Small 4](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603) | 119B total, 6.5B active; optional reasoning and an Axolotl tuning example. Larger memory and unmeasured GB10 training cost make it an escalation candidate. |
| [GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) | 30B-A3B alternative; no located SHR-like tuned comparison makes it preferable to the initial foundations. |
| [LFM2.5-8B-A1B](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B) | 8.3B total/1.5B active, with LoRA tuning support. Interesting cost alternative, but the publisher identifies knowledge-heavy questions without retrieval as a weakness; SHR sometimes needs that knowledge. |
| [Nemotron 3 Nano 4B](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-BF16) | Reasoning-capable hybrid foundation and NeMo tuning support; NVIDIA Open Model License, distinct from Apache. Exact GB10 kernels and direct-decision quality need verification. |
| [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next) | Larger total capacity with sparse active computation, but additional architecture/offload complexity and no demonstrated SHR advantage. |
| [GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash), [DeepSeek-V4-Flash-0731](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) | Current large sparse foundations, rather than assuming the older Flash releases are their latest models. Their total checkpoint scale adds substantial local/offload or rental cost without direct SHR evidence; lower priority for this MVP. |
| [EuroBERT 2.1B](https://huggingface.co/EuroBERT/EuroBERT-2.1B) | Larger multilingual encoder if the first encoder comparison exposes a capacity or language gap. Its multilingual benchmark strength alone does not establish an English SHR advantage. |
| [T5Gemma 2](https://arxiv.org/html/2512.14856v1), [LLM2Vec](https://arxiv.org/abs/2404.05961) | Alternative encoder representations; additional conversion/training work without direct SHR evidence. Jointly classify the pair rather than substituting cosine similarity for containment. |
| [MiniCheck](https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B), [GLiClass](https://huggingface.co/knowledgator/gliclass-modern-large-v3.0) | Claim support and supplied-label classification provide useful data ideas. Neither task supplies SHR's directional, context-sensitive topic relation directly. |

## Relation-only output does not require a new architecture

The smallest change to a language-model training path is to predict one verified
single-token code and map it to an SHR relation. A language-model forward pass
already produces that token's scores. A five-class head also uses one forward
pass and avoids unnecessary vocabulary output, but introduces a new training,
checkpoint and serving contract. The latter is justified by measured benefit,
not by comparing it against verbose explanation generation.

[SecJev](https://arxiv.org/html/2610.03073v1)
provides a useful controlled check: after domain tuning, its 4B decision model
scores 94.48 macro-F1 versus 94.34 for a matched single-token generative model;
reported latency is 109.1 versus 116.9 ms. Specialization produces much larger
gains than this interface difference. Its security-domain results do not
forecast SHR accuracy or training-data requirements.

A relation-only final answer is also compatible with internal reasoning. Begin
by measuring direct decisions; use bounded reasoning diagnostically on the
same difficult cases if necessary. A systematic improvement would distinguish
missing inference computation from an unsuitable foundation. It would not
automatically authorize an adaptive cascade or justify reasoning on every
production pair. Teacher reasons can remain diagnostic material without being
mandatory student output.

Encoders trained to implement a fixed task can take the pair entries directly,
with the rules learned through SHR-specific supervision. This is a different
input contract from prompting an untuned model with v26 and its examples. The
named [DeBERTa configuration](https://huggingface.co/MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli/blob/main/config.json)
has 512 positions, so it cannot simply receive the full v26 prompt. Nimble's
current v79 schema inputs measure 4,719–4,820 tokens, within its 8,192-token
contract. Future pair selections still need complete-length checks. Preserve every
entry and all subject/context text; reject overlength inputs rather than
truncate them. Record any instruction shortening separately from model changes.
If real merged pairs exceed DeBERTa's budget, prefer the longer-context encoder
rather than introduce a context-selection step solely to fit it.

## GB10 path and whole-process cost

The user's GB10 is the preferred path for anything that trains quickly there;
96GB is not a model requirement. Memory fit and training speed are separate.
Dense parameter count, active expert count and theoretical FLOPS cannot supply
a reliable wall-clock forecast for short pair training.

[Unsloth's actual DGX Spark guide](https://unsloth.ai/docs/blog/fine-tuning-llms-with-nvidia-dgx-spark-and-unsloth)
reports roughly 68GB unified memory for gpt-oss-120b QLoRA, and demonstrates
gpt-oss-20b reinforcement learning locally. Its four-hour, 1,000-step game
example is not a forecast for SHR supervised fine-tuning, but it rules out
discarding 120B merely because of the old GPU limit.

An [independent GB10 decision experiment](https://morethanamachine.com/posts/jev-style-decisions-dgx-spark/)
ran both ModernCE and Qwen3.5-4B. Its encoder's short-request latency was much
lower, but the WANLI evaluation overlaps upstream training source groups and
the paired accuracy interval spans zero. It establishes local runtime
plausibility, not an SHR quality winner or a demonstrated training duration.

For a subsequently authorized pilot, use the local path first for encoders
and compact LoRA students. Verify the exact model, ARM64/Blackwell kernels,
forward/backward, checkpoint reload and intended sequence lengths before
calling training fast. Measure a representative training segment and extrapolate
the actual proposed example count. A larger model that passes the same local
time/fit check should use GB10 too; rental is conditional on measured need and
separate spending approval.

The construction algorithm determines how many pairs SHR sees. No proposed
evaluation or deployment should score every possible pair in the full corpus.
For Q unique comparisons, total model work includes Q times the instructions,
pair entries and any reasoning tokens; merged nodes can enlarge each input.
Report batch throughput and full hierarchy build time as well as isolated
latency. Historical one-entry diagnostics do not establish future merged-input
bounds. Avoid five separately rendered NLI questions when one five-way
comparison can use the same information.

## Why SHR and SP can choose different students

SP ASv6.100 consumes a complete post and generates a variable-length hierarchy
of subjects, contexts and numbering. SHR consumes already supplied topics and
chooses one relation. The existing SP pilot compares Qwen3.8-27B, Gemma 4 31B-it
and Gemma 4 26B-A4B-it; no winner has been selected. Its long generation and
token bounds are not requirements for an SHR student.

SHR can therefore select a classifier or decision-trained foundation that
cannot generate SP's output. Conversely, sharing a foundation can reduce
deployment and fine-tuning complexity if both tasks meet their quality and
whole-process cost requirements. The right sequence is independent task
evaluation followed by a comparison of that benefit with maintaining another
model. Neither sharing one model nor splitting the models is settled here.

## Completed preparation and next useful evidence

The user subsequently authorized evaluation preparation, GB10 capacity checks,
the selected-source data audit and provisional v26 diagnostics. These are
documented in [student preparation](SHR-STUDENT-PREPARATION.md); they supply
useful evidence before the prompt is finished. A complete accepted SHR training
corpus and a final model choice remain unavailable.

The subsequently authorized input-selection phase prepared 640 source-bound
TRAIN nomination families / 1,280 complete A/B orientations, with source notes,
authors, frozen membership, SP provenance and reversal identity preserved.
The five nomination rules provide review candidates, not relation labels.
Twenty input reviews and nineteen diagnostic assessments distinguish v26
regressions from the open Food/crop-attack scope question. Six corrective native
reviews resolve the named-musician interpretation against v26's explicit
named-painter example: Kev-9B preserves containment; Kev-27B rejects it in both
directions. Earlier assessments and all measured scores remain preserved; this
is prompt-grounded agent review, not independent gold. No validation case was
nominated and no model call or fitting was added. See
[the rule review](SHR-STUDENT-PREPARATION.md#rule-review-against-shr-single-v26) and
[TRAIN pair preparation](SHR-STUDENT-PREPARATION.md#train-pair-preparation).

The subsequent offline collection support preserves complete SHR answers,
source identities, prompt versions and review history through the shared
workflow. It does not select accepted targets or fit a model; see
[SHR answer collection](SHR-STUDENT-PREPARATION.md#shr-answer-collection).

The human then approved the 20-family **SHR-single-v26 / GPT-6.1 Sol medium**
teacher pilot: 40 valid new answers, no failures/retries/reuse and 20/20
consistent reversals. All 40 source-bound agent reviews support those answers
under v26; the collected supervision remains provisional rather than human
gold. It contains eight equivalence, eight directed-parent and 24 neither
answers, with no uncertain examples. The original 640-family selection has
620 unlabelled families remaining. See
[the teacher pilot](SHR-STUDENT-PREPARATION.md#provisional-shr-single-v26-teacher-pilot).
The subsequently authorized coverage extension now has 20 source-bound families /
60 unrun cases, with 60 native input reviews. It covers differently worded
pairs, name ambiguity, related-topic contrasts, and proposed consistent or
deliberately conflicting multi-entry groups with reversal/order controls.
The pending input-review verdicts are not semantic `uncertain` targets.
See [coverage input preparation](SHR-STUDENT-PREPARATION.md#coverage-input-preparation).
The user subsequently chose **SHR-single-v79** for that teacher pilot. It
completed 60 valid new answers in 60 attempts, with all 30 A/B reversals and
20 reordered-case checks consistent. The labels are 24 equivalent, 24 uncertain,
eight neither and four directed-parent answers. All 60 current native agent
reviews support the answers under v79, and the final collection preserves their
source/split/prompt/receipt/review bindings. The original v26 preparation and
earlier teacher pilot remain unchanged. See
[the v79 coverage pilot](SHR-STUDENT-PREPARATION.md#provisional-shr-single-v79-coverage-pilot).
This is provisional supervision on TRAIN inputs, not independent human gold,
held-out accuracy or post-finetuning model evidence. A matched local diagnostic
under v79 is the next proposed model check; the earlier v26 ranking cannot
simply be carried forward to the updated prompt.

The next useful quality comparison needs the same accepted training labels
and budget for Kev-9B, its Qwen3.5-9B-Base foundation and Ettin-1B. Gemma-12B
provides the independent foundation; Nimble can replace a custom-head warm
start if keeping the standard LM path matters.
That comparison should use reviewed semantic distinctions and track disputed cases
separately. It is a proposed next phase, not permission to fit partial teacher
outputs or put validation examples into gradients.

The eventual comparison should:

1. Cover all five labels and report each confusion separately. A false parent
   creates a different hierarchy error from missed equivalence or excessive
   `uncertain`; overall agreement hides those differences.
2. Include field/activity/product distinctions, named entities, explicit
   restrictions, context-only restrictions, conflicting merged entries and
   lexical overlap with no containment. Use minimal changes that should flip
   the relation, and context paraphrases that should preserve it.
3. Keep reversed pairs, aliases, repeated questions and source-post variants
   together when splitting. Hold out semantic families and source posts where
   feasible; report overlap of common broad topics rather than pretending
   every repeated heading is removable leakage.
4. Compare warm starts with their actual corresponding original checkpoints
   after the same SHR training. Different foundation sizes, instruct/base
   versions, reasoning budgets and training examples must remain visible.
5. Measure direction reversal, entry-order invariance and conditional
   equivalence/transitivity obligations. Consistency alone cannot prove correct
   meanings. Do not repair graph outputs to conceal model contradictions.
6. Check teacher labels semantically. Existing diagnostic outputs, including
   contradictory relation sequences, are evidence about failures rather than
   ready-made gold labels.

This addresses the main remaining uncertainty: whether the inexpensive
decision/encoder students preserve complete topic scope on unseen meanings.
It also keeps label generation from freezing the unfinished prompt's mistakes
into the distilled model.

## Checkpoint identities inspected

These are Hugging Face repository revisions resolved on October 5, not adopted
production pins. Published results retain their authors' checkpoint versions
and protocols; not every benchmark used the current revision. Shortened
revisions below identify the inspected state; the
full metadata and cached source material are ignored research artifacts under
`target/shr-student-research-v1/sources/`. Model labels describe families, not
exact text-only parameter or training-memory totals.

| Repository | Inspected revision |
| --- | --- |
| `jaredpalmer/kev-9b` | `db029f08b290` |
| `jaredpalmer/kev-27b` | `af0e6d551bdc` |
| `bespokelabs/Bespoke-Nimble-9B` | `bd792f44ec8e` |
| `Qwen/Qwen3.5-9B` | `c20223623576` |
| `Qwen/Qwen3.5-9B-Base` | `68c46c4b3498` |
| `Qwen/Qwen3.8-27B` | `1d4bf0f2ff60` |
| `google/gemma-4-12B-it` | `707f0a3b8a3c` |
| `google/gemma-4-31B-it` | `842da3794eaa` |
| `google/gemma-4-26B-A4B-it` | `4d7ae4984b7d` |
| `jhu-clsp/ettin-encoder-1b` | `befd76be43d0` |
| `jhu-clsp/ettin-encoder-400m` | `7662476d60ab` |
| `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` | `b3546ea6b034` |
| `tasksource/ModernBERT-large-nli` | `ca476cb923a8` |
| `Mapika/decider-4b` | `eb5fbdfc9448` |
| `jaredpalmer/kev-4b` | `6cfce5c2fa4b` |
| `openai/gpt-oss-20b` | `6cee5e81ee83` |
| `openai/gpt-oss-120b` | `b5c939de8f75` |
| `autotrust/GEV-26B-Decide` | `7c89590ead08` |

The leading Qwen/Gemma/decision foundations identify Apache-2.0 licenses;
Ettin and the named DeBERTa identify MIT. In particular, Gemma 4's
[current linked license](https://ai.google.dev/gemma/docs/gemma_4_license)
is Apache-2.0; older Gemma licensing must not be assumed for these checkpoints.
