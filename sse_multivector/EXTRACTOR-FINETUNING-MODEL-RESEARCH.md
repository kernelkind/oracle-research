# Pretrained models for subject-and-mask fine-tuning

## Recommendation

**The leading quality-first candidates are Qwen3.8-2.4T-A95B and Nemotron 3 Ultra 550B-A55B. The most relevant encoder–decoder comparison is T5Gemma 9B-9B, about 20.3B total parameters.** Qwen3.8-27B and Gemma 4 31B remain strong dense-model alternatives.

This selection imposes **no parameter-count, GPU-memory, or single-machine ceiling**. Training and deployment requirements are reported separately. A larger model is not excluded because it is expensive, and a smaller model is not preferred merely because it fits a convenient machine.

The recommendation is a prioritized candidate set, not an established accuracy ranking. No matched study located fine-tunes these checkpoints on complete, overlapping subject masks from informal notes. Claiming that one is the most accurate would exceed the evidence.

| Role | Leading candidates | Basis for consideration |
|---|---|---|
| Quality-first general-model comparison | Qwen3.8-2.4T-A95B; Nemotron 3 Ultra 550B-A55B | Broad pretrained capability, instruction-following evidence, and verified fine-tuning implementations |
| Dense general-model comparison | Qwen3.8-27B; Gemma 4 31B | Strong general models with concrete adaptation recipes; not selected under a size ceiling |
| Encoder–decoder comparison | T5Gemma 9B-9B PrefixLM instruction-tuned | Separate input encoder and output decoder; substantial pretrained language knowledge; relevant architecture evidence |
| Specialized-extraction comparison | NuExtract3; GoLLIE-34B | Previous training for extraction or annotation-guideline following; different task assumptions that require scrutiny |

Specifications and training support are documented in the primary releases and implementation guides.[^1][^2][^3][^4][^5][^6][^7][^8] The priority judgments are inferences, not published findings about this extractor.

**If choosing a leading candidate by the completeness of its task-relevant training evidence, Nemotron Ultra is especially compelling. If choosing a frontier-capacity general-model challenger, Qwen3.8-Max deserves direct consideration.** Neither should have to wait for a smaller model to fail merely because of an assumed hardware limit.

## Required transformation

The component would replace the subject-generation and per-subject masking calls:

```text
complete note → complete set of grouped source-text masks → unchanged SSE
```

The model must discover the subjects as well as locate their evidence. A mask may contain several separated fragments, different masks may overlap, and the number of masks varies. The production output does not necessarily need the intermediate English subject descriptions.[^9]

This requires both interpretation and selection. A model can copy text perfectly while missing a subject, choosing the wrong scope, or combining unrelated meanings. Conversely, a reasonable subject interpretation can be paired with an inadequate source mask.

The current teacher versions are ASv6.23 and MPv3.5. The teacher's annotation policy—not factual-proposition segmentation, a standard named-entity inventory, or a new taxonomy—defines the intended supervision.[^10] Valid alternative masks and harmless redundancy should not be rejected merely because they differ from one reference list.

Both decoder-only and encoder–decoder models can be trained on the same complete-note input and grouped-mask output. A short task instruction is optional if the training and deployment formats agree. Some reasoning-model releases natively produce intermediate reasoning; changing that behavior through fine-tuning is a separate assumption, not something guaranteed by exposing only the final answer.

## Evidence relevant to the choice

### Direct source-mask generation

PropSegmEnt is the closest published output-structure match. Its T5-v1.1-large model generates overlapping, potentially discontinuous proposition masks. It trained on 9,913 sentences with 38,206 proposition annotations and achieved 55.50 fuzzy F1, compared with estimated human agreement of 67.07. Its BERT-based mask-head baseline scored 34.17.[^11]

This supports generative source-mask prediction as an architecture. It does not establish that T5 is the best current backbone, or that factual-proposition results transfer to informal subject masks. The imperfect results also show why copying source text is not sufficient evidence of semantic correctness.

### Model size can matter in extraction

GoLLIE fine-tuned Code Llama at 7B, 13B, and 34B to follow extraction annotation guidelines. Average supervised F1 rose from 73.0 to 73.9 to 75.0. Benefits varied by task: the 34B model improved some results substantially, while not improving every dataset. The authors also found larger models generally better at unseen tasks, with some failures still attributable to guideline problems.[^12]

The implication is not “choose 34B.” It is that an arbitrary small-model ceiling can exclude useful capacity. It is equally wrong to assume that increasing size repairs an unclear training target or every extraction error.

