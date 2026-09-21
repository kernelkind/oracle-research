# Released broader–narrower embedding models for mask text

## Conclusion

No verified release in this review combines a multi-billion-parameter text encoder, a documented broader–narrower scoring method, and convincing evidence of transfer to short, unrestricted source fragments. Large general-purpose text encoders exist. Released directional encoders also exist. The verified intersection is considerably smaller and more specialized.

The strongest available starting points remain **HierarCaps**, **Relational Sentence Embedding (RSE)**, and **HiT**, for different reasons. HierarCaps has particularly relevant phrase-to-description supervision. RSE has broader sentence-level language supervision and an approximately 355M-parameter RoBERTa-large release. HiT directly learns taxonomy direction but mainly from concept names. These are candidates, not established solutions for constructing a useful topical hierarchy.[^1][^2][^3][^4][^5][^6]

The wider search adds ontology encoders, hierarchy-enhanced BERT/RoBERTa releases, newer hyperbolic vision–language models, larger ordinary embedding models, and training-free geometric methods. None warrants claiming that a substantially larger, ready-to-use hierarchy encoder has been found. Missing checkpoints and undocumented uploads are retained as unresolved findings rather than silently treated as usable models.

**No training, fine-tuning, learned probe, or newly fitted scoring head is proposed.** A research paper whose method requires those steps is not an available solution unless the necessary trained artifact is already released.

## Input and evidence boundary

The input is the exact text inside one mask, with multiple fragments supplied together in source order. It is not the full note, a generated subject, a dictionary definition, or an expanded paraphrase. For example:

> ⟦the stock fan⟧ … ⟦getting too loud⟧

supplies those words. It does not supply the omitted device name or any explanation of the author's intentions. This is an illustrative input boundary, not a model experiment.

An eligible method independently encodes each such text into a reusable representation. Its released scoring operation must provide evidence about direction: whether one meaning is broader than another. A classifier that reads two texts together, a model that generates a parent name, or a method requiring a supplied taxonomy may be useful elsewhere, but is not the embedding component under consideration.

Three distinctions matter:

| Relationship | Example | Relevance |
|---|---|---|
| Taxonomic inclusion | Sparrow → bird | Directly addressed by noun-taxonomy models. |
| Increasing descriptive specificity | Bird → bird building a nest | Addressed more naturally by caption and entailment models. |
| Topical refinement | Coffee → roasting coffee | Relevant to discovery, but roasting is not a kind of coffee. |

These examples do not prescribe a unique hierarchy. They explain why success on one published task cannot simply be relabeled success on the desired task. Two opposing opinions about coffee may belong together topically even when an entailment model treats their propositions as contradictory.

There is also an unavoidable input limitation: identical mask strings receive identical representations from a deterministic encoder. If a distinction exists only in the removed text, a mask-only method cannot recover that distinction from evidence it never receives. This does not establish that the current masks are inadequate; it defines what this model search can address.

## Available candidates

Parameter counts below refer to the **text encoder**, not an accompanying image encoder or the original encoder–decoder model before its decoder was removed.

| Candidate | Text parameters | Text used for its specialized training | Available directional mechanism | Principal limitation |
|---|---:|---|---|---|
| HierarCaps CLIP-B / CLIP-L | Approximately 63M / 123M | Short phrases through detailed visual-scene descriptions | Angle relative to an empty-text reference | Visual-description domain; no validation on disconnected informal masks. |
| RSE RoBERTa-large | Approximately 355M | Entailment, questions, paraphrases, captions, and other sentence relations | Add a learned relation vector before comparing embeddings | Entailment is not automatically topical refinement. |
| HiT MPNet | Approximately 109M | Taxonomy concept names and ontology labels | Hyperbolic distance plus radial ordering | Mainly concept-label supervision; target calibration in reported evaluations. |
| OnT MPNet | Approximately 109M | Biomedical concept names, definitions, and verbalized logical expressions | Hyperbolic distance plus radial ordering | More complex training meanings, but a specialized biomedical domain. |
| HyCoCLIP | Approximately 63M | Image captions and their grounded noun phrases | Directed entailment-cone compatibility | Small text encoder, visual domain, and no broad CLIP initialization. |
| Original CLIP / OpenCLIP / ALIGN with Radial Embeddings | Approximately 63M–353M in the published comparison | Original image–text pretraining; no new training | Published asymmetric angle computation | Promising frozen-model evidence, but neither uniformly strong nor demonstrated on these masks. |

Sources and individual qualifications follow. This table does not rank incomparable benchmark scores.[^1][^2][^3][^4][^5][^6][^7][^25][^26]

### HierarCaps

The already-trained releases start from CLIP's image–text-pretrained text encoders and add hierarchy supervision using approximately 73,000 caption hierarchies. The hierarchy examples range from brief words or phrases to more specific scene descriptions. They are generated and filtered descriptions, not necessarily exact spans copied from a source caption. The original CLIP pretraining used 400M internet image–text pairs.[^1][^8]

Official B/L checkpoint files exist. Encoding a mask does not require an image. The released implementation normalizes text embeddings, encodes the empty string as a reference point, and measures a directional angle. It does not merely substitute another symmetric distance for cosine. The text context limit is 77 tokens.[^2]

