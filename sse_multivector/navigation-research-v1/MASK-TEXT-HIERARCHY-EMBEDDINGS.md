# Hierarchy-aware embeddings for mask text

Research reviewed through September 12, 2026. This is a literature and release audit, not a model experiment or an adopted architecture. Existing experiments, inputs, and pipeline code are unchanged.

## Conclusion

There are relevant alternatives to HiT. They differ more importantly in **what relationship they learned, from what text**, than in whether their geometry is called hyperbolic, Gaussian, or a box.

For ready-to-load experiments, the strongest verified shortlist is **HierarCaps, Relational Sentence Embedding (RSE), and HiT**. HierarCaps learns increasing specificity across phrases and captions; RSE learns directional relations between varied sentence-like texts; HiT explicitly learns taxonomy direction. None has established the behavior needed for our masks.

If training or obtaining unreleased weights is acceptable, subspace embeddings, GaussCSE, GumbelCSE, and Prompt2Box deserve serious consideration. Their published results support capabilities relevant to hierarchy, but do not establish a complete hierarchy-construction method for informal notes.

I found **no verified evaluation of our exact input transformation**: retaining possibly disconnected source fragments from informal notes, joining those fragments in source order, and constructing a topical hierarchy from them. That is a specific evidence gap, not a conclusion that transfer will fail.

## What the model would actually receive

For this research, the input is the text inside one mask. Multiple fragments would supply their exact words in source order. The model does not receive the rest of the note or a generated subject description.

For example, the source mask:

> ⟦the stock fan⟧ … ⟦getting too loud⟧

would supply those words, not an expanded statement identifying the device or explaining why its owner is frustrated. This example illustrates the input boundary, not a proposed serialization format or a recorded model result.

There are two distinct transfer questions:

1. Does the encoder preserve the meaning of these short, sometimes disconnected fragments?
2. Does its learned directional score correspond to a useful broader–narrower subject relationship?

A model can succeed at one and fail at the other. Likewise, good pair scores would supply evidence for a construction method; they would not, by themselves, choose useful category boundaries, resolve conflicting relationships, or produce readable category names.

The analysis below does not require a uniquely correct hierarchy. It distinguishes topical refinement from relations that may be useful signals but are not interchangeable with it:

| Relationship | Illustrative example | Why the distinction matters |
|---|---|---|
| Kind of | A sparrow is a bird. | This is the native relation in many taxonomy models. |
| More specific description | A bird building a nest describes something more specific than a bird. | Caption and entailment models may learn this without a taxonomy. |
| Topic refinement | Coffee roasting belongs under coffee. | Roasting is not a kind of coffee. A strict taxonomy relation can miss this. |
| Logical entailment | Someone roasted coffee beans implies someone roasted something. | Useful overlap with specificity, but not every desirable topic grouping requires logical entailment. |
| Relatedness | Coffee and breakfast. | Related topics do not automatically have a parent–child relationship. |

These are analytical examples, not training examples or expected benchmark answers.

## Shortlist by training fit and readiness

This table is a map of the candidates, not a claim that different benchmark scores can be ranked against one another. The fuller assessments and sources follow.

| Candidate | Native hierarchy/relationship training text | Representation | Current practical status |
|---|---|---|---|
| HiT | Taxonomy entity names and ontology labels | One hyperbolic vector | Verified checkpoints; strongest direct taxonomy baseline |
| RSE | Premise/hypothesis, questions, captions, paraphrases, and other relation-labelled sentence pairs | Vector plus a learned relation vector | Verified checkpoints; broader language coverage, weaker hierarchy evidence |
| Subspace embeddings | SNLI premise/hypothesis strings for the text encoder | A learned subspace represented by a matrix | Training code; no trained text checkpoint verified |
| GaussCSE | SNLI/MNLI premise, entailing hypothesis, contradicting hypothesis | Gaussian mean and variance | Training code; advertised model repository contains no usable weights |
| GumbelCSE | NLI sentence triplets | Box | Training code; no trained checkpoint verified |
| Prompt2Box | Instructions, instruction refinements, prompt–response pairs, and NLI | Box | Paper; advertised encoder repository unavailable when checked |
| Radial embeddings / HierarCaps | Short words/phrases through detailed descriptions of visual scenes | Vector with an angle-based directional score | Verified CLIP-B/L checkpoints; pertinent phrase training, visual-domain limitation |
| Hyper3-CLIP | Image captions and extracted grounded fragments | Hyperbolic vector with entailment cone | Paper checkpoint released; separate pretrained-base version is gated and incompletely documented |
| HypRAG / HyTE | Large-scale query–document pairs, with language pretraining | Hyperbolic vector | Training code; trained checkpoint not verified; direct broader–narrower supervision absent |

