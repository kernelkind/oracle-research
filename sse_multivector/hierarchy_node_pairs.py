"""Prepare reviewed local/canonical pairs from saved notes and explicit graph states.

Graph states and meanings are deliberate review inputs, not inferred placements.
Schema 2 adds recursive canonical descendants to comparisons. Standalone local
meaning inputs can separately include the original selected-root hierarchy.
"""

from graphlib import CycleError, TopologicalSorter
import hashlib
import json
from pathlib import Path
import re

try:
    from . import extraction_pipeline as engine
except ImportError:
    import extraction_pipeline as engine


VERSION = 'hierarchy-node-pairs-v1'
RELATIONS = {'equivalent', 'local_contains_canonical', 'canonical_contains_local',
             'neither', 'uncertain'}


def _fields(value, name, fields):
    if not isinstance(value, dict):
        raise ValueError(f'{name} must be an object')
    engine._expect_fields(value, name, fields)


def _local_collection(source, *, base, read, load_report):
    """Combine source-bound cases; historical judgments never become targets."""
    if type(source['schema_version']) is not int:
        raise ValueError('unsupported local node collection schema_version')
    fields = {'schema_version', 'sources', 'review'}
    if 'experiments' in source:
        fields.add('experiments')
    _fields(source, 'local node collection', fields)
    if not isinstance(source['review'], dict) or 'expected' in source['review']:
        raise ValueError('collection review must be an object without expected targets')
    if not isinstance(source['sources'], list) or not source['sources']:
        raise ValueError('collection requires nonempty sources')
    if 'experiments' in source and not isinstance(source['experiments'], list):
        raise ValueError('collection experiments must be an array')
    cases, by_input, identities = [], {}, set()

    def reference(ref, kind):
        _fields(ref, 'collection ' + kind,
                {'path'} | ({'select'} if isinstance(ref, dict) and 'select' in ref else set()))
        path = engine._resolve_path(ref['path'], 'collection ' + kind, Path(base))
        if (kind, path) in identities:
            raise ValueError('duplicate collection ' + kind + ' path')
        identities.add((kind, path))
        if 'select' in ref:
            selected = engine._validate_string_array(ref['select'], 'collection select', allow_empty=False)
            if len(selected) != len(set(selected)):
                raise ValueError('duplicate collection selection ID')
        return path

    def select(ref, rows):
        if 'select' not in ref:
            return rows
        if set(ref['select']) - {row['id'] for row in rows}:
            raise ValueError('unknown collection selection ID')
        return [row for row in rows if row['id'] in ref['select']]

    def add(payload, evidence, witness):
        raw = engine._canonical_json_bytes(payload)
        signature = hashlib.sha256(raw).hexdigest()
        if signature not in by_input:
            case = {'id': 'bootstrap-' + signature,
                    'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                    'evidence': {**evidence, 'version': 'hierarchy-local-nodes-v2',
                                 'local_input_sha256': signature,
                                 'review': {**source['review'], 'historical_witnesses': []},
                                 'application_allowed': False}}
            by_input[signature] = case
            cases.append(case)
        elif json.loads(by_input[signature]['inputs']['INPUT_JSON']) != payload:
            raise ValueError('conflicting collection input digest')
        by_input[signature]['evidence']['review']['historical_witnesses'].append(witness)

    for ref in source['sources']:
        path = reference(ref, 'source')
        document = read(path)
        if not isinstance(document, dict) or document.get('schema_version') not in (1, 3, 4):
            raise ValueError('collection sources require schema-1, schema-3 or schema-4 local node datasets')
        rows, _ = create_source(document, base=path.parent, read=read, local_only=True)
        for row in select(ref, rows):
            add(json.loads(row['inputs']['INPUT_JSON']), row['evidence'],
                {'kind': 'source', 'source': str(path), 'case': row['id'],
                 'evidence': row['evidence']})
    for ref in source.get('experiments', []):
        path = reference(ref, 'experiment')
        if load_report is None:
            raise ValueError('collection experiments require validated experiment reports')
        result = load_report(path)
        if result['adapter'] not in {'hierarchy_local_nodes', 'hierarchy_node_pairs'}:
            raise ValueError('collection experiments require local-node or node-pair inputs')
        plan = read(path / 'experiment.json')['plan']
        for row in select(ref, result['cases']):
            local = json.loads(row['inputs']['INPUT_JSON'])['local']
            payload = {'local': {key: local[key] for key in ('entry', 'post', 'hierarchy')
                                 if key in local}}
            add(payload, row['evidence'],
                {'kind': 'experiment', 'experiment': str(path), 'case': row['id'],
                 'adapter': result['adapter'], 'prompt': plan['prompt'],
                 'settings': result['settings'], 'status': row['status'],
                 'inputs': row['inputs'], 'input_sha256': row['input_sha256'],
                 'parsed': row.get('parsed'), 'receipt': row.get('receipt'),
                 'output': row.get('output'), 'error': row.get('error'),
                 'failure_kind': row.get('failure_kind'),
                 'reviews': row.get('reviews', []),
                 'expectations': row.get('expectations', []), 'evidence': row['evidence']})
    return cases, {'version': 'hierarchy-local-nodes-v2', 'cases': len(cases),
                   'historical_witnesses': sum(len(case['evidence']['review']['historical_witnesses'])
                                               for case in cases),
                   'application_allowed': False}


