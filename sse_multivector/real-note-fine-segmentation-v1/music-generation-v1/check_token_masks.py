"""Read-only diagnostic using the frozen tokenizer and production pooling rule."""

import json
from pathlib import Path

from transformers import AutoTokenizer
from worker import _byte_span_to_character_span, select_token_indices

request = json.loads(Path('/input/worker-request.json').read_text())
tokenizer = AutoTokenizer.from_pretrained(
    '/model', local_files_only=True, trust_remote_code=False, use_fast=True
)
failures = []
checked = 0
for note in request['notes']:
    text = note['text']
    tokens = tokenizer(
        text, add_special_tokens=True, padding=False, truncation=False,
        return_attention_mask=True, return_offsets_mapping=True,
    )
    offsets = tokens['offset_mapping']
    for subject in note['subjects']:
        checked += 1
        spans = subject['byte_spans']
        try:
            select_token_indices(text, spans, offsets)
        except ValueError as error:
            chars = [_byte_span_to_character_span(text, span) for span in spans]
            failures.append({
                'note_id': note['note_id'],
                'worker_subject_id': subject['subject_id'],
                'text': text,
                'byte_spans': spans,
                'fragments': [text[left:right] for left, right in chars],
                'error': str(error),
                'overlapping_tokens': [
                    {'index': i, 'id': token_id, 'offset': [left, right],
                     'text': text[left:right]}
                    for i, (token_id, (left, right)) in enumerate(
                        zip(tokens['input_ids'], offsets, strict=True)
                    )
                    if any(left < b and a < right for a, b in chars)
                ],
            })
print(json.dumps({'schema_version': 1, 'checked_masks': checked,
                  'failures': failures}, ensure_ascii=False))