The published results need two qualifications. Caption-chain ordering measures how radius orders descriptions already known to be related. It is not a direct test of finding suitable parents among arbitrary unrelated texts. The lexical benchmark adds a visual-language wrapper to individual words, so those results do not establish performance on bare mask text.[^1]

**Assessment:** the closest verified ready-weight candidate by training-text form. Its supervision includes more than dictionary nouns, but its visual domain and small text encoder remain real limits. The claim is plausibility of transfer, not evidence that the transfer succeeds.

### Relational Sentence Embedding

RSE begins with generally pretrained BERT or RoBERTa and then learns several sentence relations. Its datasets include SNLI/MNLI, duplicate questions, paraphrases, captions, question–sentence relations, and sentence identity. The paper reports entailment tail-retrieval MRR of 0.80 and Hits@1 of 0.74 in its native setting. Those are retrieval results with the relation supplied, not accurate-parent percentages.[^3]

The author's `binwang/RSE-RoBERTa-large-10-relations` release is real: its metadata lists the configuration, tokenizer, and approximately 1.42GB weight file. It is roughly a 355M-parameter encoder producing 1,024-dimensional vectors. The released scorer computes:

`cosine(embedding(A) + learned_relation, embedding(B))`

Only the first embedding receives the relation vector, making the result directional. The model is not rerun for every pair. Published training configurations commonly truncate at 32 tokens, which should not be confused with RoBERTa's larger architectural input capacity.[^4]

**Assessment:** the clearest verified option for obtaining a trained directional signal from varied sentence-like language without doing new training. It does not guarantee transitive containment or valid topical parents. No released T5-, Mistral-, or Llama-scale RSE successor was verified.

### HiT and clinical follow-up

HiT initializes from pretrained sentence encoders and learns child–parent relationships from taxonomy names. Parents are encouraged toward the origin while related children remain nearby. Its scoring function combines distance and radial difference. Its native input is a name or label—not a dictionary definition.[^5]

The released MPNet encoder has approximately 109M parameters and 768-dimensional output; smaller MiniLM variants also exist. The public evaluation implementation selects a directional coefficient and decision threshold using target validation data. Therefore its reported transfer scores should not be presented as a universal, calibration-free decision rule.[^6]

The paper's difficult transfer settings report F1 of 0.480 on Schema.org, 0.507 on FoodOn, and 0.566 on DOID for WordNet-trained MiniLM-L12. These are ontology-edge results.[^5]

A clinical follow-up supplies unusually relevant caution about short-span transfer. On CHU-50, its main table reports weighted MRR@15 of 0.627 for the hyperbolic model, 0.671 for semantic embeddings, and 0.681 for their combination. This is phenotype linking, not hierarchy construction, and its extraction step permits reformulating text.[^9]

**Assessment:** a useful direct taxonomy baseline, not evidence that concept-name training covers all informal mask meanings. The concern is the training relationship and input distribution, not simply the small parameter count.

### OnT: a released extension beyond simple taxonomy names

OnT extends the HiT approach to more complex ontology expressions. Training text includes concept names and definitions, together with verbalized conjunctions and relationships. The available domains include GALEN, Gene Ontology, and anatomy. This is more varied than isolated nouns, but still structured biomedical language.[^25]

The author's MPNet checkpoints have 109,486,464 encoder parameters; the GALEN main and role-free branches both contain real weights. MiniLM alternatives are also released. Its concept encoder accepts strings independently, and its evaluator exposes a directional score combining hyperbolic distance with the difference in distance from the origin. An ontology need not accompany every inference string, although the model's trained language and relations come from ontologies.[^25]

Its evaluation selects the radial coefficient on validation data. Current code and older model-card examples also differ in loader names and input limits, so an eventual experiment would need a pinned version rather than assuming a turnkey interface.[^25]

**Assessment:** a genuine additional available model, not a larger one. It expands the kind of hierarchy supervision represented on the shortlist. It does not establish generalization to unrestricted, disconnected source fragments.

### HyCoCLIP and related cone models

HyCoCLIP is another genuine text–text directional release. It learns from 20.5M grounded image–caption pairs, including the relationship between a complete caption and a less specific noun phrase extracted from it. Its released S/B variants both use an approximately 63M-parameter text tower with a 77-token input limit; they do not inherit the broad CLIP-400M checkpoint.[^26]

Its implemented text–text compatibility penalizes a specific caption when it lies outside a broader phrase's entailment cone. This is already a directional computation, not a proposed new scoring head. However, the published evaluations do not validate arbitrary nonvisual mask-to-mask parent selection. Its repository and model-card license labels also disagree; commercial eligibility should not be assumed.[^26]

MERU has actual checkpoints too, but its original hierarchy supervision orders captions relative to images, not arbitrary pairs of texts. Its S/B/L variants all keep the same small text tower; the larger variants enlarge the vision side.[^27]

Hyper3-CLIP's paper checkpoint also learns a text–text ordering involving captions and extracted fragments. It is distinct from the separate `hyper3-clip-v1` release initialized from pretrained CLIP. The latter has gated weights and incompletely documented training; the paper's results must not be assigned to it without evidence.[^28]

