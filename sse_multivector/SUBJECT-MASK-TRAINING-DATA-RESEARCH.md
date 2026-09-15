# Training data quantities for subject and mask extraction

## Planning estimate

**A few thousand complete notes is a defensible starting experiment. Tens of thousands is a plausible development range. Neither is an established requirement for this task.**

The closest published direct-mask system trained on about 10,000 sentences. The SSE paper's separate proposition generator trained on about 45,000 teacher-labeled sentences. Broader proposition distillation has used 226,000 passages. These are useful reference points, not interchangeable demonstrations of how much Nostr training data is necessary.[^2][^3][^4]

My recommendation is to measure an initial learning curve using **1,000, 2,000 and 5,000 notes**, then consider **10,000–50,000** if the results justify expansion. Treat **100,000 or more** as a possible later commitment, not an initial requirement. These ranges are an inference from related work, not a statistical confidence interval or a claim that 50,000 will suffice.

## The task being estimated

The existing extractor proposal replaces the subject and mask calls with:

```text
complete note → set of grouped source-text masks → unchanged SSE
```

The model must discover the subjects as well as identify their supporting text. A mask can contain separated fragments; different masks can overlap. The number of masks varies. The proposal does not require the production extractor to emit the intermediate English subject descriptions.[^1]

This is more than learning to mask a subject supplied in the input. Studies that supply a requested entity type or a fixed list of fields solve a different, narrower problem.

**The primary counting unit should be complete, distinct notes with their complete annotations.** Ten masks from one note provide ten supervised outputs, but not ten independent examples of note structure or subject coverage. A million-note deployment does not, by itself, imply a million-note training requirement.

All models discussed below started from pretrained language-model weights. The reported quantities are additional task-training data, not the text required to learn language from scratch. General pretraining, instruction tuning and earlier extraction training must be distinguished when interpreting small-data claims.

## Closest published precedents

| Study | Additional labeled inputs | Starting model | Relationship to our task |
|---|---:|---|---|
| PropSegmEnt, 2023 | 9,913 sentences; 38,206 proposition masks | Pretrained T5-v1.1-large | Predicts overlapping, potentially discontinuous source-token masks. Closest output structure. |
| SSE / SegmenT5, 2024 | 44,970 sentences with GPT-3.5-generated propositions | Pretrained T5-large | Replaces a proposition-generation teacher; masks are obtained afterward through alignment. |
| Abstractive Proposition Segmentation, 2024 | 1,923 human-labeled training passages in the grouped dataset; 226,000 teacher-generated passages for distillation | Gemini teachers; instruction-tuned Gemma 2B/7B students | Learns sets of rewritten propositions across domains, not source masks. |
| UniversalNER, 2024 | 45,889 teacher-labeled passages | Pretrained LLaMA 7B/13B | Broad text-span extraction, usually conditioned on a requested entity type. |

Sources: PropSegmEnt Table 2; SSE Appendix A; proposition-segmentation Tables 1–3 and §4.3; UniversalNER §4.1 and released dataset.[^2][^3][^4][^7]

**PropSegmEnt.** The training sentences came from 1,260 Wikipedia/news documents. T5 generated marked source copies, one per proposition. Its fuzzy set F1 was 55.50, against measured human agreement of 67.07. That score measures agreement between mask sets, not the percentage of notes perfectly understood. Cross-domain results weakened. The paper demonstrates learning this output structure with roughly 10,000 sentences; it does not establish that this volume solves informal subject extraction or is a minimum.[^2]

**The SSE paper's extractor.** Appendix A gives the precise 44,970-sentence count after filtering. The student reached 33.68 fuzzy set F1 against its teacher's 33.60 at the stricter reported matching threshold. This is meaningful evidence of teacher imitation at tens-of-thousands scale, but not evidence of excellent absolute masking quality: it generates propositions and aligns them afterward. These are the proposition generator's training examples, not the examples used to train SSE's embedding geometry.[^3]

**Broader proposition distillation.** The 226,000 passages covered 75 domains and included synthetic inputs as well as synthetic labels. For Gemma 7B, a reported reference-based F1 on Reddit increased from 36.57 with the small human dataset to 46.20 with one distilled variant. However, that Reddit evaluation contained only 20 passages. Both data source and quantity changed, so the gain cannot be attributed to volume alone. There was no result establishing 226,000 as the necessary amount.[^4]

