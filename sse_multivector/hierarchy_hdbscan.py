"""Source-bound HDBSCAN groups and numerical cuts of their saved hierarchy."""

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import struct
import subprocess

from . import canonical_trial as trial
from . import experiment as workflow


CONFIG = dict(min_samples=3, min_cluster_size=2, selection_method="excess_of_mass")
CONFIG_V42 = dict(CONFIG, min_cluster_size=4)
CONFIG_V43 = dict(CONFIG, min_samples=4)
CONFIG_V44 = dict(CONFIG_V43, min_cluster_size=4)
SECTION_CONFIGS = {
    "hierarchy-generation-v4.1": CONFIG,
    "hierarchy-generation-v4.2": CONFIG_V42,
    "hierarchy-generation-v4.3": CONFIG_V43,
    "hierarchy-generation-v4.4": CONFIG_V44,
    "hierarchy-generation-v5": CONFIG,
    "hierarchy-generation-v5.1": CONFIG,
    "hierarchy-generation-v5.2": CONFIG,
    "hierarchy-generation-v5.3": CONFIG,
}
_RESULT_FILES = ContextVar('hierarchy_hdbscan_result_files', default=None)
_VALIDATED_ROUNDS = ContextVar('hierarchy_hdbscan_validated_rounds', default=None)
_RESULT_CACHE_BYTES = 1024 * 1024 * 1024
_CPU_WORKERS = ContextVar('hierarchy_cpu_workers', default=None)
_PARALLEL_MIN_VECTORS = 1024
_NUMERICAL_STATE = None


def cpu_workers():
    configured = _CPU_WORKERS.get()
    if configured is not None:
        return configured
    available = (len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity')
                 else os.cpu_count() or 1)
    return max(1, available - 4)


@contextmanager
def cpu_scope(workers=None):
    """Share one local CPU budget; provider request admission is independent."""
    workers = cpu_workers() if workers is None else workers
    if type(workers) is not int or workers < 1:
        raise ValueError('cpu_workers must be a positive integer')
    affinity = os.sched_getaffinity(0) if hasattr(os, 'sched_getaffinity') else None
    workers = min(workers, len(affinity) if affinity else os.cpu_count() or 1)
    token = _CPU_WORKERS.set(workers)
    try:
        if affinity is not None:
            os.sched_setaffinity(0, sorted(affinity)[:workers])
        yield workers
    finally:
        if affinity is not None:
            os.sched_setaffinity(0, affinity)
        _CPU_WORKERS.reset(token)


def _numerical_worker_init(state):
    global _NUMERICAL_STATE
    _NUMERICAL_STATE = state


def _validate_saved_round(job, state=None):
    from . import hierarchy_generation as generation
    family, round_ = job
    state = _NUMERICAL_STATE if state is None else state
    with source_scope(), workflow.report_scope():
        vectors = generation._vectors(state, round_['current'])
        check_round(state, family, round_, vectors)
        if round_.get('selection') is not None and round_['groups']:
            request, mapping = request_for(state, round_['current'], vectors)
            tree = project(read_result(round_['hdbscan']['result']), request, mapping)
            if round_['selection'] != select_sections(tree, state['max_siblings']):
                raise ValueError('V5 section cut changed')


def _validation_identities(state, jobs):
    """Bind each check to its controls, vector producers and current evidence files."""
    from . import worker
    stamp = workflow.engine.ReceiptFiles._stamp
    sources = workflow.inputs.digest([state['sources'], state['hdbscan_binary']])
    encodings = {}
    for _, round_ in jobs:
        for identifier in round_['current']:
            reference = state['vectors'][state['items'][identifier]['vector_key']]
            index = reference['encoding']
            if index not in encodings:
                job = state['encodings'][index]
                config = worker.WorkerConfig.load(Path(job['config']))
                paths = [Path(job['config']), config.request_path,
                         config.output_path/'worker-receipt.json',
                         config.output_path/'raw-vectors.f32le']
                encodings[index] = workflow.inputs.digest([
                    job, [(str(p), stamp(p)) for p in paths]])
    identities = []
    for family, round_ in jobs:
        references = []
        for identifier in round_['current']:
            key = state['items'][identifier]['vector_key']
            reference = state['vectors'][key]
            references.append([identifier, key, reference, encodings[reference['encoding']]])
        evidence = round_['hdbscan']
        paths = [Path(evidence['request']), Path(evidence['result'])]
        controls = {k: round_.get(k) for k in (
            'current', 'groups', 'cases', 'unassigned', 'unpaired', 'hdbscan', 'selection')}
        identities.append(workflow.inputs.digest([
            sources, family['id'], state['generation_policy'], state['max_siblings'],
            SECTION_CONFIGS.get(state['generation_policy'], CONFIG), controls,
            references, [(str(p), stamp(p)) for p in paths]]))
    return identities


