"""Compact, streamed exports for explicitly supported numerical result families.

Native memberships/graphs retain their original meanings and IDs. Working
coordinates and distance tables are not publication outputs. Unknown historical
schemas are rejected rather than treated as interchangeable reports.
"""
import ast
from contextlib import contextmanager
import hashlib
import json
from numbers import Integral, Real
from pathlib import Path
import re
import struct
import zipfile

if __package__:
    from ._runner_bootstrap import shared
else:
    from _runner_bootstrap import shared


FORMAT = 'numerical-publication-v1'
FAMILIES = ('geometric', 'fuzzy', 'hidef', 'merge-rule', 'comparison', 'performance',
            'fine-region', 'pair-scores')
_CONFIG = {'run_id', 'method', 'config', 'parameters', 'sources', 'code', 'python',
    'numpy', 'dependencies', 'source_code_sha256', 'graph_policy_source_sha256',
    'dependency_lock_sha256', 'vector_count', 'dimensions', 'canonical_order_sha256',
    'elapsed_seconds', 'max_rss_kib', 'resolutions', 'seed_policy', 'containment',
    'consensus_similarity', 'consensus_membership', 'input_hierarchy_sha256'}
_ALIASES = {'vector_id', 'short_id', 'note_id', 'note_short_id', 'subject',
            'subject_id', 'fragments', 'byte_spans'}
_SETTINGS = {
    'diffusion': {'epsilon', 'density_normalization', 'diffusion_steps', 'merge_tolerance',
        'density_tolerance', 'bandwidth_growth', 'max_steps', 'snapshot_iterations',
        'relaxation', 'coordinate_constraint'},
    'haus': {'affinity', 'epsilon', 'max_kways', 'max_depth', 'min_points',
        'mean_cut_threshold', 'max_perturbation', 'seed'},
    'fmc': {'n_neighbors', 'density_neighbors', 'adaptive', 'alpha', 'xi', 'gamma1',
        'gamma2', 'q', 'refinement_steps', 'delta0', 'delta_decay', 'delta_until_level',
        'order_control_start_level', 'attachment_tau', 'attachment_factor', 'max_levels'},
    'hidef': {'minres', 'maxres', 'density', 'neighbors', 'jaccard', 'persistence',
        'consensus_percent', 'seed', 'candidate_min_size', 'n_iterations', 'sample', 'workers'},
    'benchmark': {'model', 'revision', 'architecture', 'method', 'lengths', 'train_batch_size',
        'inference_batch_sizes', 'steps', 'warmup_steps', 'repetitions', 'learning_rate',
        'memory_budget_gib', 'reserve_gib', 'seed', 'quantization', 'supervised_output_tokens'},
}
_PACKAGES = {'torch', 'transformers', 'peft', 'numpy', 'scipy', 'networkx', 'igraph',
    'leidenalg', 'louvain', 'hidef', 'pandas', 'scikit-learn', 'huggingface_hub', 'huggingface-hub',
    'tokenizers', 'safetensors', 'sentence-transformers', 'sentence_transformers'}
_CODE = {'geometric_experiment.py', 'geometric_diffusion.py', 'geometric_fmc.py',
    'geometric_haus.py', 'hidef_experiment.py', 'hidef_graph_policy.py',
    'merge_rule_experiment.py', 'distillation_benchmark.py', 'distillation_run.py',
    'local_weight_model.py', 'hidef_finder.py', 'weaver.py', 'utils.py'}
_SOURCE_ROLES = {'manifest', 'vectors', 'mapping', 'notes', 'aliases',
                 'baseline', 'request', 'vector_map'}
_DIAGNOSTICS = {'n_rows', 'dimension', 'initial_components', 'initial_edges',
    'initial_isolated_rows', 'adaptive_underflow_edges', 'final_aggregates'}
_MEMORY_FIELDS = {'status', 'runner_commit', 'project_commit', 'runner_source_sha256',
    'limits', 'root_allocation_gib', 'fake_provider_worker_mib', 'full_native_groups',
    'batch_count', 'full_case_count', 'attempt_cap_per_group',
    'all_coordinators_and_30_workers_barrier', 'peak_memory_gib', 'technical_failures',
    'elapsed_seconds', 'memory_events', 'post_worker_memory_gib', 'native_max_rss_gib',
    'sample_at_peak_current', 'latest_sample', 'saved_support_extra_rss_gib',
    'combined_peak_plus_saved_support_delta_gib', 'blindspots', 'margin_256',
    'first_barrier_native_max_rss_gib', 'estimate_note', 'peak_model_workers',
    'peak_native_coordinators', 'progress_at_stop', 'fake_starts', 'fake_stops', 'service_final'}


def _choose(value, names):
    return {name: value[name] for name in names if name in value}


def _allow(value, names, metadata, label):
    """Configuration is an explicit profile, never arbitrary nested metadata."""
    if not isinstance(value, dict):
        metadata.setdefault('omitted_settings', {})[label] = 1
        return {}

    def primitive(item, depth=0):
        if item is None or isinstance(item, (str, bool, Integral, Real)):
            return True
        return (depth < 2 and isinstance(item, (list, tuple))
                and all(primitive(child, depth+1) for child in item))
    result = {}
    for name, item in value.items():
        if name not in names or not primitive(item):
            continue
        if name in ('model', 'model_id', 'run_id') and isinstance(item, str) and item.startswith('/'):
            continue
        if (name.endswith('_sha256') or name == 'sha256') and not (
                isinstance(item, str) and re.fullmatch('[0-9a-f]{64}', item)):
            continue
        result[name] = _public(item)
    omitted = len(value)-len(result)
    if omitted:
        metadata.setdefault('omitted_settings', {})[label] = omitted
    return result


