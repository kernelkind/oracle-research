"""Compare lexical phrase relations with and without grammatical structure.

Edges are ambiguous proposals, not approved entailments. Original occurrences
and direct support remain separate from transitive graph reachability.
"""

import argparse
from collections import defaultdict, deque
from functools import lru_cache
import json
from pathlib import Path
import resource
import time

from mask_group_lexical_relations import ancestor_paths, digest, load_wordnet


class PhraseMatcher:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.paths = {s: ancestor_paths(s, lexicon['senses'])
                      for s, entry in lexicon['senses'].items() if entry['pos'] == 'n'}

    @lru_cache(maxsize=None)
    def relations(self, parent, parent_pos, child, child_pos, lexical):
        if parent_pos != child_pos:
            return None
        if parent == child:
            return ()
        if not lexical or parent_pos != 'NOUN':
            return None
        result = []
        for p in self.lexicon['queries'].get(parent, []):
            for c in self.lexicon['queries'].get(child, []):
                if p not in self.paths or c not in self.paths:
                    continue
                if p == c:
                    result.append(dict(parent_sense=p, child_sense=c, path=[c], kind='synonym'))
                elif p in self.paths[c]:
                    result.append(dict(parent_sense=p, child_sense=c,
                                       path=self.paths[c][p], kind='hypernym'))
        return tuple(sorted(result, key=lambda r: (r['parent_sense'], r['child_sense']))) or None

    def match(self, parent_key, child_key, structure=True, lexical=True):
        pr, pw = parent_key
        cr, cw = child_key
        if len(pw) > len(cw):
            return None
        candidates = {}
        for i, p in enumerate(pw):
            matches = [j for j, c in enumerate(cw)
                       if self.relations(p[0], p[1], c[0], c[1], lexical) is not None
                       and (not structure or (i == pr) == (j == cr))]
            if not matches:
                return None
            candidates[i] = matches
        if structure:
            visited, todo = [], deque([pr])
            while todo:
                i = todo.popleft()
                if i in visited:
                    raise ValueError('cyclic phrase structure')
                visited.append(i)
                todo.extend(j for j, w in enumerate(pw) if w[2] == i)
            if len(visited) != len(pw):
                raise ValueError('disconnected phrase structure')
        order = list(range(len(pw)))
        mapping, used = {}, set()

        def assign(k):
            if k == len(order):
                return True
            i = order[k]
            for j in candidates[i]:
                if j in used:
                    continue
                if structure:
                    if i != pr and (cw[j][3] != pw[i][3] or
                                    (pw[i][2] in mapping and cw[j][2] != mapping[pw[i][2]])):
                        continue
                    if any(pw[a][2] == i and cw[b][2] != j for a, b in mapping.items()):
                        continue
                mapping[i] = j
                used.add(j)
                if assign(k + 1):
                    return True
                used.remove(j)
                del mapping[i]
            return False

        if not assign(0):
            return None
        witnesses = []
        for i, j in sorted(mapping.items()):
            p, c = pw[i], cw[j]
            relations = self.relations(p[0], p[1], c[0], c[1], lexical)
            if relations:
                witnesses.append(dict(parent_index=i, child_index=j, relations=list(relations)))
        return dict(mapping=[[i, j] for i, j in sorted(mapping.items())], lexical_witnesses=witnesses)


def relation_edges(nodes, matcher, structure, lexical):
    edges = []
    # Necessary word coverage prunes comparisons without changing either rule.
    index = defaultdict(set)
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('distinct phrase IDs required')
    for n in nodes:
        for w in n['key'][1]:
            index[w[0], w[1]].add(n['id'])
    compatible = {}
    for token in index:
        compatible[token] = set().union(*(ids for other, ids in index.items()
            if matcher.relations(*token, *other, lexical) is not None))
    for p in sorted(nodes, key=lambda n: n['id']):
        possible = set.intersection(*(compatible[w[0], w[1]] for w in p['key'][1]))
        for cid in sorted(possible - {p['id']}):
            matched = matcher.match(p['key'], by_id[cid]['key'], structure, lexical)
            if matched is not None:
                edges.append(dict(parent=p['id'], child=cid, **matched))
    return edges


