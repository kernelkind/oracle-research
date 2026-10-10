"""Bounded, unlabelled Compare nominations from reviewed Bootstrap meanings.

This first pass has no canonical branches. SP paths nominate comparisons and
provide original local context; they never certify containment or create labels.
"""
from collections import Counter, defaultdict, deque
import json
from pathlib import Path
import re

from . import bootstrap_student_inputs as bootstrap
from . import extraction_pipeline as engine
from .hierarchy_inputs import validate_subjects


def validate_answer(answer, meaning):
    """Keep the existing three-field teacher contract and exact fixed meaning."""
    engine._expect_fields(answer, 'Compare answer', {'meaning', 'relation', 'reason'})
    if answer['meaning'] != meaning:
        raise ValueError('Compare answer must copy the fixed local meaning exactly')
    if (not isinstance(answer['relation'], str) or answer['relation'] not in {
            'equivalent', 'local_contains_canonical', 'canonical_contains_local', 'neither', 'uncertain'}):
        raise ValueError('unsupported Compare relation')
    engine._expect_string(answer['reason'], 'Compare reason')
    return answer


def collect(bundles):
    """Preserve provisional teacher decisions; never infer acceptance or labels."""
    cases, prompts, seen = [], {}, set()
    for plan, result in bundles:
        prompt_hash = engine._sha256_bytes(plan['prompt']['text'].encode())
        prompt = prompts.setdefault(prompt_hash, dict(text=plan['prompt']['text'], prompt_ids=[]))
        if plan['prompt']['id'] not in prompt['prompt_ids']:
            prompt['prompt_ids'].append(plan['prompt']['id'])
        planned = {case['id']: case for case in plan['cases']}
        for case in result['cases']:
            key = (plan['experiment'], case['id'])
            if key in seen:
                raise ValueError('duplicate collected Compare decision')
            seen.add(key)
            local = json.loads(case['inputs']['INPUT_JSON'])['local']
            answer = json.loads(case['output'],
                                object_pairs_hook=engine._position_decoder().unique_object)
            validate_answer(answer, local['meaning'])
            cases.append(dict(experiment=plan['experiment'], case_id=case['id'],
                prompt_id=plan['prompt']['id'], prompt_sha256=prompt_hash,
                input_sha256=planned[case['id']]['input_sha256'], inputs=case['inputs'],
                answer=answer, evidence=case['evidence'], reviews=case['reviews'],
                receipt=case['receipt']))
    return {'compare.json': dict(schema_version=1, prompts=prompts, cases=cases,
        semantic_status='Provisional saved Compare teacher decisions; no automatic '
                        'fit-target acceptance, semantic gold or branch qualification.')}


def accepted(reviews):
    """A current human decision takes precedence over agent assessments."""
    for role in ('user', 'agent'):
        decisions = [r for r in reviews if r.get('current') is True and r.get('role') == role
                     and r.get('verdict') in {'accept', 'reject', 'uncertain'}]
        if decisions:
            return decisions[-1]['verdict'] == 'accept'
    return False


