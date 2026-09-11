"""Fixed-group directional description diagnostic; does not construct a hierarchy."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import resource
import time

from mask_description_nli import independent_scores, sha256


def prepare_pairs(groups, fixture):
    by_id = {g['id']: g for g in groups}
    requested = [g['id'] for g in fixture['groups']]
    if (len(by_id) != len(groups) or len(requested) < 2
            or len(set(requested)) != len(requested)
            or not set(requested).issubset(by_id)):
        raise ValueError('at least two distinct known groups required')
    originals = {}
    descriptions = {}
    for group in fixture['groups']:
        key = group['id']
        phrases = [' '.join(s['source']['fragments']) for s in by_id[key]['seeds']]
        if not phrases or len({' '.join(p.casefold().split()) for p in phrases}) != 1:
            raise ValueError('all seed phrases must agree, apart from case and whitespace')
        originals[key] = phrases[0]
        descriptions[key] = group['description']
        if not originals[key].strip() or not descriptions[key].strip():
            raise ValueError('nonempty group descriptions required')
    expected = {tuple(p) for p in fixture['expected_implications']}
    if any(len(p) != 2 or p[0] == p[1] or not set(p).issubset(requested) for p in expected):
        raise ValueError('expected implications must refer to distinct requested groups')
    pairs = []
    for condition, child_context, parent_context in [
            ('both_phrases', False, False), ('child_context', True, False),
            ('parent_context', False, True), ('both_context', True, True)]:
        for child in requested:
            for parent in requested:
                if child == parent:
                    continue
                child_text = (descriptions if child_context else originals)[child]
                parent_text = (descriptions if parent_context else originals)[parent]
                pairs.append(dict(
                    condition=condition, child=child, parent=parent,
                    premise=fixture['template'].format(child_text),
                    hypothesis=fixture['template'].format(parent_text),
                    expected_implication=(child, parent) in expected))
    return pairs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--groups', type=Path, required=True)
    parser.add_argument('--fixture', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output exists; preserve earlier experiments')
    groups = json.loads(args.groups.read_bytes())
    fixture = json.loads(args.fixture.read_bytes())
    pairs = prepare_pairs(groups, fixture)
    source_groups = [g for g in groups if g['id'] in {p['child'] for p in pairs}]

    import torch
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    started = time.monotonic()
    print('Loading pinned cached model; CPU only, two threads, no downloads', flush=True)
    snapshot = Path(snapshot_download(
        fixture['model_id'], revision=fixture['model_revision'],
        cache_dir=str(args.cache), local_files_only=True, token=False))
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        snapshot, local_files_only=True, use_safetensors=True, trust_remote_code=False).cpu().eval()
    mapping = model.config.id2label
    entailment = [i for i, label in mapping.items() if label.lower() == 'entailment']
    if len(mapping) != 2 or len(entailment) != 1:
        raise ValueError('expected a binary entailment classifier')
    loading_seconds = time.monotonic() - started
    started = time.monotonic()
    print('Scoring ' + str(len(pairs)) + ' fixed ordered pairs', flush=True)
    for start in range(0, len(pairs), 4):
        batch = pairs[start:start + 4]
        tokens = tokenizer([p['premise'] for p in batch], [p['hypothesis'] for p in batch],
                           padding=True, truncation=False, return_tensors='pt')
        if tokens['input_ids'].shape[1] > 512:
            raise ValueError('input exceeds supported length; no silent truncation')
        with torch.inference_mode():
            logits = model(**tokens).logits.tolist()
        for pair, raw, score, length in zip(
                batch, logits, independent_scores(logits, entailment[0]),
                tokens['attention_mask'].sum(dim=1).tolist()):
            pair.update(logits=raw, score=score, token_count=length)
    inference_seconds = time.monotonic() - started
    summaries = []
    for condition in dict.fromkeys(p['condition'] for p in pairs):
        rows = [p for p in pairs if p['condition'] == condition]
        summaries.append(dict(
            condition=condition, pairs=len(rows),
            positive_decisions=sum(p['score'] > .5 for p in rows),
            expected_positive_decisions=sum(p['score'] > .5 and p['expected_implication'] for p in rows),
            disagreements=[p for p in rows if (p['score'] > .5) != p['expected_implication']]))
    helper = Path(__file__).with_name('mask_description_nli.py')
    config = dict(
        run_id=fixture['run_id'], model_id=fixture['model_id'], model_revision=fixture['model_revision'],
        model_files={str(p.relative_to(snapshot)): sha256(p)
                     for p in sorted(snapshot.rglob('*')) if p.is_file()},
        model_labels=mapping, parameters=sum(p.numel() for p in model.parameters()),
        groups_sha256=sha256(args.groups), fixture_sha256=sha256(args.fixture),
        runner_sha256=sha256(Path(__file__)), helper_sha256=sha256(helper),
        packages={d.metadata['Name']: d.version for d in importlib.metadata.distributions()},
        torch_threads=2, batch_size=4, seed=0, device='cpu', loading_seconds=loading_seconds,
        inference_seconds=inference_seconds, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        notes='Manual descriptions are diagnostic inputs. Scores are not calibrated probabilities. No group, mask, note membership or hierarchy changed.')
    args.output.mkdir(parents=True)
    for name, value in [('scores.json', pairs), ('summary.json', summaries),
                        ('groups.json', source_groups), ('config.json', config)]:
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    for name, source in [('fixture.json', args.fixture), ('group_description_relations.py', Path(__file__)),
                         ('mask_description_nli.py', helper)]:
        with (args.output / name).open('xb') as stream:
            stream.write(source.read_bytes())
    print(json.dumps(dict(pairs=len(pairs), inference_seconds=inference_seconds,
                         positive_decisions={r['condition']: r['positive_decisions'] for r in summaries})))


if __name__ == '__main__':
    main()
