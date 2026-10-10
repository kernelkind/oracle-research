"""Nominate local entries that resemble several overcrowded canonical siblings.

Similarity selects the next local entry; normal graph traversal owns placement.
This bounded research selector reuses saved SSE vectors and makes no calls.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def _scores(rows, siblings, vectors, *, sibling_vectors=None):
    identifiers = [row['id'] for row in siblings]
    keys = [(row['note_id'], row['number']) for row in rows]
    if len(set(identifiers)) != len(identifiers) or len(set(keys)) != len(keys):
        raise ValueError('duplicate canonical ID or local entry')
    if len(rows) > 4096 or len(siblings) > 512:
        raise ValueError('bounded shaping selection requires at most 4096 locals and 512 siblings')
    if not rows or not siblings:
        return identifiers, keys, {}, None
    headings = list(dict.fromkeys(row['subject'] for row in
                                 (rows if sibling_vectors is not None else [*rows, *siblings])))
    if any(not isinstance(text, str) or not text.strip() for text in headings):
        raise ValueError('subject headings must be nonempty text')
    if any(text not in vectors for text in headings):
        raise ValueError('missing saved subject vector')
    values = [vectors[text] for text in headings]
    if sibling_vectors is not None:
        if set(sibling_vectors) != set(identifiers):
            raise ValueError('sibling vectors must cover exactly the supplied canonical IDs')
        values += [sibling_vectors[identifier] for identifier in identifiers]
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or not matrix.shape[1] or not np.isfinite(matrix).all():
        raise ValueError('finite equal-dimension subject vectors required')
    norms = np.linalg.norm(matrix, axis=1)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise ValueError('finite nonzero subject vectors required')
    matrix /= norms[:, None]
    indices = {text: i for i, text in enumerate(headings)}
    local_headings = list(dict.fromkeys(row['subject'] for row in rows))
    sibling_matrix = (matrix[len(headings):] if sibling_vectors is not None else
                      matrix[[indices[row['subject']] for row in siblings]])
    similarities = matrix[[indices[text] for text in local_headings]] @ sibling_matrix.T
    scores = {text: similarities[i] for i, text in enumerate(local_headings)}
    return identifiers, keys, scores, sibling_matrix


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


def _local_ancestor_scores(rows, local_entries, scores, identifiers):
    """Aggregate descendant resemblance along original, same-note local paths."""
    by_key = {(row['note_id'], row['number']): row for row in local_entries}
    keys = [(row['note_id'], row['number']) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate local candidate')
    for key, row in zip(keys, rows, strict=True):
        if key not in by_key or any(row.get(field) != by_key[key].get(field)
                                   for field in ('subject', 'context')):
            raise ValueError('local candidate differs from original entry')
    indices = {key: i for i, key in enumerate(keys)}
    values = np.full((len(rows), len(identifiers)), -np.inf)
    witnesses = np.full(values.shape, -1, dtype=int)
    # Stable source identity resolves exact cosine ties, without changing scores.
    for entry_index in sorted(range(len(local_entries)), key=lambda i:
                              (local_entries[i]['note_id'], local_entries[i]['number'])):
        entry = local_entries[entry_index]
        parts = entry['number'].split('.')
        for depth in range(1, len(parts)):
            key = (entry['note_id'], '.'.join(parts[:depth]))
            if key not in by_key:
                raise ValueError('incomplete original local branch')
            if key not in indices:
                continue
            index = indices[key]
            similarities = np.clip(scores[entry['subject']], -1, 1)
            better = similarities > values[index]
            values[index, better] = similarities[better]
            witnesses[index, better] = entry_index
    return values, witnesses, by_key


def rank_subgroups(rows, siblings, vectors, *, eligible=None, max_choices=6, limit=10,
                  sibling_vectors=None, clustering='nearest', local_entries=None):
    """Propose sibling groups and inspect possible parents.

    The score is the weakest member cosine minus the strongest outside cosine.
    It measures separation, not containment direction. All proposed members must
    be eligible, while all other siblings remain in the outside comparison.
    Optional ID-bound sibling vectors replace both clustering and candidate
    comparison representations; local subject vectors stay unchanged.
    Complete-link merges use the weakest cross-group cosine and form nested
    groups. Only proper groups of two through max_choices are retained.
    With original local_entries, candidates are scored through their proper
    descendants and retain exact paths. This supplies a direction cue, not an
    established relationship to any canonical node.
    """
    if clustering not in ('nearest', 'complete'):
        raise ValueError('unknown sibling clustering method')
    if type(max_choices) is not int or not 2 <= max_choices <= 6:
        raise ValueError('bounded subgroup choice limit must be between two and six')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('subgroup candidate limit must be between one and twenty')
    siblings = sorted(siblings, key=lambda row: row['id'])
    identifiers, keys, scores, sibling_vectors = _scores(
        rows if local_entries is None else local_entries,
        siblings, vectors, sibling_vectors=sibling_vectors)
    if not rows or len(siblings) < 3:
        return []
    descendant_values = witnesses = by_key = None
    if local_entries is not None:
        descendant_values, witnesses, by_key = _local_ancestor_scores(
            rows, local_entries, scores, identifiers)
        keys = [(row['note_id'], row['number']) for row in rows]
    candidate_indices = {key: i for i, key in enumerate(keys)}
    pairwise = sibling_vectors @ sibling_vectors.T
    allowed = {}
    for key in keys:
        allowed[key] = set(identifiers) if eligible is None else set(eligible[key])
        if allowed[key] - set(identifiers):
            raise ValueError('eligibility contains an unknown sibling')
    proposals = set()
    if clustering == 'complete':
        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import squareform
        distances = 1 - np.clip(pairwise, -1, 1)
        np.fill_diagonal(distances, 0)
        merges = linkage(squareform(distances, checks=False), method='complete')
        clusters = {i: (i,) for i in range(len(siblings))}
        for index, (left, right, _, _) in enumerate(merges, start=len(siblings)):
            group = tuple(sorted(clusters[int(left)] + clusters[int(right)]))
            clusters[index] = group
            if 2 <= len(group) <= max_choices and len(group) < len(siblings):
                proposals.add(group)
    else:
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
        for candidate_index, (key, row) in enumerate(zip(keys, rows, strict=True)):
            if not set(members) <= allowed[key]:
                continue
            values = (np.clip(scores[row['subject']], -1, 1) if descendant_values is None
                      else descendant_values[candidate_index])
            if not np.isfinite(values).all():
                continue  # No proper descendants; not an original local parent.
            weakest = min(float(values[i]) for i in group)
            strongest = min(outside, key=lambda i: (-values[i], identifiers[i]))
            ranked.append(dict(local=dict(note_id=key[0], number=key[1]),
                subject=row['subject'], score=weakest - float(values[strongest]),
                weakest_member_cosine=weakest,
                strongest_outside_match=dict(canonical_id=identifiers[strongest],
                                             cosine=float(values[strongest]))))
        ranked.sort(key=lambda row: (-row['score'], -row['weakest_member_cosine'],
                                    row['local']['note_id'], row['local']['number']))
        ranked = ranked[:limit]
        if local_entries is not None:
            def match(candidate, sibling_index):
                key = (candidate['local']['note_id'], candidate['local']['number'])
                index = candidate_indices[key]
                descendant = local_entries[witnesses[index, sibling_index]]
                parts = descendant['number'].split('.')
                path = [dict(by_key[(key[0], '.'.join(parts[:depth]))])
                        for depth in range(len(key[1].split('.')), len(parts) + 1)]
                return dict(canonical_id=identifiers[sibling_index],
                            cosine=float(descendant_values[index, sibling_index]), path=path)

            for candidate in ranked:
                candidate['descendant_matches'] = [match(candidate, i) for i in group]
                outside_id = candidate['strongest_outside_match']['canonical_id']
                candidate['outside_descendant_match'] = match(candidate, identifiers.index(outside_id))
                matched = [m['path'][-1] for m in candidate['descendant_matches']]
                candidate['distinct_descendant_entries'] = len({m['number'] for m in matched})
                candidate['distinct_descendant_subjects'] = len({m['subject'] for m in matched})
        remaining = len(siblings) - len(group) + 1
        groups.append(dict(members=members, coherence=float(np.mean([
            pairwise[a, b] for i, a in enumerate(group) for b in group[i + 1:]])),
            remaining_choices_if_grouped=remaining,
            within_choice_limit_if_grouped=remaining <= max_choices,
            ranked=ranked))
        if clustering == 'complete':
            groups[-1]['minimum_pair_cosine'] = float(np.min([
                pairwise[a, b] for i, a in enumerate(group) for b in group[i + 1:]]))
    return sorted(groups, key=lambda group: (len(group['members']), -group['coherence'],
                                             group['members']))


def load_sibling_meanings(directory, state_path, siblings, subject_receipt, vector_reader):
    """Load standalone whole-meaning encodings bound to the exact native nodes."""
    directory = Path(directory).resolve()
    plan_path, request_path = directory / 'inputs.json', directory / 'worker-request.json'
    plan = json.loads(plan_path.read_bytes())
    if Path(plan['state']).resolve() != Path(state_path).resolve():
        raise ValueError('meaning-vector plan uses a different native state')
    protected = dict(plan['protected_sha256'])
    for path in (plan_path, request_path, directory / 'worker-result/worker-receipt.json',
                 directory / 'worker-result/raw-vectors.f32le'):
        protected[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path, expected in protected.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('meaning-vector source changed: ' + path)
    vectors, receipt = vector_reader.load_vectors(directory / 'worker-result', compact=True)
    if (receipt['proposal_sha256'] != protected[str(plan_path)]
            or receipt['request_sha256'] != protected[str(request_path)]):
        raise ValueError('meaning vectors differ from their saved plan or request')
    for field in ('checkpoint_sha256', 'base_model_artifact_tree_sha256', 'model', 'dimensions'):
        if receipt[field] != subject_receipt[field]:
            raise ValueError('meaning-vector SSE identity differs: ' + field)
    request = json.loads(request_path.read_bytes())
    if request['proposal_sha256'] != receipt['proposal_sha256']:
        raise ValueError('meaning-vector request proposal differs')
    notes = {note['note_id']: note for note in request['notes']}
    pairs = {pair['id']: pair for pair in plan['pairs']}
    result = {}
    for node in siblings:
        pair = pairs[plan['references']['node:' + node['id']]]
        if any(pair[field] != node[field] for field in ('subject', 'meaning')):
            raise ValueError('saved sibling heading or meaning differs: ' + node['id'])
        text = node['meaning']
        digest = hashlib.sha256(text.encode()).hexdigest()
        subject_id = hashlib.sha256((digest + f':0:{len(text.encode())}').encode()).hexdigest()[:16]
        key = (digest, subject_id)
        note = notes.get(digest)
        if (tuple(pair['representations']['meaning']) != key or note is None
                or note['text'] != text or dict(subject_id=subject_id,
                    byte_spans=[[0, len(text.encode())]]) not in note['subjects']):
            raise ValueError('sibling encoding is not its standalone full meaning: ' + node['id'])
        result[node['id']] = vectors[key]
    return result, protected


def prepare(reference_project, state_path, menu_path, parent, output, *, method='second-best',
            sibling_meanings=None, clustering='nearest', candidate_scope='subject'):
    """Freeze a nomination against existing native state, menu and SSE receipts."""
    if __package__:
        from .candidate_ranking_study import _reference
    else:
        from candidate_ranking_study import _reference
    workflow, trial, _, _, subject_vectors, vector_reader = _reference(reference_project)
    state_path, menu_path, output = (Path(path).resolve() for path in
                                      (state_path, menu_path, output))
    if output.exists():
        raise FileExistsError(output)
    if method not in ('second-best', 'subgroups'):
        raise ValueError('unknown shaping selection method')
    if sibling_meanings is not None and method != 'subgroups':
        raise ValueError('sibling meanings require the subgroup method')
    if clustering not in ('nearest', 'complete') or (clustering != 'nearest' and method != 'subgroups'):
        raise ValueError('complete-link clustering requires the subgroup method')
    if candidate_scope not in ('subject', 'local-ancestors') or (
            candidate_scope != 'subject' and method != 'subgroups'):
        raise ValueError('local ancestor candidates require the subgroup method')
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
    local_entries = [dict(note_id=note_id, **row) for note_id, note in corpus.items()
                     for row in note['subjects']]
    rows = [row for row in local_entries if (row['note_id'], row['number']) not in processed]
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
    sibling_vectors = None
    if sibling_meanings is not None:
        sibling_vectors, meaning_sources = load_sibling_meanings(
            sibling_meanings, state_path, siblings, receipt, vector_reader)
        for path, expected in meaning_sources.items():
            if path in protected and protected[path] != expected:
                raise ValueError('conflicting meaning-vector source: ' + path)
            protected[path] = expected
    score_rows = local_entries if candidate_scope == 'local-ancestors' else rows
    texts = {row['subject'] for row in (score_rows if sibling_vectors is not None else [*score_rows, *siblings])}
    vectors = {}
    for text in texts:
        digest = hashlib.sha256(text.encode()).hexdigest()
        vectors[text] = saved[(digest, digest[:16])]
    ranked = rank_candidates(rows, siblings, vectors, eligible=eligible) if method == 'second-best' else []
    groups = rank_subgroups(rows, siblings, vectors, eligible=eligible,
                           sibling_vectors=sibling_vectors,
                           clustering=clustering,
                           local_entries=local_entries if candidate_scope == 'local-ancestors' else None
                           ) if method == 'subgroups' else None
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
    if sibling_vectors is not None:
        report.update(sibling_meanings={node['id']: node['meaning'] for node in siblings},
            sibling_representation='standalone full explicit meaning', local_representation='standalone subject',
            method='nearest sibling meaning groups; weakest member minus strongest outside meaning cosine',
            meaning_vectors=str(Path(sibling_meanings).resolve()))
    if clustering == 'complete':
        import scipy
        representation = 'meaning' if sibling_vectors is not None else 'subject'
        report.update(clustering='complete',
            clustering_runtime=dict(numpy=np.__version__, scipy=scipy.__version__),
            method=f'complete-link sibling {representation} groups; weakest member minus strongest outside {representation} cosine')
    if candidate_scope == 'local-ancestors':
        report.update(candidate_scope=candidate_scope, original_local_entries=len(local_entries),
            method=report['method'] + '; candidate affinity through original proper local descendants',
            interpretation='Unused original local ancestors nominated through descendant resemblance; canonical containment remains untested.')
        by_key = {(entry['note_id'], entry['number']): entry for entry in local_entries}
        parent_keys = {(entry['note_id'], '.'.join(entry['number'].split('.')[:depth]))
                       for entry in local_entries for depth in range(1, len(entry['number'].split('.')))}
        report['unused_local_parents'] = len(parent_keys - processed)
        report['original_exact_matches'] = {}
        for sibling in siblings:
            matches = []
            for entry in local_entries:
                if entry['subject'].casefold() != sibling['subject'].casefold():
                    continue
                key = (entry['note_id'], entry['number'])
                parts = entry['number'].split('.')
                ancestors = []
                for depth in range(1, len(parts)):
                    ancestor_key = (key[0], '.'.join(parts[:depth]))
                    ancestors.append(dict(by_key[ancestor_key], processed=ancestor_key in processed))
                matches.append(dict(entry, processed=key in processed, ancestors=ancestors))
            report['original_exact_matches'][sibling['id']] = matches
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
    parser.add_argument('--sibling-meanings', type=Path,
                        help='saved auxiliary SSE directory; use full meanings for subgroup siblings')
    parser.add_argument('--clustering', choices=('nearest', 'complete'), default='nearest',
                        help='subgroup algorithm; complete uses SciPy complete-link cosine distances')
    parser.add_argument('--candidate-scope', choices=('subject', 'local-ancestors'), default='subject',
                        help='score unused local headings or their original proper descendants')
    args = parser.parse_args()
    print(json.dumps(prepare(args.reference_project, args.state, args.menu, args.parent, args.output,
                             method=args.method, sibling_meanings=args.sibling_meanings,
                             clustering=args.clustering, candidate_scope=args.candidate_scope)))


if __name__ == '__main__':
    main()
