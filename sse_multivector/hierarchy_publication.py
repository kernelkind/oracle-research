"""Export final hierarchy data and small, explicit settings from saved state.

This projects a saved snapshot; it does not replay construction or verify its
whole receipt history. Source hashes identify the recorded inputs and code.
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from .canonical_hierarchy_nostr import ENTRY_KIND, NODE_KIND, unsigned_events
from experiment_runner import json_projection


FORMAT = 'hierarchy-publication-v1'
FILES = ('hierarchy.jsonl', 'input-note-ids.txt', 'experiment.json')
_RUNNER_FIELDS = {
    'provider', 'model', 'reasoning_effort', 'max_output_tokens', 'temperature',
    'transport', 'timeout_seconds', 'concurrency', 'seed', 'prefix_caching',
}
_MODEL_FIELDS = {'base_model', 'dimensions', 'maximum_tokens', 'pooling'}
_ENCODER_FIELDS = {
    'checkpoint_sha256', 'base_model_artifact_tree_sha256', 'device',
    'container_image', 'note_batch_size',
}
_CODE_FILES = {
    'hierarchy_generation.py', 'hierarchy_generation_v5.py', 'worker.py',
    'experiment_inputs.py', 'experiment_extension.py', 'hierarchy_node_pairs.py',
    'canonical_trial.py', 'canonical_receipts.py', 'prompt_assembly.py',
    'hierarchy_hdbscan.py', 'hierarchy_publication_provenance.py',
}
_STATE_FIELDS = {
    'schema_version', 'generation_policy', 'publication_id', 'status',
    'corpus', 'note_ids', 'roots', 'inventory', 'queue', 'children',
    'nodes', 'menu', 'shape', 'sources', 'publication_provenance', 'source_upgrades',
    'worker_config', 'local_schema_version', 'max_siblings', 'min_notes',
    'v5_options', 'hdbscan_binary', 'hdbscan_configuration',
    'bootstrap_spec', 'compare_spec', 'comparison_spec', 'consolidation_spec', 'prominence_spec',
}


class _HashedInput:
    """Bind the original state bytes while the parser reads its bounded chunks."""
    def __init__(self, stream):
        self.stream = stream
        self.digest = hashlib.sha256()

    def read(self, size):
        block = self.stream.read(size)
        self.digest.update(block)
        return block


def _hash(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def _scalars(value, fields):
    """Only known scalar settings, never arbitrary nested runner configuration."""
    return {key: value[key] for key in sorted(fields) if key in value
            and (value[key] is None or type(value[key]) in (str, bool, int, float))}


def _selection(state):
    if 'note_ids' in state:
        selected = state['note_ids']
    else:
        from .canonical_trial import execution_queue
        rows = execution_queue(state)
        selected = list(dict.fromkeys(row['local']['note_id'] for row in rows))
    if (not isinstance(selected, list) or any(
            not isinstance(note, str) or not note.strip() or '\n' in note or '\r' in note
            or '\x00' in note for note in selected)
            or len(selected) != len(set(selected))):
        raise ValueError('hierarchy input selection must contain unique single-line note IDs')
    return selected


def _identity(directory, state):
    if state.get('publication_id') is not None:
        return str(uuid.UUID(state['publication_id']))
    # Legacy runs have no persisted per-run ID. Use an opaque location identity
    # rather than conflate separate preparations with identical inputs. Moving
    # such a source requires a fresh publication destination; new UUID runs do
    # not have this restriction. No local path is emitted.
    return hashlib.sha256(str(directory).encode()).hexdigest()


def _code_sources(sources):
    return [dict(path='sse_multivector/' + Path(path).name, sha256=digest)
            for path, digest in sorted(sources.items())
            if Path(path).parent.name == 'sse_multivector' and Path(path).name in _CODE_FILES]


def _deprecated(versions):
    if not isinstance(versions, list) or not versions:
        return None
    parsed = [re.fullmatch(r'ASv(\d+)(?:\.(\d+))?', version)
              if isinstance(version, str) else None for version in versions]
    if any((int(match[1]), int(match[2] or 0)) < (6, 100) for match in parsed if match):
        return True
    return False if all(parsed) else None


def _record(directory, state, state_hash, selected, execution_status, failure_type):
    sources = state.get('sources', {})
    provenance = state.get('publication_provenance', {})
    prompts = {}
    for role in ('bootstrap', 'compare', 'comparison', 'consolidation', 'prominence'):
        spec = state.get(role + '_spec')
        if not isinstance(spec, dict):
            continue
        prompt = spec.get('prompt', {})
        prompts[role] = dict(id=prompt.get('id'),
                             sha256=sources.get(prompt.get('path')),
                             runner=_scalars(spec.get('runner', {}), _RUNNER_FIELDS))
    encoder = state.get('worker_config', {})
    code = dict(preparation={})
    for name, value in provenance.get('code', {}).items():
        if name in ('oracle', 'runner') and isinstance(value, dict):
            code['preparation'][name] = _scalars(value, {'commit', 'modified'})
    code['sources'] = _code_sources(sources)
    code['upgrades'] = []
    for upgrade in state.get('source_upgrades', []):
        record = dict(before=_code_sources(upgrade.get('before', {})),
                      after=_code_sources(upgrade.get('after', {})))
        if upgrade.get('hdbscan_binary'):
            record['hdbscan_binary'] = {
                name + '_sha256': (upgrade.get(name, {}).get(path) or sources.get(path))
                for name, path in upgrade['hdbscan_binary'].items() if name in ('before', 'after')}
        code['upgrades'].append(record)
    if state.get('hdbscan_binary'):
        code['hdbscan_binary_sha256'] = sources.get(state['hdbscan_binary'])
    parameters = _scalars(state, {'generation_policy', 'local_schema_version',
                                  'max_siblings', 'min_notes'})
    if 'v5_options' in state:
        parameters['v5_options'] = _scalars(state['v5_options'],
                                            {'roots_only', 'include_original_unassigned'})
    if 'hdbscan_configuration' in state:
        parameters['hdbscan_configuration'] = _scalars(state['hdbscan_configuration'],
            {'min_samples', 'min_cluster_size', 'selection_method'})
    result = dict(schema_version=1, format=FORMAT, experiment_id=directory.name,
        source_id=_identity(directory, state),
        source_state_sha256=state_hash, status=state.get('status', 'unknown'),
        execution_status=execution_status or 'not_recorded',
        input=dict(corpus_sha256=sources.get(state.get('corpus')), count=len(selected),
                   note_ids_file='input-note-ids.txt',
                   deprecated=_deprecated(provenance.get('subject_prompt_versions')),
                   subject_prompt_versions=provenance.get('subject_prompt_versions')),
        parameters=parameters, prompts=prompts,
        encoder={**_scalars(encoder, _ENCODER_FIELDS),
                 'model': _scalars(encoder.get('model', {}), _MODEL_FIELDS)}, code=code,
        exporter=dict(sources={
            **{'sse_multivector/' + name: _hash(Path(__file__).with_name(name))
               for name in ('hierarchy_publication.py', 'canonical_hierarchy_nostr.py')},
            'experiment_runner/json_projection.py': _hash(
                Path(json_projection.__file__)),
        }))
    if failure_type:
        result['failure_type'] = failure_type
    return result


@contextmanager
def saved_snapshot(directory):
    """Refuse an active native writer without modifying a historical directory."""
    path = Path(directory).resolve() / '.hierarchy-run.lock'
    if not path.exists():
        yield
        return
    with path.open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError('hierarchy execution is active; export after it stops') from error
        yield


def export_results(directory, output=None, *, execution_status=None, failure_type=None):
    """Write three compact files; the native caller holds its execution lock.

    Historical CLI callers use saved_snapshot. experiment.json is replaced last
    and binds the two payload hashes, so interrupted updates are detectable.
    Unchanged files retain their bytes and modification times.
    """
    directory = Path(directory).resolve()
    output = Path(output) if output is not None else directory / 'publication'
    if output.is_symlink():
        raise ValueError('publication output must not be a symlink')
    output = output.resolve()
    if output == directory or output in directory.parents:
        raise ValueError('publication output must not replace a source directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return _export_results(directory, output, execution_status, failure_type)
    finally:
        os.close(descriptor)


def _export_results(directory, output, execution_status, failure_type):
    state_path = directory / 'state.json'
    before = state_path.stat()
    with state_path.open('rb') as stream:
        source = _HashedInput(stream)
        state = json_projection.project(source, _STATE_FIELDS)
        state_hash = source.digest.hexdigest()
    after = state_path.stat()
    if ((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise ValueError('hierarchy state changed during publication export')
    selected = _selection(state)
    if execution_status not in (None, 'complete', 'blocked', 'stopped', 'failed'):
        raise ValueError('invalid hierarchy publication execution status')
    if output.exists():
        if (not output.is_dir() or {p.name for p in output.iterdir()} != set(FILES)
                or any(not (output/name).is_file() or (output/name).is_symlink() for name in FILES)):
            raise ValueError('publication destination contains unrelated files')
        with (output/'experiment.json').open(encoding='utf-8') as stream:
            previous = json.load(stream)
        if (previous.get('format') != FORMAT
                or previous.get('experiment_id') != directory.name
                or previous.get('source_id') != _identity(directory, state)):
            raise ValueError('publication destination belongs to a different experiment')
        if execution_status is None and previous.get('source_state_sha256') == state_hash:
            execution_status = previous.get('execution_status')
            if execution_status == 'not_recorded':
                execution_status = None
            failure_type = previous.get('failure_type')
    record = _record(directory, state, state_hash, selected, execution_status, failure_type)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.hierarchy-publication-', dir=output.parent) as temporary:
        staged = Path(temporary)
        selected_set, represented = set(selected), set()
        nodes = roots = 0
        with (staged/'hierarchy.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
            for event in unsigned_events(state):
                if event['kind'] == NODE_KIND:
                    nodes += 1
                    for tag in event['tags']:
                        if tag[0] == 'e':
                            if tag[1] not in selected_set:
                                raise ValueError('hierarchy references a note outside the recorded selection')
                            represented.add(tag[1])
                elif event['kind'] == ENTRY_KIND:
                    roots = len(event['tags'])
                json.dump(event, stream, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
                stream.write('\n')
        with (staged/'input-note-ids.txt').open('w', encoding='utf-8', newline='\n') as stream:
            for note in selected:
                stream.write(note + '\n')
        record['outcome'] = dict(nodes=nodes, roots=roots, represented_notes=len(represented))
        record['files'] = {name: _hash(staged/name) for name in FILES if name != 'experiment.json'}
        with (staged/'experiment.json').open('w', encoding='utf-8', newline='\n') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            stream.write('\n')
        # Stage and validate everything before touching existing public results.
        for name in FILES:
            with (staged/name).open('rb') as stream:
                os.fsync(stream.fileno())
        if not output.exists():
            staged.rename(output)
        else:
            for name in FILES:
                if _hash(output/name) != _hash(staged/name):
                    os.replace(staged/name, output/name)
    return dict(output=str(output), **record['outcome'], execution_status=record['execution_status'])