def prepare(source, base):
    engine._expect_fields(source, 'Compare student input selection',
        {'schema_version', 'bootstrap', 'provenance', 'role', 'seed', 'max_pairs', 'self_pairs'})
    if type(source['schema_version']) is not int or source['schema_version'] != 1:
        raise ValueError('expected Compare input selection schema 1')
    if source['role'] not in {'train', 'evaluation'}:
        raise ValueError('expected train or evaluation role')
    for key in ('max_pairs', 'self_pairs'):
        if type(source[key]) is not int or not 0 <= source[key] <= 10000:
            raise ValueError(f'{key} must be an integer from 0 to 10000')
    if not source['max_pairs'] or source['self_pairs'] >= source['max_pairs']:
        raise ValueError('Compare nominations require non-self comparisons')
    seed = engine._expect_string(source['seed'], 'Compare nomination seed')
    protected = {}

    def load(key):
        ref = source[key]
        engine._expect_fields(ref, key, {'path', 'sha256'})
        path = engine._resolve_path(ref['path'], key, Path(base))
        raw = path.read_bytes()
        if not isinstance(ref['sha256'], str) or engine._sha256_bytes(raw) != ref['sha256']:
            raise ValueError(f'{key} hash mismatch')
        protected[str(path)] = ref['sha256']
        return json.loads(raw)

    bundle, provenance = load('bootstrap'), load('provenance')
    if (bundle.get('schema_version') != 1 or provenance.get('schema_version') != 1
            or provenance.get('inference_calls') != 0):
        raise ValueError('expected native offline Bootstrap collection')
    producers = {}
    for producer in provenance['experiments']:
        for case in producer['cases']:
            key = (producer['experiment'], case['id'])
            if key in producers:
                raise ValueError('duplicate Bootstrap producer receipt')
            producers[key] = (producer['prompt_id'], case['receipt'])
    nodes, note_roles, author_roles, text_roles = {}, {}, {}, {}
    for case in bundle['cases']:
        evidence = case['evidence']
        role = evidence.get('role')
        if evidence.get('split') != 'train' or role not in {'train', 'evaluation'}:
            raise ValueError('Compare source must retain original TRAIN and pilot roles')
        key = (case['experiment'], case['case_id'])
        if producers.get(key) != (case['prompt_id'], case['receipt']):
            raise ValueError('Bootstrap answer differs from native producer provenance')
        if case['case_id'] in nodes:
            raise ValueError('duplicate Bootstrap case identity')
        local = json.loads(case['inputs']['INPUT_JSON'])['local']
        validate_subjects({'subjects': local['hierarchy']['entries']})
        bootstrap.validate_answer(case['answer'], local['post'])
        for value, roles in [(evidence['local']['note_id'], note_roles),
                             (evidence['pubkey'], author_roles),
                             (' '.join(local['post'].split()), text_roles)]:
            if value in roles and roles[value] != role:
                raise ValueError('Compare pilot roles overlap a note, author or normalized text')
            roles[value] = role
        number = local['hierarchy']['selected']
        if number != evidence['local']['number']:
            raise ValueError('Bootstrap selected entry differs from original identity')
        entries = {entry['number']: entry for entry in local['hierarchy']['entries']}
        parts = number.split('.')
        entry = entries[number]
        original = dict(subject=entry['subject'], context=entry['context'], ancestors=[
            {k: entries['.'.join(parts[:depth])][k] for k in ('subject', 'context')}
            for depth in range(1, len(parts))])
        nodes[case['case_id']] = dict(case=case, local=local, entry=original,
            eligible=role == source['role'] and accepted(case['reviews'])
                     and case['answer']['meaning'] is not None)
    eligible = {key: node for key, node in nodes.items() if node['eligible']}
    if len(eligible) < 2 or len(eligible) < source['self_pairs']:
        raise ValueError('not enough reviewed non-null Bootstrap meanings in requested role')

    def rank(value):
        return engine._sha256_bytes(engine._canonical_json_bytes([seed, value]))

    by_note, by_heading, by_word = defaultdict(list), defaultdict(list), defaultdict(list)
    stop = {'a', 'an', 'and', 'as', 'at', 'by', 'for', 'from', 'in', 'of', 'on', 'the', 'to', 'with'}
    for key, node in eligible.items():
        by_note[node['case']['evidence']['local']['note_id']].append(key)
        heading = node['entry']['subject'].casefold()
        by_heading[heading].append(key)
        for word in set(re.findall(r'\w+', heading)) - stop:
            if len(word) > 2:
                by_word[word].append(key)
    for buckets in (by_note, by_heading, by_word):
        for values in buckets.values():
            values.sort(key=rank)
    families, seen = defaultdict(list), set()

    def nominate(a, b, family):
        pair = tuple(sorted((a, b)))
        if pair not in seen:
            families[family].append(pair)
            seen.add(pair)

    # At most two same-note partners per entry; never enumerate all SP pairs.
    for values in by_note.values():
        for index, a in enumerate(values):
            for offset in range(1, min(3, len(values))):
                nominate(a, values[(index+offset) % len(values)], 'same_tree')
    ordered = sorted(eligible, key=rank)
    notes = sorted(by_note, key=rank)
    next_note = {note: notes[(index+1) % len(notes)] for index, note in enumerate(notes)}
    for a in ordered:
        note_id = eligible[a]['case']['evidence']['local']['note_id']
        heading = eligible[a]['entry']['subject'].casefold()
        for b in by_heading[heading][:8]:
            if eligible[b]['case']['evidence']['local']['note_id'] != note_id:
                nominate(a, b, 'same_heading_cross_post')
        candidates = set()
        for word in set(re.findall(r'\w+', heading)) - stop:
            candidates.update(by_word.get(word, [])[:8])
        cross_post = [b for b in candidates
                      if eligible[b]['case']['evidence']['local']['note_id'] != note_id]
        for b in sorted(cross_post, key=lambda b: rank([a, b]))[:2]:
            nominate(a, b, 'word_overlap_cross_post')
        if len(notes) > 1:
            b = min(by_note[next_note[note_id]][:8], key=lambda b: rank([a, b]))
            nominate(a, b, 'cross_post_control')
    chosen = [(a, a, 'same_entry_control') for a in ordered[:source['self_pairs']]]
    queues = {family: deque(sorted(pairs, key=rank)) for family, pairs in families.items()}
    while len(chosen) < source['max_pairs'] and any(queues.values()):
        for family in sorted(queues):
            if queues[family] and len(chosen) < source['max_pairs']:
                chosen.append((*queues[family].popleft(), family))
    if len(chosen) != source['max_pairs']:
        raise ValueError('not enough reviewed non-null Compare nominations for requested count')
    cases = []
    for a, b, family in chosen:
        family_id = engine._sha256_bytes(engine._canonical_json_bytes([a, b]))
        for local_id, canonical_id in [(a, b)] + ([(b, a)] if a != b else []):
            left, right = eligible[local_id], eligible[canonical_id]
            payload = dict(local=dict(meaning=left['case']['answer']['meaning'],
                entry=left['entry'], post=left['local']['post']), canonical=dict(
                id=canonical_id, subject=right['entry']['subject'],
                meaning=right['case']['answer']['meaning'], entries=[right['entry']],
                parents=[], ancestors=[], descendants=[]))
            identity = engine._sha256_bytes(engine._canonical_json_bytes(payload))
            supports = {}
            for side, node in [('local', left), ('canonical', right)]:
                c = node['case']
                supports[side] = {k: c[k] for k in ('experiment', 'case_id', 'input_sha256', 'receipt')}
                supports[side].update(c['evidence']['local'], pubkey=c['evidence']['pubkey'])
            cases.append(dict(id='compare-'+identity,
                inputs={'INPUT_JSON': json.dumps(payload, ensure_ascii=False)},
                evidence=dict(**supports, family=family, family_id=family_id,
                    source_bootstrap=source['bootstrap'], source_provenance=source['provenance'],
                    role=source['role'], split='train', application_allowed=False,
                    semantic_status='Unlabelled qualification input; SP paths are not relation targets.')))
    return cases, protected, dict(method='compare_student_inputs', role=source['role'],
        eligible_meanings=len(eligible), pairs=len(chosen), cases=len(cases),
        families=dict(Counter(f for _, _, f in chosen)), target_answers=0,
        canonical_branches=False, application_allowed=False)