def create_source(source, *, base, read, local_only=False, load_report=None):
    """Resolve entry selectors through the native preparation's hashed reader."""
    if local_only and isinstance(source, dict) and source.get('schema_version') == 2:
        return _local_collection(source, base=base, read=read, load_report=load_report)
    fields = {'schema_version', 'corpus', 'nodes'} if local_only else {
        'schema_version', 'corpus', 'canonical_states', 'pairs'}
    if local_only and isinstance(source, dict) and source.get('schema_version') == 1 and 'include_hierarchy' in source:
        fields.add('include_hierarchy')
    _fields(source, 'local node source' if local_only else 'node pair source', fields)
    include_hierarchy = source.get('include_hierarchy', local_only and source['schema_version'] in (3, 4))
    if type(include_hierarchy) is not bool:
        raise ValueError('include_hierarchy must be boolean')
    allowed = (1, 3, 4) if local_only else (1, 2)
    if type(source['schema_version']) is not int or source['schema_version'] not in allowed:
        raise ValueError('unsupported node pairs schema_version')
    version = VERSION if source['schema_version'] == 1 else 'hierarchy-node-pairs-v2'
    path = engine._resolve_path(source['corpus'], 'node pair corpus', Path(base))
    corpus = read(path)
    if corpus.get('schema_version') != 1 or not isinstance(corpus.get('notes'), list):
        raise ValueError('node pair corpus requires schema_version 1 and notes')
    notes = {}
    for note in corpus['notes']:
        identifier = engine._expect_string(note['note_id'], 'note_id')
        if identifier in notes:
            raise ValueError('duplicate source note_id')
        notes[identifier] = note
    indexed, entries, hierarchies = {}, {}, {}

    def entry(reference):
        _fields(reference, 'entry reference', {'note_id', 'number'})
        note_id = engine._expect_string(reference['note_id'], 'entry note_id')
        number = engine._expect_string(reference['number'], 'entry number')
        if note_id not in notes:
            raise ValueError('unknown source note_id')
        if note_id not in indexed:
            rows = notes[note_id].get('subjects')
            if not isinstance(rows, list) or not rows:
                raise ValueError('source note requires subjects')
            numbered = {}
            for row in rows:
                n = row['number']
                if not isinstance(n, str) or not re.fullmatch(r'[1-9]\d*(?:\.[1-9]\d*)*', n):
                    raise ValueError('invalid local hierarchy number')
                if n in numbered:
                    raise ValueError('duplicate local hierarchy number')
                numbered[n] = {k: engine._expect_string(row[k], k)
                               for k in ('subject', 'context')}
            indexed[note_id] = numbered
        numbered = indexed[note_id]
        if number not in numbered:
            raise ValueError('unknown local entry number')
        key = (note_id, number)
        if key not in entries:
            parts = number.split('.')
            ancestors = ['.'.join(parts[:depth]) for depth in range(1, len(parts))]
            if any(n not in numbered for n in ancestors):
                raise ValueError('missing original local ancestor')
            entries[key] = {**numbered[number], 'ancestors': [numbered[n] for n in ancestors]}
        return entries[key]

    def hierarchy(reference, local):
        note_id, number = reference['note_id'], reference['number']
        root = number.split('.')[0]
        key = (note_id, root)
        if key not in hierarchies:
            numbered = indexed[note_id]
            numbers = sorted((n for n in numbered if n.split('.')[0] == root),
                             key=lambda n: tuple(int(part) for part in n.split('.')))
            if any('.' in n and n.rsplit('.', 1)[0] not in numbered for n in numbers):
                raise ValueError('missing original local hierarchy parent')
            hierarchies[key] = [{'number': n, **numbered[n]} for n in numbers]
        return {'selected': number, 'entries': [
            {'number': number, **{k: local[k] for k in ('subject', 'context')}}
            if row['number'] == number else row for row in hierarchies[key]]}

    if local_only:
        local_version = ('hierarchy-local-nodes-v' + str(source['schema_version'])
                         if source['schema_version'] in (3, 4) else 'hierarchy-local-nodes-v1')
        if not isinstance(source['nodes'], list) or not source['nodes']:
            raise ValueError('local nodes require nonempty nodes')
        cases, seen = [], set()
        for node in source['nodes']:
            fields = {'id', 'local', 'review'}
            if isinstance(node, dict) and 'subject_override' in node:
                fields.add('subject_override')
            _fields(node, 'local node', fields)
            identifier = engine._expect_identifier(node['id'], 'local node ID')
            if identifier in seen:
                raise ValueError('duplicate local node ID')
            seen.add(identifier)
            local = entry(node['local'])
            override = {}
            if 'subject_override' in node:
                replacement = engine._expect_string(node['subject_override'], 'subject_override')
                if not replacement.strip():
                    raise ValueError('subject_override must be nonempty text')
                override = {'subject_override': {'original': local['subject'],
                                                 'replacement': replacement}}
                local = {**local, 'subject': replacement}
            post = engine._expect_string(notes[node['local']['note_id']]['text'], 'local post')
            if not isinstance(node['review'], dict):
                raise ValueError('local node review must be an object')
            payload = {'local': {'entry': local, 'post': post}}
            if source['schema_version'] == 3:
                payload['local']['entry'] = {k: local[k] for k in ('subject', 'context')}
            if include_hierarchy:
                payload['local']['hierarchy'] = hierarchy(node['local'], local)
            if source['schema_version'] == 4:
                del payload['local']['entry']
            cases.append({'id': identifier,
                          'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                          'evidence': {'version': local_version,
                                       'local': node['local'], 'corpus': str(path), **override,
                                       'review': node['review'], 'application_allowed': False}})
        return cases, {'version': local_version, 'cases': len(cases),
                       'application_allowed': False}

    states = source['canonical_states']
    if not isinstance(states, dict) or not states:
        raise ValueError('canonical_states must be a nonempty object')
    graphs, trials, state_provenance = {}, {}, {}
    for state, rows in states.items():
        engine._expect_identifier(state, 'canonical state')
        if isinstance(rows, dict) and source['schema_version'] == 2:
            reference = rows
            _fields(reference, 'canonical trial reference', {'trial'} | (
                {'before_step'} if 'before_step' in reference else set()))
            trial_path = engine._resolve_path(rows['trial'], 'canonical trial', Path(base))
            if trial_path not in trials:
                try:
                    from . import canonical_trial
                except ImportError:
                    import canonical_trial
                saved = read(trial_path)
                canonical_trial._check(saved)
                if Path(saved['corpus']).resolve() != path:
                    raise ValueError('canonical trial corpus does not match node pair corpus')
                trials[trial_path] = saved
            state_provenance[state] = {'canonical_trial': str(trial_path)}
            if 'before_step' in reference:
                index = reference['before_step']
                steps = trials[trial_path].get('steps', [])
                if (type(index) is not int or not isinstance(steps, list)
                        or not 0 <= index < len(steps) or not isinstance(steps[index], dict)
                        or steps[index].get('index') != index):
                    raise ValueError('before_step requires a processed canonical trial step')
                rows = steps[index]['before']
                state_provenance[state]['before_step'] = index
            else:
                rows = trials[trial_path]['nodes']
        if not isinstance(rows, list) or not rows:
            raise ValueError('canonical state requires nodes')
        nodes = {}
        for node in rows:
            _fields(node, 'canonical node', {'id', 'subject', 'meaning', 'entries', 'parents'})
            identifier = engine._expect_identifier(node['id'], 'canonical node ID')
            if identifier in nodes:
                raise ValueError('duplicate canonical node ID')
            for field in ('subject', 'meaning'):
                engine._expect_string(node[field], 'canonical ' + field)
            if not isinstance(node['entries'], list) or not node['entries']:
                raise ValueError('canonical node requires supporting entries')
            refs = [json.dumps(ref, sort_keys=True) for ref in node['entries']]
            if len(set(refs)) != len(refs):
                raise ValueError('duplicate canonical supporting entry')
            support = [entry(ref) for ref in node['entries']]
            parents = engine._validate_string_array(node['parents'], 'canonical parents', allow_empty=True)
            if len(set(parents)) != len(parents):
                raise ValueError('duplicate canonical parent')
            nodes[identifier] = {**node, 'entries': support, 'parents': sorted(parents)}
        if any(parent not in nodes for node in nodes.values() for parent in node['parents']):
            raise ValueError('unknown canonical parent')
        try:
            tuple(TopologicalSorter({n: node['parents'] for n, node in nodes.items()}).static_order())
        except CycleError as exc:
            raise ValueError('canonical state contains a cycle') from exc
        graphs[state] = nodes

    if not isinstance(source['pairs'], list) or not source['pairs']:
        raise ValueError('node pairs require nonempty pairs')
    cases, seen, saved_cases = [], set(), {}
    for pair in source['pairs']:
        fields = {'id', 'local', 'canonical', 'review'}
        if isinstance(pair, dict):
            fields.update(key for key in ('local_meaning', 'local_meaning_from') if key in pair)
            if 'local_meaning' in pair and 'local_meaning_from' in pair:
                raise ValueError('local_meaning and local_meaning_from are mutually exclusive')
        _fields(pair, 'node pair', fields)
        identifier = engine._expect_identifier(pair['id'], 'node pair ID')
        if identifier in seen:
            raise ValueError('duplicate node pair ID')
        seen.add(identifier)
        local = entry(pair['local'])
        post = engine._expect_string(notes[pair['local']['note_id']]['text'], 'local post')
        _fields(pair['canonical'], 'canonical reference', {'state', 'id'})
        reference = pair['canonical']
        if reference['state'] not in graphs or reference['id'] not in graphs[reference['state']]:
            raise ValueError('unknown canonical state or node')
        nodes = graphs[reference['state']]
        canonical = nodes[reference['id']]
        ancestors, pending = set(), list(canonical['parents'])
        while pending:
            parent = pending.pop()
            if parent not in ancestors:
                ancestors.add(parent)
                pending.extend(nodes[parent]['parents'])
        payload = {
            'local': {'entry': local, 'post': post},
            'canonical': {**canonical, 'ancestors': [
                {k: nodes[n][k] for k in ('id', 'subject', 'meaning', 'parents')}
                for n in sorted(ancestors)]}}
        if source['schema_version'] == 2:
            children = {n: [] for n in nodes}
            for n, row in nodes.items():
                for parent in row['parents']:
                    children[parent].append(n)
            descendants, pending = set(), list(children[canonical['id']])
            while pending:
                child = pending.pop()
                if child not in descendants:
                    descendants.add(child)
                    pending.extend(children[child])
            payload['canonical']['descendants'] = [
                {k: nodes[n][k] for k in ('id', 'subject', 'meaning', 'parents')}
                for n in sorted(descendants)]
        if 'local_meaning' in pair:
            meaning = engine._expect_string(pair['local_meaning'], 'local_meaning')
            if not meaning.strip():
                raise ValueError('local_meaning must be nonempty text')
            payload['local']['meaning'] = meaning
        provenance = {}
        if 'local_meaning_from' in pair:
            reference_meaning = pair['local_meaning_from']
            _fields(reference_meaning, 'local_meaning_from', {'experiment', 'case'})
            directory = engine._resolve_path(reference_meaning['experiment'],
                                             'meaning experiment', Path(base))
            case_id = engine._expect_identifier(reference_meaning['case'], 'meaning case')
            if load_report is None:
                raise ValueError('local_meaning_from requires validated experiment reports')
            if directory not in saved_cases:
                report = load_report(directory)
                if report['adapter'] != 'hierarchy_local_nodes':
                    raise ValueError('local_meaning_from requires hierarchy_local_nodes experiment')
                saved_cases[directory] = {case['id']: case for case in report['cases']}
            saved = saved_cases[directory].get(case_id)
            if saved is None or saved['status'] != 'valid' or not saved.get('receipt'):
                raise ValueError('local_meaning_from requires a valid saved meaning case')
            saved_input = json.loads(saved['inputs']['INPUT_JSON'])
            expected_input = {'local': payload['local']}
            if (isinstance(saved_input, dict) and
                    isinstance(saved_input.get('local'), dict) and
                    set(saved_input['local']) == {'post', 'hierarchy'}):
                expected_input = {'local': {
                    'post': post, 'hierarchy': hierarchy(pair['local'], local)}}
            if (saved['evidence']['local'] != pair['local'] or
                    saved_input != expected_input):
                raise ValueError('saved local meaning evidence does not match original local input')
            meaning = saved['parsed']['meaning']
            if not isinstance(meaning, str) or not meaning.strip():
                raise ValueError('saved local meaning must be nonempty text')
            payload['local']['meaning'] = meaning
            provenance['local_meaning_from'] = {
                'experiment': str(directory), 'case': case_id, 'receipt': saved['receipt']}
        if not isinstance(pair['review'], dict):
            raise ValueError('node pair review must be an object')
        cases.append({'id': identifier,
                      'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                      'evidence': {'version': version, 'local': pair['local'],
                                   'canonical': reference, 'corpus': str(path),
                                   **state_provenance.get(reference['state'], {}),
                                   'review': pair['review'], **provenance, 'application_allowed': False}})
    return cases, {'version': version, 'cases': len(cases), 'application_allowed': False}


