# Semantic Region Discovery and Labeling

## Status

This is a literature review, not an architecture decision. It compares
corpus-wide, dynamic, and hybrid methods without assuming that semantic regions
must be permanent.

## Question

How can public Nostr notes be presented as understandable semantic regions that
a person can deliberately navigate?

The system may need to:

- produce useful region choices;
- describe those choices accurately;
- allow a note to contribute to more than one region;
- distinguish genuinely different choices;
- cover unfamiliar areas rather than merely reorganize the current
  neighborhood.

It does **not** follow that the system needs one permanent, authoritative set of
subjects.

## Minimum Requirement

When the interface offers navigation choices, it needs a finite set of region
descriptions and a defensible mapping from notes to those regions. That set may
be:

- precomputed for the whole corpus;
- generated from the current context;
- assembled dynamically from reusable corpus-wide structure.

The persistent requirement is reliable behavior, not persistent subject names.

## What the Literature Shows

### Dynamic regions have retrieval precedents

[Scatter/Gather](https://people.ischool.berkeley.edu/~hearst/papers/sg-sigir96/sigir96.html)
clusters the currently retrieved documents and describes each cluster with
topical terms and representative titles. The cluster boundaries therefore
change with the input rather than coming from a global taxonomy. In its user
study, participants selected the cluster containing the most relevant
documents in 31 of 38 usable cases. This was a four-person study, participants
could select several clusters, and the authors treated the result as indirect
evidence rather than a decisive evaluation.

[Grouper](https://www.sciencedirect.com/science/article/pii/S1389128699000547)
similarly creates
overlapping, phrase-labeled clusters after retrieval. It was designed around
the assumptions that documents may have several topics and that result-specific
clusters can be more useful than corpus-wide boundaries.

[Dynamic Facet Selection](https://aclanthology.org/2021.internlp-1.5/) derives
the facet-to-document mapping at query time instead of indexing a fixed facet
list. Its experiments found that the generated facets improved result ranking.

[Knowledge Navigator](https://aclanthology.org/2024.findings-emnlp.516/)
combines clustering and an LLM to turn the papers retrieved for a broad query
into a named two-level hierarchy. Users can then select a subtopic and continue
exploring.

These systems show that dynamic grouping is technically viable in retrieval
interfaces. They do not establish its fitness for corpus-wide Nostr navigation,
but they do show that a permanent subject inventory is not a logical
prerequisite. They share an important boundary:

> A dynamic method can only organize the notes supplied to it.

If its input is a narrow `similar_notes` neighborhood, it can give that
neighborhood better names but cannot reveal disconnected regions elsewhere in
the corpus. Dynamic generation does not by itself solve thematic jail.

### Corpus-wide structure is also credible

[LDA](https://www.jmlr.org/papers/v3/blei03a.html) represents each document as
a distribution over corpus-wide topics rather than assigning exactly one
topic. Contextual topic models such as
[CombinedTM](https://aclanthology.org/2021.acl-short.96/) add document
embeddings to this mixed-membership approach.
[TENOR](https://aclanthology.org/2024.eacl-long.51/) evaluated several topic
models through a 60-person label-induction study and an expert pilot. Its
CombinedTM configuration was more useful for that task than the tested LDA,
BERTopic, and embedded-topic-model configurations, even though automatic
coherence metrics suggested different winners. The corpora were not short
social posts, so this is evidence for human usefulness rather than direct Nostr
validation.

Simple clustering of contextual document embeddings can be competitive with
more elaborate neural topic models.
[Zhang et al.](https://aclanthology.org/2022.naacl-main.285/) found that direct
clustering beat or matched the neural topic models they tested on automatic
coherence and diversity metrics while being simpler and more efficient. Those
metrics did not establish human navigation quality.

[FASTopic](https://proceedings.neurips.cc/paper_files/paper/2024/hash/998f8d8ff2697da2eae5f87143668754-Abstract-Conference.html)
learns topic prototypes over frozen document embeddings and returns soft
note-to-topic weights. It is a direct modern candidate for reusable public
structure. However, its topic count is chosen in advance, it materializes
document-to-topic relations, it was tested only up to 40,000 documents, and it
did not include a human study.

A particularly relevant large-scale short-text study
[learned word-embedding topics from a corpus of 178 million tweets and could
infer a soft distribution for an individual tweet](https://aclanthology.org/W15-1526/).
This demonstrates that reusable, soft structure can be learned at social-post
scale. It did not compute or store distributions for all 178 million tweets,
its representation is now technically dated, and its human evaluation tested
topic-word coherence rather than note assignment or navigation.

Corpus-wide structure offers stable availability across the corpus and avoids
recomputing the entire map for every interaction. It does not guarantee
semantic coverage: rare or low-density meanings can still be merged or
omitted. Its subjects and granularity are model-dependent, and the literature
does not establish one objectively correct global partition.

A global structure also need not consist of unnamed latent topics.
[Scaiella et al.](https://research.google.com/pubs/archive/37745.pdf) mapped
short snippets to several weighted Wikipedia concepts, clustered the resulting
concept graph, and used Wikipedia titles as descriptions. This supplies
readable, multi-label anchors, but inherits the external ontology's omissions
and biases. It may be especially weak for emerging or Nostr-specific ideas.

### A mixed-membership score is not proof of multiple meanings

A note may discuss Rust and Bitcoin at the same time. There are several ways to
represent this:

- probabilistic topic models return several topic weights for the whole note;
- independent concept scorers can assign the note to several regions;
- token- or span-level methods can associate different portions of the note
  with different meanings;
- an LLM can propose several assignments and cite the text supporting each
  one.

Whole-note soft weights are useful, but they are ambiguous. Two high weights
may mean that the note truly expresses two subjects, or merely that the model
is uncertain which single subject fits.

The word *strength* is also underspecified. A topic proportion, classifier
score, and embedding similarity describe different quantities and are not
automatically comparable across regions. Any proposed membership strength must
state what it means and be calibrated against human assignments.

[Contextual token clustering](https://arxiv.org/abs/2010.12626) and
[Contextual-Top2Vec](https://aclanthology.org/2024.findings-emnlp.790/) address
this more directly by deriving topics from contextual token representations.
This makes separate meanings representable and auditable at the token or span
level, but does not prove that they match a person's interpretation. It costs
more than reusing one vector per note and has not been demonstrated at the
scale of the complete Nostr corpus.

[TopicGPT](https://aclanthology.org/2024.naacl-long.164/) generates open-ended
topic descriptions and assigns a topic with a supporting quotation. It can be
prompted to assign more than one topic, but that capability received only a
five-example follow-up analysis; the paper does not establish calibrated
multi-topic strengths. Its main results aligned with human categories better
than the tested LDA and BERTopic baselines, but its authors still found
missing, repeated, and poorly scoped topics. The demonstrated frontier-model
assignment also has an unattractive cost and reproducibility shape for the
complete corpus.

[LLooM](https://hci.stanford.edu/publications/2024/Lam_LLooM_CHI24.pdf)
generates concepts with names, inclusion criteria, representative examples,
and independent membership scores. It is close to the desired open-ended,
overlapping representation, but its experiments induced at most 20 concepts
from samples of roughly 200 items. Its reported mean recall and F1 were about
0.59 and varied substantially by concept. It does not establish corpus-wide
short-note performance. Fluent descriptions remain proposals, not facts.

### Labels are a separate problem

Discovering a group does not automatically produce a faithful description of
it.

The strongest recurring grounding mechanisms are:

- topical terms plus representative documents, as in Scatter/Gather;
- extracted phrases, as in Grouper;
- an explicit inclusion rule plus examples, as in LLooM;
- a quotation supporting each note-to-topic assignment, as in TopicGPT.

[Smith et al.](https://aclanthology.org/Q17-1001/) found that automatic topic
labels lagged human labels and validated labels against the documents they were
supposed to describe. From that evidence, a sensible project safeguard is to
show representative notes or supporting text with each label rather than ask
the user to trust plausible wording alone.

Stochastic generation, changing inputs, or changing context can cause
on-demand labels to change between runs; deterministic generation over
identical input need not. Until stability is measured, generated labels are
better treated as disposable navigation descriptions than canonical facts
about the corpus.

### Human validation is indispensable

Automatic topic metrics do not establish that a region is understandable or
useful.

[Reading Tea Leaves](https://proceedings.neurips.cc/paper_files/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html)
showed that held-out likelihood can favor topics that people find less
interpretable. A later
[evaluation of automated coherence](https://proceedings.neurips.cc/paper/2021/hash/0f83556a305d789b1d71815e8ea4f4b0-Abstract.html)
found that automatic metrics could declare model winners that human judgments
did not support.

Our evaluation must test the claims the interface actually makes:

1. **Coherence:** do held-out random and boundary notes in a region belong
   together?
2. **Assignment:** does a held-out note genuinely belong to every region and
   membership strength claimed for it?
3. **Label fidelity:** does the description accurately predict held-out notes,
   including notes away from the cluster center?
4. **Distinctness and granularity:** are two displayed choices meaningfully
   different, and are they divided at a level useful for navigation?
5. **Input coverage:** does the finite input used to form regions represent
   rare and disconnected areas of the broader corpus?
6. **Assignment coverage:** do sampled notes from that input have at least one
   faithful region, including deliberately mixed notes?
7. **Stability:** with the same or slightly changed input, do boundaries and
   descriptions remain understandable rather than changing arbitrarily?
8. **Navigation:** after selecting only a description and its representative
   notes, does the person receive the kind of content they expected?

Automated coherence, diversity, and clustering scores may screen obviously bad
configurations. They cannot decide success.

## Approach Comparison

| Approach | Strength | Central limitation |
| --- | --- | --- |
| Global hard clustering | Simple, reusable, stable | Forces a mixed note toward one region and fixes granularity |
| Global soft topics | Reusable graded membership and corpus-wide scope | Topic count and meanings remain model-dependent; forced weights do not prove faithful coverage; soft weights may only express uncertainty |
| Dynamic clustering or facets | No permanent taxonomy; fits the current context | Cannot expose content absent from its input and may produce unstable boundaries |
| Dynamic LLM concepts | Natural descriptions and open-ended overlap | Cost, nondeterminism, model bias, and confidently wrong mappings |
| Global geometry with dynamic regions | Separates corpus coverage from user-facing descriptions | Promising synthesis, but adds machinery and is not yet validated |

## Fit to This Project

Nostr kind-1 notes are short, informal, rapidly changing, and often contain
several ideas. The corpus is large enough that assigning every note with a
frontier LLM is the wrong first move.

The current public embedding matrix and index already contain reusable vectors
for the corpus. Their geometry was selected for semantic retrieval, not
human-interpretable region discovery. Whether it preserves the structure needed
for this new task is an unresolved prerequisite.

A hybrid is one credible hypothesis:

1. Preserve public corpus-wide geometry or another broad coverage mechanism.
2. Generate a small set of overlapping region proposals when navigation is
   requested.
3. Generate those proposals from input intended to include unexplored and
   disconnected areas, not only the current nearest-neighbor pool.
4. Describe each proposal with a short label, a more precise inclusion
   description, and representative notes.
5. Combine those public proposals with private preference evidence locally.

How to choose a finite input that actually represents rare and disconnected
areas of millions of notes is itself unresolved. A full embedding matrix does
not solve that selection problem.

Other unresolved parts include how density-based methods avoid erasing
long-tail areas and how the local personalizer orders public region proposals
against private positive evidence.

This hybrid is a research-backed candidate, not an approved architecture or a
demonstrated winner. A simpler global map could win, and a dynamic-only method
could prove sufficient.

## Conclusion

The literature does not establish a permanent subject inventory as necessary.
It supports both precomputed and dynamic methods. A hybrid cleanly separates
corpus-wide scope from user-facing descriptions, but no reviewed study
establishes that it is better for this goal.

The unresolved question is empirical:

> Which construction—corpus-wide, dynamic, or hybrid—best produces coherent,
> distinct, accurately described, overlapping region choices from broad Nostr
> input that people can navigate as expected?

The smallest useful follow-up would construct representative methods from
those families on the same Nostr sample, then compare them on separate
held-out notes with the same human tasks. No complete navigation system should
be built before this prerequisite is demonstrated.
