"""Prepare source-bound title-fragment SSE diagnostics, optionally without context.

Uses the existing native worker and frozen encoder settings. Original titles,
meanings, memberships and policies are never rewritten. This is a research
input adapter, not an automatic grammatical analysis or admission rule.
Sources may be a saved study directory or an ASv6.100 native hierarchy state;
whole-title preparation retains the full meaning as context unless standalone.
"""
import argparse
import hashlib
import json
from pathlib import Path

from sse_multivector import worker
from sse_multivector.meaning_example_probe import read, write, digest, unchanged

VIEWS = ('title', 'meaning', 'selection')


def prepare(study, entries, selected_text, output, *, standalone=False):
    study, output = Path(study).resolve(), Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if (not entries or len(set(entries)) != len(entries)
            or (selected_text is not None and not selected_text.strip())):
        raise ValueError('distinct entries and selected text or whole titles required')
    if study.is_file():
        native = read(study)
        corpus_path = Path(native['corpus'])
        if not corpus_path.is_absolute():
            corpus_path = study.parent/corpus_path
        corpus_path = corpus_path.resolve()
        corpus = read(corpus_path)
        if not corpus.get('notes') or any(n.get('origin',{}).get('prompt_version') != 'ASv6.100'
                                           for n in corpus['notes']):
            raise ValueError('approved ASv6.100 provenance required')
        originals = {r['id']:r for r in native['originals']}
        ids = native['families'][0]['rounds'][0]['current']
        if any(i not in originals for i in ids):
            raise ValueError('native initial input must contain original local entries')
        source = dict(as_version='ASv6.100', sources={}, records=[dict(
            id=i,title=originals[i]['title'],meaning=originals[i]['meaning'],
            source_note_id=originals[i]['local']['note_id']) for i in ids])
        template = native['worker_config']
        source_paths = [study,corpus_path]
    else:
        source = read(study/'plan.json')
        template = read(study/'worker-config.json')
        worker.WorkerConfig.load(study/'worker-config.json')
        source_paths = [study/'plan.json',study/'worker-config.json']
    if source.get('as_version') != 'ASv6.100':
        raise ValueError('approved ASv6.100 provenance required')
    by_id = {r['id']: r for r in source['records']}
    if any(i not in by_id for i in entries):
        raise ValueError('selected entry is absent from source')
    sources = {str(Path(p).resolve()): h for p,h in source['sources'].items()}
    for path in [*source_paths, Path(__file__), Path(worker.__file__),
                 Path(unchanged.__code__.co_filename)]:
        sources[str(path.resolve())] = worker._sha256_file(path)
    unchanged(sources)
    contexts, records = {}, []
    for entry in entries:
        item = by_id[entry]
        title, meaning = item['title'], item['meaning']
        selection = title if selected_text is None else selected_text
        if not title.strip() or not meaning.strip() or title.count(selection) != 1:
            raise ValueError('nonempty meaning and one exact title occurrence required')
        text = selection if standalone else title+'\n\n'+meaning
        note_id = hashlib.sha256(text.encode()).hexdigest()
        note = contexts.setdefault(note_id,dict(note_id=note_id,text=text,subjects=[]))
        start = len(title[:title.index(selection)].encode())
        spans = dict(title=(0,len(title.encode())),
                     meaning=(len((title+'\n\n').encode()),len(text.encode())),
                     selection=(start,start+len(selection.encode())))
        if standalone:
            spans = dict(standalone=(0,len(selection.encode())))
        views = {}
        for view,(start,end) in spans.items():
            subject_id = digest([note_id,start,end])[:16]
            subject = dict(subject_id=subject_id,byte_spans=[[start,end]])
            if subject not in note['subjects']:
                note['subjects'].append(subject)
            views[view] = dict(note_id=note_id,subject_id=subject_id)
        records.append(dict(entry=entry,title=title,meaning=meaning,
                            source_note_id=item['source_note_id'],views=views))
    output.mkdir(parents=True)
    write(output/'inputs.json',dict(status=('Frozen standalone-selection diagnostic' if standalone
        else 'Frozen title-selection diagnostic; unchanged context'),
        source_study=str(study),sources=sources,selected_text=selected_text,
        records=records,views=['standalone'] if standalone else list(VIEWS)))
    write(output/'worker-request.json',dict(schema_version=1,
        proposal_sha256=worker._sha256_file(output/'inputs.json'),notes=list(contexts.values())))
    write(output/'worker-config.json',dict(template,request_path=str(output/'worker-request.json'),
        request_sha256=worker._sha256_file(output/'worker-request.json'),
        output_path=str(output/'worker-result')))
    worker._load_request(output/'worker-request.json')
    worker.WorkerConfig.load(output/'worker-config.json')
    return dict(records=len(records),contexts=len(contexts),
                rows=sum(len(n['subjects']) for n in contexts.values()))