### Previous specialization can matter independently of size

NuExtract3 starts from Qwen3.5-4B and adds supervised extraction training followed by reinforcement learning. Its developer reports 65.2 on its structured-document extraction benchmark, versus 50.7 for the underlying Qwen3.5-4B comparator. Training uses annotated real documents and difficult synthetic examples.[^13]

That is evidence for task specialization, not evidence that a 4B model will outperform the large candidates on Nostr. The benchmark involves document-to-JSON extraction, often from images, under a supplied template. Discovering a complete subject set and assembling its masks remains untested.

A supplied schema is not, by itself, disqualifying for a generative model: it could describe a variable-length collection of masks. The important question is whether its learned behavior transfers to open-ended subject discovery, not whether its output is called JSON.

### Architecture evidence does not identify a unique winner

T5Gemma's adaptation study compared encoder–decoder variants with their Gemma 2 foundations. Its PrefixLM-plus-distillation variants generally performed better on generation-oriented evaluations, while UL2 often produced better encoder representations on SuperGLUE.[^14]

Our output is generated masks, not the extractor encoder's embedding vectors. Therefore, selecting UL2 simply because its pretraining involves masked text would be insufficient reasoning. PrefixLM is a serious option for the actual generation task; the exact advantage still needs task-specific measurement.

## Leading general-model candidates

### Nemotron 3 Ultra 550B-A55B

**Starting weights.** NVIDIA reports approximately 20T pretraining tokens covering code, mathematics, science, and general knowledge. Subsequent supervised training explicitly includes instruction following and structured outputs; later reinforcement learning and distillation also cover multiple task domains. The model has 550B total and 55B active parameters, and supports reasoning on or off.[^2]

**Why it fits.** This is a broadly pretrained model with explicit preparation for following output specifications. Those are two relevant ingredients for learning a detailed masking policy. They are not proof of source-mask fidelity, but they are a stronger basis than assuming a model is suitable because its parameter count is convenient.

**Fine-tuning is demonstrated.** NVIDIA's NeMo recipe validates LoRA training on HellaSwag with 16 GB200 GPUs. It reports decreasing training loss through the complete training and checkpointing path.[^3] That establishes implementation feasibility, not mask quality or a minimum hardware requirement.

**Judgment.** A leading candidate for the complete extractor. Its relatively detailed training disclosure and verified adaptation path make it especially attractive for a controlled fine-tuning investigation. They do not establish that it is more accurate than Qwen-Max, Kimi, or DeepSeek.

### Qwen3.8-2.4T-A95B

**Starting weights.** This is the released post-trained, text-only Qwen3.8-Max model: 2.4T total parameters, 95B activated per token. Its release reports IFBench of 82.8. The detailed pretraining corpus mixture is not specified sufficiently in the release used here to characterize it as precisely as Nemotron's.[^1]

That instruction-following result is a relevant general-capability signal, not a predicted extraction score. It must not be compared directly with differently configured IFBench results to manufacture a reliable ordering.

**Fine-tuning is real, not merely implied by downloadable weights.** NeMo documents full-parameter training using expert and pipeline parallelism. A public-checkpoint run completed 100 HellaSwag training steps on 256 GPUs. The documentation explicitly limits the result to validating training mechanics, not convergence.[^4]

**Important behavior.** The released model requires thinking mode. Answer-only mask fine-tuning or a different inference format may be possible, but neither has been demonstrated for this task. Keeping intermediate reasoning is also an option; it was not ruled out by the extractor requirements.[^1]

**Judgment.** A leading quality-first challenger, not a model to dismiss for its size. Its task-fine-tuned advantage over the dense Qwen release is unknown, and must not be inferred from parameter count alone.

### Qwen3.8-27B

This is the relevant current dense Qwen alternative. Its release reports IFBench of 79.5 versus 69.1 for Qwen3.6-27B, supports optional thinking, and retains the Qwen3.5-family hybrid language-model architecture.[^5]

NeMo has full-training and LoRA recipes for the exact checkpoint. Its documented 100-step demonstrations use medical visual question answering and report training loss, with validation disabled for those curve-only runs.[^6] They establish a working adaptation path, not extraction quality.

**Judgment.** It deserves consideration on capability and trainability, independently of any resource constraint. There is no task-based evidence justifying the earlier preference for Qwen3.5-9B over this checkpoint. Equally, there is no evidence that 27B is the right stopping point.

### Gemma 4 31B

