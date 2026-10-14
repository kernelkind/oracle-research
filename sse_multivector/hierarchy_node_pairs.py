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
    if 'local_schema_version' in source:
        fields.add('local_schema_version')
    if 'input_view' in source:
        fields.add('input_view')
    _fields(source, 'local node collection', fields)
    local_schema_version = source.get('local_schema_version')
    if 'local_schema_version' in source and (type(local_schema_version) is not int
                                             or local_schema_version != 4):
        raise ValueError('collection local_schema_version must be 4')
    input_view = source.get('input_view')
    if 'input_view' in source:
        if input_view != 'subjects_only':
            raise ValueError('collection input_view must be subjects_only')
        if local_schema_version != 4:
            raise ValueError('subjects_only requires collection local_schema_version 4')
    if not isinstance(source['review'], dict) or 'expected' in source['review']:
        raise ValueError('collection review must be an object without expected targets')
    if not isinstance(source['sources'], list) or not source['sources']:
        raise ValueError('collection requires nonempty sources')
    if 'experiments' in source and not isinstance(source['experiments'], list):
        raise ValueError('collection experiments must be an array')
    cases, by_input, identities = [], {}, set()
    regenerated_by_entry = {}

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
        if local_schema_version == 4:
            witness = {**witness, 'inputs': witness.get('inputs', {
                'INPUT_JSON': json.dumps(payload, ensure_ascii=False)})}
            node = {'id': 'selected', 'local': evidence['local'], 'review': {}}
            for name in ('subject_override', 'post_override'):
                if name in evidence:
                    node[name] = evidence[name]['replacement']
            if 'context_overrides' in evidence:
                node['context_overrides'] = {
                    number: change['replacement']
                    for number, change in evidence['context_overrides'].items()}
            definition = {'schema_version': 4, 'corpus': evidence['corpus'], 'nodes': [node]}
            key = engine._canonical_json_bytes(definition)
            if key not in regenerated_by_entry:
                regenerated, _ = create_source(definition, base=base, read=read, local_only=True)
                regenerated_by_entry[key] = (
                    json.loads(regenerated[0]['inputs']['INPUT_JSON']),
                    {name: regenerated[0]['evidence'][name]
                     for name in ('subject_override', 'context_overrides', 'post_override')
                     if name in regenerated[0]['evidence']})
            current, regenerated_overrides = regenerated_by_entry[key]
            original, local = payload['local'], current['local']
            hierarchy = local['hierarchy']
            numbered = {entry['number']: entry for entry in hierarchy['entries']}
            number = hierarchy['selected']
            selected = {key: numbered[number][key] for key in ('subject', 'context')}
            parts = number.split('.')
            ancestors = [{key: numbered['.'.join(parts[:depth])][key]
                          for key in ('subject', 'context')}
                         for depth in range(1, len(parts))]
            expected_entry = {**selected, 'ancestors': ancestors}
            if (original['post'] != local['post']
                    or ('entry' in original and (
                        not isinstance(original['entry'], dict)
                        or set(original['entry']) not in (
                            {'subject', 'context'}, {'subject', 'context', 'ancestors'})
                        or original['entry'] != {
                            key: expected_entry[key] for key in original['entry']}))
                    or ('hierarchy' in original and original['hierarchy'] != hierarchy)
                    or {name: evidence[name]
                        for name in ('subject_override', 'context_overrides', 'post_override')
                        if name in evidence} != regenerated_overrides):
                raise ValueError('collection schema-4 regeneration does not match original local input')
            payload = current
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
    preparation = {'version': 'hierarchy-local-nodes-v2', 'cases': len(cases),
                   'historical_witnesses': sum(len(case['evidence']['review']['historical_witnesses'])
                                               for case in cases),
                   'application_allowed': False}
    if input_view == 'subjects_only':
        # Validate and deduplicate original inputs first. Their identities remain
        # stable across views; the projected payload gets its own request digest.
        preparation['input_view'] = input_view
        for case in cases:
            original = json.loads(case['inputs']['INPUT_JSON'])
            local = original['local']
            projected = {'local': {'post': local['post'], 'hierarchy': {
                'selected': local['hierarchy']['selected'],
                'entries': [{key: entry[key] for key in ('number', 'subject')}
                            for entry in local['hierarchy']['entries']]}}}
            case['inputs']['INPUT_JSON'] = json.dumps(projected, ensure_ascii=False)
            case['evidence'].update(
                input_view=input_view, original_input=original,
                original_input_sha256=case['evidence']['local_input_sha256'],
                local_input_sha256=hashlib.sha256(engine._canonical_json_bytes(projected)).hexdigest())
    return cases, preparation


