"""Replace a saved epsilon section with its native synthetic definition.

Preparation reuses every remaining original vector, including unassigned ones.
Run the ordinary SSE worker on the single prepared encoding, then collect to
rerun the original HDBSCAN configuration and the unchanged epsilon rule.
No teacher calls or saved hierarchy edits are performed.
"""
import argparse
from copy import deepcopy
import hashlib
from html import escape
import json
from pathlib import Path
import subprocess

from . import hdbscan_epsilon_review as review
from . import hierarchy_generation as generation
from . import worker
from . import experiment as workflow


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(directory, experiment, case_id, *, replacement_review=None, section=None):
    directory = Path(directory).resolve()
    experiment = Path(experiment).resolve()
    native, _, _ = workflow.load(experiment)
    if native['dataset']['adapter'] != 'hierarchy_group_consolidation':
        raise ValueError('replacement requires a native grouped-consolidation section')
    with workflow.report_scope(isolated=True):
        result = workflow.report(experiment, only={case_id}, include_request_preview=False)
    if len(result['cases']) != 1 or result['cases'][0]['status'] != 'valid':
        raise ValueError('replacement requires one valid native synthetic meaning')
    case = result['cases'][0]
    evidence = case.get('evidence', {})
    if replacement_review is not None:
        if section is None:
            raise ValueError('saved group replacement requires a section')
        return _prepare_next(directory, experiment, case, source=dict(schema_version=1,
            replacement_review=str(Path(replacement_review).resolve()), section=section, stage='section'))
    if 'replacement_review' in evidence:
        return _prepare_next(directory, experiment, case)
    if not {'epsilon_review', 'state', 'section', 'groups'} <= set(evidence):
        raise ValueError('replacement requires source-bound epsilon section evidence')
    sources = {}

    def read_bytes(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if str(path) in sources and sources[str(path)] != digest:
            raise ValueError('replacement source changed during preparation: ' + str(path))
        sources[str(path)] = digest
        return raw

    def read(path):
        return json.loads(read_bytes(path))

    expected, _ = review.prepare_section_source(dict(schema_version=1,
        epsilon_review=evidence['epsilon_review'], section=evidence['section']),
        experiment, read, read_bytes)
    if (expected[0]['id'] != case_id or expected[0]['inputs'] != case['inputs']
            or expected[0]['evidence'] != evidence):
        raise ValueError('replacement producer differs from the original section')
    state = read(evidence['state'])
    analysis = read(evidence['epsilon_review'])
    groups = {g['id']: g for g in analysis['groups']}
    removed = sorted(i for g in evidence['groups'] for i in groups[g]['original_ids'])
    removed_set = set(removed)
    original_ids = state['families'][0]['rounds'][0]['current']
    if len(removed_set) != len(removed) or not removed_set <= set(original_ids):
        raise ValueError('replacement membership is not a unique original subset')
    retained = [i for i in original_ids if i not in removed_set]
    for path, expected_hash in {**native['sources'], **{
            str(experiment/name): value for name, value in native['files'].items()}}.items():
        if hashlib.sha256(read_bytes(path)).hexdigest() != expected_hash:
            raise ValueError('native replacement producer changed: ' + str(path))
    for path in [experiment/'experiment.json', Path(native['run_directory'])/'manifest.json',
                 case['receipt']['results_path'], state['hdbscan_binary']]:
        read_bytes(path)
    for path in [Path(__file__), Path(review.__file__), Path(generation.__file__),
                 Path(worker.__file__), Path(review.hdbscan.__file__)]:
        read_bytes(path)
    replacement = dict(subject=case['parsed']['title'], meaning=case['parsed']['meaning'],
                       original_ids=removed)
    pool = dict(generation_policy=state['generation_policy'], originals=state['originals'],
                note_ids=state['note_ids'], worker_config=state['worker_config'],
                items={i: deepcopy(state['items'][i]) for i in retained},
                encodings=deepcopy(state['encodings']), vectors=deepcopy(state['vectors']),
                sources={str(Path(worker.__file__).resolve()): sha(worker.__file__)})
    pool['items']['R00001'] = replacement
    directory.mkdir(parents=True, exist_ok=False)
    first_new_encoding = len(pool['encodings'])
    generation._prepare_encoding(directory, pool, ['R00001'])
    plan = dict(schema_version=1, experiment=str(experiment), case=case_id,
                receipt=case['receipt'], source_state=evidence['state'],
                source_review=evidence['epsilon_review'], removed_ids=removed,
                current_ids=retained+['R00001'], first_new_encoding=first_new_encoding,
                hdbscan_binary=state['hdbscan_binary'], sources=sources, pool=pool)
    workflow.write(directory/'replacement.json', dict(plan=plan, sha256=workflow.inputs.digest(plan)))
    return dict(removed_entries=len(removed), reused_vectors=len(retained),
                updated_entries=len(retained)+1, worker_configs=[j['config'] for j in
                pool['encodings'][first_new_encoding:]])


def _load_replacement(directory):
    directory = Path(directory).resolve()
    envelope = workflow.read(directory/'replacement.json')
    plan = envelope['plan']
    if workflow.inputs.digest(plan) != envelope['sha256']:
        raise ValueError('prepared replacement changed')
    for path, expected in plan['sources'].items():
        if sha(path) != expected:
            raise ValueError('replacement source changed: ' + path)
    return plan


def prepare_from(directory, source, *, exclude_unassigned=False):
    """Reuse a completed synthetic encoding, optionally filtering original noise."""
    directory, source = Path(directory).resolve(), Path(source).resolve()
    plan = _load_replacement(source)
    pool = plan['pool']
    generation._collect_encodings(pool)
    if any(not j['complete'] for j in pool['encodings']):
        raise ValueError('source replacement SSE encoding is incomplete')
    analysis = workflow.read(plan['source_review'])
    assigned = {i for g in analysis['groups'] for i in g['original_ids']}
    original_ids = {o['id'] for o in pool['originals']}
    excluded = sorted(i for i in plan['current_ids'] if i in original_ids and i not in assigned)
    excluded_set = set(excluded)
    ids = [i for i in plan['current_ids']
           if not exclude_unassigned or i not in excluded_set]
    pool['items'] = {i: pool['items'][i] for i in ids}
    origins = {o['id']: o['local']['note_id'] for o in pool['originals']}
    note_ids = {origins[o] for i in ids for o in pool['items'][i]['original_ids']}
    pool['note_ids'] = [n for n in pool['note_ids'] if n in note_ids]
    sources = plan['sources']
    for path in [source/'replacement.json', Path(__file__), Path(review.__file__),
                 Path(generation.__file__), Path(worker.__file__), Path(review.hdbscan.__file__)]:
        path = path.resolve()
        sources[str(path)] = sha(path)
    plan.update(current_ids=ids, first_new_encoding=len(pool['encodings']),
                source_replacement=str(source), exclude_unassigned=exclude_unassigned,
                excluded_unassigned_ids=excluded if exclude_unassigned else [])
    directory.mkdir(parents=True, exist_ok=False)
    workflow.write(directory/'replacement.json', dict(plan=plan, sha256=workflow.inputs.digest(plan)))
    return dict(updated_entries=len(ids), reused_vectors=len(ids), worker_configs=[],
                excluded_unassigned=len(plan['excluded_unassigned_ids']))


def saved_review(directory, *, execute=False):
    """Validate and reconstruct a replacement review without modifying its inputs."""
    directory = Path(directory).resolve()
    plan = _load_replacement(directory)
    pool = plan['pool']
    generation._collect_encodings(pool)
    if any(not j['complete'] for j in pool['encodings']):
        raise ValueError('replacement SSE encoding is incomplete')
    ids = plan['current_ids']
    vectors = generation._vectors(pool, ids)
    request, mapping = review.hdbscan.request_for(pool, ids, vectors)
    request_path, result_path = directory/'request.json', directory/'result.json'
    if execute:
        generation.trial._save_once(request_path, request)
    elif workflow.read(request_path) != request:
        raise ValueError('replacement request differs from saved vectors')
    if not result_path.exists():
        if not execute:
            raise ValueError('replacement HDBSCAN result is incomplete')
        executed = subprocess.run([plan['hdbscan_binary'], str(request_path)],
                                  capture_output=True, check=False)
        (directory/'stderr.txt').write_bytes(executed.stderr)
        if executed.returncode:
            raise ValueError('HDBSCAN command failed: ' + executed.stderr.decode(errors='replace'))
        response = json.loads(executed.stdout)
        review.hdbscan.members(response, request, mapping)
        generation.trial._save_once(result_path, response)
    response = workflow.read(result_path)
    new_encodings = sum(len(j['keys']) for j in pool['encodings'][plan['first_new_encoding']:])
    provenance = dict(source_state=plan['source_state'], source_review=plan['source_review'],
        replacement_experiment=plan['experiment'], replacement_case=plan['case'],
        replacement_receipt=plan['receipt'], sources=plan['sources'],
        configuration=request['hdbscan_configuration'], request=str(request_path),
        request_sha256=sha(request_path), result=str(result_path), result_sha256=sha(result_path),
        new_model_calls=0, new_encodings=new_encodings, reused_vectors=len(ids)-new_encodings,
        encoder_receipts=[dict(config=j['config'], receipt_sha256=j['receipt_sha256'])
                          for j in pool['encodings']])
    if 'source_replacement' in plan:
        provenance.update(source_replacement=plan['source_replacement'],
            exclude_unassigned=plan.get('exclude_unassigned', False),
            excluded_unassigned_ids=plan.get('excluded_unassigned_ids', []))
    result = review.group_review(response, request, mapping, pool, provenance)
    identifier = plan.get('replacement_id', 'R00001')
    original_notes = {o['id']: o['local']['note_id'] for o in pool['originals']}
    replacements = []
    for key in ids:
        if key in original_notes:
            continue
        item = pool['items'][key]
        group = next((g for g in result['groups'] if key in g['original_ids']), None)
        section = next((f'S{i+1:02d}' for i, s in enumerate(result['sections'])
                        if group and group['id'] in s['groups']), None)
        replacements.append(dict(id=key, title=item['subject'], meaning=item['meaning'],
            original_ids=item['original_ids'],
            note_ids=sorted({original_notes[i] for i in item['original_ids']}),
            group=group['id'] if group else None, section=section))
    result.update(encoded_entries=len(ids), assigned_entries=sum(g['entries'] for g in result['groups']),
        replacement=next(r for r in replacements if r['id'] == identifier))
    if 'replacement_id' in plan:
        result['replacements'] = replacements
    return result


def collect(directory, *, name='reclustered-sections'):
    directory = Path(directory).resolve()
    result = saved_review(directory, execute=True)
    review.write_review(result, directory, title='HDBSCAN after synthetic section replacement', name=name)
    return dict(groups=len(result['groups']), sections=len(result['sections']),
        epsilon=result['selection']['epsilon'], represented_notes=result['represented_notes'],
        replacement_group=result['replacement']['group'], replacement_section=result['replacement']['section'],
        svg=str(directory/(name+'.svg')))


def _saved_case(directory, case_id, read_bytes):
    """Freeze a validated native result together with its unchanged producer."""
    directory = Path(directory).resolve()
    native, _, _ = workflow.load(directory)
    if native['dataset']['adapter'] != 'hierarchy_group_consolidation':
        raise ValueError('group definition requires a grouped-consolidation producer')
    with workflow.report_scope(isolated=True):
        report = workflow.report(directory, only={case_id}, include_request_preview=False)
    if len(report['cases']) != 1 or report['cases'][0]['status'] != 'valid':
        raise ValueError('group definition requires one valid native result')
    row = report['cases'][0]
    if not row.get('receipt'):
        raise ValueError('group definition requires a native receipt')
    for path, expected in {**native['sources'], **{
            str(directory/name): digest for name, digest in native['files'].items()}}.items():
        if hashlib.sha256(read_bytes(Path(path))).hexdigest() != expected:
            raise ValueError('group producer changed: ' + str(path))
    for path in [directory/'experiment.json', Path(native['run_directory'])/'manifest.json',
                 Path(row['receipt']['results_path'])]:
        read_bytes(path)
    return row, dict(experiment=str(directory), case=case_id, receipt=row['receipt'])


def prepare_source(source, base, read, read_bytes):
    """Name changed groups first, then name their reviewed section from definitions."""
    fields = {'schema_version', 'replacement_review', 'section', 'stage'}
    if 'group_experiment' in source:
        fields.add('group_experiment')
    if (set(source) != fields or type(source['schema_version']) is not int
            or source['schema_version'] != 1
            or any(not isinstance(source[k], str) or not source[k]
                   for k in fields-{'schema_version'}) or source['stage'] not in {'groups', 'section'}):
        raise ValueError('replacement consolidation requires schema 1, review, section and stage')
    if source['stage'] == 'groups' and 'group_experiment' in source:
        raise ValueError('group experiment applies only to section consolidation')
    analysis_path = workflow.resolve(source['replacement_review'], base)
    directory = analysis_path.parent
    plan = _load_replacement(directory)
    analysis = read(analysis_path)
    if saved_review(directory) != analysis:
        raise ValueError('replacement review differs from saved native evidence')
    for path, expected in plan['sources'].items():
        if hashlib.sha256(read_bytes(Path(path))).hexdigest() != expected:
            raise ValueError('replacement source changed: ' + path)
    for name in ['replacement.json', 'request.json', 'result.json']:
        read_bytes(directory/name)
    pool = plan['pool']
    for job in pool['encodings']:
        read_bytes(Path(job['config']))
        config = worker.WorkerConfig.load(Path(job['config']))
        read_bytes(config.output_path/'worker-receipt.json')
    sections = {f'S{i+1:02d}': s for i, s in enumerate(analysis['sections'])}
    if source['section'] not in sections:
        raise ValueError('unknown replacement section: ' + source['section'])
    selected = sections[source['section']]['groups']
    if not selected:
        raise ValueError('section consolidation requires a group')
    single = len(selected) == 1
    if single and 'group_experiment' in source:
        raise ValueError('one-group section requires no intermediate group experiment')
    groups = {g['id']: g for g in analysis['groups']}
    state = read(Path(plan['source_state']))
    leaves = {frozenset(s['original_ids']): s for s in
              state['hdbscan_sections']['sections'] if s['group']}
    native_nodes = {n['item']: n for n in state['nodes']}
    cases, definitions, witnesses = [], [], []
    common = dict(replacement_review=str(analysis_path), state=plan['source_state'],
                  section=source['section'], epsilon=analysis['selection']['epsilon'])
    for group_id in selected:
        group = groups[group_id]
        ids = group['original_ids']
        payload = dict(nodes=[dict(title=pool['items'][i]['subject'], meaning=pool['items'][i]['meaning'])
                              for i in ids])
        inputs = dict(INPUT_JSON=json.dumps(payload, ensure_ascii=False))
        group_case = dict(id=f'{source["section"]}-G{group_id:02d}', inputs=inputs,
            evidence=dict(common, stage='group', groups=[group_id], input_ids=ids,
                          note_ids=group['note_ids']))
        leaf = leaves.get(frozenset(ids))
        node = native_nodes.get(leaf.get('item')) if leaf else None
        if single:
            group_case['id'] = source['section']
            group_case['evidence'].update(stage='section', group_nodes=[])
            if node:
                saved, producer = _saved_case(node['synthetic']['experiment'], node['synthetic']['case'], read_bytes)
                if (saved['inputs'] != inputs or saved['parsed'] != dict(title=node['subject'], meaning=node['meaning'])):
                    raise ValueError('saved group definition differs from exact current group input')
                group_case['evidence']['group_nodes'] = [dict(
                    group=group_id, input_ids=ids, reused=True, producer=producer)]
            return [group_case], dict(application_allowed=False,
                purpose='One group supplies its section definition directly; no one-node consolidation.')
        if node:
            saved, producer = _saved_case(node['synthetic']['experiment'], node['synthetic']['case'], read_bytes)
            if (saved['inputs'] != inputs or saved['parsed'] != dict(title=node['subject'], meaning=node['meaning'])):
                raise ValueError('saved group definition differs from exact current group input')
            reused = True
        elif source['stage'] == 'groups':
            cases.append(group_case)
            continue
        else:
            if 'group_experiment' not in source:
                raise ValueError('changed groups require a completed group experiment')
            group_directory = workflow.resolve(source['group_experiment'], base)
            saved, producer = _saved_case(group_directory, group_case['id'], read_bytes)
            if saved['inputs'] != inputs or saved['evidence'] != group_case['evidence']:
                raise ValueError('group definition differs from its exact reviewed group')
            reused = False
        definitions.append(saved['parsed'])
        witnesses.append(dict(group=group_id, input_ids=ids, reused=reused, producer=producer))
    if source['stage'] == 'section':
        input_ids = [i for g in selected for i in groups[g]['original_ids']]
        evidence = dict(common, stage='section', groups=selected, input_ids=input_ids,
                        group_nodes=witnesses,
                        note_ids=sorted({n for g in selected for n in groups[g]['note_ids']}))
        if 'group_experiment' in source:
            evidence['group_experiment'] = str(workflow.resolve(source['group_experiment'], base))
        cases = [dict(id=source['section'], inputs=dict(
            INPUT_JSON=json.dumps(dict(nodes=definitions), ensure_ascii=False)), evidence=evidence)]
    elif not cases:
        raise ValueError('all selected groups already have exact saved definitions; prepare the section directly')
    return cases, dict(application_allowed=False,
        purpose='Name reviewed groups, then their synthetic section; preserve saved hierarchies.')


def _section_result(experiment, case, *, source=None):
    """Validate one section result and freeze all of its exact source evidence."""
    evidence = case['evidence']
    reuse = source is not None
    if not reuse and evidence.get('stage') != 'section':
        raise ValueError('replacement requires a completed section definition, not a group')
    sources = {}

    def read_bytes(path):
        path = Path(path).resolve()
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if str(path) in sources and sources[str(path)] != digest:
            raise ValueError('replacement source changed during preparation: ' + str(path))
        sources[str(path)] = digest
        return raw

    def read(path):
        return json.loads(read_bytes(path))

    if not reuse:
        source = dict(schema_version=1, replacement_review=evidence['replacement_review'],
                      section=evidence['section'], stage='section')
        if 'group_experiment' in evidence:
            source['group_experiment'] = evidence['group_experiment']
    expected, _ = prepare_source(source, experiment, read, read_bytes)
    if reuse:
        witnesses = expected[0]['evidence']['group_nodes']
        if (len(witnesses) != 1 or not witnesses[0]['reused']
                or witnesses[0]['producer'] != dict(experiment=str(experiment),
                    case=case['id'], receipt=case['receipt'])):
            raise ValueError('saved definition is not the exact native group in this section')
        evidence = expected[0]['evidence']
    if (expected[0]['inputs'] != case['inputs'] or (not reuse and
            (expected[0]['id'] != case['id'] or expected[0]['evidence'] != evidence))):
        raise ValueError('replacement producer differs from the reviewed section')
    _saved_case(experiment, case['id'], read_bytes)
    prior = _load_replacement(Path(evidence['replacement_review']).parent)
    return evidence, sources, prior


def _prepare_next(directory, experiment, case, *, source=None):
    reuse = source is not None
    evidence, sources, prior = _section_result(experiment, case, source=source)
    pool = prior['pool']
    generation._collect_encodings(pool)
    removed = evidence['input_ids']
    removed_set = set(removed)
    if len(removed_set) != len(removed) or not removed_set <= set(prior['current_ids']):
        raise ValueError('replacement membership is not a unique current subset')
    origins = sorted(o for i in removed for o in pool['items'][i]['original_ids'])
    if len(set(origins)) != len(origins):
        raise ValueError('replacement original supports overlap')
    retained = [i for i in prior['current_ids'] if i not in removed_set]
    identifier = f'R{1+max((int(i[1:]) for i in pool["items"] if i.startswith("R")), default=0):05d}'
    pool['items'] = {i: pool['items'][i] for i in retained}
    pool['items'][identifier] = dict(subject=case['parsed']['title'], meaning=case['parsed']['meaning'],
                                    original_ids=origins)
    for path in [Path(__file__), Path(review.__file__), Path(generation.__file__),
                 Path(worker.__file__), Path(review.hdbscan.__file__)]:
        sources[str(path.resolve())] = sha(path)
    pool['sources'] = {str(Path(worker.__file__).resolve()): sha(worker.__file__)}
    directory.mkdir(parents=True, exist_ok=False)
    first_new_encoding = len(pool['encodings'])
    generation._prepare_encoding(directory, pool, [identifier])
    updated = dict(prior, experiment=str(experiment), case=case['id'], receipt=case['receipt'],
        replacement_id=identifier, removed_ids=origins, removed_input_ids=removed,
        reused_definition=reuse,
        source_replacement=str(Path(evidence['replacement_review']).parent),
        replacement_review=evidence['replacement_review'], current_ids=retained+[identifier],
        first_new_encoding=first_new_encoding, sources=sources, pool=pool)
    updated['replacement_ids'] = [identifier]
    updated['root_changes'] = [dict(id=identifier, section=evidence['section'],
        removed_input_ids=removed, original_ids=origins, experiment=str(experiment),
        case=case['id'], receipt=case['receipt'], reused_definition=reuse)]
    workflow.write(directory/'replacement.json', dict(plan=updated, sha256=workflow.inputs.digest(updated)))
    return dict(removed_entries=len(removed), reused_vectors=len(retained), updated_entries=len(retained)+1,
        worker_configs=[j['config'] for j in pool['encodings'][first_new_encoding:]])


def write_roots(directory, *, name='proposed-roots'):
    """Show retained synthetic roots, including those absent from current groups."""
    directory = Path(directory).resolve()
    if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name):
        raise ValueError('root artifact name requires lowercase letters, digits, hyphens or underscores')
    analysis = saved_review(directory)
    latest = _load_replacement(directory)
    chain, seen, plan = [], set(), latest
    while True:
        chain.append(plan)
        if 'source_replacement' not in plan:
            break
        path = Path(plan['source_replacement'])/'replacement.json'
        if str(path) in seen or latest['sources'].get(str(path)) != sha(path):
            raise ValueError('root lineage is cyclic or not frozen')
        seen.add(str(path))
        envelope = workflow.read(path)
        plan = envelope['plan']
        if workflow.inputs.digest(plan) != envelope['sha256']:
            raise ValueError('root lineage preparation changed')
    active, next_slot = {}, 1
    for plan in reversed(chain):
        changes = plan.get('root_changes', [dict(id=plan.get('replacement_id', 'R00001'),
                                               removed_input_ids=plan.get('removed_input_ids', []))])
        for change in changes:
            identifier = change['id']
            if identifier in active:
                continue  # A filtering-only preparation preserves the existing root.
            absorbed = [active.pop(i) for i in change['removed_input_ids'] if i in active]
            if absorbed:
                slots = sorted({s for r in absorbed for s in r['slots']})
                version = 1+max(r['version'] for r in absorbed)
            else:
                slots, version = [next_slot], 1
                next_slot += 1
            active[identifier] = dict(slots=slots, version=version)
    records = analysis.get('replacements', [analysis['replacement']])
    roots = sorted([dict(r, **active[r['id']]) for r in records], key=lambda r: r['slots'])
    notes = sorted({n for r in roots for n in r['note_ids']})
    result = dict(schema_version=1, replacement=str(directory/'replacement.json'),
        replacement_sha256=sha(directory/'replacement.json'), roots=roots, root_count=len(roots),
        represented_notes=len(notes), note_ids=notes, eligible_notes=analysis['input_notes'],
        retained_original_entries=sum(len(r['original_ids']) for r in roots),
        input_entries=analysis['encoded_entries'])
    workflow.write(directory/(name+'.json'), result)
    md = [f'# {len(roots)} proposed roots', '',
          f'{len(notes)} distinct notes represented; {analysis["input_notes"]} eligible notes.', '',
          '| Root slot | Title | Notes | Original entries |', '|---|---|---:|---:|']
    height = 150+len(roots)*125
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}">',
        '<style>text{font-family:Arial,sans-serif}</style><rect width="100%" height="100%" fill="white"/>',
        f'<text x="28" y="36" font-size="24" font-weight="bold">{len(roots)} proposed roots</text>',
        f'<text x="28" y="64" font-size="15">{len(notes)} distinct notes represented · '
        f'{analysis["input_notes"]} eligible notes · root membership preserved across clustering</text>']
    for i, root in enumerate(roots):
        slot = '+'.join(map(str, root['slots']))
        md.append(f'| {slot} v{root["version"]} | {root["title"].replace("|", "\\|")} | '
                  f'{len(root["note_ids"])} | {len(root["original_ids"])} |')
        color, y = f'hsl({(i*137.508)%360:.1f},65%,36%)', 95+i*125
        status = (f'Current clustering: G{root["group"]:02d}, {root["section"]}'
                  if root['group'] is not None else 'Current clustering: ungrouped; retained as a root')
        svg += [f'<g><title>{escape(root["meaning"])}</title>',
            f'<rect x="28" y="{y}" width="1144" height="105" rx="8" fill="white" stroke="{color}" stroke-width="2"/>',
            f'<text x="48" y="{y+30}" font-size="20" font-weight="bold" fill="{color}">'
            f'Root {slot} v{root["version"]} · {escape(root["title"])}</text>',
            f'<text x="48" y="{y+57}" font-size="15">{len(root["note_ids"])} notes · '
            f'{len(root["original_ids"])} original entries · {root["id"]}</text>',
            f'<text x="48" y="{y+82}" font-size="14">{escape(status)}</text></g>']
    for root in roots:
        md += ['', f'## Root {"+".join(map(str, root["slots"]))} v{root["version"]}: {root["title"]}',
               '', root['meaning']]
    svg += [f'<text x="28" y="{height-18}" font-size="14">'
            'Hover over a root for its complete fixed meaning. Note counts overlap across roots.</text></svg>']
    (directory/(name+'.svg')).write_text('\n'.join(svg)+'\n')
    (directory/(name+'.md')).write_text('\n'.join(md)+'\n')
    return dict(root_count=len(roots), represented_notes=len(notes), eligible_notes=analysis['input_notes'],
                svg=str(directory/(name+'.svg')), definitions=str(directory/(name+'.md')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('directory', type=Path)
    source = prepare_parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--experiment', type=Path)
    source.add_argument('--from-replacement', type=Path,
                        help='reuse the exact completed synthetic vector from this preparation')
    prepare_parser.add_argument('--case')
    prepare_parser.add_argument('--replacement-review', type=Path,
                                help='reuse an exact native definition for one group in this review')
    prepare_parser.add_argument('--section', help='section for --replacement-review')
    prepare_parser.add_argument('--exclude-unassigned', action='store_true',
                                help='exclude original unassigned nodes; requires --from-replacement')
    collect_parser = commands.add_parser('collect')
    collect_parser.add_argument('directory', type=Path)
    collect_parser.add_argument('--name', default='reclustered-sections')
    roots_parser = commands.add_parser('roots')
    roots_parser.add_argument('directory', type=Path)
    roots_parser.add_argument('--name', default='proposed-roots')
    args = parser.parse_args()
    if args.command == 'collect':
        result = collect(args.directory, name=args.name)
    elif args.command == 'roots':
        result = write_roots(args.directory, name=args.name)
    elif args.from_replacement is not None:
        if args.case is not None or args.replacement_review is not None or args.section is not None:
            parser.error('--case, --replacement-review and --section apply only to --experiment')
        result = prepare_from(args.directory, args.from_replacement,
                              exclude_unassigned=args.exclude_unassigned)
    else:
        if args.case is None or args.exclude_unassigned:
            parser.error('--experiment requires --case and does not accept --exclude-unassigned')
        if (args.replacement_review is None) != (args.section is None):
            parser.error('--replacement-review and --section must be supplied together')
        result = prepare(args.directory, args.experiment, args.case,
                         replacement_review=args.replacement_review, section=args.section)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