**Assessment:** these releases broaden the options beyond HiT, but do not reveal a hidden multi-billion-parameter hierarchy text encoder. Among this family, HierarCaps has the clearer combination of broad pretrained initialization and phrase-level hierarchy adaptation.

### Original pretrained models with a published directional calculation

Radial Embeddings also works on original pretrained CLIP-family weights without any new fitting. The published frozen-model comparison gives the following lexical-entailment correlations:[^7]

| Original pretrained text encoder | Text parameters | HyperLex correlation, all word pairs |
|---|---:|---:|
| CLIP-B | 63M | 0.44 |
| CLIP-L | 123M | 0.42 |
| OpenCLIP-B | 63M | 0.34 |
| OpenCLIP-H | 353M | 0.06 |
| Kakao ALIGN | 109M | 0.35 |

These are correlations, not classification accuracy. Larger text capacity did not consistently improve this particular signal. OpenCLIP-H still scored well on caption-chain ordering, illustrating that ordering already-related descriptions and recognizing lexical entailment are different tests.[^7]

OpenCLIP-B/H use LAION image–text pretraining. The tested Kakao ALIGN is trained on COYO-700M; it should not be confused with Google's original ALIGN training data.[^10]

The directional calculation compares the direction from the empty-text reference to a proposed broader embedding with the direction from that embedding to a proposed narrower one. This is an existing published operation, not an invented use of vector length. The method deliberately does not guarantee a mathematical partial order.[^2]

**Assessment:** an actual no-training route. It does not justify applying the same formula to an arbitrary large text model and assuming equivalent behavior.

## Larger pretrained encoders

The absence of a verified large hierarchy model is not an absence of large reusable text embeddings. The following releases have broadly pretrained backbones and do not require new training for their documented embedding tasks.

| Family | Relevant scale | Documented specialization and scoring | Finding for broader–narrower use |
|---|---:|---|---|
| Sentence-T5-XXL / GTR-T5-XXL | Approximately 4.865B released encoder parameters | Semantic similarity / retrieval; same encoder and symmetric similarity | No released directional order operation established. |
| E5-Mistral-7B-Instruct | 7B | Instructed query–passage and semantic matching | Query/document roles are not evidence of conceptual breadth. |
| GTE-Qwen2-7B-Instruct | 7B | Large-scale text matching with instructed queries | No documented broader–narrower scorer verified. |
| Qwen3-Embedding-8B | 8B | Multilingual, instruction-aware embedding tasks | Strong general embedding evidence, not a trained containment rule. |
| NV-Embed-v2 | Mistral-7B backbone, additional embedding components | Retrieval and non-retrieval instruction training | Native normalized dot product; no demonstrated hierarchy direction. |
| GritLM | Mistral 7B and Mixtral 8×7B variants | Combined embedding and generation training | Generative ability does not itself provide a geometric hierarchy score. |
| LLM2Vec | Released Llama-3-8B adapters | Language-model adaptation and contrastive sentence learning | Produces embeddings, not a verified broader–narrower operator. |
| LGAI-Embedding-Preview / LG-ANNA | Mistral 7B | Includes NLI converted into similarity training | Entailment becomes similarity; direction is not retained by cosine. |
| Nemotron-3-Embed | 1B and 8B | Question–passage retrieval, public and synthetic training pairs | A recent real release, but its documented score is retrieval similarity. |

Sources: Sentence-T5/GTR,[^11] E5/GTE/Qwen,[^12] NV-Embed/GritLM/LLM2Vec,[^13] LG-ANNA,[^14] and Nemotron-3-Embed.[^15]

Sentence-T5/GTR's size requires care: the released encoders have about 4.865B parameters, not the full source T5 model's 11B. Similarly, an EVA-CLIP-18B model contains a roughly 695M-parameter text tower; most of its parameters process images. InternVL does have an approximately 8B text tower, but its released retrieval interface and published results do not establish a text–text hierarchy score.[^11][^16]

For Nemotron-3-Embed-8B, the documented training includes more than 50M public and synthetic question–passage examples. The supplied interface distinguishes query and passage prefixes and compares normalized embeddings. Those facts support retrieval competence, not the proposition that one vector denotes a broader topic.[^15]

There is an important mathematical qualification: **symmetric cosine does not mean the entire text-to-text system is always symmetric**. Encoding A as a query and B as a passage can differ from encoding B as a query and A as a passage. However, that asymmetry reflects trained roles. It is not, without supporting evidence, a broader–narrower relationship.

Nor does a symmetric published score prove that a large model contains no information about breadth. It means a ready-to-use, supported way of obtaining the required direction has not been established. Inventing a new scoring rule or fitting a projection would be a different project.

## Region and hyperbolic methods without a verified usable release

These families were included because their representations genuinely address direction or inclusion. Their exclusion is practical and evidential, not a rejection of the mathematics.