**UniversalNER.** The approximately 46,000 passages contained 240,725 entity annotations across 13,020 types. Evaluation covered 43 datasets spanning nine domains. This supports the feasibility of broad teacher-to-student extraction, but recognizing spans for supplied types is not discovering arbitrary subject masks. Its data count is an operating point, not a measured minimum.[^7]

## Experiments that actually varied data quantity

### CycleOIE: hundreds versus thousands of sentences

CycleOIE extracts relational tuples rather than arbitrary subject masks. It initializes two models from FLAN-T5-base, already instruction-tuned, and trains extraction and sentence reconstruction together. On subsets of the same IMoJIE dataset, it reported:[^5]

| Labeled sentences | CaRB extraction F1 |
|---:|---:|
| 825 | 34.2 |
| Approximately 4,600 | 49.8 |
| Approximately 18,300 | 50.3 |

The last two counts are rounded conversions of the paper's 5% and 20% subsets of 91,725 sentences. These are extraction scores, not percentages of correct notes.

Separate teacher-labeled datasets containing 2,147 and 4,901 sentences produced F1 scores of 53.1 and 51.2. They used different annotation instructions, so their ordering is not evidence that less data is inherently better. Training used two models and up to 100 epochs; low annotation volume did not mean trivial training work.[^5]

**Implication:** a few thousand inputs can reveal whether an extraction approach works. Large gains may occur before 5,000, with much smaller gains afterward. That pattern is evidence for testing small first, not a predicted learning curve for our masks.

### NuNER: thousands versus one million sentences

NuNER starts with RoBERTa-base and adds entity-specific training on GPT-3.5 annotations. Its data-size experiment then evaluates the resulting representation through a separately trained entity classifier. One reported setting used 8–16 labeled entities per type in that later classifier stage:[^6]

| First-stage dataset size | Average downstream token-classification F1 |
|---:|---:|
| 1,000 sentences | 60.3 |
| 3,000 | 61.9 |
| 30,000 | 63.0 |
| 100,000 | 63.5 |
| 300,000 | 64.5 |
| 1,000,000 | 64.8 |

These are the paper's nominal dataset sizes. Its main million-sentence run splits data 90%/10% between training and validation. Scores average four target datasets; they do not evaluate complete subject-mask generation. One biomedical dataset peaked before the largest training size.[^6]

**Implication:** more labeled data can help while providing diminishing returns, and aggregate improvement need not mean every domain improves. Also, a downstream model advertised as needing only a handful of examples may rely on substantial earlier task-specific training.

## Other relevant bounds and cautions

**A misleading 900-example headline.** OK-IE fine-tunes a T5-base extraction stage using about 900 examples. However, it retains an earlier predicate-extraction stage. CycleOIE's subsequent comparison explicitly identifies that stage as inherited from a system trained on the full 91,725-sentence IMoJIE dataset. The 900 count therefore does not describe the training needed for the complete extraction pipeline.[^10][^5]

**Reference resolution with about 11,000 examples.** Choi et al. trained on 11,290 decontextualization examples: a sentence plus surrounding context becomes a standalone rewritten sentence. A T5-11B model was judged correctly decontextualized in 67.5% of a 100-example edited-output sample, versus 78.5% for human references. The source was selected Wikipedia material; difficult technical content and plot sections were excluded. This is relevant to resolving context, but not evidence that ten thousand examples reliably cover informal references across Nostr.[^9]

**Very small datasets can work for fixed tasks.** A 2025 clinical extraction study fine-tuned pretrained Llama-3.1 8B models. Dataset-specific models matched a second annotator with 100 breast, 95 kidney, 43 prostate and 72 bone-marrow reports. These were institution-specific reports and predefined fields, not open-ended discovery. The study also showed strong sensitivity to the learning rate. Its result supports cheap preliminary training; it does not justify expecting our whole task to work with 100 notes.[^11]