def reachable_paths(start, children):
    paths, todo = {start: [start]}, deque([start])
    while todo:
        current = todo.popleft()
        for child in sorted(children.get(current, [])):
            if child not in paths:
                paths[child] = paths[current] + [child]
                todo.append(child)
    del paths[start]
    return paths


def membership_summary(nodes, edges):
    by_id = {n['id']: n for n in nodes}
    children = defaultdict(set)
    for e in edges:
        children[e['parent']].add(e['child'])
    summaries, reciprocal = [], []
    for n in nodes:
        i = n['id']
        direct = children[i]
        reachable = set(reachable_paths(i, children))
        direct_rows = set(n['rows']).union(*(by_id[c]['rows'] for c in direct))
        direct_notes = set(n['notes']).union(*(by_id[c]['notes'] for c in direct))
        graph_rows = set(n['rows']).union(*(by_id[c]['rows'] for c in reachable))
        graph_notes = set(n['notes']).union(*(by_id[c]['notes'] for c in reachable))
        summaries.append(dict(id=i, direct_children=sorted(direct), reachable=sorted(reachable),
                              direct_rows=sorted(direct_rows), direct_notes=sorted(direct_notes),
                              graph_only_rows=sorted(graph_rows - direct_rows),
                              graph_only_notes=sorted(graph_notes - direct_notes),
                              reachable_notes=sorted(graph_notes)))
        reciprocal.extend([i, c] for c in direct if i < c and i in children[c])
    # Strongly connected components via mutual reachability; preserve, don't repair.
    reach = {s['id']: set(s['reachable']) for s in summaries}
    unseen, cycles = set(by_id), []
    while unseen:
        i = min(unseen)
        component = {i} | {j for j in reach[i] if i in reach[j]}
        unseen -= component
        if len(component) > 1:
            cycles.append(sorted(component))
    return dict(nodes=summaries, reciprocal_pairs=reciprocal, cyclic_components=cycles)


def run(source, lexicon):
    matcher = PhraseMatcher(lexicon)
    conditions = []
    for structure, lexical in [(False, False), (True, False), (False, True), (True, True)]:
        name = ('structure' if structure else 'words') + ('_lexical' if lexical else '_literal')
        edges = relation_edges(source['nodes'], matcher, structure, lexical)
        conditions.append(dict(id=name, structure=structure, lexical=lexical,
                               edges=edges, memberships=membership_summary(source['nodes'], edges)))
    return dict(run_id='SPC02', source_nodes=source['nodes'], source_edges=source['edges'],
                conditions=conditions,
                interpretation='Ambiguous relation proposals. Graph reachability is not semantic support. '
                               'Direct matching also retains unresolved source senses. No hierarchy adopted.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path)
    q = p.add_mutually_exclusive_group(required=True)
    q.add_argument('--wordnet-root', type=Path)
    q.add_argument('--lexicon', type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error('output exists; preserve previous results')
    started = time.monotonic()
    source = json.loads(args.input.read_text())
    lexicon = (json.loads(args.lexicon.read_text()) if args.lexicon else
               load_wordnet({w[0] for n in source['nodes'] for w in n['key'][1]
                             if w[1] == 'NOUN'}, args.wordnet_root))
    result = run(source, lexicon)
    config = dict(run_id='SPC02', input_sha256=digest(args.input), code_sha256=digest(Path(__file__)),
                  lexical_code_sha256=digest(Path(__file__).with_name('mask_group_lexical_relations.py')),
                  elapsed_seconds=time.monotonic() - started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  conditions=[dict(id=c['id'], edges=len(c['edges']),
                                   cycles=len(c['memberships']['cyclic_components'])) for c in result['conditions']])
    args.output.mkdir(parents=True)
    for name, data in [('result.json', result), ('lexicon.json', lexicon), ('config.json', config)]:
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')) + '\n')
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(config))


if __name__ == '__main__':
    main()
