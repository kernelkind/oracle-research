"""Experimental diffusion condensation on unchanged input-coordinate dimensions.

Independent implementation of the equations in Brugnone et al. (2019),
https://arxiv.org/html/1907.04463v3, sections III and IV; cumulative merge
membership follows Huguet et al. (2023), https://arxiv.org/html/2203.14860,
section 5.2. No CATCH or Multiscale PHATE source code is incorporated.

Working coordinates evolve, but all original rows remain present. No PCA,
diffusion-potential preprocessing, representative compression, unit-sphere
renormalization, or later hierarchy simplification is performed here.
"""

from numbers import Integral
from time import perf_counter

import numpy as np


def _squared_distances(coordinates):
    # Translation before the Gram product reduces cancellation without changing
    # the distances or the coordinates used by the actual diffusion update.
    centered = coordinates - coordinates.mean(axis=0)
    squared_norms = np.einsum("ij,ij->i", centered, centered)
    distances = -2.0 * (centered @ centered.T)
    distances += squared_norms[:, None]
    distances += squared_norms[None, :]
    if not np.isfinite(distances).all():
        raise ValueError("coordinate distances must remain finite")
    np.maximum(distances, 0.0, out=distances)
    np.fill_diagonal(distances, 0.0)
    return distances


def fit(
    X,
    *,
    epsilon,
    density_normalization=1.0,
    diffusion_steps=1,
    merge_tolerance=1e-4,
    density_tolerance=1e-4,
    bandwidth_growth=2.0,
    max_steps=2000,
    snapshot_iterations=(),
    relaxation=1.0,
):
    """Return native merge nodes, possibly multiple roots, and numerical stats.

    ``epsilon`` is the squared-distance denominator in exp(-distance²/epsilon),
    not a Euclidean radius. It is deliberately required rather than estimated
    silently. ``density_normalization`` is beta in K_ij=A_ij/(q_i*q_j)^beta,
    q=A1. Row normalization gives P; each condensation step applies P the
    specified ``diffusion_steps`` times before recomputing affinities.

    Bandwidth grows when successive unnormalized degree vectors at the same
    epsilon differ by less than ``density_tolerance`` in the infinity norm.
    Comparisons reset on a bandwidth change. Setting ``bandwidth_growth=1``
    keeps epsilon fixed. All original rows retain equal observation mass.

    ``relaxation`` optionally makes the coordinate update a convex fraction
    of the full diffusion move: (1-relaxation)*X + relaxation*(P**steps @ X).
    This adapts the explicit underrelaxation in Carreira-Perpinan (CVPR2008,
    https://iacl.ece.jhu.edu/proceedings/cvpr2008/papers/095.pdf) to the current
    density-normalized operator. One preserves the original update exactly.

    At time zero and after each update, pairs closer than ``merge_tolerance``
    add permanent membership unions. This numerical threshold is not a semantic
    acceptance rule. Simultaneous connected unions become one multiway node;
    no arbitrary binary subhierarchy is introduced. Node members are original
    row indices. A bound-limited forest is returned without fabricating a root.

    By default only scalar histories and the final coordinates are retained.
    ``snapshot_iterations`` optionally saves coordinate copies at the requested
    iterations, without changing the trajectory or its stopping conditions.
    Memory is O(n²+nd), plus requested snapshots and explicit memberships.
    The caller should limit BLAS to one thread for the pilot workflow.
    """
    started = perf_counter()
    if np.iscomplexobj(X):
        raise ValueError("X must contain finite real coordinates")
    coordinates = np.array(X, dtype=np.float64, copy=True)
    if (coordinates.ndim != 2 or min(coordinates.shape) == 0
            or not np.isfinite(coordinates).all()):
        raise ValueError("X must be a nonempty finite two-dimensional matrix")
    for name, value in (("epsilon", epsilon), ("merge_tolerance", merge_tolerance),
                        ("density_tolerance", density_tolerance)):
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be positive and finite")
    if (not np.isfinite(density_normalization)
            or not 0 <= density_normalization <= 1):
        raise ValueError("density_normalization must lie in [0, 1]")
    if not np.isfinite(bandwidth_growth) or bandwidth_growth < 1:
        raise ValueError("bandwidth_growth must be finite and at least 1")
    if not np.isfinite(relaxation) or not 0 < relaxation <= 1:
        raise ValueError("relaxation must lie in (0, 1]")
    for name, value in (("diffusion_steps", diffusion_steps), ("max_steps", max_steps)):
        minimum = 1 if name == "diffusion_steps" else 0
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    requested = set(snapshot_iterations)
    if any(isinstance(i, bool) or not isinstance(i, Integral) or i < 0 for i in requested):
        raise ValueError("snapshot iterations must be nonnegative integers")
    snapshots = {0: coordinates.copy()} if 0 in requested else {}

    n, dimensions = coordinates.shape
    initial_epsilon = float(epsilon)
    epsilon = initial_epsilon
    nodes = [{"id": i, "children": [], "members": [i], "iteration": 0,
              "epsilon": None} for i in range(n)]
    parents = list(range(n))
    active = dict(enumerate(range(n)))

    def find(member):
        while parents[member] != member:
            parents[member] = parents[parents[member]]
            member = parents[member]
        return member

    def record_merges(distances, iteration, used_epsilon):
        nonlocal active
        radius_squared = merge_tolerance * merge_tolerance
        for left in range(n - 1):
            for right in np.flatnonzero(distances[left, left + 1:] < radius_squared):
                a, b = find(left), find(left + 1 + int(right))
                if a != b:
                    parents[max(a, b)] = min(a, b)
        children_by_root = {}
        for representative, node_id in active.items():
            children_by_root.setdefault(find(representative), []).append(node_id)
        updated = {}
        created = 0
        for representative, children in sorted(children_by_root.items()):
            children.sort(key=lambda node_id: nodes[node_id]["members"][0])
            if len(children) == 1:
                updated[representative] = children[0]
                continue
            node_id = len(nodes)
            members = sorted(member for child in children for member in nodes[child]["members"])
            nodes.append({"id": node_id, "children": children, "members": members,
                          "iteration": iteration, "epsilon": used_epsilon})
            updated[representative] = node_id
            created += 1
        active = updated
        return created

    distances = _squared_distances(coordinates)
    initial_diameter = float(np.sqrt(distances.max()))
    initial_merges = record_merges(distances, 0, initial_epsilon)
    previous_degree = None
    history = []
    bandwidth_changes = 0
    for iteration in range(1, max_steps + 1):
        if len(active) == 1:
            break
        with np.errstate(over="ignore", under="ignore"):
            operator = np.exp(-distances / epsilon)
        degree = operator.sum(axis=1)
        density_change = (None if previous_degree is None else
                          float(np.max(np.abs(degree - previous_degree))))
        density_factor = degree ** density_normalization
        operator /= density_factor[:, None]
        operator /= density_factor[None, :]
        operator /= operator.sum(axis=1)[:, None]
        next_coordinates = coordinates
        for _ in range(diffusion_steps):
            next_coordinates = operator @ next_coordinates
        if relaxation < 1:
            next_coordinates = (1 - relaxation) * coordinates + relaxation * next_coordinates
        displacement = float(np.linalg.norm(next_coordinates - coordinates, axis=1).max())
        coordinates = next_coordinates
        if iteration in requested:
            snapshots[iteration] = coordinates.copy()
        distances = _squared_distances(coordinates)
        new_merges = record_merges(distances, iteration, epsilon)
        next_epsilon = epsilon
        if (len(active) > 1 and density_change is not None
                and density_change < density_tolerance and bandwidth_growth > 1):
            next_epsilon = epsilon * bandwidth_growth
            if not np.isfinite(next_epsilon):
                raise ValueError("bandwidth growth exceeded finite epsilon")
            bandwidth_changes += 1
        history.append({"iteration": iteration, "epsilon": epsilon,
                        "next_epsilon": next_epsilon, "group_count": len(active),
                        "new_merges": new_merges, "max_displacement": displacement,
                        "diameter": float(np.sqrt(distances.max())),
                        "density_change": density_change})
        previous_degree = degree if next_epsilon == epsilon else None
        epsilon = next_epsilon

    roots = [active[representative] for representative in sorted(active)]
    final_diameter = float(np.sqrt(distances.max()))
    return {
        "nodes": nodes,
        "roots": roots,
        "final_coordinates": coordinates,
        **({"snapshots": snapshots} if requested else {}),
        "stats": {
            "method": "direct_coordinate_diffusion_condensation",
            "n_vectors": n,
            "dimensions": dimensions,
            "steps": len(history),
            "stop_reason": "single_group" if len(roots) == 1 else "max_steps",
            "initial_epsilon": initial_epsilon,
            "next_epsilon": epsilon,
            "density_normalization": float(density_normalization),
            "diffusion_steps": int(diffusion_steps),
            "relaxation": float(relaxation),
            "merge_tolerance": float(merge_tolerance),
            "density_tolerance": float(density_tolerance),
            "bandwidth_growth": float(bandwidth_growth),
            "max_steps": int(max_steps),
            "bandwidth_changes": bandwidth_changes,
            "initial_merges": initial_merges,
            "initial_diameter": initial_diameter,
            "final_diameter": final_diameter,
            "all_within_tolerance": final_diameter < merge_tolerance,
            "representative_compression": False,
            "preprocessing": "none",
            "hierarchy_simplification": "none",
            "history": history,
            "elapsed_seconds": perf_counter() - started,
        },
    }
