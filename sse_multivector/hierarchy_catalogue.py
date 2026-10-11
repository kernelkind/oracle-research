"""Offline version catalogue for saved hierarchy outputs and parameter evidence.

Original experiments are read only. IDs bind output bytes, their relative source
path, and adjacent parameter evidence; a copied checkout is not another run.
"""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import tempfile


SIDECARS = {
    'configuration.json', 'config.json', 'runner-config.json', 'worker-config.json',
    'worker-receipt.json', 'worker-run.json', 'encoder.json', 'manifest.json',
    'prepared-manifest.json', 'provenance.json', 'summary.json', 'selection.json',
    'construction.json', 'plan.json', 'experiment.json', 'inputs.json',
    'run-manifest.json', 'run-summary.json', 'calibration.json', 'request.json',
    'sources.json', 'validated-source.json', 'application.json', 'measurement.json',
    'bounded-build.json', 'packaging-manifest.json', 'native-fuzzy.json',
    'execution-plan.json', 'title-reports.json', 'decision-report.json',
}
# These contain graph/corpus/model-output data rather than experimental settings.
DATA_FIELDS = {
    'nodes', 'notes', 'subjects', 'posts', 'entries', 'cases', 'steps', 'groups',
    'edges', 'sp_edges', 'browsing_edges', 'original_edges', 'original_groups',
    'member_to_group', 'membership', 'merges', 'history', 'paths', 'modules',
    'root', 'alias_groups', 'canonical_unique_ids', 'vectors', 'predictions',
    'weights', 'coefficients', 'mask_instances', 'note_masks', 'local_meanings',
    'distances', 'input', 'inputs_text', 'response', 'output', 'raw', 'text',
    'content', 'judgments', 'decisions', 'examples', 'training_examples',
    'application', 'comparisons', 'applied', 'deferred', 'masks', 'mapping',
    'meaning_references', 'source_packets', 'naming_source_packets',
    'original_members', 'title_bindings', 'recorded_no', 'tree',
    'raw_edges', 'transitive_reduced_edges', 'reachability',
    'hierarchy', 'previous_preparation', 'previous_comparisons', 'internal_comparisons',
    'inherited_comparisons', 'pending_comparisons', 'unchanged_comparisons',
    'remapped_internal_comparisons', 'equivalent_answers', 'original_node_to_combined',
    'pairs', 'guides', 'unresolved_guides', 'skipped_guides',
    'alias_inspections_by_query', 'candidates_by_query',
}
SECRET_FIELDS = {'api_key', 'access_token', 'refresh_token', 'password', 'authorization'}
HEX = re.compile(r'^[0-9a-f]{64}$')
CANDIDATES = ('hierarchy.json', 'categories.json', 'state.json', 'results.json',
              'response.json', 'hdbscan-response.json', 'graph.json',
              'native-graph.json', 'graph.sqlite', 'result.json', 'tree.json',
              'categories-with-mask-ids.json')


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as stream:
        stream.write(raw)
        temporary = Path(stream.name)
    temporary.replace(path)


