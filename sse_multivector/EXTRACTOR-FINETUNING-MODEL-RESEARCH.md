# Pretrained models for subject-and-mask fine-tuning

## Scope

This is a literature review of released models, their training data, published extraction results, and demonstrated fine-tuning requirements. Experimental decisions, baselines, annotation policies, budgets, and run proposals are maintained separately in the [Pilot plan](EXTRACTOR-FINETUNING-PILOT-PLAN.md).

The task used to judge relevance is open-ended subject discovery with grouped source-text masks, including overlapping and discontinuous masks. A benchmark that supplies the subject or a fixed list of fields tests a narrower task. No matched study located fine-tunes the reviewed checkpoints on complete subject-mask sets from informal notes; the evidence does not establish an accuracy ranking for that task.

## Evidence relevant to the choice

### Direct source-mask generation

PropSegmEnt is the closest published output-structure match. Its T5-v1.1-large model generates overlapping, potentially discontinuous proposition masks. It trained on 9,913 sentences with 38,206 proposition annotations and achieved 55.50 fuzzy F1, compared with estimated human agreement of 67.07. Its BERT-based mask-head baseline scored 34.17.[^11]

This supports generative source-mask prediction as an architecture. It does not establish that T5 is the best current backbone, or that factual-proposition results transfer to informal subject masks. The imperfect results also show why copying source text is not sufficient evidence of semantic correctness.

### Model size can matter in extraction

GoLLIE fine-tuned Code Llama at 7B, 13B, and 34B to follow extraction annotation guidelines. Average supervised F1 rose from 73.0 to 73.9 to 75.0. Benefits varied by task: the 34B model improved some results substantially, while not improving every dataset. The authors also found larger models generally better at unseen tasks, with some failures still attributable to guideline problems.[^12]

The results support a benefit from additional capacity on some extraction tasks, not a uniform benefit across datasets or a guarantee that larger models resolve every extraction error.

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

**Judgment.** Its detailed training disclosure and verified adaptation path make it relevant to the research. They do not establish greater mask accuracy than Qwen-Max, Kimi, or DeepSeek, or a minimum hardware requirement.

### Qwen3.8-2.4T-A95B

**Starting weights.** This is the released post-trained, text-only Qwen3.8-Max model: 2.4T total parameters, 95B activated per token. Its release reports IFBench of 82.8. The detailed pretraining corpus mixture is not specified sufficiently in the release used here to characterize it as precisely as Nemotron's.[^1]

That instruction-following result is a relevant general-capability signal, not a predicted extraction score. It must not be compared directly with differently configured IFBench results to manufacture a reliable ordering.

**Fine-tuning is real, not merely implied by downloadable weights.** NeMo documents full-parameter training using expert and pipeline parallelism. A public-checkpoint run completed 100 HellaSwag training steps on 256 GPUs. The documentation explicitly limits the result to validating training mechanics, not convergence.[^4]

**Important behavior.** The released model requires thinking mode. Answer-only mask fine-tuning or a different inference format may be possible, but neither has been demonstrated for this task.[^1]

**Judgment.** Its task-fine-tuned advantage over the dense Qwen release is unknown and must not be inferred from parameter count alone.

### Qwen3.8-27B

This is the relevant current dense Qwen alternative. Its release reports IFBench of 79.5 versus 69.1 for Qwen3.6-27B, supports optional thinking, and retains the Qwen3.5-family hybrid language-model architecture.[^5]

NeMo has full-training and LoRA recipes for the exact checkpoint. Its documented 100-step demonstrations use medical visual question answering and report training loss, with validation disabled for those curve-only runs.[^6] They establish a working adaptation path, not extraction quality.

A separate community project reports fine-tuning Qwen3.8-27B with 4-bit QLoRA on one RTX 3090 with 24GB memory. It extracts facts through multiple calls rather than generating our complete mask set; its release explicitly omits source spans. This is evidence for an affordable adaptation path, not a forecast of our mask quality.[^23]