def _hashes(value, names, metadata, label):
    if not isinstance(value, dict):
        return {}
    selected = {Path(name).name: digest for name, digest in value.items()
                if Path(name).name in names and isinstance(digest, str)
                and re.fullmatch('[0-9a-f]{64}', digest)}
    if len(selected) != len(value):
        metadata.setdefault('omitted_settings', {})[label] = len(value)-len(selected)
    return selected


def _bindings(value, metadata, label):
    if not isinstance(value, dict):
        return {}
    return {name: _allow(row, {'sha256'}, metadata, label+'.'+name)
            for name, row in value.items() if name in _SOURCE_ROLES}


def _configuration(value, method, metadata):
    nested = {'config', 'parameters', 'sources', 'code', 'dependencies', 'containment',
              'graph_policy', 'graph', 'input_graph', 'extension'}
    result = _allow(_choose(value, set(value)-nested), _CONFIG-nested | {'schema_version'},
                    metadata, 'configuration')
    for key in ('config', 'parameters'):
        if key in value:
            result[key] = _allow(value[key], _SETTINGS[method], metadata, 'configuration.'+key)
    if 'sources' in value:
        result['sources'] = _bindings(value['sources'], metadata, 'configuration.sources')
    if 'code' in value:
        result['code'] = _hashes(value['code'], _CODE, metadata, 'configuration.code')
    if 'dependencies' in value:
        dependencies = value['dependencies']
        scalars = (_choose(dependencies, set(dependencies)-{'versions', 'source_sha256'})
                   if isinstance(dependencies, dict) else dependencies)
        result['dependencies'] = _allow(scalars, {'hidef_version', 'hidef_commit'}, metadata,
                                         'configuration.dependencies')
        if isinstance(dependencies, dict):
            result['dependencies']['versions'] = _allow(dependencies.get('versions', {}),
                _PACKAGES, metadata, 'configuration.dependencies.versions')
            result['dependencies']['source_sha256'] = _hashes(dependencies.get('source_sha256', {}),
                _CODE, metadata, 'configuration.dependencies.source_sha256')
    if 'containment' in value:
        result['containment'] = _allow(value['containment'], {'cutoff', 'strict_subset',
            'parent_expansion', 'transitive_reduction', 'multiple_parents'}, metadata, 'containment')
    if 'graph_policy' in value:
        policy = value['graph_policy']
        scalars = (_choose(policy, set(policy)-{'tie_break'})
                   if isinstance(policy, dict) else policy)
        result['graph_policy'] = _allow(scalars, {'policy', 'definition'}, metadata,
                                         'configuration.graph_policy')
        if isinstance(policy, dict) and 'tie_break' in policy:
            result['graph_policy']['tie_break'] = _allow(policy['tie_break'],
                {'mutual_best_per_note', 'strongest_edges_matched', 'output_edge_order'}, metadata,
                'configuration.graph_policy.tie_break')
    for key in ('graph', 'input_graph'):
        if key in value:
            result[key] = _allow(value[key], {'sha256', 'vertices', 'edges', 'weight_sum'}, metadata, key)
    if 'extension' in value:
        result['extension'] = _allow(value['extension'], {'previous_maxres', 'added_resolutions',
            'boundary_log10_gap', 'singleton_resolution_bound', 'endpoint_exceeds_singleton_bound'},
            metadata, 'configuration.extension')
    return result


def _public(value):
    """Remove locations/working payloads from fields selected by an adapter."""
    excluded = {'path', 'directory', 'output', 'snapshot', 'argv', 'working_directory',
        'embedding', 'embeddings', 'coordinates', 'final_coordinates',
        'distance_matrix', 'distances', 'cosine_distances', 'pointer_config',
        'training_pid', 'verification_pid', 'model_input', 'token_ids', 'api_key',
        'credentials', 'secret', 'access_token', 'refresh_token'}
    if isinstance(value, dict):
        return {key: _public(item)
                for key, item in value.items() if key not in excluded}
    if isinstance(value, list):
        return [_public(item) for item in value]
    if isinstance(value, Integral) and not isinstance(value, (bool, int)):
        return int(value)
    if isinstance(value, Real) and not isinstance(value, (bool, int, float)):
        return float(value)
    return value


class _Reader:
    def __init__(self, stream):
        self.stream, self.digest = stream, hashlib.sha256()

    def read(self, size=-1):
        data = self.stream.read(size)
        self.digest.update(data)
        return data

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


