"""Controlled LMMS occurrence matching; fixed descriptions, CPU, three candidate sets."""
import argparse
import gc
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import time
import zipfile

import numpy as np

PARTS = {'NOUN': 'n', 'PROPN': 'n', 'VERB': 'v', 'ADJ': 'a', 'ADV': 'r'}
MODEL_REVISION = '06fa25dc1b6e034e91607fd67c247051ccaeff65'
LMMS_REVISION = '65f5829a5c9d91a0c46db3633ddf3beb8a0af4e1'
MODEL_SHA = '137eefff71696316817af618eb19f72e277daab3225b56584848c5723a47cc59'
ZIP_MD5 = 'd0ea3c709d2e8e62c0ff92cb127a1dab'
WEIGHTS_SHA = '3bde7e1ee2b8903a89033901094fd0e305566d195db577d77ecb8b892d6cfa95'


def digest(path, algorithm='sha256'):
    checksum = hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def prepare_inputs(inputs, parses):
    by_row = {p['row']: p for p in parses}
    prepared = []
    for record in inputs:
        parsed = by_row[record['row']]
        if record['subject'] != parsed['subject']:
            raise ValueError('description changed')
        words = [word for sentence in parsed['sentences'] for word in sentence]
        for word in words:
            if record['subject'][word['start_char']:word['end_char']] != word['text']:
                raise ValueError('token offset does not recover source text')
        targets = [i for i, word in enumerate(words) if word['upos'] in PARTS]
        prepared.append(dict(record, words=words, targets=targets))
    return prepared


def candidate_keys(text, lemma, upos, condition, wordnet):
    if condition == 'unrestricted':
        return None
    if upos not in PARTS:
        raise ValueError('unsupported part of speech')
    if condition == 'saved':
        return {item.key() for item in wordnet.lemmas(lemma, pos=PARTS[upos])
                if item.key().split('%')[0] == lemma}
    if condition in ('surface', 'surface_pos'):
        parts = ('n', 'v', 'a', 'r') if condition == 'surface' else (PARTS[upos],)
        return {item.key() for pos in parts
                for form in wordnet._morphy(text.lower(), pos)
                for item in wordnet.lemmas(form, pos=pos)
                if item.key().split('%')[0] == form}
    raise ValueError('unknown candidate condition')


def tokenize_words(words, tokenizer, max_length):
    ids = [tokenizer.cls_token_id]
    spans = []
    for word in words:
        pieces = tokenizer.encode(word, add_special_tokens=False)
        if not pieces:
            raise ValueError('token produced no WordPieces')
        spans.append([len(ids), len(ids) + len(pieces)])
        ids.extend(pieces)
    ids.append(tokenizer.sep_token_id)
    if len(ids) > max_length:
        raise ValueError('description exceeds model length; no truncation')
    return ids, spans


def pool_layers(states, spans, weights):
    if len(states) != 25 or len(weights) != 25:
        raise ValueError('expected BERT-large states and published 25 weights')
    length = states[0].shape[1]
    if any(not 1 <= start < end <= length - 1 for start, end in spans):
        raise ValueError('invalid WordPiece range')
    layers = []
    for state in reversed(states[1:]):
        if hasattr(state, 'detach'):
            state = state.detach().cpu().numpy()
        layers.append(np.stack([state[0, start:end].mean(axis=0) for start, end in spans]))
    # Match the native numpy weighted sum, without per-layer normalization.
    return np.stack([weight * layer for weight, layer in zip(weights, layers)]).sum(axis=0)


def rank_conditions(labels, scores, candidates, topn=5):
    if len(labels) != len(scores) or not np.isfinite(scores).all():
        raise ValueError('one finite score required per inventory entry')
    # Same deterministic file-order tie break in every condition.
    order = np.argsort(-scores, kind='stable')
    result = {}
    for condition, allowed in candidates.items():
        selected = []
        for index in order:
            key = labels[index]
            if allowed is None or key in allowed:
                selected.append((key, float(scores[index])))
                if len(selected) == topn:
                    break
        result[condition] = selected
    return result


def read_inventory(path, dimension=1024, max_bytes=4 * 1024 ** 3):
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir() and m.filename.endswith('.txt')]
        if len(members) != 1 or members[0].file_size > max_bytes:
            raise ValueError('expected one bounded text vector inventory')
        member = members[0]
        with archive.open(member) as stream:
            count = sum(1 for _ in stream)
        if count > 250000 or count * dimension * 4 > max_bytes:
            raise ValueError('inventory allocation exceeds limit')
        matrix = np.empty((count, dimension), dtype=np.float32)
        labels = []
        with archive.open(member) as stream:
            for index, line in enumerate(stream):
                label, values = line.decode('utf-8').strip().split(' ', 1)
                vector = np.fromstring(values, sep=' ', dtype=np.float32)
                norm = np.linalg.norm(vector)
                if vector.shape != (dimension,) or not np.isfinite(vector).all() or norm <= 0:
                    raise ValueError('invalid sense vector')
                labels.append(label)
                matrix[index] = vector / norm
        if len(set(labels)) != len(labels):
            raise ValueError('duplicate inventory sensekeys')
    return labels, matrix, dict(member=member.filename, rows=count, dimension=dimension,
                               uncompressed_bytes=member.file_size, matrix_bytes=matrix.nbytes)