| Method | Native text or task | Release finding | Consequence under no training |
|---|---|---|---|
| Subspace embeddings | SNLI texts encoded as matrices representing subspaces | Text-encoder training code; no trained text checkpoint verified | Cannot use the published text model as-is. |
| GaussCSE | SNLI/MNLI sentences encoded as Gaussian means and variances | Author model repository contains only `.gitattributes` | No usable released weights verified. |
| GumbelCSE | NLI sentences encoded as overlapping boxes | Training code; no author checkpoint verified | Requires a released trained artifact before it qualifies. |
| Prompt2Box | Instructions, constrained refinements, prompt–response pairs, and NLI | Advertised encoder repository unavailable; accessible repository is a website | Paper results are not an available encoder. |
| BoxTaxo / PEB-TAXO | Taxonomy learning, including names and definitions | No ready general mask-text checkpoint verified; PEB-TAXO linked repository empty | Not a usable as-is alternative. |
| ProtoBox | A specified word in a contextual sentence | Different required input and no matching ready release verified | Does not supply the specified standalone mask interface. |
| SpheREx | BERT text representations projected into hyperspheres for taxonomy and similarity tasks | No trained arbitrary-text directional checkpoint verified | Original BERT alone cannot reproduce its learned representation. |
| HypRAG / HyTE | Language pretraining and large-scale retrieval | Training code, but no trained checkpoint verified | No released checkpoint or documented text–text broader–narrower operation verified. |
| HiM / HELM / Hyperbolic BERT | Hyperbolic language-model architectures or task-specific training | No suitable released broad text-to-hierarchy encoder verified | Architecture papers do not establish an available model. |
| TaSe / HiVG | Hierarchical visual-semantic supervision | No trained checkpoint verified at the linked project | Not presently an available option. |

Sources: subspaces,[^17] GaussCSE,[^18] GumbelCSE,[^19] Prompt2Box,[^20] taxonomy/word-box methods,[^21] HypRAG,[^22] hyperbolic language models,[^23] TaSe,[^24] and SpheREx.[^29]

Some papers have impressive numbers on narrower questions. For example, GaussCSE's 97.42% SNLI direction result assumes that one sentence already entails the other; a text-length baseline achieves 92.63% on that test. Its binary entailment task is different. Neither number is the accuracy of selecting appropriate broader topics from arbitrary masks.[^18]

Subspace composition likewise combines independently represented meanings algebraically. It does not establish that concatenating disconnected source fragments gives a faithful representation, or that its span operation corresponds to the desired union of topical children.[^17]

## Other plausible releases and misleading matches

### Hierarchy-enhanced RoBERTa is not necessarily directional

The `jeslev/*-with-hierarchy-properties` releases include real BERT-large and RoBERTa-large weights. Their training uses concept names accompanied by definitions and examples derived from WordNet taxonomic relationships. The paper reports improvements in some hierarchy properties, but uneven transfer to downstream tasks.[^30]

The decisive implementation detail is that the released training uses cosine triplet loss. The paper's reported geometric results use mean-pooled cosine without the exploratory LEAR-like norm terms also present in its repository. Its hypernym-discovery experiments separately fine-tune a classifier. Consequently, these are genuine hierarchy-enhanced embeddings, but not a verified ready directional replacement for HiT or RSE.[^30]

### Asymmetric retrieval is a different learned relationship

Entailment-tuned DPR has an author checkpoint. Its training introduces an entailment stage and then trains for Natural Questions retrieval. Its separate question and passage encoders produce a role-asymmetric dot-product score. The pretrained relationship is question-to-supporting-passage relevance, not topical parenthood.[^31]

Hypencoder also has usable releases. It independently embeds documents and converts a query into a small scoring network. This is a genuine learned alternative to cosine, but it is trained for passage relevance with BERT-base, not for general broader–narrower relationships.[^32]

ColBERT's independently generated token vectors and directed query-to-document matching are similarly relevant adjacent technology. Its native evidence is passage retrieval. Token coverage must not be silently reinterpreted as conceptual inclusion.[^33]

### Other entailment-named embeddings

FRIDA is a released approximately 0.8B T5-derived encoder with an entailment task prefix. Both strings receive the same prefix and are compared by normalized dot product, so that mode is symmetric. Its card also leaves English quality unresolved. AnglE/UAE's angle-based training likewise does not make its documented cosine comparison a broader–narrower score.[^34]

Two uploads deserve explicit unresolved status:

- `vcmt794/qwen3-embedding-4b-legal-entailment` contains an actual approximately 47MB LoRA adapter for Qwen3-Embedding-4B. Its configuration declares feature extraction, but the model card is an unfilled template. The training data, objective, scoring rule, provenance, and evaluation are not established. Its name is not enough to infer directionality.[^35]
- `AtPeak/dualcse` contains an actual BERT-base checkpoint. The author's DualCSE method can score literal and implied meanings asymmetrically, but this upload's relationship to the reported models is unverified. It is not a newly discovered large encoder.[^36]

Large `hierarchy_*` Llama/Mistral uploads were also inspected. For example, the hbakrim models expose causal-language-model configurations and generation artifacts, not a documented independent embedding scorer. The namannn hyperbolic-pruned Llama models use hyperbolic comparisons to compress model layers; this does not give their output text embeddings semantic containment.[^37]

Other small releases do not close the gap: the MIMIC hierarchical EmbeddingGemma card documents normalized similarity, while CoRover's asymmetric Finsler model describes procedural next-step order. Neither documents the required topical broader–narrower relationship.[^46]

### Vision-language releases with no demonstrated text-pair direction

HyFL-CLIP has genuine released weights and a longer text context. Its entailment constraint links a text's aggregated token representation to its own global representation; its reported text-pair comparison uses a symmetric Lorentz inner product. That is different from training one independently supplied description to be broader than another.[^38]

