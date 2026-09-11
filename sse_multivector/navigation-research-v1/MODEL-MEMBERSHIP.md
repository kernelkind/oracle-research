# Learned description membership

The entailment classifier recognizes several broad subjects that literal matching
misses, but also confuses a statement about morning coffee with a greeting.
A query/passage relevance model does not resolve the problem: for Coffee it ranks
the mask `Good morning` above two masks explicitly discussing coffee.
Neither experiment constructs a hierarchy or establishes a membership rule.
The original browser and ND02-NP01 remain unchanged.

## Research question

MDH02 can connect Bread to Sourdough bread through shared words, but cannot supply
unwritten broader descriptions or reliably separate word senses. The next question
is whether a released language model can match a proposed description to the
meaning of a mask. This is a component test, not a replacement objective: useful
membership evidence must eventually support complete, meaningful browsing paths.

Conceptual indexing supplies a relevant precedent: Woods combines parsed phrases,
lexical knowledge and subsumption relations rather than inferring meaning from
document overlap alone. Its existing lexicon and morphological rules are substantial
resources, not something this experiment recreates.[^1]

TaxoLLaMA offers a learned route to broader-term proposals through WordNet-based
training. However, its error analysis reports overly broad predictions and missing
middle-level connections; changing a perplexity threshold can introduce wrong
edges. Lexical type relations are also not the full range of useful browsing
refinements. It remains a candidate proposal mechanism, not a verified hierarchy
constructor for these notes. No TaxoLLaMA model was run here.[^2]

Entailment-based zero-shot classification converts a category into a hypothesis
sentence and scores it against the input text.[^3] That is a plausible cheap
membership component, but published follow-up work finds substantial task and
training variation: good NLI benchmark performance does not guarantee good
classification. Improving robustness on one entailment test did not consistently
improve the target classification tasks.[^4] Those results concern different
models; they motivate testing, not a verdict about the model below.

## NLI01: fixed masks and descriptions

**Hypothesis:** A pretrained classifier recognizes source-supported broader
subjects and rejects misleading shared words on these examples.

The model is `MoritzLaurer/deberta-v3-base-zeroshot-v2.0`, revision
`8e7e5af5983a0ddb1a5b45a38b129ab69e2258e8`, with 184,423,682 parameters.
It is a DeBERTa-based encoder classifier, not a generative agent or SSE. Its
released training combines synthetic classification tasks and entailment data;
the exact version's training description is in the author model card.[^5]
No training or prompt tuning took place locally.

For each pair, the model receives:

- First text: exact mask fragments joined by one space, in source order.
- Second text: `This text is about {description}`.

The original note and generated subject are saved for inspection but are not
model inputs. Consequently this does not test SSE's full-note contextual
encoding. Each score is the model's binary entailment softmax for that pair,
independent of the other descriptions. It is **not cosine similarity or a
calibrated probability of category membership**.

Twelve real masks from eleven distinct notes were compared with nine descriptions:
art, technological advancement, morning greetings, coffee, bread, sourdough bread,
food, price increases and physical exercise. All 108 pairs are saved, including
unfavorable results. The fixture was fixed before inference.

| Mask ID | Note | Exact mask fragments |
| --- | --- | --- |
| V224 | N027 | ⟦CombiCookTop V4000 I804⟧ ⟦one of V-Zug's most state-of-the-art products⟧ |
| V377 | N048 | ⟦art⟧ |
| V486 | N058 | ⟦GM Nostr⟧ |
| V120 | N017 | ⟦Good morning⟧ |
| V494 | N058 | ⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧ |
| V321 | N041 | ⟦I don't feel I need⟧ ⟦coffee to start living today⟧ |
| V107 | N015 | ⟦sourdough bread⟧ |
| V658 | N072 | ⟦Irish soda bread recipe⟧ ⟦I tried⟧ ⟦recently⟧ |
| V786 | N085 | ⟦Brisket on the smoker⟧ |
| V519 | N062 | ⟦Aussies' Christmas lunch costs rise⟧ |
| V114 | N016 | ⟦by mid-day i⟧ ⟦consumed half a pound of chocolate⟧ ⟦starting to make me sick⟧ |
| V620 | N069 | ⟦Work out in zone 2 as much as you can.⟧ |

These IDs identify existing masked inputs, not newly generated vectors.
[All scores and complete original records](./NLI01/scores.json),
[fixed fixture](./NLI01/fixture.json), [configuration](./NLI01/config.json).

