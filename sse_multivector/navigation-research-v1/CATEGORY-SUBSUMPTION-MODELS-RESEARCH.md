# Released models for category subsumption

**Evidence:** Unlinked data file references below identify local originals outside this checkout. See [publication availability](../../docs/experiments/README.md#reading-the-research-records).

## Conclusion

Released models exist that can read two texts together and predict a directional relationship. The choices are materially broader than independently embedded descriptions. However, no verified release combines convincing evidence for general, multiword topical-category subsumption with a ready, reliable accept/reject decision.

The most defensible next specialist to test is **Google’s TRUE NLI-mixture T5-XXL**. This is a recommendation based on training coverage, binary entailment output, usable weights, and clear licensing—not measured superiority on this project. **EV-XXL** is a credible alternative with published gains over its own Flan-T5 base, but release and task-fit qualifications. **TaSeR** is the closest native category-relation classifier, but its documented transfer weaknesses prevent recommending it as the presumed solution.

TaxoLLaMA is a released larger taxonomy specialist. Its native strength is generating or ranking parents. Turning its likelihoods into dependable yes/no decisions remains an additional unverified step.

The practical conclusion is a short, discriminating specialist comparison, not another open-ended series of model substitutions. A prompted frontier model remains a reasonable fallback. Neither its success nor the failure of all specialists has been established.

## The required decision

The input is two existing category titles or descriptions, A and B. The required decision is whether **every instance belonging to category B also belongs to category A**. A positive result supplies the edge A → B. The reverse direction must be considered separately; two positive directions suggest equivalence and require checking before consolidation.

For example, “Open-source operating systems” is narrower than “Operating systems.” “Open-source software” and “Operating systems” overlap, but neither contains the other. A system must distinguish both situations even though all three descriptions are related.

These are categories of notes. This matters when transferring ontology models: a category about coffee brewing can refine a category about coffee, although brewing is not a kind of beverage. The model must interpret the descriptions as the intended content categories, not silently substitute a different relationship between their constituent objects.

This report accepts joint-input neural classifiers, specialized generative models, and directional embeddings. It requires already-trained, available weights; training a new classifier, projection, or adapter is outside the proposed work. Generating missing categories, changing HDBSCAN, and constructing the final graph are separate questions.

## Ranked shortlist

The order below is a judgment of practical plausibility for the present task, not a leaderboard. Published scores use different datasets and cannot supply an honest head-to-head ranking.

| Priority | Model | What it computes | Main qualification |
| --- | --- | --- | --- |
| 1 | TRUE NLI-mixture T5-XXL, approximately 11B | Binary entailment from two texts read jointly | Broad sentence training; category transfer untested |
| 2 | EV-XXL, approximately 11B | Yes/no entailment score from an instructed text pair | Promising specialization; ranking-based training and incomplete release documentation |
| 3 | TaSeR, approximately 67M | Seven-way relationship classification of category labels | Closest native interface; severe variation across domains |
| 4 | TaxoLLaMA / TaxoLLaMA3.1, 7B / 8B | Conditional likelihood of a proposed parent | WordNet specialization; likelihood is not a calibrated subsumption decision |
| Reserve | GLiClass instruct-large, approximately 439M | Task-instructed joint classification | Can express the desired task, but no category-containment evidence |
| Reserve | Broad ModernBERT / DeBERTa NLI classifiers | Entailment, neutral, contradiction, or binary entailment | Cheap, plausible baselines; earlier small probes already warn against assuming transfer |

### TRUE NLI-mixture T5-XXL

This is a general pretrained T5 model subsequently trained for binary entailment. Its specialization mixes SNLI, MNLI, FEVER, SciTail, PAWS, and VitaminC: caption-derived sentence pairs, varied prose, factual claims, science, and difficult paraphrase distinctions. It is not restricted to dictionary definitions or visual-caption supervision alone.[^1]

The native input is “premise: … hypothesis: …”; its output labels are 1 for entailment and 0 for non-entailment. The approximately 11B model has released weights and an Apache-2.0 license. It is **not** the separately released TrueTeacher model.[^1]

For A subsuming B, the relevant inference runs from a faithful statement of B’s category membership to A’s—not A to B. Converting titles to that input is an adaptation whose fidelity must be inspected. There is no published category-subsumption result for this checkpoint, and the original TRUE paper used a differently trained model; its results must not be assigned automatically to this release.[^1][^2]

**Assessment:** the best clean large-model trial, because the available model already learned positive and negative entailment decisions over varied language. This does not mean that eleven billion parameters guarantee the necessary knowledge or scope sensitivity.

There is relevant counterevidence to any size-based optimism: the MiniCheck paper reports 61.0 balanced accuracy for T5-NLI-Mixed against 74.7 for MiniCheck-Flan-T5-Large on its factual-support aggregate. That is a different task, not a category test, but shows that a larger NLI model need not transfer better.[^16]

### EV-XXL

EV-XXL starts from instruction-trained Flan-T5-XXL, then specializes on adversarial NLI, reading-comprehension questions, and commonsense explanations: ANLI, RACE, ECQA, and StrategyQA. It scores whether a premise supports a hypothesis. Its final training objective ranks supported hypotheses above alternatives, using incorrect answer choices and generated negative examples, rather than learning only a hard binary boundary.[^3]

The paper reports 0.78 average macro-F1 across ten entailment-verification datasets, against 0.71 for the base Flan-T5 model and 0.79 for its contemporary GPT-4 comparator. These are not category-hierarchy results or comparisons with current frontier models. The reported unseen-dataset average is 0.82, where “unseen” concerns this specialization, not necessarily every earlier training stage.[^3]

Actual 11.135B weights exist. The checkpoint lacks a declared license and tokenizer files; the supplied example uses the base tokenizer. Its card also prints the entailment direction backwards and displays a suspicious negative result for a valid coal/fossil-fuel example. That could be a documentation error; it is not an observed inference failure here.[^4]

**Assessment:** a substantial candidate, but TRUE is the cleaner first choice. EV’s preference for softer support judgments deserves particular scrutiny when overlapping categories must be rejected.

### TaSeR

TaSeR jointly reads two class labels and classifies equivalence, subclass, superclass, part-of, has-part, relatedness, or unrelatedness. The released DistilBERT variant specializes on WordNet, DBpedia, and Schema.org, with WordNet dominating the examples. It does not require an ontology at inference time.[^5]

Its unchanged-model micro-F1 varies sharply: 0.929 for the text benchmark, but 0.154 for furniture and 0.268 for clothing. The refinement benchmarks contain supplied correspondences rather than arbitrary all-pairs negatives; they do not establish dependable rejection of unrelated pairs. Model selection also used aggregate benchmark performance.[^5]

The approximately 67M classifier has verified weights and explicit output labels, under CC-BY-SA-4.0. No larger released TaSeR was verified; evaluated BERT/RoBERTa variants do not establish downloadable checkpoints.[^6]

**Assessment:** worth retaining as the most directly specialized small baseline, not as the strongest general solution. Its training and transfer evidence repeat a concern already encountered with dictionary-based specialists.

### TaxoLLaMA and TaxoLLaMA3.1

TaxoLLaMA adapts a broadly pretrained Llama model to WordNet hypernym generation. The original 7B release is an adapter requiring its Llama-2 base. The authors provide a scorer that measures the conditional perplexity of a proposed parent given the child; the prompt tokens are excluded from that loss. Lower perplexity favors that parent.[^7][^8]

The 2026 extension includes Llama-3.1-8B-Instruct variants trained either on hypernym prediction or several taxonomy tasks. It also constructs graphs by scoring all possible edges and choosing thresholds. Those thresholds are optimized on benchmark results; they are not a demonstrated portable decision boundary. Weak transfer to computer-science and psychology taxonomies remains relevant.[^9]

A real 8.03B full checkpoint is available. Its model card is an unfilled template; the exact correspondence to the paper’s “hyp” versus “multi” variant and checkpoint-specific license remain unresolved. Independent published work used this exact release for hypernym generation, confirming genuine use but not reliable category-pair judgments.[^10]

**Assessment:** a credible specialist, but below the binary entailment candidates for this task. Frequent, short, synonymous, or overly broad parent strings can receive favorable likelihood without establishing strict subsumption. Generating a good parent and rejecting every wrong proposed parent are different abilities.

### GLiClass instruct and broad encoder NLI

GLiClass instruct-large uses a DeBERTa-v3-large backbone and reads task instructions, text, and labels jointly. The released configuration and card support label descriptions, examples, and a native NLI mode with one hypothesis at a time. Disclosed training sources include logic and commonsense tasks. Its approximately 439M weights are Apache-2.0.[^11]

Its advertised hierarchical labels are supplied label organization, not discovered subsumption. Classification benchmark results therefore cannot establish category placement. Its attraction is that the exact desired relationship can be stated to a small trained model without modifying weights.

The broad encoder alternatives include tasksource/ModernBERT-large-nli, tasksource-trained DeBERTa, Moritz Laurer’s multi-NLI DeBERTa, and his binary zeroshot-v2.0 classifiers. These use substantially different training mixtures. Some include adversarial inference, formal reasoning, or many synthetic classification tasks; they should not all be treated as the same MNLI-only model.[^12]

**Assessment:** plausible efficient baselines, but not evidence that the previous DeBERTa problems are fixed. A current model name, broad multitask table, or higher unrelated benchmark average is insufficient to justify that conclusion.

## Other released specialists

### Entailer and Vera

Entailer-11B is a T5-based model trained around science explanations and EntailmentBank. It can generate supporting premises, assess factuality, and judge whether premises imply a hypothesis. For this task, the relevant operation is its “implied” verifier, not its independent truth judgment. The weights are Apache-2.0. It is more compelling when descriptions supply explicit reasoning premises than when it must infer broad topical relationships from short titles alone.[^13]

Vera is approximately 5B parameters: the encoder of T5-v1.1-XXL plus a trained scalar scoring head, not the full 11B encoder-decoder. It was trained on roughly seven million examples from 19 QA datasets, ATOMIC2020, and GenericsKB. It scores the plausibility of a single commonsense statement and is MIT-licensed. The paper distinguishes that scope from encyclopedic facts and contextual NLI.[^14]

Using Vera to judge a statement that B belongs within A is a plausible adaptation, not a validated author-provided category interface. Everyday generalizations may support its task while being insufficient for universal category containment. Consequently it is a reserve route, not an obvious upgrade over joint entailment.

### Document-support and general judging models

These releases show that the choice is not limited to tiny encoders. Their specialization, however, answers whether a claim is supported by a document or whether an answer satisfies a rubric. That is adjacent to, not identical with, category subsumption.

| Family | Backbone / size and specialization | Release and reason for lower priority |
| --- | --- | --- |
| AlignScore | RoBERTa, 125M/355M; 4.7M examples across seven alignment-related task families | MIT, actual weights; directional context/claim alignment, not category validation[^15] |
| MiniCheck | Flan-T5-large, approximately 770M; adversarial NLI plus structured synthetic support checking | MIT; document-grounding evaluation rather than category containment[^16] |
| Bespoke-MiniCheck | InternLM2.5-chat, approximately 7.74B; synthetic grounding specialization | CC-BY-NC; Llama generated training data but is not this model’s backbone[^17] |
| TrueTeacher | T5, approximately 11B; synthetic summary consistency plus ANLI | CC-BY-NC; distinct from the broader TRUE NLI-mixture checkpoint[^18] |
| FactCG | DeBERTa-large; synthetic multi-hop factuality examples | MIT; published threshold tuning and grounding task require careful interpretation[^19] |
| HHEM-2.1-Open | Flan-T5-base-derived support classifier | Apache-2.0; the newer commercial HHEM-2.3 is not this open checkpoint[^20] |
| Patronus Lynx | Llama-derived 8B/70B; question/answer faithfulness to supplied documents | CC-BY-NC; large but task-mismatched[^21] |
| GLIDER | Phi-3.5-derived approximately 4B; rubric-conditioned evaluation | CC-BY-NC; can state the desired criterion, but no subsumption validation[^21] |

These should not become an automatic queue of eight more experiments. Their inclusion documents available alternatives and explains why the more direct shortlist comes first.

## Ontology and taxonomy methods that are not ready general classifiers

**BERTSubs** implements the right binary pair task, but its normal workflow builds examples from supplied ontologies and fine-tunes BERT. Disabling fine-tuning only reuses an already-trained checkpoint; it does not give untouched BERT a learned subsumption head. No reusable, general trained checkpoint was verified. **BERTMap** primarily learns synonym/equivalence matching, not the required directional decision. **OntoLAMA** supplies valuable subsumption benchmarks and analysis, not a verified ready universal classifier.[^22]

**WikiNLI** is particularly relevant because it pretrains BERT/RoBERTa on Wikipedia category pairs with parent, child, and neutral labels. However, Wikipedia parent links are not uniformly strict subsumption, and construction filters exclude many composed category names. The author repository links a pretrained RoBERTa-large model but instructs removing its top classifier before downstream use. The downloadable archive’s retained head could not be verified. Reported downstream improvements involve further task training; they do not establish a ready English category-pair classifier.[^23]

**TaxoInstruct** uses Llama-3-8B and taxonomy-oriented instructions, but the final paper begins with a disease taxonomy and then adapts models to target tasks. An author-linked model archive exists; its exact contents and licensing were not verified. Its parent-selection results cannot be treated as untouched general subsumption performance.[^24]

**OntoTune** has actual Llama-3-8B weights specialized using SNOMED CT. Its reported hypernym-discovery evaluations additionally instruction-tune on evaluation-task training sets. Those scores do not describe the unchanged released medical model.[^25]

**BSC’s biomedical semantic-relation models** are genuine four-label BROAD/EXACT/NARROW/NO_RELATION releases, including a complete SetFit classifier. They are Spanish biomedical models, not general English replacements. The official examples also expose part-whole/relatedness confusion.[^26]

**AgentMap, TaxoRefine, and LLM-assisted ontology-learning systems** use prompted general models, ontology context, or expert supervision. They support the plausibility of the frontier fallback, but do not supply a newly trained, portable subsumption specialist. Formal ontology reasoners require supplied axioms; they do not independently understand arbitrary category descriptions.[^27]

## Larger hypernym checkers: RankAlign

RankAlign examines whether a language model’s generated answers agree with its yes/no judgments. Its hypernym benchmark uses concrete object categories with both true and false pairs. The principal objective is agreement between those two operations, not maximizing subsumption accuracy.[^28]

That distinction changes the interpretation of its results. In the Gemma-2 experiment, validator AUROC falls from 0.970 for the base model to 0.935 for RankAlign, while the simpler fine-tuning baseline reaches 0.983. The headline improvement in generator–validator correlation is therefore not evidence of improved correctness. Tests with different vocabulary are encouraging for consistency, but do not establish abstract multiword-category transfer.[^28]

Public TAUR-dev Gemma-2 checkpoints associated with RankAlign exist, including a verified 2.614B variant. Its card specifies a concrete-object hypernym task and an experimental loss configuration. It cannot be reliably identified with the paper’s main evaluated variant; some card-referenced evaluation scripts are absent from the official repository. The card has no explicit license declaration.[^29]

**Assessment:** a real lead, but not a justified first trial or a demonstrated stronger hypernym checker. Its inclusion closes an important gap left by searching only embedding encoders.

## Directional embeddings and lexical relationship models

Joint-input models broaden the search, but they do not erase the existing evidence about embeddings. The following distinctions prevent unavailable or unsuitable methods from repeatedly reappearing as supposed solutions.

| Family | Available capability | Why it is not a leading new solution |
| --- | --- | --- |
| RSE / HierarCaps | Released directional sentence representations | Already tested locally; no demonstrated overall parent-selection gain for RSE[^30] |
| HiT | Released MiniLM/MPNet hierarchy encoders | WordNet specialization and small encoders; general topical-category decisions remain unproved[^31] |
| OnT | Released ontology text encoders | Biomedical/formal-ontology specialization, not evidence of broad transfer[^32] |
| DSR / ChangeIsKey | Released RoBERTa-large definition-pair relation classifier | Already tested locally; dictionary-definition specialization did not transfer reliably[^33] |
| RelBERT | Released 355M relationship embeddings for ordered pairs | Published lexical classification fits an extra MLP; its trained classifier is not supplied[^34] |
| HyperVec | Released directional word-vector table | Fixed vocabulary, not an arbitrary description encoder[^35] |
| LEAR / GLEN | Lexically specialized word vectors or mapper | Word-level inference; resource verification gaps and no general phrase decision interface[^35] |
| GET, including Llama-3-8B | Relevant lexical-relation and graded-entailment method | Official code/data found; specialized trained weights not verified[^36] |
| HyperDef | Binary hypernym model over words and definitions | Source promises pretrained use, but accessible trained weights not verified[^37] |
| LIiC / related lexical classifiers | Contextual lexical-inference methods | Code/data do not establish available trained classifiers[^37] |
| GaussCSE | Gaussian sentence representations, directional KL scoring | Linked official model repository contains no trained weights[^38] |
| GumbelCSE | Sentence boxes with directional overlap | Code available; official trained checkpoint not verified[^38] |
| Subspace sentence embeddings | Directed inclusion through learned subspaces | Official code release, no verified trained specialized head[^38] |
| DualCSE | Explicit/implicit sentence representations | Official weights not verified; third-party BERT checkpoint lacks sufficient provenance/license[^38] |

RelBERT deserves special emphasis: its downloadable neural model is real, but it represents the relationship between two supplied terms. Comparing relationship vectors is not the same as having a trained classifier that names that relationship. The official lexical-classification code explicitly fits a new MLP. Doing that would violate the present no-training constraint.[^34]

Similarly, a large static word-vector file is not a large language model that can read a novel category description. HyperVec’s millions of stored word vectors do not confer arbitrary phrase composition. GLEN’s mapper accepts word vectors, and its current prediction script discards its asymmetric calculation in favor of cosine output.[^35]

General retrieval embeddings and rerankers may score relatedness or relevance, but those scores are not automatically subsumption scores. Knowledge-graph embeddings over known entity IDs also do not provide a general text-input classifier. Neither architectural asymmetry nor a model’s name substitutes for evidence about the relationship it learned.

## What the existing experiments establish

The preserved RSE01 experiment used 180 category descriptions from HRC03. RSE selected the intended parent in 49 of 60 matched comparisons, equal to HierarCaps; ordinary cosine on RSE’s own vectors selected it in 50. RSE improved some examples and worsened others. Its released inference was independently reproduced, so the results are not merely an unverified implementation concern.[^30]

Those experiments are useful evidence about the tested representations. They do not measure the rejection of arbitrary proposed edges. A model could choose the better of two bad parents and still be incapable of deciding that neither subsumes the child. Conversely, a modest ranking score does not reveal all possible precision/recall tradeoffs for an absolute decision.

The new model search therefore does not justify rerunning the same forced-parent comparison and calling it a full subsumption evaluation. It also does not justify declaring all NLI models failed because an earlier small DeBERTa configuration made errors.

## Evaluation implications

The next comparison should keep the actual decision fixed: does A subsume B? It should include true containment, reversed containment, equivalence, overlapping categories, related siblings, and unrelated categories across the corpus’s different subject areas. Acceptable paraphrases of the same category should not reverse the decision. Ambiguous descriptions should be distinguished from demonstrably wrong model judgments.

This does not prescribe one correct hierarchy. Several parents or arrangements can be valid. The assessment concerns each proposed relationship and the meanings of its two categories—not agreement with an arbitrarily chosen complete tree.

There are three implementation traps to avoid before interpreting scores:

1. **Direction.** A subsumes B corresponds to B implying A in an entailment formulation. Some model cards contain misleading example labels, so orientation needs simple sanity checks.
2. **Relative versus absolute scores.** Ranking a candidate first, generating it frequently, or assigning low perplexity does not prove the relationship. A rejection decision must be assessed explicitly.
3. **Discarded uncertainty.** The Hugging Face zero-shot pipeline can normalize entailment against contradiction while omitting neutral. Hypothetical full probabilities of 0.10 entailment, 0.89 neutral, and 0.01 contradiction would then become approximately 0.91. That is not evidence of 91% category inclusion. Three-class NLI should retain all three outputs; binary models should use their actual trained label definitions.[^39]

The most economical recommendation is to qualify TRUE NLI-mixture first with a small set of genuine category-pair decisions, then broaden only if the actual errors leave it plausible. EV-XXL is the strongest additional large entailment alternative from this search. TaSeR can serve as a cheap, native-relation comparison, but its poor transfer evidence does not justify a prolonged rescue effort.

If those trials fail on clear relationships across domains, proceeding to a frontier prompt is justified as a practical choice. That conclusion should be “the tested specialists did not provide an adequate mechanism,” not “no specialist can ever work.” No training is required or proposed by this recommendation.

## Availability, compute, and evidence limits

Availability means a real model artifact or an explicitly qualified author archive—not just a paper, base-model name, or repository of training scripts. These checks are current to September 12, 2026. No new inference or training is reported here.

Joint pair classifiers cannot cache two independent vectors and finish with cosine. They perform neural computation on each proposed pair. For K categories, checking all ordered non-self pairs requires K(K−1) judgments: 9,900 for 100 categories. Batched inference changes throughput, not the number of semantic decisions.

Eleven billion parameters occupy roughly 22 GB at two bytes per parameter before activations and other runtime memory. That is a storage arithmetic estimate, not a measured hardware requirement. Available FP32 files can be substantially larger. Quantization could reduce memory but would itself be an experimental change. No paid compute, downloads of model weights, or additional training were undertaken for this report.

The public search covers direct ontology subsumption, semantic-relation typing, lexical entailment, hypernym generation and validation, taxonomy instruction models, general NLI, larger entailment verifiers, factual-support models, directional embeddings, and relevant 2025–2026 follow-up work. The unresolved gaps are principally unpublished weights, incomplete checkpoint provenance, and missing transfer evidence. Private or unindexed releases cannot be ruled out; “no verified release found” is not a claim that a method never had weights.

## Sources

[^1]: Google, [TRUE NLI-mixture T5-XXL model card, datasets, interface, and files](https://huggingface.co/google/t5_xxl_true_nli_mixture), released 2022. This is the exact recommended checkpoint, not TrueTeacher.

[^2]: Honovich et al., [TRUE: Re-evaluating Factual Consistency Evaluation](https://aclanthology.org/2022.naacl-main.287/), NAACL 2022. General T5 pretraining: Raffel et al., [Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://www.jmlr.org/papers/v21/20-074.html), JMLR 2020.

[^3]: Sanyal et al., [Are Machines Better at Complex Reasoning? Unveiling Human-Machine Inference Gaps in Entailment Verification](https://aclanthology.org/2024.findings-acl.618/), Findings ACL 2024, especially Table 4 and the training/evaluation appendices.

[^4]: Sanyal, [nli-entailment-verifier-xxl checkpoint and native scoring example](https://huggingface.co/soumyasanyal/nli-entailment-verifier-xxl). Verified revision: 9a9a8cbc41607f2216a4a89543b0a1f08f1e4b7a. No checkpoint-specific license declared in the inspected card.

[^5]: Hertling and Paulheim, [Transformer Based Semantic Relation Typing for Knowledge Graph Integration](https://2023.eswc-conferences.org/wp-content/uploads/2023/05/paper_Hertling_2023_Transformer.pdf), ESWC 2023, especially Tables 2, 3, and 5. The relevant result is DistilBERT/WDS/Task, not additional test-case fine-tuning.

[^6]: University of Mannheim, [TaSeR checkpoint](https://huggingface.co/dwsunimannheim/TaSeR), [configuration](https://huggingface.co/dwsunimannheim/TaSeR/raw/main/config.json), and [author supplementary archive](https://figshare.com/articles/dataset/TaSeR/21750338). Verified checkpoint revision: c3f02918a04773578e33c2838d981892632c028c. The archive contents were not inspected.

[^7]: Moskvoretskii et al., [TaxoLLaMA](https://arxiv.org/html/2403.09207v2), ACL 2024; [original adapter](https://huggingface.co/VityaVitalich/TaxoLLaMA).

[^8]: TaxoLLaMA authors, [conditional-perplexity scorer](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/TExEval-2_testdata_1.2/est_ppl.py) and [prompt definitions](https://github.com/VityaVitalich/TaxoLLaMA/blob/7881f9fd26c4ab935d98ffce0fac91eb1fac621c/pipeline_src/dataset/prompt_schemas.py).

[^9]: Moskvoretskii et al., [Large Language Models for Creation, Enrichment and Evaluation of Taxonomic Graphs](https://journals.sagepub.com/doi/10.1177/22104968251404186), 2026 journal extension, especially Sections 4–7; [author repository](https://github.com/uhh-lt/taxonomic-graphs-swj).

[^10]: [TaxoLlama3.1-8b-instruct full checkpoint](https://huggingface.co/VityaVitalich/TaxoLlama3.1-8b-instruct/tree/6680118fd7b58a497ebb9cfe53ce5009043bb4ef); independent use in [Grouping Entities with Shared Properties](https://aclanthology.org/2025.emnlp-main.787.pdf), EMNLP 2025, footnote 7.

[^11]: Knowledgator, [GLiClass instruct-large-v1.0 model card](https://huggingface.co/knowledgator/gliclass-instruct-large-v1.0), [actual architecture configuration](https://huggingface.co/knowledgator/gliclass-instruct-large-v1.0/raw/main/config.json), and [official implementation](https://github.com/knowledgator/gliclass). The inspected configuration names microsoft/deberta-v3-large and the uni-encoder architecture.

[^12]: [tasksource/ModernBERT-large-nli](https://huggingface.co/tasksource/ModernBERT-large-nli); [multi-NLI DeBERTa-large](https://huggingface.co/MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli); [binary DeBERTa zeroshot-v2.0](https://huggingface.co/MoritzLaurer/deberta-v3-large-zeroshot-v2.0); [tasksource DeBERTa](https://huggingface.co/sileod/deberta-v3-large-tasksource-nli). These are distinct checkpoints, not interchangeable training descriptions.

[^13]: Ai2, [Entailer-11B model](https://huggingface.co/allenai/entailer-11b) and [official generation/verification task documentation](https://github.com/allenai/entailment_bank/blob/main/entailer.md), 2022.

[^14]: Liu et al., [Vera paper](https://arxiv.org/html/2305.03695v2), 2023; [model card and custom inference](https://huggingface.co/liujch1998/vera).

[^15]: Zha et al., [AlignScore official release](https://github.com/yuh-zha/AlignScore), 2023. The direct NLI operation is distinct from the default document-splitting/aggregation mode.

[^16]: Tang et al., [MiniCheck paper](https://aclanthology.org/2024.emnlp-main.499/), EMNLP 2024; [Flan-T5-Large checkpoint](https://huggingface.co/lytang/MiniCheck-Flan-T5-Large).

[^17]: Bespoke Labs, [Bespoke-MiniCheck-7B model card](https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B). Its 7.74B backbone and synthetic-data teacher are different models.

[^18]: Gekhman et al., [TrueTeacher paper](https://aclanthology.org/2023.emnlp-main.127/), EMNLP 2023; [TrueTeacher-plus-ANLI checkpoint](https://huggingface.co/google/t5_11b_trueteacher_and_anli).

[^19]: [FactCG paper](https://arxiv.org/html/2501.17144v1), 2025; [DeBERTa-large checkpoint](https://huggingface.co/yaxili96/FactCG-DeBERTa-v3-Large).

[^20]: Vectara, [HHEM open checkpoint and version distinction](https://huggingface.co/vectara/hallucination_evaluation_model).

[^21]: Patronus AI, [Lynx-8B model card](https://huggingface.co/PatronusAI/Llama-3-Patronus-Lynx-8B-Instruct) and [GLIDER model card](https://huggingface.co/PatronusAI/glider).

[^22]: DeepOnto, [BERTSubs workflow](https://krr-oxford.github.io/DeepOnto/bertsubs/) and [BERTMap workflow](https://krr-oxford.github.io/DeepOnto/bertmap/); He et al., [Language Model Analysis for Ontology Subsumption Inference](https://aclanthology.org/2023.findings-acl.213/), Findings ACL 2023; [OntoLAMA dataset](https://huggingface.co/datasets/krr-oxford/OntoLAMA).

[^23]: Chen et al., [Mining Knowledge for Natural Language Inference from Wikipedia Categories](https://aclanthology.org/2020.findings-emnlp.313/), Findings EMNLP 2020; [author repository, head-removal instruction, and pretrained-model link](https://github.com/ZeweiChu/WikiNLI).

[^24]: [TaxoInstruct final paper](https://aclanthology.org/2025.findings-acl.167.pdf), Findings ACL 2025; [official repository](https://github.com/yanzhen4/TaxoInstruct); [author model archive folder](https://drive.google.com/drive/folders/1uzvK0jppBEni9B7Hy5OhZLQ9McbQym32). Archive presence is verified; contents are not.

[^25]: [OntoTune paper](https://arxiv.org/html/2502.05478v1), 2025, especially Sections 4.2.2–4.2.3; [released medical model](https://huggingface.co/zjukg/OntoTune-sft-Llama3-8B).

[^26]: Barcelona Supercomputing Center, [biomedical semantic-relation classifier](https://huggingface.co/BSC-NLP4BIA/biomedical-semantic-relation-classifier), [SetFit release](https://huggingface.co/BSC-NLP4BIA/biomedical-semantic-relation-classifier-setfit), and [official examples](https://github.com/nlp4bia-bsc/KeyCARE/blob/main/nbs/Tutorial_RelExtractor.ipynb).

[^27]: [AgentMap](https://arxiv.org/html/2607.27130v1), 2026; [From Subsumption to Satisfiability](https://arxiv.org/html/2604.16672v1), 2026; [TaxoRefine](https://link.springer.com/article/10.1007/s12599-025-00982-y), 2025.

[^28]: Rodriguez, Ding, Erk, and Durrett, [RankAlign: A Ranking View of the Generator-Validator Gap in Large Language Models](https://arxiv.org/html/2504.11381v2), COLM 2025, especially Table 2 and the metric definitions; [official code](https://github.com/juand-r/rankalign).

[^29]: TAUR-dev, [verified experimental Gemma-2 checkpoint](https://huggingface.co/TAUR-dev/rankalign-v6-gemma-2-2b-d0.15-e2-hc-b2d-dbl-all-tcs-ln-p0-nv1-ng1-fsx-sm0.1). Revision: 8e2c8d83391d31713d69782d2e5aaf236ae5dc47. Its loss configuration and dataset name must not be conflated with the paper’s principal variant.

[^30]: Project evidence, [RSE01 results](./RSE01/RESULTS.md), [complete cases](./RSE01/CASES.md), and independent inference verification (`./RSE01/verification.json`). These are prior local experiments, not new measurements in this review.

[^31]: [Language Models as Hierarchy Encoders](https://arxiv.org/html/2401.11374v4); [official HiT release](https://github.com/KRR-Oxford/HierarchyTransformers).

[^32]: [Language Models as Ontology Encoders](https://arxiv.org/html/2507.14334v1); [OnT checkpoint inventory](https://github.com/HuiYang1997/OnT).

[^33]: [DSR paper](https://aclanthology.org/2024.acl-long.249/), ACL 2024; [released ChangeIsKey classifier](https://huggingface.co/ChangeIsKey/change-type-classifier). Earlier project measurements: SRR01 (`./SRR01/scores.json`), SRR02 (`./SRR02/scores.json`), SRR03 (`./SRR03/scores.json`). These are not new evidence here.

[^34]: [RelBERT checkpoint and training configuration](https://huggingface.co/relbert/relbert-roberta-large); [official lexical-classification evaluator that fits an MLP](https://github.com/asahi417/relbert/blob/master/relbert/evaluation/lexical_relation_classification.py); [2025 journal extension](https://orca.cardiff.ac.uk/id/eprint/179566/).

[^35]: Nguyen et al., [HyperVec paper](https://aclanthology.org/D17-1022/), EMNLP 2017, and [pretrained-vector resource](https://www.ims.uni-stuttgart.de/forschung/ressourcen/experiment-daten/hypervec/); [LEAR paper](https://aclanthology.org/N18-1103/) and [repository](https://github.com/nmrksic/LEAR); [GLEN paper](https://aclanthology.org/P19-1476/) and [prediction implementation](https://github.com/codogogo/glen/blob/master/glen_predict.py).

[^36]: [GET paper](https://aclanthology.org/2025.acl-long.511/), ACL 2025; [official code/data repository](https://github.com/ginwind/GET).

[^37]: [HyperDef paper](https://aclanthology.org/S18-2025/) and [pretrained inference source with local weight paths](https://github.com/yinwenpeng/HyperDef/blob/master/test_pretrained_HyperDef_allDef.py); [contextual lexical-inference paper](https://aclanthology.org/2021.eacl-main.108/) and [repository](https://github.com/mnschmit/lm-lexical-inference).

[^38]: [GaussCSE paper](https://aclanthology.org/2024.eacl-short.36/) and [empty official model repository](https://huggingface.co/yoda122/gausscse/tree/main); [GumbelCSE paper](https://doi.org/10.1109/ACCESS.2026.3691815) and [code](https://github.com/iehok/GumbelCSE); [subspace-embedding paper](https://arxiv.org/abs/2508.16687) and [code](https://github.com/gabmoreira/subembed); [DualCSE paper](https://aclanthology.org/2026.findings-eacl.74/), [official code](https://github.com/iehok/DualCSE), and [qualified third-party weights](https://huggingface.co/AtPeak/dualcse/tree/main).

[^39]: Hugging Face, [production zero-shot classification scoring](https://github.com/huggingface/transformers/blob/main/src/transformers/pipelines/zero_shot_classification.py). The numerical example is illustrative arithmetic, not a model observation.

**Selected data:** The [publication catalog](../../docs/experiments/publications.csv) lists compact pair-score results, inputs and parameters selected for release for these saved runs:

- `SRR01` — `numerical/pair-scores-40ce4abc5f6c4cfd`.
- `SRR02` — `numerical/pair-scores-491376be0d396173`.
- `SRR03` — `numerical/pair-scores-55e2f987d071484a`.

These compact exports use a different format. Other cited artifacts remain separate originals.
