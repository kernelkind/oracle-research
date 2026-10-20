"""Preserve starting subject trees and join them with separately shared posts."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from ._runner_bootstrap import shared


FORMAT = 'hierarchy-inputs-publication-v1'


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _stamp(path):
    value = Path(path).stat()
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _selection(path):
    selected = Path(path).read_text(encoding='utf-8').splitlines()
    if (not selected or any(not identifier.strip() or identifier != identifier.strip()
                            or '\x00' in identifier for identifier in selected)
            or len(set(selected)) != len(selected)):
        raise ValueError('note selection requires unique nonempty single-line IDs')
    return selected


def _selection_hash(selected):
    return hashlib.sha256(''.join(identifier+'\n' for identifier in selected).encode()).hexdigest()


@contextmanager
def _ordered_rows(path, selected, project):
    """One source pass and an on-disk spool; RAM holds only IDs and offsets.

    Source order need not match the experiment's selected order. Never retain
    unrelated posts, or all selected text/subject trees, in memory.
    """
    import ijson

    path = Path(path)
    before = _stamp(path)
    needed, positions = set(selected), {}
    with tempfile.TemporaryFile() as spool, path.open('rb') as stream:
        rows = ((json.loads(line) for line in stream) if path.suffix == '.jsonl'
                else ijson.items(stream, 'notes.item'))
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('note_id'), str):
                raise ValueError('corpus rows require note_id strings')
            identifier = row['note_id']
            if identifier not in needed:
                continue
            if identifier in positions:
                raise ValueError('duplicate selected note ID: '+identifier)
            raw = json.dumps(project(row), ensure_ascii=False, separators=(',', ':'),
                             allow_nan=False).encode()
            positions[identifier] = spool.tell(), len(raw)
            spool.write(raw)
        if needed != positions.keys():
            raise ValueError('missing selected note IDs: '+', '.join(sorted(needed-positions.keys())[:5]))
        if _stamp(path) != before:
            raise ValueError('corpus source changed while reading')

        def ordered():
            for identifier in selected:
                offset, length = positions[identifier]
                spool.seek(offset)
                yield json.loads(spool.read(length))

        yield ordered()
        if _stamp(path) != before:
            raise ValueError('corpus source changed while reading')


def _post(row):
    if not isinstance(row.get('text'), str) or not row['text'].strip():
        raise ValueError('selected post text must be nonempty')
    return dict(note_id=row['note_id'], text=row['text'])


def _subjects(row):
    rows = row.get('subjects')
    if not isinstance(rows, list):
        raise ValueError('selected note requires a subjects array')
    subjects, seen = [], set()
    for entry in rows:
        if (not isinstance(entry, dict) or not isinstance(entry.get('number'), str)
                or not re.fullmatch(r'[1-9]\d*(?:\.[1-9]\d*)*', entry['number'])
                or any(not isinstance(entry.get(key), str) or not entry[key].strip()
                       for key in ('subject', 'context'))):
            raise ValueError('invalid starting subject')
        number = entry['number']
        if number in seen:
            raise ValueError('duplicate starting subject number')
        seen.add(number)
        subjects.append({key: entry[key] for key in ('number', 'subject', 'context')})
    if any('.' in number and number.rsplit('.', 1)[0] not in seen for number in seen):
        raise ValueError('starting subject tree is missing a parent')
    origin = row.get('origin', {})
    version = origin.get('prompt_version') if isinstance(origin, dict) else None
    if version is not None and (not isinstance(version, str) or not version.strip()):
        raise ValueError('invalid starting subject prompt version')
    return dict(note_id=row['note_id'], subjects=subjects, origin=dict(prompt_version=version))


def export_inputs(corpus, note_ids, output):
    corpus, output = Path(corpus).resolve(), Path(output)
    selected = _selection(note_ids)
    before = _stamp(corpus)
    digest, selection_digest = _hash(corpus), _selection_hash(selected)
    if corpus.is_relative_to(output.resolve()) or Path(note_ids).resolve().is_relative_to(output.resolve()):
        raise ValueError('publication output overlaps its inputs')
    metadata = dict(schema_version=1, format=FORMAT,
        source_id=hashlib.sha256((digest+selection_digest).encode()).hexdigest(),
        input=dict(corpus_sha256=digest, note_ids_sha256=selection_digest, notes=len(selected)),
        parameters=dict(subject_fields=['number', 'subject', 'context'],
                        post_binding='SHA-256 of exact UTF-8 post text'),
        outcome=dict(subjects=0, root_subjects=0, notes_without_subjects=0),
        exporter_sources={'sse_multivector/published_corpus.py': _hash(__file__)})

    def project(note):
        return dict(**_subjects(note), text_sha256=hashlib.sha256(_post(note)['text'].encode()).hexdigest())

    def records():
        versions = set()
        with _ordered_rows(corpus, selected, project) as rows:
            for row in rows:
                metadata['outcome']['subjects'] += len(row['subjects'])
                metadata['outcome']['root_subjects'] += sum('.' not in s['number'] for s in row['subjects'])
                metadata['outcome']['notes_without_subjects'] += not row['subjects']
                versions.add(row['origin']['prompt_version'])
                yield row
        if _stamp(corpus) != before:
            raise ValueError('corpus source changed during export')
        metadata['input']['subject_prompt_versions'] = sorted(v for v in versions if v is not None)
        if None in versions:
            metadata['input']['subject_prompt_versions'].append(None)

    return shared('publication_files').write_publication(output, metadata, {'subjects.jsonl': records()})


def prepare_corpus(posts, note_ids, output, subjects=None):
    """Make a fresh native corpus, preserving selected order and exact text."""
    posts, output = Path(posts), Path(output)
    selected = _selection(note_ids)
    if output.exists() or output.is_symlink():
        raise ValueError('corpus output already exists')
    subject_path, expected_hash = None, None
    if subjects is not None:
        directory = Path(subjects)
        metadata = json.loads((directory/'experiment.json').read_bytes())
        subject_path = directory/'subjects.jsonl'
        if (metadata.get('schema_version') != 1 or metadata.get('format') != FORMAT
                or metadata.get('input', {}).get('note_ids_sha256') != _selection_hash(selected)
                or metadata['input'].get('notes') != len(selected)):
            raise ValueError('starting subjects do not match the ordered note selection')
        expected_hash = metadata['files']['subjects.jsonl']['sha256']
        if _hash(subject_path) != expected_hash:
            raise ValueError('starting subject payload hash mismatch')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.corpus-', dir=output.parent) as temporary:
        staged = Path(temporary)/'corpus.json'
        with _ordered_rows(posts, selected, _post) as originals, staged.open('w', encoding='utf-8') as stream:
            stream.write('{"schema_version":1,"notes":[')

            def write(rows, starting=None):
                for index, note in enumerate(rows):
                    if starting is not None:
                        row = next(starting)
                        if (row['note_id'] != note['note_id']
                                or row.get('text_sha256') != hashlib.sha256(note['text'].encode()).hexdigest()):
                            raise ValueError('starting subjects bind different post text')
                        note.update({k: value for k, value in _subjects(row).items() if k != 'note_id'})
                    if index:
                        stream.write(',')
                    json.dump(note, stream, ensure_ascii=False, separators=(',', ':'), allow_nan=False)

            if subject_path is None:
                write(originals)
            else:
                with _ordered_rows(subject_path, selected, lambda row: row) as starting:
                    write(originals, starting)
                if _hash(subject_path) != expected_hash:
                    raise ValueError('starting subject payload hash changed')
            stream.write(']}\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Hard-linking the complete staged file refuses an existing destination,
        # including a symlink, without ever exposing a partial native corpus.
        os.link(staged, output)
    return dict(output=str(output), notes=len(selected), saved_subjects=subjects is not None)
