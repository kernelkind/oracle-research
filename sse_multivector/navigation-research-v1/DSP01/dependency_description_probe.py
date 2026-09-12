"""Inspect grammatical paths in frozen descriptions without assigning categories."""

import argparse
import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import resource
import time


PROCESSORS = dict(tokenize='ewt', mwt='ewt', pos='ewt_nocharlm',
                  lemma='ewt_nocharlm', depparse='ewt_nocharlm')
REVISION = '3485d1dd01841c4cace1834d8078395a6f5e4520'
RESOURCES_REVISION = '9e22b9943b68a0c83bf9187131992825c1a3c829'


def dependency_paths(sentences):
    result = []
    for number, words in enumerate(sentences):
        ids = [w['id'] for w in words]
        if (not words or ids != list(range(1, len(words) + 1))
                or sum(w['head'] == 0 for w in words) != 1
                or any(w['head'] not in [0] + ids or not w.get('lemma')
                       or not w.get('upos') or not w.get('deprel') for w in words)):
            raise ValueError('a labeled, connected dependency tree is required')
        by_id = {w['id']: w for w in words}
        chains = {}
        for i in ids:
            chain = []
            while i:
                if i in chain:
                    raise ValueError('dependency cycle')
                chain.append(i)
                i = by_id[i]['head']
            chains[chain[0]] = chain
        for left, right in itertools.combinations(ids, 2):
            a, b = chains[left], chains[right]
            common = next(i for i in a if i in b)
            path = a[:a.index(common) + 1] + b[:b.index(common)][::-1]
            edges = []
            for first, second in zip(path, path[1:]):
                if by_id[first]['head'] == second:
                    edges.append(['up', by_id[first]['deprel']])
                else:
                    edges.append(['down', by_id[second]['deprel']])
            result.append(dict(
                sentence=number, word_ids=path,
                nodes=[[by_id[i]['lemma'].casefold(), by_id[i]['upos']] for i in path],
                edges=edges,
                case_dependents=[[[w['lemma'].casefold(), w['upos']] for w in words
                                  if w['head'] == i and w['deprel'] == 'case']
                                 for i in path]))
    return result


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def parse_descriptions(subjects, cache, offline):
    import stanza
    import torch

    if stanza.__version__ != '1.11.0':
        raise ValueError('this diagnostic requires Stanza 1.11.0')
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    if not offline:
        stanza.download(
            'en', model_dir=str(cache), package=None, processors=PROCESSORS,
            resources_version='1.11.0',
            resources_url='https://raw.githubusercontent.com/stanfordnlp/stanza-resources/'
                          + RESOURCES_REVISION,
            model_url='https://huggingface.co/stanfordnlp/stanza-en/resolve/'
                      + REVISION + '/models/{filename}',
            verbose=False)
    started = time.monotonic()
    pipeline = stanza.Pipeline(
        'en', dir=str(cache), package=None, processors=PROCESSORS,
        download_method=stanza.DownloadMethod.NONE, use_gpu=False,
        depparse_batch_size=128, pos_batch_size=128, verbose=False)
    load_seconds = time.monotonic() - started

    def parse(text):
        doc = pipeline(text)
        sentences = [[{name: getattr(w, name) for name in (
            'id', 'text', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel',
            'start_char', 'end_char')} for w in sentence.words]
                     for sentence in doc.sentences]
        return dict(subject=text, sentences=sentences, paths=dependency_paths(sentences))

    native = parse('The cat chased the dogs.')
    native_edges = {(w['lemma'], w['deprel'],
                     sentence[w['head'] - 1]['lemma'] if w['head'] else None)
                    for sentence in native['sentences'] for w in sentence}
    if not {('cat', 'nsubj', 'chase'), ('dog', 'obj', 'chase')} <= native_edges:
        raise ValueError('native subject/object smoke check failed')
    started = time.monotonic()
    parses = [parse(text) for text in subjects]
    metadata = dict(
        model_revision=REVISION, resources_revision=RESOURCES_REVISION,
        processors=PROCESSORS, native=native, device='cpu', threads=2,
        model_files={str(p.relative_to(cache)): digest(p)
                     for p in sorted(cache.rglob('*')) if p.is_file()},
        load_seconds=load_seconds, inference_seconds=time.monotonic() - started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        packages={p: importlib.metadata.version(p) for p in
                  ['stanza', 'torch', 'numpy', 'emoji', 'protobuf']})
    return parses, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--rows', type=int, nargs='+', required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('use a new output directory')
    source = json.loads(args.input.read_text())['inputs']
    if len(set(args.rows)) != len(args.rows) or any(i < 0 or i >= len(source) for i in args.rows):
        raise ValueError('distinct in-range source rows required')
    selected = [source[i] for i in args.rows]
    if any(r['row'] != i or not isinstance(r['subject'], str)
           or not r['subject'].strip() for r, i in zip(selected, args.rows)):
        raise ValueError('ordered source with nonempty subject strings required')
    parses, metadata = parse_descriptions([r['subject'] for r in selected], args.cache, args.offline)
    for record, parse in zip(selected, parses):
        parse['row'] = record['row']
    args.output.mkdir(parents=True)
    for name, data in [('inputs.json', selected), ('parses.json', parses),
                       ('config.json', dict(metadata, input_sha256=digest(args.input),
                                            code_sha256=digest(__file__), rows=args.rows))]:
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    print(json.dumps(dict(descriptions=len(selected), **{k: metadata[k] for k in
                     ['inference_seconds', 'peak_rss_kib']})))


if __name__ == '__main__':
    main()
