"""Compare literal and scored memberships using the existing description relations.

Preparation copies source inputs unchanged. Analysis consumes native single-label
scores; it performs no inference, candidate selection, or semantic certification.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

import mask_description_hierarchy


def _validate_inputs(inputs):
    if not isinstance(inputs, list) or not inputs:
        raise ValueError('nonempty ordered input records required')
    for row, record in enumerate(inputs):
        if (type(record.get('row')) is not int or record['row'] != row
                or not isinstance(record.get('subject'), str) or not record['subject'].strip()
                or not isinstance(record.get('note'), str) or not record['note']):
            raise ValueError('ordered rows with subjects and note owners required')


def prepare_candidates(patterns, anchors):
    """Keep each anchor and every saved adjacent pair containing an anchor."""
    inputs, tokens = patterns['inputs'], patterns['tokens']
    spans = patterns['casefolded_character_spans']
    _validate_inputs(inputs)
    if (not anchors or any(not isinstance(a, str) or not a or a != a.casefold()
                           or any(c.isspace() for c in a) for a in anchors)
            or len(set(anchors)) != len(anchors)):
        raise ValueError('distinct nonempty casefolded single-token anchors required')
    if len(tokens) != len(inputs) or len(spans) != len(inputs):
        raise ValueError('one token and character-span sequence per source row required')
    for record, words, offsets in zip(inputs, tokens, spans):
        if len(words) != len(offsets):
            raise ValueError('token and character-span counts differ')
        previous_end = 0
        for word, span in zip(words, offsets):
            if (not isinstance(word, str) or not word or len(span) != 2
                    or any(type(v) is not int for v in span)
                    or not previous_end <= span[0] < span[1] <= len(record['subject'].casefold())
                    or record['subject'].casefold()[span[0]:span[1]] != word):
                raise ValueError('saved token does not match its casefolded character span')
            previous_end = span[1]

    candidates = []
    for anchor in anchors:
        digest = hashlib.sha256(json.dumps(['unigram', [anchor]], ensure_ascii=False).encode()).hexdigest()
        candidates.append(dict(id='U' + digest[:12], tokens=[anchor], family='unigram'))
    for pair in patterns['adjacent']:
        if set(pair['tokens']) & set(anchors):
            if len(pair['tokens']) != 2 or pair['tokens'][0] == pair['tokens'][1]:
                raise ValueError('saved adjacent patterns require two distinct tokens')
            candidates.append(dict(copy.deepcopy(pair), family='adjacent'))

    for candidate in candidates:
        words = candidate['tokens']
        label = ' '.join(words)
        positions, characters = [], []
        for row, row_tokens in enumerate(tokens):
            indices = [list(range(i, i + len(words)))
                       for i in range(len(row_tokens) - len(words) + 1)
                       if row_tokens[i:i + len(words)] == words]
            if not indices:
                continue
            occurrences = [[spans[row][p[0]][0], spans[row][p[-1]][1]] for p in indices]
            if any(inputs[row]['subject'].casefold()[start:end] != label
                   for start, end in occurrences):
                raise ValueError('space-joined label differs from a saved casefolded occurrence')
            positions.append([row, indices])
            characters.append([row, occurrences])
        rows = [row for row, _ in positions]
        notes = sorted({inputs[row]['note'] for row in rows})
        if candidate['family'] == 'adjacent' and any(candidate[k] != value for k, value in
                [('positions', positions), ('rows', rows), ('notes', notes)]):
            raise ValueError('saved adjacent pattern rows, notes or positions differ from source')
        candidate.update(label=label, features=words.copy(), positions=positions,
                         rows=rows, notes=notes, casefolded_character_occurrences=characters)
    if (len({c['id'] for c in candidates}) != len(candidates)
            or len({c['label'] for c in candidates}) != len(candidates)):
        raise ValueError('duplicate candidate ID or label')
    return dict(inputs=copy.deepcopy(inputs), candidates=candidates)


def _membership_summary(candidates):
    classes = {}
    for candidate in candidates:
        classes.setdefault(tuple(candidate['notes']), []).append(candidate['id'])
    return dict(candidates=candidates,
                relations=mask_description_hierarchy.description_relations(candidates),
                equal_note_set_classes=[dict(notes=list(notes), candidate_ids=sorted(ids))
                                        for notes, ids in sorted(classes.items()) if len(ids) > 1],
                empty_candidates=sorted(c['id'] for c in candidates if not c['notes']),
                single_note_candidates=sorted(c['id'] for c in candidates if len(c['notes']) == 1))


def analyze_scores(prepared, scores, cutoffs):
    """Validate the complete matrix, then threshold note maxima independently."""
    inputs, candidates = prepared['inputs'], prepared['candidates']
    _validate_inputs(inputs)
    if (not cutoffs or any(type(c) not in (int, float) or not math.isfinite(c)
                           or not 0 <= c <= 1 for c in cutoffs)
            or len(set(cutoffs)) != len(cutoffs)):
        raise ValueError('distinct finite score cutoffs in [0, 1] required')
    labels = {c['label']: c for c in candidates}
    if (not candidates or len(labels) != len(candidates)
            or len({c['id'] for c in candidates}) != len(candidates)):
        raise ValueError('distinct nonempty candidate IDs and labels required')
    if not isinstance(scores, list) or len(scores) != len(inputs) * len(labels):
        raise ValueError('exact complete row-by-label score matrix required')
    matrix = {}
    for record in scores:
        row, requested = record.get('row'), record.get('labels')
        values = record.get('scores')
        if (type(row) is not int or not 0 <= row < len(inputs)
                or record.get('text') != inputs[row]['subject']
                or record.get('condition') != 'single'
                or not isinstance(requested, list) or len(requested) != 1
                or not isinstance(requested[0], str) or requested[0] not in labels
                or not isinstance(values, list) or len(values) != 1
                or not isinstance(values[0], dict) or values[0].get('label') != requested[0]):
            raise ValueError('native single-label request or subject text mismatch')
        value = values[0]
        if (any(type(value.get(k)) not in (int, float) or not math.isfinite(value[k])
                for k in ('score', 'logit')) or not 0 <= value['score'] <= 1):
            raise ValueError('finite native logit and probability score required')
        key = (row, requested[0])
        if key in matrix:
            raise ValueError('duplicate row-label score')
        matrix[key] = value['score']
    if set(matrix) != {(r['row'], label) for r in inputs for label in labels}:
        raise ValueError('missing or unexpected row-label score')

    note_rows = {}
    for record in inputs:
        note_rows.setdefault(record['note'], []).append(record['row'])
    note_scores = []
    for candidate in candidates:
        label = candidate['label']
        for note, rows in sorted(note_rows.items()):
            maximum = max(matrix[row, label] for row in rows)
            note_scores.append(dict(candidate_id=candidate['id'], label=label, note=note,
                                    score=maximum,
                                    attaining_rows=[r for r in rows if matrix[r, label] == maximum]))

    literal = _membership_summary(copy.deepcopy(candidates))
    thresholds = []
    for cutoff in cutoffs:
        memberships = []
        for candidate in candidates:
            rows = [r['row'] for r in inputs if matrix[r['row'], candidate['label']] >= cutoff]
            notes = sorted({inputs[row]['note'] for row in rows})
            # Do not copy literal occurrence positions onto newly scored rows.
            memberships.append(dict(id=candidate['id'], label=candidate['label'],
                                    features=candidate['features'].copy(), rows=rows, notes=notes,
                                    added_notes=sorted(set(notes) - set(candidate['notes'])),
                                    removed_notes=sorted(set(candidate['notes']) - set(notes))))
        summary = _membership_summary(memberships)
        changes = {}
        for rule, relation in summary['relations'].items():
            changes[rule] = {}
            for field in ('all_edges', 'immediate_edges'):
                old = {tuple(e) for e in literal['relations'][rule][field]}
                new = {tuple(e) for e in relation[field]}
                changes[rule][field] = dict(added=[list(e) for e in sorted(new - old)],
                                            removed=[list(e) for e in sorted(old - new)])
        thresholds.append(dict(cutoff=cutoff, edge_changes=changes, **summary))
    return dict(literal=literal, note_scores=note_scores, thresholds=thresholds)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def _source(path, raw):
    return dict(path=str(path.resolve()), sha256=_sha(raw))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--patterns', type=Path, required=True)
    prepare.add_argument('--anchors', nargs='+', required=True)
    analyze = commands.add_parser('analyze')
    analyze.add_argument('--prepared', type=Path, required=True)
    analyze.add_argument('--scores', type=Path, required=True)
    analyze.add_argument('--cutoffs', nargs='+', type=float, required=True)
    for command in (prepare, analyze):
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise FileExistsError('output exists; preserve earlier results')
    snapshots = {name: Path(__file__).with_name(name).read_bytes() for name in
                 ('category_path_compatibility.py', 'mask_description_hierarchy.py',
                  'select_mask_distinctions.py', 'select_note_categories.py')}
    config = dict(command=args.command, code_sha256={name: _sha(raw) for name, raw in snapshots.items()},
                  limitations=['labels are source-derived token strings, not certified meanings',
                               'note membership is a maximum over all subject records',
                               'all candidates remain; no equivalence collapse or membership propagation',
                               'existing relations are not evidence of semantic correctness'])
    if args.command == 'prepare':
        raw = args.patterns.read_bytes()
        patterns = json.loads(raw)
        prepared = prepare_candidates(patterns, args.anchors)
        artifacts = {'inputs.json': _json_bytes(prepared['inputs']),
                     'candidates.json': _json_bytes(prepared['candidates']),
                     'literal.json': _json_bytes(_membership_summary(prepared['candidates']))}
        config.update(patterns_source=_source(args.patterns, raw), anchors=args.anchors,
                      source_run_id=patterns.get('run_id'),
                      candidates_sha256=_sha(artifacts['candidates.json']))
    else:
        input_raw = (args.prepared / 'inputs.json').read_bytes()
        candidate_raw = (args.prepared / 'candidates.json').read_bytes()
        prepared_raw = (args.prepared / 'config.json').read_bytes()
        prepared_config = json.loads(prepared_raw)
        if (_sha(input_raw) != prepared_config['inputs_sha256']
                or _sha(candidate_raw) != prepared_config['candidates_sha256']):
            raise ValueError('prepared input or candidate hash mismatch')
        for name, digest in prepared_config['code_sha256'].items():
            if _sha((args.prepared / 'source' / name).read_bytes()) != digest:
                raise ValueError('prepared source snapshot hash mismatch')
        prepared = dict(inputs=json.loads(input_raw), candidates=json.loads(candidate_raw))
        raw = args.scores.read_bytes()
        result = analyze_scores(prepared, json.loads(raw), args.cutoffs)
        artifacts = {'inputs.json': input_raw, 'candidates.json': candidate_raw,
                     'scores.json': raw, 'result.json': _json_bytes(result),
                     'prepared-config.json': prepared_raw}
        config.update(prepared_source=_source(args.prepared / 'config.json', prepared_raw),
                      scores_source=_source(args.scores, raw), cutoffs=args.cutoffs,
                      patterns_source=prepared_config['patterns_source'],
                      candidates_sha256=_sha(candidate_raw))
    config.update(inputs_sha256=_sha(artifacts['inputs.json']),
                  input_count=len(prepared['inputs']), candidate_count=len(prepared['candidates']),
                  note_count=len({r['note'] for r in prepared['inputs']}),
                  labels=[c['label'] for c in prepared['candidates']])
    artifacts['config.json'] = _json_bytes(config)
    args.output.mkdir(parents=True, exist_ok=False)
    for name, content in artifacts.items():
        with (args.output / name).open('xb') as stream:
            stream.write(content)
    (args.output / 'source').mkdir()
    for name, content in snapshots.items():
        with (args.output / 'source' / name).open('xb') as stream:
            stream.write(content)
    print(json.dumps(dict(command=args.command, inputs=config['input_count'],
                          candidates=config['candidate_count'], notes=config['note_count'])))


if __name__ == '__main__':
    main()