class _Sources:
    def __init__(self, metadata, values):
        self.hashes = metadata['sources']
        self.values = values or {}

    @contextmanager
    def read(self, path):
        path = Path(path)
        before = path.stat()
        with path.open('rb') as stream:
            reader = _Reader(stream)
            yield reader
            while reader.read(65536):
                pass
        after = path.stat()
        stamp = lambda value: (value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)
        digest = reader.digest.hexdigest()
        if stamp(before) != stamp(after) or self.hashes.get(path.name, digest) != digest:
            raise ValueError('numerical result source changed during export')
        self.hashes[path.name] = digest

    def fields(self, path, names):
        if Path(path).name in self.values:
            with self.read(path):
                pass
            value = self.values[Path(path).name]
            if not isinstance(value, dict):
                raise ValueError('numerical configuration must be a JSON object')
            return _choose(value, names)
        from experiment_runner.json_projection import project
        with self.read(path) as stream:
            return project(stream, names)

    def items(self, path, prefix='item'):
        if Path(path).name in self.values:
            with self.read(path):
                pass

            def select(value, keys):
                if not keys:
                    yield value
                elif keys[0] == 'item':
                    if isinstance(value, (list, tuple)):
                        for item in value:
                            yield from select(item, keys[1:])
                elif isinstance(value, dict) and keys[0] in value:
                    yield from select(value[keys[0]], keys[1:])
            yield from select(self.values[Path(path).name], prefix.split('.'))
            return
        import ijson
        with self.read(path) as stream:
            yield from ijson.items(stream, prefix, use_float=True)

    def lines(self, path):
        with self.read(path) as stream:
            for raw in stream.stream:
                stream.digest.update(raw)
                if raw.strip():
                    yield json.loads(raw)


def _mapping(sources, directory, header=None):
    evidence = directory/'evidence.json'
    if evidence.is_file():
        for index, row in enumerate(sources.items(evidence)):
            aliases = row.get('aliases')
            if not isinstance(aliases, list):
                raise ValueError('numerical evidence requires an alias list')
            yield dict(row=row.get('row', index), canonical_id=row.get('canonical_id'),
                       aliases=[_public(_choose(alias, _ALIASES)) for alias in aliases])
    elif header and 'canonical_unique_ids' in header:
        identifiers, aliases = header['canonical_unique_ids'], header.get('alias_groups')
        if (not isinstance(identifiers, list) or not isinstance(aliases, list)
                or len(identifiers) != len(aliases)):
            raise ValueError('canonical IDs and aliases must have equal lengths')
        for index, (identifier, group) in enumerate(zip(identifiers, aliases)):
            yield dict(row=index, canonical_id=identifier, aliases=group)


def _geometric(sources, directory, metadata):
    config = sources.fields(directory/'configuration.json', _CONFIG)
    if config.get('method') not in ('diffusion', 'haus', 'fmc'):
        raise ValueError('unsupported geometric configuration')
    metadata['parameters'] = _configuration(config, config['method'], metadata)
    header = sources.fields(directory/'hierarchy.json', {'method', 'roots', 'stop_reason',
        'config', 'diagnostics', 'summary'})
    if not isinstance(header.get('roots'), list):
        raise ValueError('geometric result requires roots')
    if 'config' in header:
        header['config'] = _allow(header['config'], _SETTINGS[config['method']], metadata,
                                   'hierarchy.config')
    if 'diagnostics' in header:
        header['diagnostics'] = _allow(header['diagnostics'], _DIAGNOSTICS, metadata,
                                        'hierarchy.diagnostics')

    def results():
        yield dict(type='hierarchy', **_public(header))
        count = 0
        for node in sources.items(directory/'hierarchy.json', 'nodes.item'):
            if not {'id', 'children', 'members'} <= node.keys():
                raise ValueError('geometric node requires ID, children and memberships')
            count += 1
            yield dict(type='node', **_public(_choose(node, {
                'id', 'children', 'members', 'note_ids', 'stats'})))
        metadata['outcome'] = dict(nodes=count)
    return results(), _mapping(sources, directory)


def _npy_rows(stream):
    """Stream C-order numerical rows from an NPZ member without loading NumPy."""
    if stream.read(6) != b'\x93NUMPY':
        raise ValueError('fuzzy result array is not NPY')
    version = stream.read(2)
    if version not in (b'\x01\x00', b'\x02\x00', b'\x03\x00'):
        raise ValueError('unsupported fuzzy NPY version')
    width = 2 if version == b'\x01\x00' else 4
    raw = stream.read(width)
    if len(raw) != width:
        raise ValueError('incomplete fuzzy NPY header')
    size = int.from_bytes(raw, 'little')
    if size > 65536:
        raise ValueError('fuzzy NPY header is too large')
    try:
        header = ast.literal_eval(stream.read(size).decode('utf-8'))
    except (ValueError, SyntaxError, UnicodeError) as error:
        raise ValueError('invalid fuzzy NPY header') from error
    shape, dtype = header.get('shape'), header.get('descr')
    if (header.get('fortran_order') is not False or not isinstance(shape, tuple)
            or len(shape) != 2 or any(type(n) is not int or n < 0 for n in shape)
            or dtype not in ('<f8', '>f8', '<f4', '>f4')):
        raise ValueError('fuzzy result requires a C-order two-dimensional float array')
    yield dict(type='fuzzy_array', shape=list(shape), dtype=dtype)
    number = struct.Struct(dtype[0] + ('d' if dtype[2] == '8' else 'f'))
    for row in range(shape[0]):
        columns, values = [], []
        for column in range(shape[1]):
            raw = stream.read(number.size)
            if len(raw) != number.size:
                raise ValueError('incomplete fuzzy membership array')
            value = number.unpack(raw)[0]
            if value:
                columns.append(column)
                values.append(value)
        yield dict(type='fuzzy_row', row=row, columns=columns, values=values)
    if stream.read(1):
        raise ValueError('fuzzy array has trailing bytes')


