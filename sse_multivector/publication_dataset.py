"""Select executed Oracle evidence for the shared dataset preparation step."""
import hashlib
import json
from contextlib import ExitStack
from pathlib import Path

from ._runner_bootstrap import shared


def sharing_rules():
    """Share whole scientific values without coalescing trial or case records."""
    rules = []

    def add(format, file, *paths):
        rules.extend(dict(format=format, file=file, path=list(path), min_bytes=256)
                     for path in paths)

    add('prompt-publication-v1', 'inputs.jsonl', ('inputs',))
    add('prompt-publication-v1', 'results.jsonl', ('output',), ('reviews',))
    for format in ('grading-publication-v1', 'review-evaluation-publication-v1'):
        add(format, 'answers.jsonl', ('answer',))
        add(format, 'judgments.jsonl', ())
    add('grading-publication-v1', 'results.jsonl', ('premises', '*', 'audits', '*'))
    add('review-evaluation-publication-v1', 'results.jsonl',
        ('checks', 'matching', '*', 'evidence'),
        ('checks', 'relationship', '*', 'evidence'),
        ('checks', 'support', '*', 'evidence'))
    add('evaluation-publication-v1', 'results.jsonl', ('answer',))
    return rules


def _prepared_only(directory, metadata):
    """A saved failure, answer, receipt or reuse always prevents omission."""
    if metadata.get('format') != 'prompt-publication-v1':
        return False
    outcome = metadata.get('outcome', {})
    if not outcome.get('cases') or outcome.get('unrun') != outcome['cases']:
        return False
    digest, count = hashlib.sha256(), 0
    with (directory / 'results.jsonl').open('rb') as stream:
        for line in stream:
            digest.update(line)
            row = json.loads(line)
            if (row.get('status') != 'unrun' or row.get('output') is not None
                    or row.get('reused') or row.get('receipt') or row.get('reused_from')
                    or row.get('origin') == 'mechanical' or row.get('attempt', 0)
                    or row.get('attempts', 0)):
                return False
            count += 1
    if (count != outcome['cases']
            or digest.hexdigest() != metadata['files']['results.jsonl']['sha256']):
        raise ValueError('unrun preparation payload does not match its saved metadata')
    return True


def _hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _execution_evidence(decision, roots):
    positive = {'experiment', 'report', 'runner_config', 'manifest'}
    negative = {'results_ledger', 'execution-settings.jsonl', 'code-upgrades.jsonl'}
    evidence = decision['evidence']
    if (not positive | negative <= evidence.keys()
            or any(evidence[name].get('exists') is not True for name in positive)
            or any(evidence[name].get('exists') is not False for name in negative)
            or decision['run_entries'] != ['manifest.json']):
        raise ValueError('unexecuted preparation evidence lacks required execution checks')
    label, relative = decision['source'].split(':', 1)
    root = Path(roots[label]).resolve()
    experiment = (root / relative).resolve()
    if not experiment.is_relative_to(root) or experiment.name != 'experiment.json':
        raise ValueError('invalid execution evidence source path')
    directory = experiment.parent
    run = Path(decision['resolved_run_directory'])
    paths = {'experiment': experiment, 'report': directory / 'report.json',
             'runner_config': directory / 'runner-config.json', 'manifest': run / 'manifest.json',
             'results_ledger': run / 'results.jsonl',
             'execution-settings.jsonl': directory / 'execution-settings.jsonl',
             'code-upgrades.jsonl': directory / 'code-upgrades.jsonl',
             'native_report': directory / 'native-report.json'}
    for name, expected in evidence.items():
        path = paths[name]
        if path.exists() != expected['exists'] or (expected['exists'] and _hash(path) != expected['sha256']):
            raise ValueError('execution evidence is stale: ' + decision['publication'])
    if sorted(p.name for p in run.iterdir()) != sorted(decision['run_entries']):
        raise ValueError('execution evidence is stale: run directory changed')
    return directory


def prepare(source, output, selection=None):
    """Require fresh, bound execution evidence before omitting an unrun snapshot."""
    source = Path(source).resolve()
    decisions, roots = {}, {}
    if selection is not None:
        evidence = json.loads(Path(selection).read_text())
        roots = json.loads(Path(evidence['source_mapping']).read_text())
        for row in evidence['publications']:
            identifier = row['publication']
            if identifier in decisions:
                raise ValueError('duplicate publication selection decision')
            decisions[identifier] = row
    excluded, unresolved, verified = {}, [], []
    for path in sorted(source.rglob('experiment.json')):
        metadata = json.loads(path.read_bytes())
        if not _prepared_only(path.parent, metadata):
            continue
        identifier = path.parent.relative_to(source).as_posix()
        decision = decisions.get(identifier)
        if decision is None:
            raise ValueError('saved unrun snapshot requires execution evidence via --selection: ' + identifier)
        snapshot = metadata.get('snapshot', {})
        if (decision['plan_sha256'] != metadata['source_id']
                or decision['evidence']['experiment']['sha256'] != snapshot.get('experiment_sha256')
                or decision['evidence']['report']['sha256'] != snapshot.get('report_sha256')
                or decision['exported_outcome'] != metadata['outcome']):
            raise ValueError('execution evidence does not bind the selected saved snapshot')
        if decision['decision'] == 'exclude_unexecuted_preparation':
            if not decision.get('source_snapshot_unchanged'):
                raise ValueError('unexecuted preparation evidence is not verified')
            excluded[identifier] = hashlib.sha256(path.read_bytes()).hexdigest()
            verified.append(decision)
        elif decision['decision'] == 'keep_unknown':
            unresolved.append(identifier)
        else:
            raise ValueError('unsupported publication selection decision')
    # Hold the native workflow's existing read locks through preparation. Opening
    # them does not create or alter files in the original experiment directories.
    with ExitStack() as locks:
        snapshot = shared('prompt_publication').saved_snapshot
        for decision in sorted(verified, key=lambda row: row['source']):
            label, relative = decision['source'].split(':', 1)
            directory = (Path(roots[label]) / relative).resolve().parent
            locks.enter_context(snapshot(directory))
            _execution_evidence(decision, roots)
        result = shared('publication_dataset').prepare_dataset(
            source, output, rules=sharing_rules(), excluded=excluded)
    return {**result, 'excluded_unexecuted_preparations': len(excluded),
            'retained_ambiguous_snapshots': unresolved}