def collect(directory):
    import numpy as np
    directory = Path(directory).resolve()
    inputs = read(directory/'inputs.json')
    unchanged(inputs['sources'])
    config = worker.WorkerConfig.load(directory/'worker-config.json')
    if worker._sha256_file(config.request_path) != config.request_sha256:
        raise ValueError('worker request hash differs')
    proposal,notes = worker._load_request(config.request_path)
    if proposal != worker._sha256_file(directory/'inputs.json'):
        raise ValueError('worker proposal differs from frozen inputs')
    receipt = read(config.output_path/'worker-receipt.json')
    raw_path = config.output_path/'raw-vectors.f32le'
    for key,expected in dict(proposal_sha256=proposal,request_sha256=config.request_sha256,
            checkpoint_sha256=config.checkpoint_sha256,
            base_model_artifact_tree_sha256=config.base_model_artifact_tree_sha256,
            model=config.model.to_json(),dimensions=config.model.dimensions).items():
        if receipt[key] != expected:
            raise ValueError('worker identity differs: '+key)
    if (receipt['runtime']['worker_sha256'] != worker._sha256_file(Path(worker.__file__))
            or receipt['files'][raw_path.name]['sha256'] != worker._sha256_file(raw_path)):
        raise ValueError('worker source or vector bytes differ')
    keys = [(n.note_id,s.subject_id) for n in notes for s in n.subjects]
    if keys != [(r['note_id'],r['subject_id']) for r in receipt['rows']]:
        raise ValueError('worker row mapping differs')
    raw = np.fromfile(raw_path,dtype='<f4').reshape(len(keys),config.model.dimensions).astype(float)
    if not np.isfinite(raw).all() or (np.linalg.norm(raw,axis=1)==0).any():
        raise ValueError('finite nonzero vectors required')
    raw /= np.linalg.norm(raw,axis=1)[:,None]
    lookup = {k:i for i,k in enumerate(keys)}
    files = {}
    for view in inputs['views']:
        values = raw[[lookup[(r['views'][view]['note_id'],r['views'][view]['subject_id'])]
                      for r in inputs['records']]]
        path = directory/(view+'-vectors.npy')
        if path.exists():
            if not np.array_equal(np.load(path,allow_pickle=False),values):
                raise ValueError('existing collected vectors differ')
        else:
            np.save(path,values,allow_pickle=False)
        files[path.name] = worker._sha256_file(path)
    report = dict(records=len(inputs['records']),dimensions=config.model.dimensions,files=files,
        inputs_sha256=worker._sha256_file(directory/'inputs.json'),
        receipt_sha256=worker._sha256_file(config.output_path/'worker-receipt.json'))
    path = directory/'collected.json'
    if path.exists() and read(path) != report:
        raise ValueError('existing collection receipt differs')
    if not path.exists():
        write(path,report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    p.add_argument('study',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--entry',action='append',required=True)
    selection=p.add_mutually_exclusive_group(required=True)
    selection.add_argument('--title-text')
    selection.add_argument('--whole-title',action='store_true',
                           help='Use each entire title; retain meaning context unless --standalone')
    p.add_argument('--standalone',action='store_true',
                   help='Encode only the selected text; reuse saved contextual vectors separately')
    p=sub.add_parser('collect')
    p.add_argument('directory',type=Path)
    a=parser.parse_args()
    result=(prepare(a.study,a.entry,a.title_text,a.output,standalone=a.standalone) if a.command=='prepare'
            else collect(a.directory))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