Gemma 4's training covers broad web documents, code, and multimodal data, followed by instruction tuning. The dense 31B release reports stronger general benchmark results than its 12B sibling; for example, MMLU Pro is 85.2 versus 77.2, and BigBench Extra Hard is 74.4 versus 53.0.[^7]

These are reasons to consider the larger checkpoint, not forecasts of mask accuracy. NVIDIA also publishes a concrete Gemma 4 31B fine-tuning example for structured receipt extraction.[^8] Receipts provide a relevant structured-output demonstration but very different semantics and source structure.

**Judgment.** A strong independent dense-model candidate. Restricting the previous investigation to Gemma 4 12B was not supported by an explicit size requirement.

## Encoder–decoder candidates

### T5Gemma 9B-9B PrefixLM instruction-tuned

The model adapts Gemma 2 weights into separate encoder and decoder networks. The released model card reports 2T adaptation tokens; the PrefixLM approach combines prefix-continuation learning with knowledge distillation. Public checkpoint metadata counts **20,333,401,088 parameters**, not 9B total.[^14][^15]

This preserves substantial pretrained knowledge while separating full-input encoding from answer generation. It is a more appropriate unconstrained-size comparison than selecting only the smaller T5Gemma 2 release.

**Why PrefixLM first within this family?** Its published generation-oriented results provide a reason to try it, whereas UL2's stronger encoder representations do not directly answer the generated-mask question. This is a starting hypothesis, not a demonstrated superiority on masks. The UL2 checkpoint remains a legitimate comparison.[^14]

### T5Gemma 2 4B-4B

This remains relevant despite being smaller. It adapts Gemma 3 pretrained weights, uses approximately 2T additional training tokens, and has a redesigned architecture and broader multilingual/multimodal preparation. Its text component is approximately 7.1B parameters. Released checkpoints are pretrained rather than instruction-tuned.[^16]

The meaningful comparison is therefore **a larger older-foundation encoder–decoder versus a smaller newer-foundation encoder–decoder**. Neither “newer wins” nor “larger wins” follows automatically. The model should be compared after task fine-tuning, rather than eliminated for poor instruction following before adaptation.

### FLAN-UL2 20B and FLAN-T5-XXL 11B

These remain usable established baselines, not excluded by size. FLAN-UL2 applies instruction tuning to a 20B encoder–decoder with mixed denoising pretraining; its release compares favorably with FLAN-T5-XXL on several general evaluations.[^22] Neither result establishes subject-mask accuracy. I prioritize T5Gemma for investigating a more recent pretrained foundation, while retaining the FLAN models when their mature implementation or a controlled architecture comparison is valuable.

## Additional candidates and limits of the evidence

| Candidate | What makes it plausible | Why it is not established as the winner |
|---|---|---|
| DeepSeek-V4-Pro-0813 | Large text model; the V4 family reports more than 32T diverse pretraining tokens and extensive post-training | Released capability results do not measure our extraction policy; latest-update gains prominently concern agentic tasks |
| Kimi K3 | 2.8T total/104B active; pretraining includes web text, code, mathematics, knowledge, and vision | Native reasoning and agentic capability are not direct source-mask evaluations |
| GLM-5.3 | Large, broadly pretrained foundation with further post-training | Its release attributes improvements to post-training focused on coding and long-horizon tasks; that does not establish an extraction improvement |
| gpt-oss-120b | Fine-tunable open weights, text generation, structured-output capability; 117B total/5.1B active | No matched post-fine-tuning advantage established for subject discovery and masks |
| NuExtract3 | Extraction-specialized Qwen3.5-based generator; learnable variable output structure | Its previous task is document/template extraction, not our complete annotation policy |
| GoLLIE-34B | Explicitly trained to follow extraction guidelines and generalize to new labels | Older Code Llama foundation; entity/relation/event tasks rather than grouped subject masks |

These are credible candidates, not rejected models. The evidence does not justify confidently placing DeepSeek or Kimi below the leading general models on mask quality.[^12][^13][^17][^18][^19][^20]

Other screened families include Mistral Medium, Qwen3.8-Flash-Next, and diffusion language models. None supplied a matched result that resolves the choice. DiffusionGemma, for example, is a fine-tunable experimental alternative for text generation; its speed-oriented generation design is not evidence that it discovers better subject masks.[^21]

The shortlist is deliberately based on distinct, relevant hypotheses. It is not a claim that every unnamed model is worse.

## Compute requirements are tradeoffs, not eligibility rules

The following numbers are **arithmetic estimates for weights alone**, at two bytes per parameter. They exclude activations, gradients, optimizer state, temporary buffers, and inference caches. Decimal GB/TB are used. Quantized checkpoints can require substantially less weight memory.