**Observed useful behavior:**

| Mask | Description | Score |
| --- | --- | ---: |
| V224, advanced appliance | technological advancement | 0.941329 |
| V224, advanced appliance | art | 0.000650 |
| V377, art tag | art | 0.987038 |
| V107, sourdough bread | sourdough bread | 0.993537 |
| V107, sourdough bread | bread | 0.989833 |
| V107, sourdough bread | food | 0.999225 |
| V658, soda-bread recipe | bread | 0.994881 |
| V658, soda-bread recipe | sourdough bread | 0.000214 |
| V786, smoking brisket | food | 0.999036 |
| V519, lunch costs rising | price increases | 0.983005 |
| V114, chocolate consumption | food | 0.998818 |
| V620, zone-2 workout | physical exercise | 0.999275 |

The sourdough example supports matching broader meanings; it does not prove
automatic construction of a Food → Bread → Sourdough path. Those descriptions
were supplied manually for this diagnostic. The art tag establishes recognition
of the selected word, not that the complete Tolstoy quote substantively discusses
art. Food support for an advanced kitchen appliance is a scope question, not
automatically an invalid classification.

**Counterevidence:** V486 receives only 0.008920 for morning greetings, below
technological advancement at 0.117907. V321 receives only 0.038406 for Coffee.
V494 receives 0.814089 for morning greetings although its mask only concerns
hot coffee in the morning. N058 actually has a separate greeting mask, so this
last error is wrong mask evidence, not an additional wrong note in a greeting
destination. All original notes were inspected to make that distinction.

The fourteen predeclared relative checks are all positive. That is not fourteen
successful memberships: comparing GM with an obviously unrelated description
conceals its very low greeting score and its higher wrong-description score.
No complete gold matrix, threshold, precision estimate or holdout claim is made.

## NLI02: isolate the suspicious effects

The same model and hypothesis sentence were retained. Three original masked
inputs were compared with four explicitly synthetic interventions. These are not
revised real notes, approved masks or a held-out sample.

The original N058, shared by V486 and V494, is:

> GM Nostr!
>
> Happy Sunday!
>
> Woke up to 35 degress today---brrr. It'll warm up, but fall is definitely here.
>
> Glad the coffee is hot this AM!
>
> #coffeechain

The original N041, containing V321, is:

> I think I got grasp on that fog/clarity meat eaters often mention.
> I fell asleep with the kids, very tired and kind of cold. Woke up at five and my brain was started.
> I don't feel I need a coffee to start living today. Fog is lifted and all.
> It might be just a good sleep, but I've had a very good sleep last days. Usually I'm up like three times, now I just sleep like a bear.
> #fasting #keto #carnivore

| Input | Exact text sent as the first text | Greeting score | Coffee score |
| --- | --- | ---: | ---: |
| V486 | GM Nostr | 0.008920 | 0.000080 |
| CF-GM | Good morning Nostr | 0.997543 | 0.001512 |
| V321 | I don't feel I need coffee to start living today | 0.006175 | 0.038406 |
| CF-NEED | I feel I need coffee to start living today | 0.052036 | 0.575756 |
| V494 | coffee hot this AM | 0.814089 | 0.974478 |
| CF-AM | The coffee is hot this morning. | 0.612640 | 0.972891 |
| CF-PM | The coffee is hot this afternoon. | 0.009230 | 0.980495 |

Expanding GM restores greeting recognition. Removing negation increases Coffee
support despite both inputs concerning coffee. Restoring grammar reduces but
does not eliminate the greeting interpretation; replacing morning with afternoon
removes most of it while Coffee support stays similar. These isolate behavior
on these inputs, not a universal causal explanation of the model's training.

For the fixed greeting description, a cutoff cannot both admit V486 at 0.008920
and exclude the nongreeting CF-AM at 0.612640. The problem therefore cannot be
removed by adjusting only that cutoff. Six of seven relative checks are positive;
again this is not a membership accuracy result.

[All 21 scores and original/synthetic records](./NLI02/scores.json),
[intervention fixture](./NLI02/fixture.json),
[separate intervention evidence](./nli02-evidence.json).

## RER01 and RER02: query/passage relevance

**Hypothesis:** A relevance model better preserves topic membership despite
negation and rejects loose associations on these fixed examples.

