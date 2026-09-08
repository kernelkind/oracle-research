#!/usr/bin/env python3
"""Tokenize complete original notes, then freeze a deterministic text-only sample."""

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
AUDIT = ROOT.parent / 'corpus-audit'
sys.path.insert(0, str(AUDIT))
from audit_corpus import EXPOSED_PRIOR_IDS, order, visible_words

SOURCE = AUDIT / 'food-combined-manually-eligible-v2.json'
IMAGE = 'sha256:a6c9674dca720e1f094b7feeb1397b6e6b0a97e10f13e0a6555deebf4b70ddaa'


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def read_source():
    raw = SOURCE.read_bytes()
    rows = json.loads(raw)['notes']
    assert len(rows) == len({row['note_id'] for row in rows}) == 194
    assert rows == sorted(rows, key=order)
    for row in rows:
        assert hash_bytes(row['content'].encode()) == row['original_content_sha256']
        assert order(row) == row['selection_order_sha256']
    return raw, rows


def tokenize(model):
    import tokenizers
    import transformers
    from transformers import AutoTokenizer
    raw, rows = read_source()
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False, use_fast=True)
    assert tokenizer.is_fast
    assert tokenizer.model_max_length == 512
    records = []
    for row in rows:
        tokens = tokenizer(row['content'], add_special_tokens=True, padding=False, truncation=False, return_attention_mask=True, return_offsets_mapping=True)
        count = sum(tokens['attention_mask'])
        assert count == len(tokens['input_ids']) == len(tokens['offset_mapping'])
        assert tokens['input_ids'][-1] == tokenizer.eos_token_id
        records.append({'note_id': row['note_id'], 'original_content_sha256': row['original_content_sha256'], 'tokens_including_special_tokens': count, 'within_limit': count <= 512})
    files = {path.name: {'bytes': path.stat().st_size, 'sha256': hash_bytes(path.read_bytes())} for path in sorted(model.iterdir()) if path.is_file()}
    write_json(ROOT / 'token-counts.json', {
        'schema_version': 1,
        'input_file': '../corpus-audit/food-combined-manually-eligible-v2.json',
        'input_sha256': hash_bytes(raw),
        'base_model': 'sentence-transformers/sentence-t5-base',
        'base_model_revision': 'fc5d4628481afbbaaacd7af6bb07cf9d3865f781',
        'tokenizer_class': type(tokenizer).__name__,
        'tokenizer_files': files,
        'transformers_version': transformers.__version__,
        'tokenizers_version': tokenizers.__version__,
        'maximum_tokens_including_special_tokens': 512,
        'settings': {'local_files_only': True, 'trust_remote_code': False, 'use_fast': True, 'add_special_tokens': True, 'padding': False, 'truncation': False, 'return_attention_mask': True, 'return_offsets_mapping': True},
        'production_path_match': 'sse_multivector/worker.py OfficialSseEncoder tokenization settings; unpadded lengths equal production attention-mask sums',
        'container_image': IMAGE,
        'resource_limits': {'network': 'none', 'cpus': 2, 'memory': '2g', 'model_or_checkpoint_loaded': False},
        'records': records,
    })
    print(json.dumps({'counted': len(records), 'over_512': sum(not row['within_limit'] for row in records), 'maximum': max(row['tokens_including_special_tokens'] for row in records)}))


