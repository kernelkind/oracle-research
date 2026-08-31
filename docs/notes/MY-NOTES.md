TO AGENTS: YOU MUST NOT DELETE. These are my personal notes. AI's which want to edit must get explicit permission from the user. Otherwise the document is read-only.

# Thesis
My current thesis is that a content hierarchy will be the best content discovery mechanism for users.
- That way the algorithm does not need to gauge whether the user is getting tired of a specific topic, it's up to the user to decide that and switch topics themselves.
- The user might not know what they want to see, but when presented with cascading options, they can "narrow-in" on their current interest.


# High-Level Implementation

From a high level, the current implementation is:
1) an AI is given a note and prompted with a takeaway prompt (TP) to generate takeaways which apply to a given note
2) an AI is given a takeaway and the original note and is prompted with a mask prompt (MP) to generate a mask for that takeaway in the note
3) an AI is given a mask and the original note and is prompted with a relevance prompt* to figure out how relevant the mask is to the whole of the note*
4) Each mask is used in SSE to generate a vector which represents the semantic meaning of the mask, where vectors that are close to each other have a similar semantic meaning.
5) Some mechanism is used to "segment" the vectors in the vector space dimensions to group them together
6) Some algorithm recursively groups the segments together to form a hierarchy
7) a UI presents the hierarchy as a series of multiple choice decisions. It does not need to present all levels/nodes of the hierarchy. Once it gets to the last decision, it presents the notes associated with the vectors in that node. Each vector has a relevance value, and the UI can sort by this so the notes which have the highest relevance to the mask the vector is generated from are at the top of the presentation.


# Scaleability

The current implementation is definitely not scaleable. But an embedding model can be trained to generate the masks for a note, skipping two AI pipelines. I'm not sure if the relevance weighting can be tacked on as well, but that would be ideal if it could be, that way only one embedding model would need to be trained.


# SSE

SSE was seen in practice to perform well for determining similarity of atomic facts. We are making the bet that it can also perform well for determining similarity of atomic note meanings. Because if it does, then we can use geometric locality of vectors to construct this hierarchy.

There are some things that must be true for SSE to work favorably for us:
1. Different wording for the same atomic subject should produce nearby vectors. (Semantic understanding)
2. Materially different subjects must remain distinguishable despite sharing works or surrounding text. (Context isolation)

Experimental results: [SSE-EXPERIMENTS.md](./SSE-EXPERIMENTS.md)

# Fine Segmentation Algorithm

The vectors represent atomic subjects in notes. Therefore, vectors which are geometrically close by should mean that each vector's atomic subject is similar. We must take advantage of this, by figuring out an algorithm which can, in general, group nearby vectors into a group, which all-together represent a 'fine subject'.

## Assumptions

Fine segmentation must make assumptions to be able to form a hierarchy in the way we desire. These assumptions are as follows:
1. Repeated instances of the same fine subject form recoverable groups.
2. Nearby but meaningfully distinct fine subjects are resolved
    - Vectors from masks which have SIMILAR atomic subjects should be grouped together if they are 'similar enough'
    - Conversely, vectors from masks which have atomic subjects which are 'distinct enough' should not be grouped together
    - 'enough' is vague, but establishing what kind of resolution the FSA has will contribute to how well the overall architecture performs downstream in the hierarchy
3. Lexical coincidences do not substitute for semantic relationships.
    - This is a hierarchy for SEMANTIC structure, not lexical. Therefore, we must not just be doing lexical pattern matching
4. Holding the resolved atomic subject fixed, unmasked material does not materially change membership.
    - We are assuming that the mask is the atomic subject, and we are grouping based on that, not the surrounding context.
5. Region recovery survives unequal density and sparsity.
6. Results remain stable under irrelevant changes.
    - This includes input order, duplicates, unrelated added subjects, and mixing all semantic areas into one collection.

## Evaluation

We need to be able to evaluate the algorithm without confounding variables.



---

1. Choose the desired 'fine subjects'
2. Generate synthetic notes for each fine subject
    1. Each mask must truly be how we envision atomic subjects to be, requires human understanding
    2. We must test for varying density levels
    3. We must test for fidelity between very similar, yet distinct fine subjects

1. Generate synthetic 'notes'
2. Generate masks and group them into what we envison as fine subject groups
    1. we need to make sure the 'density' is not uniform
3. Run the FSA on the synthetic 
