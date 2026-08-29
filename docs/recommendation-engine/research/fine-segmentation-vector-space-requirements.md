# Fine-Segmentation Vector-Space Requirements

## Status

This document records the method-independent properties of the vector-space
problem. It does not select a fine-segmentation algorithm or define what its
output memberships must look like.

Its purpose is to provide a common basis for evaluating CkNN and other
candidate methods without turning any candidate's assumptions into system
requirements.

## Problem Boundary

The fine-segmentation algorithm receives a finite collection of opaque vector
IDs and 768-dimensional SSE vectors representing atomic subjects. It receives
no note text, masks, subject descriptions, labels, authors, or expected
relationships.

For now, each SSE vector is normalized to length one. The working geometry is
therefore angular: cosine similarity, or the equivalent Euclidean chord
distance between normalized vectors.

## Known Properties of the Point Cloud

Any candidate method must contend with the following properties.

### 1. High dimensionality

The points inhabit 768-dimensional space. Pairwise distances may concentrate,
and some vectors may become hubs near many other vectors.

### 2. Highly unequal and potentially abrupt density

Some portions of the point cloud contain many observations while others
contain few. Density may change sharply because corpus prevalence is not a
smooth sampling process.

### 3. Non-independent sampling

Multiple atomic subjects may come from one note. The corpus also contains
repeated authors, copied notes, and near-duplicates. The vectors therefore
cannot be assumed to be independent samples.

### 4. Unknown geometric structure

We have not established that the points form smooth manifolds, convex clouds,
spheres, density modes, or any other particular shape.

### 5. Unknown number and scale of structures

We cannot supply a correct region count in advance. Small structures and much
larger structures may coexist.

### 6. Sparse and isolated observations

Some portions of the point cloud may contain only one or two observed vectors.
Their nearest available vectors may still be absolutely distant.

### 7. Arbitrary coordinate orientation

Individual embedding axes have no established meaning. An orthogonal rotation
or reflection that preserves all pairwise geometry must not change the result.

## Assumptions That Are Not Established

A candidate method must not receive privileged status from theory that requires
any of the following unless we first establish that the requirement holds for
our vectors:

- independent sampling;
- smoothly varying density;
- one smooth underlying manifold;
- equal density, size, or local dimensionality;
- convex or spherical regions;
- a fixed number of regions;
- exhaustive assignment of every point;
- non-overlapping regions; or
- nearest-neighbor connectivity being sufficient to define a region.

Whether the output should be exhaustive, overlapping, non-overlapping, hard,
or weighted remains unresolved. Those are output-contract decisions, not known
properties of the vector-space problem.

## Use in Candidate Evaluation

For each candidate method, evaluate:

1. which geometric and sampling assumptions it requires;
2. which known point-cloud properties it handles directly;
3. how it fails when its assumptions do not hold;
4. which parameters or prior choices it introduces; and
5. whether its claimed guarantees actually apply to this input.

CkNN is one candidate heuristic. Its manifold-consistency result does not, by
itself, establish suitability here because independent sampling and smoothly
varying manifold density are not known properties of this point cloud.