def _fuzzy(sources, directory, metadata):
    projected, inputs = _geometric(sources, directory, metadata)
    native = sources.fields(directory/'native-fuzzy.json', {
        'method', 'config', 'stop_reason', 'diagnostics', 'levels', 'transitions'})
    if native.get('method') != 'fmc2005_experimental_fuzzy':
        raise ValueError('unsupported native fuzzy result')
    if 'config' in native:
        native['config'] = _allow(native['config'], _SETTINGS['fmc'], metadata, 'fuzzy.config')
    if 'diagnostics' in native:
        native['diagnostics'] = _allow(native['diagnostics'], _DIAGNOSTICS, metadata,
                                        'fuzzy.diagnostics')

    def results():
        for record in projected:
            yield dict(record, representation='hard_projection')
        yield dict(type='fuzzy', **_public(_choose(native, {
            'method', 'config', 'stop_reason', 'diagnostics'})))
        path = directory/'native-fuzzy-arrays.npz'
        with sources.read(path) as source:
            while source.read(65536):
                pass
        before = path.stat()
        with zipfile.ZipFile(path) as archive:
            for collection, field in (('levels', 'membership'), ('transitions', 'interpolation')):
                for index, level in enumerate(native.get(collection, [])):
                    reference = level.get(field, {})
                    key = reference.get('array')
                    if not isinstance(key, str) or not re.fullmatch(r'array_\d+', key):
                        raise ValueError('invalid fuzzy array reference')
                    with archive.open(key+'.npy') as stream:
                        for record in _npy_rows(stream):
                            if record['type'] == 'fuzzy_array' and record['shape'] != reference.get('shape'):
                                raise ValueError('fuzzy array shape differs from its result reference')
                            yield dict(record, role=field, level=level.get('level', index))
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError('fuzzy result source changed during export')
    return results(), inputs


def _hidef(sources, directory, metadata):
    config = sources.fields(directory/'configuration.json', _CONFIG | {
        'schema_version', 'graph_policy', 'graph', 'input_graph', 'extension'})
    if config.get('schema_version') != 'hidef-configuration-v1':
        raise ValueError('unsupported HiDeF configuration')
    metadata['parameters'] = _configuration(config, 'hidef', metadata)
    header = sources.fields(directory/'hierarchy.json', {'schema_version', 'method', 'root',
        'canonical_unique_ids', 'alias_groups', 'summary'})
    if header.get('schema_version') != 'containment-hierarchy-v1':
        raise ValueError('unsupported HiDeF hierarchy')

    def results():
        yield dict(type='hierarchy', **_choose(header, {'schema_version', 'method', 'root', 'summary'}))
        for group in sources.items(directory/'strict-dag.json', 'groups.item'):
            yield dict(type='group', **_public(_choose(group, {
                'id', 'kind', 'vector_ids', 'note_ids', 'parents', 'children', 'persistence'})))
        for group in sources.items(directory/'persistent-groups.json', 'groups.item'):
            yield dict(type='persistent_group', **_public(_choose(group, {
                'family_id', 'support_count', 'distinct_resolution_count', 'vector_ids',
                'note_ids', 'empty_after_consensus'})))
        timings = sources.fields(directory/'timings.json', {'discovery_seconds', 'persistence_seconds',
            'containment_seconds', 'note_projection_seconds', 'elapsed_seconds', 'peak_rss_kib'})
        yield dict(type='measurements', **timings)
    return results(), _mapping(sources, directory, header)


def _merge(sources, path, metadata):
    header = sources.fields(path, {'schema_version', 'run_id', 'method', 'sources',
        'source_code_sha256', 'definition', 'missing_partner_policy', 'tie_rule', 'distance',
        'excluded_undirected_edges', 'canonical_unique_ids', 'alias_groups', 'vector_count',
        'summary', 'elapsed_seconds'})
    if header.get('schema_version') != 'merge-rule-experiment-v1':
        raise ValueError('unsupported merge-rule result')
    metadata['parameters'] = _allow(_choose(header, set(header)-{
        'sources', 'canonical_unique_ids', 'alias_groups', 'summary', 'elapsed_seconds'}),
        {'schema_version', 'run_id', 'method', 'source_code_sha256', 'definition',
         'missing_partner_policy', 'tie_rule', 'distance', 'excluded_undirected_edges',
         'vector_count'}, metadata, 'merge-rule')
    metadata['parameters']['sources'] = _bindings(header.get('sources', {}), metadata, 'merge-rule.sources')

    def results():
        yield dict(type='summary', **_choose(header, {'summary', 'elapsed_seconds'}))
        for merge in sources.items(path, 'merges.item'):
            if not {'id', 'left', 'right', 'merge_score'} <= merge.keys():
                raise ValueError('merge result requires child references and score')
            yield dict(type='merge', **_public(_choose(merge, {
                'id', 'left', 'right', 'size', 'merge_score', 'unsupported_left', 'unsupported_right'})))
    return results(), _mapping(sources, path.parent, header)