def encode_records(records, model_path, weights):
    import torch
    from transformers import BertModel, BertTokenizer
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    tokenizer = BertTokenizer.from_pretrained(model_path, local_files_only=True, do_lower_case=False)
    model = BertModel.from_pretrained(model_path, local_files_only=True,
                                     use_safetensors=True, attn_implementation='eager').cpu().eval()
    if model.config.num_hidden_layers != 24 or model.config.hidden_size != 1024:
        raise ValueError('expected pinned BERT-large shape')
    outputs, vectors = [], []
    for record in records:
        ids, spans = tokenize_words([w['text'] for w in record['words']], tokenizer,
                                   model.config.max_position_embeddings)
        tensor = torch.tensor([ids])
        with torch.inference_mode():
            states = model(input_ids=tensor, attention_mask=torch.ones_like(tensor),
                           output_hidden_states=True).hidden_states
        pooled = pool_layers(states, spans, weights)
        for target in record['targets']:
            raw = pooled[target]
            norm = np.linalg.norm(raw)
            if not np.isfinite(raw).all() or norm <= 0:
                raise ValueError('invalid contextual vector')
            vectors.append(raw / norm)
            outputs.append(dict(row=record['row'], note=record['note'], subject=record['subject'],
                                word_index=target, word=record['words'][target]))
        record['input_ids'], record['wordpiece_ranges'] = ids, spans
        print(f"Encoded row {record['row']}: {len(ids)} WordPieces, {len(record['targets'])} targets", flush=True)
    del model
    gc.collect()
    return outputs, np.asarray(vectors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['inputs', 'parses', 'assets', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve prior runs')
    from nltk.corpus import wordnet as wn
    model_path = args.assets / 'bert'
    inventory = args.assets / 'lmms-sp-usm.bert-large-cased.vectors.zip'
    weights_path = args.assets / 'weights.txt'
    for path, algorithm, expected in [(model_path / 'model.safetensors', 'sha256', MODEL_SHA),
                                      (inventory, 'md5', ZIP_MD5), (weights_path, 'sha256', WEIGHTS_SHA)]:
        if digest(path, algorithm) != expected:
            raise ValueError(f'asset checksum mismatch: {path.name}')
    memory = {line.split(':')[0]: int(line.split()[1]) for line in
              Path('/proc/meminfo').read_text().splitlines()}
    if memory['MemAvailable'] < 8 * 1024 ** 2:
        raise RuntimeError('less than 8 GiB available; do not start model loading')
    records = prepare_inputs(json.loads(args.inputs.read_bytes()), json.loads(args.parses.read_bytes()))
    weights = np.array([float(x) for x in weights_path.read_text().split()])
    started = time.monotonic()
    targets, vectors = encode_records(records, model_path, weights)
    encoding_seconds = time.monotonic() - started
    started = time.monotonic()
    labels, matrix, info = read_inventory(inventory)
    inventory_keys = set(labels)
    if len(targets) * len(labels) * 8 > 512 * 1024 ** 2:
        raise ValueError('score allocation exceeds diagnostic limit')
    all_scores = (matrix @ vectors.T).T
    for target, scores in zip(targets, all_scores):
        word = target['word']
        candidates = {condition: candidate_keys(word['text'], word['lemma'], word['upos'], condition, wn)
                      for condition in ('saved', 'surface', 'unrestricted')}
        ranked = rank_conditions(labels, scores, candidates)
        target['candidates'] = {c: dict(requested=len(keys), available=len(keys & inventory_keys),
                                        missing=sorted(keys - inventory_keys))
                                if keys is not None else dict(available=len(labels))
                                for c, keys in candidates.items()}
        target['matches'] = {condition: [dict(key=key, cosine=cosine,
                                             synset=wn.lemma_from_key(key).synset().name(),
                                             definition=wn.lemma_from_key(key).synset().definition())
                                         for key, cosine in pairs] for condition, pairs in ranked.items()}
    config = dict(run_id='USM01', model_revision=MODEL_REVISION, lmms_revision=LMMS_REVISION,
                  layers=list(range(-1, -25, -1)), published_weights=weights.tolist(),
                  used_weights=weights[:24].tolist(), device='cpu', torch_threads=2,
                  wordpiece_pooling='mean', attention='eager', batch_size=1,
                  target_dtype=str(vectors.dtype), score_dtype=str(all_scores.dtype),
                  tie_break='inventory file order, shared across conditions',
                  inventory=info, encoding_seconds=encoding_seconds,
                  inventory_and_matching_seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  initial_memavailable_kib=memory['MemAvailable'],
                  input_sha256=digest(args.inputs), parses_sha256=digest(args.parses),
                  runner_sha256=digest(Path(__file__)),
                  assets={str(p.relative_to(args.assets)): digest(p)
                          for p in sorted(args.assets.rglob('*')) if p.is_file()},
                  packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()})
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', targets), ('tokenization.json', records), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    with (args.output / 'target-vectors.npz').open('xb') as stream:
        np.savez_compressed(stream, vectors=vectors)
    for name, source in [('inputs.json', args.inputs), ('lmms_occurrence_probe.py', Path(__file__))]:
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(targets=len(targets), notes=len({t['note'] for t in targets}),
                          peak_rss_kib=config['peak_rss_kib'])), flush=True)


if __name__ == '__main__':
    main()