The released taxonomic-VLM projector is an image-to-language component used with an image and a yes/no question. It does not independently encode two masks. Training-free classification methods such as SHiNe consume a supplied hierarchy rather than discover arbitrary textual inclusion.[^39]

## Training-free geometry research

The absence of specialized weights does not automatically exclude a method: a published calculation on frozen released weights can qualify. Radial Embeddings is the strongest verified example here. Several other promising-sounding papers do not provide the required interface.

| Work | What it actually establishes or requires | Why it does not supply this component |
|---|---|---|
| Sen2Pro | Represents embedding variability using repeated dropout and augmented inputs | Its published comparison is symmetric; uncertainty is not demonstrated topical breadth. |
| The Lattice Representation Hypothesis | Fits attribute directions from labeled object examples; uses synonym-derived object representations | Requires new fitted directions and extra concept data. |
| Linear Representations of Hierarchical Concepts in Language Models | Estimates hierarchy-level transformations and parent prototypes, including on 8B/14B models | Requires hierarchy examples, fitted maps, and known candidate concepts. |
| Geometry of Semantics in Next-Token Prediction | Finds structure in a frozen model's vocabulary matrix | Constructs token groups, not a directional comparison between arbitrary complete mask strings. |
| Unpacking the Suitcase of Semantic Similarity | Trains projections from existing embeddings, including large encoders | The fitted projections are not the original pretrained model; no usable released projection was verified. |
| Beyond Surface Similarity / OrthoGeoLoRA | Adapts encoders and geometric metrics using structured concept relationships | No suitable already-trained checkpoint verified. |
| The Geometry of Meaning | Uses norm comparisons; its three-class extension uses absolute norm difference | That extension removes direction, and its results do not establish the required topical relation. |
| Set-Theoretic Compositionality in Embeddings | Tests embeddings against supplied sentences expressing overlap, difference, and union | A benchmark of operations is not a released broader–narrower encoder. |

Sources: Sen2Pro,[^40] lattice and hierarchical linear representations,[^41] vocabulary geometry,[^42] semantic-similarity projections,[^43] adapted concept retrieval,[^44] and norm/compositionality studies.[^47]

The Lattice paper and the linear-hierarchy paper are scientifically relevant. Their findings support studying learned geometry. They do **not** establish that downloading the original large language model provides their reported semantic inclusion behavior without the additional learned components.[^41]

The frozen-vocabulary work is a different limitation: it does not require fine-tuning for that analysis, but its objects are groups of tokens identified through directions in the output vocabulary matrix. It should not be dismissed as a training method, nor promoted as an already demonstrated whole-text hierarchy encoder.[^42]

## Coverage and practical conclusion

The directly plausible space covered here includes independently encoded taxonomy relations; sentence entailment; order/radial encodings; hyperbolic cones; Gaussian, box, sphere, and subspace representations; ontology-language encoders; frozen large-model geometric analyses; asymmetric retrieval; large instruction-conditioned embeddings; and visual-language hierarchy models. Citation and release checks also covered fixed-vocabulary word/knowledge-graph embeddings and hierarchy-conditioned classification. Those latter methods need vocabulary, ontology, or label inputs different from arbitrary mask text.[^45]

**The useful additions are OnT and HyCoCLIP, not a verified jump to a large general hierarchy encoder.** The hierarchy-properties RoBERTa release is real but lacks the needed established directional scorer. The Qwen3-4B legal adapter is a genuine large-model lead whose essential documentation is missing. These are materially different findings and should remain separate.

For this input and no-training constraint, the plausibility order remains:

1. **HierarCaps**, for short phrases through richer descriptions and an existing directional operation.
2. **RSE RoBERTa-large**, for broader sentence-language supervision and a larger verified text encoder.
3. **HiT**, for direct taxonomy direction, with **OnT** as a related but biomedical-specialized alternative.
4. **HyCoCLIP**, for source-phrase/caption direction, with a smaller and more restricted pretraining base.

This is a ranking by input/training fit, not measured performance on these masks. The original frozen CLIP plus Radial Embeddings provides a useful no-adaptation comparison, not evidence that increasing model size solves the problem.

The computing pattern of the qualified models is straightforward: encode each mask once, retain its representation, then calculate pair scores without asking a generative model to judge every pair. Their native scores are evidence that could inform a hierarchy-construction method; none chooses all categories, validates every parent, or resolves a complete collection's organization by itself.

There is no evidence-backed reason to call any candidate a dependable replacement yet. Equally, the absence of a larger verified release is not evidence that the smaller candidates fail. The search establishes what is actually available and what each release learned; effectiveness on these masks remains unmeasured.

## Research limits

The literature and release status here were checked through September 12, 2026. A negative release finding means that usable weights and the required scoring behavior were not verified in the public sources—not that private weights cannot exist or a release cannot appear later.

The directly relevant families and their plausible release leads have been covered; a literal guarantee that every obscure or unpublished model has been found would not be defensible. In particular, missing author checkpoints, incomplete public model cards, and inaccessible manuscripts bound the conclusion. The SpheREx and semantic-similarity projection assessments rely partly on publicly indexed primary-manuscript passages where complete pages were inaccessible; neither is presented as a fully audited usable release.