def _followup_memory(sources, path, metadata, header):
    """The saved synthetic coordinator stress summaries, not their worker jobs."""
    required = {'runner_commit', 'project_commit', 'runner_source_sha256', 'limits',
        'root_allocation_gib', 'fake_provider_worker_mib', 'full_case_count', 'peak_memory_gib',
        'all_coordinators_and_30_workers_barrier', 'status'}
    if (not required <= header.keys() or not ({'full_native_groups', 'batch_count'} & header.keys())
            or any(not isinstance(header[name], str) or not re.fullmatch('[0-9a-f]{40}', header[name])
                   for name in ('runner_commit', 'project_commit'))):
        raise ValueError('unsupported followup-memory-scale summary')
    settings = {'runner_commit', 'project_commit', 'root_allocation_gib',
        'fake_provider_worker_mib', 'full_case_count', 'full_native_groups', 'batch_count',
        'attempt_cap_per_group'}
    metadata['parameters'] = _allow(_choose(header, settings), settings, metadata, 'memory.workload')
    metadata['parameters'].update(profile='followup-memory-scale',
        workload='Synthetic coordinator resource stress with simulated provider workers; no model inference')
    metadata['parameters']['runner_source_sha256'] = _hashes(header['runner_source_sha256'],
        {'experiment.py', 'extraction_pipeline.py'}, metadata, 'memory.runner_source_sha256')
    if len(metadata['parameters']['runner_source_sha256']) != 2:
        raise ValueError('followup-memory-scale summary requires its two runner source hashes')
    metadata['parameters']['limits'] = _allow(header['limits'],
        {'memory.max', 'memory.swap.max', 'memory.oom.group'}, metadata, 'memory.limits')
    nested = {
        'sample_at_peak_current': {'elapsed', 'memory_current', 'memory_peak', 'model_workers',
            'native_coordinators', 'native_rss', 'native_rss_max', 'python_count', 'python_rss', 'events'},
        'latest_sample': {'elapsed', 'memory_current', 'memory_peak', 'model_workers',
            'native_coordinators', 'native_rss', 'native_rss_max', 'python_count', 'python_rss', 'events'},
        'progress_at_stop': {'elapsed', 'completed', 'total', 'barrier_met', 'failures'},
        'service_final': {'ActiveState', 'SubState', 'Result', 'reason'},
    }
    fields = _MEMORY_FIELDS-settings-set(nested)-{'runner_source_sha256', 'limits'}
    measurements = _allow(_choose(header, fields), fields, metadata, 'memory.measurements')
    for name, allowed in nested.items():
        if name in header:
            measurements[name] = _allow(header[name], allowed, metadata, 'memory.'+name)
    if 'progress_at_stop' in header:
        metadata['status'] = 'stopped'

    def results():
        yield dict(type='measurements', **measurements)
        for row in sources.items(path, 'real_saved_support_verification.item'):
            yield dict(type='saved_support_verification', **_allow(row,
                {'event', 'elapsed', 'rss', 'peak_rss', 'jobs'}, metadata, 'memory.saved_support'))
    return results(), iter(())


def _performance(sources, path, metadata):
    header = sources.fields(path, {'schema_version', 'workload', 'config', 'config_sha256',
        'code_sha256', 'system', 'versions', 'complete', 'checkpoint_saved', 'awaiting_verification',
        'reload_matches', 'load_seconds', 'save_seconds', 'reload_seconds', 'parameters',
        'request_sha256', 'binary_sha256', 'state_sha256', 'original_state_sha256',
        'saved_full_bytes', 'compact_persisted_bytes', 'cpu_workers', 'reserved_cpus',
        'state_unchanged', 'teacher_calls', 'nodes', 'rounds', 'validation_seconds',
        'total_seconds', 'groups_tree_aliases_and_memberships_identical', 'saved_hr35_result_matches',
        'kind', 'all_six_requests_and_results_byte_identical', 'observed_cpu_processes',
        'native_advance_completed', 'nodes_exact', 'notes_exact', 'all_prepared_case_inputs_exact',
        'all_membership_additions_exact', 'experiments', 'families', 'standalone_advance_wall_seconds',
        'baseline_in_process_advance_seconds', 'timing_qualification', 'elapsed_seconds',
        'input_entries', 'compact_response_identity', 'result_bytes',
        'groups_and_unassigned_identical', 'native_result_validation_passed',
        'new_teacher_result_ledgers', 'checks', 'error'} | _MEMORY_FIELDS)
    if 'fake_provider_worker_mib' in header:
        return _followup_memory(sources, path, metadata, header)
    if not (header.get('workload') or 'state_sha256' in header or 'request_sha256' in header
            or 'original_state_sha256' in header
            or header.get('kind') == 'offline-no-inference-fixed-input-replay'):
        raise ValueError('unsupported performance report')
    error = header.pop('error', None)
    metadata['status'] = ('failed' if error else 'complete' if header.get('complete') is True else
                          'not_recorded' if 'complete' not in header else 'incomplete')
    if isinstance(error, str) and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', error.split(':', 1)[0]):
        metadata['failure_type'] = error.split(':', 1)[0]
    metadata['parameters'] = _allow(_choose(header, {'workload', 'config_sha256',
        'request_sha256', 'binary_sha256', 'state_sha256'}), {'workload', 'config_sha256',
        'request_sha256', 'binary_sha256', 'state_sha256'}, metadata, 'performance')
    if 'config' in header:
        metadata['parameters']['config'] = _allow(header['config'], _SETTINGS['benchmark'],
                                                   metadata, 'performance.config')
    if 'versions' in header:
        metadata['parameters']['versions'] = _allow(header['versions'], _PACKAGES,
                                                     metadata, 'performance.versions')
    if 'code_sha256' in header:
        metadata['parameters']['code_sha256'] = _hashes(header['code_sha256'], _CODE,
                                                         metadata, 'performance.code')
    if 'system' in header:
        metadata['parameters']['system'] = _allow(header['system'], {'architecture', 'gpu',
            'available_bytes_before_load', 'cuda_total_bytes'}, metadata, 'performance.system')
    if 'parameters' in header:
        header['parameters'] = _allow(header['parameters'], {'total', 'stored_tensor_elements',
            'trainable', 'pointer_head'}, metadata, 'performance.parameter_counts')

    def results():
        yield dict(type='measurements', **_public({key: value for key, value in header.items()
                   if key not in metadata['parameters']}))
        for field in ('training', 'inference', 'measurements', 'records'):
            for row in sources.items(path, field+'.item'):
                yield dict(type=field, **_allow(row, {'tokens_per_example', 'batch_size', 'steps',
                    'step_seconds', 'warmup_step_seconds', 'median_step_seconds', 'losses',
                    'peak_cuda_allocated_bytes', 'available_system_bytes_after',
                    'supervised_tokens_per_example', 'seconds', 'median_batch_seconds',
                    'examples_per_second', 'wall_seconds', 'user_seconds', 'system_seconds',
                    'peak_rss_kib', 'mode', 'bytes', 'node', 'request.json', 'result.json',
                    'validated_rounds'},
                    metadata, 'performance.'+field))
    return results(), iter(())