def project_fixed_meanings(case):
    """Project a pinned native pair while retaining source evidence for audit."""
    original = json.loads(case['inputs']['INPUT_JSON'])
    local, canonical = original['local'], original['canonical']

    def text(value, name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(name + ' must be nonempty text')
        return value

    def node(value, name):
        keys = ('id', 'subject', 'meaning', 'parents')
        if not isinstance(value, dict) or not set(keys) <= value.keys():
            raise ValueError(name + ' requires id, subject, meaning and parents')
        result = {key: text(value[key], name + ' ' + key) for key in keys[:-1]}
        engine._validate_string_array(value['parents'], name + ' parents', allow_empty=True)
        result['parents'] = list(value['parents'])
        return result

    selected = node(canonical, 'canonical node')
    for key in ('ancestors', 'descendants'):
        if key not in canonical or not isinstance(canonical[key], list):
            raise ValueError('fixed_meanings requires canonical ' + key)
        selected[key] = [node(value, 'canonical ' + key) for value in canonical[key]]
    payload = {'local': {
        'subject': text(local['entry']['subject'], 'local subject'),
        'meaning': text(local.get('meaning'), 'fixed local meaning')},
        'canonical': selected}
    evidence = case.get('evidence', {})
    if 'input_view' in evidence or 'unprojected_input' in evidence:
        raise ValueError('fixed_meanings requires original unprojected node pairs')
    return {**case, 'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
            'evidence': {**evidence, 'input_view': 'fixed_meanings',
                         'unprojected_input': original}}


def validate(raw, *, diagnostics=False, meaning=None):
    """Validate the approved output mechanics without judging its semantics."""
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    fields = {'meaning', 'relation', 'reason'} | ({'questions', 'answers'} if diagnostics else set())
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('expected meaning, questions, answers, relation, and reason' if diagnostics
                         else 'expected meaning, relation, and reason')
    if not isinstance(value['relation'], str) or value['relation'] not in RELATIONS:
        raise ValueError('unknown hierarchy comparison relation')
    if value['meaning'] is None:
        if value['relation'] != 'uncertain':
            raise ValueError('null local meaning requires uncertain')
    elif not isinstance(value['meaning'], str) or not value['meaning'].strip():
        raise ValueError('meaning must be nonempty text or null')
    if not isinstance(value['reason'], str) or not value['reason'].strip():
        raise ValueError('reason must be nonempty text')
    if diagnostics:
        if not isinstance(meaning, str) or value['meaning'] != meaning:
            raise ValueError('Compare answer must copy the fixed local meaning exactly')
        directions = {'local_contains_canonical', 'canonical_contains_local'}
        for key, identifier, fields in (
                ('questions', 'id', {'id', 'question'}),
                ('answers', 'question_id', {'question_id', 'answer', 'justification'})):
            rows = value[key]
            if not isinstance(rows, list) or len(rows) != 2:
                raise ValueError(key + ' requires exactly two records')
            seen = set()
            for row in rows:
                if not isinstance(row, dict) or set(row) != fields:
                    raise ValueError(key + ' record has invalid fields')
                direction = row[identifier]
                if not isinstance(direction, str) or direction not in directions or direction in seen:
                    raise ValueError(key + ' requires each containment direction exactly once')
                seen.add(direction)
                for field in fields - {identifier}:
                    text = row[field]
                    if field == 'answer' and text is None:
                        if value['relation'] != 'uncertain':
                            raise ValueError('null coverage answer requires uncertain')
                    elif not isinstance(text, str) or not text.strip():
                        raise ValueError(field + ' must be nonempty text')
    return value


def validate_meaning(raw, *, post=None, diagnostic=False, ambiguity_diagnostics=False):
    """Validate a standalone local meaning without judging its semantics."""
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    diagnostic = diagnostic or ambiguity_diagnostics
    fields = {'meaning', 'evidence'} if diagnostic else {'meaning'}
    if ambiguity_diagnostics:
        fields.update({'ambiguities', 'resolutions'})
    if not isinstance(value, dict) or set(value) != fields:
        if ambiguity_diagnostics:
            raise ValueError('expected ambiguities, resolutions, meaning and evidence')
        raise ValueError('expected meaning and evidence' if diagnostic else 'expected only meaning')
    if value['meaning'] is not None and (
            not isinstance(value['meaning'], str) or not value['meaning'].strip()):
        raise ValueError('meaning must be nonempty text or null')
    if ambiguity_diagnostics:
        if not isinstance(value['ambiguities'], list) or not isinstance(value['resolutions'], list):
            raise ValueError('ambiguities and resolutions must be arrays')
        questions = set()
        for record in value['ambiguities']:
            if not isinstance(record, dict) or set(record) != {'id', 'question'}:
                raise ValueError('expected id and question in each ambiguity')
            for name in ('id', 'question'):
                if not isinstance(record[name], str) or not record[name].strip():
                    raise ValueError('ambiguity ' + name + ' must be nonempty text')
            if record['id'] in questions:
                raise ValueError('duplicate ambiguity ID')
            questions.add(record['id'])
        resolved = set()
        for record in value['resolutions']:
            if not isinstance(record, dict) or set(record) != {'ambiguity_id', 'answer', 'justification'}:
                raise ValueError('expected ambiguity_id, answer and justification in each resolution')
            for name in ('ambiguity_id', 'justification'):
                if not isinstance(record[name], str) or not record[name].strip():
                    raise ValueError('resolution ' + name + ' must be nonempty text')
            identifier = record['ambiguity_id']
            if identifier not in questions or identifier in resolved:
                raise ValueError('each resolution must match a distinct ambiguity ID')
            resolved.add(identifier)
            answer = record['answer']
            if answer is not None and (not isinstance(answer, str) or not answer.strip()):
                raise ValueError('resolution answer must be nonempty text or null')
            if answer is None and value['meaning'] is not None:
                raise ValueError('an unresolved ambiguity requires a null meaning')
        if resolved != questions:
            raise ValueError('each ambiguity requires exactly one resolution')
    if 'evidence' in value:
        if not isinstance(post, str):
            raise ValueError('diagnostic evidence requires the original local post')
        records = value['evidence']
        if not isinstance(records, list):
            raise ValueError('diagnostic evidence must be an array')
        if value['meaning'] is not None and not records:
            raise ValueError('a non-null meaning requires diagnostic evidence')
        for record in records:
            if not isinstance(record, dict) or set(record) != {'quote', 'supports', 'inference'}:
                raise ValueError('expected quote, supports and inference in each diagnostic record')
            for name in ('quote', 'supports'):
                if not isinstance(record[name], str) or not record[name].strip():
                    raise ValueError('diagnostic ' + name + ' must be nonempty text')
            if record['quote'] not in post:
                raise ValueError('diagnostic quote must be an exact contiguous excerpt of the local post')
            inference = record['inference']
            if inference is not None and (not isinstance(inference, str) or not inference.strip()):
                raise ValueError('diagnostic inference must be nonempty text or null')
    return value