### HierarCaps: pretrained phrase-to-description hierarchy encoding

HierarCaps fine-tunes pretrained CLIP text encoders on approximately 73,000 four-level caption hierarchies, from words and short phrases to more detailed descriptions. Higher-level descriptions and negatives are generated and filtered; these are not exact fragments mechanically lifted from the original caption. Hierarchy training itself uses text, without requiring image inputs.[^25]

The score measures a directional angle relative to a root representation, rather than ordinary cosine. The method deliberately relaxes strict partial-order constraints. Its strong chain-ordering result instead measures **distance from the empty-string root** for already-related captions—not the pair-angle score's ability to select parents. Its HyperLex word-pair results use a visual-language prefix, not bare input words.[^25]

Official CLIP-B and CLIP-L checkpoints are available. Their text towers have approximately 63M and 123M parameters respectively; full model downloads also contain the image tower. The code fine-tunes the text encoder and projection, includes a penalty against drifting from pretrained embeddings, and uses the empty-string embedding as root. Its default input limit is 77 tokens.[^26]

**Assessment:** a particularly relevant ready-weight candidate because its hierarchy supervision spans short phrases and richer descriptions. No image is necessary to encode our masks. The visual domain remains a substantial limitation for abstract or technical subjects, and the benchmark's added text prefix must not silently enter our mask-only pipeline.

### HiT: a useful available baseline, with a specific training mismatch

HiT trains on child, parent, and negative-parent triples. Its text inputs are entity names, including ontology labels—not definitions or complete notes. Training makes children close to their parents while placing parents nearer the origin. The score combines distance with the difference in radial position. It is directional, not a probability.[^1]

Transfer exists, but is limited: the WordNet-trained MiniLM-L12 reports hard-negative F1 of 0.480 on Schema.org, 0.507 on FoodOn, and 0.566 on DOID. These tests concern ontology edges, not topical note navigation.[^1]

The released MPNet version has approximately 109M parameters and 768-dimensional output. MiniLM alternatives have approximately 22.7M or 33.4M parameters and 384-dimensional output. These retain language-pretrained, sentence-embedding backbones before hierarchy fine-tuning. The MPNet model card contains copied MiniLM example code; its actual configuration confirms MPNet/768 dimensions. The evaluation implementation tunes the directional coefficient and threshold on the target validation split.[^2]

**Assessment:** especially plausible for clear noun-phrase masks. Less directly supported for activity phrases, clauses, or disconnected fragments. Its limitations are not simply model size: learning “is a kind of” is not the same task as learning every useful topic refinement.

An unusually relevant follow-up makes the transfer concern concrete. A 2026 clinical-span study found standalone HPO HiT worse than ordinary semantic embeddings on CHU-50 weighted MRR@15: 0.627 versus 0.671; their hybrid reached 0.681. The authors discuss the mismatch between ontology-level supervision and clinical spans. This was ontology linking, not hierarchy construction, and the extraction prompt allowed reformulating spans, so it does not validate exact masks either.[^3]

### RSE: an available directional model trained on varied language

RSE independently encodes each text and learns a vector for each relation. Its relation-specific score is:

`cosine(embedding(A) + relation, embedding(B))`

Its training includes SNLI/MNLI entailment, duplicate Quora questions, ParaNMT paraphrases, captions of the same Flickr image, question–answer-sentence pairs, and Wikipedia sentence identity. Reported **in-domain tail-sentence retrieval, with the relation supplied**, reaches MRR 0.80 and Hits@1 0.74 for entailment. This is not direction discrimination or transfer to a new hierarchy.[^4]

