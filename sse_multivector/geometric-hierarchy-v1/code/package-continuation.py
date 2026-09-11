"""Package unchanged experimental evidence and verify recorded source hashes.

No model calls, fitting, relabeling, pruning, or modification of prior runs.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from geometric_experiment import overlay, write_json

evidence = json.loads((ROOT/'GDC09/evidence.json').read_text())
for record in evidence:
    for a in record['aliases']:
        a['full_note_with_inline_mask'] = overlay(a['text'], a['byte_spans'])
ids = {a['short_id']: r['row'] for r in evidence for a in r['aliases']}
targets = ['V356', 'V494', 'V595', 'V482', 'V746', 'V150', 'V301', 'V765']
paths = {}
for run in ['GDC02', 'GDC06', 'GDC07', 'GDC08', 'GDC09']:
    tree = json.loads((ROOT/run/'hierarchy.json').read_text())
    nodes = {n['id']: n for n in tree['nodes']}
    parents = {c: n['id'] for n in tree['nodes'] for c in n['children']}
    chains = {}
    for v in targets:
        chain = [ids[v]]
        while chain[-1] in parents:
            chain.append(parents[chain[-1]])
        chains[v] = chain
    selected = set(n for chain in chains.values() for n in chain)
    paths[run] = dict(chains_leaf_to_root=chains,
                     nodes=[nodes[n] for n in sorted(selected)],
                     stop_reason=tree['stats']['stop_reason'])
write_json(ROOT/'path-evidence.json', dict(
    description='Complete native ancestor chains, not a pruned hierarchy. Member row numbers index evidence; every alias includes original full note and exact inline mask. Human discussion labels were not inputs.',
    source_runs=paths, evidence=evidence,
    diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))

crossings = {}
for run in ['GFM01', 'GFM02']:
    native = json.loads((ROOT/run/'native-fuzzy.json').read_text())
    arrays = np.load(ROOT/run/'native-fuzzy-arrays.npz')
    levels = [arrays[l['membership']['array']] for l in native['levels']]
    transitions = [arrays[t['interpolation']['array']] for t in native['transitions']]
    rows = []
    for step, (m, after, p) in enumerate(zip(levels, levels[1:], transitions), 1):
        assert np.allclose(m @ p, after, rtol=0, atol=2e-14)
        before_winner, after_winner = m.argmax(axis=1), after.argmax(axis=1)
        count = np.zeros(p.shape, dtype=int)
        np.add.at(count, (before_winner, after_winner), 1)
        split = np.count_nonzero(count, axis=1) > 1
        rows.append(dict(new_level=step, nonempty_prior_groups=int(np.count_nonzero(count.sum(axis=1))),
                         crossing_children=int(split.sum()),
                         rows_in_crossing_children=int(count[split].sum()),
                         minimum_changed_winners=int(np.sum(count.sum(axis=1)-count.max(axis=1))),
                         local_argmax_disagreements=int(np.count_nonzero(p.argmax(axis=1)[before_winner] != after_winner)),
                         zero_edge_winners=int(np.count_nonzero(p[before_winner, after_winner] == 0))))
    crossings[run] = rows
assert crossings['GFM01'][5]['minimum_changed_winners'] == 141
assert crossings['GFM02'][7]['minimum_changed_winners'] == 218
write_json(ROOT/'fmc-native-crossings.json', dict(
    description='Independent per-level argmax diagnostic, not a prescribed native FMC readout or semantic error count. Counts prove the two winner partitions cannot both remain unchanged whole-child partitions.',
    argmax_ties='NumPy first index, matching the existing diagnostic; all raw matrices preserved.',
    results=crossings,
    diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))

# Mechanically extend the existing generated provenance index. Old results are
# never rewritten. Every source version used by a fit must have a matching copy.
provenance_path = ROOT/'provenance.json'
provenance = json.loads(provenance_path.read_text())
archives = {}
for source in ROOT.rglob('*.py'):
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    archives.setdefault(sha, []).append(str(source.relative_to(ROOT)))
indexed = {r['run_id'] for r in provenance['runs']}
for configuration in sorted(ROOT.glob('G*/configuration.json')):
    run = configuration.parent
    if run.name in indexed:
        continue
    config = json.loads(configuration.read_text())
    code = {}
    for filename, sha in config['code'].items():
        assert sha in archives, (run.name, filename, sha)
        code[filename] = dict(sha256=sha, archived_files=sorted(archives[sha]))
    files = {}
    for file in sorted(run.iterdir()):
        if file.is_file():
            blob = file.read_bytes()
            files[file.name] = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob),
                                    tracked=file.name != 'coordinate-snapshots.npz')
    provenance['runs'].append(dict(run_id=run.name, code=code, files=files))
provenance['continuation_diagnostics'] = {
    file.name: dict(sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                   bytes=file.stat().st_size)
    for file in [ROOT/'continuation-validation.json', ROOT/'path-evidence.json',
                 ROOT/'fmc-native-crossings.json']}
provenance_path.write_text(json.dumps(provenance, indent=2) + '\n')
print('Packaged complete paths, independently verified FMC crossings, and source provenance.')
