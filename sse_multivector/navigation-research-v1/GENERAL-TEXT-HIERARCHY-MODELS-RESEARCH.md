# Alternatives to HierarCaps for general-text categories

Research and release audit: September 12, 2026.

## Conclusion

**RSE RoBERTa-large is the strongest currently verified direct candidate for a broader-text experiment. HiT is the strongest complementary candidate trained explicitly on category relationships. Neither is established as a successful replacement.** Their strengths are different: RSE learns relationships between varied sentences; HiT learns direction between taxonomy labels.[^1][^2][^3]

The deeper search also identifies genuine larger alternatives, including **TaxoLLaMA3.1-8B**, but these generate or score text rather than independently encode each category for a geometric comparison. They belong in a separate architectural decision, not a claim that a large HierarCaps replacement has been found.[^17][^18]

The most relevant newer representation methods are **GaussCSE, GumbelCSE, and subspace embeddings**. All offer more explicit directional structure than ordinary cosine. However, usable official trained checkpoints could not be verified through their public release paths. Under the no-training constraint, they are research leads rather than runnable recommendations.[^5][^6][^8]

This is a bounded negative finding about available evidence and releases. It is not proof that no better model exists, that small models necessarily fail, or that a usable model must make no mistakes.

## The task being investigated

The proposed pipeline first obtains groups from the SSE vectors, then names those groups, then places the named groups in a broader-to-narrower organization. This search concerns that last component. Its immediate inputs are **category names or descriptions**, such as “Software distributed under the GPL” and “Open-source software.” It does not receive the original note unless that input contract is deliberately changed.

Earlier searches focused on disconnected source-mask text. Clean category descriptions remove some of that input difficulty, but create their own transfer question: does the model understand newly composed descriptive phrases, rather than only familiar labels?

A direct replacement should provide:

- Released, already-trained weights. No new training, fitted classifier or learned projection is assumed.
- An independently reusable representation of each input text.
- A documented directional calculation relevant to broader–narrower meaning.
- A plausible training distribution for nonvisual subjects, not just image captions.

Those are selection criteria, not a demand for a uniquely correct hierarchy. Topical refinement is also not identical to logical entailment between factual claims. Successful NLI, dictionary hypernym prediction and topical parent placement must remain separate empirical claims.

The completed [HRC03 transfer experiment](./HRC03/RESULTS.md) motivates this search. HierarCaps preferred the intended parent in 49/60 matched comparisons, versus 50/60 for cosine on the same HierarCaps embeddings. Software was especially weak, and some parent paraphrases changed the preferred placement. That establishes problems with this configuration on this fixture—not universal failure outside visual data.

## Direct candidates, ranked by fit

### 1. RSE RoBERTa-large

**Weights:** generally pretrained RoBERTa-large, then relation-aware sentence training. The roughly 355M-parameter encoder produces 1,024-dimensional representations. Its training combines SNLI/MNLI, duplicate questions, paraphrases, caption correspondence, question–answer relations and sentence identity. It is neither trained solely on WordNet nor confined to image captions.[^1][^2]

**Calculation:** independently encode the two texts, then use the released entailment relation vector:

```text
score(child, proposed parent)
    = cosine(embedding(child) + entailment_relation,
             embedding(proposed parent))
```

Only the first vector receives the learned relation, so reversing the inputs can change the score. The official pooling/MLP and relation weights are part of the model; loading a generic RoBERTa encoder and taking plain cosine would not reproduce RSE.[^2]

**Why first:** its language training has the clearest breadth among the verified independent directional encoders. The released calculation is already trained; adopting it for an experiment does not require inventing or learning a new score.

**What remains unproven:** the relation is sentence entailment, not a trained topical-containment guarantee. Its geometry does not enforce transitivity. The paper's STS, retrieval and transfer results do not establish reliable category placement, and benchmark-specific checkpoint results should not automatically be attributed to the 10-relation release. Common training/inference configurations use 32-token truncation, which warrants checking against actual description lengths.[^1][^2]