def create_meaning_diagnostic_source(source, *, base, read, load_report):
    """Copy a receipt-bound meaning, optionally with its exact original evidence."""
    _fields(source, 'meaning diagnostic source', {'schema_version', 'corpus', 'nodes'})
    if type(source['schema_version']) is not int or source['schema_version'] != 1:
        raise ValueError('unsupported meaning diagnostic schema_version')
    if not isinstance(source['nodes'], list) or not source['nodes']:
        raise ValueError('meaning diagnostics require nonempty nodes')
    corpus = engine._resolve_path(source['corpus'], 'meaning diagnostic corpus', Path(base))
    cases, seen, saved_cases = [], set(), {}
    version = 'hierarchy-meaning-diagnostics-v1'
    for node in source['nodes']:
        _fields(node, 'meaning diagnostic node', {'id', 'producer', 'include_source', 'review'})
        identifier = engine._expect_identifier(node['id'], 'meaning diagnostic ID')
        if identifier in seen:
            raise ValueError('duplicate meaning diagnostic ID')
        seen.add(identifier)
        if type(node['include_source']) is not bool:
            raise ValueError('meaning diagnostic include_source must be boolean')
        if not isinstance(node['review'], dict):
            raise ValueError('meaning diagnostic review must be an object')
        producer = node['producer']
        _fields(producer, 'meaning diagnostic producer', {'experiment', 'case', 'record_sha256'})
        expected = producer['record_sha256']
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError('meaning diagnostic record_sha256 must be a SHA-256 digest')
        directory = engine._resolve_path(producer['experiment'], 'meaning experiment', Path(base))
        case_id = engine._expect_identifier(producer['case'], 'meaning case')
        if load_report is None:
            raise ValueError('meaning diagnostics require validated experiment reports')
        if directory not in saved_cases:
            report = load_report(directory)
            if report['adapter'] != 'hierarchy_local_nodes':
                raise ValueError('meaning diagnostics require a hierarchy_local_nodes experiment')
            saved_cases[directory] = {case['id']: case for case in report['cases']}
        saved = saved_cases[directory].get(case_id)
        if saved is None or saved['status'] != 'valid' or not saved.get('receipt'):
            raise ValueError('meaning diagnostics require a valid saved meaning case')
        if saved['receipt']['record_sha256'] != expected:
            raise ValueError('meaning diagnostic producer receipt does not match record_sha256')
        meaning = saved['parsed']['meaning']
        if not isinstance(meaning, str) or not meaning.strip():
            raise ValueError('meaning diagnostic saved meaning must be nonempty text')
        regenerated, _ = create_source(
            {'schema_version': 4, 'corpus': str(corpus), 'nodes': [
                {'id': identifier, 'local': saved['evidence']['local'], 'review': {}}]},
            base=base, read=read, local_only=True)
        original = json.loads(saved['inputs']['INPUT_JSON'])
        if original != json.loads(regenerated[0]['inputs']['INPUT_JSON']):
            raise ValueError('meaning diagnostic producer does not match original schema-4 local input')
        payload = {'meaning': meaning}
        if node['include_source']:
            payload['local'] = original['local']
        cases.append({'id': identifier,
                      'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                      'evidence': {'version': version, 'corpus': str(corpus),
                                   'local': saved['evidence']['local'],
                                   'include_source': node['include_source'],
                                   'producer': {'experiment': str(directory), 'case': case_id,
                                                'receipt': saved['receipt']},
                                   'review': node['review'], 'application_allowed': False}})
    return cases, {'version': version, 'cases': len(cases), 'application_allowed': False}


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
            if isinstance(node, dict) and source['schema_version'] == 4:
                fields.update(name for name in ('context_overrides', 'post_override') if name in node)
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
            if 'post_override' in node:
                replacement = engine._expect_string(node['post_override'], 'post_override')
                if not replacement.strip():
                    raise ValueError('post_override must be nonempty text')
                override['post_override'] = {'original': post, 'replacement': replacement}
                post = replacement
            if not isinstance(node['review'], dict):
                raise ValueError('local node review must be an object')
            payload = {'local': {'entry': local, 'post': post}}
            if source['schema_version'] == 3:
                payload['local']['entry'] = {k: local[k] for k in ('subject', 'context')}
            if include_hierarchy:
                number = node['local']['number']
                root = number.split('.')[0]
                numbered = indexed[node['local']['note_id']]
                numbers = sorted((n for n in numbered if n.split('.')[0] == root),
                                 key=lambda n: tuple(int(part) for part in n.split('.')))
                if any('.' in n and n.rsplit('.', 1)[0] not in numbered for n in numbers):
                    raise ValueError('missing original local hierarchy parent')
                contexts = node.get('context_overrides', {})
                if not isinstance(contexts, dict):
                    raise ValueError('context_overrides must be an object')
                changes = {}
                for n, replacement in contexts.items():
                    if not isinstance(n, str) or n not in numbered or n.split('.')[0] != root:
                        raise ValueError('context_overrides requires original entry numbers in the selected root tree')
                    replacement = engine._expect_string(replacement, 'context_overrides replacement')
                    if not replacement.strip():
                        raise ValueError('context_overrides replacement must be nonempty text')
                    changes[n] = {'original': numbered[n]['context'], 'replacement': replacement}
                if changes:
                    override['context_overrides'] = changes
                payload['local']['hierarchy'] = {'selected': number, 'entries': [
                    {'number': n, **({k: local[k] for k in ('subject', 'context')}
                                    if n == number else numbered[n]),
                     **({'context': contexts[n]} if n in contexts else {})}
                    for n in numbers]}
            if source['schema_version'] == 4:
                del payload['local']['entry']
            cases.append({'id': identifier,
                          'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                          'evidence': {'version': local_version,
                                       'local': node['local'], 'corpus': str(path), **override,
                                       'review': node['review'], 'application_allowed': False}})
        return cases, {'version': local_version, 'cases': len(cases),
                       'application_allowed': False}

    saved_cases = {}

    def saved_meaning(reference, original, label):
        _fields(reference, label, {'experiment', 'case'})
        description = 'local meaning' if label == 'local_meaning_from' else 'canonical meaning'
        directory = engine._resolve_path(reference['experiment'],
                                         'meaning experiment', Path(base))
        case_id = engine._expect_identifier(reference['case'], 'meaning case')
        if load_report is None:
            raise ValueError(label + ' requires validated experiment reports')
        if directory not in saved_cases:
            report = load_report(directory)
            if report['adapter'] != 'hierarchy_local_nodes':
                raise ValueError(label + ' requires hierarchy_local_nodes experiment')
            saved_cases[directory] = {case['id']: case for case in report['cases']}
        saved = saved_cases[directory].get(case_id)
        if saved is None or saved['status'] != 'valid' or not saved.get('receipt'):
            raise ValueError(label + ' requires a valid saved meaning case')
        local = entry(original)
        post = engine._expect_string(notes[original['note_id']]['text'], 'local post')
        saved_input = json.loads(saved['inputs']['INPUT_JSON'])
        expected_input = {'local': {'entry': local, 'post': post}}
        if (isinstance(saved_input, dict)
                and isinstance(saved_input.get('local'), dict)
                and set(saved_input['local']) == {'post', 'hierarchy'}):
            expected_input = {'local': {'post': post, 'hierarchy': hierarchy(original, local)}}
        if saved['evidence']['local'] != original or saved_input != expected_input:
            raise ValueError('saved ' + description + ' evidence does not match original local input')
        meaning = saved['parsed']['meaning']
        if not isinstance(meaning, str) or not meaning.strip():
            raise ValueError('saved ' + description + ' must be nonempty text')
        return meaning, {'experiment': str(directory), 'case': case_id, 'receipt': saved['receipt']}

    states = source['canonical_states']
    if not isinstance(states, dict) or not states:
        raise ValueError('canonical_states must be a nonempty object')
    graphs, trials, state_provenance, canonical_producers = {}, {}, {}, {}
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
            if trials[trial_path].get('generation_policy'):
                # Construction provenance stays in the bound state, outside model input.
                rows=[{key:node[key] for key in ('id','subject','meaning','entries','parents')}
                      for node in rows]
        if not isinstance(rows, list) or not rows:
            raise ValueError('canonical state requires nodes')
        nodes, producers = {}, {}
        for node in rows:
            fields = {'id', 'subject', 'entries', 'parents'}
            fields.add('meaning_from' if isinstance(node, dict) and 'meaning_from' in node else 'meaning')
            _fields(node, 'canonical node', fields)
            identifier = engine._expect_identifier(node['id'], 'canonical node ID')
            if identifier in nodes:
                raise ValueError('duplicate canonical node ID')
            engine._expect_string(node['subject'], 'canonical subject')
            if not isinstance(node['entries'], list) or not node['entries']:
                raise ValueError('canonical node requires supporting entries')
            refs = [json.dumps(ref, sort_keys=True) for ref in node['entries']]
            if len(set(refs)) != len(refs):
                raise ValueError('duplicate canonical supporting entry')
            support = [entry(ref) for ref in node['entries']]
            if 'meaning_from' in node:
                if len(node['entries']) != 1:
                    raise ValueError('canonical meaning_from requires one original supporting entry')
                meaning, producers[identifier] = saved_meaning(
                    node['meaning_from'], node['entries'][0], 'canonical meaning_from')
                if node['subject'] != support[0]['subject']:
                    raise ValueError('canonical meaning_from subject does not match original entry')
                node = {key: value for key, value in node.items() if key != 'meaning_from'}
                node['meaning'] = meaning
            else:
                engine._expect_string(node['meaning'], 'canonical meaning')
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
        canonical_producers[state] = producers

    if not isinstance(source['pairs'], list) or not source['pairs']:
        raise ValueError('node pairs require nonempty pairs')
    cases, seen = [], set()
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
        if canonical_producers[reference['state']]:
            provenance['canonical_meaning_from'] = canonical_producers[reference['state']]
        if 'local_meaning_from' in pair:
            meaning, producer = saved_meaning(
                pair['local_meaning_from'], pair['local'], 'local_meaning_from')
            payload['local']['meaning'] = meaning
            provenance['local_meaning_from'] = producer
        if not isinstance(pair['review'], dict):
            raise ValueError('node pair review must be an object')
        cases.append({'id': identifier,
                      'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                      'evidence': {'version': version, 'local': pair['local'],
                                   'canonical': reference, 'corpus': str(path),
                                   **state_provenance.get(reference['state'], {}),
                                   'review': pair['review'], **provenance, 'application_allowed': False}})
    return cases, {'version': version, 'cases': len(cases), 'application_allowed': False}