def parameters(value):
    """Retain saved settings and bindings, without embedding corpus/graph bodies."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key.lower() in SECRET_FIELDS:
                continue
            if key in DATA_FIELDS and isinstance(item, (dict, list, str)) and not (
                    isinstance(item, dict) and 'path' in item):
                continue
            if key in ('canonical_configuration_json',):
                result[key] = parameters(json.loads(item) if isinstance(item, str) else item)
            elif key != 'canonical_fine_output_json':
                result[key] = parameters(item)
        return result
    if isinstance(value, list):
        if len(value) > 100 and all(isinstance(v, (int, float, list)) for v in value):
            return {'values_omitted': len(value)}
        return [parameters(v) for v in value]
    return value


def classify(value):
    if not isinstance(value, dict):
        return None
    if 'nodes' in value and 'corpus' in value and 'steps' in value:
        return 'Canonical' if value['nodes'] else None
    if 'artifact' in value and isinstance(value['artifact'], dict):
        if 'canonical_configuration_json' in value['artifact']:
            return 'HDBSCAN'
    if 'groups' in value and value.get('schema_version') == 'containment-hierarchy-v1':
        return 'HiDeF'
    if 'tree' in value and 'original_members' in value and 'policy' in value:
        return 'Saved tree'
    if 'nodes' in value and 'original_edges' in value and 'settings' in value:
        return 'Saved graph'
    if 'merges' in value and value.get('schema_version') == 'merge-rule-experiment-v1':
        return 'Merge rules'
    if 'nodes' in value and ('notes' in value or 'roots' in value or 'root_node_id' in value):
        return value.get('method', 'Browsing export' if 'root_node_id' in value else 'Hierarchy')
    if 'nodes' in value and 'edges' in value:
        return 'Saved graph'
    if {'groups', 'member_to_group', 'edges'} <= value.keys():
        return 'Saved graph'
    if 'modules' in value and 'paths' in value:
        return 'Infomap'
    if 'levels' in value and ('partitions' in value or 'resolutions' in value):
        return 'HiDeF'
    if 'constrained' in value and 'unconstrained' in value and 'settings' in value:
        return 'Subject order'
    return None


def source_roots(source):
    spec = json.loads(source.read_text())
    if spec.get('schema_version') != 1:
        raise ValueError('unsupported catalogue source schema')
    roots = [(source.parent / p).resolve() for p in spec.get('roots', [])]
    if 'repository' in spec:
        repository = (source.parent / spec['repository']).resolve()
        output = subprocess.check_output(['git', '-C', str(repository), 'worktree', 'list', '--porcelain'], text=True)
        roots += [Path(line[9:]) for line in output.splitlines() if line.startswith('worktree ')]
    return sorted(set(roots), key=str)


def discover(root, destination):
    areas = [str(root / area) for area in ('target', 'sse_multivector') if (root / area).is_dir()]
    if not areas:
        return
    command = ['rg', '--files', '--hidden', '--no-ignore', '-0']
    for pattern in (*CANDIDATES, '*hierarchy*.json', 'M0[1-9].json'):
        command.extend(['-g', pattern])
    for pattern in ('node_modules', 'site-packages', '.venv', 'debug', 'release',
                    'fixtures', 'tests', '*smoke*', '*persistent-cost*', '*browser-test*',
                    'hierarchy-catalogue'):
        command.extend(['-g', f'!**/{pattern}/**'])
    found = subprocess.run(command + areas, capture_output=True)
    if found.returncode not in (0, 1):
        raise ValueError(found.stderr.decode())
    for name in found.stdout.split(b'\0'):
        if name:
            path = Path(name.decode())
            if destination not in path.parents:
                yield path


class Evidence:
    def __init__(self):
        self.cache = {}
        self.cache_stamps = {}
        self.hashes = {}
        self.written = set()

    def sha(self, path):
        path = path.resolve()
        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        prior = self.hashes.get(path)
        if prior is None or prior[:2] != stamp:
            self.hashes[path] = (*stamp, digest(path))
        return self.hashes[path][2]

    def load(self, path):
        path = path.resolve()
        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if self.cache_stamps.get(path) != stamp:
            raw = path.read_bytes()
            data = json.loads(raw)
            if path.name == 'experiment.json' and 'plan' in data:
                from experiment_runner import inputs
                if inputs.digest(data['plan']) != data.get('sha256'):
                    raise ValueError('saved experiment plan hash does not match')
            projection = {'data_records_omitted': len(data)} if isinstance(data, list) else parameters(data)
            self.cache[path] = (hashlib.sha256(raw).hexdigest(), projection)
            self.cache_stamps[path] = stamp
        return self.cache[path]

    def adjacent(self, path, root):
        result = set()
        for directory in (path.parent, *path.parent.parents):
            if directory in (root, root / 'target', root / 'sse_multivector'):
                break
            if root not in directory.parents:
                break
            for name in SIDECARS:
                candidate = directory / name
                if candidate.is_file() and candidate != path:
                    result.add(candidate)
            # Worker/runtime and native experiment metadata commonly live here.
            for sub in ('run', 'worker-result', 'encoder-run'):
                for name in SIDECARS:
                    candidate = directory / sub / name
                    if candidate.is_file() and candidate != path:
                        result.add(candidate)
        return sorted(result)

    def collect(self, path, root, direct, store):
        queue = list(self.adjacent(path, root))
        seen, evidence, bindings, unknown = set(), [], {}, []

        def reference(name, expected=None, parent=path.parent):
            if not isinstance(name, str) or '\n' in name or len(name) > 4096:
                return
            candidate = Path(name)
            if not candidate.is_absolute():
                candidate = parent / candidate
            if not candidate.exists():
                if expected:
                    bindings[str(candidate)] = {'sha256': expected, 'status': 'missing'}
                return
            if candidate.is_dir():
                queue.extend(candidate / n for n in SIDECARS if (candidate / n).is_file())
                return
            if expected:
                binding = {'sha256': expected, 'status': 'recorded (not rehashed)'}
                if candidate.suffix in {'.json', '.py', '.md', '.txt'}:
                    actual = self.sha(candidate)
                    binding.update(status='verified' if actual == expected else 'changed', actual_sha256=actual)
                bindings[str(candidate)] = binding
            if candidate.suffix == '.json' and (candidate.name in SIDECARS or
                    any(w in candidate.name for w in ('spec', 'source', 'recipe', 'model', 'policy'))):
                queue.append(candidate)

        def references(value, parent):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == 'path' or key.endswith('_path') or key in {'corpus', 'base_trial', 'history_root',
                            'experiment', 'preparation', 'source_model', 'source_experiment', 'subject_probe',
                            'probe_path', 'trial', 'selection_report'}:
                        reference(item, value.get('sha256') if key == 'path' else None, parent)
                    if isinstance(item, str) and HEX.fullmatch(item) and ('/' in key or key.endswith('.json')):
                        reference(key, item, parent)
                    references(item, parent)
            elif isinstance(value, list):
                for item in value:
                    references(item, parent)

        references(direct, path.parent)
        while queue:
            candidate = queue.pop(0).resolve()
            if candidate in seen or candidate == path:
                continue
            seen.add(candidate)
            try:
                sha, saved = self.load(candidate)
            except (OSError, ValueError):
                unknown.append(f'Unreadable parameter evidence: {candidate}')
                continue
            evidence.append({'path': str(candidate), 'sha256': sha, 'file': f'evidence/{sha}.json'})
            destination = store / f'evidence/{sha}.json'
            if sha not in self.written:
                write(destination, saved)
                self.written.add(sha)
            references(saved, candidate.parent)
        for name, binding in bindings.items():
            if binding['status'] in {'missing', 'changed'}:
                unknown.append(f"{binding['status'].capitalize()} frozen source: {name}")
        if not evidence:
            unknown.append('No saved configuration or provenance sidecar found.')
        unknown.append('Only saved settings and verified archived signature defaults are shown; other historical defaults remain unknown.')
        return sorted(evidence, key=lambda e: e['path']), bindings, sorted(set(unknown))


def archived_defaults(path, root, configuration):
    """Read defaults only from an archived source matching the recorded code hash."""
    methods = {'haus': 'geometric_haus.py', 'diffusion': 'geometric_diffusion.py',
               'fmc': 'geometric_fmc.py'}
    method = configuration.get('method')
    filename = methods.get(method)
    expected = configuration.get('code', {}).get(filename)
    if not expected:
        return None
    family = root / 'sse_multivector/geometric-hierarchy-v1'
    candidates = [path.parent / filename, family / 'GHA01' / filename,
                  family / 'GFM01' / filename]
    candidates += list((family / 'code').glob('*.py'))
    for candidate in candidates:
        if not candidate.is_file() or digest(candidate) != expected:
            continue
        tree = ast.parse(candidate.read_text())
        defaults = {}
        fixed_calls = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ('fit', 'fit_affinity'):
                args = node.args.args[-len(node.args.defaults):] if node.args.defaults else []
                pairs = list(zip(args, node.args.defaults)) + list(zip(node.args.kwonlyargs, node.args.kw_defaults))
                for argument, value in pairs:
                    if value is not None:
                        try:
                            defaults[argument.arg] = ast.literal_eval(value)
                        except ValueError:
                            pass
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'KMeans':
                settings = {}
                for keyword in node.keywords:
                    if keyword.arg:
                        try:
                            settings[keyword.arg] = ast.literal_eval(keyword.value)
                        except ValueError:
                            settings[keyword.arg] = {'source_expression': ast.unparse(keyword.value)}
                fixed_calls.append({'call': 'KMeans', 'settings': settings})
        return {'source': str(candidate), 'sha256': expected,
                'signature_defaults': defaults, 'fixed_calls': fixed_calls,
                'overrides': configuration.get('config', {})}
    return None


def sqlite_snapshot(path, directory):
    destination = directory / 'snapshot.sqlite'
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source:
        tables = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'entries', 'owners', 'edges'} <= tables:
            return None
        with sqlite3.connect(destination) as target:
            source.backup(target)
            counts = {'entries': target.execute('SELECT COUNT(*) FROM entries').fetchone()[0],
                      'groups': target.execute('SELECT COUNT(*) FROM owners WHERE id=parent').fetchone()[0],
                      'raw_edges': target.execute('SELECT COUNT(*) FROM edges').fetchone()[0]}
    return destination, counts



CODE_SUFFIXES = {'.py', '.rs', '.sh', '.js', '.ts', '.nix', '.toml', '.lock', '.md', '.txt'}


class CodeSources:
    """Preserve only source bytes matching a run's recorded SHA-256."""
    def __init__(self, roots, output, evidence):
        self.roots, self.output, self.evidence = roots, output, evidence
        self.resolved, self.history = {}, {}

    def preserve(self, recorded, expected):
        key = (recorded, expected)
        path = Path(recorded)
        suffix = path.suffix if path.suffix in CODE_SUFFIXES else '.source'
        destination = self.output / 'code' / f'{expected}{suffix}'
        result = {'recorded_path': recorded, 'sha256': expected,
                  'kind': 'prompt or text source' if path.suffix in {'.md', '.txt'} else 'code'}
        if destination.exists():
            if digest(destination) != expected:
                raise ValueError(f'changed preserved source: {destination}')
            result.update(status='preserved', snapshot=str(destination.relative_to(self.output)))
            self.resolved[key] = result
            return result
        if key in self.resolved:
            return self.resolved[key]
        candidates = [path]
        relative = None
        for root in self.roots:
            if root in path.parents:
                relative = path.relative_to(root)
                candidates += [other / relative for other in self.roots]
                break
        raw, origin = None, None
        for candidate in candidates:
            if candidate.is_file() and self.evidence.sha(candidate) == expected:
                raw, origin = candidate.read_bytes(), {'path': str(candidate)}
                break
        if raw is None:
            parent = path.parent
            while not parent.exists() and parent != parent.parent:
                parent = parent.parent
            repository = subprocess.run(['git', '-C', str(parent), 'rev-parse', '--show-toplevel'],
                                        capture_output=True, text=True)
            if repository.returncode == 0:
                repo = Path(repository.stdout.strip())
                if repo in path.parents:
                    relative = str(path.relative_to(repo))
                    common = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', '--git-common-dir'], text=True).strip()
                    history_key = (str((repo / common).resolve()), relative)
                    if history_key not in self.history:
                        objects = subprocess.check_output(['git', '-C', str(repo), 'rev-list', '--objects', '--all', '--', relative], text=True)
                        blobs = {line.split(' ', 1)[0] for line in objects.splitlines()
                                 if line.endswith(' ' + relative)}
                        matches = {}
                        for blob in blobs:
                            content = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'blob', blob])
                            matches[hashlib.sha256(content).hexdigest()] = blob
                        self.history[history_key] = matches
                    blob = self.history[history_key].get(expected)
                    if blob:
                        raw = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'blob', blob])
                        origin = {'repository': str(repo), 'git_blob': blob}
        if raw is not None and hashlib.sha256(raw).hexdigest() == expected:
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(raw)
            result.update(status='preserved', snapshot=str(destination.relative_to(self.output)), recovered_from=origin)
        else:
            result['status'] = 'unknown: matching source bytes unavailable'
        self.resolved[key] = result
        return result

    def record(self, row, documents):
        references = {(path, binding['sha256']) for path, binding in row['bindings'].items()
                      if Path(path).suffix in CODE_SUFFIXES}
        commits = set()

        def visit(value, parent):
            if isinstance(value, dict):
                for field in ('path', 'source', 'source_path'):
                    if isinstance(value.get(field), str) and HEX.fullmatch(str(value.get('sha256', ''))):
                        path = Path(value[field])
                        if path.suffix in CODE_SUFFIXES:
                            references.add((str(path if path.is_absolute() else parent / path), value['sha256']))
                for key, item in value.items():
                    if isinstance(item, str) and HEX.fullmatch(item) and Path(key).suffix in CODE_SUFFIXES:
                        path = Path(key)
                        references.add((str(path if path.is_absolute() else parent / path), item))
                    if key in {'commit', 'git_commit', 'source_commit', 'code_commit', 'git_revision'} and isinstance(item, str) and re.fullmatch(r'[0-9a-f]{7,40}', item):
                        commits.add(item)
                    visit(item, parent)
            elif isinstance(value, list):
                for item in value:
                    visit(item, parent)

        visit(row['parameters'], Path(row['locations'][0]).parent)
        for item in row['evidence']:
            visit(documents[item['sha256']], Path(item['path']).parent)
        # M01–M09 recorded the module hash without its filename.
        if row['family'] == 'Merge rules' and HEX.fullmatch(str(row['parameters'].get('source_code_sha256', ''))):
            references.add((str(self.roots[0] / 'sse_multivector/merge_rule_experiment.py'), row['parameters']['source_code_sha256']))
        grouped = {}
        for path, sha in references:
            grouped.setdefault(sha, set()).add(path)
        files = []
        for sha, paths in sorted(grouped.items()):
            choices = [self.preserve(path, sha) for path in sorted(paths)]
            chosen = next((c for c in choices if c['status'] == 'preserved'), choices[0])
            files.append({**chosen, 'recorded_paths': sorted(paths)})
        return {'recorded_commits': sorted(commits),
                'commit_status': 'recorded' if commits else 'unknown: not recorded',
                'files': files,
                'coverage': 'Only source files identified by saved hashes; unrecorded files and dependency defaults remain unknown.'}