def check_rounds(state, jobs):
    """Validate new or changed numerical evidence once within a source scope."""
    cache = _VALIDATED_ROUNDS.get()
    identities = _validation_identities(state, jobs) if cache is not None else None
    if cache is not None:
        pending = [(job, identity) for job, identity in zip(jobs, identities, strict=True)
                   if cache.get(job[1]['hdbscan']['result']) != identity]
        jobs = [job for job, _ in pending]
        identities = [identity for _, identity in pending]
    if not jobs:
        return
    workers = min(cpu_workers(), len(jobs))
    if workers > 1 and sum(len(r['current']) for _, r in jobs) >= _PARALLEL_MIN_VECTORS:
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context('spawn'),
                                 initializer=_numerical_worker_init, initargs=(state,)) as pool:
            futures = [pool.submit(_validate_saved_round, job) for job in jobs]
            for future in futures:
                future.result()
    else:
        for job in jobs:
            _validate_saved_round(job, state)
    if cache is not None:
        if identities != _validation_identities(state, jobs):
            raise ValueError('numerical evidence changed during validation')
        for job, identity in zip(jobs, identities, strict=True):
            cache[job[1]['hdbscan']['result']] = identity


def _cluster_round(job):
    from . import hierarchy_generation as generation
    directory, inputs, workers = job
    with source_scope(), workflow.report_scope():
        return round_for(directory, _NUMERICAL_STATE, inputs,
                         generation._vectors(_NUMERICAL_STATE, inputs['current']), workers=workers)


def cluster_rounds(state, jobs):
    """Run independent clustering and result processing without a shared Python GIL."""
    with ProcessPoolExecutor(max_workers=min(cpu_workers(), len(jobs)),
                             mp_context=multiprocessing.get_context('spawn'),
                             initializer=_numerical_worker_init, initargs=(state,)) as pool:
        pending = [pool.submit(_cluster_round, job) for job in jobs]
        return [future.result() for future in pending]


@contextmanager
def source_scope(*, isolated=False, projected_cache_bytes=_RESULT_CACHE_BYTES):
    """Bounded immutable-result reads shared by one hierarchy coordinator."""
    if not isolated and _RESULT_FILES.get() is not None:
        yield
        return
    # Large membership trees retain several MiB per compact view. The ordinary
    # receipt reader's 16 MiB default repeatedly evicts those immutable views.
    token = _RESULT_FILES.set(workflow.engine.ReceiptFiles(
        projected_cache_bytes=projected_cache_bytes))
    checks = _VALIDATED_ROUNDS.set({})
    try:
        yield
    finally:
        _VALIDATED_ROUNDS.reset(checks)
        _RESULT_FILES.reset(token)


def _hierarchy_fields(response):
    """Retain the fields used by hierarchy checks, not unused quadratic data."""
    artifact = response.get('artifact') if isinstance(response, dict) else None
    result = artifact.get('result') if isinstance(artifact, dict) else None
    algorithm = result.get('algorithm_result') if isinstance(result, dict) else None
    if not isinstance(algorithm, dict):
        return response
    retained = dict(result, algorithm_result={
        k: v for k, v in algorithm.items() if k in ('vector_count', 'clusters', 'condensed_tree')})
    if isinstance(retained.get('fine_output'), dict):
        retained['fine_output'] = {k: v for k, v in retained['fine_output'].items() if k == 'segments'}
    return dict(response, artifact=dict(
        {k: v for k, v in artifact.items() if k != 'canonical_fine_output_json'}, result=retained))


