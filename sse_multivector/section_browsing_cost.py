"""Offline conditional browsing-cost diagnostic for saved section partitions.

This does not decide whether to split. It assumes correct child selection and
reports how much additional navigation a smaller note list could repay. Note
inspection, menu reading and clicking are not silently assigned equal costs.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def summarize(note_ids, labels):
    """Compare a flat note list with best/uniform/worst valid-child routes.

    Targets are uniform over distinct notes; note-list order is random. The
    expected position of the target in an m-note list is (m + 1) / 2. All three
    routing profiles assume the user selects a child containing the target;
    they are conditional scenarios, not measured behavior or confidence bounds.
    """
    notes, labels = np.asarray(note_ids), np.asarray(labels)
    if (notes.ndim != 1 or labels.ndim != 1 or not len(notes)
            or len(notes) != len(labels) or notes.dtype.kind not in 'US'
            or any(not n for n in notes.tolist()) or labels.dtype.kind not in 'iu'
            or not np.array_equal(np.unique(labels), np.arange(len(np.unique(labels))))):
        raise ValueError('Aligned nonempty note IDs and contiguous integer section labels required')
    children = [set(notes[labels == k].tolist()) for k in range(int(labels.max()) + 1)]
    counts = [len(child) for child in children]
    routes = {}
    for k, child in enumerate(children):
        for note in child:
            routes.setdefault(note, []).append(k)
    parent = len(routes)
    flat = (parent + 1) / 2
    per_note = []
    for note, available in sorted(routes.items()):
        inspections = [(counts[k] + 1) / 2 for k in available]
        per_note.append(dict(note_id=note, children=available,
                             best_valid=min(inspections),
                             uniform_valid=sum(inspections) / len(inspections),
                             worst_valid=max(inspections)))
    profiles = {}
    for name in ['best_valid', 'uniform_valid', 'worst_valid']:
        expected = sum(row[name] for row in per_note) / parent
        profiles[name] = dict(expected_note_inspections=expected,
                              maximum_extra_navigation_cost=flat - expected)
    return dict(parent_notes=parent, child_note_counts=counts,
                extra_note_child_memberships=sum(counts) - parent,
                all_children_narrow=all(count < parent for count in counts),
                distinct_child_note_sets=len({frozenset(c) for c in children}) == len(children),
                flat_expected_note_inspections=flat,
                conditional_profiles=profiles, per_note=per_note)


def analyze(note_ids, labels, *, shuffles, seed):
    """Preserve entry counts while shuffling which entries form each child."""
    if type(shuffles) is not int or shuffles < 1:
        raise ValueError('At least one shuffled-membership control required')
    observed = summarize(note_ids, labels)
    labels = np.asarray(labels)
    rng = np.random.default_rng(seed)
    controls = []
    for draw in range(shuffles):
        shuffled = rng.permutation(labels)
        summary = summarize(note_ids, shuffled)
        summary.pop('per_note')
        controls.append(dict(draw=draw, labels=shuffled.tolist(),
                             child_entry_counts=np.bincount(shuffled).tolist(), **summary))
    return dict(status='Experimental diagnostic, not a stopping rule or semantic qualification',
                assumptions=[
                    'Each distinct parent note is equally likely to be the target.',
                    'Notes are inspected in a random order until the target is found.',
                    'Every routing profile assumes selection of a child containing the target.',
                    'Best-valid routing is an optimistic bound; uniform/worst-valid also exclude wrong turns.',
                    'Extra navigation cost includes menu reading and clicking, in units of one note inspection.',
                    'No numerical conversion from menu reading/clicking to note inspections is assumed.',
                    'Topics, titles and semantic grouping quality are not evaluated by these costs.'],
                observed=observed, shuffled_memberships=controls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', type=Path, help='Saved input.npz, plan.json and direct/constrained.json')
    parser.add_argument('output', type=Path)
    parser.add_argument('--shuffles', type=int, default=64)
    parser.add_argument('--seed', type=int, default=20261018)
    args = parser.parse_args()
    if args.shuffles < 1 or args.seed < 0:
        parser.error('Positive shuffle count and nonnegative seed required')
    source = args.experiment.resolve()
    paths = [source / name for name in ['input.npz', 'plan.json', 'direct/constrained.json']]
    sources = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    source_plan = json.loads(paths[1].read_text())
    if sources[str(paths[0])] != source_plan['input_sha256']:
        parser.error('Saved experiment input hash changed')
    for path, expected in source_plan.get('sources', {}).items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            parser.error('Frozen experiment source hash changed: ' + path)
    selected = json.loads(paths[2].read_text())['best']
    packet = np.load(paths[0], allow_pickle=False)
    notes = packet['notes']
    observed = summarize(notes, selected['labels'])
    if observed['child_note_counts'] != selected['section_notes']:
        parser.error('Saved distinct-note counts disagree with memberships')
    args.output.mkdir(parents=True, exist_ok=False)
    plan = dict(status='Frozen before conditional browsing-cost calculation; no HiGen change',
                sources=sources,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                shuffles=args.shuffles, seed=args.seed, numpy_version=np.__version__,
                target_weighting='uniform distinct parent notes',
                list_scan='random-order sequential inspection until the target is found',
                navigation_cost='unknown; report break-even cost in note-inspection units',
                controls='Shuffle entry labels while preserving each child entry count')
    (args.output / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    result = analyze(notes, selected['labels'], shuffles=args.shuffles, seed=args.seed)
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('notes', observed['parent_notes'], 'children', observed['child_note_counts'],
          'flat inspections', observed['flat_expected_note_inspections'],
          'conditional uniform-route inspections',
          observed['conditional_profiles']['uniform_valid']['expected_note_inspections'])


if __name__ == '__main__':
    main()
