"""Parse fixed source descriptions into native PMB graphs for construction research."""

import argparse
from collections import deque
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shlex
import time


CONCEPT = re.compile(r'[^\s"]+\.[nvars]\.\d{2}$')
INDEX = re.compile(r'[+-]\d+$')
CONNECTOR = re.compile(r'[<>]\d+$')
ROLE = re.compile(r'[A-Z][A-Za-z-]*$')
# These names end in Of but are ordinary PMB relations, not inverted roles.
BASE_OF = {'Of', 'InstanceOf', 'SubOf', 'PartOf', 'MadeOf', 'FeatureOf',
           'ContentOf', 'YearOfCentury', 'DayOfWeek', 'MonthOfYear',
           'DayOfMonth'}


def parse_sbn(text):
    """Read sequence notation without guessing omitted senses or references.

    Concepts alone advance relative concept indices; context separators advance
    context indices. Constants and comparison operators remain in the native
    graph, but are not invented as WordNet concept nodes.
    """
    tokens = shlex.split(text, posix=False)
    nodes, edges, anchors = [], [], []
    contexts = [{'id': 0, 'relation': None, 'target': None}]
    owner = None
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if CONCEPT.fullmatch(token):
            owner = len(nodes)
            nodes.append(dict(id=owner, sense=token, context=len(contexts) - 1))
            i += 1
            continue
        if i + 1 == len(tokens):
            raise ValueError(f'incomplete relation or context at token {i}: {token}')
        value = tokens[i + 1]
        if token.isupper() and CONNECTOR.fullmatch(value):
            current = len(contexts)
            target = current + (-1 if value[0] == '<' else 1) * int(value[1:])
            contexts.append(dict(id=current, relation=token, target=target))
            owner = None
        elif owner is not None and ROLE.fullmatch(token):
            if INDEX.fullmatch(value):
                target = owner + int(value)
                source, role = owner, token
                if role.endswith('Of') and role not in BASE_OF:
                    source, target, role = target, source, role[:-2]
                edges.append(dict(source=source, role=role, target=target))
            else:
                if CONCEPT.fullmatch(value) or ROLE.fullmatch(value):
                    raise ValueError(f'missing reference/constant after {token}')
                anchors.append(dict(source=owner, role=token, value=value))
        else:
            raise ValueError(f'unrecognized native sequence token {i}: {token}')
        i += 2
    if not nodes:
        raise ValueError('no concept in native sequence')
    for edge in edges:
        if not (0 <= edge['source'] < len(nodes) and 0 <= edge['target'] < len(nodes)):
            raise ValueError(f'concept reference outside native sequence: {edge}')
    for context in contexts[1:]:
        if not 0 <= context['target'] < len(contexts):
            raise ValueError(f'context reference outside native sequence: {context}')
    return dict(nodes=nodes, edges=edges, anchors=anchors, contexts=contexts)


def select_inputs(records, rows):
    by_row = {r['row']: r for r in records}
    if len(by_row) != len(records) or len(set(rows)) != len(rows):
        raise ValueError('distinct source and selected rows required')
    if not set(rows) <= set(by_row):
        raise ValueError('selected row absent from frozen inputs')
    selected = [by_row[row] for row in sorted(rows)]
    if any(not r['subject'] or not r['note'] for r in selected):
        raise ValueError('complete descriptions and source note IDs required')
    return selected


def decode_output(record):
    try:
        if not record['ended_with_eos']:
            raise ValueError('generation did not reach EOS; incomplete output')
        graph = dict(row=record['row'], **parse_sbn(record['output']))
        return dict(**record, graph=graph, error=None)
    except ValueError as error:
        return dict(**record, graph=None, error=str(error))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def normalize_senses(graphs, root):
    """Canonicalize a predicted numbered sense, never choose a different sense."""
    import nltk.data
    from nltk.corpus.reader.wordnet import WordNetCorpusReader, WordNetError
    from nltk.data import ZipFilePathPointer
    archive = root / 'corpora' / 'wordnet.zip'
    nltk.data.path[:] = [str(root)]
    reader = WordNetCorpusReader(ZipFilePathPointer(str(archive), 'wordnet/'), None)
    graphs = json.loads(json.dumps(graphs))
    entries, pending, unknown = {}, deque(), set()
    for graph in graphs:
        for node in graph['nodes']:
            native = node['sense']
            try:
                synset = reader.synset(native)
                node['sense'] = synset.name()
                pending.append(synset)
            except WordNetError:
                unknown.add(native)
            node['native_sense'] = native
    while pending:
        synset = pending.popleft()
        name = synset.name()
        if name in entries:
            continue
        parents = synset.hypernyms() + synset.instance_hypernyms()
        entries[name] = dict(definition=synset.definition(), lemmas=synset.lemma_names(),
                             hypernyms=sorted({p.name() for p in parents}), known=True)
        pending.extend(parents)
    for name in unknown:
        entries[name] = dict(definition=None, lemmas=[], hypernyms=[], known=False)
    for name in sorted(entries):
        paths, todo = {name: [name]}, deque([name])
        while todo:
            current = todo.popleft()
            for parent in entries[current]['hypernyms']:
                if parent not in paths:
                    paths[parent] = paths[current] + [parent]
                    todo.append(parent)
        entries[name]['ancestors'] = sorted(paths)
        entries[name]['paths'] = dict(sorted(paths.items()))
    return graphs, dict(senses=dict(sorted(entries.items())), unknown=sorted(unknown),
                        source=dict(version=reader.get_version(), archive_sha256=digest(archive),
                                    nltk_version=importlib.metadata.version('nltk'),
                                    relations=['hypernyms', 'instance_hypernyms']))