def read_result(path):
    """Reuse a compact parsed view within the native operation's bounded cache.

    The complete source remains unchanged and its full-file hash is still checked.
    Unused numerical diagnostics remain in the source rather than the read cache.
    """
    files = _RESULT_FILES.get()
    if files is not None:
        return files.json(Path(path), project=_hierarchy_fields)
    return workflow.read(path, project=_hierarchy_fields)


def section_plan(response, request, mapping, max_siblings):
    """Keep selected groups as leaves; cut only their original ancestor tree."""
    groups = members(response, request, mapping)
    if not groups:
        return dict(roots=[], sections=[], cuts=[])
    result = response["artifact"]["result"]
    algorithm = result["algorithm_result"]
    count = algorithm["vector_count"]
    aliases = result["alias_groups"]
    unique = result["canonical_unique_ids"]
    if (type(count) is not int or count < 1 or len(aliases) != count
            or len(unique) != count or len(set(unique)) != count
            or any(not a or a[0] != u for a, u in zip(aliases, unique))
            or sorted(i for a in aliases for i in a) != sorted(mapping)
            or len(algorithm["clusters"]) != len(groups)):
        raise ValueError("invalid HDBSCAN tree input identities")
    selected = {}
    for cluster, group in zip(algorithm["clusters"], groups, strict=True):
        identifier = cluster["id"]
        if (type(identifier) is not int or identifier < count or identifier in selected
                or any(type(i) is not int or not 0 <= i < count for i in cluster["members"])
                or sorted(mapping[x] for i in cluster["members"] for x in aliases[i]) != sorted(group)):
            raise ValueError("HDBSCAN selected cluster differs from saved group")
        selected[identifier] = group
    positions = {node: i for i, node in enumerate(selected)}
    parents, children = {}, {}
    for edge in algorithm["condensed_tree"]:
        parent, child, value = edge["parent"], edge["child"], edge["lambda"]
        if (type(parent) is not int or parent < count or type(child) is not int
                or child < 0 or child == parent or child in parents
                or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0):
            raise ValueError("invalid HDBSCAN condensed tree")
        parents[child] = (parent, value)
        if child >= count:
            children.setdefault(parent, []).append(child)
    needed = set()
    for leaf in selected:
        node, path = leaf, set()
        while node not in needed:
            if node in path:
                raise ValueError("cyclic HDBSCAN condensed tree")
            path.add(node)
            if node == count:
                break
            if node not in parents:
                raise ValueError("disconnected HDBSCAN selected group")
            node = parents[node][0]
        needed.update(path)
    # Postorder without Python recursion, including long chain-shaped trees.
    order, stack = [], [count]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(c for c in children.get(node, []) if c in needed)
    projected, representative, sizes, first = {}, {}, {}, {}
    for node in reversed(order):
        below = [representative[c] for c in children.get(node, []) if c in needed]
        if node in selected:
            if below:
                raise ValueError("HDBSCAN selected groups are not independent leaves")
            representative[node] = node
            sizes[node], first[node] = 1, positions[node]
        elif len(below) == 1:
            representative[node] = below[0]
        elif len(below) >= 2:
            values = [parents[c][1] for c in children[node] if c in needed]
            if any(not math.isclose(v, values[0], rel_tol=1e-12) for v in values):
                raise ValueError("HDBSCAN branch split distances differ")
            distance = 1 / values[0]
            if any(c in projected and projected[c]["distance"] > distance for c in below):
                raise ValueError("HDBSCAN branch distances are not ordered")
            below.sort(key=first.__getitem__)
            projected[node] = dict(children=below, distance=distance)
            representative[node] = node
            sizes[node] = sum(sizes[c] for c in below)
            first[node] = min(first[c] for c in below)
        else:
            raise ValueError("empty HDBSCAN ancestor branch")

    def cut(node):
        if sizes[node] <= max_siblings:
            leaves, pending = [], [node]
            while pending:
                current = pending.pop()
                if current in selected:
                    leaves.append(current)
                else:
                    pending.extend(projected[current]["children"])
            return sorted(leaves, key=first.__getitem__), None
        frontier, upper = [node], None
        while True:
            distance = max(projected[c]["distance"] for c in frontier if c in projected)
            expanded, pending = [], list(frontier)
            while pending:
                current = pending.pop()
                if current in projected and projected[current]["distance"] == distance:
                    pending.extend(projected[current]["children"])
                else:
                    expanded.append(current)
            if len(expanded) > max_siblings:
                if len(frontier) == 1:
                    raise ValueError("HDBSCAN tied split exceeds the section limit")
                return sorted(frontier, key=first.__getitem__), dict(
                    lower=distance, upper=upper, epsilon=(distance + upper) / 2)
            frontier, upper = expanded, distance
            if all(c in selected for c in frontier):
                return sorted(frontier, key=first.__getitem__), None

    root = representative[count]
    roots, boundary = cut(root)
    cuts = [dict(cluster_id=root, children=roots, boundary=boundary)]
    records, pending = {}, list(roots)
    while pending:
        node = pending.pop()
        if node in records:
            continue
        below, boundary = ([], None) if node in selected else cut(node)
        if below:
            cuts.append(dict(cluster_id=node, children=below, boundary=boundary))
        records[node] = dict(cluster_id=node, children=below,
                             group=selected.get(node, []))
        pending.extend(below)
    order, pending = [], list(roots)
    while pending:
        node = pending.pop()
        order.append(node)
        pending.extend(records[node]["children"])
    sections = []
    original_ids = {}
    for node in reversed(order):
        record = records[node]
        original_ids[node] = sorted(record["group"] or [
            i for child in record["children"] for i in original_ids[child]])
        sections.append(dict(record, original_ids=original_ids[node]))
    cuts.sort(key=lambda c: c["cluster_id"])
    return dict(roots=roots, sections=sections, cuts=cuts)