The historical-maintenance notice is real, but no author-designated successor was identified. Newer related papers are not evidence that RSE has been superseded on this task. The current model card also lacks explicit license metadata; code availability should not be substituted for a verified weight-license statement.[^2]

### 2. HiT / Hierarchy Transformers

**Weights:** generally pretrained sentence encoders, subsequently trained on taxonomy relationships. Available WordNet models include MPNet and MiniLM. The MPNet checkpoint has 109,486,464 parameters and a 768-dimensional representation.[^3]

**Calculation:** the score combines hyperbolic distance with a weighted radial difference. Related concepts should remain close, while a parent is encouraged nearer the origin than its child. Unlike ordinary cosine, the calculation has an explicit direction.[^3]

**Why second:** training directly addresses category relationships, and the paper includes transfer beyond the training ontology. This is more directly relevant to short category names than the earlier raw-mask input setting.

**Important qualifications:** the paper uses entity names or labels, not arbitrary free-form descriptions. The published WordNet-to-other-ontology transfer belongs to the MiniLM-L12 model, not automatically to the larger MPNet checkpoint. With hard negatives, reported transfer F1 is .480 on Schema.org, .507 on FoodOn and .566 on DOID. The scoring weight and classification threshold are selected using validation data; these are not calibration-free accuracy claims.[^3]

HiT is therefore worth considering as a distinct learned signal, not as a larger or demonstrably better general replacement. Any experiment must distinguish the author’s selected scoring configuration from additional tuning on the project’s cases.

### Why there is no equally strong third direct recommendation

**OnT**, the released successor in the HiT family, extends encoding to formal ontology expressions, including verbalized complex concepts and roles. Six MiniLM/MPNet checkpoints exist for GO, GALEN and anatomy. This is genuine progress in expressive input, but all released specializations are biomedical. Verbalizing a formal expression is also different from understanding arbitrary category prose. Plain concept encoding need not consult a runtime ontology; the concern is demonstrated transfer, not an invented inference dependency.[^4]

The third-party **DualCSE** release is a possible future audit target, but its provenance and license are insufficiently documented to rank beside the official releases. Other verified models predominantly return to visual-language training or require a different interface.

## Newer representations: what is real and what is missing

| Method | What the model represents | Training relevant to transfer | Release finding and consequence |
| --- | --- | --- | --- |
| **GaussCSE**, EACL 2024 | A Gaussian mean and diagonal variance per sentence; asymmetric KL-based scoring. | SNLI/MNLI entailment, contradiction and reversed entailment. | Official code exists on `master`. The linked HF model repository contains only `.gitattributes`; trained weights were not verified. Not runnable under the no-training constraint.[^5] |
| **GumbelCSE**, IEEE Access 2026 | A box per sentence; directional overlap divided by the premise-box volume. Additional interpretation representations use reference sentences. | SNLI/MNLI, with separate ambiguity tests. | Substantial official code now exists—earlier “title-only repository” descriptions are stale. No official trained weights or release assets were verified.[^6] |
| **DualCSE**, EACL 2026 | Separate explicit and implicit meaning representations, with cross-role cosine scoring. | INLI dialogue-based explicit/implicit entailment, rather than image captions. | Official training code exists. A real third-party checkpoint exists, but its equivalence to reported models and licensing remain unresolved.[^7] |
| **Subspace embeddings**, KDD 2026 | A soft projection matrix per text; normalized trace overlap supplies directed inclusion. | MiniLM/MPNet backbones fine-tuned on SNLI. | Official release and Zenodo archive contain code, not verified trained heads. Public backbone weights alone are insufficient.[^8] |
| **KLCSE**, June 2026 | Adds asymmetric KL terms during contrastive training. | SimCSE-derived sentence training; reported STS/MTEB evaluation. | No verified checkpoint. The documented evaluation exports ordinary pooled vectors, and the example model link is supervised SimCSE. Asymmetric training is not evidence of a usable directional inference score.[^9] |
| **HiM**, TMLR 2026 | A small Mamba-based sentence encoder with hyperbolic hierarchy training. | SNLI and taxonomy training; WordNet and ontology evaluations. | Official instructions train SentenceMamba, then HiM. No trained checkpoint was located. Its roughly 16M size is not the exclusion criterion; missing weights are.[^10] |