def create_saved_comparisons(source, *, base, read, load_report):
    """Retain exact receipt-bound A/B inputs; old answers remain audit evidence."""
    _fields(source, 'saved comparisons', {'schema_version', 'saved_comparisons'})
    selections = source['saved_comparisons']
    if (type(source['schema_version']) is not int or source['schema_version'] != 1
            or not isinstance(selections, list) or not 1 <= len(selections) <= 128):
        raise ValueError('expected schema 1 and 1 through 128 saved comparisons')
    if load_report is None:
        raise ValueError('saved comparisons require validated experiment reports')
    cases, identifiers = [], set()
    for selection in selections:
        fields = {'id', 'experiment', 'case_id', 'reverse'}
        if isinstance(selection, dict):
            fields.update(key for key in ('review', 'record_sha256') if key in selection)
        _fields(selection, 'saved comparison selection', fields)
        identifier = engine._expect_identifier(selection['id'], 'comparison id')
        if identifier in identifiers:
            raise ValueError('duplicate saved comparison id')
        identifiers.add(identifier)
        if type(selection['reverse']) is not bool:
            raise ValueError('saved comparison reverse must be boolean')
        review = selection.get('review', {})
        if not isinstance(review, dict):
            raise ValueError('saved comparison review must be an object')
        reference = selection['experiment']
        _fields(reference, 'saved comparison reference', {'path', 'sha256'})
        directory = engine._resolve_path(reference['path'], 'saved comparison', Path(base))
        expected = engine._expect_sha256(reference['sha256'], 'saved comparison sha256')
        envelope_path = directory / 'experiment.json'
        if engine._sha256_file(envelope_path) != expected:
            raise ValueError('saved comparison reference hash differs')
        read(envelope_path)
        report = load_report(directory)
        if report['adapter'] not in {'generic', 'hierarchy_node_pairs'}:
            raise ValueError('saved comparison requires a generic or hierarchy_node_pairs experiment')
        case_id = engine._expect_identifier(selection['case_id'], 'saved comparison case_id')
        matching = [case for case in report['cases'] if case['id'] == case_id]
        if (len(matching) != 1 or matching[0]['status'] != 'valid'
                or not matching[0].get('receipt')):
            raise ValueError('saved comparison requires a valid receipt-bound case')
        saved = matching[0]
        if 'record_sha256' in selection:
            expected_receipt = engine._expect_sha256(
                selection['record_sha256'], 'saved comparison record_sha256')
            if saved['receipt']['record_sha256'] != expected_receipt:
                raise ValueError('saved comparison receipt hash differs')
        _fields(saved['inputs'], 'saved comparison inputs', {'INPUT_JSON'})
        original = json.loads(saved['inputs']['INPUT_JSON'],
                              object_pairs_hook=engine._position_decoder().unique_object)
        _fields(original, 'saved comparison input', {'A', 'B'})
        for role in ('A', 'B'):
            _fields(original[role], 'saved comparison ' + role, {'subject', 'meaning'})
            for key in ('subject', 'meaning'):
                text = engine._expect_string(original[role][key], 'saved comparison ' + key)
                if not text.strip():
                    raise ValueError('saved comparison ' + key + ' must be nonempty text')
        validate(saved['output'], diagnostics=True, symmetric=True)
        raw = saved['inputs']['INPUT_JSON']
        if selection['reverse']:
            raw = json.dumps({'A': original['B'], 'B': original['A']}, ensure_ascii=False)
        cases.append(dict(id=identifier, inputs={'INPUT_JSON': raw}, evidence=dict(
            saved_comparison=dict(selection=selection, experiment=str(directory),
                prompt_id=report['prompt_id'], input_sha256=saved['input_sha256'],
                receipt=saved['receipt'], parsed=saved['parsed'], original_input=original,
                original_evidence=saved.get('evidence', {})),
            review=review, application_allowed=False)))
    return cases, dict(input_view='saved_comparisons', cases=len(cases), application_allowed=False)