def plan_for(state, round_, vectors):
    request, mapping = request_for(state, round_["current"], vectors)
    return section_plan(read_result(round_["hdbscan"]["result"]), request,
                        mapping, state["max_siblings"])


def request_for(state, ids, vectors):
    inputs, mapping, raw = [], {}, bytearray()
    for identifier, vector in zip(ids, vectors, strict=True):
        norm = math.sqrt(sum(v * v for v in vector))
        if not math.isfinite(norm) or norm == 0:
            raise ValueError("invalid HDBSCAN input vector")
        normalized = [v / norm for v in vector]
        opaque = workflow.inputs.digest([identifier, state["items"][identifier]["vector_key"]])
        mapping[opaque] = identifier
        inputs.append(dict(opaque_id=opaque, normalized_vector=normalized))
        raw.extend(struct.pack("<" + "d" * len(normalized), *normalized))
    return dict(
        schema_version=1, candidate="hdbscan", inputs=inputs,
        source_vector_manifest_sha256=workflow.inputs.digest([
            [identifier, state["items"][identifier]["vector_key"]] for identifier in ids
        ]),
        normalized_vector_sha256=hashlib.sha256(raw).hexdigest(),
        hdbscan_configuration=SECTION_CONFIGS.get(state.get("generation_policy"), CONFIG),
    ), mapping