The official release includes BERT and RoBERTa variants, including large backbones. Actual weight/config/tokenizer files were verified for `binwang/RSE-BERT-base-10-relations`; the repository lists additional checkpoints. Its custom loader exposes the relation vectors. The ten-relation demonstration model should not be confused with the task-specific mixtures used for every paper result.[^5]

**Assessment:** a strong low-friction baseline for the question “can a trained directional relation add useful information to these mask strings?” It does not enforce an ordering in which all children consistently remain below their ancestors. A directional score is not automatically a containment score.

### Subspace embeddings: the most interesting alternative representation

This method represents text as a learned linear subspace, using inclusion and effective dimension to model direction and breadth. Its text encoder is fine-tuned on SNLI; WordNet results come from separately optimized node representations, **not this text encoder**.[^6]

MPNet's binary SNLI accuracy is 91.91% versus 91.74% for its strongest vector baseline. Its compositional results combine **separately encoded hypotheses algebraically**, rather than encoding joined fragments as one text. That synthetic benchmark also filters out cases where baselines already fail on the component statements.[^6]

The released code independently maps text to a 64×64 or 128×128 matrix, using a pretrained transformer plus attention pooling and a projection head. Training code exists; I did not verify a downloadable trained text encoder. The text model is not a lookup table and could encode unseen mask strings after training.[^7]

**Assessment:** strongest architectural lead for explicitly representing both meaning and breadth without relying on a single radius. Its native text supervision is closer to descriptive masks than a dictionary-only model, but remains entailment training. Its matrix representation also has meaningful storage costs, discussed below.

It does not solve the earlier “one shape includes unwanted meanings between children” concern by definition. The linear span of two subspaces contains combinations beyond their literal set union. Whether those additional combinations are semantically appropriate is still a learned-and-tested property, not a consequence of the mathematics.

### GaussCSE: sentence meaning plus a learned directional distribution

GaussCSE independently maps each text to Gaussian mean and diagonal variance. It trains with SNLI/MNLI entailing and contradicting pairs, plus a loss distinguishing reversed entailment. BERT and RoBERTa base/large versions were evaluated. Its score uses directional KL divergence, not cosine.[^8]

The strongest full-loss RoBERTa-large result reports 97.42% SNLI direction accuracy, but only on pairs already known to entail in one direction. A text-length baseline scores 92.63% on that same task. Binary entailment accuracy is a different result: 76.68% on SNLI and 79.07% on MNLI. Those figures do not establish 97% accurate hierarchy edges.[^8]

A subtle implementation convention matters: this model trains the entailing premise to have **larger variance**. We must not assume its variance means the same thing as a box’s volume or a subspace’s dimension.[^8]

The author repository has code, but its Hugging Face model repository contains only `.gitattributes`, without weights or configuration. The inspected training entry point also needs attention before reproduction: it saves metrics/configuration but not model weights, and defaults differ from the paper.[^9]

**Assessment:** relevant sentence-level direction training, with broader native text than noun taxonomies. A research candidate requiring reproduction or author-supplied weights—not a ready download.

### GumbelCSE: a text-to-box implementation

GumbelCSE trains BERT/RoBERTa sentence encoders with a box head using NLI triplets. Each text can be encoded independently. Additional representations for possible interpretations are obtained by intersecting its box with reference boxes; those reference operations are not required merely to encode two texts and compare them.[^10]

Its direction benchmark, like GaussCSE’s, uses known-entailing pairs. This is narrower than identifying valid parents among arbitrary masks. The official training script uses BERT-base, 64-dimensional boxes, and 64-token truncation. Code is available; no trained checkpoint was verified.[^11]

**Assessment:** a concrete region-based comparison against subspaces or Gaussians. Box containment is an attractive mechanism, but NLI supervision and the shape restriction still need testing against our desired topical relationships. The final publication is IEEE Access, May 2026; an earlier OpenReview manuscript should not be presented as an accepted ICLR paper.[^10]

### Prompt2Box: broader–narrower training beyond taxonomies

Prompt2Box uses an MPNet-based SentenceTransformer and two jointly trained heads to produce boxes. Its 203,138 training examples combine prompt–response similarity, MNLI, constraint hierarchies, LLM-generated instruction generalizations, and cross-dataset links. The directional score is the fraction of A’s box covered by B’s box.[^12]

