# Models for fine-tuning the subject-and-mask extractor

## Recommendation

**Start with Qwen3.5-9B. Compare it with T5Gemma 2 4B-4B before committing to an architecture. Keep Gemma 4 12B as the next general-purpose alternative.** These are priorities for task-specific fine-tuning, not a claim that a published benchmark has already established the winner.

The intended replacement is:

```text
complete Nostr note → complete set of grouped source-text masks → unchanged SSE
```

The difficult part is discovering the meanings and choosing their evidence. Producing a JSON array is comparatively easy. A useful student needs broad language understanding as well as reliable source-text selection; neither an extraction-branded model nor an encoder–decoder architecture guarantees both.

| Priority | Checkpoint | Size relevant to text | Reason to consider it | Main uncertainty |
|---|---|---:|---|---|
| 1 | `Qwen/Qwen3.5-9B` | 9B language model | Modern general understanding; documented task fine-tuning; a practical first student | Whether its understanding and source selection survive task adaptation at the required quality |
| 2 | `google/t5gemma-2-4b-4b` | About 7.1B text parameters | Modern encoder–decoder; complete-input encoding and source-reconstruction pretraining | Less mature serving support; released checkpoint is pretrained, not instruction-tuned |
| 3 | `google/gemma-4-12B-it` | About 12B | Independent, broadly pretrained general model with current fine-tuning support | More memory; no direct evidence of better subject-mask extraction |

Model specifications come from the releases and technical reports.[^1][^2][^3][^4] The ranking is an inference from task fit, pretrained capability, and implementation risk. No study located compares these models on complete, overlapping subject-mask extraction from informal social-media notes.

## The task the student must learn

The existing proposal removes the separate subject-generation and per-subject masking calls from production. The student must discover the number and contents of the masks itself. Supplying a subject and asking for its mask would test only half of that replacement.[^5]

A mask is a set of source-text ranges. Its fragments can be separated; different masks can overlap. The source note can contain pronouns, implied meaning, quotations, jokes, multiple topics, and unfamiliar names. The model must interpret these in context while selecting text that captures the subject's scope, without adding unrelated meaning.

The frozen teacher records are ASv6.23 for subjects and MPv3.5 for masks. They can supply training supervision, but the production student does not necessarily need to generate the intermediate subject descriptions or the subject agent's auxiliary context field. The final student output format remains a design choice, not something settled by this model comparison.[^6]

Subject descriptions, exact fragments, and source ranges should remain available in the training records even if only masks are ultimately emitted. This preserves the evidence needed to diagnose whether a bad output arose from a missing subject or a badly scoped mask.

There is not necessarily one correct list of masks. Valid alternatives and harmless redundancy should not be mistaken for failure. Conversely, a valid JSON document containing exact copied text can still omit subjects, combine unrelated meanings, or select the wrong evidence.

## Relevant experimental evidence

### Direct mask generation: PropSegmEnt

PropSegmEnt is the closest structural precedent. Its T5-v1.1-large model generates proposition masks that can overlap and contain separated text. Training used 9,913 sentences with 38,206 proposition annotations. Reported in-domain fuzzy F1 was 55.50, compared with 67.07 human agreement under the same evaluation; its BERT-based segmentation baseline scored 34.17.[^7]

This establishes that a pretrained text-to-text model can learn the output structure. It does not establish adequate Nostr performance: the annotations are factual propositions, the source domains differ, and performance was imperfect. The T5/BERT comparison is evidence about those particular systems, not proof that every generator beats every encoder with an extraction head.

### Learning decomposition from a teacher

The SSE work trained a separate T5-large proposition generator on 44,970 teacher-labeled sentences. It then obtained masks through a separate alignment procedure. This supports learning a decomposition task from a stronger model, but not direct mask accuracy.[^8]

Abstractive Proposition Segmentation also distilled proposition generation into Gemma 2B/7B students using 226,000 generated passages across 75 domains. These outputs were rewritten propositions rather than source masks. The relevance is that decoder-only models are viable students for generating multiple meanings; the training quantity is not a minimum for this project.[^9]

### Recent structured-extraction fine-tuning

A 2026 merchant-extraction study fine-tuned several models on 6,125 transaction records. Its Qwen3.5-4B JSON-only configuration reported F1 of 96.60, close to the tested Llama-3.1-8B configurations.[^10]