def create_counterexample_checks(source, *, base, read, load_report):
    """Bind exact saved proposals to receipt-bound meanings without old labels."""
    engine._expect_fields(source, 'saved counterexample checks',
                          {'schema_version', 'saved_counterexamples'})
    selections = source['saved_counterexamples']
    if (type(source['schema_version']) is not int or source['schema_version'] != 1
            or not isinstance(selections, list) or not 1 <= len(selections) <= 128):
        raise ValueError('expected schema 1 and 1 through 128 saved counterexamples')
    cases, identifiers = [], set()
    for selection in selections:
        fields = {'id', 'experiment', 'case_id', 'direction', 'field', 'excerpt', 'reverse'}
        if isinstance(selection, dict) and 'nodes_from' in selection:
            fields.add('nodes_from')
        engine._expect_fields(selection, 'saved counterexample selection', fields)
        identifier = engine._expect_identifier(selection['id'], 'counterexample id')
        if identifier in identifiers:
            raise ValueError('duplicate counterexample id')
        identifiers.add(identifier)
        reference = selection['experiment']
        engine._expect_fields(reference, 'saved comparison reference', {'path', 'sha256'})
        directory = engine._resolve_path(reference['path'], 'saved comparison', base)
        envelope_path = directory / 'experiment.json'
        if engine._sha256_file(envelope_path) != reference['sha256']:
            raise ValueError('saved comparison reference hash differs')
        read(envelope_path)
        report = load_report(directory)
        matching = [case for case in report['cases'] if case['id'] == selection['case_id']]
        if (len(matching) != 1 or matching[0]['status'] != 'valid'
                or not matching[0].get('receipt')):
            raise ValueError('counterexample requires a valid saved comparison')
        saved = matching[0]
        legacy_directions = {'local_contains_canonical', 'canonical_contains_local'}
        symmetric_directions = {'A_contains_B', 'B_contains_A'}
        if (not isinstance(selection['direction'], str)
                or selection['direction'] not in legacy_directions | symmetric_directions):
            raise ValueError('unknown counterexample containment direction')
        if selection['field'] not in {'answer', 'justification'}:
            raise ValueError('counterexample field must be answer or justification')
        original = json.loads(saved['inputs']['INPUT_JSON'],
                              object_pairs_hook=engine._position_decoder().unique_object)
        original = engine._expect_object(original, 'saved counterexample input')
        symmetric = selection['direction'] in symmetric_directions
        roles = ('A', 'B') if symmetric else ('local', 'canonical')
        if set(original) != set(roles):
            raise ValueError('counterexample direction does not match saved input')
        parsed = (validate(saved['output'], diagnostics=True, symmetric=True)
                  if symmetric else engine._expect_object(
                      saved.get('parsed') or {}, 'saved comparison answer'))
        directions = symmetric_directions if symmetric else legacy_directions
        for key, direction_field in (('answers', 'question_id'), ('questions', 'id')):
            rows = parsed.get(key, [])
            if (not isinstance(rows, list) or any(not isinstance(row, dict)
                    or not isinstance(row.get(direction_field), str)
                    or row[direction_field] not in directions for row in rows)):
                raise ValueError('saved containment directions do not match input')
        answers = [row for row in parsed.get('answers', [])
                   if row.get('question_id') == selection['direction']]
        if len(answers) != 1:
            raise ValueError('counterexample requires exactly one saved directional answer')
        proposal = answers[0].get(selection['field'])
        engine._expect_string(proposal, 'saved counterexample text')
        excerpt = selection['excerpt']
        if excerpt is not None:
            engine._expect_string(excerpt, 'counterexample excerpt')
            if proposal.count(excerpt) != 1:
                raise ValueError('counterexample requires an exact unique excerpt')
            proposal = excerpt
        if type(selection['reverse']) is not bool:
            raise ValueError('counterexample reverse must be boolean')
        nodes = {}
        for role in roles:
            value = engine._expect_object(original[role], 'fixed ' + role)
            if symmetric:
                _fields(value, 'fixed ' + role, {'subject', 'meaning'})
            elif not {'subject', 'meaning'} <= set(value):
                raise ValueError('fixed ' + role + ' requires subject and meaning')
            nodes[role] = {key: engine._expect_string(value[key], 'fixed ' + key)
                           for key in ('subject', 'meaning')}
            if any(not text.strip() for text in nodes[role].values()):
                raise ValueError('fixed subject and meaning must be nonempty text')
        provenance = {}
        if 'nodes_from' in selection:
            if not symmetric:
                raise ValueError('nodes_from requires a symmetric saved counterexample')
            reference = selection['nodes_from']
            _fields(reference, 'nodes_from', {'experiment', 'case_id'})
            targets, _ = create_saved_comparisons(dict(schema_version=1,
                saved_comparisons=[dict(id=identifier, **reference, reverse=False)]),
                base=base, read=read, load_report=load_report)
            nodes = json.loads(targets[0]['inputs']['INPUT_JSON'])
            provenance['nodes_from'] = targets[0]['evidence']['saved_comparison']
        if selection['reverse']:
            first, second = roles
            nodes[first], nodes[second] = nodes[second], nodes[first]
        payload = {**nodes, 'case': proposal}
        cases.append(dict(id=identifier,
            inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
            evidence=dict(saved_counterexample=dict(selection=selection,
                experiment=str(directory), prompt_id=report['prompt_id'],
                input_sha256=saved['input_sha256'], receipt=saved['receipt'],
                parsed=saved['parsed'], original_input=original), **provenance,
                application_allowed=False)))
    return cases, dict(input_view='saved_counterexamples', cases=len(cases),
                       application_allowed=False)


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