| Model | Total parameters | Parameters active per token, where applicable | Approximate BF16 weight storage |
|---|---:|---:|---:|
| Qwen3.8-Max | 2.4T | 95B | 4.8 TB |
| Nemotron 3 Ultra | 550B | 55B | 1.1 TB |
| Qwen3.8-27B language model | 27B | — | 54 GB |
| Gemma 4 31B | Approximately 31B | — | 62 GB |
| T5Gemma 9B-9B | 20.33B | — | 40.7 GB |

Parameter counts come from the releases above.[^1][^2][^5][^7][^15] The storage values are calculated, not measured deployments. Mixture-of-experts models use only part of their weights for each token, but the remaining experts must still be stored and made available; active parameter count is not their complete memory footprint.

Full-parameter fine-tuning additionally maintains trainable state for the model. LoRA trains a much smaller set of added parameters but still requires access to the foundation weights, as illustrated by the adaptation implementations above.[^3][^4][^6] Quantization, sequence length, batch size, parallelism, and optimizer choice materially affect the actual requirement. An inference demonstration on one GPU is not a training-resource estimate.

The public implementation evidence is more concrete than guessing one universal GPU count:

| Model | Demonstrated adaptation | Published demonstration hardware | What it establishes |
|---|---|---|---|
| Nemotron Ultra | LoRA on HellaSwag | 16 GB200 GPUs | Working training and checkpointing; not extractor accuracy |
| Qwen3.8-Max | Full-parameter training, 100 HellaSwag steps | 256 GB200 GPUs | Training mechanics, explicitly not convergence |
| Qwen3.8-27B | Full training and LoRA on medical visual questions | 8 H100 80GB GPUs | Working recipes for the exact checkpoint |
| Gemma 4 31B | Full fine-tuning for receipt-to-JSON extraction | 8 A100 80GB or H100 80GB GPUs in the guide | A concrete structured-extraction training path |

These configurations are **neither minimum requirements nor proposed purchases**.[^3][^4][^6][^8] They use different tasks and training methods, so their GPU counts do not form a fair efficiency benchmark. No compute rental, training run, or weight download was performed for this research.

The economic question remains important because the extractor is intended to replace repeated frontier-model calls. A larger fine-tuned model may be worthwhile if it materially reduces errors or if its batched throughput is favorable. A smaller model may deliver equivalent usable masks at lower cost. Neither result follows from model size alone, and this research does not establish a break-even volume.

## What would settle the choice

**The unresolved quantity is useful mask quality after learning our annotation policy.** General instruction-following scores, a decreasing fine-tuning loss, and an extraction benchmark with supplied field names cannot substitute for that measurement.

A meaningful comparison would hold the reviewed training notes and target policy fixed, keep evaluation notes separate, and inspect both subject coverage and whether each mask selects the appropriate source meaning. Exact copying is necessary but insufficient. Alternative faithful boundaries and harmless redundant masks must not be counted as semantic failures solely because they differ from one teacher output.

Compare realistic task-adapted versions, not an instruction-tuned general model against an encoder–decoder that has never been trained to follow the task. Record output tokens, throughput, training cost, and serving requirements alongside quality. The choice should reflect a useful quality–cost tradeoff, not an unrequested hardware ceiling or an unrequested requirement to maximize accuracy at any cost.

**My corrected recommendation is to retain three genuinely different possibilities:** a large general model such as Nemotron Ultra or Qwen3.8-Max; a strong current dense model such as Qwen3.8-27B or Gemma 4 31B; and the larger T5Gemma encoder–decoder. NuExtract3 is a worthwhile extraction-specialized comparison, not an established replacement for discovering subjects.

The earlier small-model-only recommendation was unjustified. The corrected literature review supports this wider candidate set and identifies concrete adaptation paths; it does not establish a task-fine-tuned winner. Choosing which training runs to fund remains a separate decision.

## Sources

