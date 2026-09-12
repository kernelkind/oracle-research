"""Construct source-backed phrase candidates and observed head-preserving paths."""

import argparse
from collections import defaultdict
import json
from pathlib import Path

from dependency_description_probe import dependency_paths, digest


UNIT = frozenset({'flat', 'fixed'})
CORE = UNIT | {'compound', 'amod', 'nummod'}
FULL = CORE | {'nmod'}


def phrase_stages(words, head):
    children = defaultdict(list)
    by_id = {w['id']: w for w in words}
    for word in words:
        children[word['head']].append(word['id'])

    def projection(allowed):
        selected = set()

        def visit(i, root=False):
            selected.add(i)
            for child in children[i]:
                rel = by_id[child]['deprel'].split(':')[0]
                if rel in allowed or (not root and rel in {'case', 'conj', 'cc', 'advmod'}):
                    visit(child)

        visit(head, root=True)
        return tuple(sorted(selected))

    # The equal stages retain their names in the occurrence, not duplicate nodes.
    return [(name, projection(allowed)) for name, allowed in
            [('head', UNIT), ('core', CORE), ('nominal_modifiers', FULL)]]


def phrase_key(words, selected, head):
    indices = {i: position for position, i in enumerate(selected)}
    by_id = {w['id']: w for w in words}
    return json.dumps([
        indices[head],
        [[by_id[i]['lemma'].casefold(), by_id[i]['upos'],
          indices.get(by_id[i]['head'], -1),
          'root' if i == head else by_id[i]['deprel']] for i in selected],
    ], ensure_ascii=False, separators=(',', ':'))


def source_fragments(text, words, selected):
    spans = []
    for i in selected:
        w = words[i - 1]
        start, end = w.get('start_char'), w.get('end_char')
        if start is None or end is None:
            return None
        if (not isinstance(start, int) or not isinstance(end, int)
                or not 0 <= start < end <= len(text) or text[start:end] != w['text']):
            raise ValueError('word offsets must reproduce their exact source text')
        if spans and start < spans[-1][1]:
            raise ValueError('overlapping expanded words cannot supply exact fragments')
        if spans and not text[spans[-1][1]:start].strip():
            spans[-1][1] = end
        else:
            spans.append([start, end])
    return spans, [text[a:b] for a, b in spans]


def construct(records, parses):
    sources = {r['row']: r for r in records}
    native = {p['row']: p for p in parses}
    if (len(sources) != len(records) or len(native) != len(parses)
            or set(sources) != set(native)):
        raise ValueError('distinct matching source and parse rows required')
    candidates, links, skipped = {}, defaultdict(list), []
    for row in sorted(sources):
        record, parsed = sources[row], native[row]
        text = record['subject']
        if not text or parsed['subject'] != text or not record['note']:
            raise ValueError('parse must preserve the complete source description')
        dependency_paths(parsed['sentences'])  # Validate the production tree contract.
        for sentence, words in enumerate(parsed['sentences']):
            for w in words:
                if w['upos'] not in {'NOUN', 'PROPN'}:
                    continue
                head = w['id']
                stages = defaultdict(list)
                for name, selected in phrase_stages(words, head):
                    stages[selected].append(name)
                produced = []
                for selected, names in stages.items():
                    aligned = source_fragments(text, words, selected)
                    if aligned is None:
                        skipped.append(dict(row=row, sentence=sentence, head=head,
                                            word_ids=list(selected), stages=names,
                                            reason='native word lacks exact source offsets'))
                        continue
                    spans, fragments = aligned
                    key = phrase_key(words, selected, head)
                    occurrence = dict(row=row, note=record['note'], sentence=sentence,
                                      head=head, word_ids=list(selected), stages=names,
                                      character_spans=spans, fragments=fragments)
                    if key not in candidates:
                        candidates[key] = dict(key=json.loads(key), head_lemma=w['lemma'].casefold(),
                                               occurrences=[])
                    candidates[key]['occurrences'].append(occurrence)
                    produced.append((key, selected))
                for (parent, pwords), (child, cwords) in zip(produced, produced[1:]):
                    if not set(pwords) < set(cwords):
                        raise ValueError('source phrase extensions must be strictly nested')
                    links[parent, child].append(dict(row=row, note=record['note'],
                                                     sentence=sentence, head=head,
                                                     parent_word_ids=list(pwords),
                                                     child_word_ids=list(cwords)))
    ids = {key: f'P{i:04d}' for i, key in enumerate(sorted(candidates))}
    nodes = []
    for key in sorted(candidates):
        node = candidates[key]
        forms = defaultdict(set)
        for occ in node['occurrences']:
            forms[' '.join(occ['fragments'])].add(occ['note'])
        forms = [dict(text=form, notes=sorted(notes)) for form, notes in sorted(forms.items())]
        label = min(forms, key=lambda f: (-len(f['notes']), f['text']))['text']
        nodes.append(dict(id=ids[key], label=label, **node, forms=forms,
                          notes=sorted({o['note'] for o in node['occurrences']}),
                          rows=sorted({o['row'] for o in node['occurrences']})))
    by_id = {n['id']: n for n in nodes}
    edges = []
    for (parent, child), witnesses in sorted(links.items()):
        p, c = ids[parent], ids[child]
        edges.append(dict(parent=p, child=c, witnesses=witnesses,
                          child_notes_outside_parent=sorted(set(by_id[c]['notes']) - set(by_id[p]['notes']))))
    result = dict(run_id='SPC01', source_rows=sorted(sources),
                  source_notes=sorted({r['note'] for r in records}),
                  nodes=nodes, edges=edges, skipped_projections=skipped)
    return result