This is useful evidence that a contemporary smaller model can learn precise structured output from noisy text. However, the outputs were predefined merchant-related fields. It did not test discovering arbitrary subject meanings or grouping discontinuous masks. It also did not test Qwen3.5-9B. Its high score is therefore not an estimate of this extractor's likely accuracy.

These studies favor testing a generative student. They do not establish that copying, interpretation, and complete subject discovery will all become reliable together.

## Candidate 1: Qwen3.5-9B

**What the weights have learned.** The release describes broad vision-language pretraining followed by post-training, including reinforcement learning, with support for 201 languages and dialects. The 9B text model combines Gated DeltaNet layers with full-attention layers. This is a general language model, not an embedding model or a specialist mask extractor.[^1]

**Why it is first.** The practical hypothesis is that a capable general model already understands much of an informal note, and task training can teach the specific extraction policy. Qwen offers a manageable starting size and a documented fine-tuning path, without first building a new prediction head or a separate subject-discovery mechanism. LlamaFactory documents Qwen3.5-9B LoRA training; Unsloth also documents text fine-tuning.[^11][^12]

Start from the post-trained checkpoint, rather than the separately released base checkpoint. This is a data-efficiency hypothesis, not a universal rule: instruction following may help a student learn the task from a modest annotation set. The model supports disabling its thinking output; direct task output is the proposed starting configuration.[^1]

**Important practical limitation.** Unsloth currently warns against 4-bit QLoRA for Qwen3.5 because of quantization differences, and recommends BF16 setups. Its published 9B BF16-LoRA memory figure is approximately 22GB under its configuration. That figure is not a guarantee for this dataset's batch size or output lengths.[^12]

**Unproven:** whether Qwen can discover the full subject set and preserve difficult mask boundaries after fine-tuning. General reasoning scores, JSON support, and the merchant study cannot answer that.

## Candidate 2: T5Gemma 2 4B-4B

**What the weights have learned.** T5Gemma 2 initializes from Gemma 3 pretrained weights, then receives approximately two trillion tokens of further training. Its data includes multilingual web text, code, mathematics, and images. The UL2 training mixture includes recovering corrupted text and continuing prefixes.[^3]

That is relevant preparation for reading source text and generating selected content, but recovering deliberately hidden text is not the same task as deciding which subject masks should exist.

**What the model does.** An encoder builds contextual representations of the complete input. A decoder generates the output while attending to those representations. This separates input processing from output generation. Google adapted the architecture from a modern language model rather than relying on the original T5 weights.[^13]

**Its size is easy to misread.** The 4B-4B model has approximately 7.1B text parameters, not 4B total. Shared embeddings reduce the combined count. The vision component adds about 417M parameters. Text-only inputs are supported, but that does not establish that the standard loader omits the vision weights; budget for the complete checkpoint initially.[^3][^13][^14]

**Why it deserves a comparison.** The source-to-mask task fits an encoder–decoder naturally, and the model brings much newer pretraining than original T5. It is the strongest architectural alternative in this shortlist. Nevertheless, a decoder-only model's generated answer also has access to the complete input: bidirectional encoder attention is a plausible advantage to test, not proof of superior contextual understanding.

**Practical disadvantages.** The released T5Gemma 2 checkpoints are pretrained, not instruction-tuned. A weak response to the teacher prompt before fine-tuning would not be a fair reason to reject it. Transformers documents support, but the vLLM request for this model is closed as not planned. Straightforward batched Transformers inference remains possible; a high-throughput production setup is less established than for the decoder-only candidates.[^14][^15]

T5Gemma 2 uses the Gemma license, unlike the Apache-licensed Qwen and Gemma 4 releases. This is a licensing distinction to check before deployment, not an assessment of legal suitability.[^1][^2][^14]

## Candidate 3: Gemma 4 12B

**What the weights have learned.** Gemma 4 pretraining covers web documents, code, images, and audio. The instruction-tuned release adds post-training for following instructions. The 12B variant is a dense, approximately 12-billion-parameter model; it is not the smaller active portion of a much larger mixture-of-experts model.[^2][^4]

**Why it is a useful alternative.** It provides an independently trained general model with potentially different interpretation errors. Google documents LoRA and full tuning for the 12B release. It therefore offers a practical quality comparison without depending on the same family as Qwen.[^16]

