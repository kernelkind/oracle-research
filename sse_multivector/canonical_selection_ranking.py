"""Bounded text/SSE candidate retrieval; scores never establish a relationship."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import re

from sse_multivector.ancestor_cosine_probe import cosine, load_vectors
from sse_multivector.subject_matching_probe import load_subject_vectors
from sse_multivector.worker import _load_request, _sha256_file


MAX_ROWS = 4096
MAX_ANCESTORS = 64
MAX_FIELD_BYTES = 16384
MAX_INPUT_BYTES = 4 * 1024 * 1024
_WORDS = re.compile(r'\w+', re.UNICODE)
_STOP = frozenset('a an and as at be by for from in is it of on or that the their '
                  'these this to used using was were which with'.split())


def _validate(query_subject, query_meaning, rows, query_ancestors):
    if not isinstance(rows, (list, tuple)) or len(rows) > MAX_ROWS:
        raise ValueError(f'candidate retrieval requires at most {MAX_ROWS} rows')
    if (not isinstance(query_ancestors, (list, tuple))
            or len(query_ancestors) > MAX_ANCESTORS):
        raise ValueError('candidate retrieval requires at most 64 ancestor headings')
    total = 0

    def text(value, name, empty=False):
        nonlocal total
        if not isinstance(value, str) or (not empty and not value.strip()):
            raise ValueError(name + ' must be text')
        size = len(value.encode('utf-8'))
        if size > MAX_FIELD_BYTES:
            raise ValueError(name + ' exceeds retrieval field byte limit')
        total += size

    text(query_subject, 'query subject')
    text(query_meaning, 'query meaning', empty=True)
    for heading in query_ancestors:
        text(heading, 'ancestor heading')
    ids = set()
    for row in rows:
        if not isinstance(row, dict) or not {'id', 'subject', 'meaning'} <= set(row):
            raise ValueError('candidate rows require id, subject, and meaning')
        text(row['id'], 'candidate ID')
        text(row['subject'], 'candidate subject')
        text(row['meaning'], 'candidate meaning', empty=True)
        if row['id'] in ids:
            raise ValueError('duplicate candidate ID')
        ids.add(row['id'])
    if total > MAX_INPUT_BYTES:
        raise ValueError('candidate retrieval exceeds total input byte limit')


def _features(text):
    words = [word for word in _WORDS.findall(text.casefold()) if word not in _STOP]
    return Counter(words + [' '.join(pair) for pair in zip(words, words[1:])])


def rank_text(query_subject, query_meaning, rows, query_ancestors=()):
    """Original TF-IDF reference; optional ancestor headings are separate queries."""
    _validate(query_subject, query_meaning, rows, query_ancestors)
    queries = [_features(query_subject + ' ' + query_subject + ' ' + query_meaning)]
    queries.extend(_features(heading + ' ' + heading) for heading in query_ancestors)
    documents = {row['id']: _features(row['subject'] + ' ' + row['subject']
                                    + ' ' + row['meaning']) for row in rows}
    frequencies = Counter(word for words in documents.values() for word in words)
    idf = {word: math.log((1 + len(rows)) / (1 + frequencies[word])) + 1
           for word in set(frequencies).union(*(set(query) for query in queries))}

    def vector(words):
        values = {word: (1 + math.log(count)) * idf[word] for word, count in words.items()}
        norm = math.sqrt(sum(value * value for value in values.values())) or 1
        return {word: value / norm for word, value in values.items()}

    query_vectors = [vector(query) for query in queries]
    document_vectors = {identifier: vector(words) for identifier, words in documents.items()}
    scores = {identifier: max(sum(query.get(word, 0) * value
                                 for word, value in words.items())
                              for query in query_vectors)
              for identifier, words in document_vectors.items()}
    return sorted(scores, key=lambda identifier: (-scores[identifier], identifier)), scores


@lru_cache(maxsize=1)
def _saved_vectors(probe):
    return load_subject_vectors(Path(probe))


def _alternate(first, second):
    streams, order, seen = [iter(first), iter(second)], [], set()
    while streams:
        active = []
        for stream in streams:
            selected = next((identifier for identifier in stream if identifier not in seen), None)
            if selected is not None:
                order.append(selected)
                seen.add(selected)
                active.append(stream)
        streams = active
    return order


def rank_candidates(query_subject, query_meaning, rows, subject_probe=None, query_ancestors=()):
    """Return (order, provenance), with one candidate list and no model decisions.

    Ancestor headings can nominate broader topics. They do not redefine the
    selected topic or provide new vectors: each uses its own saved heading row.
    A cached probe is rehashed on every call; a changed source fails closed.
    """
    text_order, text_scores = rank_text(query_subject, query_meaning, rows, query_ancestors)
    headings = list(dict.fromkeys([query_subject, *query_ancestors]))
    sources = {str(Path(__file__).resolve()): _sha256_file(Path(__file__).resolve())}
    sse_scores, vector_metadata = None, None
    order = text_order
    if subject_probe is not None:
        probe = Path(subject_probe).resolve()
        vectors, receipt, protected = _saved_vectors(str(probe))
        for path, expected in protected.items():
            if _sha256_file(Path(path)) != expected:
                raise ValueError('saved SSE source changed: ' + path)
        sources.update(protected)
        for function in (load_subject_vectors, load_vectors, cosine, _load_request):
            path = Path(function.__code__.co_filename).resolve()
            sources[str(path)] = _sha256_file(path)

        selected = {}
        for heading in dict.fromkeys([*headings, *(row['subject'] for row in rows)]):
            digest = hashlib.sha256(heading.encode('utf-8')).hexdigest()
            vector = vectors.get((digest, digest[:16]))
            if vector is None:
                raise ValueError('missing saved SSE heading: ' + heading)
            cosine(vector, vector)
            selected[heading] = vector
        by_heading = {subject: max(cosine(selected[heading], selected[subject])
                                   for heading in headings)
                      for subject in dict.fromkeys(row['subject'] for row in rows)}
        sse_scores = {row['id']: by_heading[row['subject']] for row in rows}
        sse_order = sorted(sse_scores, key=lambda identifier: (-sse_scores[identifier], identifier))
        order = _alternate(sse_order, text_order)
        vector_metadata = dict(probe=str(probe), loaded_vectors=len(vectors),
            **deepcopy({key: receipt.get(key) for key in ('dimensions', 'checkpoint_sha256',
                'base_model_artifact_tree_sha256', 'model', 'runtime', 'device', 'note_batch_size')}))
    return order, dict(scores={identifier: 1 / (index + 1) for index, identifier in enumerate(order)},
        text_scores=text_scores, sse_scores=sse_scores, query_headings=headings,
        sources=sources, subject_vectors=vector_metadata, inference_calls=0, new_encodings=0,
        method='alternate SSE-first/text next unseen' if subject_probe is not None else 'text only',
        score_interpretation='reciprocal position in final order; not semantic confidence',
        ancestor_query_policy='maximum similarity across selected topic and supplied ancestor headings')