That release reports one training pass over 4,255 rows, taking 20,860 seconds including epoch evaluation. The reported runtime is for that dataset and training recipe, not a mask-extraction training forecast.[^23]

**Judgment.** Its published capability and adaptation evidence make it relevant. Neither its parameter count nor those results establish superior subject-mask quality over smaller or larger alternatives.

### Gemma 4 31B

Gemma 4's training covers broad web documents, code, and multimodal data, followed by instruction tuning. The dense 31B release reports stronger general benchmark results than its 12B sibling; for example, MMLU Pro is 85.2 versus 77.2, and BigBench Extra Hard is 74.4 versus 53.0.[^7]

These are reasons to consider the larger checkpoint, not forecasts of mask accuracy. NVIDIA also publishes a concrete Gemma 4 31B fine-tuning example for structured receipt extraction.[^8] Receipts provide a relevant structured-output demonstration but very different semantics and source structure.

Unsloth's Gemma 4 training guide also reports that 31B QLoRA works with 22GB GPU memory and provides a training notebook. This is a lower-memory adaptation path than the full-training demonstration; memory still depends on the workload and training settings.[^24]

**Judgment.** A strong independent dense-model candidate with both structured-extraction and adapter-training evidence. Neither establishes subject-mask accuracy.

### Gemma 4 26B-A4B

The instruction-tuned MoE checkpoint has approximately 26B total and 3.8B active parameters per token. It is ungated and Apache-2.0 licensed. The Gemma 4 report gives MMLU Pro scores of 82.6 for this model and 85.2 for 31B, while other benchmark gaps are larger. These are reasons to test its retained understanding, not predictions of mask or prominence quality.[^7][^25]

Unsloth publishes an adapter-training notebook for this checkpoint. Its saved 60-step run reports 48.99 GiB peak reserved memory and 22.1 minutes on one A100 80GB. The corresponding 31B notebook reports 21.43 GiB and 6.5 minutes on an A100 40GB. Different hardware and adapter details prevent a controlled speed comparison; neither run establishes minimum memory or our workload's cost. They do show that fewer active parameters do not guarantee cheaper training.[^26]

Lower active computation could reduce corpus-generation cost, but total expert storage, batching, quantization and serving software affect realized throughput. vLLM lists native Gemma 4 and LoRA support. T5Gemma is absent from its native support list, although Transformers supports it; this is uncertainty about an efficient serving path, not an inability to run the model.[^27]

**Judgment.** A credible quality–cost comparison with dense Gemma 31B. Its mask quality, prominence quality and batched generation cost require measurement. Comparing these checkpoints does not isolate architecture alone.

## Encoder–decoder candidates

### T5Gemma 9B-9B PrefixLM instruction-tuned

The model adapts Gemma 2 weights into separate encoder and decoder networks. The released model card reports 2T adaptation tokens; the PrefixLM approach combines prefix-continuation learning with knowledge distillation. Public checkpoint metadata counts **20,333,401,088 parameters**, not 9B total.[^14][^15]

This preserves substantial pretrained knowledge while separating full-input encoding from answer generation. It provides a larger, older-foundation alternative to the smaller T5Gemma 2 release discussed below.

The encoder runs once per input; only the decoder generates each subsequent output token while attending to encoder outputs. The paper reports latency similar to decoder-only Gemma 2 9B for its 9B–9B model, with better evaluated quality. That experiment used 200 GSM8K questions at batch size one and does not establish batched source-mask throughput. Decoder-only models also receive the complete note before generating their first output token.[^14]

**Why PrefixLM first within this family?** Its published generation-oriented results provide a reason to try it, whereas UL2's stronger encoder representations do not directly answer the generated-mask question. This is a starting hypothesis, not a demonstrated superiority on masks. The UL2 checkpoint remains a legitimate comparison.[^14]

### T5Gemma 2 4B-4B