**Hundreds of examples can conceal a much larger starting model.** Dagdelen et al. demonstrated scientific structured extraction with hundreds of annotated texts. Their materials datasets included approximately 650 and 507 records, with 90% used for training in repeated splits. Tested generators included Llama-2-70B and GPT-3's 175B model. The outputs followed task-specific structured schemas. This is useful evidence of adaptation from existing knowledge, but not a direct small-local-model sample-complexity estimate.[^12]

**Hundreds of thousands are used for broader extraction products.** GLiNER2 reports 254,334 training examples: 135,698 real and 118,636 synthetic, annotated with GPT-4o. It uses a 205M-parameter encoder and supports supplied schemas for several extraction tasks. The paper evaluates entity recognition and classification; its broader structured extraction capability was not benchmarked there. It gives a scale reference for broad specialization, not evidence that our extractor needs a quarter-million notes.[^8]

## Interpretation for Nostr

The nearest task matches make **10,000–50,000 labeled notes a reasonable working range to investigate**, rather than a number established by the literature. Three uncertainties prevent a tighter forecast.

First, the proposed extractor must learn the annotation policy as well as recognize language. It must decide which subject meanings to emit and what evidence belongs in each mask. A model can copy text accurately while omitting subjects or adding unrelated meaning. Additional token-level labels do not automatically address those failures.

Second, coverage matters independently of count. Thousands of similar food notes may teach less about informal reference resolution, questions, quotes and fragmented writing than a smaller but varied collection. That does not mean every topic needs its own examples: a pretrained model already has transferable knowledge. It means a pooled average can hide gaps relevant to deployment.

Third, the student model and the required quality remain unspecified. The amount needed to improve a weak baseline differs from the amount needed to approach the current teacher. A model that already understands the passages may mainly need to learn the output convention; another may lack the necessary interpretation skills. The published counts cannot resolve that distinction for us.

The quantity estimates also depend on whether training uses direct grouped masks, rewritten subject text, or both. The research does not establish that one representation requires a particular multiple of the other's data. Preserving existing intermediate annotations is useful, but does not commit production to emitting them.

## Measuring the requirement without labeling everything first

The next training investigation should measure how the chosen student's performance changes with additional **unique notes**, while holding the task definition and evaluation constant. This is a recommendation, not an approved training run.

1. **Choose one pretrained student and a fixed output contract.** Changing the model, annotation policy and dataset size together would prevent attributing improvement to more data. Check that training and output parsing work on a small sample first.
2. **Set aside independently checked notes.** Split before training, keeping duplicated or closely related material from leaking across the split. Include ordinary notes as well as the extraction challenges actually present in the corpus. Do not use this final set to tune every revision.
3. **Compare nested sets of 1,000, 2,000 and 5,000 training notes.** Larger sets retain the smaller sets' notes. These are economical measurement points, not claims of sufficiency. Give each run a reasonable opportunity to learn; a poorly trained checkpoint is not evidence that more annotations are needed.
4. **Assess meaning separately from formatting.** Check subject coverage, unsupported selections, missing context and added meaning. Exact mask matching can assist analysis, but alternative valid masks and harmless duplication should not be treated as automatic semantic failures.
5. **Expand where the result justifies it.** If meaningful errors decline, test 10,000 and then a larger set. If they remain unchanged, examine label quality, missing coverage, model capability and training behavior before purchasing more of the same data. Confirm small gains with repeat runs before making a large commitment.

The decision is not whether the student reproduces every teacher boundary. It is whether it preserves the subjects and source evidence needed by the unchanged SSE pipeline at an acceptable error rate. A later controlled SSE check can establish whether observed extraction differences matter; clustering changes should not be mixed into the data-volume experiment.

No universal accuracy target or single canonical mask set is assumed here. Required data volume only becomes measurable relative to a specified student, data distribution and acceptable quality.

## Connection to the saved token estimate

The current Astra-low subject-plus-mask measurements imply approximately 28,432 teacher tokens per labeled note through the existing runner. At that unchanged average:[^13]

| Notes receiving subject and mask labels | Estimated teacher tokens |
|---:|---:|
| 1,000 | 28 million |
| 5,000 | 142 million |
| 10,000 | 284 million |
| 25,000 | 711 million |
| 50,000 | 1.42 billion |