def _fine_region(sources, path, metadata):
    header = sources.fields(path, {'schema_version', 'pilot_id', 'config_sha256',
        'baseline_archive_sha256', 'analysis_manifest_sha256', 'generation_manifest_sha256',
        'normalized_vectors_sha256', 'partition_analysis_sha256', 'review_decisions_sha256',
        'hierarchy_source_sha256', 'partition_source_sha256', 'pilot_source_sha256',
        'fine_region_hierarchy_source_sha256', 'scc_source_sha256', 'preflight_source_sha256',
        'command_source_sha256', 'cargo_lock_sha256', 'rules', 'vector_count', 'note_count',
        'dimensions', 'accepted_review_count', 'accepted_minimum_cosine', 'partition_cutoff_cosine',
        'fine_segment_selection', 'hierarchy_vector_count', 'hierarchy_note_count',
        'pairwise_cosines', 'cross_note_nearest_cosines', 'first_rejected_minimum_cosine',
        'cross_note_candidate_segment_count', 'cross_note_fine_segment_count',
        'excluded_strict_subset_segment_count', 'singleton_fine_segment_count',
        'unreviewed_same_note_group_count', 'unreviewed_same_note_vector_count',
        'flake_nix_sha256', 'flake_lock_sha256'})
    pilot = header.get('pilot_id')
    if pilot not in ('sse-fine-region-partition-v1', 'sse-fine-region-hierarchy-v2',
                     'scc-hierarchy-preflight-v1'):
        raise ValueError('unsupported fine-region report')
    rules = header.pop('rules', None)
    distributions = {name: header.pop(name) for name in ('pairwise_cosines', 'cross_note_nearest_cosines')
                     if name in header}
    metadata['parameters'] = _allow(header, set(header), metadata, 'fine-region')
    if rules is not None:
        metadata['parameters']['rules'] = _allow(rules, {'resolution_source', 'complete_linkage',
            'dp_vmf', 'dp_vmf_orders', 'coassignment_order', 'labels_used_for_membership',
            'fine_segments', 'higher_groups', 'fine_segment_weighting', 'labels_used_for_geometry'},
            metadata, 'fine-region.rules')
    for name, values in distributions.items():
        metadata['parameters'][name] = _allow(values, {'count', 'minimum', 'p05', 'p25', 'median',
            'p75', 'p95', 'maximum', 'mean'}, metadata, 'fine-region.'+name)

    def results():
        if pilot == 'sse-fine-region-partition-v1':
            for row in sources.items(path, 'resolutions.item'):
                yield dict(type='partition', **_public(row))
        elif pilot == 'sse-fine-region-hierarchy-v2':
            for name in ('fine_segments', 'merges'):
                for row in sources.items(path, 'hierarchy.'+name+'.item'):
                    yield dict(type=name, **_public(row))
            for root in sources.items(path, 'hierarchy.root'):
                yield dict(type='root', root=root)
        else:
            for row in sources.items(path, 'report.variants.item'):
                yield dict(type='schedule', **_public(row))

    def inputs():
        if pilot == 'sse-fine-region-partition-v1':
            for row in sources.items(path, 'vectors.item'):
                yield _public(_choose(row, {'ordinal', 'note_id', 'subject_id', 'takeaway',
                                           'selected_source_fragments'}))
    return results(), inputs()