This remains relevant despite being smaller. It adapts Gemma 3 pretrained weights, uses approximately 2T additional training tokens, and has a redesigned architecture and broader multilingual/multimodal preparation. Its text component is approximately 7.1B parameters. Released checkpoints are pretrained rather than instruction-tuned.[^16]

The meaningful comparison is therefore **a larger older-foundation encoder–decoder versus a smaller newer-foundation encoder–decoder**. Neither “newer wins” nor “larger wins” follows automatically. The model should be compared after task fine-tuning, rather than eliminated for poor instruction following before adaptation.

### FLAN-UL2 20B and FLAN-T5-XXL 11B

FLAN-UL2 applies instruction tuning to a 20B encoder–decoder with mixed denoising pretraining; its release compares favorably with FLAN-T5-XXL on several general evaluations.[^22] Neither result establishes subject-mask accuracy. These provide established encoder–decoder foundations alongside the newer T5Gemma family.

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

The reviewed evidence covers distinct pretrained foundations and extraction approaches. It does not establish that every unnamed model is worse.

## Published training hardware and weight storage

The following numbers are **arithmetic estimates for weights alone**, at two bytes per parameter. They exclude activations, gradients, optimizer state, temporary buffers, and inference caches. Decimal GB/TB are used. Quantized checkpoints can require substantially less weight memory.

| Model | Total parameters | Parameters active per token, where applicable | Approximate BF16 weight storage |
|---|---:|---:|---:|
| Qwen3.8-Max | 2.4T | 95B | 4.8 TB |
| Nemotron 3 Ultra | 550B | 55B | 1.1 TB |
| Qwen3.8-27B language model | 27B | — | 54 GB |
| Gemma 4 31B | Approximately 31B | — | 62 GB |
| Gemma 4 26B-A4B | Approximately 26B | 3.8B | 52 GB |
| T5Gemma 9B-9B | 20.33B | — | 40.7 GB |

Parameter counts come from the releases above.[^1][^2][^5][^7][^15][^25] The storage values are calculated, not measured deployments. Mixture-of-experts models use only part of their weights for each token, but the remaining experts must still be stored and made available; active parameter count is not their complete memory footprint.

Full-parameter fine-tuning additionally maintains trainable state for the model. LoRA trains a much smaller set of added parameters but still requires access to the foundation weights, as illustrated by the adaptation implementations above.[^3][^4][^6] Quantization, sequence length, batch size, parallelism, and optimizer choice materially affect the actual requirement. An inference demonstration on one GPU is not a training-resource estimate.

The public implementation evidence is more concrete than guessing one universal GPU count:

| Model | Demonstrated adaptation | Published demonstration hardware | What it establishes |
|---|---|---|---|
| Nemotron Ultra | LoRA on HellaSwag | 16 GB200 GPUs | Working training and checkpointing; not extractor accuracy |
| Qwen3.8-Max | Full-parameter training, 100 HellaSwag steps | 256 GB200 GPUs | Training mechanics, explicitly not convergence |
| Qwen3.8-27B | Full training and LoRA on medical visual questions | 8 H100 80GB GPUs | Working recipes for the exact checkpoint |
| Qwen3.8-27B | Community 4-bit QLoRA for fact extraction | One RTX 3090, 24GB | Lower-memory task adaptation; different outputs and evaluation from our masks |
| Gemma 4 31B | Full fine-tuning for receipt-to-JSON extraction | 8 A100 80GB or H100 80GB GPUs in the guide | A concrete structured-extraction training path |
| Gemma 4 31B | QLoRA training guide and notebook | Reported 22GB GPU memory | Lower-memory adapter-training support; not a measured subject-mask workload |
| Gemma 4 26B-A4B | Adapter-training notebook, 60 steps | One A100 80GB; 48.99 GiB peak reserved | Working published training example; not a minimum-memory or mask-quality result |

These configurations are **not established minimum requirements**.[^3][^4][^6][^8][^23][^24][^26] They use different tasks and training methods, so their GPU counts do not form a fair efficiency benchmark.