[^1]: Qwen, [Qwen3.8-2.4T-A95B model card](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B). Architecture, instruction-following results, reasoning format, and release links. See also its [license](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/blob/main/LICENSE); open weights should not be confused with identical terms across model families.
[^2]: NVIDIA, [Nemotron 3 Ultra 550B-A55B model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16). Pretraining, post-training, architecture, and supported reasoning modes.
[^3]: NVIDIA NeMo, [Nemotron 3 Ultra end-to-end adaptation recipe](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/nemotron-3-ultra). LoRA, HellaSwag, hardware, and validation scope.
[^4]: NVIDIA NeMo, [Qwen3.8-2.4T-A95B training coverage](https://docs.nvidia.com/nemo/automodel/model-coverage/large-language-models/qwen/qwen3-8-2-4t-a95b). Full-parameter training implementation and the limits of its 100-step validation.
[^5]: Qwen, [Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B). Dense-model architecture, optional reasoning, and release benchmark results.
[^6]: NVIDIA NeMo, [Qwen3.8-27B end-to-end adaptation recipes](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/qwen3-8-27b). Full training and LoRA examples; validation conditions.
[^7]: Google, [Gemma 4 31B instruction-tuned model card](https://huggingface.co/google/gemma-4-31B-it) and [Gemma 4 technical report](https://arxiv.org/html/2607.02770v1). Training background, model sizes, and general capability results.
[^8]: NVIDIA NeMo, [Gemma 4 fine-tuning for structured receipt extraction](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/gemma-4). Training task and hardware examples.
[^9]: Repository architecture discussion, [Direct note-to-mask extractor](../docs/recommendation-engine/research/direct-note-to-mask-extractor.md). Architectural target; its older prompt references are not the current frozen teacher versions.
[^10]: Current teacher records: [ASv6.23 freeze](./subject-prompt-goal-v1/asv6.23/frozen.json) and [MPv3.5 freeze](./mask-prompt-goal-v1/frozen.json).
[^11]: Chen et al., [PropSegmEnt: A Large-Scale Corpus for Proposition-Level Segmentation and Entailment Recognition](https://aclanthology.org/2023.findings-acl.565.pdf), Findings of ACL 2023. Segmentation training data, generative architecture, and measured performance.
[^12]: Sainz et al., [GoLLIE: Annotation Guidelines Improve Zero-Shot Information-Extraction](https://arxiv.org/html/2310.03668v5), and [released 34B checkpoint](https://huggingface.co/HiTZ/GoLLIE-34B). Training procedure, model-size comparisons, and generalization limits.
[^13]: NuMind, [NuExtract 3 release and training description](https://about.nuextract.ai/blog/nuextract-3-release) and [released checkpoint](https://huggingface.co/numind/NuExtract3). Developer-reported extraction benchmark and supervised/RL preparation.
[^14]: Zhang et al., [Encoder-Decoder Gemma: Improving the Quality-Efficiency Trade-Off via Adaptation](https://arxiv.org/html/2504.06225). Adaptation, PrefixLM/UL2 comparison, and generation-versus-encoder evaluation.
[^15]: Google, [T5Gemma 9B-9B PrefixLM instruction-tuned checkpoint](https://huggingface.co/google/t5gemma-9b-9b-prefixlm-it) and its [machine-readable parameter metadata](https://huggingface.co/api/models/google/t5gemma-9b-9b-prefixlm-it). The metadata reports 20,333,401,088 parameters. The [UL2 instruction-tuned counterpart](https://huggingface.co/google/t5gemma-9b-9b-ul2-it) is also released.
[^16]: Google, [T5Gemma 2 paper](https://arxiv.org/html/2512.14856v1), [4B-4B checkpoint](https://huggingface.co/google/t5gemma-2-4b-4b), and [release explanation](https://blog.google/innovation-and-ai/technology/developers-tools/t5gemma-2/). Foundation, adaptation data, architecture, and release status.
[^17]: DeepSeek, [V4-Pro-0813 release](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) and [V4 technical report](https://arxiv.org/html/2606.19348). Foundation training and subsequent release emphasis.
[^18]: Moonshot AI, [Kimi K3 release](https://huggingface.co/moonshotai/Kimi-K3) and [technical report](https://arxiv.org/html/2607.24653). Architecture and training background.
[^19]: Z.ai, [GLM-5.3 release](https://huggingface.co/zai-org/GLM-5.3). Relationship to GLM-5.2 and post-training emphasis.
[^20]: OpenAI, [gpt-oss-120b documentation](https://developers.openai.com/api/docs/models/gpt-oss-120b). Parameter counts, supported outputs, license, and fine-tuning availability.
[^21]: Primary releases for additional screened approaches: [Mistral Medium 3.5](https://docs.mistral.ai/models/mistral-medium-3-5-26-04), [Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next), and [DiffusionGemma overview and fine-tuning links](https://ai.google.dev/gemma/docs/diffusiongemma).
[^22]: Google, [FLAN-UL2 model card](https://huggingface.co/google/flan-ul2). Pretraining objective, instruction tuning, model size, and comparison with FLAN-T5-XXL.