def _comparison(sources, path, metadata):
    header = sources.fields(path, {'schema_version', 'comparison_source_sha256',
        'parameters_except_seed', 'resolution_count', 'reference_resolution', 'sample',
        'sources', 'validation', 'validation_scope', 'interpretation',
        'repeat_seed_exact_sets', 'repeat_seed_multinote_exact_sets'})
    if header.get('schema_version') not in ('hidef-graph-policy-comparison-v1',
                                           'hidef-resolution-extension-comparison-v1'):
        raise ValueError('unsupported numerical comparison schema')
    metadata['parameters'] = _allow(_choose(header, {'schema_version', 'comparison_source_sha256',
        'resolution_count', 'reference_resolution'}), {'schema_version', 'comparison_source_sha256',
        'resolution_count', 'reference_resolution'}, metadata, 'comparison')
    if 'parameters_except_seed' in header:
        metadata['parameters']['parameters_except_seed'] = _allow(header['parameters_except_seed'],
            _SETTINGS['hidef'], metadata, 'comparison.parameters_except_seed')
    if 'sample' in header:
        metadata['parameters']['sample'] = _allow(header['sample'], {'anchors', 'extra_groups',
            'extra_edges', 'edges', 'satoshi_canonical_vector_ids', 'added_selection', 'counterpart_pool'},
            metadata, 'comparison.sample')
    if 'sources' in header:
        metadata['parameters']['sources'] = _bindings(header['sources'], metadata, 'comparison.sources')

    def results():
        yield dict(type='comparison', **_public({key: value for key, value in header.items()
                   if key not in metadata['parameters']}))
        for field in ('runs', 'correspondence', 'baseline_primary_evidence'):
            for row in sources.items(path, field+'.item'):
                yield dict(type=field, **_public(row))

    def inputs():
        for row in sources.items(path, 'mask_evidence.item'):
            yield _public(_choose(row, _ALIASES | {'canonical_id'}))
    return results(), inputs()


def _pair_scores(sources, directory, metadata):
    fields = {
        'experiment_id', 'experiment', 'run_id', 'model_id', 'model_revision', 'revision', 'input_sha256',
        'code_sha256', 'scope', 'score_definition', 'comparison_definition', 'dtype', 'device',
        'batch_size', 'seed', 'packages', 'evidence_sha256', 'fixture_sha256', 'runner_sha256',
        'groups_sha256', 'helper_sha256', 'source_sha256', 'loading_seconds',
        'inference_seconds', 'peak_rss_kib', 'model_labels', 'decision', 'displayed_score',
        'max_input_tokens', 'max_new_tokens', 'label_token_ids', 'cpu_threads', 'threads',
        'torch_threads', 'condition', 'queries', 'pooling', 'maximum_tokens', 'input_count',
        'unique_subject_count', 'model_input_field', 'generation', 'parameter_count', 'parameters',
        'truncation', 'threshold', 'threshold_decision', 'load_seconds', 'notes'}
    configuration = sources.fields(directory/'config.json', fields)
    nested = {'packages', 'pooling', 'model_labels', 'label_token_ids', 'generation'}
    metadata['parameters'] = _allow(_choose(configuration, fields-nested), fields-nested,
                                       metadata, 'pair-scores')
    profiles = {
        'packages': _PACKAGES,
        'pooling': {'word_embedding_dimension', 'pooling_mode_cls_token', 'pooling_mode_max_tokens',
            'pooling_mode_mean_tokens', 'pooling_mode_mean_sqrt_len_tokens',
            'pooling_mode_weightedmean_tokens', 'pooling_mode_lasttoken', 'include_prompt'},
        'model_labels': {'0', '1', '2', '3', '4'},
        'label_token_ids': {'0', '1'},
        'generation': {'do_sample', 'num_beams', 'max_new_tokens', 'return_dict_in_generate',
                       'output_logits'},
    }
    for name, allowed in profiles.items():
        if name in configuration:
            metadata['parameters'][name] = _allow(configuration[name], allowed, metadata,
                                                   'pair-scores.'+name)

    def assessments(path, kind):
        import ijson
        with path.open('rb') as stream:
            array = stream.read(1024).lstrip().startswith(b'[')
        if array:
            for value in sources.items(path):
                yield dict(type=kind, value=_public(value))
        else:
            with sources.read(path) as stream:
                for key, value in ijson.kvitems(stream, '', use_float=True):
                    yield dict(type=kind, field=key, value=_public(value))

    def results():
        neighborhoods = directory/'neighborhoods.json'
        if neighborhoods.is_file():
            if metadata['parameters'].get('run_id') != 'PPR01':
                raise ValueError('unsupported affinity neighborhood schema')
            import ijson
            with sources.read(neighborhoods) as stream:
                for query, metrics in ijson.kvitems(stream, '', use_float=True):
                    for metric, neighbors in metrics.items():
                        if metric not in ('cosine', 'euclidean') or not isinstance(neighbors, list):
                            raise ValueError('unsupported affinity neighborhood metric')
                        yield dict(type='neighbors', query=query, metric=metric,
                                   neighbors=[_choose(row, {'row', 'note', 'score'}) for row in neighbors])
            return
        count = 0
        path = directory/'scores.jsonl'
        rows = sources.lines(path) if path.is_file() else sources.items(directory/'scores.json')
        for row in rows:
            if not isinstance(row, dict) or not (
                    {'premise', 'hypothesis', 'score'} <= row.keys()
                    or {'query', 'passage', 'score'} <= row.keys()
                    or {'a', 'b', 'angle_degrees'} <= row.keys()
                    or {'first', 'second', 'prediction', 'scores'} <= row.keys()
                    or {'generated_text', 'generated_token_ids', 'predicted'} <= row.keys()):
                raise ValueError('unsupported numerical pair-score schema')
            count += 1
            result = dict(type='pair_score', **_public(_choose(row, {'vector', 'description',
                'premise', 'hypothesis', 'source', 'logits', 'score', 'token_count',
                'a', 'b', 'angle_radians', 'angle_degrees', 'cosine', 'a_id', 'b_id',
                'query', 'passage', 'condition', 'child', 'parent', 'expected_implication',
                'child_group', 'parent_group', 'first', 'second', 'baseline', 'scores', 'prediction',
                'id', 'case', 'domain', 'kind', 'wording', 'role', 'expected', 'format',
                'generated_text', 'generated_token_ids', 'eos_terminated', 'predicted',
                'entailment_score', 'logit_0_first_token', 'logit_1_first_token',
                'probability_0_first_token', 'first_token_binary_score', 'first_token_binary_label',
                'label_prefix_probability_mass', 'argmax_token_id', 'threshold_predicted',
                'row', 'note', 'group', 'candidate', 'measurement', 'child_candidate',
                'parent_candidate', 'baseline_score', 'source_pair', 'source_index',
                'category_id', 'category_title'})))
            if 'masks' in row:
                if not isinstance(row['masks'], list) or any(
                        not isinstance(mask, dict) for mask in row['masks']):
                    raise ValueError('numerical category memberships must be mask records')
                result['masks'] = [_public(_choose(mask, _ALIASES | {'judgment', 'ordinal',
                    'reviewed_note_index', 'reviewed_subject', 'reviewed_subject_id',
                    'reviewed_subject_index', 'worker_subject_id', 'token_count', 'note_text_sha256'}))
                    for mask in row['masks']]
            yield result
        metadata['outcome'] = dict(pairs=count)
        for name in ('checks', 'summary', 'analysis'):
            path = directory/(name+'.json')
            if path.is_file():
                yield from assessments(path, name)

    def inputs():
        path = directory/'inputs.json'
        if path.is_file():
            for row in sources.items(path):
                result = _public(_choose(row, {'id', 'case', 'domain', 'wording', 'role',
                    'vector', 'description', 'subject', 'note_id', 'note', 'row', 'source'}))
                if isinstance(row.get('text'), str):
                    result['description'] = row['text']
                yield result
    return results(), inputs()