`BAAI/bge-reranker-v2-m3`, revision
`953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, has 567,755,777 parameters.
This is an XLM-RoBERTa sequence classifier initialized from BGE-M3. The author
interface takes a query and passage and returns a relevance logit; it does not
produce an embedding. The comparison follows that interface with the description
as query and joined fragments as passage.[^6] The linked older reranker training
recipe is not evidence of this exact checkpoint's full training-data mixture.

All 108 NLI01 pairs become RER01, and all 21 NLI02 pairs become RER02. No examples
are removed and no descriptions are changed. The NLI hypothesis sentence and
previous scores are not model inputs. Raw logits and their independent sigmoid
transforms are saved; the sigmoid is not calibrated membership confidence.
This changes the complete model, not only its training objective, so causal
claims about NLI training versus relevance training would be unjustified.

**Same Coffee query, different masked inputs:**

| Mask | Relevance sigmoid score |
| --- | ---: |
| V120: ⟦Good morning⟧ | 0.493458 |
| V494: ⟦coffee⟧ ⟦hot⟧ ⟦this AM⟧ | 0.131592 |
| V321: ⟦I don't feel I need⟧ ⟦coffee to start living today⟧ | 0.001090 |

The exact masked input `Good morning` ranks above both explicit coffee meanings.
No cutoff on this query's scores can retain those two and reject that mask.
N017's original does contain `#coffeechain`, which the model never received;
this distinction prevents claiming an unrelated whole-note admission from this
mask-level counterexample. The original is:

> Good morning, crushed a solid gym session this morning to kick off the weekend. Now time for a late breakfast! #coffeechain

For the fixed Food query, `Good morning` also scores 0.025917, above smoking
brisket at 0.002018 and the soda-bread recipe at 0.001118. Both latter masked
inputs plainly concern food. This demonstrates bad within-query ordering,
without pretending scores are comparable across differently phrased queries.

**Controlled interventions under the relevance model:**

| Input | Greeting score | Coffee score |
| --- | ---: | ---: |
| V486 | 0.000054 | 0.000220 |
| CF-GM | 0.953362 | 0.075867 |
| V321 | 0.000222 | 0.001090 |
| CF-NEED | 0.003900 | 0.186273 |
| V494 | 0.022713 | 0.131592 |
| CF-AM | 0.010097 | 0.669030 |
| CF-PM | 0.000022 | 0.593830 |

GM still needs expansion; removing negation still increases Coffee support.
Grammatical coffee sentences receive stronger Coffee support than the fragment
sequence. Morning remains associated with greetings, though less strongly than
in NLI02. Absolute cross-model score changes are not calibrated improvements;
the within-model wrong orderings are the clearer evidence against adoption.

Other useful behaviors remain: the bare art mask and explicit Good morning
receive strong support for their respective descriptions, and exact sourdough
text matches Sourdough bread strongly. These do not cancel the counterexamples.
All 129 outputs were inspected, rather than only the earlier relative checks.

[RER01 complete results](./RER01/scores.json),
[RER02 complete results](./RER02/scores.json),
[frozen comparison hypothesis](./relevance-fixture.json).

## What this establishes

Learned text models can supply some broader semantic recognition absent from
literal matching. Neither tested configuration is a validated automatic
membership rule. These experiments do not establish that all classifiers or
rerankers will fail, nor that occasional errors are unacceptable. They identify
specific wrong orderings which a threshold adjustment cannot fix.

No parent was generated or accepted, no existing category gained notes, and no
complete browsing path improved in these runs. Candidate-description generation,
membership verification and semantic parentage remain separate unresolved work.
Taxonomy-generation research may inform the first; the current classifier scores
must not silently become the definition of the latter two. Further work should
not require perfect classification before testing construction, but any use of
these scores must retain and audit their known counterexamples.

The next construction-focused diagnostic can retain the automatically obtained
MDH02 descriptions and their exact source memberships, then test directional
relations between those descriptions. This would isolate proposed parentage
from membership expansion, use no hand-created taxonomy and expose whether
learned generalization adds useful relationships beyond literal inclusion.
Mutual similarity must not be treated as narrowing, and every proposed edge
must be inspected against the complete child masks and notes. The current
classifier's score alone cannot certify that relation. This is a research
question to investigate, not an adopted graph-building rule.

## Reproduction and verification