def catalogue(source, registry, output, *, saved_only=False):
    source, registry, output = source.resolve(), registry.resolve(), output.resolve()
    roots = source_roots(source)
    for root in roots:
        if output == root or root in output.parents and output.parts[len(root.parts)] != 'target':
            raise ValueError('catalogue output must be under target or outside source checkouts')
    output.mkdir(parents=True, exist_ok=True)
    saved = json.loads(registry.read_text()) if registry.exists() else {'schema_version': 1, 'versions': []}
    if saved.get('schema_version') != 1:
        raise ValueError('unsupported version registry schema')
    versions = {r['identity']: r for r in saved['versions']}
    if len(versions) != len(saved['versions']) or len({r['version_id'] for r in versions.values()}) != len(versions):
        raise ValueError('duplicate version registry identity or ID')
    number = max((int(r['version_id'][1:]) for r in versions.values()), default=0)
    evidence = Evidence()
    payloads = {}
    current = {}
    errors = []
    candidates = 0
    if saved_only:
        prior = json.loads((output / 'catalogue.json').read_text())
        current = {row['identity']: row for row in prior['hierarchies'] if row['currently_discovered']}
        errors, candidates = prior['discovery_errors'], prior['candidates_checked']
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        for root in ([] if saved_only else roots):
            for path in sorted(discover(root, output)):
                candidates += 1
                relative = str(path.relative_to(root))
                try:
                    if path.suffix == '.sqlite':
                        snapshot = sqlite_snapshot(path, Path(temporary))
                        if snapshot is None:
                            continue
                        artifact, stats = snapshot
                        data, family = {'sqlite_counts': stats}, 'Local SQLite'
                    else:
                        artifact = path
                        raw = path.read_bytes()
                        sha = hashlib.sha256(raw).hexdigest()
                        if sha not in payloads:
                            data = json.loads(raw)
                            payloads[sha] = (classify(data), parameters(data))
                        family, data = payloads[sha]
                        if family is None:
                            continue
                    if path.suffix == '.sqlite':
                        sha = digest(artifact)
                    direct = parameters(data)
                    adjacent = evidence.adjacent(path, root)
                    adjacent_hashes = {str(p.relative_to(root)): evidence.sha(p) for p in adjacent}
                    identity = hashlib.sha256(encoded([relative, sha, adjacent_hashes])).hexdigest()
                    if identity in current:
                        current[identity]['locations'].append(str(path))
                        continue
                    configuration = path.parent / 'configuration.json'
                    if configuration.exists():
                        defaults = archived_defaults(path, root, evidence.load(configuration)[1])
                        if defaults:
                            direct['archived_method_defaults'] = defaults
                    refs, bindings, unknown = evidence.collect(path, root, direct, output)
                    if identity not in versions:
                        number += 1
                        versions[identity] = {'version_id': f'H{number:04d}', 'identity': identity,
                                             'artifact_path': relative, 'sha256': sha, 'family': family}
                    version = versions[identity]['version_id']
                    snapshot_path = output / 'outputs' / f'{version}{path.suffix}'
                    snapshot_path.parent.mkdir(exist_ok=True)
                    if snapshot_path.exists() and digest(snapshot_path) != sha:
                        raise ValueError(f'changed immutable snapshot: {snapshot_path}')
                    if not snapshot_path.exists():
                        if path.suffix == '.sqlite':
                            shutil.copyfile(artifact, snapshot_path)
                        else:
                            snapshot_path.write_bytes(raw)
                    name = data.get('run_id') or data.get('experiment_id') or data.get('hierarchy_id') or path.parent.name
                    text = json.dumps([direct, [evidence.cache[Path(e['path'])][1] for e in refs]])
                    subject_versions = sorted(set(re.findall(r'ASv\d+\.\d+', text)))
                    older = any(tuple(map(int, v[3:].split('.'))) < (6, 100) for v in subject_versions)
                    status = ('historical/deprecated' if older else
                              'source recorded: ' + ', '.join(subject_versions) if subject_versions else 'subject version unknown')
                    row = {**versions[identity], 'name': name, 'source_status': status,
                           'subject_versions': subject_versions, 'run_status': data.get('status', 'saved'),
                           'output': str(snapshot_path.relative_to(output)), 'locations': [str(path)],
                           'parameters': direct, 'evidence': refs, 'bindings': bindings, 'unknown': unknown}
                    current[identity] = row
                except (OSError, ValueError, sqlite3.Error) as error:
                    errors.append({'path': str(path), 'error': str(error)})
    rows = []
    for record in sorted(versions.values(), key=lambda r: r['version_id']):
        path = output / 'records' / f"{record['version_id']}.json"
        row = current.get(record['identity'])
        if row is not None:
            if path.exists():
                previous = json.loads(path.read_text())
                if previous['identity'] != row['identity'] or previous['sha256'] != row['sha256']:
                    raise ValueError(f'changed retained version record: {path}')
                # Preserve settings recovered while their frozen sources existed.
                # Later edits to a source must not replace that historical evidence.
                prior_evidence = {e['path']: e for e in previous['evidence']}
                row['evidence'] = [prior_evidence.get(e['path'], e) for e in row['evidence']]
                row['evidence'] += [e for e in previous['evidence'] if e['path'] not in {n['path'] for n in row['evidence']}]
                row['parameters'] = {**previous['parameters'], **row['parameters']}
            write(path, row)
        elif path.exists():
            row = json.loads(path.read_text())
        else:
            raise ValueError(f"missing retained record for {record['version_id']}; preserve the catalogue output directory")
        row = {**row, 'currently_discovered': record['identity'] in current}
        rows.append(row)
    by_sha = {}
    for row in rows:
        by_sha.setdefault(row['sha256'], []).append(row['version_id'])
    for row in rows:
        row['same_output_versions'] = [v for v in by_sha[row['sha256']] if v != row['version_id']]
        row['source_versions'] = sorted({v for binding in row['bindings'].values()
                                        for v in by_sha.get(binding['sha256'], []) if v != row['version_id']})
    documents = {sha: parameters(json.loads((output / 'evidence' / f'{sha}.json').read_text()))
                 for sha in sorted({e['sha256'] for r in rows for e in r['evidence']})}
    code_sources = CodeSources(roots, output, evidence)
    for row in rows:
        row['generator_code'] = code_sources.record(row, documents)
        write(output / 'records' / f"{row['version_id']}.json", row)
    result = {'schema_version': 1, 'generated_at': datetime.now(timezone.utc).isoformat(),
              'roots': [str(r) for r in roots], 'hierarchies': rows, 'discovery_errors': errors,
              'candidates_checked': candidates,
              'parameter_evidence': documents}
    write(output / 'catalogue.json', result)
    template = Path(__file__).with_name('hierarchy_catalogue.html').read_text()
    payload = json.dumps(result, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    (output / 'index.html').write_text(template.replace('__CATALOGUE__', payload))
    write(registry, {'schema_version': 1, 'versions': sorted(versions.values(), key=lambda r: r['version_id'])})
    return {'hierarchies': len(rows), 'currently_discovered': len(current), 'copies': sum(len(r['locations']) - 1 for r in current.values()),
            'families': dict(Counter(r['family'] for r in rows)), 'errors': errors, 'catalogue': str(output / 'index.html'), 'inference_calls': 0}