def export_results(source, output=None, family=None, *, source_values=None):
    """Export supported saved results through the same path used by final writers.

    Files default to publication/<stem> alongside their original; directory
    sources default to their publication/ subdirectory. Ambiguous old report
    files require an explicit family. Final writers may provide the same values
    they just saved, avoiding another parse or a streaming-parser dependency on
    remote workers. Their saved files are still hashed and bound. Offline reads
    stream with the runner's parser. No model or numerical algorithm is rerun.
    """
    write_publication = shared('publication_files').write_publication
    source = Path(source).resolve()
    if family is None:
        if source.is_file():
            family = 'merge-rule'
        elif (source/'native-fuzzy.json').is_file():
            family = 'fuzzy'
        elif (source/'strict-dag.json').is_file():
            family = 'hidef'
        elif (source/'hierarchy.json').is_file() and (source/'configuration.json').is_file():
            family = 'geometric'
        elif (source/'report.json').is_file():
            family = 'performance'
        else:
            raise ValueError('select an explicit supported numerical publication family')
    if family not in FAMILIES:
        raise ValueError('unsupported numerical publication family')
    directory = source if source.is_dir() else source.parent
    if output is None:
        output = directory/'publication' if source.is_dir() else directory/'publication'/source.stem
    output = Path(output)
    if output.is_symlink():
        raise ValueError('publication destination must not be a symlink')
    output = output.resolve()
    if output == directory or output in directory.parents:
        raise ValueError('publication output must not replace a source directory')
    metadata = dict(schema_version=1, format=FORMAT, family=family,
        source_id=hashlib.sha256((family+':'+str(source)).encode()).hexdigest(),
        experiment_id=source.name, status='not_recorded', sources={},
        exporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    sources = _Sources(metadata, source_values)
    if family in ('geometric', 'fuzzy', 'hidef', 'pair-scores'):
        adapter = {'geometric': _geometric, 'fuzzy': _fuzzy, 'hidef': _hidef,
                   'pair-scores': _pair_scores}[family]
        results, inputs = adapter(sources, source, metadata)
    else:
        name = ('report.json' if family == 'performance' else
                'comparison.json' if family == 'comparison' else 'analysis.json')
        path = source/name if source.is_dir() else source
        adapter = {'merge-rule': _merge, 'performance': _performance,
                   'fine-region': _fine_region, 'comparison': _comparison}[family]
        results, inputs = adapter(sources, path, metadata)
    return write_publication(output, metadata, {'results.jsonl': results, 'inputs.jsonl': inputs})