These papers do support the plausibility of independently encoding directional meaning. They do **not** establish an available broad-domain winner. Direction prediction on a pair already known to entail is easier than deciding whether an unrelated or merely associated category is a valid parent. Development-set thresholds and length baselines therefore matter when interpreting headline results.

No method in this table was trained or run during this search.

## Larger models and training-free readouts

**Large ordinary embeddings.** Qwen3-Embedding, E5-Mistral, GTE-Qwen, NV-Embed, GritLM, LLM2Vec, LG-ANNA and Nemotron retrieval encoders provide substantial general language capacity. However, their published retrieval/similarity results do not establish a ready broader–narrower calculation. Query/document instructions can make an overall pipeline asymmetric without making that asymmetry represent category inclusion. No verified transfer result justifies treating an instruction alone as a replacement for trained hierarchy direction.[^11]

**HypRAG / HyTE.** This is a particularly relevant newer line because it pursues hyperbolic text retrieval beyond a purely visual setting, including pretrained-encoder initialization and a Qwen variant. But the checked public channels did not expose a verified pretrained HyTE download. Its published retrieval calculation is hyperbolic distance; depth illustrations and specificity diagnostics do not by themselves provide a validated directional category scorer.[^12]

**HELM.** Real 120M hyperbolic language-model checkpoints are available. The separate 1B download link is empty. Training uses Wikipedia; qualitative analysis of the 1B model connects radius with generality. Those observations should not automatically be attributed to the released 120M checkpoints. No tested recipe was found that combines category relatedness and breadth for arbitrary descriptions. This is not dismissed as too small; it lacks the necessary demonstrated readout.[^13]

**Hierarchy information inside large LLMs.** Recent Llama/Qwen and Gemma studies provide evidence that hierarchical information can be recovered from language-model representations. However, the examined methods estimate concept directions, prototypes, linear maps or transformations using known relationships or descendant sets. A frozen backbone does not make the whole method training-free. Those results do not provide an untouched encoder-plus-score ready for this project.[^14]

**“Unpacking the Suitcase of Semantic Similarity.”** This work explicitly trains projections. Its reported “entailment coefficient” for E5-Mistral is a fitted regression coefficient, not a native entailment probability or a ready directional formula. The full publication/release status remains unresolved; it cannot support a claim that an ordinary 7B embedding model already solves the problem.[^15]

**A correction concerning “The Geometry of Meaning.”** The PeerJ paper does publish a training-free directional rule: predict entailment when the premise-vector norm is at least the hypothesis-vector norm. Its later three-way classifier instead uses an absolute norm gap and validation-selected thresholds, which lose direction. Calling the entire paper symmetric would be incorrect.[^16]

The directional rule has a different limitation: for any two unrelated inputs with unequal norms, it still assigns entailment in one direction. That is a consequence of the formula, not an experimental finding. The released script also does not reproduce the paper's accuracy/F1 evaluation: it reads sentences and counts decisions without reading gold labels. This weakens reproducibility evidence; it does not prove the reported results false. A generality ranking alone is not a complete parent-membership test.[^16]

## Larger, released alternatives with a different interface

These are included so that an embedding-only search does not conceal adjacent solutions. None is silently adopted as the next architecture.

### TaxoLLaMA and TaxoLLaMA3.1-8B

The original model starts from generally pretrained Llama-2-7B and specializes on WordNet hypernym relationships and definitions. The later family includes **Llama-3.1-8B-Instruct** variants. The author’s 8B repository contains actual full weights, and a separate EMNLP paper uses that exact release.[^17][^18]