Each run pins model revision, downloaded model-file hashes, source hashes,
input hashes and installed package versions. All inference used CPU, two Torch
threads, one interop thread, FP32 and batches of four. Inputs exceeding 512
tokens are rejected rather than silently truncated. Downloaded safetensors are
loaded without remote model code. No paid API call, remote compute or training
was used. Public model weights remain outside Git.

| Run | Pairs | Inference seconds | Peak process memory, GiB |
| --- | ---: | ---: | ---: |
| NLI01 | 108 | 3.229 | 4.796 |
| NLI02 | 21 | 0.676 | 4.795 |
| RER01 | 108 | 4.803 | 4.795 |
| RER02 | 21 | 0.967 | 4.795 |

Timings exclude loading/download and artifact serialization. They are small-run
measurements, not a large-corpus throughput forecast. Configurations preserve
separate loading times and exact peak-memory values.

Using the existing local environment, from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export LD_LIBRARY_PATH=/nix/store/8lahnh9pn3lrrnhax5nk7ibvjcbjmnkm-gcc-15.2.0-lib/lib:/nix/store/b2swxfi8srrbsafvh9iyyhd26mz9giwf-zlib-1.3.2/lib

/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/NLI01/mask_description_nli.py \
  --evidence sse_multivector/geometric-hierarchy-v1/GDC09/evidence.json \
  --fixture sse_multivector/navigation-research-v1/NLI01/fixture.json \
  --output /tmp/nli01-reproduction --cache /tmp/oracle-nli-model-cache

/tmp/oracle-nli-probe-venv/bin/python \
  sse_multivector/navigation-research-v1/RER01/mask_description_relevance.py \
  --input sse_multivector/navigation-research-v1/RER01/input.json \
  --fixture sse_multivector/navigation-research-v1/RER01/fixture.json \
  --output /tmp/rer01-reproduction --cache /tmp/oracle-nli-model-cache
```

Choose nonexistent output directories. NLI02 uses its own saved runner/fixture
and `nli02-evidence.json`; RER02 uses its own saved runner/input/fixture.
The environment uses Python 3.11, Torch 2.8.0+cpu, Transformers 4.57.1,
NumPy 2.3.4, SentencePiece 0.2.1 and Safetensors 0.6.2; complete distributions
are in each config. These temporary environment paths are local conveniences,
not permanent external dependencies of the browser.

Saved-source reproductions match score files byte-for-byte. Configurations match
except loading/inference time and peak memory. All source records, pair texts,
raw-logit transformations and provenance hashes were independently checked.
The nine new tests exercise the actual preparation/scoring functions and
overwrite-refusing CLIs; both modules' initial tests failed before implementation.
Together with the existing relevant suites, 68 tests pass. A separate audit agent
could not be started because of the thread limit; verification was performed
locally, not represented as independent semantic consensus.

## Sources

[^1]: W. A. Woods, [Conceptual Indexing: Practical Large-Scale AI for Efficient Information Access](https://cdn.aaai.org/AAAI/2000/AAAI00-215.pdf), 2000. Main text read; a research lead rather than an implemented dependency.
[^2]: V. Moskvoretskii et al., [TaxoLLaMA: WordNet-based Model for Solving Multiple Lexical Semantic Tasks](https://aclanthology.org/2024.acl-long.127.pdf), 2024, methods and §§6–7/limitations. Error analysis and limitations reread for this comparison; no claim to reviewing every appendix. The [2026 extension](https://www.inf.uni-hamburg.de/en/inst/ab/lt/publications/2026-moskvoretskiietal-swj.pdf), relevant training and evaluation sections, was also inspected, not its complete thirty pages.
[^3]: W. Yin, J. Hay and D. Roth, [Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach](https://aclanthology.org/D19-1404.pdf), 2019, relevant method and evaluation sections.
[^4]: T. Ma et al., [Issues with Entailment-based Zero-shot Text Classification](https://aclanthology.org/2021.acl-short.99.pdf), 2021. Main five pages read, including the negative robustness results; not all appendices.
[^5]: M. Laurer, [DeBERTa-v3-base zero-shot v2.0 model card](https://huggingface.co/MoritzLaurer/deberta-v3-base-zeroshot-v2.0), training and usage sections, accessed September 2026. Actual model revision and files are pinned in the experiments.
[^6]: BAAI, [BGE-reranker-v2-m3 model card](https://huggingface.co/BAAI/bge-reranker-v2-m3), author Reranker/Transformers sections, accessed September 2026. The automatically supplied SentenceTransformer embedding snippet at the top is not the reranker interface and was not used.