It is third rather than first because this investigation found no closely matched extraction result establishing an advantage over Qwen, while its weight memory is higher. That is a prioritization decision, not a finding that it is less accurate. It becomes more valuable if Qwen's remaining errors concern interpreting the note rather than generating source text correctly.

The release is Apache 2.0. Its optional multimodal inputs are not a reason to add images or audio to this experiment.[^2]

## Other models and why they are not the first comparison

| Model or approach | Assessment |
|---|---|
| **T5Gemma 9B-2B** | Particularly interesting if generation cost becomes the bottleneck: a large encoder processes the input and a smaller decoder emits the answer. Published experiments support the quality–efficiency rationale. It uses Gemma 2 rather than Gemma 3 pretraining and is a reserve architecture, not automatically inferior because it is older.[^17] |
| **FLAN-T5-XXL, about 11B** | A valid established baseline. It adds instruction tuning on more than 1,000 tasks to T5. Its size alone does not make it a better starting point than modern alternatives, and no matched result located establishes it as the best student here.[^18] |
| **Qwen3.5-4B** | The first smaller model to consider after identifying a successful training recipe. It has related extraction evidence, but prioritizing its lower cost immediately could confound an unclear task with insufficient model capability.[^10] |
| **IBM Granite 4.1 8B** | A credible general-model reserve. IBM reports approximately 15T pretraining tokens, followed by instruction tuning and staged reinforcement learning. Its documented strength in structured/instruction-following tasks is relevant, but no direct grouped-mask advantage was established.[^19] |
| **gpt-oss-20b** | A credible fine-tunable open-weight reserve, with about 21B total and 3.6B active parameters. Active parameters are not total weight memory. Configurable reasoning and structured output are useful capabilities, but neither establishes a mask-extraction advantage.[^20] |
| **Qwen3.8-27B** | A larger current family option if interpretation quality, rather than annotation coverage or training setup, appears to limit the smaller student. This is not the first run: it increases the resource commitment before the task has been tested.[^21] |
| **GLiNER2 and similar schema-driven extractors** | Relevant for supplied entity types and fields, but not drop-in replacements for open-ended subject discovery. Their smaller size does not solve the missing task definition. A new subject-discovery mechanism or substantially different prediction setup would be required.[^22] |
| **Custom encoder with mask-prediction heads** | Potentially efficient, but involves choosing how to predict an unknown number of overlapping, discontinuous masks. The closest published baseline did not beat its generative counterpart. Worth revisiting only with evidence that generation cost justifies the additional model-design work.[^7] |

Phi, Ministral, and Liquid model families also supply trainable general or extraction-oriented models. Their availability does not make them unsuitable; the research did not find sufficiently matched evidence to displace the first two candidates. Treating every released model as an initial contender would spend training resources without a clear discriminating hypothesis.

## Training and inference requirements

The student starts from existing language-model weights. No large-scale language pretraining, embedding-model training, or change to SSE is proposed.

### Weight memory

These figures are approximate decimal GB for **16-bit weights alone**, calculated as two bytes per parameter. They exclude gradients, optimizer state, activations, caches, temporary buffers, and additional multimodal modules unless stated.

| Candidate | Approximate weight memory | Interpretation |
|---|---:|---|
| Qwen3.5-9B text model | 18GB | Not total training memory |
| T5Gemma 2 4B-4B complete checkpoint | 15GB | About 14.2GB belongs to the text model |
| Gemma 4 12B | 24GB | A 24GB card is not a sensible assumption for unquantized training |
| FLAN-T5-XXL | 22GB | Parameter count is not evidence of better quality |

Parameter sources are the model releases and reports.[^1][^3][^4][^18] The memory arithmetic is an estimate, not measured usage on the corpus.

**Adapter fine-tuning** keeps the base weights fixed and trains a much smaller set of added weights. It reduces gradient and optimizer memory, but the base model still has to be loaded and its computations still run. **Full fine-tuning** updates all weights and requires substantially more memory. **Quantization** reduces weight precision and can change outputs; it should not silently become an additional variable in the initial model comparison.

For planning, a single 48GB-class GPU is a reasonable starting resource for sequential BF16-adapter experiments with these candidates, short notes, small batches, and memory-saving training settings. This is a provisional engineering estimate, not a claim that an untested T5Gemma setup will fit every batch. Profile the longest source-and-output examples before booking a larger run. Qwen's documented 22GB result supports feasibility but does not substitute for that check.[^12]

