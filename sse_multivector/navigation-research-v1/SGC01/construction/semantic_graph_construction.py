"""Construct and preserve semantic graph patterns from saved native parser output."""

import argparse
import json
from pathlib import Path
import time

from geometric_experiment import overlay
from semantic_graph_patterns import construct
from semantic_graph_probe import decode_output, digest, normalize_senses, save


def replay_native(records, native):
    by_row = {r['row']: r for r in records}
    if len(by_row) != len(records) or len({r['row'] for r in native}) != len(native):
        raise ValueError('source and native rows must be unique')
    if {r['row'] for r in native if r['row'] >= 0} != set(by_row):
        raise ValueError('native outputs must cover the frozen selected records')
    decoded, selected, graphs = [], [], []
    for raw in native:
        result = decode_output({k: v for k, v in raw.items() if k not in {'graph', 'error'}})
        decoded.append(result)
        if raw['row'] < 0:
            continue
        source = by_row[raw['row']]
        if raw['subject'] != source['subject'] or raw['note'] != source['note']:
            raise ValueError('native output has changed its source description or note')
        if result['graph']:
            selected.append(source)
            graphs.append(result['graph'])
    return decoded, selected, graphs


def canonicalize_graphs(graphs, lexicon):
    normalized = json.loads(json.dumps(graphs))
    for graph in normalized:
        for node in graph['nodes']:
            native = node['sense']
            canonical = lexicon['canonical_senses'][native]
            if canonical not in lexicon['senses']:
                raise ValueError('canonical sense is missing from saved lexicon')
            node['native_sense'], node['sense'] = native, canonical
    return normalized


def source_record(records, decoded, graphs, lexicon, evidence):
    aliases = {a['short_id']: a for row in evidence for a in row['aliases']}
    outputs, parsed = {r['row']: r for r in decoded}, {g['row']: g for g in graphs}
    lines = ['# SGC01 complete source evidence', '',
             'Each section retains the original note and original mask, the unchanged',
             'description supplied to the parser, and its exact output. Numbered senses',
             'are predictions, not accepted meanings. A syntax check is not a semantic judgment.', '']
    for record in records:
        row = record['row']
        alias = aliases[record['alias_ids'][0]]
        if (alias['text'] != record['text'] or alias['fragments'] != record['fragments']
                or alias['note_short_id'] != record['note']):
            raise ValueError('source overlay does not match frozen evidence')
        marked = overlay(record['text'], alias['byte_spans'])
        lines += [f"## Row {row} · {record['note']} · {' '.join(record['alias_ids'])}", '',
                  '\n'.join('> ' + line for line in marked.splitlines()), '',
                  f"Parser input: {record['subject']}", '',
                  'Exact native output:', '', '```text', outputs[row]['output'], '```', '',
                  'Syntax check: ' + (outputs[row]['error'] or 'passed local sequence/reference checks'), '']
        if row in parsed:
            graph = parsed[row]
            lines += ['Predicted concepts:', '', '| Node | Native sense | Dictionary meaning |',
                      '|---|---|---|']
            for node in graph['nodes']:
                definition = lexicon['senses'][node['sense']]['definition'] or 'No such sense in cached WordNet 3.0'
                lines.append(f"| {node['id']} | `{node['native_sense']}` | {definition.replace('|', '/')} |")
            lines += ['', 'Predicted relationships (IDs refer only to this row):', '', '```text']
            lines += [f"{e['source']} — {e['role']} → {e['target']}" for e in graph['edges']]
            lines += ['```', '']
    return '\n'.join(lines) + '\n'


def inventory(result):
    lines = ['# SGC01 recurring patterns', '',
             'All patterns remain in result.json. This report lists the most-specific',
             'patterns available for each recurring note set. Different meanings are',
             'not merged merely because their notes coincide. Arrows below are native',
             'semantic relationships, not navigation edges or accepted category labels.', '']
    for condition in result['conditions']:
        by_id = {p['id']: p for p in condition['patterns']}
        lines += [f"## {condition['id']}", '',
                  f"{len(by_id)} patterns; {len(condition['edges'])} construction links; "
                  f"{len(condition['recurring_groups'])} recurring note sets.", '']
        for group in condition['recurring_groups']:
            lines += [f"### {' '.join(group['notes'])}", '']
            for identifier in group['most_specific_pattern_ids']:
                p = by_id[identifier]
                lines += [f"- `{identifier}`: {' — '.join(p['key'])}; rows "
                          + ', '.join(map(str, p['rows']))]
            lines += ['']
    return '\n'.join(lines) + '\n'


def run(args):
    if args.output.exists():
        raise ValueError('output exists; preserve previous construction')
    started = time.monotonic()
    records = json.loads((args.native / 'inputs.json').read_bytes())
    native = [json.loads(line) for line in (args.native / 'native.jsonl').read_text().splitlines()]
    decoded, selected, graphs = replay_native(records, native)
    if args.lexicon:
        lexicon = json.loads(args.lexicon.read_bytes())
        graphs = canonicalize_graphs(graphs, lexicon)
    else:
        graphs, lexicon = normalize_senses(graphs, args.wordnet_root)
    result = construct(selected, graphs, lexicon['senses'])
    result['run_id'] = 'SGC01'
    result['excluded_rows'] = [r['row'] for r in decoded if r['row'] >= 0 and r['error']]
    args.output.mkdir(parents=True)
    for filename, data in [('decoded.json', decoded), ('inputs.json', records),
                           ('graphs.json', graphs), ('lexicon.json', lexicon), ('result.json', result)]:
        save(args.output / filename, data)
    for name in ['semantic_graph_probe.py', 'semantic_graph_patterns.py', Path(__file__).name]:
        source = Path(__file__).parent / name
        (args.output / name).write_bytes(source.read_bytes())
    (args.output / 'INVENTORY.md').write_text(inventory(result))
    (args.output / 'SOURCE-EVIDENCE.md').write_text(source_record(
        records, decoded, graphs, lexicon, json.loads(args.evidence.read_bytes())))
    save(args.output / 'config.json', dict(
        run_id='SGC01', native_sha256=digest(args.native / 'native.jsonl'),
        inputs_sha256=digest(args.native / 'inputs.json'), evidence_sha256=digest(args.evidence),
        elapsed_seconds=time.monotonic() - started, source_hashes={name: digest(args.output / name)
        for name in ['semantic_graph_probe.py', 'semantic_graph_patterns.py', Path(__file__).name]}))
    print(json.dumps({'excluded_rows': result['excluded_rows'], 'conditions': [
        dict(id=c['id'], patterns=len(c['patterns']), links=len(c['edges']),
             recurring_note_sets=len(c['recurring_groups'])) for c in result['conditions']]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--wordnet-root', type=Path)
    source.add_argument('--lexicon', type=Path)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
