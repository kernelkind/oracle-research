"""Pinned SUMO resource preparation and three-condition SGC03 construction."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time
from urllib.request import urlopen

from semantic_graph_patterns import construct
from semantic_graph_probe import digest, save
from semantic_ontology_comparison import compare_condition, resource_names
from semantic_ontology_order import augment, parse_mappings, parse_ontology


SUMO_REVISION = 'abcb7cc1090c5b35cbfacd9e44e50e50c7434433'
SIGMA_REVISION = '9dba684eac829fd1e5d6740b8d28c5e208dc8204'
CONFIG_URL = ('https://raw.githubusercontent.com/ontologyportal/sigmakee/' + SIGMA_REVISION +
              '/docker/sigmakee2023/kbs/config.xml')
SUMO_URL = 'https://raw.githubusercontent.com/ontologyportal/sumo/' + SUMO_REVISION + '/'


def experiment(inputs, graphs, senses, mappings, ontology, baseline):
    """Change only the available ancestor order; retain all frozen source data."""
    rows = {g['row'] for g in graphs}
    records = [r for r in inputs if r['row'] in rows]
    original = construct(records, graphs, senses, relation_policy='connection')
    expected = {k: v for k, v in baseline.items() if k not in {'run_id', 'excluded_rows'}}
    if original != expected:
        raise ValueError('construction differs from frozen baseline')
    conditions = [{'id': 'wordnet', 'result': original}]
    for name, pos in [('nouns', ['n']), ('nouns_and_verbs', ['n', 'v'])]:
        augmented = augment(senses, mappings, ontology, pos)
        result = construct(records, graphs, augmented['senses'], relation_policy='connection')
        if result['conditions'][0] != original['conditions'][0]:
            raise ValueError('literal construction changed across ancestor orders')
        conditions.append({'id': name, 'augmentation': augmented, 'result': result})
    comparisons = []
    for a, b in [(0, 1), (0, 2), (1, 2)]:
        comparisons.append(dict(
            before=conditions[a]['id'], after=conditions[b]['id'],
            **compare_condition(conditions[a]['result']['conditions'][1],
                                conditions[b]['result']['conditions'][1],
                                allow_sumo_support_changes=a != 0)))
    return dict(run_id='SGC03', inputs=inputs, graphs=graphs,
                excluded_rows=baseline['excluded_rows'], conditions=conditions, comparisons=comparisons)


def fetch(cache):
    """Cache immutable public resources, validating upstream Git blob hashes."""
    cache.mkdir(parents=True, exist_ok=True)
    def download(name, url, blob=None):
        path = cache / name
        if path.exists():
            data = path.read_bytes()
        else:
            with urlopen(url, timeout=60) as response:
                data = response.read()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob and actual != blob:
            raise ValueError(f'upstream Git blob mismatch: {name}')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return dict(file=name, url=url, sha256=hashlib.sha256(data).hexdigest(),
                    git_blob_sha1=actual, size=len(data))
    tree_url = 'https://api.github.com/repos/ontologyportal/sumo/git/trees/' + SUMO_REVISION + '?recursive=1'
    tree_record = download('tree.json', tree_url)
    tree = json.loads((cache / 'tree.json').read_bytes())
    if tree.get('truncated') or tree['sha'] != SUMO_REVISION:
        raise ValueError('incomplete or unexpected upstream tree')
    blobs = {item['path']: item['sha'] for item in tree['tree'] if item['type'] == 'blob'}
    config = download('config.xml', CONFIG_URL)
    names = resource_names((cache / 'config.xml').read_text())
    names += ['README.txt', 'WordNetMappings/README.txt',
              'WordNetMappings/WordNetMappings30-noun.txt', 'WordNetMappings/WordNetMappings30-verb.txt']
    with ThreadPoolExecutor(max_workers=4) as pool:
        resources = list(pool.map(lambda name: download(name, SUMO_URL + name, blobs[name]), names))
    manifest = dict(sumo_revision=SUMO_REVISION, sigma_revision=SIGMA_REVISION,
                    resources=[config, tree_record] + sorted(resources, key=lambda r: r['file']))
    target = cache / 'manifest.json'
    if target.exists() and json.loads(target.read_bytes()) != manifest:
        raise ValueError('cache manifest differs; preserve previous resource record')
    save(target, manifest)
    print(json.dumps(dict(files=len(resources), bytes=sum(r['size'] for r in resources))))


def prepare(cache, lexicon, archive):
    manifest = json.loads((cache / 'manifest.json').read_bytes())
    if manifest['sumo_revision'] != SUMO_REVISION or manifest['sigma_revision'] != SIGMA_REVISION:
        raise ValueError('resource revision mismatch')
    for resource in manifest['resources']:
        if digest(cache / resource['file']) != resource['sha256']:
            raise ValueError('resource hash mismatch: ' + resource['file'])
    if digest(archive) != lexicon['source']['archive_sha256']:
        raise ValueError('frozen WordNet archive mismatch')
    from nltk.corpus.reader.wordnet import WordNetCorpusReader
    from nltk.data import ZipFilePathPointer
    reader = WordNetCorpusReader(ZipFilePathPointer(str(archive), 'wordnet/'), None)
    if reader.get_version() != lexicon['source']['version']:
        raise ValueError('WordNet version mismatch')
    names = resource_names((cache / 'config.xml').read_text())
    ontology = parse_ontology({name: (cache / name).read_text() for name in names})
    mapping_rows, mapping_stats = {}, {}
    for pos, name in [('n', 'noun'), ('v', 'verb')]:
        file = f'WordNetMappings/WordNetMappings30-{name}.txt'
        rows = parse_mappings((cache / file).read_text(), pos, file)
        mapping_rows.update(rows)
        mapping_stats[pos] = dict(rows=len(rows), malformed=[r for r in rows.values() if r.get('error')],
                                 multiple=sum(len(r['mappings']) > 1 for r in rows.values()))
    by_sense, lookup = {}, {}
    for sense, entry in sorted(lexicon['senses'].items()):
        if not entry['known']:
            lookup[sense] = dict(status='unknown_frozen_wordnet_sense')
            continue
        synset = reader.synset(sense)
        key = f'{synset.pos()}:{synset.offset():08d}'
        lookup[sense] = dict(key=key, status='matched' if key in mapping_rows else 'no_mapping_row')
        if key in mapping_rows:
            by_sense[sense] = mapping_rows[key]
    return ontology, by_sense, dict(manifest=manifest, mapping_statistics=mapping_stats, sense_lookup=lookup)


def run(args):
    if args.output.exists():
        raise ValueError('output already exists; preserve previous results')
    started = time.monotonic()
    baseline_path = args.sgc02 / 'result.json'
    paths = {name: args.sgc01 / name for name in ['inputs.json', 'graphs.json', 'lexicon.json']}
    inputs, graphs, lexicon = (json.loads(paths[name].read_bytes()) for name in paths)
    ontology, mappings, resource_record = prepare(args.cache, lexicon, args.wordnet)
    result = experiment(inputs, graphs, lexicon['senses'], mappings, ontology,
                        json.loads(baseline_path.read_bytes()))
    args.output.mkdir(parents=True)
    save(args.output / 'result.json', result)
    save(args.output / 'ontology.json', ontology)
    save(args.output / 'mappings.json', mappings)
    save(args.output / 'resources.json', resource_record)
    sources = ['semantic_ontology_experiment.py', 'semantic_ontology_comparison.py',
               'semantic_ontology_order.py', 'semantic_graph_patterns.py', 'semantic_graph_probe.py']
    for name in sources:
        (args.output / name).write_bytes((Path(__file__).parent / name).read_bytes())
    notices = ['# Upstream resource notices', '',
               'Exact headers from the pinned resources. The resource cache retains full files.', '']
    names = resource_names((args.cache / 'config.xml').read_text()) + [
        'WordNetMappings/WordNetMappings30-noun.txt', 'WordNetMappings/WordNetMappings30-verb.txt',
        'README.txt', 'WordNetMappings/README.txt']
    for name in names:
        content = (args.cache / name).read_text()
        header = content.split('\n(')[0] if name.endswith('.kif') else '\n'.join(content.splitlines()[:55])
        notices += ['## ' + name, '', '```text', header.strip(), '```', '']
    (args.output / 'RESOURCE-NOTICES.md').write_text('\n'.join(notices))
    save(args.output / 'config.json', dict(
        run_id='SGC03', frozen_sha256={str(p): digest(p) for p in [baseline_path, *paths.values()]},
        source_hashes={name: digest(args.output / name) for name in sources},
        cache=str(args.cache), no_new_inference=True, no_source_repairs=True,
        elapsed_seconds=time.monotonic() - started))
    print(json.dumps([dict(id=c['id'], patterns=len(c['result']['conditions'][1]['patterns']),
                           note_sets=len(c['result']['conditions'][1]['recurring_groups']))
                      for c in result['conditions']]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    download = commands.add_parser('fetch')
    download.add_argument('--cache', type=Path, required=True)
    construction = commands.add_parser('run')
    for name in ['cache', 'sgc01', 'sgc02', 'wordnet', 'output']:
        construction.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    fetch(args.cache) if args.command == 'fetch' else run(args)


if __name__ == '__main__':
    main()
