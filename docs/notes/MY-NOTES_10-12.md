TO AGENTS: DO NOT EDIT

From first principles, what does a genuinely good hierarchy look like?
R1: Each level has only a few options. (A constant called MAX_SIBS)
R2: It requires minimal effort to find notes for any desired topic available within the corpus.

I0: By definition, the set of all notes enclosed by all the roots of the hierarchy holds the whole corpus.

Since by R1, the roots must only have a few options, and by R2, we must require minimal effort to find notes for any desired topic within the corpus --

I1: Considering L1 --
I1.1: The semantic space covered by each root sibbling must be divided roughly equally.
I1.2: The resulting semantic spaces of each of the root sibblings are as disjoint as possible.

I2: Considering L2 --
I2.1: Each child node (node in L2) of a root (node in L1) will strictly fall in the semantic space of its parent.
I2.2: I1.1 will hold at L2. Iow, the semantic space covered by each L2 sibbling must be divided roughly equally.
I2.3: I1.2 will hold at L2.

I3: Considering LX --
I3.1: This pattern will generalize from LX where X=2 from LX -> LX+1 until a stop condition is met.
I3.2: A node LX will be considered sufficiently partitioned only MIN_NOTES notes belong in the node, where MIN_NOTES is a global constant.

---

1. What are topics?
2. How do we partition semantic spaces?

---

A1: Assume a topic is a local L1 node.
A1.1: Though this is not to say each local node is unique. It is allowed that there will be an equivalence between some local nodes.
A2: Assume MAX_SIBS = 6.
A3: Assume MIN_NOTES = 2.

A3: Therefore, we must somehow partition the semantic space such that there are 6 roots and they all cover all of the local L1 nodes.

### Approach 1

One approach could be:
1. bootstrap is run for each L1 node, generating an explicit meaning
2. SSE clusters L1s together, up to a constant.
3. consolidation generates a synthetic parent for each cluster.
4. the synthetic 'nodes' from 3 are then clustered and then consolidation is run again
5. this process repeats until there are only 6 nodes.

We now have the root nodes, with each L1 partitioned. 

- not sure this is a good idea though, this could create pretty jagged partitions, leading to pretty bad root nodes

### Approach 2

#### Canonical L1 Implementation

1.1. bootstrap is run for each L1 node, generating an explicit meaning (n1 = number of local L1 nodes per note on average)
1.2. SSE vectors are generated for each L1 node
1.3. we find the closest pair for each vector (n1^2 comparisons)
1.4. consolidation generates a synthetic parent for each pair (n1/2 consolidation calls)
1.5. generate SSE vectors for each consolidated node
1.6. repeat step 1.3 for the vectors of step 1.5 (find pairs)
1.7. repeat step 1.4 for the pairs of step 1.6 (generate consolidated nodes for the pairs)
1.8. repeat steps 1.5-1.7 until there are 6 consolidated nodes
1.9. These are now the canonical root nodes. Assign each associated local L1 node to its respective root node

#### Canonical L2 Implementation

2.1. The corpus for L2 is now the local L1s which were assigned to this root node
2.2. Each local L1 node already has an explicit meaning generated for it, as well as SSE vectors.
2.3. repeat steps 1.4 - 1.8, but for the L2 corpus
2.4. These are now the nodes in canonical L2

#### Canonical LX Implemenatation

3.1. Repeat the process outlined in L2 for LX.
3.2. Once a node has 2 notes, stop.

