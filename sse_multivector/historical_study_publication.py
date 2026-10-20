"""Publish selected historical final evidence from explicitly hash-bound sources."""
from contextlib import contextmanager
import importlib
import json
from pathlib import Path, PurePosixPath
import re

from ._runner_bootstrap import shared
from .prompt_study_publication import _Sources, _json, _sha, _stamp


FORMAT = 'historical-study-publication-v1'
_PROFILES = {'atomic': 'atomic_study_publication',
             'subject-goal': 'subject_goal_publication',
             'mask-goal': 'mask_goal_publication',
             'standalone-prompt': 'standalone_prompt_publication',
             'prominence': 'prominence_study_publication',
             'title-audit': 'title_audit_publication',
             'segmentation-study': 'segmentation_study_publication',
             'frontier-study': 'frontier_study_publication',
             'baseline-study': 'baseline_study_publication',
             'saved-hierarchy': 'saved_hierarchy_publication',
             'navigation-study': 'navigation_study_publication',
             'performance-study': 'performance_study_publication'}


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _path(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or name != str(PurePosixPath(name)) or name.startswith('/')
            or any(part in ('', '.', '..') for part in name.split('/'))):
        raise ValueError('source path must be a portable repository-relative path')
    return name


def _bindings(value, result):
    if isinstance(value, list):
        for item in value:
            _bindings(item, result)
    elif isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            path, digest = _path(value['path']), value['sha256']
            if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('invalid selected source SHA-256')
            if path in result and result[path] != digest:
                raise ValueError('conflicting selected source hashes')
            result[path] = digest
        for item in value.values():
            _bindings(item, result)


class Sources:
    """Bounded reads of declared sources, including hash-bound moved files."""
    def __init__(self, root, selection, metadata):
        self.root = root
        self.bindings = {}
        _bindings(selection, self.bindings)
        self.hashes = metadata['sources']
        self._reader = _Sources(root, metadata)

    def raw(self, path):
        path = _path(path)
        if path not in self.bindings:
            raise ValueError('source is not selected with a SHA-256: ' + path)
        raw = self._reader.raw(self.root / path, path)
        if _sha(raw) != self.bindings[path]:
            raise ValueError('selected source hash mismatch: ' + path)
        return raw

    def read(self, path):
        return _json(self.raw(path))

    @contextmanager
    def stream(self, path):
        """Read a declared large source incrementally and verify its full bytes."""
        from . import numerical_publication

        path = _path(path)
        if path not in self.bindings:
            raise ValueError('source is not selected with a SHA-256: ' + path)
        source = self.root / path
        if not source.is_file():
            raise ValueError('missing saved study source: ' + path)
        code = Path(numerical_publication.__file__)
        code_stamp = _stamp(code)
        digest = _sha(code.read_bytes())
        label = 'sse_multivector/numerical_publication.py'
        exporters = self._reader.metadata.setdefault('exporter_sources', {})
        if exporters.get(label, digest) != digest:
            raise ValueError('publication code changed during export')
        exporters[label] = digest
        before = _stamp(source)
        with source.open('rb') as stream:
            reader = numerical_publication._Reader(stream)
            yield reader
            while reader.read(65536):
                pass
        if before != _stamp(source):
            raise ValueError('saved study source changed during export')
        if reader.digest.hexdigest() != self.bindings[path]:
            raise ValueError('selected source hash mismatch: ' + path)
        if code_stamp != _stamp(code):
            raise ValueError('publication code changed during export')
        self._reader.stamps[source] = before
        self.hashes[path] = reader.digest.hexdigest()

    def check(self):
        self._reader.check()


def export_results(source_root, spec, study_id, output=None):
    root, spec = Path(source_root).resolve(), Path(spec).resolve()
    if not root.is_dir():
        raise ValueError('historical study source root must be a directory')
    specification_reader = _Sources(spec.parent, {'sources': {}})
    specification = _json(specification_reader.raw(spec, 'selection'))
    if (not isinstance(specification, dict) or type(specification.get('schema_version')) is not int
            or specification['schema_version'] != 1
            or not isinstance(specification.get('studies'), dict)):
        raise ValueError('invalid historical study selection')
    if study_id not in specification['studies']:
        raise ValueError('study is not explicitly selected: ' + str(study_id))
    selection = specification['studies'][study_id]
    if not isinstance(selection, dict) or selection.get('profile') not in _PROFILES:
        raise ValueError('unsupported historical study profile')
    selected_sha = _sha(_canonical(selection))
    source_id = _sha(_canonical(dict(study_id=study_id, selection_sha256=selected_sha)))
    metadata = dict(schema_version=1, format=FORMAT, source_id=source_id,
                    experiment_id=study_id, profile=selection['profile'],
                    selection_sha256=selected_sha, sources={}, exporter_sources={})
    sources = Sources(root, selection, metadata)
    if not sources.bindings:
        raise ValueError('study has no selected source hashes')
    destination = Path(output) if output is not None else (
        root / 'target/publication-exports/historical-studies' / source_id)
    resolved = destination.resolve()
    if root == resolved or root.is_relative_to(resolved) or spec.is_relative_to(resolved):
        raise ValueError('publication destination overlaps study sources')
    if any((root / path).resolve().is_relative_to(resolved) for path in sources.bindings):
        raise ValueError('publication destination overlaps study sources')
    module = importlib.import_module('.' + _PROFILES[selection['profile']], __package__)
    writer = shared('publication_files')
    code = [Path(__file__), Path(module.__file__),
            Path(__file__).with_name('prompt_study_publication.py'),
            Path(__file__).with_name('_runner_bootstrap.py'), Path(writer.__file__)]
    code_stamps = {}
    for path in code:
        code_stamps[path] = _stamp(path)
        label = ('experiment_runner/' if path.parent.name == 'experiment_runner'
                 else 'sse_multivector/') + path.name
        metadata['exporter_sources'][label] = _sha(path.read_bytes())
    payloads = module.prepare(sources, selection, metadata)
    if set(payloads) != {'inputs.jsonl', 'answers.jsonl', 'judgments.jsonl', 'results.jsonl'}:
        raise ValueError('historical study profile must supply four final payloads')
    final_records = payloads['results.jsonl']

    def checked_results():
        yield from final_records
        # Also verify declared provenance sources not otherwise materialized by the profile.
        for path in sorted(sources.bindings.keys() - sources.hashes.keys()):
            sources.raw(path)
        sources.check()
        specification_reader.check()
        if any(_stamp(path) != stamp for path, stamp in code_stamps.items()):
            raise ValueError('publication code changed during export')
        for label, digest in metadata['exporter_sources'].items():
            if label.startswith('experiment_runner/'):
                path = Path(writer.__file__).parent / label.removeprefix('experiment_runner/')
            elif label.startswith('sse_multivector/'):
                path = Path(__file__).parent / label.removeprefix('sse_multivector/')
            else:
                raise ValueError('unsupported publication code source label')
            if _sha(path.read_bytes()) != digest:
                raise ValueError('publication code changed during export')
        metadata['source_snapshot_sha256'] = _sha(_canonical(sources.hashes))

    payloads['results.jsonl'] = checked_results()
    return writer.write_publication(destination, metadata, payloads)
