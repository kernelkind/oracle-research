Relative-neighborhood geometry for the pilot.
- For vectors A and B, ask whether another vector lies closer to both. This uses the
- surrounding geometry, rather than judging A–B from one cosine alone. It has already
- been used to expose distinct directions in semantic vector spaces.

# Continuous k-nearest neighbors (CkNN)
Continuous k-nearest neighbors as the scalable baseline.
CkNN adjusts each vector’s neighborhood to its local density instead of forcing every
vector to have the same number or radius of neighbors. It has strong theoretical
support under manifold-sampling assumptions. 

 CkNN asks whether two vectors are close relative to how densely sampled their respective
  neighborhoods are.

  For every vector A, calculate the distance to its kth-nearest vector. Call that A’s local
  spacing.

  Then connect A and B when:

  distance(A, B) < δ × geometric_mean(local_spacing(A), local_spacing(B))

  Consequently:

  - In a dense Bitcoin region, local spacing is small, so two vectors must be very close to
    connect.

  - In a sparsely represented flute-repair region, local spacing is larger, so meaningful
    neighbors may connect across a greater absolute distance.

  Here, k estimates local density; it does not force every vector to have exactly k
  connections. δ controls how permissive the graph is.

  Its weakness is that a sparse semantic boundary can look like one sparse region, causing
  an inappropriate connection.

 Imagine drawing a circle around every vector, expanding it until it contains exactly k
  other vectors.

  - In a crowded region, that circle will be small.
  - In a sparse region, it will be large.

  That circle’s radius estimates the local spacing around the vector.

  Suppose k = 3:

  A’s third-nearest vector is 0.10 away → radius(A) = 0.10
  B’s third-nearest vector is 0.14 away → radius(B) = 0.14

  CkNN combines those radii:

  connection threshold = δ × √(0.10 × 0.14)
                       = δ × 0.118

  With δ = 1:

  - If distance(A,B) = 0.09, connect them.
  - If distance(A,B) = 0.13, do not connect them.

  Now consider two vectors in a sparse region:

  radius(C) = 0.40
  radius(D) = 0.25

  threshold = √(0.40 × 0.25) = 0.316

  If C and D are 0.28 apart, they connect—even though that distance would be enormous
  inside the crowded region.

  So CkNN’s rule is:

  > Connect two vectors when they are close compared with the normal spacing around both
  > vectors.



# Hierarchical Felzenszwalb–Huttenlocher

Hierarchical Felzenszwalb–Huttenlocher as the primary segmentation method.
 It asks concretely:
 
 > Is crossing between these two regions a larger semantic change than the variation
 > already present inside them?

It then records the accepted merges as a nested hierarchy. Every parent is exactly the
union of complete children. This is the closest existing analogue to detecting an
object boundary in an image.

 Frozen fine segments = regions
  CkNN/RNG connections = which regions touch
  Vector distances = how different touching meanings are

  For every pair of touching regions, it compares two measurements.

Variation inside each region:

  Suppose the vectors inside region A require connections as large as 0.12 to hold the
  region together.

  internal variation(A) = 0.12

  Region B’s internal variation might be 0.10.

Difference across their boundary:

  Find the closest connection crossing from A to B:

  boundary difference(A,B) = 0.14

  The boundary is only slightly larger than the variation already accepted inside A and B:

 inside A:       0.12
  across A → B:   0.14

  That is weak evidence for keeping them separate, so they merge relatively early.

  Now consider region C:

  internal variation(C) = 0.11
  boundary difference(A,C) = 0.45

  Crossing from A to C requires a much larger semantic jump than movement inside either
  region. That is a strong boundary, so they remain separate until much later.

  ### Producing the hierarchy

  The algorithm determines the scale at which every boundary becomes weak enough to remove:

  small scale:
  A   B   C

  larger scale:
  [A + B]   C

  largest scale:
  [A + B + C]

  The hierarchical version records these merges permanently. A region never later moves
  somewhere else, so every parent is exactly the union of its children.

  It also includes a size adjustment: small regions are easier to merge because limited
  evidence makes their internal variation unreliable. Whether “size” should mean atomic-
  vector count in our system is an open question; corpus frequency may not equal semantic
  importance.

  The central hypothesis is:

  > A real subject boundary appears as an unusually large local semantic jump compared with
  > the variation on either side.

  The main weakness is that the boundary measurement uses the closest cross-region
  connection. One accidental bridge could make two otherwise separate regions look
  mergeable. That is specifically what we would need to inspect in the pilot.