Unlike a runtime WordNet lookup, this is a learned language model that can process new inputs. But WordNet remains its specialization data; newer and larger does not remove the question of transfer to descriptive topical categories.

The original published ranking method compares conditional text likelihoods in the two directions. This requires processing the pair, not computing a native geometric score from two independently cached embeddings. The paper reports threshold sensitivity and errors involving polysemy and synonyms. The 2026 extension adds real taxonomy evidence, but does not establish robust parent placement across this project's five domains. Its generic 8B model card does not fully identify the training variant or provide a complete inference recipe. Older 7B benchmark results must not be attributed automatically to the 8B upload.[^17][^18]

**Disposition:** a genuine, larger nonvisual lead if pairwise language-model scoring is explicitly considered. Not a direct embedding replacement, and not a proven fix.

### TaxoInstruct and OntoTune

**TaxoInstruct** trains a generative model to find parents and siblings. The final ACL 2025 paper uses Llama-3-8B and CTD's disease taxonomy for initial specialized training, then uses target-task fine-tuning. This differs materially from the older preprint's Llama-2 and MAG-plus-CTD setup. The author-linked Drive folder contains `model.zip`, but its contents and suitability as an unchanged general model were not verified. Its reported task results cannot be treated as no-training transfer.[^19]

**OntoTune** has a real released Llama-3-8B checkpoint. It uses SNOMED CT to specialize an instruction model, and reports medical hypernym discovery and medical QA. This is a useful counterexample to “only tiny models exist,” but not evidence that the desired general-category embedding model is available.[^20]

### General pairwise entailment models

**ModernBERT-large-NLI** is a verified roughly 396M-parameter model with broad NLI specialization, including multi-genre, adversarial, dialogue, document, logical and label-classification tasks. It reads the two texts together and predicts entailment/neutral/contradiction. Its training distribution is broader than caption-only learning, but its published model-card results do not establish topical parent placement.[^21]

**TrueTeacher** is a real 11B T5 model, trained with ANLI and synthetic factual-consistency examples from news summaries. Its intended task and noncommercial research license make it a poor first choice here. Size does not compensate for a mismatched decision task.[^22]

Neither is an independent embedding substitute. Restricting pair scoring to a candidate list could reduce computation, but the quality of that candidate list would become another untested dependency. No such pipeline was implemented or authorized by this search.

## Why newer visual-language models are not the leading answer

MERU, HyCoCLIP, PHyCLIP, UNCHA, Hyper3-CLIP, ARGENT and related cone-based methods are directly relevant to the geometry. Their principal supervision and evaluations nevertheless remain image–text or visually grounded hierarchy tasks. They do not establish the requested expansion to software, economics, political ideas and interpersonal descriptions.[^23]

There is an important release correction for **Hyper3-CLIP**. Its current HF repository advertises a completed 500,000-step paper run and contains a real checkpoint. The GitHub README still describes the public artifact as an earlier non-paper model. The HF configuration specifies a randomly initialized CLIP-B/32 text architecture, not a large general-text pretrained model. This discrepancy should be resolved before attributing paper results to a particular download; it is not accurate simply to say no weights exist.[^24]

A July 2026 audit of released MERU, HyCoCLIP and PHyCLIP checkpoints reports that their intended radial/cone hierarchy mechanisms are weak or inactive under its diagnostics. This is relevant contrary evidence, not a verdict on all hyperbolic models. It neither audits HierarCaps nor establishes that Hyper3-CLIP or ARGENT must fail.[^25]

## Search coverage and remaining gaps

The search followed the independent-sentence relation, Gaussian/box/subspace, taxonomy/ontology, large-encoder, frozen-readout and visual-hierarchy families. Adjacent pairwise and generative models were checked separately. The release audit used author repositories, alternate branches, release assets, linked storage, HF author inventories, file manifests and model configurations—not just paper abstracts or repository names.

Additional relevant branches were retained rather than counted as direct solutions:

| Branch | Why it does not currently supply the requested replacement |
| --- | --- |
| Vendrov order embeddings | A live official archive is documented as COCO image–caption weights. The separate textual-entailment branch has code but no verified trained text-entailment model.[^26] |
| Hyperbolic sentence representations, arXiv 2406.15472 | This is a 2018 thesis uploaded in 2024. Higher-scoring variants add a pair classifier; no complete trained release was verified.[^27] |
| Entailment-based sentence embeddings, Mahabadi et al. | Directly relevant independent representations and scoring, but no official trained artifact was located.[^28] |
| Distilled Sentence Embedding | Microsoft releases training and loading code; no verified ready general entailment checkpoint was found in that release.[^29] |
| Sen2Pro | Probabilistic sentence representation, but its final comparison is symmetric.[^30] |
| ProtoBox, HyperVec, LEAR, lexical order/box methods | Primarily word/sense representations and lexical relationships; not established encoders of arbitrary descriptive phrases.[^31] |
| Prompt2Box | Relevant architecture, but no verified trained model release. A project-site repository is not the model artifact.[^32] |
| Hierarchy-properties RoBERTa | Actual weights exist, but cosine-based training and additional learned classification for relevant evaluations do not provide a verified native directional category score.[^33] |
| NeurOWL | Uses a runtime ontology; its OnT branch fine-tunes on that ontology. It is not evidence of a newly released universal OnT encoder.[^34] |
| FST taxonomy/residual embeddings | A potentially relevant general-topic abstract was located. Full method and trained artifact could not be verified; no native inclusion calculation established.[^35] |

Remaining uncertainty is concentrated in unverified artifacts, incomplete model cards and transfer evidence—not evidence that another broad keyword search will necessarily reveal a qualified winner. Public searches cannot rule out private, unindexed or future releases. Authors were not contacted. In particular, the missing-weight findings for GaussCSE, GumbelCSE, subembed, HiM and HyTE are dated release checks, not permanent claims that weights never existed.

Three earlier shortcuts must not recur:

1. **Paper available → trained model available.** Several apparently promising releases stop at code.
2. **Broad pretraining → reliable hierarchy transfer.** Specialization data and the actual scoring objective still matter.
3. **Directional score → valid parent.** A score can order unrelated concepts, exploit wording length or detect entailment without resolving topical placement.

## Recommended next decision

The least-assumptive next experiment is **RSE on the existing category-transfer inputs**, using its native released entailment scorer. HiT can supply a complementary taxonomy-trained comparison, with its scoring configuration recorded explicitly. The existing descriptions should not be rewritten after inspecting scores to make either model look better.

That would test whether different training and scoring address the observed weakness, without simultaneously changing the corpus, masks, node generation or hierarchy algorithm. Ambiguous cases in HRC03 should remain visibly qualified rather than treated as incontrovertible failures.

TaxoLLaMA3.1 is the most concrete larger adjacent lead from this search, but testing it would be a separately acknowledged move to conditional language-model scoring. Missing specialist weights do not justify training them without authorization.

No alternative model was run, no weights were downloaded, and no experiment or production code was changed for this research.

## Sources