def own_memory():
    return {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
            for line in Path('/proc/self/status').read_text().splitlines()
            if line.startswith(('VmRSS:', 'VmHWM:'))}


def run(args):
    if args.output.exists():
        raise ValueError('output already exists; preserve previous runs')
    records = select_inputs(json.loads(args.inputs.read_bytes()), args.rows)
    args.output.mkdir(parents=True)
    save(args.output / 'inputs.json', records)
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    config = dict(run_id='SGC01', inputs_sha256=digest(args.inputs), rows=args.rows,
                  model=args.model, revision=args.revision, cpu_threads=2,
                  max_new_tokens=2048, do_sample=False, num_beams=1,
                  input_truncation=False, versions={p: importlib.metadata.version(p)
                      for p in ['transformers', 'torch', 'huggingface-hub']})
    save(args.output / 'config.json', config)
    import torch
    from transformers import AutoTokenizer, T5ForConditionalGeneration
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    started = time.monotonic()
    print('Loading pinned ByT5 checkpoint on CPU.', flush=True)
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.revision,
                                              cache_dir=str(args.cache))
    model = T5ForConditionalGeneration.from_pretrained(
        args.model, revision=args.revision, cache_dir=str(args.cache),
        torch_dtype=torch.float32, low_cpu_mem_usage=True, weights_only=True).eval()
    config['parameter_count'] = sum(p.numel() for p in model.parameters())
    config['model_config'] = model.config.to_dict()
    config['generation_config'] = model.generation_config.to_dict()
    save(args.output / 'config.json', config)
    outputs = []
    control = dict(row=-1, subject='I am a student.', note=None)
    with (args.output / 'native.jsonl').open('x') as stream:
        for record in [control] + records:
            encoded = tokenizer(record['subject'], return_tensors='pt', truncation=False)
            if encoded['input_ids'].shape[1] > 512:
                raise ValueError('native input exceeds fixed 512-token envelope; not truncated')
            began = time.monotonic()
            with torch.inference_mode():
                ids = model.generate(**encoded, max_new_tokens=2048, do_sample=False,
                                     num_beams=1)[0].tolist()
            output = dict(row=record['row'], subject=record['subject'], note=record['note'],
                          output=tokenizer.decode(ids, skip_special_tokens=True,
                                                  clean_up_tokenization_spaces=False),
                          input_token_ids=encoded['input_ids'][0].tolist(), output_token_ids=ids,
                          ended_with_eos=bool(ids and ids[-1] == tokenizer.eos_token_id),
                          elapsed_seconds=time.monotonic() - began)
            decoded = decode_output(output)
            stream.write(json.dumps(decoded, ensure_ascii=False, sort_keys=True) + '\n')
            stream.flush()
            outputs.append(decoded)
            print(f"row {record['row']}: {len(ids)} output tokens; "
                  f"{output['elapsed_seconds']:.2f}s; {decoded['error'] or 'parsed'}", flush=True)
    config.update(elapsed_seconds=time.monotonic() - started, memory=own_memory())
    save(args.output / 'config.json', config)
    save(args.output / 'graphs.json', [r['graph'] for r in outputs if r['graph'] and r['row'] >= 0])
    save(args.output / 'excluded.json', [r for r in outputs if r['error']])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--rows', type=int, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--model', default='XiaoZhang98/byT5-DRS')
    parser.add_argument('--revision', default='d8ec0dea6b9ac786927a864bfe87bca0951b2ce7')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
