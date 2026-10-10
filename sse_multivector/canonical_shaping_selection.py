"""Nominate local entries that resemble several overcrowded canonical siblings.

Similarity selects the next local entry; normal graph traversal owns placement.
This bounded research selector reuses saved subject vectors and makes no calls.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _scores(rows, siblings, vectors):
    identifiers = [row['id'] for row in siblings]
    keys = [(row['note_id'], row['number']) for row in rows]
    if len(set(identifiers)) != len(identifiers) or len(set(keys)) != len(keys):
        raise ValueError('duplicate canonical ID or local entry')
    if len(rows) > 4096 or len(siblings) > 512:
        raise ValueError('bounded shaping selection requires at most 4096 locals and 512 siblings')
    if not rows or not siblings:
        return identifiers, keys, {}, None
    headings = list(dict.fromkeys(row['subject'] for row in [*rows, *siblings]))
    if any(not isinstance(text, str) or not text.strip() for text in headings):
        raise ValueError('subject headings must be nonempty text')
    if any(text not in vectors for text in headings):
        raise ValueError('missing saved subject vector')
    matrix = np.asarray([vectors[text] for text in headings], dtype=np.float64)
    if matrix.ndim != 2 or not matrix.shape[1] or not np.isfinite(matrix).all():
        raise ValueError('finite equal-dimension subject vectors required')
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise ValueError('finite nonzero subject vectors required')
    matrix /= norms[:, None]
    indices = {text: i for i, text in enumerate(headings)}
    local_headings = list(dict.fromkeys(row['subject'] for row in rows))
    sibling_vectors = matrix[[indices[row['subject']] for row in siblings]]
    similarities = matrix[[indices[text] for text in local_headings]] @ sibling_vectors.T
    scores = {text: similarities[i] for i, text in enumerate(local_headings)}
    return identifiers, keys, scores, sibling_vectors


def rank_candidates(rows, siblings, vectors, *, eligible=None):
    """Order local entries by their second-best eligible sibling cosine.

    ``eligible`` maps (note_id, number) to IDs supplied by normal construction.
    Entries with fewer than two eligible siblings remain last, with no score.
    Identical headings share computation, but their local entries stay distinct.
    """
    identifiers, keys, scores, sibling_vectors = _scores(rows, siblings, vectors)
    if sibling_vectors is None:
        return []
    result = []
    for key, row in zip(keys, rows, strict=True):
        allowed = set(identifiers) if eligible is None else set(eligible[key])
        if allowed - set(identifiers):
            raise ValueError('eligibility contains an unknown sibling')
        matches = sorted((dict(canonical_id=identifier,
                               cosine=float(np.clip(scores[row['subject']][i], -1, 1)))
                          for i, identifier in enumerate(identifiers) if identifier in allowed),
                         key=lambda match: (-match['cosine'], match['canonical_id']))
        result.append(dict(local=dict(note_id=key[0], number=key[1]), subject=row['subject'],
                           score=matches[1]['cosine'] if len(matches) >= 2 else None,
                           eligible_siblings=len(matches), matches=matches[:3]))
    return sorted(result, key=lambda row: (row['score'] is None,
                  -(row['score'] or 0), row['local']['note_id'], row['local']['number']))


def rank_subgroups(rows, siblings, vectors, *, eligible=None, max_choices=6, limit=10):
    """Propose overlapping nearest-neighbor groups and inspect possible parents.

    The score is the weakest member cosine minus the strongest outside cosine.
    It measures separation, not containment direction. All proposed members must
    be eligible, while all other siblings remain in the outside comparison.
    """
    if type(max_choices) is not int or not 2 <= max_choices <= 6:
        raise ValueError('bounded subgroup choice limit must be between two and six')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('subgroup candidate limit must be between one and twenty')
    siblings = sorted(siblings, key=lambda row: row['id'])
    identifiers, keys, scores, sibling_vectors = _scores(rows, siblings, vectors)
    if not rows or len(siblings) < 3:
        return []
    pairwise = sibling_vectors @ sibling_vectors.T
    allowed = {}
    for key in keys:
        allowed[key] = set(identifiers) if eligible is None else set(eligible[key])
        if allowed[key] - set(identifiers):
            raise ValueError('eligibility contains an unknown sibling')
    proposals = set()
    for seed in range(len(siblings)):
        neighbors = sorted((i for i in range(len(siblings)) if i != seed),
                           key=lambda i: (-pairwise[seed, i], identifiers[i]))
        for size in range(2, min(max_choices, len(siblings) - 1) + 1):
            proposals.add(tuple(sorted([seed, *neighbors[:size - 1]])))
    groups = []
    for group in sorted(proposals):
        members = [identifiers[i] for i in group]
        outside = [i for i in range(len(siblings)) if i not in group]
        ranked = []
        for key, row in zip(keys, rows, strict=True):
            if not set(members) <= allowed[key]:
                continue
            values = np.clip(scores[row['subject']], -1, 1)
            weakest = min(float(values[i]) for i in group)
            strongest = min(outside, key=lambda i: (-values[i], identifiers[i]))
            ranked.append(dict(local=dict(note_id=key[0], number=key[1]),
                subject=row['subject'], score=weakest - float(values[strongest]),
                weakest_member_cosine=weakest,
                strongest_outside_match=dict(canonical_id=identifiers[strongest],
                                             cosine=float(values[strongest]))))
        ranked.sort(key=lambda row: (-row['score'], -row['weakest_member_cosine'],
                                    row['local']['note_id'], row['local']['number']))
        remaining = len(siblings) - len(group) + 1
        groups.append(dict(members=members, coherence=float(np.mean([
            pairwise[a, b] for i, a in enumerate(group) for b in group[i + 1:]])),
            remaining_choices_if_grouped=remaining,
            within_choice_limit_if_grouped=remaining <= max_choices,
            ranked=ranked[:limit]))
    return sorted(groups, key=lambda group: (len(group['members']), -group['coherence'],
                                             group['members']))


def prepare(reference_project, state_path, menu_path, parent, output, *, method='second-best'):
    """Freeze a nomination against existing native state, menu and SSE receipts."""
    if __package__:
        from .candidate_ranking_study import _reference
    else:
        from candidate_ranking_study import _reference
    workflow, trial, _, _, subject_vectors, _ = _reference(reference_project)
    state_path, menu_path, output = (Path(path).resolve() for path in
                                      (state_path, menu_path, output))
    if output.exists():
        raise FileExistsError(output)
    if method not in ('second-best', 'subgroups'):
        raise ValueError('unknown shaping selection method')
    state_bytes, menu_bytes = state_path.read_bytes(), menu_path.read_bytes()
    protected = {str(state_path): hashlib.sha256(state_bytes).hexdigest(),
                 str(menu_path): hashlib.sha256(menu_bytes).hexdigest()}
    state, menu = json.loads(state_bytes), json.loads(menu_bytes)
    trial._check(state)
    if (state['status'] != 'complete' or 'shape' in state
            or menu.get('status') != 'shaped_candidate' or 'shape' not in menu):
        raise ValueError('selection requires a complete raw state and a completed menu')
    raw_nodes = {node['id']: node for node in state['nodes']}
    raw_ancestors = trial._ancestors(state['nodes'])
    trial._ancestors(menu['nodes'])
    for node in menu['nodes']:
        original = raw_nodes.get(node['id'])
        if original is None or any(node[field] != original[field]
                                   for field in ('subject', 'meaning', 'entries')):
            raise ValueError('menu changed an original canonical node')
        if set(node['parents']) - raw_ancestors[node['id']]:
            raise ValueError('menu contains an unwitnessed parent relationship')
    if parent is not None and parent not in {node['id'] for node in menu['nodes']}:
        raise ValueError('unknown menu parent')
    siblings = [node for node in menu['nodes'] if
                (not node['parents'] if parent is None else parent in node['parents'])]
    if len(siblings) <= 6:
        raise ValueError('selected group is not overcrowded under K=6')
    corpus_path = Path(state['corpus'])
    if menu['corpus'] != state['corpus']:
        raise ValueError('menu and raw state use different corpora')
    selected_notes = {row['note_id'] for row in state['roots']}
    corpus_bytes = corpus_path.read_bytes()
    protected[str(corpus_path)] = hashlib.sha256(corpus_bytes).hexdigest()
    corpus = {note['note_id']: note for note in json.loads(corpus_bytes)['notes']
              if note['note_id'] in selected_notes}
    processed = {(step['local']['note_id'], step['local']['number']) for step in state['steps']}
    rows = [dict(note_id=note_id, **row) for note_id, note in corpus.items()
            for row in note['subjects'] if (note_id, row['number']) not in processed]
    mapping = {(entry['note_id'], entry['number']): node['id']
               for node in state['nodes'] for entry in node['entries']}
    sibling_ids = {node['id'] for node in siblings}
    eligible = {}
    for row in rows:
        local = {field: row[field] for field in ('note_id', 'number')}
        mapped = mapping.get((row['note_id'], row['number'].rsplit('.', 1)[0])) \
            if '.' in row['number'] else None
        eligible[(row['note_id'], row['number'])] = sibling_ids.intersection(
            node['id'] for node in trial._eligible(state, local, mapped))
    policy = state.get('comparison_policy') or state.get('previous_comparison_policy')
    if not policy or not policy.get('subject_probe'):
        raise ValueError('state has no saved subject-vector source')
    probe = Path(policy['subject_probe'])
    saved, receipt, vector_sources = subject_vectors.load_subject_vectors(probe)
    for path, expected in vector_sources.items():
        if path in protected and protected[path] != expected:
            raise ValueError('conflicting selection source: ' + path)
        protected[path] = expected
    own_source = Path(__file__).resolve()
    protected[str(own_source)] = hashlib.sha256(own_source.read_bytes()).hexdigest()
    texts = {row['subject'] for row in [*rows, *siblings]}
    vectors = {}
    for text in texts:
        digest = hashlib.sha256(text.encode()).hexdigest()
        vectors[text] = saved[(digest, digest[:16])]
    ranked = rank_candidates(rows, siblings, vectors, eligible=eligible) if method == 'second-best' else []
    groups = rank_subgroups(rows, siblings, vectors, eligible=eligible) if method == 'subgroups' else None
    for path, expected in protected.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('selection source changed: ' + path)
    report = dict(schema_version=1 if groups is None else 2, state=str(state_path), menu=str(menu_path),
        parent=parent, siblings=sorted(sibling_ids), max_choices=6,
        method=('second-highest eligible sibling subject cosine' if groups is None else
                'nearest sibling groups; weakest member minus strongest outside subject cosine'), ranked=ranked,
        selected=ranked[0]['local'] if ranked and ranked[0]['score'] is not None else None,
        sources=protected, dimensions=receipt['dimensions'], inference_calls=0, new_encodings=0,
        interpretation='Nomination only; no containment or placement is established.')
    if groups is not None:
        report.update(groups=groups, sibling_subjects={node['id']: node['subject'] for node in siblings},
                      interpretation='Offline subgroup candidates only; no parent direction or automatic selection is established.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return dict(selected=report['selected'], candidates=len(rows), siblings=len(siblings),
                output=str(output), inference_calls=0, new_encodings=0,
                **({'groups': len(groups)} if groups is not None else {}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference-project', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--menu', type=Path, required=True)
    parser.add_argument('--parent', help='canonical parent ID; omit to consider roots')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--method', choices=('second-best', 'subgroups'), default='second-best')
    args = parser.parse_args()
    print(json.dumps(prepare(args.reference_project, args.state, args.menu, args.parent, args.output,
                             method=args.method)))


if __name__ == '__main__':
    main()