def project_symmetric_fixed_meanings(case, *, input_order=None):
    """Expose only the two fixed scopes, retaining the pinned source for audit."""
    if input_order is not None and input_order not in (['A', 'B'], ['B', 'A']):
        raise ValueError('input_order must be ["A", "B"] or ["B", "A"]')
    original = json.loads(case['inputs']['INPUT_JSON'])
    if not isinstance(original, dict) or set(original) not in ({'local', 'canonical'}, {'A', 'B'}):
        raise ValueError('symmetric_fixed_meanings requires local/canonical or symmetric A/B node inputs')
    evidence = case.get('evidence', {})
    symmetric = set(original) == {'A', 'B'}
    if symmetric and evidence.get('input_view') != 'symmetric_fixed_meanings':
        raise ValueError('symmetric A/B inputs require symmetric_fixed_meanings source evidence')
    payload = {}
    for source, target in (tuple((key, key) for key in original) if symmetric
                           else (('local', 'A'), ('canonical', 'B'))):
        value = original[source]
        if not isinstance(value, dict):
            raise ValueError(source + ' node must be an object')
        if symmetric and set(value) != {'subject', 'meaning'}:
            raise ValueError('symmetric A/B nodes require only subject and meaning')
        entry = value.get('entry', value)
        if not isinstance(entry, dict):
            raise ValueError(source + ' entry must be an object')
        subject = entry.get('subject')
        meaning = value.get('meaning')
        if any(not isinstance(text, str) or not text.strip() for text in (subject, meaning)):
            raise ValueError(source + ' subject and fixed meaning must be nonempty text')
        payload[target] = value if symmetric else {'subject': subject, 'meaning': meaning}
    provenance = {} if symmetric else {'source_input': original}
    if not symmetric and 'input_view' in evidence:
        provenance['source_input_view'] = evidence['input_view']
    if input_order is not None:
        payload = {key: payload[key] for key in input_order}
        provenance['input_order'] = list(input_order)
    return {**case, 'inputs': {'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
            'evidence': {**evidence, **provenance, 'input_view': 'symmetric_fixed_meanings'}}


def validate(raw, *, diagnostics=False, meaning=None, symmetric=False):
    """Validate the approved output mechanics without judging its semantics."""
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    if symmetric and not diagnostics:
        raise ValueError('symmetric Compare requires questions and answers')
    fields = {'relation', 'reason'} | (set() if symmetric else {'meaning'})
    fields |= {'questions', 'answers'} if diagnostics else set()
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError('expected questions, answers, relation, and reason' if symmetric else
                         'expected meaning, questions, answers, relation, and reason' if diagnostics else
                         'expected meaning, relation, and reason')
    directions = ({'A_contains_B', 'B_contains_A'} if symmetric else
                  {'local_contains_canonical', 'canonical_contains_local'})
    relations = {'equivalent', 'neither', 'uncertain'} | directions
    if not isinstance(value['relation'], str) or value['relation'] not in relations:
        raise ValueError('unknown hierarchy comparison relation')
    if not symmetric:
        if value['meaning'] is None:
            if value['relation'] != 'uncertain':
                raise ValueError('null local meaning requires uncertain')
        elif not isinstance(value['meaning'], str) or not value['meaning'].strip():
            raise ValueError('meaning must be nonempty text or null')
    if not isinstance(value['reason'], str) or not value['reason'].strip():
        raise ValueError('reason must be nonempty text')
    if diagnostics:
        if not symmetric and (not isinstance(meaning, str) or value['meaning'] != meaning):
            raise ValueError('Compare answer must copy the fixed local meaning exactly')
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


def validate_meaning(raw, *, post=None, diagnostic=False, ambiguity_diagnostics=False, with_title=False):
    """Validate a local meaning, matching NBSP and ordinary spaces in quotes."""
    value = json.loads(raw, object_pairs_hook=engine._position_decoder().unique_object)
    diagnostic = diagnostic or ambiguity_diagnostics
    fields = {'meaning', 'evidence'} if diagnostic else {'meaning'}
    if ambiguity_diagnostics:
        fields.update({'ambiguities', 'resolutions'})
    if with_title:
        fields.add('title')
    if not isinstance(value, dict) or set(value) != fields:
        if with_title:
            raise ValueError('expected ' + ', '.join(sorted(fields)))
        if ambiguity_diagnostics:
            raise ValueError('expected ambiguities, resolutions, meaning and evidence')
        raise ValueError('expected meaning and evidence' if diagnostic else 'expected only meaning')
    if value['meaning'] is not None and (
            not isinstance(value['meaning'], str) or not value['meaning'].strip()):
        raise ValueError('meaning must be nonempty text or null')
    if with_title:
        if value['title'] is not None and (
                not isinstance(value['title'], str) or not value['title'].strip()):
            raise ValueError('title must be nonempty text or null')
        if (value['meaning'] is None) != (value['title'] is None):
            raise ValueError('title must be null exactly when meaning is null')
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
        quote_post = post.replace('\u00a0', ' ')
        for record in records:
            if not isinstance(record, dict) or set(record) != {'quote', 'supports', 'inference'}:
                raise ValueError('expected quote, supports and inference in each diagnostic record')
            for name in ('quote', 'supports'):
                if not isinstance(record[name], str) or not record[name].strip():
                    raise ValueError('diagnostic ' + name + ' must be nonempty text')
            if record['quote'].replace('\u00a0', ' ') not in quote_post:
                raise ValueError('diagnostic quote must be an exact contiguous excerpt of the local post')
            inference = record['inference']
            if inference is not None and (not isinstance(inference, str) or not inference.strip()):
                raise ValueError('diagnostic inference must be nonempty text or null')
    return value
