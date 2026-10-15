"""Apply disjoint native section definitions from one frozen clustering together.

Teacher requests remain ordinary shared-runner experiments. This offline step
validates their receipts and common input pool, prepares only missing synthetic
vectors, and preserves original grouped eligibility and retained-root lineage.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from . import hdbscan_section_replacement as replacement
from . import hdbscan_epsilon_review as review
from . import hierarchy_generation as generation
from . import worker
from . import experiment as workflow


def prepare(directory, source_path):
    directory, source_path = Path(directory).resolve(), Path(source_path).resolve()
    sources, cached = {}, {}

    def read_bytes(path):
        path = Path(path).resolve()
        if path not in cached:
            cached[path] = path.read_bytes()
        sources[str(path)] = hashlib.sha256(cached[path]).hexdigest()
        return cached[path]

    source = json.loads(read_bytes(source_path))
    if (set(source) != {'schema_version', 'replacement_review', 'proposals'}
            or type(source['schema_version']) is not int or source['schema_version'] != 1
            or not isinstance(source['replacement_review'], str)
            or not isinstance(source['proposals'], list) or not source['proposals']):
        raise ValueError('root round requires schema 1, replacement_review and nonempty proposals')
    analysis_path = workflow.resolve(source['replacement_review'], source_path.parent)
    previous = analysis_path.parent
    base = replacement._load_replacement(previous)
    if replacement.saved_review(previous) != json.loads(read_bytes(analysis_path)):
        raise ValueError('round review differs from saved native evidence')
    sections, removed, validated = set(), set(), []
    for proposal in source['proposals']:
        fields = {'experiment', 'case'} | ({'section'} if 'section' in proposal else set())
        if (set(proposal) != fields or any(not isinstance(v, str) or not v for v in proposal.values())):
            raise ValueError('round proposal requires experiment, case and optional saved-group section')
        experiment = workflow.resolve(proposal['experiment'], source_path.parent)
        case, _ = replacement._saved_case(experiment, proposal['case'], read_bytes)
        override = (dict(schema_version=1, replacement_review=str(analysis_path),
                         section=proposal['section'], stage='section') if 'section' in proposal else None)
        evidence, protected, prior = replacement._section_result(experiment, case, source=override)
        if evidence['replacement_review'] != str(analysis_path) or prior != base:
            raise ValueError('round proposals must share the same frozen input pool')
        if evidence['section'] in sections or removed.intersection(evidence['input_ids']):
            raise ValueError('round section proposals overlap')
        sections.add(evidence['section'])
        removed.update(evidence['input_ids'])
        for path, digest in protected.items():
            if path in sources and sources[path] != digest:
                raise ValueError('conflicting round source: ' + path)
            sources[path] = digest
        validated.append((experiment, case, evidence, override is not None))
    pool = deepcopy(base['pool'])
    generation._collect_encodings(pool)
    if any(not job['complete'] for job in pool['encodings']):
        raise ValueError('round source vectors are incomplete')
    if not removed <= set(base['current_ids']):
        raise ValueError('round membership is not a current input subset')
    retained = [i for i in base['current_ids'] if i not in removed]
    next_id = 1+max(int(i[1:]) for i in pool['items'] if i.startswith('R'))
    changes = []
    for index, (experiment, case, evidence, reused) in enumerate(validated):
        identifier = f'R{next_id+index:05d}'
        origins = sorted(o for i in evidence['input_ids'] for o in pool['items'][i]['original_ids'])
        if len(set(origins)) != len(origins):
            raise ValueError('round original supports overlap')
        pool['items'][identifier] = dict(subject=case['parsed']['title'],
            meaning=case['parsed']['meaning'], original_ids=origins)
        changes.append(dict(id=identifier, section=evidence['section'],
            removed_input_ids=evidence['input_ids'], original_ids=origins,
            experiment=str(experiment), case=case['id'], receipt=case['receipt'], reused_definition=reused))
    added = [c['id'] for c in changes]
    pool['items'] = {i: pool['items'][i] for i in retained+added}
    for path in [Path(__file__), Path(replacement.__file__), Path(review.__file__),
                 Path(generation.__file__), Path(worker.__file__), Path(review.hdbscan.__file__)]:
        read_bytes(path)
    for path, expected in sources.items():
        if replacement.sha(path) != expected:
            raise ValueError('round source changed during preparation: ' + path)
    pool['sources'] = {str(Path(worker.__file__).resolve()): replacement.sha(worker.__file__)}
    directory.mkdir(parents=True, exist_ok=False)
    first_new_encoding = len(pool['encodings'])
    generation._prepare_encoding(directory, pool, added)
    last = changes[-1]
    plan = dict(base, experiment=last['experiment'], case=last['case'], receipt=last['receipt'],
        replacement_id=last['id'], replacement_ids=added, root_changes=changes,
        removed_ids=last['original_ids'], removed_input_ids=sorted(removed),
        source_replacement=str(previous), replacement_review=str(analysis_path),
        current_ids=retained+added, first_new_encoding=first_new_encoding,
        round_source=str(source_path), sources=sources, pool=pool)
    workflow.write(directory/'replacement.json', dict(plan=plan, sha256=workflow.inputs.digest(plan)))
    return dict(proposals=len(changes), removed_entries=len(removed), updated_entries=len(retained)+len(added),
        reused_vectors=len(retained), added_ids=added,
        worker_configs=[j['config'] for j in pool['encodings'][first_new_encoding:]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    prepare_parser.add_argument('directory', type=Path)
    prepare_parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.directory, args.source)))


if __name__ == '__main__':
    main()