The economic question remains important because the extractor is intended to replace repeated frontier-model calls. A larger fine-tuned model may be worthwhile if it materially reduces errors or if its batched throughput is favorable. A smaller model may deliver equivalent usable masks at lower cost. Neither result follows from model size alone, and this research does not establish a break-even volume.

## Limits of the published evidence

**The unresolved quantity is useful mask quality after learning our annotation policy.** General instruction-following scores, a decreasing fine-tuning loss, and an extraction benchmark with supplied field names cannot substitute for that measurement.

The studies use different input distributions, annotation policies, model sizes, and training methods. Their results cannot be combined into a reliable ranking of fine-tuned subject-mask extractors. Existing knowledge, task-specific learning, annotation quality, and serving cost remain distinct considerations; no reviewed result resolves their tradeoff for this task.

## Sources

[^1]: Qwen, [Qwen3.8-2.4T-A95B model card](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B). Architecture, instruction-following results, reasoning format, and release links. See also its [license](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/blob/main/LICENSE); open weights should not be confused with identical terms across model families.
[^2]: NVIDIA, [Nemotron 3 Ultra 550B-A55B model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16). Pretraining, post-training, architecture, and supported reasoning modes.
[^3]: NVIDIA NeMo, [Nemotron 3 Ultra end-to-end adaptation recipe](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/nemotron-3-ultra). LoRA, HellaSwag, hardware, and validation scope.
[^4]: NVIDIA NeMo, [Qwen3.8-2.4T-A95B training coverage](https://docs.nvidia.com/nemo/automodel/model-coverage/large-language-models/qwen/qwen3-8-2-4t-a95b). Full-parameter training implementation and the limits of its 100-step validation.
[^5]: Qwen, [Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B). Dense-model architecture, optional reasoning, and release benchmark results.
[^6]: NVIDIA NeMo, [Qwen3.8-27B end-to-end adaptation recipes](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/qwen3-8-27b). Full training and LoRA examples; validation conditions.
[^7]: Google, [Gemma 4 31B instruction-tuned model card](https://huggingface.co/google/gemma-4-31B-it) and [Gemma 4 technical report](https://arxiv.org/html/2607.02770v1). Training background, model sizes, and general capability results.
[^8]: NVIDIA NeMo, [Gemma 4 fine-tuning for structured receipt extraction](https://docs.nvidia.com/nemo/automodel/recipes-e2e-examples/gemma-4). Training task and hardware examples.
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
[^23]: Thomas Davis, [Donto Qwen3.8-27B predicate extractor](https://huggingface.co/ajaxdavis/donto-qwen3.8-27b-predicate-extractor?library=peft). Community release reporting single-RTX-3090 QLoRA training, multi-stage fact extraction, and limitations; not a source-mask benchmark.
[^24]: Unsloth, [Gemma 4 fine-tuning guide](https://unsloth.ai/docs/models/gemma-4/train). QLoRA support, reported 22GB memory for the 31B model, and training notebook.
[^25]: Google, [Gemma 4 26B-A4B instruction-tuned checkpoint](https://huggingface.co/google/gemma-4-26B-A4B-it). Architecture, active parameters, license and access status.
[^26]: Unsloth, [Gemma 4 26B-A4B text-training notebook](https://github.com/unslothai/notebooks/blob/main/nb/Gemma4_%2826B_A4B%29-Text.ipynb) and [Gemma 4 31B text-training notebook](https://github.com/unslothai/notebooks/blob/main/nb/Gemma4_%2831B%29-Text.ipynb). Saved training outputs inspected September 24, 2026; resource figures describe those demonstrations only.
[^27]: vLLM, [supported models](https://github.com/vllm-project/vllm/blob/main/docs/models/supported_models.md); Hugging Face, [T5Gemma in Transformers](https://huggingface.co/docs/transformers/model_doc/t5gemma). Serving-support evidence inspected September 24, 2026.