This is genuinely hierarchy-related supervision beyond WordNet: more constrained instructions are refinements of broader instructions. The latest paper reports FollowBench hierarchical retrieval of 0.738 versus 0.640 for its vector baseline, alongside lower STS-B similarity performance, 0.760 versus 0.835. The WildChat source instructions were initially filtered to 8–150 words.[^12]

The paper’s advertised encoder repository returned 404 when checked. The accessible P2B repository contains the project website, not a usable encoder implementation. I did not verify trained weights or the exact starting SentenceTransformer checkpoint.[^13]

**Assessment:** a valuable training idea, especially because it combines semantic relatedness and refinement. Not automatically the best transfer to short descriptive masks: an instruction’s constraints define acceptable responses, which is not identical to a social note’s topic. It should remain on the research shortlist, not be called deployment-ready.

## What language knowledge is present before the special training?

The answer varies; “uses a transformer” does not settle it.

| Backbone family | Weights before the candidate’s special training | Approximate backbone size |
|---|---|---:|
| SentenceTransformer MPNet | General MPNet pretraining, then contrastive sentence-pair training drawn from a collection exceeding one billion pairs | 109M |
| SentenceTransformer MiniLM | Distilled transformer followed by sentence-pair embedding training | 22.7M / 33.4M |
| CLIP text tower | Text–image contrastive pretraining; HierarCaps subsequently fine-tunes text–text hierarchy | 63M / 123M |
| BERT | BooksCorpus and English Wikipedia; masked-token and next-sentence training | 110M / 340M |
| RoBERTa | Masked-language training on a larger mixture of books, Wikipedia, news, web text, and stories | 125M / 355M |

These are backbone sizes, not exact total counts after custom heads. The MPNet sentence-training mixture includes Reddit, question–answer pairs, and title/abstract pairs; that knowledge precedes its hierarchy fine-tuning. BERT/RoBERTa-based methods likewise are not trained from nothing on NLI unless explicitly noted otherwise.[^14] CLIP's initial language learning is grounded in paired images and text; it is not a general language-model pretraining stage equivalent to BERT's.[^26]

A pretrained encoder can use all the words it receives to interpret a word. In our setting, those words are only the mask fragments. It may know that a smoker can be cooking equipment, but cannot reliably recover a disambiguating phrase that we removed. Fine-tuning can also change which distinctions its final representation preserves. Neither a familiar backbone nor a larger parameter count proves suitable broader–narrower behavior.

## Compute and release implications

Encoding is independent of other masks for the main shortlist: encode each input once, save its representation, and score pairs later. None inherently requires a frontier-model generation call for every pair. This does not make unrestricted all-pairs comparison cheap; candidate selection and hierarchy construction remain separate decisions.

Backbone-only FP16 weight storage is approximately 0.22 GB for 109M parameters and 0.71 GB for 355M parameters. These are arithmetic lower bounds, **not RAM/VRAM requirements**: inference also needs runtime buffers and activations; training adds gradients, optimizer state, and larger working memory.

Representation storage differs substantially. For one million masks in FP32, excluding indexes and metadata:

| Representation | Numbers per mask | Approximate storage |
|---|---:|---:|
| 768-dimensional vector | 768 | 3.07 GB |
| 768-dimensional Gaussian mean plus variance | 1,536 | 6.14 GB |
| 64-dimensional box, two endpoints | 128 | 0.51 GB |
| 128×128 subspace matrix | 16,384 | 65.54 GB |

These are illustrative arithmetic comparisons, not equal-capability configurations. Low-rank/compressed representations may change the subspace cost; they require their own accuracy checks. Its published SNLI training used a 49 GB RTX 8000, batch 1,024, and 35-token inputs; that is a reported configuration, not a demonstrated minimum requirement.[^6]

Ready checkpoints therefore matter. Loading HiT or RSE is a different commitment from reproducing GaussCSE, GumbelCSE, or subspace training. Missing weights are a practical blocker to an immediate test—not evidence against the method’s semantic potential.

## Other families examined