def support_view(result, minimum_notes):
    if minimum_notes < 1:
        raise ValueError('positive minimum note count required')
    by_id = {n['id']: n for n in result['nodes']}
    retained = {n['id'] for n in result['nodes'] if len(n['notes']) >= minimum_notes}
    children = defaultdict(set)
    for edge in result['edges']:
        children[edge['parent']].add(edge['child'])
    edges = set()
    for parent in sorted(retained):
        todo = list(children[parent])
        seen = set()
        while todo:
            child = todo.pop()
            if child in seen:
                continue
            seen.add(child)
            if child in retained:
                edges.add((parent, child))
            else:
                todo.extend(children[child])
    edges = [dict(parent=p, child=c) for p, c in sorted(edges)]
    incoming = {e['child'] for e in edges}
    groups = defaultdict(list)
    for i in sorted(retained):
        groups[tuple(by_id[i]['notes'])].append(i)
    return dict(minimum_notes=minimum_notes, node_ids=sorted(retained), edges=edges,
                roots=sorted(retained - incoming),
                equal_note_edges=[e for e in edges if by_id[e['parent']]['notes'] == by_id[e['child']]['notes']],
                equal_note_groups=[ids for _, ids in sorted(groups.items()) if len(ids) > 1])


def inventory(result, views):
    lines = ['# SPC01 source phrase inventory', '',
             'Automatically produced expressions, not approved category titles.',
             'Counts refer to distinct original notes. All source occurrences are in result.json.', '']
    by_id = {n['id']: n for n in result['nodes']}
    for view in views:
        lines += [f"## At least {view['minimum_notes']} notes", '',
                  f"{len(view['node_ids'])} choices; {len(view['roots'])} roots; "
                  f"{len(view['edges'])} edges; {len(view['equal_note_edges'])} equal-note edges.", '',
                  '### Complete root menu', '']
        for i in sorted(view['roots'], key=lambda i: (by_id[i]['label'].casefold(), i)):
            n = by_id[i]
            lines.append(f"- {i}: {n['label']} — {len(n['notes'])} notes")
        lines += ['', '### All proposed edges', '']
        for e in view['edges']:
            p, c = by_id[e['parent']], by_id[e['child']]
            lines += [f"- {p['id']} {p['label']} → {c['id']} {c['label']} "
                      f"({len(p['notes'])} → {len(c['notes'])} notes); "
                      + ' '.join(c['notes'])]
        lines.append('')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--parses', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('use a new output directory')
    source = json.loads(args.input.read_text())
    records = source['inputs'] if isinstance(source, dict) else source
    parses = json.loads(args.parses.read_text())
    result = construct(records, parses)
    views = [support_view(result, n) for n in (2, 5)]
    args.output.mkdir(parents=True)
    for name, data in [('inputs.json', records), ('result.json', result), ('views.json', views),
                       ('config.json', dict(input_sha256=digest(args.input),
                                            parses_sha256=digest(args.parses),
                                            code_sha256=digest(__file__),
                                            validation_code_sha256=digest(Path(__file__).with_name('dependency_description_probe.py'))))]:
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (args.output / 'INVENTORY.md').write_text(inventory(result, views))
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(candidates=len(result['nodes']), edges=len(result['edges']),
                         views=[{k: len(v[k]) for k in ('node_ids', 'roots', 'edges')} for v in views])))


if __name__ == '__main__':
    main()