The speed question is **complete notes processed at acceptable mask quality**, not advertised token throughput. Encoder–decoder models process the input through a separate encoder; decoder-only models encode their input before generating output too. Long output sets, batching, implementation support, and the exact input/output format can change their relative costs. None of the sources supplies a credible wall-clock estimate for this corpus.

Current uncertainty therefore does not justify quoting a rental bill or assuming that one million notes will be cheap enough. A measured end-to-end rate on the actual task is needed first.

## A comparison that would resolve the choice

The first question is whether a student can replace the complete teacher workflow, not which student best follows the existing long prompt without training.

Use the same complete, reviewed note annotations for both primary candidates. Begin with the modest learning-curve sizes already proposed in the training-data review, rather than generating a huge corpus before observing student behavior. Those sizes are experimental starting points, not established requirements.[^23]

Keep the meaning of the target output fixed across models. Do not give one candidate supplied subjects while requiring the other to discover them. Do not judge the pretrained T5Gemma 2 checkpoint against instruction-tuned Qwen solely through zero-shot prompts. Task fine-tuning is the comparison being proposed.

Separate three observations:

1. **Coverage:** did the model identify the subject meanings that should be represented?
2. **Mask fidelity:** does each mask select the right evidence, with the intended scope?
3. **Mechanical validity:** are fragments exact source text, and can their occurrences be mapped unambiguously back to the note?

Mechanical checks can identify fabricated text or unusable ranges cheaply. They cannot establish coverage or semantic fidelity. Those need semantic inspection of held-out complete notes, with valid alternative masks accepted. Split by note and keep near-duplicate posts together so training and evaluation do not share essentially the same content.

Adapter configurations need not use identical rank or identical layer names across different architectures. The relevant control is a comparable, documented adaptation opportunity. A failed run caused by unsupported layers, truncation, or a broken output parser says nothing about the model's semantic capacity.

The next decision should follow the observed error:

- If copied text is malformed but subject coverage is good, investigate output representation or constrained generation before increasing model size.
- If masks are well formed but difficult meanings are consistently missed, distinguish missing training examples from deficient interpretation; then consider Gemma 4 12B or a larger model.
- If both primary candidates approach teacher quality, measure throughput and try a smaller model rather than keeping the larger one by default.
- If quality remains inadequate, more training data is one possible response—not an automatic explanation or an unlimited commitment.

This keeps the central decision narrow: **which pretrained student most reliably learns the actual extraction policy at a practical cost?**

## Conclusion

**Qwen3.5-9B is the best first practical candidate; T5Gemma 2 4B-4B is the most important architectural comparison.** Gemma 4 12B is a credible next alternative. Original T5-11B should not be selected merely because earlier extraction papers used T5.

The literature supports attempting this distillation. It does not yet establish the best model, the necessary number of notes, or production-quality direct masks for this annotation policy. A small, controlled task-fine-tuning comparison is the evidence that would turn this shortlist into a selection.

## Sources

Model availability and implementation guidance checked in September 2026. Software support and release recommendations can change.

[^1]: Qwen, [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B), 2026. Language-model parameter count, pretraining/post-training, architecture, multilingual coverage, non-thinking mode, and Apache license.