### Larger hyperbolic encoders: HypRAG / HyTE

HypRAG includes fully hyperbolic and hybrid text encoders. The fully hyperbolic model is approximately 149M parameters, with Wikipedia language pretraining followed by roughly 235M query–document pairs and retrieval fine-tuning. Hybrid variants use pretrained Euclidean token encoders; the project also reports a Qwen3-Embedding-4B-based variant.[^15]

However, its contrastive score is hyperbolic distance, a symmetric quantity. Its MeSH title/abstract retrieval and selected specificity probes do not establish a directional topic-containment model. Radial stability in a pooling operation is not proof that radius faithfully measures semantic breadth.[^15]

The repository exposes training code/configurations, with multi-GPU examples, but no usable trained checkpoint was verified. The 4B project result should not be presented as a released four-billion-parameter HiT replacement.[^16]

**Assessment:** a potentially stronger general semantic encoder with hierarchy-motivated geometry. Less direct evidence for our requested relationship than its name suggests. Worth monitoring, not the first broader–narrower test.

### Visual-caption hierarchy models

HierarCaps above is the most immediately pertinent verified release in this family. Two successors illustrate why their names alone are not sufficient evidence. TaSe/HiVG learns visual-description refinements with a CLIP-based encoder and adapters, but its tested pipeline also uses image-grounded detection and its linked repository was empty. H²em learns prompts for predefined states/objects and conditions text representations on image features; it is not an independent arbitrary-mask encoder.[^27]

Hyper3-CLIP explicitly trains a text–text direction between a complete caption and an extracted fragment: the caption is more specific. Its paper model trains both towers from scratch on GRIT, rather than inheriting CLIP weights. That gives it genuine fragment-level supervision, but within visual descriptions; its evaluations do not establish broad social-text hierarchy transfer.[^17]

The paper checkpoint is released. A separate Hyper3-CLIP v1 line starts from pretrained CLIP and provides a SentenceTransformers wrapper, but is gated behind contact-sharing/conditions. Its public card does not adequately disclose the corpus or text–text hierarchy objective. Its documented Lorentz inner-product retrieval score is symmetric. The paper checkpoint’s claims must not be transferred to this different model line.[^18]

**Assessment:** do not dismiss multimodal models merely for being multimodal. Their fragment training can be pertinent. Conversely, recognizing visual category hierarchies does not establish understanding of abstract, technical, rhetorical, or social-note subjects.

### Definition and word-sense region models

BoxTaxo independently encodes an entity name plus a definition with BERT and learns box containment from an existing taxonomy. It is not merely an entity-ID lookup table, but the definition-assisted input and taxonomy-expansion task differ from our masks. Code is public; a trained encoder was not verified.[^19]

ProtoBox takes a sentence **and a target-word position**, training with SemCor senses and WordNet relationships. It predicts a representation of that word in context, not the entire arbitrary fragment string. That is a different interface, even though the underlying BERT is contextual.[^20]

PEB-TAXO is another definition-assisted taxonomy method; the linked repository contained only an empty data file when checked. None of these should be promoted by quietly adding definitions, generated subject descriptions, or the full note to our input.

### Other text and hyperbolic models

| Family | Why it does not presently displace the shortlist |
|---|---|
| HiM | Hierarchy Mamba successor, but its reported HiM models are randomly reinitialized before hierarchy training; 16M/32M comparisons use random-initialized HiT baselines. No ready hierarchy checkpoint verified. |
| HELM | Hyperbolic language modeling, including a 1B model trained on Wikipedia; next-token and QA results do not supply a validated phrase-level directional embedding score. |
| Hyperbolic BERT | Language pretraining in hyperbolic space; inspected code uses masked-language and next-sentence objectives, not broader–narrower text supervision. |
| DualCSE | Learns literal and implied meaning from contextualized premise/hypothesis examples. Its target is implication, not generality; conversational context is often essential to its native task. |
| Order Embeddings | Genuine early independent sentence encoder and asymmetric order score, but SNLI-trained GRU without a modern pretrained language backbone; legacy implementation and no usable entailment checkpoint verified. |
| Poincaré embeddings, classic entailment cones, many knowledge-graph boxes | Often learn vectors for known entity IDs. A geometric containment rule alone does not give a model that can encode new mask text. |
| Hierarchical text classifiers | Usually require the target category inventory and label hierarchy as supervision. Classification within that hierarchy is not discovering one from arbitrary mask strings. |