The August 2026 MeSH-HyRerank workshop listing is another unresolved lead: an accessible full paper and usable checkpoint were not verified. It is not counted as a usable model, nor ruled out on an assumed training objective.[^48]

This is a release-focused literature assessment, not an experimental comparison. No models were run, no weight files were downloaded, and no gated access conditions were accepted. None of the native benchmarks reviewed establishes a browsable topical hierarchy from these exact mask inputs.

## Sources

[^1]: Alper and Averbuch-Elor, *Emergent Visual-Semantic Hierarchies in Image–Text Representations*, ECCV 2024. [Paper](https://arxiv.org/html/2407.08521v2), especially dataset, evaluation, and supplementary input-format sections.
[^2]: HierarCaps author releases: [CLIP-B](https://huggingface.co/malper/hierarcaps-clip-b), [CLIP-L](https://huggingface.co/malper/hierarcaps-clip-l), [training and angle implementation](https://github.com/TAU-VAILab/hierarcaps/blob/main/code/train.py), [inference](https://github.com/TAU-VAILab/hierarcaps/blob/main/code/evaluation/hierarchical_retrieval.py).
[^3]: Wang and Li, *Relational Sentence Embedding for Flexible Semantic Matching*, RepL4NLP 2023. [Paper](https://aclanthology.org/2023.repl4nlp-1.20.pdf).
[^4]: RSE author [repository](https://github.com/BinWang28/RSE), [RoBERTa-large checkpoint](https://huggingface.co/binwang/RSE-RoBERTa-large-10-relations), [weight metadata](https://huggingface.co/api/models/binwang/RSE-RoBERTa-large-10-relations?blobs=true), [scoring implementation](https://github.com/BinWang28/RSE/blob/main/rse_src/inference.py).
[^5]: He et al., *Language Models as Hierarchy Encoders*, NeurIPS 2024. [Paper, version 3](https://arxiv.org/html/2401.11374v3).
[^6]: HiT [MPNet release](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun), [configuration](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun/blob/main/config.json), [evaluation implementation](https://github.com/KRR-Oxford/HierarchyTransformers/blob/main/scripts/evaluation/hit/eval_hit.py).
[^7]: Alper and Averbuch-Elor, ECCV 2024, [Table 1](https://arxiv.org/html/2407.08521v2#S6.T1) and [supplement, model counts and evaluation details](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/06864-supp.pdf). Frozen-model and fine-tuned results must be kept separate.
[^8]: Radford et al., *Learning Transferable Visual Models From Natural Language Supervision*, ICML 2021. [Paper](https://proceedings.mlr.press/v139/radford21a.html).
[^9]: Labbé et al., *Hierarchy-Aware Hyperbolic and Semantic Reranking for Ontology-Based Phenotype Linking*, BioNLP 2026. [Paper, main Table 2](https://aclanthology.org/2026.bionlp-1.5.pdf), [released model](https://huggingface.co/labbeth/HiT-all-MiniLM-L12-v2-hpo), [span prompt](https://github.com/labbeth/HyperRAG/blob/main/prompts/span_detection.txt).
[^10]: Original-model training cards: [OpenCLIP-B](https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K), [OpenCLIP-H](https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K), [Kakao ALIGN](https://huggingface.co/kakaobrain/align-base).
[^11]: Ni et al., *Sentence-T5*, Findings of ACL 2022. [Paper](https://aclanthology.org/2022.findings-acl.146/); [Sentence-T5-XXL](https://huggingface.co/sentence-transformers/sentence-t5-xxl), [exact artifact metadata](https://huggingface.co/api/models/sentence-transformers/sentence-t5-xxl?blobs=true); [GTR-T5-XXL](https://huggingface.co/sentence-transformers/gtr-t5-xxl), [exact artifact metadata](https://huggingface.co/api/models/sentence-transformers/gtr-t5-xxl?blobs=true).
[^12]: Author model cards and documented scoring: [E5-Mistral-7B](https://huggingface.co/intfloat/e5-mistral-7b-instruct), [GTE-Qwen2-7B](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct), [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B).
[^13]: Author releases: [NV-Embed-v2](https://huggingface.co/nvidia/NV-Embed-v2); [GritLM-7B](https://huggingface.co/GritLM/GritLM-7B), [GritLM repository](https://github.com/ContextualAI/gritlm); [LLM2Vec Llama-3-8B supervised adapter](https://huggingface.co/McGill-NLP/LLM2Vec-Meta-Llama-3-8B-Instruct-mntp-supervised).
[^14]: *LG-ANNA*, 2025. [Primary methods](https://arxiv.org/html/2506.07438v1), [LGAI-Embedding-Preview release](https://huggingface.co/annamodels/LGAI-Embedding-Preview).
[^15]: NVIDIA, *Nemotron-3-Embed*, July 2026 release. [8B model card and training data](https://huggingface.co/nvidia/Nemotron-3-Embed-8B-BF16), [release collection](https://huggingface.co/collections/nvidia/nemotron-3-embed).
[^16]: *EVA-CLIP-18B*, 2024. [Architecture tables](https://arxiv.org/html/2402.04252v1); OpenGVLab [InternVL-14B-224px release and input interface](https://huggingface.co/OpenGVLab/InternVL-14B-224px).
[^17]: Moreira et al., *Native Hierarchical and Compositional Representations with Subspace Embeddings*, KDD 2026. [Paper, version 2](https://arxiv.org/html/2508.16687v2), [author implementation](https://github.com/gabmoreira/subembed).
[^18]: Yoda et al., *Sentence Representations via Gaussian Embedding*, EACL 2024. [Paper](https://aclanthology.org/2024.eacl-short.36.pdf), [repository](https://github.com/yoda122/GaussCSE), [author model metadata](https://huggingface.co/api/models/yoda122/gausscse).
[^19]: Oda et al., *Representing Sentence Interpretations with Overlapping Box Embeddings*, IEEE Access 2026. [Publication](https://doi.org/10.1109/ACCESS.2026.3691815), [accessible primary manuscript](https://openreview.net/pdf/3df07ed17593840877b30d2a364763122adfc66e.pdf), [GumbelCSE implementation](https://github.com/iehok/GumbelCSE).
[^20]: *Prompt2Box*, [version 3, September 2026](https://arxiv.org/html/2603.21438v3); [advertised encoder repository](https://github.com/zawedcvg/box_embeddings), unavailable when checked; [accessible website repository](https://github.com/zawedcvg/P2B).
[^21]: [BoxTaxo paper](https://www.ijcai.org/proceedings/2024/0934.pdf), [code](https://github.com/songjiang0909/BoxTaxo); [PEB-TAXO paper](https://link.springer.com/article/10.1007/s11063-024-11575-3), [linked repository](https://github.com/lizaozhou/PEB-TAXO); [ProtoBox paper](https://aclanthology.org/2024.repl4nlp-1.1.pdf), [code](https://github.com/iehok/ProtoBox).
[^22]: *HypRAG*, 2026. [Paper](https://arxiv.org/html/2602.07739v2), [author training repository](https://github.com/Graph-and-Geometric-Learning/HypRAG).
[^23]: [HiM paper](https://arxiv.org/html/2505.18973v3), [initialization code](https://github.com/BerryByte/HiM/blob/main/src/HIM_l.py); [HELM paper](https://arxiv.org/html/2505.24722v2), [repository](https://github.com/Graph-and-Geometric-Learning/helm); [Hyperbolic BERT code](https://github.com/thunlp/hyperbolic_llm). Hyperbolic BERT's inaccessible full text limits its assessment to the inspected release.
[^24]: *TaSe / HiVG*, [August 2026 version](https://arxiv.org/html/2509.24192v3), [linked repository](https://github.com/ssojungan/tase).
[^25]: Yang et al., *Language Models as Ontology Encoders*, 2025. [Paper](https://arxiv.org/html/2507.14334v1), [author release list](https://github.com/HuiYang1997/OnT#available-pre-trained-models), [GALEN MPNet checkpoint](https://huggingface.co/Hui97/OnT-MPNet-galen), [actual file metadata](https://huggingface.co/api/models/Hui97/OnT-MPNet-galen?blobs=true), [directional evaluator](https://github.com/HuiYang1997/OnT/blob/main/ont/evaluation/evaluator.py).
[^26]: Pal et al., *Compositional Entailment Learning for Hyperbolic Vision-Language Models*. [Paper](https://arxiv.org/html/2410.06912v2), [HyCoCLIP model zoo](https://github.com/PalAvik/hycoclip/blob/main/model-zoo.md), [released weights and model card](https://huggingface.co/avik-pal/hycoclip), [native text–text cone computation](https://github.com/PalAvik/hycoclip/blob/main/hycoclip/models.py#L449).
[^27]: Desai et al., *Hyperbolic Image-Text Representations*. [MERU paper](https://arxiv.org/html/2304.09172v1), [author releases](https://github.com/facebookresearch/meru).
[^28]: *Hyper3-CLIP*, August 2026. [Paper](https://arxiv.org/html/2608.29313v1), [paper checkpoint](https://huggingface.co/hyper3labs/hyper3-clip), [separate v1 checkpoint](https://huggingface.co/hyper3labs/hyper3-clip-v1), [author repository](https://github.com/Hyper3Labs/hyper3-clip).
[^29]: *SpheREx*. [Primary OpenReview manuscript](https://openreview.net/pdf?id=lcrFXKWzF7), especially release note and Appendix D. Acceptance and pretrained-checkpoint availability were not verified.
[^30]: Lovón-Melgarejo et al., *Probing Pretrained Language Models with Hierarchy Properties*, ECIR 2024. [Paper](https://arxiv.org/html/2312.09670v1), [released RoBERTa-large configuration](https://huggingface.co/jeslev/roberta-large-with-hierarchy-properties/blob/main/config.json), [actual training loss](https://github.com/jeslev/hierarchy_properties_plms/blob/main/train/model.py), [evaluation methods](https://github.com/jeslev/hierarchy_properties_plms/blob/main/evaluation/evaluate_properties.py).
[^31]: *Entailment Tuning*, EMNLP 2024. [Paper](https://aclanthology.org/2024.emnlp-main.636/), [author repository](https://github.com/stellaludai/EntailmentTuning), [released DPR model](https://huggingface.co/stellaludai/dpr_single_nq_base_entailtuned), [bi-encoder scorer](https://github.com/stellaludai/EntailmentTuning/blob/main/dpr/models/biencoder.py).
[^32]: Hypencoder [author model card](https://huggingface.co/jfkback/hypencoder.4_layer), [implementation and paper link](https://github.com/jfkback/hypencoder-paper).
[^33]: Khattab and Zaharia, *ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT*, SIGIR 2020. [Paper](https://arxiv.org/abs/2004.12832), [author implementation](https://github.com/stanford-futuredata/ColBERT).
[^34]: [FRIDA author card and entailment example](https://huggingface.co/ai-forever/FRIDA); [UAE/AnglE documented embedding use](https://huggingface.co/WhereIsAI/UAE-Large-V1).
[^35]: [Qwen3-4B legal-entailment model card](https://huggingface.co/vcmt794/qwen3-embedding-4b-legal-entailment), [adapter configuration](https://huggingface.co/vcmt794/qwen3-embedding-4b-legal-entailment/blob/main/adapter_config.json), [actual file metadata](https://huggingface.co/api/models/vcmt794/qwen3-embedding-4b-legal-entailment?blobs=true).
[^36]: *DualCSE*, Findings of EACL 2026. [Paper](https://aclanthology.org/2026.findings-eacl.74/), [author model code](https://github.com/iehok/DualCSE/blob/main/src/models.py); third-party [checkpoint metadata](https://huggingface.co/api/models/AtPeak/dualcse?blobs=true), [saved configuration](https://huggingface.co/AtPeak/dualcse/blob/main/args.yaml).
[^37]: [hbakrim Mistral model metadata](https://huggingface.co/api/models/hbakrim/hierarchy_by_level_mistral_7b), [configuration](https://huggingface.co/hbakrim/hierarchy_by_level_mistral_7b/blob/main/config.json); [namannn hyperbolic-pruned model card](https://huggingface.co/namannn/llama2-7b-hyperbolic-cluster-pruned/blob/main/README.md).
[^38]: *HyFL-CLIP*, July 2026. [Paper](https://arxiv.org/html/2607.00428v1), [author weights](https://huggingface.co/jeeit17/HyFL-CLIP).
[^39]: Taxonomic VLM [demo documentation](https://huggingface.co/sally-xu-42/taxonomic-vlms-projector/blob/main/demo.md), [actual inference](https://huggingface.co/sally-xu-42/taxonomic-vlms-projector/blob/main/demo_inference.py); *SHiNe*, [paper](https://arxiv.org/abs/2405.10053).
[^40]: *Sen2Pro*, RepL4NLP 2023. [Paper, §4.1](https://aclanthology.org/2023.repl4nlp-1.26.pdf).
[^41]: *The Lattice Representation Hypothesis*, ICLR 2026. [Primary paper, fitted directions in §4.1](https://arxiv.org/html/2603.01227v1); Sakata et al., *Linear Representations of Hierarchical Concepts in Language Models*, April 2026. [Paper](https://arxiv.org/html/2604.07886v3), [author repository](https://github.com/masaki-sakata/linear-hierarchical-encoding).
[^42]: Zhao and Thrampoulidis, *Geometry of Semantics in Next-Token Prediction: How Optimization Implicitly Organizes Linguistic Representations*, 2025. [Version 2](https://arxiv.org/html/2505.08348v2), [title and version history](https://arxiv.org/abs/2505.08348).
[^43]: *Unpacking the Suitcase of Semantic Similarity*. [Primary OpenReview manuscript](https://openreview.net/pdf?id=OCVIGEitkg). Publicly indexed abstract and methods identify newly trained projections; no released projection was verified. Publication status is not assumed.
[^44]: *Beyond Surface Similarity: A Riemannian Hierarchical Approach*, CIKM 2025. [University publication record](https://openresearch.surrey.ac.uk/esploro/outputs/conferenceProceeding/Beyond-Surface-Similarity-A-Riemannian-Hierarchical/991050566402346); *OrthoGeoLoRA*, [January 2026 paper](https://arxiv.org/html/2601.09185v1).
[^45]: Representative boundary checks: [Order Embeddings](https://arxiv.org/abs/1511.06361), [hyperbolic entailment cones](https://proceedings.mlr.press/v80/ganea18a.html), [ConE](https://snap.stanford.edu/cone/), [HierPrompt](https://aclanthology.org/2025.findings-emnlp.207/). These do not establish a released large arbitrary-mask encoder with the requested interface.
[^46]: [MIMIC hierarchical EmbeddingGemma card](https://huggingface.co/gaspard-loeillot/embeddinggemma-mimic-hierarchical); [CoRover asymmetric Finsler model card](https://huggingface.co/CoRover/Hybrid-Finsler-Assymetric-Embeddings).
[^47]: *The Geometry of Meaning*, 2025. [Paper](https://peerj.com/articles/cs-2957/), [released implementation](https://github.com/suhaibani/geometry/blob/main/geometry.py); *Set-Theoretic Compositionality in Embeddings*, [paper](https://arxiv.org/abs/2502.20975).
[^48]: GALOP workshop at KDD 2026, [program including MeSH-HyRerank](https://hyperboliclearning.github.io/events/kdd2026workshop). Listing verified; model availability and full methods unresolved.