[^2]: Google, [Gemma 4 12B instruction-tuned model card](https://huggingface.co/google/gemma-4-12B-it), 2026. Released checkpoint, size, modalities, post-training status, and Apache license.

[^3]: Zhang et al., [T5Gemma 2: Seeing, Reading, and Understanding Longer](https://arxiv.org/html/2512.14856v1), December 2025. Table 2 for parameter accounting; §3.1 for initialization, data, and approximately 2T-token additional pretraining.

[^4]: Gemma Team, [Gemma 4 Technical Report](https://arxiv.org/html/2607.02770v1), July 2026. Architecture and parameters; §§2.4 and 3 for pretraining and instruction tuning.

[^5]: Repository proposal, [Direct note-to-mask extractor](../docs/recommendation-engine/research/direct-note-to-mask-extractor.md). Architectural target only; older prompt references there are not the current frozen versions.

[^6]: Repository freeze records: [ASv6.23](./subject-prompt-goal-v1/asv6.23/frozen.json) and [MPv3.5](./mask-prompt-goal-v1/frozen.json). Current teacher input/output responsibilities.

[^7]: Chen et al., [PropSegmEnt: A Large-Scale Corpus for Proposition-Level Segmentation and Entailment Recognition](https://aclanthology.org/2023.findings-acl.565.pdf), Findings of ACL, 2023. Table 2 for training size; §4 and Tables 3–4 for output structure, model results, and agreement.

[^8]: Chen et al., [Sub-Sentence Encoder: Contrastive Learning of Propositional Semantic Representations](https://aclanthology.org/2024.naacl-long.89.pdf), NAACL, 2024. Appendix A for the separate teacher-trained proposition generator and subsequent alignment.

[^9]: Hosseini et al., [Scalable and Domain-General Abstractive Proposition Segmentation](https://aclanthology.org/2024.findings-emnlp.517.pdf), Findings of EMNLP, 2024. Gemma student training and the 226,000-passage, 75-domain distillation corpus.

[^10]: [How Small Can You Go? LoRA Fine-Tuning 270M–8B Models for Merchant Information Extraction in Financial Transactions](https://arxiv.org/html/2606.08051v1), June 2026. Fixed-field transaction extraction; dataset splits and model/configuration comparisons. Its task and reported metric do not establish performance for open-ended masks.

[^11]: LlamaFactory, [Fine-Tuning Qwen3.5 with LlamaFactory](https://blog.llamafactory.net/en/posts/qwen3_5_finetuning/), March 2026. Concrete 9B LoRA support; the demonstration task is not this extractor.

[^12]: Unsloth, [Qwen3.5 Fine-tuning Guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune), accessed September 2026. Published BF16-LoRA memory figures and current warning against 4-bit training. Memory figures are configuration-specific.

[^13]: Google, [T5Gemma 2: The next generation of encoder-decoder models](https://blog.google/innovation-and-ai/technology/developers-tools/t5gemma-2/), December 2025. Modern decoder-to-encoder–decoder adaptation and text-only model sizes.

[^14]: Google, [T5Gemma 2 4B-4B model card](https://huggingface.co/google/t5gemma-2-4b-4b), December 2025; Hugging Face, [T5Gemma 2 Transformers documentation](https://huggingface.co/docs/transformers/main/model_doc/t5gemma2). Pretrained release status, text-model support, and license.

[^15]: vLLM, [T5Gemma 2 support request, issue 31004](https://github.com/vllm-project/vllm/issues/31004), opened December 2025; status checked September 2026. Closed as not planned. This is a limitation of the documented serving path, not proof that efficient deployment is impossible.

[^16]: Google Developers, [Gemma 4 12B: The Developer Guide](https://developers.googleblog.com/gemma-4-12b-the-developer-guide/), 2026. Adapter/full fine-tuning and deployment guidance.

[^17]: Zhang et al., [Encoder-Decoder Gemma: Improving the Quality-Efficiency Trade-Off via Adaptation](https://arxiv.org/html/2504.06225), 2025; Google, [T5Gemma 9B-2B UL2 instruction-tuned checkpoint](https://huggingface.co/google/t5gemma-9b-2b-ul2-it). Asymmetric encoder/decoder design and measured efficiency comparisons, not measurements for Nostr extraction.

[^18]: Google, [FLAN-T5-XXL model card](https://huggingface.co/google/flan-t5-xxl), 2022. T5-based instruction-tuned release and task coverage.

[^19]: IBM Research, [Introducing the IBM Granite 4.1 family of models](https://research.ibm.com/blog/granite-4-1-ai-foundation-models), 2026. Dense 3B/8B/30B releases and their training approach.

[^20]: OpenAI, [gpt-oss-20b model documentation](https://developers.openai.com/api/docs/models/gpt-oss-20b), accessed September 2026. Open weights, total/active parameters, fine-tunability, reasoning settings, and structured outputs.

[^21]: Qwen, [Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B), 2026. Released larger-model alternative, not an extraction result.

[^22]: Zaratiana et al., [GLiNER2: An Efficient Multi-Task Information Extraction System with Schema-Driven Interface](https://arxiv.org/html/2507.18546v1), 2025. Schema-conditioned task formulation and evaluation.

[^23]: Repository research, [Training-data volume for a subject-and-mask extractor](./SUBJECT-MASK-TRAINING-DATA-RESEARCH.md). Related-study counts, proposed learning curve, and limits of quantity extrapolation.