Sources and inspected release boundaries for these exclusions are recorded below.[^21][^22][^23][^24]

## What the evidence does—and does not—justify

The literature establishes that independently encoded text can carry a learned asymmetric relation. It also supplies multiple geometries that can express more than symmetric closeness. We do not have to assume cosine is the only available comparison.

It does **not** establish that all asymmetric relations mean topical refinement. It also does not establish that a short-mask input will inherit a paper's results from dictionary definitions, complete instructions, or contextualized language examples.

We should not impose a stronger logical task than content discovery requires. For example, “Coffee tastes good” and “Coffee tastes bad” can share a topic despite disagreeing. Entailment training can treat such disagreement as a negative relation. That is a reason to examine the learned signal against our actual purpose, not to assume either that the model is unsuitable or that logical correctness guarantees useful grouping.

Several misleading shortcuts need to be avoided:

- A 95–97% direction result may assume that one text already entails the other. It does not test selecting a parent from a mixture of related, unrelated, and conflicting texts.
- A title-to-abstract retrieval result is not direct evidence that the system ordered abstracts by semantic breadth.
- Good reconstruction of a known taxonomy using learned entity IDs is not transfer by a text encoder.
- “Code available” does not mean pretrained weights are downloadable, or that the published pipeline can be reproduced without work.
- A higher-dimensional region is not automatically the appropriate union of its children. Its geometry can include extra meanings.
- No benchmark here establishes a uniquely correct organization of our corpus. A legitimate unexpected grouping must remain admissible.

The source text itself also creates an identifiability boundary. If two masks contain the same words but their intended meanings differ only through removed context, an independent deterministic encoder receives identical inputs. No choice among these models can reliably recover that distinction from the mask text alone. This is a property of the input, not a claim that every mask needs more context.

## Recommendation

I would not name one winner from incomparable native benchmarks. I would make the next choice according to what we want to learn:

1. **First usable comparison: HierarCaps, RSE, and HiT-MPNet.** These offer verified weights and complementary supervision. HierarCaps is my strongest new ready-weight lead for phrase-level specificity; RSE supplies more varied sentence relationships; HiT supplies a direct taxonomy baseline. This is a plausibility judgment from their training, not a measured ranking on our masks. If choosing only two new probes beyond existing HiT work, I would choose HierarCaps and RSE.
2. **First new representation to investigate: subspace embeddings.** It is a real independent text encoder, with code and direct text-entailment training, and represents breadth more richly than one point. Obtaining or reproducing trained weights is the prerequisite.
3. **Second representation family: GaussCSE or GumbelCSE.** These supply sentence-level directional training with relatively compact representations. Choose based on recoverable weights/reproducibility, rather than treating Gaussian versus box shape as an answer in itself.
4. **Training-data research lead: Prompt2Box.** Its mixture of relatedness and refinements extends beyond a fixed noun taxonomy. Its input/task mismatch and unavailable encoder release prevent an immediate strong recommendation for our masks.

A future test should compare the exact mask strings—not summaries or restored full notes—and separate whether two fragments are related from whether one is an appropriate broader destination. It should include both recognizable phrases and disconnected fragments, and allow more than one defensible parent. This is a recommendation, not a test run or a newly frozen evaluation specification.

## Research scope and unresolved access

The review followed hierarchy-text, sentence-entailment, probabilistic/region, subspace, and visual-language hierarchy families; it checked methods, training inputs, native objectives, evaluation tasks, and release code/metadata. General embedding and hierarchical-classification papers were screened for whether they actually supplied an independent directional text representation.

Only papers, model cards, source code, and release metadata were read. No model weights were downloaded, no models were run, and no gated conditions were accepted. Negative release findings mean “not verified at the checked author links on this date,” not proof that no private or subsequently published checkpoint exists. This is a broad targeted review, not a claim that every possible related publication has been exhausted.

## Sources

