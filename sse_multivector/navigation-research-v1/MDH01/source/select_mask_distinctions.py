"""Experimental lexical evidence for redundant category transitions.

This is NOT a semantic equivalence test. It preserves every retained category's
notes, masks, and title, and abstains when its literal evidence is insufficient.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import re

from select_note_categories import memberships


def mask_words(fragments):
    """Keep every casefolded word, including function words and numbers.

    No stemming, stopword removal, semantic expansion, or invented phrases
    between fragments. Punctuation, symbols, word order, and repetition are not
    represented; the resulting limitation is recorded in the experiment.
    """
    return {word for fragment in fragments for word in re.findall(r'[^\W_]+', fragment.casefold())}


def describe_categories(categories, hierarchy, evidence):
    memberships(categories)
    native = {str(n['id']): n for n in hierarchy['nodes']}
    if len(native) != len(hierarchy['nodes']):
        raise ValueError('duplicate native node IDs')
    words = []
    for row, record in enumerate(evidence):
        if record['row'] != row or not record['aliases']:
            raise ValueError('evidence rows must be ordered and have aliases')
        aliases = [mask_words(a['fragments']) for a in record['aliases']]
        if any(a != aliases[0] for a in aliases):
            raise ValueError('canonical aliases have different lexical evidence')
        words.append(aliases[0])
    result = {}
    for node in categories['nodes']:
        i = node['node_id']
        if i not in native:
            raise ValueError('category has no native mask membership')
        rows = native[i]['members']
        if not rows or any(not isinstance(r, int) or r < 0 or r >= len(words) for r in rows):
            raise ValueError('invalid native evidence rows')
        common = set.intersection(*(words[r] for r in rows))
        result[i] = dict(common_words=sorted(common), rows=rows.copy(),
                         word_sets=[sorted(words[r]) for r in rows])
    return result


def select_distinctions(categories, descriptions):
    """Remove a child only if EACH mask equals its parent's common word set.

    A shared intersection alone is insufficient. Remaining children are promoted
    and tested against their new parent using the original, frozen evidence.
    """
    full = memberships(categories)
    if set(descriptions) != set(full):
        raise ValueError('every category needs its frozen evidence profile')
    for d in descriptions.values():
        if not d['word_sets'] or len(d['rows']) != len(d['word_sets']):
            raise ValueError('empty or inconsistent evidence profile')
        if set.intersection(*(set(w) for w in d['word_sets'])) != set(d['common_words']):
            raise ValueError('common words do not match mask evidence')
    result = deepcopy(categories)
    nodes = {n['node_id']: n for n in result['nodes']}
    trace, order = [], []

    def visit(parent):
        node = nodes[parent]
        common = descriptions[parent]['common_words']
        position = 0
        while position < len(node['children']):
            child = node['children'][position]
            if common and all(w == common for w in descriptions[child]['word_sets']):
                promoted = nodes[child]['children'].copy()
                node['children'][position:position + 1] = promoted
                trace.append(dict(parent=parent, removed=child, promoted=promoted,
                                  common_words=common.copy(),
                                  parent_notes=sorted(full[parent]), child_notes=sorted(full[child])))
                del nodes[child]
            else:
                position += 1
        node['note_ids'] = sorted(full[parent] - set().union(*(full[c] for c in node['children'])))
        order.append(parent)
        for child in node['children']:
            visit(child)

    visit(result['root_node_id'])
    result['nodes'] = [nodes[i] for i in order]
    if 'note_masks' in result:
        result['note_masks'] = {i: result['note_masks'][i] for i in order}
    if memberships(result) != {i: full[i] for i in order}:
        raise ValueError('retained category membership changed')
    return result, trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('categories', type=Path)
    parser.add_argument('--hierarchy', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    sources = {}
    loaded = {}
    for key in ('categories', 'hierarchy', 'evidence'):
        path = getattr(args, key)
        raw = path.read_bytes()
        sources[key] = dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest())
        loaded[key] = json.loads(raw)
    descriptions = describe_categories(**loaded)
    weak_edges = []
    for n in loaded['categories']['nodes']:
        for child in n['children']:
            common = descriptions[n['node_id']]['common_words']
            if common and common == descriptions[child]['common_words']:
                weak_edges.append(dict(parent=n['node_id'], child=child, common_words=common,
                                       child_extra_words=[sorted(set(w) - set(common))
                                                          for w in descriptions[child]['word_sets']]))
    selected, trace = select_distinctions(loaded['categories'], descriptions)
    selected['hierarchy_id'] += '-' + args.run_id
    selected_rows = sorted({r for edge in weak_edges for i in (edge['parent'], edge['child'])
                            for r in descriptions[i]['rows']})
    args.output.mkdir(parents=True)
    artifacts = {
        'categories.json': selected,
        'descriptions.json': descriptions,
        'diagnostic.json': dict(common_words_equal=weak_edges,
                               nonempty_descriptions=sum(bool(d['common_words']) for d in descriptions.values())),
        'review.json': [loaded['evidence'][r] for r in selected_rows],
        'selection.json': dict(run_id=args.run_id, sources=sources,
                               rule='every_child_mask_equals_parent_common_words',
                               features='casefolded_unicode_words_no_stopwords',
                               limitations=['literal words are not semantic descriptions',
                                            'punctuation, symbols, order, and repetition are not represented',
                                            'context outside masks is not represented',
                                            'empty common words imply abstention, not incoherence'],
                               code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                               count_before=len(loaded['categories']['nodes']),
                               count_after=len(selected['nodes']), removals=trace),
    }
    for filename, value in artifacts.items():
        with (args.output / filename).open('x') as file:
            json.dump(value, file, ensure_ascii=False, indent=2)
            file.write('\n')
    with (args.output / 'runner.py').open('x') as file:
        file.write(Path(__file__).read_text())
    print(json.dumps(dict(run_id=args.run_id, before=len(loaded['categories']['nodes']),
                          after=len(selected['nodes']), weak_edges=len(weak_edges),
                          removed=len(trace))))


if __name__ == '__main__':
    main()