def members(response, request, mapping):
    if (response.get("schema_version") != 1
            or response.get("candidate_identity") not in (
                "hdbscan-explicit-config-v1", "hdbscan-hierarchy-output-v1")):
        raise ValueError("unexpected HDBSCAN response identity")
    artifact = response["artifact"]
    manifest = artifact["manifest"]
    configuration = request["hdbscan_configuration"]
    if (configuration not in SECTION_CONFIGS.values()
            or json.loads(artifact["canonical_configuration_json"]) != configuration
            or manifest.get("parameters") != configuration
            or manifest.get("algorithm_version") != "hdbscan-star-exact-angular-v1"
            or manifest.get("fine_output_selector_version") != "hdbscan-clusters-members-v1"
            or any(manifest.get(k) != request[k] for k in (
                "source_vector_manifest_sha256", "normalized_vector_sha256"))
            or artifact.get("canonical_input_ids") != sorted(mapping)):
        raise ValueError("HDBSCAN controls or input identities changed")
    segments = artifact["result"]["fine_output"]["segments"]
    if not isinstance(segments, list):
        raise ValueError("HDBSCAN groups must be an array")
    assigned = []
    for group in segments:
        if (not isinstance(group, list) or len(group) < configuration["min_cluster_size"]
                or any(not isinstance(i, str) or i not in mapping for i in group)):
            raise ValueError("invalid HDBSCAN group membership")
        assigned.extend(group)
    if len(set(assigned)) != len(assigned):
        raise ValueError("HDBSCAN groups overlap or repeat members")
    return [[mapping[i] for i in group] for group in segments]


def round_for(directory, state, family, vectors, *, workers=None):
    ids = list(family["current"])
    request, mapping = request_for(state, ids, vectors)
    destination = directory / f"hdbscan-{len(family['rounds']):05d}"
    destination.mkdir(exist_ok=True)
    request_path, result_path = destination / "request.json", destination / "result.json"
    trial._save_once(request_path, request)
    if not result_path.exists():
        environment = dict(os.environ, RAYON_NUM_THREADS=str(cpu_workers() if workers is None else workers))
        command = [state["hdbscan_binary"], str(request_path)]
        result = subprocess.run([*command, '--hierarchy-output'],
                                capture_output=True, check=False, env=environment)
        # Historical frozen executables predate compact output. Preserve their
        # resumability without hiding numerical or input errors from newer ones.
        if result.returncode and result.stderr.strip().endswith(
                b'usage: fine-segmentation-candidate REQUEST.json [--threads N]'):
            result = subprocess.run(command, capture_output=True, check=False, env=environment)
        (destination / "stderr.txt").write_bytes(result.stderr)
        if result.returncode:
            raise ValueError("HDBSCAN command failed: " + result.stderr.decode(errors="replace"))
        decoded = json.loads(result.stdout)
        members(decoded, request, mapping)
        trial._save_once(result_path, decoded)
    groups = members(read_result(result_path), request, mapping)
    assigned = {i for group in groups for i in group}
    return dict(
        current=ids, groups=groups,
        cases={f"{family['id']}-G{i:05d}": group for i, group in enumerate(groups)},
        unassigned=[i for i in ids if i not in assigned], unpaired=[],
        hdbscan=dict(request=str(request_path), request_sha256=trial._hash(request_path),
                     result=str(result_path), result_sha256=trial._hash(result_path)),
    )


def check_round(state, family, round_, vectors):
    request, mapping = request_for(state, round_["current"], vectors)
    evidence = round_["hdbscan"]
    if (trial._hash(evidence["request"]) != evidence["request_sha256"]
            or trial._hash(evidence["result"]) != evidence["result_sha256"]
            or workflow.read(evidence["request"]) != request):
        raise ValueError("saved HDBSCAN evidence changed")
    groups = members(read_result(evidence["result"]), request, mapping)
    assigned = {i for group in groups for i in group}
    if (round_["groups"] != groups
            or round_["cases"] != {
                f"{family['id']}-G{i:05d}": group for i, group in enumerate(groups)}
            or round_["unassigned"] != [i for i in round_["current"] if i not in assigned]
            or round_["unpaired"]):
        raise ValueError("saved HDBSCAN membership changed")