[^1]: He et al., *Language Models as Hierarchy Encoders*, NeurIPS 2024: [paper, version 3](https://arxiv.org/html/2401.11374v3), especially §§3–4 and Tables 2–3.
[^2]: [HiT repository](https://github.com/KRR-Oxford/HierarchyTransformers); [MPNet checkpoint](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun); [actual encoder configuration](https://huggingface.co/Hierarchy-Transformers/HiT-MPNet-WordNetNoun/blob/main/config.json); [MiniLM-L12 checkpoint](https://huggingface.co/Hierarchy-Transformers/HiT-MiniLM-L12-WordNetNoun); [evaluation/calibration implementation](https://github.com/KRR-Oxford/HierarchyTransformers/blob/main/scripts/evaluation/hit/eval_hit.py).
[^3]: Labbé et al., *Hierarchy-Aware Hyperbolic and Semantic Reranking for Ontology-Based Phenotype Linking*, BioNLP 2026: [paper](https://aclanthology.org/2026.bionlp-1.5.pdf), Table 2 and §6.2; [checkpoint](https://huggingface.co/labbeth/HiT-all-MiniLM-L12-v2-hpo); [span-detection prompt](https://github.com/labbeth/HyperRAG/blob/main/prompts/span_detection.txt). Main and appendix absolute metrics differ; the values quoted here are from the main table.
[^4]: Wang and Li, *Relational Sentence Embedding for Flexible Semantic Matching*, RepL4NLP 2023: [paper](https://aclanthology.org/2023.repl4nlp-1.20.pdf).
[^5]: [RSE repository and checkpoint list](https://github.com/BinWang28/RSE); [ten-relation BERT-base model](https://huggingface.co/binwang/RSE-BERT-base-10-relations); [weight-file metadata](https://huggingface.co/api/models/binwang/RSE-BERT-base-10-relations); [independent encoding and relation-vector implementation](https://github.com/BinWang28/RSE/blob/main/rse_src/inference.py).
[^6]: Moreira et al., *Native Hierarchical and Compositional Representations with Subspace Embeddings*, KDD 2026: [latest paper](https://arxiv.org/html/2508.16687v2), §§3–5 and Appendix D. The original 2025 preprint used “Logical and Hierarchical” in its title.
[^7]: [Subspace implementation and training instructions](https://github.com/gabmoreira/subembed); [independent text encoder](https://github.com/gabmoreira/subembed/blob/main/model.py); [NLI training and checkpoint-writing code](https://github.com/gabmoreira/subembed/blob/main/train_nli.py).
[^8]: Yoda et al., *Sentence Representations via Gaussian Embedding*, EACL 2024: [paper](https://aclanthology.org/2024.eacl-short.36.pdf), especially §2.4 and Tables 1–4.
[^9]: [GaussCSE repository](https://github.com/yoda122/GaussCSE); [author model metadata](https://huggingface.co/api/models/yoda122/gausscse); [training implementation](https://github.com/yoda122/GaussCSE/blob/master/src/main.py).
[^10]: Oda et al., *Representing Sentence Interpretations with Overlapping Box Embeddings*: [primary manuscript](https://openreview.net/pdf/3df07ed17593840877b30d2a364763122adfc66e.pdf); [IEEE Access publication](https://doi.org/10.1109/ACCESS.2026.3691815); [author publication record](https://www.jaist.ac.jp/~kshirai/publications.html). Detailed method checks used the accessible manuscript and released code, not an assumed identical final PDF.
[^11]: [GumbelCSE model code](https://github.com/iehok/GumbelCSE/blob/main/src/models.py); [training configuration](https://github.com/iehok/GumbelCSE/blob/main/scripts/train_gumbelcse.sh).
[^12]: *Prompt2Box*, [version 3, September 4, 2026](https://arxiv.org/html/2603.21438v3). Version matters: this review uses its revised data mixture and evaluations.
[^13]: [Advertised Prompt2Box encoder repository](https://github.com/zawedcvg/box_embeddings), unavailable when checked; [accessible website repository](https://github.com/zawedcvg/P2B).
[^14]: [MPNet sentence-embedding pretraining](https://huggingface.co/sentence-transformers/all-mpnet-base-v2); [MiniLM-L12 sentence-embedding pretraining](https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2); [BERT model card](https://huggingface.co/google-bert/bert-base-uncased); [official BERT release](https://github.com/google-research/bert); [RoBERTa model card](https://huggingface.co/FacebookAI/roberta-base); [official RoBERTa release](https://github.com/facebookresearch/fairseq/tree/main/examples/roberta).
[^15]: *HypRAG*, [paper](https://arxiv.org/html/2602.07739v2); [author project](https://graph-and-geometric-learning.github.io/projects/hyprag). Main and appendix retrieval tables should not be casually combined as one configuration.
[^16]: [HypRAG training repository](https://github.com/Graph-and-Geometric-Learning/HypRAG).
[^17]: *Hyper3-CLIP*, [August 2026 paper](https://arxiv.org/html/2608.29313v1), especially text–text entailment training and prompt-sensitivity results.
[^18]: [Paper-checkpoint card](https://huggingface.co/hyper3labs/hyper3-clip); [separate v1 card](https://huggingface.co/hyper3labs/hyper3-clip-v1); [v1 file listing](https://huggingface.co/hyper3labs/hyper3-clip-v1/tree/main); [repository](https://github.com/Hyper3Labs/hyper3-clip). The repository's checkpoint paragraph describes an earlier artifact and is not reliable evidence for the separate v1 training objective.
[^19]: [BoxTaxo primary paper](https://www.ijcai.org/proceedings/2024/0934.pdf); [implementation](https://github.com/songjiang0909/BoxTaxo); [PEB-TAXO paper](https://link.springer.com/article/10.1007/s11063-024-11575-3); [PEB-TAXO linked repository](https://github.com/lizaozhou/PEB-TAXO).
[^20]: [ProtoBox paper](https://aclanthology.org/2024.repl4nlp-1.1.pdf); [implementation](https://github.com/iehok/ProtoBox).
[^21]: [HiM, version 3](https://arxiv.org/html/2505.18973v3); [code showing random initialization](https://github.com/BerryByte/HiM/blob/main/src/HIM_l.py); [HELM paper](https://arxiv.org/html/2505.24722v2); [HELM release](https://github.com/Graph-and-Geometric-Learning/helm); [Hyperbolic BERT code](https://github.com/thunlp/hyperbolic_llm). The IEEE Hyperbolic BERT full text was inaccessible, so its assessment is limited to inspected release code.
[^22]: [DualCSE paper](https://aclanthology.org/2026.findings-eacl.74.pdf); [code](https://github.com/iehok/DualCSE); [INLI training-data schema](https://github.com/google-deepmind/inli).
[^23]: [Order Embeddings paper](https://arxiv.org/pdf/1511.06361); [legacy implementation](https://github.com/ivendrov/order-embedding); [entailment cones](https://proceedings.mlr.press/v80/ganea18a.html); [ConE project](https://snap.stanford.edu/cone/); [MERU release](https://github.com/facebookresearch/meru).
[^24]: [HierPrompt, EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.207/); [hierarchy-aware text classification, ACL 2022](https://arxiv.org/abs/2203.03825). These are adjacent supervised classification methods, not direct replacements for arbitrary-text broader–narrower encoders.
[^25]: Alper and Averbuch-Elor, *Emergent Visual-Semantic Hierarchies in Image–Text Representations*, ECCV 2024: [paper](https://arxiv.org/html/2407.08521v2); [author project and dataset description](https://tau-vailab.github.io/hierarcaps/).
[^26]: [HierarCaps training/scoring code](https://github.com/TAU-VAILab/hierarcaps/blob/main/code/train.py); [CLIP-B checkpoint](https://huggingface.co/malper/hierarcaps-clip-b); [CLIP-L checkpoint](https://huggingface.co/malper/hierarcaps-clip-l); [CLIP paper](https://proceedings.mlr.press/v139/radford21a.html). Checkpoint metadata was inspected without downloading weights.
[^27]: [TaSe / HiVG, latest August 31, 2026 manuscript](https://arxiv.org/html/2509.24192v3); [linked empty repository](https://github.com/ssojungan/tase); [H²em paper](https://arxiv.org/html/2512.20029v1).