[^1]: Wang and Li, *Relational Sentence Embedding for Flexible Semantic Matching*, RepL4NLP 2023. [Paper](https://aclanthology.org/2023.repl4nlp-1.20/), [full text](https://arxiv.org/html/2212.08802v2).

[^2]: RSE [official inference at inspected revision](https://github.com/BinWang28/RSE/blob/2fc202227bf95bd12ce3b41acbbfefb1a45c983f/rse_src/inference.py), [10-relation model files](https://huggingface.co/binwang/RSE-RoBERTa-large-10-relations/tree/b1da9ad30f7c5f943ea35d3c2685df0862ad3cb5), [artifact metadata](https://huggingface.co/api/models/binwang/RSE-RoBERTa-large-10-relations?blobs=true). The roughly 1.42GB weight file is present; no load was performed.

[^3]: *Language Models as Hierarchy Encoders*, [paper](https://arxiv.org/html/2401.11374v4), [official implementation](https://github.com/KRR-Oxford/HierarchyTransformers), [MPNet files at verified revision](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun/tree/733a89bb4487d49304c976fdadb654ba1ecfb244), [artifact metadata](https://huggingface.co/api/models/Hierarchy-Transformers/HiT-MPNet-WordNetNoun?blobs=true). The model card contains copied details; the actual configuration and pooling files take precedence.

[^4]: *Language Models as Ontology Encoders*, [paper](https://arxiv.org/html/2507.14334v1), [official checkpoint list](https://github.com/HuiYang1997/OnT), [GO MPNet artifact](https://huggingface.co/Hui97/OnT-MPNet-go).

[^5]: Yoda et al., *Sentence Representations via Gaussian Embedding*, [EACL 2024 paper](https://aclanthology.org/2024.eacl-short.36.pdf), [code branch](https://github.com/yoda122/GaussCSE/tree/c94c8a050fa3145381a074633bd2a0d6c17e9d2c), [empty model artifact at checked revision](https://huggingface.co/yoda122/gausscse/tree/4d571469b7e6109b47c28159f4a3de86a46dd4a7).

[^6]: *Representing Sentence Interpretations via Overlapping Box Embeddings*, [2026 publication DOI](https://doi.org/10.1109/ACCESS.2026.3691815), [earlier primary manuscript](https://openreview.net/pdf/3df07ed17593840877b30d2a364763122adfc66e.pdf), [GumbelCSE code at checked revision](https://github.com/iehok/GumbelCSE/tree/aef8ef6f63be75fd5c34f8832c0799387c3588bd). Numerical results from different manuscript versions are not interchanged here.

[^7]: DualCSE, [published paper](https://aclanthology.org/2026.findings-eacl.74/), [official implementation](https://github.com/iehok/DualCSE/tree/535fc92ea7197cab2d9481a08a345df1450d701d), [third-party checkpoint](https://huggingface.co/AtPeak/dualcse/tree/483be03ca910ccebc93dc5f08e0fa82e355aaf33). Its `args.yaml` specifies BERT-base, `dualcse_mono` and 64-token input; the approximately 1.31GB training checkpoint is not evidence of a 1.31B-parameter encoder.

[^8]: Moreira et al., *Native Hierarchical and Compositional Representations with Subspace Embeddings*, [paper](https://arxiv.org/html/2508.16687v2), [code](https://github.com/gabmoreira/subembed/tree/71ad7628e3f39d085a4c277e171b0439979d1b48), [Zenodo file manifest](https://zenodo.org/api/records/20357423).

[^9]: KLCSE, [publisher article](https://link.springer.com/article/10.1007/s10115-026-02794-2), [repository at checked revision](https://github.com/na978292231/KLCSE/tree/0bb63fc4af66ebc1cc16603f36212fd6f12c11ce).

[^10]: *HiM: Hierarchical Mamba Meets Hyperbolic Geometry*, [paper](https://arxiv.org/html/2505.18973v3), [official code and training instructions](https://github.com/BerryByte/HiM).

[^11]: Representative primary sources: [Qwen3 Embedding paper](https://arxiv.org/html/2506.05176v1), [Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B), [E5-Mistral](https://huggingface.co/intfloat/e5-mistral-7b-instruct), [GTE-Qwen2-7B](https://huggingface.co/Alibaba-NLP/gte-Qwen2-7B-instruct), [NV-Embed-v2](https://huggingface.co/nvidia/NV-Embed-v2), [GritLM](https://github.com/ContextualAI/gritlm), [LLM2Vec](https://github.com/McGill-NLP/llm2vec), [LG-ANNA paper](https://arxiv.org/html/2506.07438v1), [Nemotron-3-Embed-8B](https://huggingface.co/nvidia/Nemotron-3-Embed-8B-BF16).

[^12]: HypRAG/HyTE [paper](https://arxiv.org/html/2602.07739v2), [project](https://graph-and-geometric-learning.github.io/projects/hyprag), [official repository](https://github.com/Graph-and-Geometric-Learning/HypRAG).

[^13]: HELM [paper](https://arxiv.org/html/2505.24722v2), [official repository](https://github.com/Graph-and-Geometric-Learning/helm), [120M checkpoint manifest](https://zenodo.org/api/records/18729608).

[^14]: *Linear Representations of Hierarchical Concepts in Language Models*, [paper](https://arxiv.org/html/2604.07886v3), [dataset-only repository](https://github.com/masaki-sakata/linear-hierarchical-encoding); *Hierarchical Concept Geometry in Language Models Emerges from Word Co-occurrence*, [paper](https://arxiv.org/html/2605.23821v1).

[^15]: *Unpacking the Suitcase of Semantic Similarity*, [primary OpenReview PDF](https://openreview.net/pdf?id=OCVIGEitkg). Search-indexed sections 3.5 and 4.4 distinguish trained projections from regression over cosine. Direct full-text access encountered a browser challenge; final publication and artifacts were not verified.

[^16]: *The Geometry of Meaning: Evaluating Sentence Embeddings from Diverse Transformer-Based Models for Natural Language Inference*, [PeerJ paper](https://peerj.com/articles/cs-2957/), [native article XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12193426/fullTextXML), [author implementation](https://github.com/suhaibani/geometry/blob/main/geometry.py).

[^17]: TaxoLLaMA [ACL 2024 paper](https://arxiv.org/html/2403.09207v2); *Large Language Models for Creation, Enrichment and Evaluation of Taxonomic Graphs*, [2026 journal extension](https://journals.sagepub.com/doi/10.1177/22104968251404186), [author-hosted PDF](https://www.inf.uni-hamburg.de/en/inst/ab/lt/publications/2026-moskvoretskiietal-swj.pdf).

[^18]: [Original TaxoLLaMA adapter](https://huggingface.co/VityaVitalich/TaxoLLaMA/tree/16eee40bf4205c1de762711fff1b907590cf5fd4); [TaxoLlama3.1-8b-instruct verified full weights](https://huggingface.co/VityaVitalich/TaxoLlama3.1-8b-instruct/tree/6680118fd7b58a497ebb9cfe53ce5009043bb4ef), [metadata](https://huggingface.co/api/models/VityaVitalich/TaxoLlama3.1-8b-instruct?blobs=true); *Grouping Entities with Shared Properties*, [independent use of the exact release, footnote 7](https://aclanthology.org/2025.emnlp-main.787.pdf). The artifact contains 8,030,261,248 parameters and approximately 16GB of BF16 weights; this is storage, not measured inference memory.

[^19]: TaxoInstruct [final ACL 2025 paper](https://aclanthology.org/2025.findings-acl.167.pdf), [older preprint](https://arxiv.org/html/2402.13405v3), [official release instructions](https://github.com/yanzhen4/TaxoInstruct), [author-linked artifact folder](https://drive.google.com/drive/folders/1uzvK0jppBEni9B7Hy5OhZLQ9McbQym32). Archive listing verified; contents not downloaded.

[^20]: OntoTune [paper](https://arxiv.org/html/2502.05478v1), [official repository](https://github.com/zjukg/OntoTune), [8B release at checked revision](https://huggingface.co/zjukg/OntoTune-sft-Llama3-8B/tree/b3cf3654b95e495297925d18a7d0bbef2ffa3e8c).

[^21]: ModernBERT-large-NLI [model card](https://huggingface.co/tasksource/ModernBERT-large-nli), [verified checkpoint revision](https://huggingface.co/tasksource/ModernBERT-large-nli/tree/ca476cb923a8637073d4ceb0f19f7fc236e260d4), [artifact metadata](https://huggingface.co/api/models/tasksource/ModernBERT-large-nli?blobs=true). Test scores are author-reported, not measurements from this project.

[^22]: TrueTeacher [paper](https://aclanthology.org/2023.emnlp-main.127.pdf), [released model, intended use and license](https://huggingface.co/google/t5_11b_trueteacher_and_anli), [training dataset](https://huggingface.co/datasets/google/trueteacher).

[^23]: [HyCoCLIP paper](https://arxiv.org/html/2410.06912v2), [HyCoCLIP model zoo](https://github.com/PalAvik/hycoclip/blob/main/model-zoo.md), [PHyCLIP official repository](https://github.com/tksmatsubara/PHyCLIP), [ARGENT paper](https://arxiv.org/abs/2603.23311), [ARGENT project](https://hmchuong.github.io/argent/). The latest checked ARGENT page advertises code as forthcoming.

[^24]: Hyper3-CLIP [paper](https://arxiv.org/html/2608.29313v1), [GitHub README](https://github.com/Hyper3Labs/hyper3-clip), [current HF card](https://huggingface.co/hyper3labs/hyper3-clip/blob/main/README.md). The similarly named `hyper3-clip-v1` is a separate model line and must not inherit this checkpoint's results.

[^25]: Kim et al., *Is the Geometry Doing the Work? An Operating-Point Audit of Hierarchy in Hyperbolic Vision-Language Models*, [July 2026 preprint](https://arxiv.org/abs/2607.05268v3). Conclusions are bounded to its audited checkpoints and diagnostics.

[^26]: Vendrov [textual-entailment branch](https://github.com/ivendrov/order-embedding/tree/5e8bf4b33dfc9a4bce590eb1081fd3cacbe49dcf), [master release description](https://github.com/ivendrov/order-embedding/tree/2057e6056a887ea00d304fc43a8a7e4810f4d669).

[^27]: *Hyperbolic Sentence Representations for Solving Textual Entailment*, [thesis](https://arxiv.org/html/2406.15472v1), [author's plausible source repository](https://github.com/PetrovskiIgor/SentenceEmbeddings/tree/d1bfa99cd50110ba32ae3e9f11b6b58e8e4213a8).

[^28]: *Learning Entailment-Based Sentence Embeddings from Natural Language Inference*, [author-hosted paper](https://publications.idiap.ch/downloads/reports/2019/rabeehkarimimahabadi_Idiap-RR-20-2019.pdf), [author publication page](https://florianmai.github.io/publications/entailmentvectors/).

[^29]: *Scalable Attentive Sentence-Pair Modeling via Distilled Sentence Embedding*, [paper](https://arxiv.org/abs/1908.05161), [official repository](https://github.com/microsoft/Distilled-Sentence-Embedding).

[^30]: Sen2Pro [paper](https://aclanthology.org/2023.repl4nlp-1.26.pdf).

[^31]: ProtoBox [paper](https://aclanthology.org/2024.repl4nlp-1.1/); HyperVec [paper](https://arxiv.org/abs/1707.07273); lexical-model scope and comparisons in the [TaxoLLaMA related-work review](https://arxiv.org/html/2403.09207v2).

[^32]: Prompt2Box [paper](https://arxiv.org/html/2603.21438v3), [project-site repository](https://github.com/zawedcvg/P2B), [advertised model repository](https://github.com/zawedcvg/box_embeddings). The advertised model path was unavailable in the checked release audit.

[^33]: *Probing Pretrained Language Models with Hierarchy Properties*, [paper](https://arxiv.org/html/2312.09670v1), [training implementation](https://github.com/jeslev/hierarchy_properties_plms/blob/main/train/model.py), [RoBERTa-large artifact](https://huggingface.co/jeslev/roberta-large-with-hierarchy-properties).

[^34]: NeurOWL [paper](https://arxiv.org/html/2607.15776v1).

[^35]: FST, *Taxonomy Co-Training and Residual Decomposition*, [SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6960741). Abstract-level lead only; full methods and artifact status remain unresolved.