def project(response, request, mapping):
    """Project the original condensed tree onto the fixed selected groups."""
    groups = members(response, request, mapping)
    # Use the native validator without imposing its ordinary six-way cut.
    section_plan(response, request, mapping, max(1, len(groups)))
    if not groups:
        raise ValueError('no selected HDBSCAN groups')
    algorithm = response['artifact']['result']['algorithm_result']
    count = algorithm['vector_count']
    selected = {c['id']: i + 1 for i, c in enumerate(algorithm['clusters'])}
    parents, children = {}, defaultdict(list)
    for edge in algorithm['condensed_tree']:
        parents[edge['child']] = (edge['parent'], edge['lambda'])
        if edge['child'] >= count:
            children[edge['parent']].append(edge['child'])
    needed = {count}
    for node in selected:
        while node not in needed:
            needed.add(node)
            node = parents[node][0]
    order, pending = [], [count]
    while pending:
        node = pending.pop()
        order.append(node)
        pending.extend(c for c in children[node] if c in needed)
    nodes, representative = {}, {}
    for node in reversed(order):
        below = [representative[c] for c in children[node] if c in needed]
        if node in selected:
            nodes[node] = dict(node=node, groups=[selected[node]], children=[])
        elif len(below) == 1:
            representative[node] = below[0]
            continue
        else:
            below.sort(key=lambda c: min(nodes[c]['groups']))
            nodes[node] = dict(node=node, children=below,
                               groups=sorted(g for c in below for g in nodes[c]['groups']),
                               distance=1 / parents[next(c for c in children[node]
                                                         if c in needed)][1])
        representative[node] = node
    return dict(root=representative[count], nodes=list(nodes.values()))


def curve(tree):
    splits = defaultdict(int)
    for node in tree['nodes']:
        if node['children']:
            splits[node['distance']] += len(node['children']) - 1
    distances = sorted(splits, reverse=True)
    points, count = [], 1
    for i, distance in enumerate(distances):
        count += splits[distance]
        following = distances[i + 1] if i + 1 < len(distances) else 0
        points.append(dict(distance=distance, following_distance=following,
                           section_count=count, midpoint=(distance + following) / 2))
    return points


def select_epsilon(tree):
    points = curve(tree)
    trim = math.ceil(.10 * len(points))
    retained = points[trim:len(points) - trim]
    if len(retained) < 3:
        raise ValueError('candidate needs at least three retained distance levels')
    first, last = retained[0], retained[-1]
    scored = []
    for point in retained:
        x = ((point['section_count'] - first['section_count']) /
             (last['section_count'] - first['section_count']))
        y = ((first['distance'] - point['distance']) /
             (first['distance'] - last['distance']))
        scored.append(dict(point, score=x-y))
    best = max(scored, key=lambda p: (p['score'], -p['section_count']))
    if best['score'] <= 0:
        raise ValueError('candidate needs a positive bend; no fallback is defined')
    return dict(rule='trimmed-bend-10-percent-v1', epsilon=best['midpoint'],
                omitted_levels_per_end=trim, selected_point=best,
                fitted_points=scored, curve=points)


def partition(tree, epsilon):
    nodes = {n['node']: n for n in tree['nodes']}
    sections, pending = [], [tree['root']]
    while pending:
        node = nodes[pending.pop()]
        if not node['children'] or node['distance'] <= epsilon:
            sections.append(node)
        else:
            pending.extend(reversed(node['children']))
    return sections


def select_sections(tree, max_siblings=6):
    """V5's bend, V4 cut, then ranked-group fallback; never drop a tree leaf."""
    leaves = [n for n in tree['nodes'] if not n['children']]
    if len(leaves) <= max_siblings:
        return dict(rule='group-leaves-v5', epsilon=None,
                    sections=sorted(leaves, key=lambda n: n['groups']))
    try:
        result = select_epsilon(tree)
        return dict(result, sections=partition(tree, result['epsilon']))
    except ValueError as error:
        reason = str(error)
    points = [p for p in curve(tree) if 2 <= p['section_count'] <= max_siblings]
    if points:
        epsilon = points[-1]['midpoint']
        return dict(rule='six-section-v4', epsilon=epsilon, reason=reason,
                    sections=partition(tree, epsilon))
    # Selection ranks these leaves by distinct supporting notes, not group size.
    return dict(rule='largest-groups-v5', epsilon=None, reason=reason,
                sections=sorted(leaves, key=lambda n: n['groups']))