def select(finalize):
    raw, rows = read_source()
    token_raw = (ROOT / 'token-counts.json').read_bytes()
    token_data = json.loads(token_raw)
    assert token_data['input_sha256'] == hash_bytes(raw)
    tokens = {row['note_id']: row for row in token_data['records']}
    assert set(tokens) == {row['note_id'] for row in rows}
    quarantined = EXPOSED_PRIOR_IDS | {'2c054d399715c118387a16ab9d3960d3dcb27cd8c3ee33cea2ac3336138a1b6a'}
    authors = collections.Counter()
    retained = []
    fingerprints = []
    log = []
    for combined_rank, row in enumerate(rows, 1):
        token_count = tokens[row['note_id']]['tokens_including_special_tokens']
        entry = {'combined_hash_rank': combined_rank, 'note_id': row['note_id'], 'tokens_including_special_tokens': token_count, 'selection_order_sha256': order(row)}
        if token_count > 512:
            entry.update(status='excluded', reason='Complete original note exceeds 512 tokens; no truncation or URL removal allowed.')
        elif row['note_id'] in quarantined:
            entry.update(status='excluded', reason='Previously recorded provenance-search quarantine.')
        elif len(retained) == 100:
            entry.update(status='not_selected', reason='First 100 passing notes already selected in deterministic hash order; no semantic or length quota.')
        else:
            words = visible_words(row['content'])
            normalized = ' '.join(words)
            shingles = set(zip(words, words[1:], words[2:], words[3:]))
            copied = None
            for previous_id, previous_words, previous_normalized, previous_shingles in fingerprints:
                if normalized == previous_normalized:
                    copied = (previous_id, 'exact_normalized_visible_text_copy')
                    break
                ratio = min(len(words), previous_words) / max(len(words), previous_words)
                union = shingles | previous_shingles
                if ratio >= .7 and union and len(shingles & previous_shingles) / len(union) >= .8:
                    copied = (previous_id, 'four_word_shingle_jaccard_ge_0.8_length_ratio_ge_0.7')
                    break
            if copied:
                entry.update(status='excluded', reason=copied[1], copied_selected_note_id=copied[0])
            elif authors[row['pubkey']] >= 2:
                entry.update(status='excluded', reason='Two earlier selected notes already represent this public author.')
            else:
                authors[row['pubkey']] += 1
                fingerprints.append((row['note_id'], len(words), normalized, shingles))
                retained.append({
                    'note_id': row['note_id'], 'text': row['content'], 'pubkey': row['pubkey'],
                    'provenance': {
                        'source_file': 'target/crec-113-formal-v1/sample/sample.jsonl',
                        'source_file_sha256': '8edb8a51246201100e6ba7cf7bf1bbf9cd501881d7c70b8a9cfc7a380d1b168e',
                        'source_row': row['source_row'], 'source_split': row['split'],
                        'original_content_sha256': row['original_content_sha256'],
                        'corpus_audit_file': row['audit_source_file'],
                        'corpus_audit_candidate_rank': row['candidate_rank'],
                        'combined_hash_rank': combined_rank, 'selection_order_sha256': order(row),
                    },
                    'selection_rank': len(retained) + 1,
                    'tokens_including_special_tokens': token_count,
                    'visible_word_count': row['visible_word_count'],
                    'selection_rationale': row['broad_area_eligibility_rationale'],
                })
                entry.update(status='selected', selection_rank=len(retained), reason=row['broad_area_eligibility_rationale'])
        log.append(entry)
    assert len(retained) == len({row['note_id'] for row in retained}) == 100
    assert max(authors.values()) <= 2
    data = {'schema_version': 1, 'notes': retained}
    summary = {
        'input_notes': len(rows), 'selected_notes': len(retained), 'selected_authors': len(authors),
        'maximum_notes_per_author': max(authors.values()),
        'selected_token_range': [min(row['tokens_including_special_tokens'] for row in retained), max(row['tokens_including_special_tokens'] for row in retained)],
        'selected_5_to_17_word_notes_observed_not_quota': sum(row['visible_word_count'] <= 17 for row in retained),
        'last_selected_combined_hash_rank': retained[-1]['provenance']['combined_hash_rank'],
        'excluded_counts': dict(collections.Counter(row['reason'] for row in log if row['status'] == 'excluded')),
        'not_selected_after_first_100': sum(row['status'] == 'not_selected' for row in log),
    }
    if not finalize:
        write_json(ROOT / 'selection-draft.json', data)
        write_json(ROOT / 'selection-accounting-draft.json', {'schema_version': 1, 'summary': summary, 'records': log})
    else:
        assert json.loads((ROOT / 'selection-draft.json').read_text()) == data
        review = json.loads((ROOT / 'complete-note-review.json').read_text())
        assert review['reviewed_selection_rank_range'] == [1, 100]
        assert review['selection_draft_sha256'] == hash_bytes((ROOT / 'selection-draft.json').read_bytes())
        assert review['complete_original_text_reviewed'] is True
        write_json(ROOT / 'notes.json', data)
        write_json(ROOT / 'selection-accounting.json', {'schema_version': 1, 'summary': summary, 'records': log})
        manifest = {
            'schema_version': 1, 'frozen_before_subject_mask_generation_and_sse': True,
            'area': 'Food and drink: preparation, eating experiences and preferences',
            'selection_rule': 'First 100 manually eligible notes in domain-separated SHA-256 event-ID order passing complete-original-text <=512 pinned Sentence-T5 tokens, recorded quarantine, exact/near-copy check and max-two-per-public-author; no semantic or length quotas.',
            'source_input_sha256': hash_bytes(raw), 'token_counts_sha256': hash_bytes(token_raw),
            'verified_base_model_artifact_tree_sha256': 'bba50abbbb7de6165ee3828c4e4abb0c88a6386bd4754374469246cde5017e5d',
            'summary': summary,
            'files': {name: {'bytes': (ROOT / name).stat().st_size, 'sha256': hash_bytes((ROOT / name).read_bytes())} for name in ['notes.json', 'selection-accounting.json', 'token-counts.json', 'complete-note-review.json', 'freeze_selection.py']},
            'all_original_text_preserved_without_truncation': True,
            'prior_familiarity': 'Possible old coffee-roasting/decaf text familiarity remains recorded in corpus audit. Familiarity is not an automatic exclusion for this development collection; ten already quarantined examples remain excluded.',
            'no_vectors_or_prior_clustering_outcomes_used': True,
        }
        write_json(ROOT / 'manifest.json', manifest)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('tokenize', 'draft', 'freeze'))
    parser.add_argument('--model', type=Path)
    args = parser.parse_args()
    if args.mode == 'tokenize':
        assert args.model is not None
        tokenize(args.model)
    else:
        select(args.mode == 'freeze')