These are **label-generation tokens, not student-training tokens or dollar prices**. They inherit the previous estimate's limitations: 248 selected notes, the current runner, approximately 9.8 subjects per note, and no allowance for new review work. Node-title generation is excluded. The table illustrates why measuring a small learning curve before generating a large labeled corpus has practical value; it is not a spending authorization.

## Sources

[^1]: Repository design record, [Direct Note-to-Mask Extractor](../docs/recommendation-engine/research/direct-note-to-mask-extractor.md). Used for the proposed transformation, not its older prompt-version references or historical status statements.

[^2]: Chen et al., [PropSegmEnt](https://aclanthology.org/2023.findings-acl.565.pdf), Findings of ACL, 2023. Table 2: train/dev/test quantities; §4 and Tables 3–4: mask generation, agreement and domain transfer.

[^3]: Chen et al., [Sub-Sentence Encoder: Contrastive Learning of Propositional Semantic Representations](https://aclanthology.org/2024.naacl-long.89.pdf), NAACL, 2024. Appendix A.1–A.2 and Table 7: 44,970-sentence supervision set, separate proposition generator and alignment procedure.

[^4]: Hosseini et al., [Scalable and Domain-General Abstractive Proposition Segmentation](https://aclanthology.org/2024.findings-emnlp.517.pdf), Findings of EMNLP, 2024. Tables 1–3; §§4.2–4.3 and 5: human data, synthetic distillation and evaluation-set sizes.

[^5]: [CycleOIE: A Low-Resource Training Framework For Open Information Extraction](https://aclanthology.org/2025.coling-main.227.pdf), COLING, 2025. Tables 2–5 and §§4.3–5.2: model initialization, training counts, controlled subsets and OK-IE's inherited first stage.

[^6]: Bogdanov et al., [NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data](https://aclanthology.org/2024.emnlp-main.660.pdf), EMNLP, 2024. §§3.3–3.4 and 5.3; Figure 10 and Appendix Table 7: first-stage training, subsequent classifier evaluation and data-size curve.

[^7]: Zhou et al., [UniversalNER: Targeted Distillation from Large Language Models for Open Named Entity Recognition](https://proceedings.iclr.cc/paper_files/paper/2024/file/34678d08b36076de986df95c5bbba92f-Paper-Conference.pdf), ICLR, 2024. §4.1 and the [released Pile-NER-type dataset](https://huggingface.co/datasets/Universal-NER/Pile-NER-type): passage and annotation counts.

[^8]: Zaratiana et al., [GLiNER2: An Efficient Multi-Task Information Extraction System with Schema-Driven Interface](https://arxiv.org/html/2507.18546v1), 2025. §§2.3 and 3: model scale, data composition, tasks and evaluation limits.

[^9]: Choi et al., [Decontextualization: Making Sentences Stand-Alone](https://aclanthology.org/2021.tacl-1.27.pdf), TACL, 2021. Table 1; data-selection and human-evaluation sections.

[^10]: Fan and He, [Efficient Data Learning for Open Information Extraction with Pre-trained Language Models](https://aclanthology.org/2023.findings-emnlp.869.pdf), Findings of EMNLP, 2023. Two-stage method and low-resource results. The first-stage training-count clarification is from CycleOIE, source 5.

[^11]: Liu et al., [Human level information extraction from clinical reports with finetuned language models](https://www.nature.com/articles/s41598-025-28767-z), Scientific Reports, 2025. Learning-curve analysis, Figure 5, and discussion of institution-specific extraction and training sensitivity.

[^12]: Dagdelen et al., [Structured information extraction from scientific text with large language models](https://www.nature.com/articles/s41467-024-45563-x), Nature Communications, 2024. Methods and model/data details; [author-hosted paper](https://perssongroup.lbl.gov/papers/dagdelen_structured_information_extraction_2024.pdf).

[^13]: Repository measurement record, [Token estimate for 1 million notes](TOKEN-USAGE-ESTIMATE-1M-NOTES.md). Scaling uses the recorded 7,051,025 extraction tokens across 248 notes, excluding title calls. This is a different quantity from the number of unique annotated training texts.
